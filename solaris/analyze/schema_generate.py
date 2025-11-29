from collections import defaultdict
from collections.abc import Callable
from functools import partial
import importlib
import re
from typing import TYPE_CHECKING, ClassVar, TypedDict, TypeVar, cast
from typing_extensions import TypeIs, Unpack

from pydantic import GetJsonSchemaHandler
from pydantic.json_schema import (
	GenerateJsonSchema,
	JsonSchemaMode,
	JsonSchemaValue,
	model_json_schema,
)
from pydantic_core import CoreSchema
from seerapi_models.build_model import BaseGeneralModel

if TYPE_CHECKING:
	from pydantic._internal._core_utils import CoreSchemaOrField

from seerapi_models.common import ApiResourceList, NamedData, ResourceRef

from solaris.utils import join_url

seerapi_models = importlib.import_module('seerapi_models')
seerapi_common_models = importlib.import_module('seerapi_models.common')
all_models = seerapi_common_models.__dict__ | seerapi_models.__dict__


ROOT_MARK = type('RootMark', (), {})()
ROOT_MARK_KEY = type('RootMarkKey', (), {})()


def _mark_in_schema(core_schema) -> bool:
	return core_schema.get(ROOT_MARK_KEY) is ROOT_MARK


def _add_mark_to_schema(core_schema) -> dict:
	core_schema[ROOT_MARK_KEY] = ROOT_MARK
	return core_schema


def _get_cls_from_schema(core_schema: CoreSchema) -> type | None:
	return core_schema.get('cls')


class _ExtraSchemaField(TypedDict):
	model_name: str


def create_extra_schema(**kwargs: Unpack[_ExtraSchemaField]) -> dict[str, object]:
	"""创建额外的 JSON Schema 字段，使用 x- 前缀符合 JSON Schema 规范

	Args:
		**kwargs: 额外字段的键值对，key 会自动添加 x- 前缀并转换为连字符格式

	Returns:
		包含 x- 前缀字段的字典，例如 {'x-model-name': 'Pet'}
	"""
	return {f'x-{key.replace("_", "-")}': value for key, value in kwargs.items()}


def _get_model_name(cls: type) -> str:
	cls_name: str = cls.__name__
	bracket_matches = re.findall(r'\[([^\]]+)\]', cls_name)
	if len(bracket_matches) == 0:
		raise ValueError(f'无效的模型名称: {cls_name}，该模型不是泛型模型')

	model_cls_name = bracket_matches[0]
	if (model := all_models.get(model_cls_name)) is None:
		raise ValueError(
			f'无效的模型名称: {cls_name}，找不到泛型参数{model_cls_name}对应的模型'
		)

	return model.resource_name()


def is_base_general_model(cls: type) -> TypeIs['type[BaseGeneralModel]']:
	return issubclass(cls, BaseGeneralModel)


injected_func = Callable[[CoreSchema, GetJsonSchemaHandler], JsonSchemaValue]
_TCoreSchemaOrField = TypeVar('_TCoreSchemaOrField', bound='CoreSchemaOrField')


class PydanticJsFunctionInjector:
	"""JSON Schema 自定义函数注入器

	提供集中式的机制来为特定类型批量注册 JSON Schema 生成函数，
	避免在每个模型类上重复实现 __get_pydantic_json_schema__。

	工作原理：
	1. 通过 @register 装饰器将自定义函数与目标类型关联
	2. 在 schema 生成时，inject_functions 将注册的函数注入到 CoreSchema 的 metadata 中
	3. Pydantic 在生成 JSON Schema 时会自动调用 metadata['pydantic_js_functions'] 中的所有函数

	使用场景：
	- 为多个相似类型统一添加额外的 JSON Schema 字段（如 ResourceRef 和 ApiResourceList）
	- 实现跨模型的 JSON Schema 增强逻辑，而无需修改模型定义

	Example:
		>>> @PydanticJsFunctionInjector.register(ResourceRef, ApiResourceList)
		... def add_model_name(schema, handler):
		...     json_schema = handler(schema)
		...     json_schema['extra'] = {'model_name': 'example'}
		...     return json_schema
	"""

	injected_functions: ClassVar[defaultdict[type, list[injected_func]]] = defaultdict(
		list
	)

	@classmethod
	def register(cls, *types: type):
		"""装饰器工厂：将函数注册到指定的类型

		注册的函数会在对应类型生成 JSON Schema 时被调用，
		允许对 JSON Schema 进行自定义修改。

		Args:
			*types: 需要应用此函数的目标类型（支持多个）

		Returns:
			装饰器函数，接收并返回 injected_func 类型的函数
		"""

		def decorator(func: injected_func) -> injected_func:
			for type_ in types:
				cls.injected_functions[type_].append(func)

			return func

		return decorator

	@classmethod
	def inject_functions(cls, schema: _TCoreSchemaOrField) -> _TCoreSchemaOrField:
		"""将已注册的函数注入到 CoreSchema 的 metadata 中

		遍历所有已注册的类型，如果 schema 对应的类是某个注册类型的子类，
		则将对应的函数列表注入到 metadata['pydantic_js_functions'] 中。
		Pydantic 内部会在 JSON Schema 生成过程中自动调用这些函数。

		Args:
			schema: 待注入的 CoreSchema 或 CoreSchemaField

		Returns:
			注入后的 schema（原地修改）
		"""
		model_cls = schema.get('cls')
		if model_cls is None:
			return schema
		if (metadata := schema.get('metadata')) is None:
			return schema

		# 遍历注册表，匹配第一个符合的类型
		for type_, functions in cls.injected_functions.items():
			if issubclass(model_cls, type_):
				metadata['pydantic_js_functions'].extend(functions)
				break

		return schema


@PydanticJsFunctionInjector.register(ResourceRef, ApiResourceList)
def ref_get_pydantic_json_schema(schema, handler):
	cls = schema.get('cls')
	json_schema = handler(schema)
	try:
		model_name = _get_model_name(cls)
	except ValueError:
		return json_schema

	return json_schema | create_extra_schema(model_name=model_name)


@PydanticJsFunctionInjector.register(NamedData)
def named_data_get_pydantic_json_schema(schema, handler):
	json_schema = {
		'$schema': 'https://json-schema.org/draft/2020-12/schema',
		'title': 'NamedData',
		'type': 'object',
		'properties': {
			'data': {
				'type': 'object',
				'patternProperties': {'^[0-9]+$': {'$dynamicRef': '#TResModel'}},
				'additionalProperties': False,
			}
		},
		'required': ['data'],
		'$defs': {'TResModel': {'$dynamicAnchor': 'TResModel'}},
	}
	return json_schema


class JsonSchemaGenerator(GenerateJsonSchema):
	base_url: str

	def generate_inner(self, schema):
		PydanticJsFunctionInjector.inject_functions(schema)
		return super().generate_inner(schema)

	def model_schema(self, schema):
		if not hasattr(self, 'base_url'):
			raise ValueError('base_url is not set')

		json_schema = super().model_schema(schema)
		cls = _get_cls_from_schema(schema)
		if cls is None or not is_base_general_model(cls) or _mark_in_schema(schema):
			return json_schema

		return {'$ref': join_url(self.base_url, cls.schema_path())}

	def generate(self, schema, mode: JsonSchemaMode = 'serialization'):
		json_schema = super().generate(schema, mode)
		json_schema['$schema'] = self.schema_dialect
		return json_schema


class ShrinkOnlyNonRoot(JsonSchemaGenerator):
	def generate(self, schema, mode: JsonSchemaMode = 'serialization'):
		"""
		重写根级别 schema 生成，
		将非根模型的 BaseGeneralModel schema 省略为 $ref 引用
		"""
		cls = _get_cls_from_schema(schema)

		if cls is not None and is_base_general_model(cls):
			# 标记为根模型以输出完整 schema
			new_core_schema = schema.copy()
			_add_mark_to_schema(new_core_schema)
		else:
			new_core_schema = schema

		json_schema = super().generate(new_core_schema, mode)
		return json_schema


_GT = TypeVar('_GT', bound=GenerateJsonSchema)


def create_generator(model_type: type[_GT], *, base_url: str) -> type[_GT]:
	"""
	为给定的 GenerateJsonSchema 类型动态创建子类，
	并将 base_url 注入为子类的类属性
	"""
	return cast(
		type[_GT],
		type(
			model_type.__name__,
			(model_type,),
			{'base_url': base_url},
		),
	)


model_json_schema = partial(
	model_json_schema,
	mode='serialization',
)

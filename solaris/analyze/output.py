from collections import defaultdict
from collections.abc import Iterable, Mapping, MutableMapping, Sequence
import inspect
from pathlib import Path
from typing import (
	Annotated,
	Any,
	Protocol,
	TypeAlias,
	TypeVar,
	overload,
)

from pydantic import BaseModel, TypeAdapter
from pydantic.fields import FieldInfo
from pydantic.json_schema import GenerateJsonSchema, model_json_schema
from seerapi_models.common import (
	ApiResourceList,
	BaseGeneralModel,
	NamedData,
	NamedResourceRef,
	ResourceRef,
)
from seerapi_models.metadata import ApiMetadata
from tqdm import tqdm

from solaris.analyze.db import DBManager
from solaris.analyze.schema_generate import (
	JsonSchemaGenerator,
	ShrinkOnlyNonRoot,
	create_extra_schema,
	create_generator,
	seerapi_common_models,
)
from solaris.analyze.typing_ import AnalyzeResult, TResModelRequiredId
from solaris.analyze.utils import to_json
from solaris.utils import join_url

HASH_FIELD = FieldInfo(
	annotation=str,
	title='Hash',
	description='数据哈希值，目前pydantic不支持对key进行排序，所以哈希值变化可能意味着数据结构变化而非数据值变化',
)

DEFAULT_FIELDS = (('hash', HASH_FIELD),)


_TMap = TypeVar('_TMap', bound=MutableMapping[str, Any])
DataMap: TypeAlias = Mapping[int, TResModelRequiredId]


def _add_fields_to_schema(
	schema: _TMap, fields: Iterable[tuple[str, FieldInfo]]
) -> _TMap:
	"""向schema添加额外字段"""
	if 'properties' not in schema:
		return schema

	for field_name, field_info in fields:
		field_name = field_info.alias or field_name
		adapter = TypeAdapter(Annotated[field_info.annotation, field_info])
		schema['properties'][field_name] = adapter.json_schema(mode='serialization')
		if field_info.is_required:
			schema['required'].append(field_name)

	return schema


def _calc_hash(data: str | bytes) -> str:
	import anycrc

	crc32 = anycrc.Model('CRC32')
	if isinstance(data, str):
		data = data.encode('utf-8')

	hash_value = crc32.calc(data)
	return format(hash_value, 'x')


def _create_index_model(name: str, data: dict[str, Any]) -> type[BaseModel]:
	from pydantic import Field, create_model

	return create_model(
		name,
		**{
			k: (str, Field(field_title_generator=lambda k, __: f'{k} Path'))
			for k in data.keys()
		},  # type: ignore
	)


def _generate_api_resource_list(data: DataMap[TResModelRequiredId]) -> ApiResourceList:
	refs: list[NamedResourceRef] = [
		NamedResourceRef.from_res_name(
			id=i.id,
			resource_name=i.resource_name(),
			name=getattr(i, 'name', None),
		)
		for i in data.values()
	]
	return ApiResourceList(count=len(refs), results=refs)


_GT = TypeVar('_GT', bound=GenerateJsonSchema)


class OutputterProtocol(Protocol):
	"""输出器协议"""

	def run(self, results: Sequence[AnalyzeResult]) -> None:
		"""执行输出流程"""
		pass


class JsonOutputter(OutputterProtocol):
	"""负责将分析结果输出为JSON文件和Schema的类"""

	def __init__(
		self,
		*,
		metadata: ApiMetadata,
		base_output_dir: str | Path = '.',
		schema_output_dir: str | Path,
		base_schema_url: str | None = None,
		data_output_dir: str | Path,
		base_data_url: str | None = None,
	) -> None:
		"""初始化JSON输出器

		Args:
			metadata: API元数据
			base_output_dir: 基础输出目录
			schema_output_dir: Schema输出目录（相对于版本目录）
			base_schema_url: Schema基础URL（可选）
			data_output_dir: 数据输出目录（相对于版本目录）
			base_data_url: 数据基础URL（可选）
		"""
		self.metadata = metadata

		# 计算URL
		version = metadata.api_version
		base_url = metadata.api_url
		self.data_url = base_data_url or join_url(
			base_url, version, str(data_output_dir)
		)
		self.schema_url = base_schema_url or join_url(
			base_url, version, str(schema_output_dir)
		)

		# 设置全局资源URL
		ResourceRef.base_data_url = self.data_url

		# 计算输出目录
		self.data_output_dir = Path().joinpath(
			base_output_dir,
			version,
			data_output_dir,
		)
		self.schema_output_dir = Path().joinpath(
			base_output_dir,
			version,
			schema_output_dir,
		)

		# 创建输出目录
		self.data_output_dir.mkdir(parents=True, exist_ok=True)
		self.schema_output_dir.mkdir(parents=True, exist_ok=True)

		self.shrink_generator = self._create_generator(ShrinkOnlyNonRoot)
		self.normal_generator = self._create_generator(JsonSchemaGenerator)

	def _dump_data(self, data: Any, path: Path | str) -> None:
		if isinstance(data, BaseModel):
			data = data.model_dump(by_alias=True)
		if not isinstance(data, MutableMapping):
			raise ValueError(f'Invalid data type: {type(data)}')

		data['hash'] = _calc_hash(to_json(data, indent=None))

		path = self.data_output_dir.joinpath(path)
		path.parent.mkdir(parents=True, exist_ok=True)
		path.write_bytes(to_json(data))

	def _dump_schema(
		self,
		schema: MutableMapping[str, Any],
		path: Path | str,
		*,
		fields: tuple[tuple[str, FieldInfo], ...] = DEFAULT_FIELDS,
	) -> None:
		schema = _add_fields_to_schema(schema, fields)
		path = self.schema_output_dir.joinpath(path)
		path.parent.mkdir(parents=True, exist_ok=True)
		path.write_bytes(to_json(schema))

	def _create_generator(self, schema_generator: type[_GT]) -> type[_GT]:
		return create_generator(schema_generator, base_url=self.schema_url)

	def _output_all_common_model_schema(self) -> None:
		for model in seerapi_common_models.__dict__.values():
			if not issubclass(model, BaseGeneralModel) or inspect.isabstract(model):
				continue

			schema_path = model.schema_path()
			self._dump_schema(
				model_json_schema(model, schema_generator=self.shrink_generator),
				Path(schema_path) / 'index.json',
				fields=(),
			)

	def _generate_schema_for_result(
		self, result: AnalyzeResult
	) -> MutableMapping[str, Any]:
		"""为分析结果生成Schema

		Args:
			result: 分析结果

		Returns:
			生成的Schema
		"""
		if result.schema is not None:
			return result.schema

		return model_json_schema(result.model, schema_generator=self.shrink_generator)

	def _output_json_and_schema(
		self,
		path: Path | str,
		*,
		data: Any,
		schema: Any | None = None,
		schema_generator: type[GenerateJsonSchema] = ShrinkOnlyNonRoot,
		post_add_fields: tuple[tuple[str, FieldInfo], ...] = DEFAULT_FIELDS,
	) -> None:
		"""输出JSON数据和对应的Schema

		Args:
			path: 输出路径（相对于输出目录）
			data: 要输出的数据
			schema: 可选的Schema，如果不提供则自动生成
			schema_generator: Schema生成器类型
			post_add_fields: 要添加到Schema的额外字段
		"""
		generator = create_generator(schema_generator, base_url=self.schema_url)
		if schema is None:
			if isinstance(data, TypeAdapter):
				schema = data.json_schema(schema_generator=generator)
			elif isinstance(data, BaseModel):
				schema = model_json_schema(type(data), schema_generator=generator)

		if not isinstance(schema, MutableMapping):
			raise ValueError(f'Invalid schema: {schema}')

		self._dump_data(data, path)
		self._dump_schema(schema, path, fields=post_add_fields)

	def _output_merged_json(
		self,
		resource_name: str,
		data: Any,
		schema: MutableMapping[str, Any],
	) -> None:
		"""输出合并模式的JSON（所有数据在一个文件中）

		Args:
			resource_name: 资源名称
			data: 要输出的数据
			schema: Schema
		"""
		self._output_json_and_schema(
			f'{resource_name}.json',
			data=data,
			schema=schema,
		)

	def _generate_named_data_schema(
		self, resource_name: str
	) -> MutableMapping[str, Any]:
		"""生成名称到数据的映射表的Schema"""
		schema = {
			'$schema': 'https://json-schema.org/draft/2020-12/schema',
			'type': 'object',
			'properties': {
				'data': {
					'$defs': {
						'TResModel': {
							'$dynamicAnchor': 'TResModel',
							'type': 'object',
							'$ref': join_url(self.schema_url, resource_name, '$id'),
						}
					},
					'$ref': join_url(self.schema_url, 'common', 'named_data'),
				}
			},
			'required': ['data'],
		}

		return schema

	def _generate_name_data(
		self, data: DataMap[TResModelRequiredId]
	) -> Mapping[str, NamedData[TResModelRequiredId]]:
		"""生成名称到数据的映射表

		Args:
			result: 分析结果
		"""
		name_data: defaultdict[str, NamedData[TResModelRequiredId]] = defaultdict(
			lambda: NamedData(data={})
		)
		for id, model in data.items():
			if name := getattr(model, 'name', None):
				name_data[str(name)].data[id] = model

		return name_data

	def _output_named_json(
		self,
		name_data: Mapping[str, NamedData[TResModelRequiredId]],
		resource_name: str,
		schema: MutableMapping[str, Any],
	) -> None:
		"""以名称作为key，将数据输出为JSON文件

		Args:
			name_data: 名称到数据的映射表
			resource_name: 资源名称
			schema: JSON Schema
		"""

		# 准备输出路径
		output_paths: dict[Path, NamedData[TResModelRequiredId]] = {}
		for name, res_data in name_data.items():
			res_path = Path(resource_name).joinpath(name, 'index.json')
			output_paths[res_path] = res_data

		# 输出Schema
		schema = self._generate_named_data_schema(resource_name)
		schema_path = Path(resource_name).joinpath('$name', 'index.json')
		self._dump_schema(schema, schema_path)

		# 批量输出数据文件
		for path, data in output_paths.items():
			self._dump_data(data, path)

	def _output_individual_json(
		self,
		data: DataMap[TResModelRequiredId],
		resource_name: str,
		schema: MutableMapping[str, Any],
	) -> None:
		"""输出按ID分散的JSON数据

		将数据按资源ID分散到不同的文件中，每个资源ID对应一个独立的JSON文件。
		同时输出对应的JSON Schema和API资源列表。

		Args:
			data: 分析出的数据，键为资源ID，值为资源模型实例
			resource_name: 资源名称，用于构建输出路径
			schema: JSON Schema定义，用于数据验证
		"""
		# 准备输出路径
		output_paths: dict[Path, TResModelRequiredId] = {}
		for res_id, res_data in data.items():
			res_path = Path(resource_name).joinpath(str(res_id), 'index.json')
			output_paths[res_path] = res_data

		# 输出Schema
		schema_path = Path(resource_name).joinpath('$id', 'index.json')
		self._dump_schema(schema, schema_path)

		# 输出ApiResourceList
		self._output_api_resource_list(data, resource_name)

		# 批量输出数据文件
		for path, res_data in output_paths.items():
			self._dump_data(res_data, path)

	def _output_api_resource_list(
		self,
		data: DataMap[TResModelRequiredId],
		resource_name: str,
	) -> None:
		"""输出ApiResourceList

		Args:
			data: 分析结果数据
			resource_name: 资源名称
		"""
		api_resource_list = _generate_api_resource_list(data)
		api_resource_list_schema = model_json_schema(
			ApiResourceList,
			schema_generator=self.normal_generator,
		) | create_extra_schema(model_name=resource_name)

		self._output_json_and_schema(
			Path(resource_name) / 'index.json',
			data=api_resource_list,
			schema=api_resource_list_schema,
		)

	def _process_single_result(
		self,
		result: AnalyzeResult[TResModelRequiredId],
		*,
		merge_json_table: bool,
		output_name_data: bool,
	) -> tuple[str, str] | None:
		"""处理单个分析结果

		Args:
			result: 分析结果
			merge_json_table: 是否合并为单个JSON文件
			output_name_data: 是否输出名称映射
		Returns:
			如果需要输出，返回 (resource_name, resource_url)，否则返回 None
		"""
		# 检查是否需要输出到JSON
		if result.output_mode not in ('json', 'all'):
			return None

		# 提取基本信息
		model = result.model
		resource_name = model.resource_name()
		schema = self._generate_schema_for_result(result)
		data = result.data

		# 根据模式输出
		if merge_json_table:
			self._output_merged_json(resource_name, data, schema)
		else:
			self._output_individual_json(data, resource_name, schema)
			# 输出名称映射
			if output_name_data:
				name_data = self._generate_name_data(data)
				self._output_named_json(name_data, resource_name, schema)

		# 返回索引信息
		return resource_name, join_url(self.data_url, resource_name)

	def _output_metadata(self) -> None:
		"""输出metadata文件"""
		self._output_json_and_schema('metadata.json', data=self.metadata)

	def _output_root_index(self, index_data: dict[str, str]) -> None:
		"""输出根目录的index.json

		Args:
			index_data: 索引数据
		"""
		index_model = _create_index_model('Index', index_data)
		self._output_json_and_schema(
			'index.json',
			data=index_data,
			schema=model_json_schema(index_model),
		)

	def run(
		self,
		results: Sequence[AnalyzeResult],
		*,
		merge_json_table: bool = False,
		output_name_data: bool = False,
	) -> None:
		"""执行JSON输出流程

		Args:
			results: 分析结果序列
			merge_json_table: 是否合并为单个JSON文件
		"""
		# 输出通用模型Schema
		self._output_all_common_model_schema()

		# 处理所有结果
		root_index_data: dict[str, str] = {}
		for result in (pbar_result := tqdm(results, leave=False)):
			resource_name = result.model.resource_name()
			pbar_result.set_description(
				f'正在输出JSON数据|输出{resource_name}',
				refresh=True,
			)

			# 处理单个结果
			result_info = self._process_single_result(
				result,
				merge_json_table=merge_json_table,
				output_name_data=output_name_data,
			)
			if result_info is not None:
				resource_name, resource_url = result_info
				root_index_data[resource_name] = resource_url

		# 输出metadata
		self._output_metadata()

		# 输出根目录index（仅在非合并模式）
		if not merge_json_table:
			self._output_root_index(root_index_data)


class DBOutputter(OutputterProtocol):
	"""负责将分析结果输出到数据库的类"""

	@overload
	def __init__(self, metadata: ApiMetadata, *, db_manager: DBManager) -> None: ...

	@overload
	def __init__(
		self,
		metadata: ApiMetadata,
		*,
		db_url: str,
		echo: bool = False,
		**kwargs,
	) -> None: ...

	def __init__(self, metadata: ApiMetadata, **kwargs) -> None:
		self.metadata = metadata
		if 'db_manager' in kwargs:
			self.db_manager = kwargs['db_manager']
		elif 'db_url' in kwargs and 'echo' in kwargs:
			self.db_manager = DBManager(**kwargs)
		else:
			raise ValueError('Invalid arguments')

	def init(self) -> None:
		if not self.db_manager.initialized:
			self.db_manager.init()

	@property
	def initialized(self) -> bool:
		return self.db_manager.initialized

	def run(self, results: Sequence[AnalyzeResult]) -> None:
		"""执行数据库输出流程

		Args:
			results: 分析结果序列
		"""
		if not self.initialized:
			raise RuntimeError('Database not initialized')

		for result in (pbar_result := tqdm(results, leave=False)):
			name = result.model.resource_name()
			pbar_result.set_description(
				f'正在输出数据库数据|输出{name}',
				refresh=True,
			)
			data = result.data
			output_mode = result.output_mode

			if output_mode not in ('db', 'all'):
				continue

			with self.db_manager.get_session() as session:
				from solaris.analyze.db import write_result_to_db

				write_result_to_db(session, data)

		# 保存元数据
		with self.db_manager.get_session() as session:
			session.add(self.metadata.to_orm())
			session.commit()

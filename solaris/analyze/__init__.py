from collections.abc import Iterable, MutableMapping, Sequence
from pathlib import Path
from typing import Annotated, Any, TypeVar

from pydantic import BaseModel, Field, TypeAdapter, create_model
from pydantic.fields import FieldInfo
from pydantic.json_schema import GenerateJsonSchema
from tqdm import tqdm

from solaris.utils import import_all_classes

from .base import BaseAnalyzer
from .db import DBManager, write_result_to_db
from .model import (
	ApiMetadata,
	ApiResourceList,
	BaseGeneralModel,
	NamedResourceRef,
	ResourceRef,
)
from .schema_generate import JsonSchemaGenerator, ShrinkOnlyNonRoot, model_json_schema
from .typing_ import AnalyzeResult
from .utils import to_json

ANALYZER_DEFAULT_PACKAGE_NAME = 'solaris.analyze.analyzers'

HASH_FIELD = FieldInfo(
	annotation=str,
	title='Hash',
	description='数据哈希值，目前pydantic不支持对key进行排序，所以哈希值变化可能意味着数据结构变化而非数据值变化'
)

DEFAULT_FIELDS = (
	('hash', HASH_FIELD),
)


def _calc_hash(data: str | bytes) -> str:
	import anycrc
	crc32 = anycrc.Model('CRC32')
	if isinstance(data, str):
		data = data.encode('utf-8')

	hash_value = crc32.calc(data)
	return format(hash_value, 'x')


def _dump_data(data: Any, path: Path) -> None:
	if isinstance(data, BaseModel):
		data = data.model_dump(by_alias=True)
	if not isinstance(data, MutableMapping):
		raise ValueError(f'Invalid data type: {type(data)}')

	data['hash'] = _calc_hash(to_json(data, indent=None))

	path.parent.mkdir(parents=True, exist_ok=True)
	path.write_bytes(to_json(data))


T = TypeVar('T', bound=MutableMapping[str, Any])
def _add_fields_to_schema(
	schema: T,
	fields: Iterable[tuple[str, FieldInfo]]
) -> T:
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


def _dump_schema(
	schema: MutableMapping[str, Any],
	path: Path,
	*,
	fields: tuple[tuple[str, FieldInfo], ...] = ()
) -> None:
	schema = _add_fields_to_schema(schema, fields)

	path.parent.mkdir(parents=True, exist_ok=True)
	path.write_bytes(to_json(schema))


def _output_all_general_model_schema(output_dir: Path, *, base_url: str) -> None:
	BaseGeneralModel.base_url = base_url
	for path, model in BaseGeneralModel.__subclasses_dict__.items():
		_dump_schema(model_json_schema(model), output_dir / path / 'index.json')


def _generate_api_resource_list(result: AnalyzeResult) -> ApiResourceList:
	refs: list[NamedResourceRef] = [
		NamedResourceRef(
			id=i.id,
			resource_name=i.resource_name(),
			name=getattr(i, 'name', None),
		)
		for i in result.data.values()
	]
	return ApiResourceList(count=len(refs), results=refs)


def _create_index_model(name: str, data: dict[str, Any]) -> type[BaseModel]:
	return create_model(
		name,
		**{
			k: (str, Field(field_title_generator=lambda k, __: f'{k} Path'))
			for k in data.keys()
		},  # type: ignore
	)


def _join_url(base_url: str, *parts: str, end_slash: bool = False) -> str:
	url = '/'.join(
		str(i).strip('/')
		for i in [base_url, *parts]
		if i and i not in ('.', '/', './')
	)
	if end_slash:
		url += '/'

	return url


def analyze_result_to_json(
	results: Sequence[AnalyzeResult],
	*,
	metadata: ApiMetadata,
	base_output_dir: str | Path = '.',
	schema_output_dir: str | Path,
	base_schema_url: str | None = None,
	data_output_dir: str | Path,
	base_data_url: str | None = None,
	merge_json_table: bool = False,
) -> None:
	"""分析数据并输出到JSON文件"""
	version = metadata.api_version
	base_url = metadata.api_url
	data_url = base_data_url or _join_url(
		base_url, version, str(data_output_dir)
	)
	schema_url = base_schema_url or _join_url(
		base_url, version, str(schema_output_dir)
	)

	ResourceRef.base_data_url = data_url

	data_output_dir = Path().joinpath(
		base_output_dir,
		version,
		data_output_dir,
	)
	data_output_dir.mkdir(parents=True, exist_ok=True)
	schema_output_dir = Path().joinpath(
		base_output_dir,
		version,
		schema_output_dir,
	)
	schema_output_dir.mkdir(parents=True, exist_ok=True)
	_output_all_general_model_schema(
		schema_output_dir,
		base_url=schema_url,
	)

	def output_json_and_schema(
		path: Path | str,
		*,
		data: Any,
		schema: Any | None = None,
		schema_generator: type[GenerateJsonSchema] = ShrinkOnlyNonRoot,
		post_add_fields: tuple[tuple[str, FieldInfo], ...] = DEFAULT_FIELDS,
	) -> None:
		if schema is None:
			if isinstance(data, TypeAdapter):
				schema = data.json_schema(schema_generator=schema_generator)
			elif isinstance(data, BaseModel):
				schema = model_json_schema(
					type(data),
					schema_generator=schema_generator,
				)

		if not isinstance(schema, MutableMapping):
			raise ValueError(f'Invalid schema: {schema}')

		_dump_data(data, data_output_dir.joinpath(path))
		_dump_schema(schema, schema_output_dir.joinpath(path), fields=post_add_fields)

	index_data: dict[str, str] = {}
	for result in (pbar_result := tqdm(results, leave=False)):
		# 初始化变量
		model = result.model
		resource_name = result.name or model.resource_name()
		schema = result.schema or model_json_schema(model)
		data = result.data
		output_mode = result.output_mode

		# 检查是否需要输出到JSON
		if output_mode not in ('json', 'all'):
			continue

		# 设置进度条
		pbar_result.set_description(
			f'正在输出JSON数据|输出{resource_name}',
			refresh=True,
		)

		output_paths: dict[Path, Any] = {}
		if merge_json_table:
			output_json_and_schema(
				f'{resource_name}.json',
				data=data,
				schema=schema,
				post_add_fields=(),  # 不添加额外字段
			)
		else:
			for res_id, res_data in data.items():
				res_path = data_output_dir.joinpath(
					resource_name,
					str(res_id),
					'index.json',
				)
				res_path.parent.mkdir(parents=True, exist_ok=True)
				output_paths[res_path] = res_data

			schema_path = schema_output_dir.joinpath(resource_name, '$id', 'index.json')
			_dump_schema(schema, schema_path, fields=DEFAULT_FIELDS)

			# 输出ApiResourceList
			api_resource_list = _generate_api_resource_list(result)
			output_json_and_schema(
				Path(resource_name) / 'index.json',
				data=api_resource_list,
				schema_generator=JsonSchemaGenerator,
			)

		for path, data in output_paths.items():
			_dump_data(data, path)

		index_data[resource_name] = _join_url(data_url, resource_name)

	# 输出metadata
	output_json_and_schema('metadata.json', data=metadata)

	if not merge_json_table:  # 输出根目录 index.json
		index_model = _create_index_model('Index', index_data)
		output_json_and_schema(
			'index.json',
			data=index_data,
			schema=model_json_schema(index_model),
		)


def analyze_result_to_db(
	results: Sequence[AnalyzeResult],
	*,
	metadata: ApiMetadata,
	db_url: str = 'sqlite:///solaris.db',
) -> None:
	db_manager = DBManager(db_url)
	if not db_manager.initialized:
		db_manager.init()

	for result in (pbar_result := tqdm(results, leave=False)):
		name = result.name or result.model.resource_name()
		pbar_result.set_description(
			f'正在输出数据库数据|输出{name}',
			refresh=True,
		)
		data = result.data
		output_mode = result.output_mode

		if output_mode not in ('db', 'all'):
			continue

		with db_manager.get_session() as session:
			write_result_to_db(session, data)

	with db_manager.get_session() as session:
		session.add(metadata.to_orm())
		session.commit()


def import_analyzer_classes(
	package_name: str = ANALYZER_DEFAULT_PACKAGE_NAME,
) -> list[type[BaseAnalyzer]]:
	return import_all_classes(
		package_name,
		BaseAnalyzer,
	)


def run_all_analyzer(
	analyzers: list[type[BaseAnalyzer]],
) -> list[AnalyzeResult]:
	results: list[AnalyzeResult] = []
	for analyzer_cls in (pbar_analyzer := tqdm(analyzers, leave=False)):
		pbar_analyzer.set_description(
			f'正在分析数据|调用{analyzer_cls.__name__}',
			refresh=True,
		)
		analyzer = analyzer_cls()
		result = analyzer.analyze()
		results.extend(result)

	return results

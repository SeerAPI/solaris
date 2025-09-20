from collections.abc import Sequence
from pathlib import Path
from typing import Any

from pydantic import BaseModel, TypeAdapter, create_model
from pydantic.json_schema import GenerateJsonSchema
from tqdm import tqdm

from solaris.utils import import_all_classes, to_json

from .base import BaseAnalyzer
from .db import DBManager, write_result_to_db
from .model import (
	ApiMetadata,
	ApiResourceList,
	BaseGeneralModel,
	NamedResourceRef,
	ResourceRef,
)
from .schema_generate import ShrinkAll, ShrinkOnlyNonRoot, model_json_schema
from .typing_ import AnalyzeResult

ANALYZER_DEFAULT_PACKAGE_NAME = 'solaris.analyze.analyzers'


def _output_all_general_model_schema(output_dir: Path, *, base_url: str) -> None:
	BaseGeneralModel.base_url = base_url
	for path, model in BaseGeneralModel.__subclasses_dict__.items():
		path = output_dir / path
		schema = model_json_schema(model)
		path.write_bytes(to_json(schema))


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
	from pydantic import Field

	return create_model(
		name,
		**{
			k: (str, Field(field_title_generator=lambda k, __: f'{k} Path'))
			for k in data.keys()
		},  # type: ignore
	)


def analyze_result_to_json(
	results: Sequence[AnalyzeResult],
	*,
	metadata: ApiMetadata,
	schema_output_dir: str | Path,
	data_output_dir: str | Path,
	base_output_dir: str | Path = '.',
	merge_json_table: bool = False,
) -> None:
	"""分析数据并输出到JSON文件"""
	version = metadata.api_version
	base_url = metadata.api_url.rstrip('/')
	data_url = '/'.join(str(i) for i in [base_url, data_output_dir, version])
	schema_url = '/'.join(str(i) for i in [base_url, schema_output_dir, version])
	ResourceRef.base_data_url = data_url

	data_output_dir = Path().joinpath(
		base_output_dir,
		data_output_dir,
		version,
	)
	data_output_dir.mkdir(parents=True, exist_ok=True)
	schema_output_dir = Path().joinpath(
		base_output_dir,
		schema_output_dir,
		version,
	)
	schema_output_dir.mkdir(parents=True, exist_ok=True)
	_output_all_general_model_schema(
		schema_output_dir,
		base_url=schema_url,
	)

	def output_json_and_schema(
		*paths: Path | str,
		data: Any,
		schema_generator: type[GenerateJsonSchema] = ShrinkOnlyNonRoot,
	) -> None:
		if isinstance(data, TypeAdapter):
			schema = data.json_schema(schema_generator=schema_generator)
		elif isinstance(data, BaseModel):
			schema = model_json_schema(type(data), schema_generator=schema_generator)
		else:
			schema = data

		data_output_dir.joinpath(*paths).write_bytes(to_json(data))
		schema_output_dir.joinpath(*paths).write_bytes(to_json(schema))

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
			output_json_and_schema(f'{resource_name}.json', data=data)
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
			schema_path.parent.mkdir(parents=True, exist_ok=True)
			schema_path.write_bytes(to_json(schema))

			# 输出ApiResourceList
			api_resource_list = _generate_api_resource_list(result)
			output_json_and_schema(
				resource_name,
				'index.json',
				data=api_resource_list,
				schema_generator=ShrinkAll,
			)

		for path, data in output_paths.items():
			path.parent.mkdir(parents=True, exist_ok=True)
			path.write_bytes(to_json(data))

		index_data[resource_name] = '/'.join([data_url, resource_name])

	# 输出metadata
	output_json_and_schema('metadata.json', data=metadata)

	if not merge_json_table:  # 输出根目录 index.json
		path = data_output_dir.joinpath('index.json')
		path.write_bytes(to_json(index_data))
		schema_path = schema_output_dir.joinpath('index.json')
		index_model = _create_index_model('Index', index_data)
		schema_path.write_bytes(to_json(model_json_schema(index_model)))


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

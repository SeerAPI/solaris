from collections.abc import Sequence
from pathlib import Path

from seerapi_models.metadata import ApiMetadata
from tqdm import tqdm

from solaris.utils import import_all_classes

from .base import BaseAnalyzer
from .db import DBManager
from .output import DBOutputter, JsonOutputter
from .typing_ import AnalyzeResult

ANALYZER_DEFAULT_PACKAGE_NAME = 'solaris.analyze.analyzers'

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
	"""分析数据并输出到JSON文件（向后兼容的函数包装）"""
	outputter = JsonOutputter(
		metadata=metadata,
		base_output_dir=base_output_dir,
		schema_output_dir=schema_output_dir,
		base_schema_url=base_schema_url,
		data_output_dir=data_output_dir,
		base_data_url=base_data_url,
	)
	outputter.run(results, merge_json_table=merge_json_table)


def analyze_result_to_db(
	results: Sequence[AnalyzeResult],
	*,
	metadata: ApiMetadata,
	db_url: str = 'sqlite:///solaris.db',
) -> None:
	"""分析数据并输出到数据库（向后兼容的函数包装）"""
	outputter = DBOutputter(
		metadata=metadata,
		db_url=db_url,
		echo=False,
	)
	outputter.init()
	outputter.run(results)


def import_analyzer_classes(
	package_name: str = ANALYZER_DEFAULT_PACKAGE_NAME,
) -> list[type[BaseAnalyzer]]:
	return import_all_classes(package_name, BaseAnalyzer)


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

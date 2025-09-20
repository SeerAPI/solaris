from pathlib import Path

from solaris.parse.base import BaseParser
from solaris.utils import change_workdir, import_all_classes

PARSER_DEFAULT_PACKAGE_NAME = 'solaris.parse.parsers'


def import_parser_classes(
	package_name: str = PARSER_DEFAULT_PACKAGE_NAME,
) -> list[type[BaseParser]]:
	"""导入包下的所有解析器类

	Args:
		package_name: 包名，默认为 "solaris.parse.parsers"

	Returns:
		解析器类列表
	"""
	return import_all_classes(
		package_name,
		BaseParser,
	)


def run_all_parser(
	parser_classes: list[type[BaseParser]],
	source_dir: Path,
	output_dir: Path,
) -> None:
	"""运行所有解析器

	Args:
		parser_classes: 解析器类列表
		source_dir: 源配置文件目录
		output_dir: 解析结果输出目录
	"""

	parsed_data = {}
	with change_workdir(source_dir):
		for parser_cls in parser_classes:
			parser = parser_cls()
			data = parser.load_source_config()
			parsed_data[parser_cls] = parser.parse(data)

	with change_workdir(output_dir):
		for parser_cls in parser_classes:
			parser = parser_cls()
			parser.save_parsed_config(parsed_data[parser_cls])


__all__ = [
	'BaseParser',
	'import_parser_classes',
	'run_all_parser',
]

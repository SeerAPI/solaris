from collections.abc import Sequence
from pathlib import Path

import click

from solaris.parse import import_parser_classes, run_all_parser
from solaris.parse.base import BaseParser


def format_parsers(parser_classes: Sequence[type[BaseParser]]) -> str:
	""""""
	source_filenames: list[str] = []
	parsed_filenames: list[str] = []
	module_names: list[str] = []

	for parser_class in parser_classes:
		source_filenames.append(parser_class.source_config_filename())
		parsed_filenames.append(parser_class.parsed_config_filename())
		module_names.append(parser_class.__module__)

	string = f'找到 {len(parser_classes)} 个 parser:\n'
	max_source_len = max(
		map(len, source_filenames), default=0
	)  # 对齐source_config_filename
	max_parsed_len = max(
		map(len, parsed_filenames), default=0
	)  # 对齐parsed_config_filename
	for source_filename, parsed_filename, module_name in zip(
		source_filenames,
		parsed_filenames,
		module_names,
	):
		string += '\n'.join(
			[
				f'{source_filename.ljust(max_source_len)} -> '
				f'{parsed_filename.ljust(max_parsed_len)}'
				f'    {module_name}\n'
			]
		)
	return string


@click.command()
@click.option(
	'--source-dir',
	type=click.Path(
		exists=True,
		dir_okay=True,
		file_okay=False,
		path_type=Path,
	),
	default='source',
)
@click.option(
	'--output-dir',
	type=click.Path(
		exists=False,
		dir_okay=True,
		file_okay=False,
		path_type=Path,
	),
	default='output',
)
@click.option(
	'--package-name',
	type=str,
	multiple=True,
	default=('solaris.parse.parsers',),
	show_default=True,
	help='解析器所在的包名',
)
@click.option('-l', '--list-parsers', is_flag=True, help='输出解析器信息')
def parse(
	source_dir: Path,
	output_dir: Path,
	package_name: tuple[str, ...],
	list_parsers: bool,
) -> None:
	parser_classes = []
	for name in package_name:
		parser_classes.extend(import_parser_classes(name))

	if list_parsers:
		click.echo(format_parsers(parser_classes))
		return

	run_all_parser(parser_classes, source_dir, output_dir)

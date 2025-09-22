from pathlib import Path
from typing import TypeVar

import click

from solaris.analyze import (
	analyze_result_to_db,
	analyze_result_to_json,
	import_analyzer_classes,
	run_all_analyzer,
)
from solaris.analyze.base import (
	BaseAnalyzer,
	DataImportConfig,
	DataSourceDirSettings,
)
from solaris.analyze.model import ApiMetadata
from solaris.settings import BaseSettings, CreateSettingsError

TSettings = TypeVar('TSettings', bound=BaseSettings)


def create_settings(
	ctx: click.Context,
	settings_class: type[TSettings],
	*,
	msg_maps: dict[str, str] | None = None,
	**init_kwargs,
) -> TSettings:
	try:
		settings = settings_class.create_settings(
			msg_maps=msg_maps,
			**init_kwargs,
		)
	except CreateSettingsError as e:
		ctx.fail('\n    ' + e.message.replace('\n', '\n    '))

	return settings


@click.command()
@click.option(
	'-w',
	'--source-dir',
	type=click.Path(file_okay=False, dir_okay=True, exists=True),
	default=None,
	help='数据源目录，如果未指定，则尝试使用环境变量 SOLARIS_DATA_BASE_DIR 的值，'
	'如果均不存在，则使用./source 目录',
)
@click.option(
	'-o',
	'--output-mode',
	type=click.Choice(('json', 'db', 'all')),
	default='json',
	show_default=True,
	help='输出模式，json: 输出JSON表，db: 输出到数据库，all: 两者都输出',
)
@click.option(
	'--json-output-dir',
	type=click.Path(file_okay=False, dir_okay=True),
	default='data',
	show_default=True,
	help='JSON表输出目录，仅在 --output-mode 为 json 或 all 时有效',
)
@click.option(
	'--schema-output-dir',
	type=click.Path(file_okay=False, dir_okay=True),
	default='schema',
	show_default=True,
	help='JSON Schema 输出目录，仅在 --output-mode 为 json 或 all 时有效',
)
@click.option(
	'-d',
	'--db-url',
	type=str,
	default='solaris.db',
	show_default=True,
	help='数据库URL，仅在 --output-mode 为 db 或 all 时有效',
)
@click.option(
	'--api-url',
	type=str,
	default=None,
	help='指定API基础URL，该值会作为基础URL与JSON表中的路径拼接，同时写入到metadata.url，'
	'如果未指定，则尝试使用环境变量 SOLARIS_API_URL 的值',
)
@click.option(
	'--api-version',
	type=str,
	default=None,
	help='指定API版本 (例如"v1beta")，该值会作为API URL中的版本号部分，'
	'并写入到metadata.api_version，如果未指定，'
	'则尝试使用环境变量 SOLARIS_API_VERSION 的值',
)
@click.option(
	'--package-name',
	type=str,
	multiple=True,
	default=('solaris.analyze.analyzers',),
	show_default=True,
	help='要导入的分析器包名',
)
@click.option(
	'-l',
	'--list-analyzers',
	is_flag=True,
	help='输出分析器信息并退出',
)
@click.pass_context
def analyze(
	ctx: click.Context,
	source_dir: str | None,
	output_mode: str,
	json_output_dir: str,
	schema_output_dir: str,
	db_url: str,
	api_url: str | None,
	api_version: str | None,
	list_analyzers: bool,
	package_name: tuple[str, ...],
) -> None:
	analyzer_classes: list[type[BaseAnalyzer]] = []
	for name in package_name:
		analyzer_classes.extend(import_analyzer_classes(name))

	ctx.obj['analyzer_classes'] = analyzer_classes

	if list_analyzers:
		string = f'找到 {len(analyzer_classes)} 个分析器:\n'
		string += '\n'.join(
			analyzer_class.get_list_info()
			for analyzer_class in analyzer_classes
		)
		click.echo(string)
		return

	settings = DataSourceDirSettings()
	if source_dir:
		settings.BASE_DIR = Path(source_dir)

	DataImportConfig.set_source_dir(settings)
	metadata = create_settings(
		ctx,
		ApiMetadata,
		msg_maps={
			'api_url': (
				'未获取到有效的API URL，请使用 --api-url 指定，'
				'或设置环境变量 SOLARIS_API_URL'
			),
			'api_version': (
				'未获取到有效的API版本，请使用 --api-version 指定，'
				'或设置环境变量 SOLARIS_API_VERSION'
			),
		},
		api_url=api_url,
		api_version=api_version,
	)

	results = run_all_analyzer(analyzer_classes)
	if output_mode in ('json', 'all'):
		analyze_result_to_json(
			results,
			schema_output_dir=schema_output_dir,
			data_output_dir=json_output_dir,
			metadata=metadata,
		)
	if output_mode in ('db', 'all'):
		analyze_result_to_db(
			results,
			metadata=metadata,
			db_url=db_url,
		)

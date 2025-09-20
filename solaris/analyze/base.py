from abc import ABC, abstractmethod
from collections.abc import Callable
from dataclasses import KW_ONLY, dataclass, field
import json
from pathlib import Path
from typing import Any, ClassVar, cast
from typing_extensions import Self

from pydantic import model_validator

from solaris.settings import ENV_PREFIX, SETTINGS_CONFIG, BaseSettings
from solaris.typing import JSON, Paths
from solaris.utils import get_nested_value

from .typing_ import (
	AnalyzeData,
	AnalyzeResult,
	DataSourceType,
	JSONObject,
	Patch,
)


class DataSourceDirSettings(BaseSettings):
	model_config = SETTINGS_CONFIG | {'env_prefix': f'{ENV_PREFIX}DATA_'}
	BASE_DIR: Path = Path('./source')
	PATCH_DIR: Path = Path(BASE_DIR, 'patch')
	HTML5_DIR: Path = Path(BASE_DIR, 'html5')
	UNITY_DIR: Path = Path(BASE_DIR, 'unity')
	FLASH_DIR: Path = Path(BASE_DIR, 'flash')

	@model_validator(mode='after')
	def combine_dirs(self) -> Self:
		self.HTML5_DIR = self.HTML5_DIR
		self.PATCH_DIR = self.PATCH_DIR
		self.UNITY_DIR = self.UNITY_DIR
		self.FLASH_DIR = self.FLASH_DIR
		return self


@dataclass
class DataImportConfig:
	SOURCE_DIR_SETTINGS: ClassVar[DataSourceDirSettings] = DataSourceDirSettings()
	_: KW_ONLY
	patch_paths: Paths = field(default_factory=tuple)
	html5_paths: Paths = field(default_factory=tuple)
	unity_paths: Paths = field(default_factory=tuple)
	flash_paths: Paths = field(default_factory=tuple)

	def __post_init__(self):
		self.patch_paths = self._resolve_paths(
			self.patch_paths, self.SOURCE_DIR_SETTINGS.PATCH_DIR
		)
		self.html5_paths = self._resolve_paths(
			self.html5_paths, self.SOURCE_DIR_SETTINGS.HTML5_DIR
		)
		self.unity_paths = self._resolve_paths(
			self.unity_paths, self.SOURCE_DIR_SETTINGS.UNITY_DIR
		)
		self.flash_paths = self._resolve_paths(
			self.flash_paths, self.SOURCE_DIR_SETTINGS.FLASH_DIR
		)

	def _resolve_paths(self, paths: Paths, base_dir: Path) -> tuple[Path, ...]:
		"""将字符串路径解析为完整的Path对象"""
		return tuple(base_dir.joinpath(path) for path in paths)

	def __add__(self, other: 'DataImportConfig') -> 'DataImportConfig':
		return DataImportConfig(
			patch_paths=self.patch_paths + other.patch_paths,
			html5_paths=self.html5_paths + other.html5_paths,
			unity_paths=self.unity_paths + other.unity_paths,
			flash_paths=self.flash_paths + other.flash_paths,
		)

	@classmethod
	def set_source_dir(cls, settings: DataSourceDirSettings) -> None:
		cls.SOURCE_DIR_SETTINGS = settings


class DataLoader(ABC):
	"""数据加载器抽象基类"""

	def __init__(self) -> None:
		super().__init__()
		import_config = self.get_data_import_config()
		base_dirs: DataSourceDirSettings = import_config.SOURCE_DIR_SETTINGS
		self.data: AnalyzeData = {
			'html5': self._load_data_by_category(
				import_config.html5_paths, base_dirs.HTML5_DIR, self._load_data
			),
			'patch': self._load_data_by_category(
				import_config.patch_paths, base_dirs.PATCH_DIR, self._load_patch
			),
			'unity': self._load_data_by_category(
				import_config.unity_paths, base_dirs.UNITY_DIR, self._load_data
			),
			'flash': self._load_data_by_category(
				import_config.flash_paths, base_dirs.FLASH_DIR, self._load_data
			),
		}

		for patch in self.data['patch'].values():
			target = patch['target']
			patch_type = patch['type']
			mode = patch['mode']
			content = patch['content']
			# 如果补丁模式为 create，则直接在指定平台中新建一条数据，
			# 如果已存在同名数据则覆盖
			if mode == 'create':
				content = self._process_create_patch_content(content)
				self.data[patch_type][target] = content
				continue
			# 如果补丁模式为 append，则将内容追加到目标数据的指定位置
			for fp, origin_data in self.data[patch_type].items():
				if target != fp:
					continue

				obj_path = patch['path']
				if (
					origin := get_nested_value(cast(dict, origin_data), obj_path)
				) is None:
					continue

				if not isinstance(origin, type(content)):
					raise ValueError(f'patch {fp} content type mismatch')
				if isinstance(origin, list) and isinstance(content, list):
					origin.extend(content)
				elif isinstance(origin, dict) and isinstance(content, dict):
					origin.update(content)

	@staticmethod
	def _load_data_by_category(
		paths: Paths, base_dir: Path, loader_func: Callable[[str | Path], Any]
	) -> dict[str, Any]:
		"""根据路径列表和加载函数加载数据"""
		return {
			str(Path(path).relative_to(base_dir)): loader_func(path) for path in paths
		}

	@classmethod
	def _load_patch(cls, path: str | Path) -> Patch:
		return cast(Patch, cls._load_data(path))

	@classmethod
	def _load_data(cls, path: str | Path) -> JSONObject:
		return json.loads(Path(path).read_text())

	@classmethod
	@abstractmethod
	def get_data_import_config(cls) -> 'DataImportConfig':
		pass

	def _get_data(self, source: DataSourceType, key: str) -> Any:
		if not (sub := self.data.get(source)):
			raise ValueError(f'data.{source} is required')
		if not (sub := sub.get(key)):
			raise ValueError(f'data.{source}.{key} is required')
		return sub

	@staticmethod
	def _process_create_patch_content(content: JSON) -> JSONObject:
		"""处理补丁 context，将内容转换为以ID为键的字典格式

		Args:
			content: 输入的JSON内容，可以是字典或列表

		Returns:
			JSONObject: 以ID为键的字典，键为整数类型的ID，值为原始数据

		Raises:
			ValueError: 当ID不是有效的字符串、整数或浮点数类型时抛出异常
		"""
		new_content = {}
		for i, v in enumerate(
			content.values() if isinstance(content, dict) else content
		):
			if isinstance(v, dict):
				id_ = v.get('id') or v.get('ID') or i
			else:
				id_ = i

			if not isinstance(id_, (str, int, float)):
				raise ValueError(f'invalid id: {id_}')

			new_content[int(id_)] = v

		return new_content


class BaseAnalyzer(DataLoader):
	"""分析器抽象基类"""

	@abstractmethod
	def analyze(self) -> tuple[AnalyzeResult, ...]:
		pass

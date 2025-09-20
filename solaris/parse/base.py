from abc import ABC, abstractmethod
import os
from typing import Generic, TypeVar

from solaris.utils import to_json

T = TypeVar('T')


class BaseParser(ABC, Generic[T]):
	"""解析器基类"""

	def load_source_config(self) -> bytes:
		"""加载源配置文件"""
		filename = self.source_config_filename()
		if not os.path.exists(filename):
			raise FileNotFoundError(
				f'配置文件不存在: {filename}，'
				f'请检查工作目录和设置的文件名是否正确'
				f'工作目录: {os.getcwd()}'
			)
		with open(filename, 'rb') as f:
			return f.read()

	def save_parsed_config(self, data: T) -> None:
		"""保存解析后的配置文件"""
		filename = self.parsed_config_filename()
		with open(filename, 'wb') as f:
			f.write(to_json(data))

	@classmethod
	@abstractmethod
	def source_config_filename(cls) -> str:
		"""源配置文件名"""
		pass

	@classmethod
	@abstractmethod
	def parsed_config_filename(cls) -> str:
		"""解析后的配置文件名"""
		pass

	@abstractmethod
	def parse(self, data: bytes) -> T:
		"""解析数据"""
		pass


__all__ = ['BaseParser']

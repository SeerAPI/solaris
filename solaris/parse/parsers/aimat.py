from typing import TypedDict

from ..base import BaseParser
from ..bytes_reader import BytesReader


class ItemItem(TypedDict):
	id: int
	state: int
	type: int


class _Root(TypedDict):
	"""根数据结构"""

	item: list[ItemItem]


class _Data(TypedDict):
	"""顶层数据结构"""

	root: _Root


class AimatParser(BaseParser[_Data]):
	@classmethod
	def source_config_filename(cls) -> str:
		return 'aimat.bytes'

	@classmethod
	def parsed_config_filename(cls) -> str:
		return 'aimat.json'

	def parse(self, data: bytes) -> _Data:
		reader = BytesReader(data)
		result: _Data = {'root': {'item': []}}

		# 检查根数据是否存在
		if not reader.ReadBoolean():
			return result

		# 检查项目数组是否存在
		if not reader.ReadBoolean():
			return result

		# 读取项目数量
		count = reader.ReadSignedInt()

		# 读取每个项目
		for _ in range(count):
			item: ItemItem = {
				'id': reader.ReadSignedInt(),
				'state': reader.ReadSignedInt(),
				'type': reader.ReadSignedInt(),
			}
			result['root']['item'].append(item)

		return result

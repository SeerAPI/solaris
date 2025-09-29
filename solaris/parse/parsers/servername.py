from typing import TypedDict

from ..base import BaseParser
from ..bytes_reader import BytesReader


class ServerNameItem(TypedDict):
	"""服务器名称项"""

	id: int
	name: str


class _ServerNameRoot(TypedDict):
	"""服务器名称根节点"""

	list: list[ServerNameItem]  # 对应 C# 的 list 字段


class _ServerNameData(TypedDict):
	"""服务器名称顶层数据"""

	root: _ServerNameRoot


class ServernameParser(BaseParser[_ServerNameData]):
	"""服务器名称配置解析器"""

	@classmethod
	def source_config_filename(cls) -> str:
		return 'servername.bytes'

	@classmethod
	def parsed_config_filename(cls) -> str:
		return 'servername.json'

	def parse(self, data: bytes) -> _ServerNameData:
		reader = BytesReader(data)
		result: _ServerNameData = {'root': {'list': []}}

		# 检查header - 根据IRootInterface.Parse逻辑
		if not reader.ReadBoolean():
			return result

		# 检查是否有list数据 - 根据IRoot.Parse逻辑
		if reader.ReadBoolean():
			count = reader.ReadSignedInt()

			for _ in range(count):
				# 按照IListItem.Parse的顺序读取字段
				id = reader.ReadSignedInt()
				name = reader.ReadUTFBytesWithLength()

				item = ServerNameItem(id=id, name=name)
				result['root']['list'].append(item)

		return result

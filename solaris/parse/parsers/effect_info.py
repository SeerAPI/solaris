from typing import TypedDict

from ..base import BaseParser
from ..bytes_reader import BytesReader


# 参数类型项结构定义
class ParamTypeItem(TypedDict):
	"""参数类型项数据结构"""

	id: int
	params: str


# 效果信息项结构定义
class EffectInfoItem(TypedDict):
	"""效果信息项数据结构"""

	info: str
	param: list[int]  # 可选数组，优先使用空列表而不是None
	args_num: int
	id: int


# 内部根结构
class _Root(TypedDict):
	effect: list[EffectInfoItem]
	param_type: list[ParamTypeItem]


# 顶层数据结构
class _Data(TypedDict):
	root: _Root


# 效果信息Parser实现
class EffectInfoParser(BaseParser[_Data]):
	"""解析效果信息配置数据"""

	@classmethod
	def source_config_filename(cls) -> str:
		return 'effectInfo.bytes'

	@classmethod
	def parsed_config_filename(cls) -> str:
		return 'effectInfo.json'

	def parse(self, data: bytes) -> _Data:
		reader = BytesReader(data)
		result: _Data = {'root': {'effect': [], 'param_type': []}}

		# 检查根布尔标志
		if not reader.read_bool():
			return result

		# 读取Effect数组
		if reader.read_bool():
			effect_count = reader.read_i32()
			for _ in range(effect_count):
				# 按照C#解析顺序读取字段
				args_num = reader.read_i32()  # argsNum
				effect_id = reader.read_i32()  # id
				info = reader.ReadUTFBytesWithLength()

				# 处理可选的param数组
				param: list[int] = []
				if reader.read_bool():
					param_count = reader.read_i32()
					param = [reader.read_i32() for _ in range(param_count)]

				effect_item: EffectInfoItem = {
					'info': info,
					'param': param,
					'args_num': args_num,
					'id': effect_id,
				}
				result['root']['effect'].append(effect_item)

		# 读取ParamType数组
		if reader.read_bool():
			param_type_count = reader.read_i32()
			for _ in range(param_type_count):
				param_type_item: ParamTypeItem = {
					'id': reader.read_i32(),
					'params': reader.ReadUTFBytesWithLength(),
				}
				result['root']['param_type'].append(param_type_item)

		return result

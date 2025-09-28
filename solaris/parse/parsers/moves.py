from typing import TypedDict

from ..base import BaseParser
from ..bytes_reader import BytesReader


# 基础招式项结构
class MoveItem(TypedDict):
	atk_num: int
	atk_type: int
	category: int
	friend_side_effect: list[int]
	friend_side_effect_arg: list[int]
	id: int
	max_pp: int
	mon_id: int
	must_hit: int
	name: str
	power: int
	priority: int
	side_effect: list[int]
	side_effect_arg: list[int]
	type: int
	info: str
	ordinary: int


# 招式集合内部结构
class _Moves(TypedDict):
	move: list[MoveItem]
	text: str


# 招式表内部结构
class _MovesTbl(TypedDict):
	moves: _Moves | None


# 招式数据根结构
class MovesData(TypedDict):
	root: _MovesTbl | None


# 招式描述项结构
class FgtvDesMoveItem(TypedDict):
	fgtv_des: str
	id: int


# 招式描述根内部结构
class _FgtvDesRoot(TypedDict):
	move: list[FgtvDesMoveItem]


# 招式描述数据结构
class MoveFgtvDesData(TypedDict):
	root: _FgtvDesRoot | None


class MovesParser(BaseParser[MovesData]):
	"""基础招式解析器"""

	@classmethod
	def source_config_filename(cls) -> str:
		return 'moves.bytes'

	@classmethod
	def parsed_config_filename(cls) -> str:
		return 'moves.json'

	def parse(self, data: bytes) -> MovesData:
		reader = BytesReader(data)
		result: MovesData = {'root': None}

		# 检查是否有MovesTbl数据
		if reader.ReadBoolean():
			moves_tbl: _MovesTbl = {'moves': None}

			# 检查是否有Moves数据
			if reader.ReadBoolean():
				moves: _Moves = {'move': [], 'text': ''}

				# 检查是否有Move数组数据
				if reader.ReadBoolean():
					move_count = reader.ReadSignedInt()

					# 循环读取每个MoveItem
					for _ in range(move_count):
						move_item: MoveItem = {
							'atk_num': reader.ReadSignedInt(),
							'atk_type': reader.ReadSignedInt(),
							'category': reader.ReadSignedInt(),
							'friend_side_effect': [],
							'friend_side_effect_arg': [],
							'id': 0,
							'max_pp': 0,
							'mon_id': 0,
							'must_hit': 0,
							'name': '',
							'power': 0,
							'priority': 0,
							'side_effect': [],
							'side_effect_arg': [],
							'type': 0,
							'info': '',
							'ordinary': 0
						}

						# 读取可选的FriendSideEffect数组
						if reader.ReadBoolean():
							friend_se_count = reader.ReadSignedInt()
							move_item['friend_side_effect'] = [
								reader.ReadSignedInt()
								for _ in range(friend_se_count)
							]

						# 读取可选的FriendSideEffectArg数组
						if reader.ReadBoolean():
							friend_se_arg_count = reader.ReadSignedInt()
							move_item['friend_side_effect_arg'] = [
								reader.ReadSignedInt()
								for _ in range(friend_se_arg_count)
							]

						# 继续读取基础字段
						move_item['id'] = reader.ReadSignedInt()
						move_item['max_pp'] = reader.ReadSignedInt()
						move_item['mon_id'] = reader.ReadSignedInt()
						move_item['must_hit'] = reader.ReadSignedInt()
						move_item['name'] = reader.ReadUTFBytesWithLength()
						move_item['power'] = reader.ReadSignedInt()
						move_item['priority'] = reader.ReadSignedInt()

						# 读取可选的SideEffect数组
						if reader.ReadBoolean():
							se_count = reader.ReadSignedInt()
							move_item['side_effect'] = [
								reader.ReadSignedInt()
								for _ in range(se_count)
							]

						# 读取可选的SideEffectArg数组
						if reader.ReadBoolean():
							se_arg_count = reader.ReadSignedInt()
							move_item['side_effect_arg'] = [
								reader.ReadSignedInt()
								for _ in range(se_arg_count)
							]

						# 完成剩余字段
						move_item['type'] = reader.ReadSignedInt()
						move_item['info'] = reader.ReadUTFBytesWithLength()
						move_item['ordinary'] = reader.ReadSignedInt()

						moves['move'].append(move_item)

				# 读取_text字段
				moves['text'] = reader.ReadUTFBytesWithLength()
				moves_tbl['moves'] = moves

			result['root'] = moves_tbl

		return result


class MoveFgtvDesParser(BaseParser[MoveFgtvDesData]):
	"""招式描述解析器"""

	@classmethod
	def source_config_filename(cls) -> str:
		return 'MoveFgtvDes.bytes'

	@classmethod
	def parsed_config_filename(cls) -> str:
		return 'moveFgtvDes.json'

	def parse(self, data: bytes) -> MoveFgtvDesData:
		reader = BytesReader(data)
		result: MoveFgtvDesData = {'root': None}

		# 检查是否有root数据
		if reader.ReadBoolean():
			root: _FgtvDesRoot = {'move': []}

			# 检查是否有Move数组数据
			if reader.ReadBoolean():
				move_count = reader.ReadSignedInt()

				# 循环读取每个MoveItem
				for _ in range(move_count):
					move_item: FgtvDesMoveItem = {
						'fgtv_des': reader.ReadUTFBytesWithLength(),
						'id': reader.ReadSignedInt()
					}
					root['move'].append(move_item)

			result['root'] = root

		return result

# 技能变更项结构
class MovesItem(TypedDict):
	move_id: int
	new_name: str
	skin_id: int
	move_name1: str
	move_name2: str


# 技能变更内部结构
class _Move(TypedDict):
	moves: list[MovesItem]


# 技能变更数据根结构
class MoveChangeData(TypedDict):
	root: _Move | None


class MoveChangeParser(BaseParser[MoveChangeData]):
	"""技能变更解析器"""

	@classmethod
	def source_config_filename(cls) -> str:
		return 'move_change.bytes'

	@classmethod
	def parsed_config_filename(cls) -> str:
		return 'moveChange.json'

	def parse(self, data: bytes) -> MoveChangeData:
		reader = BytesReader(data)
		result: MoveChangeData = {'root': None}

		# 检查是否有Move数据
		if reader.ReadBoolean():
			move: _Move = {'moves': []}

			# 检查是否有Moves数组数据
			if reader.ReadBoolean():
				moves_count = reader.ReadSignedInt()

				# 循环读取每个MovesItem
				for _ in range(moves_count):
					moves_item: MovesItem = {
						'move_id': reader.ReadSignedInt(),
						'new_name': reader.ReadUTFBytesWithLength(),
						'skin_id': reader.ReadSignedInt(),
						'move_name1': reader.ReadUTFBytesWithLength(),
						'move_name2': reader.ReadUTFBytesWithLength()
					}
					move['moves'].append(moves_item)

			result['root'] = move

		return result

from typing import TypedDict

from solaris.parse.bytes_reader import BytesReader

from ..base import BaseParser


class SkillType(TypedDict):
	id: int
	is_dou: int
	cn: str
	en: list[str]
	att: str


class _Root(TypedDict):
	item: list[SkillType]


class _Data(TypedDict):
	root: _Root


class SkillTypeParser(BaseParser[_Data]):
	@classmethod
	def source_config_filename(cls) -> str:
		return 'skillTypes.bytes'

	@classmethod
	def parsed_config_filename(cls) -> str:
		return 'skillType.json'

	def parse(self, data: bytes) -> _Data:
		reader = BytesReader(data)
		result: _Data = {'root': {'item': []}}
		if not (reader.ReadBoolean() and reader.ReadBoolean()):
			return result

		num = reader.ReadSignedInt()
		for _ in range(num):
			item: SkillType = {
				'att': reader.ReadUTFBytesWithLength(),
				'cn': reader.ReadUTFBytesWithLength(),
				'en': [
					reader.ReadUTFBytesWithLength()
					for _ in range(reader.ReadSignedInt())
				]
				if reader.ReadBoolean()
				else [],
				'id': reader.ReadSignedInt(),
				'is_dou': reader.ReadSignedInt(),
			}
			result['root']['item'].append(item)

		return result

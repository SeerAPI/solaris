from typing import TypedDict

from ..base import BaseParser
from ..bytes_reader import BytesReader


class ArchivesBook(TypedDict):
	bookid: int
	chapterid: int
	chaptername: str
	id: int
	txt: str
	txtdivide: str


class _ArchivesBookConfig(TypedDict):
	data: list[ArchivesBook]


class ArchivesBookParser(BaseParser[_ArchivesBookConfig]):
	@classmethod
	def source_config_filename(cls) -> str:
		return 'archivesbook.bytes'

	@classmethod
	def parsed_config_filename(cls) -> str:
		return 'archivesBook.json'

	def parse(self, data: bytes) -> _ArchivesBookConfig:
		reader = BytesReader(data)
		if not reader.read_bool():
			return _ArchivesBookConfig(data=[])

		result = _ArchivesBookConfig(data=[])
		for _ in range(reader.read_i32()):
			bookid = reader.read_i32()
			chapterid = reader.read_i32()
			chaptername_len = reader.read_u16()
			chaptername = reader.read_utf(chaptername_len)
			id = reader.read_i32()
			txt = []
			if reader.read_bool():
				txt_count = reader.read_i32()
				txt = [reader.read_utf(reader.read_u16()) for _ in range(txt_count)]

			txtdivide = []
			if reader.read_bool():
				txtdivide_count = reader.read_i32()
				txtdivide = [reader.read_i32() for _ in range(txtdivide_count)]

			result['data'].append(
				ArchivesBook(
					bookid=bookid,
					chapterid=chapterid,
					chaptername=chaptername,
					id=id,
					txt='|'.join(txt),
					txtdivide='|'.join(map(str, txtdivide)),
				)
			)

		return result


class ArchivesStoryInfo(TypedDict):
	classid: int
	classname: str
	id: int
	isrec: int
	monid: int
	monname: str
	samemonid: str | None
	storyid: int
	txt: str


class _ArchivesStoryData(TypedDict):
	data: list[ArchivesStoryInfo]


class ArchivesStoryInfoParser(BaseParser[_ArchivesStoryData]):
	@classmethod
	def source_config_filename(cls) -> str:
		return 'archivesstory.bytes'

	@classmethod
	def parsed_config_filename(cls) -> str:
		return 'archivesStory.json'

	def parse(self, data: bytes) -> _ArchivesStoryData:
		result = _ArchivesStoryData(data=[])
		reader = BytesReader(data)
		if not reader.read_bool():
			return result

		for _ in range(reader.read_i32()):
			story_info = ArchivesStoryInfo(
				classid=reader.read_i32(),
				classname=reader.read_utf(reader.read_u16()),
				id=reader.read_i32(),
				isrec=reader.read_i32(),
				monid=reader.read_i32(),
				monname=reader.read_utf(reader.read_u16()),
				samemonid=(
					'_'.join(str(reader.read_i32()) for _ in range(reader.read_i32()))
					if reader.read_bool()
					else None
				),
				storyid=reader.read_i32(),
				txt=reader.read_utf(reader.read_u16()),
			)
			result['data'].append(story_info)

		return result

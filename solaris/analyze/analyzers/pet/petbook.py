import re
from typing import TYPE_CHECKING, Any

from sqlmodel import Field, Relationship

from solaris.analyze.model import (
	BaseCategoryModel,
	BaseResModel,
	ConvertToORM,
	ResourceRef,
)
from solaris.analyze.typing_ import AnalyzeResult
from solaris.analyze.utils import create_category_map

from ._general import BasePetAnalyzer

if TYPE_CHECKING:
	from .pet import Pet, PetORM


class PetEncyclopediaEntryBase(BaseResModel):
	id: int = Field(primary_key=True, description='精灵图鉴ID', foreign_key='pet.id')
	name: str = Field(description='精灵名称')
	has_sound: bool = Field(description='精灵是否存在叫声')
	height: float | None = Field(
		default=None,
		description="精灵身高，当这个值在图鉴中为'未知'时，这个值为null",
	)
	weight: float | None = Field(
		default=None,
		description="精灵重量，当这个值在图鉴中为'未知'时，这个值为null",
	)
	foundin: str | None = Field(default=None, description='精灵发现地点')
	food: str | None = Field(default=None, description='精灵喜爱的食物')
	introduction: str = Field(description='精灵介绍')

	@classmethod
	def resource_name(cls) -> str:
		return 'pet_encyclopedia_entry'


class PetEncyclopediaEntry(
	PetEncyclopediaEntryBase, ConvertToORM['PetEncyclopediaEntryORM']
):
	pet: ResourceRef['Pet'] = Field(description='精灵')

	@classmethod
	def get_orm_model(cls) -> type['PetEncyclopediaEntryORM']:
		return PetEncyclopediaEntryORM

	def to_orm(self) -> 'PetEncyclopediaEntryORM':
		return PetEncyclopediaEntryORM(
			id=self.id,
			name=self.name,
			has_sound=self.has_sound,
			height=self.height,
			weight=self.weight,
			foundin=self.foundin,
			food=self.food,
			introduction=self.introduction,
		)


class PetEncyclopediaEntryORM(PetEncyclopediaEntryBase, table=True):
	pet: 'PetORM' = Relationship(back_populates='encyclopedia')


class PetArchiveStoryEntryBase(BaseResModel):
	id: int = Field(primary_key=True, description='故事条目ID')
	content: str = Field(description='故事条目内容')

	@classmethod
	def resource_name(cls) -> str:
		return 'pet_archive_story_entry'


class PetArchiveStoryEntry(
	PetArchiveStoryEntryBase, ConvertToORM['PetArchiveStoryEntryORM']
):
	pet: ResourceRef['Pet'] = Field(description='精灵')
	book: ResourceRef['PetArchiveStoryBook'] = Field(description='故事')

	@classmethod
	def get_orm_model(cls) -> type['PetArchiveStoryEntryORM']:
		return PetArchiveStoryEntryORM

	def to_orm(self) -> 'PetArchiveStoryEntryORM':
		return PetArchiveStoryEntryORM(
			id=self.id, content=self.content, pet_id=self.pet.id, book_id=self.book.id
		)


class PetArchiveStoryEntryORM(PetArchiveStoryEntryBase, table=True):
	pet_id: int = Field(description='精灵ID', foreign_key='pet.id')
	pet: 'PetORM' = Relationship(back_populates='archive_story')
	book_id: int = Field(
		foreign_key='pet_archive_story_book.id',
	)
	book: 'PetArchiveStoryBookORM' = Relationship(back_populates='entries')


class PetArchiveStoryBookBase(BaseCategoryModel):
	name: str = Field(description='故事名称')

	@classmethod
	def resource_name(cls) -> str:
		return 'pet_archive_story_book'


class PetArchiveStoryBook(
	PetArchiveStoryBookBase, ConvertToORM['PetArchiveStoryBookORM']
):
	entries: list[ResourceRef[PetArchiveStoryEntryBase]] = Field(
		default_factory=list, description='故事条目'
	)

	@classmethod
	def get_orm_model(cls) -> type['PetArchiveStoryBookORM']:
		return PetArchiveStoryBookORM

	def to_orm(self) -> 'PetArchiveStoryBookORM':
		return PetArchiveStoryBookORM(
			id=self.id,
			name=self.name,
		)


class PetArchiveStoryBookORM(PetArchiveStoryBookBase, table=True):
	entries: list[PetArchiveStoryEntryORM] = Relationship(back_populates='book')


def get_height_or_weight(text: Any) -> float | None:
	if not text:
		return None
	if isinstance(text, (int, float)):
		return text

	match = re.findall(r'-?\d+\.\d+|-?\d+', text)
	if not match:
		return None

	return float(match[0])


class PetEncyclopediaAnalyzer(BasePetAnalyzer):
	def analyze(self) -> tuple[AnalyzeResult, ...]:
		results = {}
		for id_, data in self.pet_encyclopedia_data.items():
			food = data.get('Food', '未知')
			if food == '未知':
				food = None
			foundin = data.get('Foundin', '--')
			if foundin == '--':
				foundin = None

			height = get_height_or_weight(data.get('Height', 0))
			weight = get_height_or_weight(data.get('Weight', 0))
			entry = PetEncyclopediaEntry(
				id=id_,
				name=data['DefName'],
				has_sound=bool(data.get('hasSound')),
				height=height,
				weight=weight,
				foundin=foundin,
				food=food,
				introduction=data.get('Features', ''),
				pet=ResourceRef(id=id_, resource_name='pet'),
			)
			results[id_] = entry
		return (
			AnalyzeResult(
				model=PetEncyclopediaEntry,
				data=results,
			),
		)


class PetArchiveStoryAnalyzer(BasePetAnalyzer):
	def analyze(self) -> tuple[AnalyzeResult, ...]:
		book_map = create_category_map(
			self._get_data('patch', 'pet_archive_story_book.json'),
			model_cls=PetArchiveStoryBook,
			array_key='entries',
		)
		entry_map: dict[int, PetArchiveStoryEntry] = {}
		for id_, data in self.pet_archive_story_book_data.items():
			content = data.get('txt')
			if not content:
				continue

			story_id = data['storyid']
			entry = PetArchiveStoryEntry(
				id=id_,
				content=content,
				pet=ResourceRef(id=data['monid'], resource_name='pet'),
				book=ResourceRef.from_model(PetArchiveStoryBook, id=story_id),
			)
			entry_map[id_] = entry
			ref = ResourceRef.from_model(entry)
			book_map.add_element(story_id, ref)

		return (
			AnalyzeResult(model=PetArchiveStoryEntry, data=entry_map),
			AnalyzeResult(model=PetArchiveStoryBook, data=book_map),
		)

from typing import TYPE_CHECKING, Any

from sqlmodel import Field, Relationship, SQLModel

from solaris.analyze.base import AnalyzeResult, BaseDataSourceAnalyzer, DataImportConfig
from solaris.analyze.model import (
	BaseCategoryModel,
	BaseResModel,
	ConvertToORM,
	ResourceRef,
	SkillEffectInUse,
	SkillEffectInUseORM,
)
from solaris.analyze.utils import CategoryMap

from ._general import Item, ItemORM, get_items_from_category_name

if TYPE_CHECKING:
	from ..element_type import TypeCombination, TypeCombinationORM


class SkillStoneEffectLink(SQLModel, table=True):
	"""技能石效果链接表"""

	skill_stone_category_id: int | None = Field(
		default=None, foreign_key='skill_stone_category.id', primary_key=True
	)
	effect_in_use_id: int | None = Field(
		default=None, foreign_key='skill_effect_in_use.id', primary_key=True
	)


class SkillStoneBase(BaseResModel):
	id: int = Field(primary_key=True, foreign_key='item.id', description='技能石ID')
	name: str = Field(description='技能石名称')
	rank: int = Field(description='技能石等级，1到5分别对应D, C, B, A, S')

	@classmethod
	def resource_name(cls) -> str:
		return 'skill_stone'


class SkillStone(SkillStoneBase, ConvertToORM['SkillStoneORM']):
	category: ResourceRef['SkillStoneCategory'] = Field(description='技能石分类')
	item: ResourceRef['Item'] = Field(description='技能石物品资源引用')

	@classmethod
	def get_orm_model(cls) -> type['SkillStoneORM']:
		return SkillStoneORM

	def to_orm(self) -> 'SkillStoneORM':
		return SkillStoneORM(
			id=self.id,
			name=self.name,
			rank=self.rank,
			category_id=self.category.id,
		)


class SkillStoneORM(SkillStoneBase, table=True):
	category_id: int = Field(
		description='技能石分类ID', foreign_key='skill_stone_category.id'
	)
	category: 'SkillStoneCategoryORM' = Relationship(
		back_populates='skill_stone',
	)
	item: 'ItemORM' = Relationship(
		back_populates='skill_stone',
	)


class SkillStoneCategoryBase(BaseCategoryModel):
	name: str = Field(description='技能石分类名称')

	@classmethod
	def resource_name(cls) -> str:
		return 'skill_stone_category'


class SkillStoneCategory(SkillStoneCategoryBase, ConvertToORM['SkillStoneCategoryORM']):
	skill_stone: list[ResourceRef['SkillStone']] = Field(
		default_factory=list,
		description='技能石列表',
	)
	type: ResourceRef['TypeCombination'] = Field(description='技能石类型')
	hide_effect: list['SkillEffectInUse'] = Field(
		default_factory=list,
		description='该分类技能石可获得的隐藏效果',
	)  # TODO: 需要补充隐藏效果数据

	@classmethod
	def get_orm_model(cls) -> 'type[SkillStoneCategoryORM]':
		return SkillStoneCategoryORM

	def to_orm(self) -> 'SkillStoneCategoryORM':
		return SkillStoneCategoryORM(
			id=self.id,
			name=self.name,
			type_id=self.type.id,
		)


class SkillStoneCategoryORM(SkillStoneCategoryBase, table=True):
	type_id: int = Field(
		description='技能石类型ID', foreign_key='element_type_combination.id'
	)
	type: 'TypeCombinationORM' = Relationship(
		back_populates='skill_stone_category',
	)
	skill_stone: list['SkillStoneORM'] = Relationship(
		back_populates='category',
	)
	hide_effect: list['SkillEffectInUseORM'] = Relationship(
		back_populates='skill_stone_category',
		link_model=SkillStoneEffectLink,
	)


class SkillStoneAnalyzer(BaseDataSourceAnalyzer):
	@classmethod
	def get_data_import_config(cls) -> DataImportConfig:
		return DataImportConfig(
			html5_paths=('xml/items.json',),
		)

	def analyze(self) -> tuple[AnalyzeResult, ...]:
		item_category_data = self._get_data('html5', 'xml/items.json')
		skill_stone_data: dict[int, Any] = {
			stone['ID']: stone
			for stone in get_items_from_category_name(
				item_category_data, category_name='技能石'
			)['Item']
		}

		category_id = 1
		category_type_set = set()
		skill_stone_map: dict[int, SkillStone] = {}
		skill_stone_category_map: CategoryMap[int, SkillStoneCategory, SkillStone] = (
			CategoryMap('skill_stone')
		)
		for id_, skill_stone in skill_stone_data.items():
			item_ref = ResourceRef.from_model(Item, id=id_)
			category_name = skill_stone['Name'][2:]
			type_id = skill_stone['Type']
			if type_id not in category_type_set:
				category_type_set.add(type_id)
				skill_stone_category_map[category_id] = SkillStoneCategory(
					id=category_id,
					name=category_name,
					type=ResourceRef(
						id=type_id,
						resource_name='element_type_combination',
					),
				)
				category_id += 1

			category = skill_stone_category_map[category_id - 1]
			skill_stone_obj = SkillStone(
				id=id_,
				name=skill_stone['Name'],
				rank=skill_stone['Rank'],
				item=item_ref,
				category=ResourceRef.from_model(category),
			)
			category.skill_stone.append(ResourceRef.from_model(skill_stone_obj))
			skill_stone_map[id_] = skill_stone_obj

		return (
			AnalyzeResult(
				model=SkillStone,
				data=skill_stone_map,
			),
			AnalyzeResult(
				model=SkillStoneCategory,
				data=skill_stone_category_map,
			),
		)

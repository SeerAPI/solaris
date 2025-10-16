from functools import cached_property
from itertools import chain
from typing import TYPE_CHECKING

from sqlmodel import Field, Relationship, SQLModel

from solaris.analyze.base import AnalyzeResult, DataImportConfig
from solaris.analyze.model import (
	BaseCategoryModel,
	BaseResModel,
	BaseResModelWithOptionalId,
	ConvertToORM,
	ResourceRef,
	SkillEffectInUse,
	SkillEffectInUseORM,
)
from solaris.analyze.utils import CategoryMap
from solaris.utils import split_string_arg

from ..skill import BaseSkillEffectAnalyzer, SkillEffectType
from ._general import BaseItemAnalyzer, Item, ItemORM

if TYPE_CHECKING:
	from solaris.parse.parsers.items_optimize import Item11

	from ..element_type import TypeCombination, TypeCombinationORM


class SkillStoneEffectLink(SQLModel, table=True):
	"""技能石效果链接表"""

	skill_stone_effect_id: int | None = Field(
		default=None, foreign_key='skill_stone_effect.id', primary_key=True
	)
	effect_in_use_id: int | None = Field(
		default=None, foreign_key='skill_effect_in_use.id', primary_key=True
	)


class SkillStoneEffectBase(BaseResModelWithOptionalId):
	prob: float = Field(description='技能石效果激活概率，0到1之间')
	skill_stone_id: int = Field(
		description='技能石ID', foreign_key='skill_stone.id', exclude=True
	)
	@classmethod
	def resource_name(cls) -> str:
		return 'skill_stone_effect'


class SkillStoneEffect(SkillStoneEffectBase, ConvertToORM['SkillStoneEffectORM']):
	effect: list['SkillEffectInUse'] = Field(
		description='技能石效果列表'
	)

	@classmethod
	def get_orm_model(cls) -> type['SkillStoneEffectORM']:
		return SkillStoneEffectORM

	def to_orm(self) -> 'SkillStoneEffectORM':
		return SkillStoneEffectORM(
			id=self.id,
			prob=self.prob,
			skill_stone_id=self.skill_stone_id,
			effect=[effect.to_orm() for effect in self.effect],
		)


class SkillStoneEffectORM(SkillStoneEffectBase, table=True):
	effect: list['SkillEffectInUseORM'] = Relationship(
		back_populates='skill_stone_effect',
		link_model=SkillStoneEffectLink,
	)
	skill_stone: 'SkillStoneORM' = Relationship(back_populates='effect')


class SkillStoneBase(BaseResModel):
	id: int = Field(primary_key=True, foreign_key='item.id', description='技能石ID')
	name: str = Field(description='技能石名称')
	rank: int = Field(description='技能石等级，1到5分别对应D, C, B, A, S')
	power: int = Field(description='技能石威力')
	max_pp: int = Field(description='技能石最大PP')
	accuracy: int = Field(description='技能石命中率')

	@classmethod
	def resource_name(cls) -> str:
		return 'skill_stone'


class SkillStone(SkillStoneBase, ConvertToORM['SkillStoneORM']):
	category: ResourceRef['SkillStoneCategory'] = Field(description='技能石分类')
	item: ResourceRef['Item'] = Field(description='技能石物品资源引用')
	effect: list['SkillStoneEffect'] = Field(description='完美技能石效果列表')

	@classmethod
	def get_orm_model(cls) -> type['SkillStoneORM']:
		return SkillStoneORM

	def to_orm(self) -> 'SkillStoneORM':
		return SkillStoneORM(
			id=self.id,
			name=self.name,
			rank=self.rank,
			power=self.power,
			max_pp=self.max_pp,
			accuracy=self.accuracy,
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
	effect: list['SkillStoneEffectORM'] = Relationship(
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


if TYPE_CHECKING:
	class SkillStoneDict(Item11):
		power: int
		max_pp: int
		accuracy: int
		effect: list['SkillStoneEffect']


class SkillStoneAnalyzer(BaseSkillEffectAnalyzer, BaseItemAnalyzer):
	@classmethod
	def get_data_import_config(cls) -> DataImportConfig:
		config = DataImportConfig(
			flash_paths=('config.xml.SkillXMLInfo_skillStoneClass.xml',),
		)
		return (
			config
			+ BaseItemAnalyzer.get_data_import_config()
			+ BaseSkillEffectAnalyzer.get_data_import_config()
		)

	@cached_property
	def skill_stone_data(self) -> dict[int, "SkillStoneDict"]:
		unity_data: list["Item11"] = self.get_category(11)['root']['items']
		flash_data = self._get_data(
			'flash', 'config.xml.SkillXMLInfo_skillStoneClass.xml'
		)['MoveStones']['MoveStone']
		flash_data_map = {stone['ID']: stone for stone in flash_data}
		result = {}
		for stone in unity_data:
			id_ = stone['id'] - 1100000
			flash_stone = flash_data_map[id_]
			move_effects = [
				SkillStoneEffect(
					prob=effect['EffectProb'] / 100,
					skill_stone_id=id_,
					effect=self.create_skill_effect(
						type_ids=split_string_arg(effect['SideEffect']),
						args=split_string_arg(effect['SideEffectArg']),
					),
				)
				for effect in flash_stone['MoveEffect']
			]
			result[id_] = {
				**stone,
				'power': flash_stone['Power'],
				'max_pp': flash_stone['MaxPP'],
				'accuracy': flash_stone['Accuracy'],
				'effect': move_effects,
			}
		return result

	def analyze(self) -> tuple[AnalyzeResult, ...]:
		SkillEffectInUse.model_rebuild(
			force=True,
			_parent_namespace_depth=2,
			_types_namespace={'SkillEffectType': SkillEffectType},
		)
		skill_stone_data = self.skill_stone_data

		category_type_set = set()
		skill_stone_map: dict[int, SkillStone] = {}
		skill_stone_category_map: CategoryMap[
			int,
			SkillStoneCategory,
			SkillStone,
		] = CategoryMap('skill_stone')
		for id_, skill_stone in skill_stone_data.items():
			item_ref = ResourceRef.from_model(Item, id=id_ + 1100000)
			# 获取不带等级的技能石名称
			category_name = skill_stone['name'].split('级')[1]
			type_id = skill_stone['type']
			if type_id not in category_type_set:
				category_type_set.add(type_id)
				skill_stone_category_map[type_id] = SkillStoneCategory(
					id=type_id,
					name=category_name,
					type=ResourceRef(
						id=type_id,
						resource_name='element_type_combination',
					),
				)

			category = skill_stone_category_map[type_id]
			skill_stone_obj = SkillStone(
				id=id_,
				name=skill_stone['name'],
				rank=skill_stone['rank'],
				power=skill_stone['power'],
				max_pp=skill_stone['max_pp'],
				accuracy=skill_stone['accuracy'],
				item=item_ref,
				category=ResourceRef.from_model(category),
				effect=skill_stone['effect'],
			)
			category.skill_stone.append(ResourceRef.from_model(skill_stone_obj))
			skill_stone_map[id_] = skill_stone_obj

		return (
			AnalyzeResult(model=SkillStone, data=skill_stone_map),
			AnalyzeResult(model=SkillStoneCategory, data=skill_stone_category_map),
			AnalyzeResult(
				model=SkillStoneEffect,
				data=dict(enumerate(chain(
						effect
						for stone in skill_stone_map.values()
						for effect in stone.effect
					))),
				output_mode='db'
			),
		)

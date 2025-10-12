from functools import cached_property
from typing import TYPE_CHECKING, Optional, cast

from sqlmodel import Field, Relationship, SQLModel

from solaris.analyze.analyzers.skill import BaseSkillEffectAnalyzer
from solaris.analyze.base import DataImportConfig
from solaris.analyze.model import (
	BaseCategoryModel,
	BaseResModel,
	ConvertToORM,
	ResourceRef,
	SkillEffectInUse,
	SkillEffectInUseORM,
)
from solaris.analyze.typing_ import AnalyzeResult
from solaris.analyze.utils import CategoryMap
from solaris.utils import split_string_arg

if TYPE_CHECKING:
	from solaris.parse.parsers.gems import GemItem as UnityGemItem


class GemEffectLink(SQLModel, table=True):
	gem_id: int | None = Field(default=None, foreign_key='gem.id', primary_key=True)
	skill_effect_in_use_id: int | None = Field(
		default=None, foreign_key='skill_effect_in_use.id', primary_key=True
	)


class GemBase(BaseResModel):
	name: str = Field(description='宝石名称')
	level: int = Field(description='宝石等级')
	generation_id: int = Field(
		description='宝石世代', foreign_key='gem_generation_category.id'
	)

	@classmethod
	def resource_name(cls) -> str:
		return 'gem'


class GemResRefs(SQLModel):
	next_level_gem: ResourceRef['Gem'] | None = Field(
		default=None,
		description='该宝石的下一等级的引用，当为None时表示该宝石为最高等级',
	)
	category: ResourceRef['GemCategory'] = Field(description='宝石类型引用')
	effect: list[SkillEffectInUse] = Field(description='宝石效果')


class Gem(GemBase, GemResRefs, ConvertToORM['GemORM']):
	inlay_rate: float | None = Field(default=None, description='镶嵌成功率')
	equivalent_level1_count: int | None = Field(
		default=None, description='相当于多少个1级宝石'
	)
	fail_compensate_range: tuple[int, int] | None = Field(
		default=None, description='当镶嵌失败时返还的宝石的等级范围，仅在1代宝石中有效'
	)

	upgrade_cost: int | None = Field(
		default=None, description='升级到该等级需要的石之砂数量，仅在2代宝石中有效'
	)

	@classmethod
	def get_orm_model(cls) -> type['GemORM']:
		return GemORM

	def to_orm(self) -> 'GemORM':
		gen1_part = None
		gen2_part = None
		if self.generation_id == 1:
			fail_compensate_range = cast(tuple[int, int], self.fail_compensate_range)
			gen1_part = GemGen1PartORM(
				id=self.id,
				inlay_rate=cast(float, self.inlay_rate),
				equivalent_level1_count=cast(int, self.equivalent_level1_count),
				fail_compensate_level_start=fail_compensate_range[0],
				fail_compensate_level_end=fail_compensate_range[1],
			)
		elif self.generation_id == 2:
			gen2_part = GemGen2PartORM(
				id=self.id,
				upgrade_cost=cast(int, self.upgrade_cost),
			)
		return GemORM(
			id=self.id,
			name=self.name,
			level=self.level,
			generation_id=self.generation_id,
			gen1_part=gen1_part,
			gen2_part=gen2_part,
			next_level_gem_id=self.next_level_gem.id if self.next_level_gem else None,
			category_id=self.category.id,
			skill_effect_in_use=[effect.to_orm() for effect in self.effect],
		)

	def to_detailed(self) -> 'GemGen1 | GemGen2':
		general_args = {
			'id': self.id,
			'name': self.name,
			'level': self.level,
			'generation_id': self.generation_id,
			'category': self.category,
			'effect': self.effect,
			'next_level_gem': self.next_level_gem,
		}
		if self.generation_id == 1:
			return GemGen1(
				**general_args,
				inlay_rate=cast(float, self.inlay_rate),
				equivalent_level1_count=cast(int, self.equivalent_level1_count),
				fail_compensate_range=cast(tuple[int, int], self.fail_compensate_range),
			)
		else:
			return GemGen2(
				**general_args,
				upgrade_cost=cast(int, self.upgrade_cost),
			)


class GemGen1(GemBase, GemResRefs):
	inlay_rate: float = Field(description='镶嵌成功率')
	equivalent_level1_count: int = Field(description='相当于多少个1级宝石')
	fail_compensate_range: tuple[int, int] = Field(
		description='当镶嵌失败时返还的宝石的等级范围'
	)


class GemGen2(GemBase, GemResRefs):
	upgrade_cost: int = Field(description='升级到该等级需要的石之砂数量')


class GemORM(GemBase, table=True):
	next_level_gem_id: int | None = Field(
		default=None,
		description='该宝石的下一等级的引用，当为None时表示该宝石为最高等级',
	)
	category_id: int = Field(foreign_key='gem_category.id')
	generation: 'GemGenCategoryORM' = Relationship(
		back_populates='gem',
	)
	category: Optional['GemCategoryORM'] = Relationship(
		back_populates='gem',
		sa_relationship_kwargs={
			'primaryjoin': 'GemORM.category_id == GemCategoryORM.id',
		},
	)
	skill_effect_in_use_id: int | None = Field(
		default=None, foreign_key='skill_effect_in_use.id'
	)
	skill_effect_in_use: list['SkillEffectInUseORM'] = Relationship(
		back_populates='gem',
		link_model=GemEffectLink,
	)

	gen1_part: Optional['GemGen1PartORM'] = Relationship(
		back_populates='gem',
		sa_relationship_kwargs={
			'primaryjoin': 'GemORM.id == GemGen1PartORM.id',
		},
	)
	gen2_part: Optional['GemGen2PartORM'] = Relationship(
		back_populates='gem',
		sa_relationship_kwargs={
			'primaryjoin': 'GemORM.id == GemGen2PartORM.id',
		},
	)


class GemGen1PartORM(BaseResModel, table=True):
	id: int = Field(primary_key=True, foreign_key='gem.id')
	inlay_rate: float = Field(description='镶嵌成功率')
	equivalent_level1_count: int = Field(description='相当于多少个1级宝石')

	fail_compensate_level_start: int = Field(
		description='当镶嵌失败时返还的宝石的等级范围'
	)
	fail_compensate_level_end: int = Field(
		description='当镶嵌失败时返还的宝石的等级范围'
	)

	gem: 'GemORM' = Relationship(
		back_populates='gen1_part',
		sa_relationship_kwargs={
			'primaryjoin': 'GemORM.id == GemGen1PartORM.id',
		},
	)

	@classmethod
	def resource_name(cls) -> str:
		return 'gem_gen1_part'


class GemGen2PartORM(BaseResModel, table=True):
	id: int = Field(primary_key=True, foreign_key='gem.id')
	upgrade_cost: int = Field(description='升级到该等级需要的石之砂数量')

	gem: 'GemORM' = Relationship(
		back_populates='gen2_part',
		sa_relationship_kwargs={
			'primaryjoin': 'GemORM.id == GemGen2PartORM.id',
		},
	)

	@classmethod
	def resource_name(cls) -> str:
		return 'gem_gen2_part'


class GemCategoryBase(BaseCategoryModel):
	name: str = Field(description='名称')
	generation_id: int = Field(
		description='宝石世代', foreign_key='gem_generation_category.id'
	)

	@classmethod
	def resource_name(cls) -> str:
		return 'gem_category'


class GemCategory(GemCategoryBase, ConvertToORM['GemCategoryORM']):
	gem: list[ResourceRef] = Field(default_factory=list, description='宝石列表')

	@classmethod
	def get_orm_model(cls) -> type['GemCategoryORM']:
		return GemCategoryORM

	def to_orm(self) -> 'GemCategoryORM':
		return GemCategoryORM(
			id=self.id,
			name=self.name,
			generation_id=self.generation_id,
		)


class GemCategoryORM(GemCategoryBase, table=True):
	gem: list['GemORM'] = Relationship(
		back_populates='category',
	)
	generation: list['GemGenCategoryORM'] = Relationship(
		back_populates='category',
	)


class GemGenCategoryBase(BaseCategoryModel):
	@classmethod
	def resource_name(cls) -> str:
		return 'gem_generation_category'


class GemGenCategory(GemGenCategoryBase, ConvertToORM['GemGenCategoryORM']):
	gem_category: list[ResourceRef] = Field(
		default_factory=list, description='宝石类别列表'
	)

	@classmethod
	def get_orm_model(cls) -> type['GemGenCategoryORM']:
		return GemGenCategoryORM

	def to_orm(self) -> 'GemGenCategoryORM':
		return GemGenCategoryORM(
			id=self.id,
		)


class GemGenCategoryORM(GemGenCategoryBase, table=True):
	gem: list['GemORM'] = Relationship(
		back_populates='generation',
		sa_relationship_kwargs={
			'primaryjoin': 'GemORM.generation_id == GemGenCategoryORM.id',
		},
	)
	category: 'GemCategoryORM' = Relationship(
		back_populates='generation',
	)


def _get_generation_id_from_category(category_id: int) -> int:
	"""根据宝石类别ID获取宝石世代"""
	if category_id < 100:
		return 1
	elif category_id > 100:
		return 2
	else:
		raise ValueError(f'Invalid category id: {category_id}')


if TYPE_CHECKING:
	class GemItem(UnityGemItem):
		fail_compensate_start: int
		fail_compensate_end: int
		equit_lv1_cnt1: int
		inlay_prob: int


class GemAnalyzer(BaseSkillEffectAnalyzer):
	"""刻印宝石数据解析器"""

	@classmethod
	def get_data_import_config(cls) -> DataImportConfig:
		return super().get_data_import_config() + DataImportConfig(
			unity_paths=('gems.json',),
			flash_paths=('config.xml.GemsXMLInfo.xml',)
		)

	@cached_property
	def gem_data(self) -> dict[int, 'GemItem']:
		unity_data: list['UnityGemItem'] = self._get_data(
			'unity', 'gems.json'
		)['gems']['gem']
		flash_data = self._get_data(
			'flash', 'config.xml.GemsXMLInfo.xml'
		)['Gems']['Gem']
		flash_data_map = {i['ID']: i for i in flash_data}
		result = {}
		for gem in unity_data:
			id_ = gem['id']

			result[id_] = {
				**gem,
				'fail_compensate_start': flash_data_map[id_]['FailCompensateStart'],
				'fail_compensate_end': flash_data_map[id_]['FailCompensateEnd'],
				'equit_lv1_cnt1': flash_data_map[id_]['EquitLv1Cnt1'],
				'inlay_prob': flash_data_map[id_]['InlayProb'],
			}
		return result

	def _create_gem_effect(self, data: 'GemItem') -> list[SkillEffectInUse]:
		effect = data['skill_effects'][0]['effect']
		if not effect:
			return []
		id_ = effect['effect_id']
		args = effect['param']
		effect_in_use_list = self.create_skill_effect(type_ids=[id_], args=args)
		if not effect_in_use_list:
			raise ValueError(f'宝石效果创建失败: {id_} {args}')

		return effect_in_use_list

	def analyze(self) -> tuple[AnalyzeResult, ...]:
		"""分析宝石数据并返回模式构建器列表"""
		gem_map: dict[int, Gem] = {}
		gem_category_map: CategoryMap[int, GemCategory, ResourceRef] = CategoryMap(
			'gem'
		)
		gem_gen_category_map: CategoryMap[int, GemGenCategory, ResourceRef] = (
			CategoryMap('gem_category')
		)
		for gem_id, gem_data in self.gem_data.items():
			category_id = gem_data['category']
			if category_id in gem_category_map:
				continue

			generation_id = _get_generation_id_from_category(category_id)
			name_slice = -3 if generation_id == 1 else -1
			category = GemCategory(
				id=category_id,
				name=gem_data['name'][:name_slice],
				generation_id=generation_id,
			)
			gem_category_map[category_id] = category

			if generation_id in gem_gen_category_map:
				continue
			gem_gen_category_map[generation_id] = GemGenCategory(
				id=generation_id,
			)

		for gem_id, gem_data in self.gem_data.items():
			category_id = gem_data['category']
			category_ref = ResourceRef.from_model(gem_category_map[category_id])

			generation_id = _get_generation_id_from_category(category_id)
			fail_compensate_range = None
			upgrade_cost = None
			equivalent_level1_count = None
			if generation_id == 1:
				fail_compensate_range = (
					gem_data['fail_compensate_start'],
					gem_data['fail_compensate_end'],
				)
				equivalent_level1_count = gem_data['equit_lv1_cnt1']
			else:
				upgrade_cost = gem_data['equit_lv1_cnt1']

			gem_obj = Gem(
				id=gem_id,
				name=gem_data['name'],
				level=gem_data['lv'],
				generation_id=generation_id,
				category=category_ref,
				inlay_rate=gem_data['inlay_prob'] / 100,
				equivalent_level1_count=equivalent_level1_count,
				effect=self._create_gem_effect(gem_data),
				upgrade_cost=upgrade_cost,
				fail_compensate_range=fail_compensate_range,
			)
			gem_map[gem_id] = gem_obj

			gem_ref = ResourceRef.from_model(gem_obj)
			gem_category_map.add_element(category_id, gem_ref)
			gem_gen_category_map.add_element(generation_id, gem_ref)

		for gem_id, gem_data in self.gem_data.items():
			if upgrade_gem_id := gem_data.get('upgrade_gem_id'):
				gem_map[upgrade_gem_id].next_level_gem = ResourceRef.from_model(
					gem_map[gem_id],
				)

		return (
			AnalyzeResult(model=Gem, data=gem_map),
			AnalyzeResult(model=GemCategory, data=gem_category_map,
			),
			AnalyzeResult(
				model=GemGenCategory,
				data=gem_gen_category_map,
			),
			AnalyzeResult(
				model=GemGen1,
				data={
					gem_id: gem.to_detailed()
					for gem_id, gem in gem_map.items()
					if gem.generation_id == 1
				},
				output_mode='json',
			),
			AnalyzeResult(
				model=GemGen2,
				data={
					gem_id: gem.to_detailed()
					for gem_id, gem in gem_map.items()
					if gem.generation_id == 2
				},
				output_mode='json',
			),
		)

from typing import TYPE_CHECKING, Any, Optional, cast

from pydantic import BaseModel
from sqlmodel import Field, Relationship, SQLModel

from solaris.utils import split_string_arg

from ..base import BaseDataSourceAnalyzer, DataImportConfig
from ..model import (
	BaseCategoryModel,
	BaseResModel,
	BaseResModelWithOptionalId,
	ConvertToORM,
	ResourceRef,
	SixAttributes,
	SixAttributesORM,
)
from ..typing_ import AnalyzeResult
from ..utils import CategoryMap, create_category_map

if TYPE_CHECKING:
	from solaris.parse.parsers.mintmark import MintmarkConfig, MintMarkItem

	from .pet.pet import Pet, PetORM
	from .skill import Skill, SkillORM


class SkillMintmarkLink(SQLModel, table=True):
	skill_id: int | None = Field(default=None, foreign_key='skill.id', primary_key=True)
	mintmark_id: int | None = Field(
		default=None, foreign_key='mintmark.id', primary_key=True
	)


class MintmarkMaxAttrORM(SixAttributesORM, table=True):
	ability_mintmark: list['AbilityPartORM'] = Relationship(
		back_populates='max_attr_value',
	)
	universal_mintmark: list['UniversalPartORM'] = Relationship(
		back_populates='max_attr_value',
	)

	@classmethod
	def resource_name(cls) -> str:
		return 'mintmark_max_attr'


class MintmarkBaseAttrORM(SixAttributesORM, table=True):
	universal_mintmark: list['UniversalPartORM'] = Relationship(
		back_populates='base_attr_value',
	)

	@classmethod
	def resource_name(cls) -> str:
		return 'mintmark_base_attr'


class MintmarkExtraAttrORM(SixAttributesORM, table=True):
	universal_mintmark: list['UniversalPartORM'] = Relationship(
		back_populates='extra_attr_value',
	)

	@classmethod
	def resource_name(cls) -> str:
		return 'mintmark_extra_attr'


class PetMintmarkLink(SQLModel, table=True):
	pet_id: int | None = Field(default=None, foreign_key='pet.id', primary_key=True)
	mintmark_id: int | None = Field(
		default=None, foreign_key='mintmark.id', primary_key=True
	)


class SkillMintmarkEffect(BaseModel):
	effect: int = Field(description='增幅效果ID')
	arg: int | None = Field(description='增幅效果参数')


class MintmarkBase(BaseResModel):
	name: str = Field(description='名称')
	desc: str = Field(description='刻印描述')
	rarity_id: int = Field(
		foreign_key='mintmark_rarity.id',
		exclude=True,
	)


class MintmarkResRefs(SQLModel):
	type: ResourceRef['MintmarkTypeCategory'] = Field(description='刻印类型')
	rarity: ResourceRef['MintmarkRarityCategory'] = Field(description='刻印稀有度')
	pet: list[ResourceRef['Pet']] | None = Field(
		default=None, description='表示该刻印仅能安装在这些精灵上，null表示无精灵限制'
	)


class AbilityMintmark(MintmarkBase, MintmarkResRefs):
	max_attr_value: SixAttributes = Field(
		description='刻印满级属性值，仅当该刻印为能力刻印或全能刻印时有效'
	)

	@classmethod
	def resource_name(cls) -> str:
		return 'ability_mintmark'


class SkillMintmark(MintmarkBase, MintmarkResRefs):
	effect: SkillMintmarkEffect = Field(
		description='技能刻印效果，仅当刻印类型为技能刻印时有效'
	)
	skill: list[ResourceRef['Skill']] = Field(
		default_factory=list, description='该刻印所绑定的技能列表'
	)

	@classmethod
	def resource_name(cls) -> str:
		return 'skill_mintmark'


class UniversalMintmark(MintmarkBase, MintmarkResRefs):
	mintmark_class: ResourceRef['MintmarkClassCategory'] | None = Field(
		default=None, description='刻印所属系列，当该刻印是精灵专属刻印时可能为null'
	)
	base_attr_value: SixAttributes = Field(
		description='刻印基础属性值，仅当该刻印为全能刻印时有效'
	)
	max_attr_value: SixAttributes = Field(
		description='刻印满级属性值，仅当该刻印为能力刻印或全能刻印时有效'
	)
	extra_attr_value: SixAttributes | None = Field(
		default=None,
		description='刻印隐藏属性值，仅当该刻印为全能刻印并具有隐藏属性时有效',
	)

	@classmethod
	def resource_name(cls) -> str:
		return 'universal_mintmark'


class AbilityPartORM(BaseResModelWithOptionalId, table=True):
	mintmark_id: int = Field(foreign_key='mintmark.id')
	mintmark: 'MintmarkORM' = Relationship(
		back_populates='ability_part',
		sa_relationship_kwargs={
			'primaryjoin': 'MintmarkORM.id == AbilityPartORM.mintmark_id',
		},
	)
	max_attr_value: 'MintmarkMaxAttrORM' = Relationship(
		back_populates='ability_mintmark',
	)
	max_attr_value_id: int | None = Field(
		default=None, foreign_key='mintmark_max_attr.id'
	)

	@classmethod
	def resource_name(cls) -> str:
		return 'ability_mintmark_part'


class SkillPartORM(BaseResModelWithOptionalId, table=True):
	mintmark_id: int = Field(foreign_key='mintmark.id')
	mintmark: 'MintmarkORM' = Relationship(
		back_populates='skill_part',
		sa_relationship_kwargs={
			'primaryjoin': 'MintmarkORM.id == SkillPartORM.mintmark_id',
		},
	)
	effect: int = Field(description='增幅效果ID')
	arg: int | None = Field(default=None, description='增幅效果参数')

	@classmethod
	def resource_name(cls) -> str:
		return 'skill_mintmark_part'


class UniversalPartORM(BaseResModelWithOptionalId, table=True):
	mintmark_id: int = Field(foreign_key='mintmark.id')
	mintmark: 'MintmarkORM' = Relationship(
		back_populates='universal_part',
		sa_relationship_kwargs={
			'primaryjoin': 'MintmarkORM.id == UniversalPartORM.mintmark_id',
		},
	)
	mintmark_class_id: int | None = Field(default=None, foreign_key='mintmark_class.id')
	mintmark_class: Optional['MintmarkClassCategoryORM'] = Relationship(
		back_populates='mintmark',
	)
	base_attr_value: 'MintmarkBaseAttrORM' = Relationship(
		back_populates='universal_mintmark',
	)
	base_attr_value_id: int | None = Field(
		default=None, foreign_key='mintmark_base_attr.id'
	)
	max_attr_value: 'MintmarkMaxAttrORM' = Relationship(
		back_populates='universal_mintmark',
	)
	max_attr_value_id: int | None = Field(
		default=None, foreign_key='mintmark_max_attr.id'
	)
	extra_attr_value: Optional['MintmarkExtraAttrORM'] = Relationship(
		back_populates='universal_mintmark',
	)
	extra_attr_value_id: int | None = Field(
		default=None, foreign_key='mintmark_extra_attr.id'
	)

	@classmethod
	def resource_name(cls) -> str:
		return 'universal_mintmark_part'


class Mintmark(MintmarkBase, MintmarkResRefs, ConvertToORM['MintmarkORM']):
	effect: SkillMintmarkEffect | None = Field(
		default=None, description='技能刻印效果，仅当刻印类型为技能刻印时有效'
	)
	mintmark_class: ResourceRef['MintmarkClassCategory'] | None = Field(
		default=None, description='刻印所属系列，仅当该刻印为全能刻印时有效'
	)
	base_attr_value: SixAttributes | None = Field(
		default=None, description='刻印基础属性值，仅当该刻印为全能刻印时有效'
	)
	max_attr_value: SixAttributes | None = Field(
		default=None, description='刻印满级属性值，仅当该刻印为能力刻印或全能刻印时有效'
	)
	extra_attr_value: SixAttributes | None = Field(
		default=None,
		description='刻印隐藏属性值，仅当该刻印为全能刻印并具有隐藏属性时有效',
	)
	skill: list[ResourceRef['Skill']] | None = Field(
		default=None, description='该刻印所绑定的技能列表，仅当该刻印为技能刻印时有效'
	)

	@classmethod
	def resource_name(cls) -> str:
		return 'mintmark'

	@classmethod
	def get_orm_model(cls) -> type['MintmarkORM']:
		return MintmarkORM

	def to_orm(self) -> 'MintmarkORM':
		part_kwargs: dict = {
			'ability_part': None,
			'skill_part': None,
			'universal_part': None,
		}
		type_id = self.type.id
		if type_id == 0:
			self = cast(AbilityMintmark, self)
			part_kwargs['ability_part'] = AbilityPartORM(
				mintmark_id=self.id,
				max_attr_value=MintmarkMaxAttrORM(
					**self.max_attr_value.model_dump(),
				),
			)
		elif type_id == 1:
			self = cast(SkillMintmark, self)
			part_kwargs['skill_part'] = SkillPartORM(
				mintmark_id=self.id,
				effect=self.effect.effect,
				arg=self.effect.arg,
			)
		elif type_id == 3:
			self = cast(UniversalMintmark, self)
			part_kwargs['universal_part'] = UniversalPartORM(
				mintmark_id=self.id,
				mintmark_class_id=self.mintmark_class.id
				if self.mintmark_class
				else None,
				base_attr_value=MintmarkBaseAttrORM(
					**self.base_attr_value.model_dump(),
				),
				max_attr_value=MintmarkMaxAttrORM(
					**self.max_attr_value.model_dump(),
				),
				extra_attr_value=MintmarkExtraAttrORM(
					**self.extra_attr_value.model_dump(),
				)
				if self.extra_attr_value
				else None,
			)

		return MintmarkORM(
			id=self.id,
			name=self.name,
			desc=self.desc,
			type_id=type_id,
			rarity_id=self.rarity_id,
			**part_kwargs,
		)

	def to_detailed(self) -> 'AbilityMintmark | SkillMintmark | UniversalMintmark':
		general_args = {
			'id': self.id,
			'name': self.name,
			'desc': self.desc,
			'pet': self.pet,
			'rarity': self.rarity,
			'rarity_id': self.rarity_id,
			'type': self.type,
		}
		if self.type.id == 0:
			self = cast(AbilityMintmark, self)
			return AbilityMintmark(
				**general_args,
				max_attr_value=self.max_attr_value,
			)
		elif self.type.id == 1:
			self = cast(SkillMintmark, self)
			return SkillMintmark(
				**general_args,
				effect=self.effect,
				skill=self.skill or [],
			)
		elif self.type.id == 3:
			self = cast(UniversalMintmark, self)
			return UniversalMintmark(
				**general_args,
				mintmark_class=self.mintmark_class,
				base_attr_value=self.base_attr_value,
				max_attr_value=self.max_attr_value,
				extra_attr_value=self.extra_attr_value,
			)

		raise ValueError(f'Invalid mintmark type: {self.type.id}')


class MintmarkORM(MintmarkBase, table=True):
	type_id: int = Field(foreign_key='mintmark_type.id')
	type: 'MintmarkTypeCategoryORM' = Relationship(
		back_populates='mintmark',
	)
	rarity_id: int = Field(foreign_key='mintmark_rarity.id')
	rarity: 'MintmarkRarityCategoryORM' = Relationship(
		back_populates='mintmark',
	)
	ability_part_id: int | None = Field(
		default=None, foreign_key='ability_mintmark_part.id'
	)
	ability_part: Optional['AbilityPartORM'] = Relationship(
		back_populates='mintmark',
		sa_relationship_kwargs={
			'primaryjoin': 'MintmarkORM.id == AbilityPartORM.mintmark_id',
		},
	)
	skill_part_id: int | None = Field(
		default=None, foreign_key='skill_mintmark_part.id'
	)
	skill_part: Optional['SkillPartORM'] = Relationship(
		back_populates='mintmark',
		sa_relationship_kwargs={
			'primaryjoin': 'MintmarkORM.id == SkillPartORM.mintmark_id',
		},
	)
	universal_part_id: int | None = Field(
		default=None, foreign_key='universal_mintmark_part.id'
	)
	universal_part: Optional['UniversalPartORM'] = Relationship(
		back_populates='mintmark',
		sa_relationship_kwargs={
			'primaryjoin': 'MintmarkORM.id == UniversalPartORM.mintmark_id',
		},
	)
	pet: list['PetORM'] = Relationship(
		back_populates='exclusive_mintmark',
		link_model=PetMintmarkLink,
	)
	skill: list['SkillORM'] = Relationship(
		back_populates='mintmark',
		link_model=SkillMintmarkLink,
	)

	@classmethod
	def resource_name(cls) -> str:
		return 'mintmark'


class MintmarkRarityBase(BaseCategoryModel):
	@classmethod
	def resource_name(cls) -> str:
		return 'mintmark_rarity'


class MintmarkRarityCategory(
	MintmarkRarityBase, ConvertToORM['MintmarkRarityCategoryORM']
):
	mintmark: list[ResourceRef['Mintmark']] = Field(
		default_factory=list, description='刻印列表'
	)

	@classmethod
	def get_orm_model(cls) -> type['MintmarkRarityCategoryORM']:
		return MintmarkRarityCategoryORM

	def to_orm(self) -> 'MintmarkRarityCategoryORM':
		return MintmarkRarityCategoryORM(
			id=self.id,
		)


class MintmarkRarityCategoryORM(MintmarkRarityBase, table=True):
	mintmark: list['MintmarkORM'] = Relationship(
		back_populates='rarity',
	)


class MintmarkTypeBase(BaseCategoryModel):
	name: str = Field(description='名称')

	@classmethod
	def resource_name(cls) -> str:
		return 'mintmark_type'


class MintmarkTypeCategory(MintmarkTypeBase, ConvertToORM['MintmarkTypeCategoryORM']):
	mintmark: list[ResourceRef['Mintmark']] = Field(
		default_factory=list, description='刻印列表'
	)

	@classmethod
	def get_orm_model(cls) -> type['MintmarkTypeCategoryORM']:
		return MintmarkTypeCategoryORM

	def to_orm(self) -> 'MintmarkTypeCategoryORM':
		return MintmarkTypeCategoryORM(
			id=self.id,
			name=self.name,
		)


class MintmarkTypeCategoryORM(MintmarkTypeBase, table=True):
	mintmark: list['MintmarkORM'] = Relationship(
		back_populates='type',
	)


class MintmarkClassBase(BaseCategoryModel):
	name: str = Field(description='名称')

	@classmethod
	def resource_name(cls) -> str:
		return 'mintmark_class'


class MintmarkClassCategory(
	MintmarkClassBase, ConvertToORM['MintmarkClassCategoryORM']
):
	mintmark: list[ResourceRef['UniversalMintmark']] = Field(
		default_factory=list, description='刻印列表'
	)

	@classmethod
	def get_orm_model(cls) -> type['MintmarkClassCategoryORM']:
		return MintmarkClassCategoryORM

	def to_orm(self) -> 'MintmarkClassCategoryORM':
		return MintmarkClassCategoryORM(
			id=self.id,
			name=self.name,
		)


class MintmarkClassCategoryORM(MintmarkClassBase, table=True):
	mintmark: list['UniversalPartORM'] = Relationship(
		back_populates='mintmark_class',
	)


def _create_attr_values(data: 'MintMarkItem') -> dict[str, Any]:
	kwargs = {}
	for k, name in [
		('base_attri_value', 'base_attr_value'),
		('max_attri_value', 'max_attr_value'),
		('extra_attri_value', 'extra_attr_value'),
	]:
		if value := data[k]:
			kwargs[name] = SixAttributes.from_list(value)

	return kwargs


class MintmarkAnalyzer(BaseDataSourceAnalyzer):
	"""刻印相关数据分析器"""

	@classmethod
	def get_data_import_config(cls) -> DataImportConfig:
		return DataImportConfig(
			unity_paths=('mintmark.json',),
			flash_paths=('config.xml.CountermarkXMLInfo.xml',),
			patch_paths=('mintmark_type.json',),
		)

	def analyze(self) -> tuple[AnalyzeResult, ...]:
		"""分析刻印数据并返回模式构建器列表"""
		mintmark_data: MintmarkConfig = self._get_data('unity', 'mintmark.json')
		mintmark_type_csv = self._get_data('patch', 'mintmark_type.json')
		mintmark_list = mintmark_data['mint_marks']['mint_mark']
		classes_map: CategoryMap[int, MintmarkClassCategory, ResourceRef] = CategoryMap(
			'mintmark'
		)
		classes_map.update(
			{
				i['id']: MintmarkClassCategory(id=i['id'], name=i['class_name'])
				for i in mintmark_data['mint_marks']['mintmark_class']
			}
		)
		type_map: CategoryMap[int, MintmarkTypeCategory, ResourceRef] = (
			create_category_map(
				mintmark_type_csv,
				model_cls=MintmarkTypeCategory,
				array_key='mintmark',
			)
		)
		rarity_map: CategoryMap[int, MintmarkRarityCategory, ResourceRef] = CategoryMap(
			'mintmark'
		)
		rarity_map.update({i: MintmarkRarityCategory(id=i) for i in range(1, 6)})
		effect_map: dict[int, int] = {
			i['ID']: i['Effect']
			for i in self._get_data(
				'flash', 'config.xml.CountermarkXMLInfo.xml'
			)['MintMarks']['MintMark']
			if 'Effect' in i
		}
		mintmark_map: dict[int, Mintmark] = {}
		ability_mintmark_map: dict[int, AbilityMintmark] = {}
		skill_mintmark_map: dict[int, SkillMintmark] = {}
		universal_mintmark_map: dict[int, UniversalMintmark] = {}
		for mintmark in mintmark_list:
			id_ = mintmark['id']
			# 跳过最后三个刻印（大，中，小碎片）
			if id_ > 49999:
				continue
			name = mintmark['des']
			type_id = mintmark['type']
			mintmark_ref = ResourceRef.from_model(
				Mintmark,
				id=id_,
			)
			type_ref = ResourceRef.from_model(
				MintmarkTypeCategory,
				id=type_id,
			)
			rarity_ref = ResourceRef.from_model(
				MintmarkRarityCategory,
				id=(rarity_id := mintmark['rare']),
			)
			pet_refs = None
			if pet_ids := mintmark['monster_id']:
				pet_refs = [
					ResourceRef(id=id_, resource_name='pet')
					for id_ in pet_ids
				]
			skill_refs = None
			if skill_ids := mintmark['move_id']:
				skill_refs = [
					ResourceRef(id=id_, resource_name='skill')
					for id_ in skill_ids
				]
			# 飓风利袭刻印的Arg字段是错误的，删除它
			if id_ == 20187:
				mintmark['arg'].clear()

			skill_effect = None
			max_attr_value = None
			attr_kwargs = _create_attr_values(mintmark)
			if type_id == 0:
				max_attr_value = SixAttributes.from_list(mintmark['arg'])
				attr_kwargs['max_attr_value'] = max_attr_value
			elif type_id == 1:
				skill_effect = SkillMintmarkEffect(
					effect=effect_map[id_],
					arg=mintmark['arg'][0] if mintmark['arg'] else None,
				)

			class_ref = None
			if classes_id := mintmark['mintmark_class']:
				classes_map.add_element(classes_id, mintmark_ref)
				class_ref = ResourceRef.from_model(
					MintmarkClassCategory,
					id=classes_id,
				)
			mintmark_obj = Mintmark(
				id=id_,
				name=name,
				type=type_ref,
				rarity=rarity_ref,
				rarity_id=rarity_id,
				pet=pet_refs,
				effect=skill_effect,
				desc=mintmark['effect_des'],
				mintmark_class=class_ref,
				skill=skill_refs,
				**attr_kwargs,
			)
			mintmark_map[id_] = mintmark_obj
			type_map.add_element(type_id, mintmark_ref)
			rarity_map.add_element(rarity_id, mintmark_ref)
			if type_id == 0:
				ability_mintmark_map[id_] = cast(
					AbilityMintmark, mintmark_obj.to_detailed()
				)
			elif type_id == 1:
				skill_mintmark_map[id_] = cast(
					SkillMintmark, mintmark_obj.to_detailed()
				)
			elif type_id == 3:
				universal_mintmark_map[id_] = cast(
					UniversalMintmark, mintmark_obj.to_detailed()
				)
		return (
			AnalyzeResult(model=Mintmark, data=mintmark_map),
			AnalyzeResult(model=AbilityMintmark, data=ability_mintmark_map),
			AnalyzeResult(model=SkillMintmark, data=skill_mintmark_map),
			AnalyzeResult(model=UniversalMintmark, data=universal_mintmark_map),
			AnalyzeResult(model=MintmarkClassCategory, data=classes_map),
			AnalyzeResult(model=MintmarkTypeCategory, data=type_map),
			AnalyzeResult(model=MintmarkRarityCategory, data=rarity_map),
		)

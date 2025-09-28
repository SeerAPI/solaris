from functools import cached_property
from typing import TYPE_CHECKING, Any, Optional, cast
from typing_extensions import Self

from pydantic import BaseModel
from sqlmodel import Field, Relationship, SQLModel

from solaris.analyze.base import BaseDataSourceAnalyzer, DataImportConfig
from solaris.analyze.model import (
	BaseCategoryModel,
	BaseResModel,
	BaseResModelWithOptionalId,
	ConvertToORM,
	EidEffect,
	EidEffectInUse,
	EidEffectInUseORM,
	ResourceRef,
	SixAttributes,
	SixAttributesORM,
)
from solaris.analyze.typing_ import AnalyzeResult
from solaris.analyze.utils import create_category_map
from solaris.utils import get_nested_value, split_string_arg

if TYPE_CHECKING:
	from .pet.pet import Pet, PetORM


def _create_pk_attribute(equip: dict[str, Any]) -> 'PkAttribute | None':
	pk_hp = equip.pop('PkHp', 0)
	pk_atk = equip.pop('PkAtk', 0)
	pk_fire_range = equip.pop('PkFireRange', 0)
	if pk_hp or pk_atk or pk_fire_range:
		return PkAttribute(
			pk_hp=pk_hp,
			pk_atk=pk_atk,
			pk_fire_range=pk_fire_range,
		)

	return None


class SuitBonusAttrORM(SixAttributesORM, table=True):
	suit_bonus: 'SuitBonusORM' = Relationship(
		back_populates='attribute',
	)

	@classmethod
	def resource_name(cls) -> str:
		return 'suit_bonus_attr'


class EquipBonusAttrORM(SixAttributesORM, table=True):
	equip_bonus: 'EquipBonusORM' = Relationship(
		back_populates='attribute',
	)

	@classmethod
	def resource_name(cls) -> str:
		return 'equip_bonus_attr'


class PkAttribute(BaseModel):
	"""装备PK加成（战队保卫战等远古活动使用）"""

	pk_hp: int = Field(description='装备提供的血量加成')
	pk_atk: int = Field(description='装备提供的攻击力加成')
	pk_fire_range: int = Field(description='装备提供的射击范围加成')


class OtherAttribute(BaseModel):
	hit_rate: int = Field(default=0, description='命中加成')
	dodge_rate: int = Field(default=0, description='闪避加成')
	crit_rate: int = Field(default=0, description='暴击加成')

	@classmethod
	def from_list(cls, other_attr_args: list[int]) -> Self:
		return cls(
			hit_rate=other_attr_args[0],
			dodge_rate=other_attr_args[1],
			crit_rate=other_attr_args[2],
		)


class PetSuitLink(SQLModel, table=True):
	pet_id: int | None = Field(default=None, foreign_key='pet.id', primary_key=True)
	suit_id: int | None = Field(
		default=None, foreign_key='suit_bonus.id', primary_key=True
	)


class EquipEffectBase(BaseResModelWithOptionalId):
	newse_id: int = Field()

	@classmethod
	def resource_name(cls) -> str:
		return 'equip_effect'


class EquipEffect(EquipEffectBase):
	eid_effect: EidEffectInUse | None = Field(
		default=None,
		description='部件效果，不是所有的部件都使用EID+EffectArgs来表示效果',
	)


class EquipBonusBase(BaseResModelWithOptionalId):
	desc: str = Field(description='部件描述')

	@classmethod
	def resource_name(cls) -> str:
		return 'equip_bonus'


class EquipBonus(EquipBonusBase, ConvertToORM['EquipBonusORM']):
	attribute: SixAttributes | None = Field(
		default=None, description='属性加成，仅在部件有属性加成时有效'
	)
	other_attribute: OtherAttribute | None = Field(
		default=None, description='其他属性加成，仅在部件有命中/闪避/暴击加成时有效'
	)
	effect: EquipEffect | None = Field(
		default=None, description='部件效果，仅当该部件为能力加成部件时有效'
	)

	@classmethod
	def get_orm_model(cls) -> type['EquipBonusORM']:
		return EquipBonusORM

	def to_orm(self) -> 'EquipBonusORM':
		other_attr_kwargs = (
			self.other_attribute.model_dump() if self.other_attribute else {}
		)
		effect_in_use_orm = None
		if self.effect and self.effect.eid_effect:
			effect_in_use_orm = self.effect.eid_effect.to_orm()

		return EquipBonusORM(
			id=self.id,
			desc=self.desc,
			newse_id=self.effect.newse_id if self.effect else None,
			effect_in_use=effect_in_use_orm,
			attribute=EquipBonusAttrORM(**self.attribute.model_dump())
			if self.attribute
			else None,
			**other_attr_kwargs,
		)


class EquipBonusORM(EquipBonusBase, table=True):
	equip: 'EquipORM' = Relationship(
		back_populates='bonus',
	)

	newse_id: int | None = Field(default=None)
	effect_in_use_id: int | None = Field(foreign_key='eid_effect_in_use.id')
	effect_in_use: Optional['EidEffectInUseORM'] = Relationship(
		back_populates='equip_bonus',
	)
	attribute_id: int | None = Field(default=None, foreign_key='equip_bonus_attr.id')
	attribute: Optional['EquipBonusAttrORM'] = Relationship(
		back_populates='equip_bonus',
	)

	hit_rate: int | None = Field(default=None)
	dodge_rate: int | None = Field(default=None)
	crit_rate: int | None = Field(default=None)


class SuitBonusBase(BaseResModelWithOptionalId):
	desc: str = Field(description='套装描述')

	@classmethod
	def resource_name(cls) -> str:
		return 'suit_bonus'


class SuitBonus(SuitBonusBase, ConvertToORM['SuitBonusORM']):
	effect: EquipEffect = Field(description='套装效果')
	effective_pets: list[ResourceRef['Pet']] | None = Field(
		default=None,
		description='表示套装效果仅在这些精灵上生效，null表示对所有精灵都生效',
	)
	attribute: SixAttributes | None = Field(
		default=None, description='属性加成，仅在套装效果为属性加成时有效'
	)

	@classmethod
	def get_orm_model(cls) -> type['SuitBonusORM']:
		return SuitBonusORM

	def to_orm(self) -> 'SuitBonusORM':
		effect_in_use_orm = None
		if self.effect and self.effect.eid_effect:
			effect_in_use_orm = self.effect.eid_effect.to_orm()

		return SuitBonusORM(
			id=self.id,
			desc=self.desc,
			newse_id=self.effect.newse_id,
			effect_in_use=effect_in_use_orm,
			attribute=SuitBonusAttrORM(**self.attribute.model_dump())
			if self.attribute
			else None,
		)


class SuitBonusORM(SuitBonusBase, table=True):
	suit: 'SuitORM' = Relationship(
		back_populates='bonus',
	)

	newse_id: int | None = Field(default=None)
	effect_in_use_id: int | None = Field(
		default=None, foreign_key='eid_effect_in_use.id'
	)
	effect_in_use: Optional['EidEffectInUseORM'] = Relationship(
		back_populates='suit_bonus',
	)
	attribute_id: int | None = Field(default=None, foreign_key='suit_bonus_attr.id')
	attribute: Optional['SuitBonusAttrORM'] = Relationship(
		back_populates='suit_bonus',
	)

	effective_pets: list['PetORM'] = Relationship(
		back_populates='exclusive_suit_bonus',
		link_model=PetSuitLink,
	)


class SuitBase(BaseResModel):
	name: str = Field(description='名称')
	transform: bool = Field(description='是否可变形')
	tran_speed: float | None = Field(
		default=None, description='变形速度，仅当该套装可变形时有效'
	)
	suit_desc: str = Field(description='套装描述')

	@classmethod
	def resource_name(cls) -> str:
		return 'suit'


class Suit(SuitBase, ConvertToORM['SuitORM']):
	equips: list[ResourceRef['Equip']] = Field(
		default_factory=list, description='部件列表'
	)
	bonus: SuitBonus | None = Field(
		default=None, description='套装效果，仅当该套装为能力加成套装时有效'
	)

	@classmethod
	def get_orm_model(cls) -> type['SuitORM']:
		return SuitORM

	def to_orm(self) -> 'SuitORM':
		return SuitORM(
			id=self.id,
			name=self.name,
			transform=self.transform,
			tran_speed=self.tran_speed,
			suit_desc=self.suit_desc,
			bonus=self.bonus.to_orm() if self.bonus else None,
		)


class SuitORM(SuitBase, table=True):
	equips: list['EquipORM'] = Relationship(
		back_populates='suit',
	)
	bonus_id: int | None = Field(default=None, foreign_key='suit_bonus.id')
	bonus: Optional['SuitBonusORM'] = Relationship(
		back_populates='suit',
	)


class EquipBase(BaseResModel):
	name: str = Field(description='名称')
	speed: float | None = Field(
		default=None, description='部件速度移动加成，一般只有脚部部件提供'
	)

	@classmethod
	def resource_name(cls) -> str:
		return 'equip'


class Equip(EquipBase, ConvertToORM['EquipORM']):
	bonus: EquipBonus | None = Field(
		default=None, description='部件效果，仅当该部件为能力加成部件时有效'
	)
	occasion: ResourceRef['EquipEffectiveOccasion'] | None = Field(
		default=None, description='部件生效场合，仅当该部件为能力加成部件时有效'
	)
	suit: ResourceRef[Suit] | None = Field(
		default=None, description='部件所属套装，仅当该部件有套装时有效'
	)
	part_type: ResourceRef['EquipType'] = Field(description='部件类型')
	pk_attribute: PkAttribute | None = Field(
		default=None,
		description='部件PK加成，战队保卫战等老玩法使用，当三个加成项都为0时为null',
	)

	@classmethod
	def get_orm_model(cls) -> type['EquipORM']:
		return EquipORM

	def to_orm(self) -> 'EquipORM':
		pk_kwargs = self.pk_attribute.model_dump() if self.pk_attribute else {}
		return EquipORM(
			id=self.id,
			name=self.name,
			speed=self.speed,
			part_type_id=self.part_type.id,
			suit_id=self.suit.id if self.suit else None,
			occasion_id=self.occasion.id if self.occasion else None,
			bonus=self.bonus.to_orm() if self.bonus else None,
			**pk_kwargs,
		)


class EquipORM(EquipBase, table=True):
	part_type_id: int = Field(foreign_key='equip_type.id')
	part_type: 'EquipTypeORM' = Relationship(
		back_populates='equip',
	)
	suit_id: int | None = Field(default=None, foreign_key='suit.id')
	suit: 'SuitORM' = Relationship(
		back_populates='equips',
	)
	bonus_id: int | None = Field(default=None, foreign_key='equip_bonus.id')
	bonus: Optional['EquipBonusORM'] = Relationship(
		back_populates='equip',
	)
	occasion_id: int | None = Field(
		default=None, foreign_key='equip_effective_occasion.id'
	)
	occasion: 'EquipEffectiveOccasionORM' = Relationship(
		back_populates='equip',
	)

	pk_hp: int | None = Field(default=None)
	pk_atk: int | None = Field(default=None)
	pk_fire_range: int | None = Field(default=None)


class EquipTypeBase(BaseCategoryModel):
	name: str = Field(description='部件类型名称')

	@classmethod
	def resource_name(cls) -> str:
		return 'equip_type'


class EquipType(EquipTypeBase, ConvertToORM['EquipTypeORM']):
	equip: list[ResourceRef] = Field(default_factory=list, description='部件列表')

	@classmethod
	def get_orm_model(cls) -> type['EquipTypeORM']:
		return EquipTypeORM

	def to_orm(self) -> 'EquipTypeORM':
		return EquipTypeORM(
			id=self.id,
			name=self.name,
		)


class EquipTypeORM(EquipTypeBase, table=True):
	equip: list['EquipORM'] = Relationship(
		back_populates='part_type',
	)


class EquipEffectiveOccasionBase(BaseCategoryModel):
	description: str = Field(description='部件生效场合描述')

	@classmethod
	def resource_name(cls) -> str:
		return 'equip_effective_occasion'


class EquipEffectiveOccasion(
	EquipEffectiveOccasionBase, ConvertToORM['EquipEffectiveOccasionORM']
):
	equip: list[ResourceRef] = Field(default_factory=list, description='部件列表')

	@classmethod
	def get_orm_model(cls) -> type['EquipEffectiveOccasionORM']:
		return EquipEffectiveOccasionORM

	def to_orm(self) -> 'EquipEffectiveOccasionORM':
		return EquipEffectiveOccasionORM(
			id=self.id,
			description=self.description,
		)


class EquipEffectiveOccasionORM(EquipEffectiveOccasionBase, table=True):
	equip: list['EquipORM'] = Relationship(
		back_populates='occasion',
	)


class EquipAnalyzer(BaseDataSourceAnalyzer):
	"""装备数据解析器"""

	@classmethod
	def get_data_import_config(cls) -> DataImportConfig:
		return DataImportConfig(
			html5_paths=('xml/items.json', 'xml/suit.json', 'xml/equip.json'),
			patch_paths=('equip_effective_occasion.json', 'equip_type.json'),
		)

	@cached_property
	def _ability_equip_map(self) -> dict[int, dict[str, Any]]:
		return {
			equip['ItemID']: equip
			for equip in self._get_data('html5', 'xml/equip.json')['Equips']['Equip']
		}

	def _get_equip_to_suit_map(self, suit_data: dict) -> dict[int, Suit]:
		"""
		获取装备到套装的映射关系
		"""
		suit_map: dict[int, Suit] = {}
		for suit in suit_data['root']['item']:
			suit: dict
			suit_id = suit['id']
			suit_bonus: SuitBonus | None = None
			equip_ids = split_string_arg(suit['cloths'])
			if part_dict := self._ability_equip_map.get(equip_ids[0]):
				effect_id = part_dict.get('SuitEffectID')
				newse_id = part_dict.get('SuitNewseId')
				if effect_id or newse_id:
					effect_args = None
					if effect_id:
						effect_args = split_string_arg(part_dict.get('SuitEffectArgs'))

					attr: SixAttributes | None = None
					# 浴火之前的套装使用EffectID+EffectArgs来表示属性加成，
					# 从浴火开始使用独立的AddArgs字段，
					# 该字段第一个参数表示是否为百分比加成
					if effect_args:
						if effect_id == 630:
							attr = SixAttributes.from_list(effect_args, percent=True)
						elif effect_id == 631:
							attr = SixAttributes.from_list(effect_args, percent=False)
						elif add_args_string := part_dict.get('AddArgs'):
							add_args = split_string_arg(add_args_string)
							percent = bool(add_args.pop(0))
							attr = SixAttributes.from_list(add_args, percent=percent)

					equip_effect = EquipEffect(
						newse_id=cast(int, newse_id),
						eid_effect=EidEffectInUse(
							effect=ResourceRef.from_model(EidEffect, id=effect_id),
							effect_args=effect_args,
						)
						if effect_id
						else None,
					)
					effective_pets = None
					pet_ids = split_string_arg(part_dict.pop('MonID', []))
					if any(pet_ids):
						effective_pets = [
							ResourceRef(
								id=pet_id,
								resource_name='pet',
							)
							for pet_id in pet_ids
						]
					suit_bonus = SuitBonus(
						effective_pets=effective_pets,
						desc=get_nested_value(suit, 'describe._cdata') or '',
						attribute=attr,
						effect=equip_effect,
					)

			suit_obj = Suit(
				id=suit_id,
				name=suit['name'],
				suit_desc=suit['suitdes'],
				equips=[
					ResourceRef.from_model(Equip, id=equip_id) for equip_id in equip_ids
				],
				transform=bool(suit.get('transform')),
				tran_speed=suit.get('tranSpeed'),
				bonus=suit_bonus,
			)
			suit_map[suit_id] = suit_obj

		return suit_map

	def analyze(self) -> tuple[AnalyzeResult, ...]:
		items_data: dict = self._get_data('html5', 'xml/items.json')
		suit_data: dict = self._get_data('html5', 'xml/suit.json')

		part_type_csv = self._get_data('patch', 'equip_type.json')
		occasion_csv = self._get_data('patch', 'equip_effective_occasion.json')

		origin_equip_map: dict[int, dict[str, Any]] = {
			item['ID']: item
			for category in items_data['Items']['Cat']
			if category['Name'] == '个人装扮'
			for item in category['Item']
		}
		suit_map = self._get_equip_to_suit_map(suit_data)
		equip_to_suit_map = {
			equip_ref.id: suit_obj
			for suit_obj in suit_map.values()
			for equip_ref in suit_obj.equips
		}

		# 处理部件
		part_type_map_for_name = {row['name']: row for row in part_type_csv.values()}
		part_type_map = create_category_map(
			part_type_csv,
			model_cls=EquipType,
			array_key='equip',
		)
		occasion_map = create_category_map(
			occasion_csv,
			model_cls=EquipEffectiveOccasion,
			array_key='equip',
		)
		equip_map: dict[int, Equip] = {}
		for equip_id, equip_dict in origin_equip_map.items():
			equip_name = equip_dict['Name']
			equip_ref = ResourceRef.from_model(Equip, id=equip_id)
			equip_bonus = None
			occasion = None

			# 处理部件加成
			if ability_equip := self._ability_equip_map.get(equip_id):
				occasion = ResourceRef.from_model(
					occasion_map[ability_equip['Occasion']]
				)
				# 获取部件加成数据
				bonus: dict[str, Any] = ability_equip['Rank'][-1]
				if desc := bonus.get('Desc'):
					attr_args = split_string_arg(bonus.get('Attribute'))
					attr = None
					if any(attr_args):
						attr = SixAttributes.from_list(
							attr_args, hp_first=True, percent=bool(bonus['AddWay'])
						)
					other_attr_args = split_string_arg(bonus.get('OtherAttribute'))
					other_attr = (
						OtherAttribute.from_list(other_attr_args)
						if any(other_attr_args)
						else None
					)
					equip_effect = None
					if effect_id := bonus.get('EffectID'):
						effect_args = split_string_arg(bonus['EffectArgs'])
						equip_effect = EquipEffect(
							eid_effect=EidEffectInUse(
								effect=ResourceRef.from_model(EidEffect, id=effect_id),
								effect_args=effect_args,
							)
							if effect_id
							else None,
							newse_id=bonus['EquipNewseId'],
						)
					equip_bonus = EquipBonus(
						attribute=attr,
						other_attribute=other_attr,
						desc=desc,
						effect=equip_effect,
					)
				occasion_map.add_element(occasion.id, equip_ref)

			suit_ref = None
			if suit_obj := equip_to_suit_map.get(equip_id):
				suit_ref = ResourceRef.from_model(
					suit_obj,
				)

			part_type_name = equip_dict.get('type')
			part_type_id = part_type_map_for_name[part_type_name]['id']
			part_type_ref = ResourceRef.from_model(part_type_map[part_type_id])

			speed = equip_dict.get('speed')  # int or null
			equip_map[equip_id] = Equip(
				id=equip_id,
				name=equip_name,
				part_type=part_type_ref,
				speed=speed,
				pk_attribute=_create_pk_attribute(equip_dict),
				suit=suit_ref,
				bonus=equip_bonus,
				occasion=occasion,
			)
			part_type_map.add_element(part_type_id, equip_ref)

		return (
			AnalyzeResult(model=Equip, data=equip_map),
			AnalyzeResult(model=Suit, data=suit_map),
			AnalyzeResult(
				model=SuitBonus,
				data={
					suit_id: suit_obj.bonus
					for suit_id, suit_obj in suit_map.items()
					if suit_obj.bonus
				},
				output_mode='db',
			),
			AnalyzeResult(model=EquipType, data=part_type_map),
			AnalyzeResult(model=EquipEffectiveOccasion, data=occasion_map),
		)

from functools import cached_property
from typing import TYPE_CHECKING, Any, Optional, TypedDict
from typing_extensions import Self

from pydantic import BaseModel
from sqlmodel import Field, Relationship, SQLModel

from solaris.analyze.analyzers.items._general import BaseItemAnalyzer
from solaris.analyze.base import DataImportConfig
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
from solaris.utils import split_string_arg

if TYPE_CHECKING:
	from solaris.parse.parsers.equip import EquipItem as UnityEquipItem
	from solaris.parse.parsers.items_optimize import (
		Item1,
		Item13,
	)
	from solaris.parse.parsers.suit import SuitConfig

	from .pet.pet import Pet, PetORM

def _create_suit_attribute(
	suit_effect_id: int | None,
	suit_effect_args: list[int],
	add_args_string: str | None,
) -> SixAttributes | None:
	"""
	创建套装属性加成

	浴火之前的套装使用EffectID+EffectArgs来表示属性加成，
	从浴火开始使用独立的AddArgs字段，
	该字段第一个参数表示是否为百分比加成
	"""
	if suit_effect_id == 630:
		return SixAttributes.from_list(suit_effect_args, percent=True)
	elif suit_effect_id == 631:
		return SixAttributes.from_list(suit_effect_args, percent=False)
	elif add_args_string:
		add_args = split_string_arg(add_args_string)
		if not add_args:
			return None

		percent = bool(add_args.pop(0))
		if not any(add_args):
			return None

		return SixAttributes.from_list(add_args, percent=percent)

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


class EquipEffect(SQLModel):
	newse_id: int | None = Field(
		default=None,
		description='部件特性ID，一部分套装使用该字段来表示效果',
	)
	eid_effect: EidEffectInUse | None = Field(
		default=None,
		description='部件效果，一部分套装使用该字段来表示效果',
	)


class EquipBonusBase(BaseResModelWithOptionalId):
	desc: str = Field(description='部件描述')

	@classmethod
	def resource_name(cls) -> str:
		return 'equip_bonus'


class EquipBonus(EquipBonusBase, EquipEffect, ConvertToORM['EquipBonusORM']):
	attribute: SixAttributes | None = Field(
		default=None, description='属性加成，仅在部件有属性加成时有效'
	)
	other_attribute: OtherAttribute | None = Field(
		default=None, description='其他属性加成，仅在部件有命中/闪避/暴击加成时有效'
	)

	@classmethod
	def get_orm_model(cls) -> type['EquipBonusORM']:
		return EquipBonusORM

	def to_orm(self) -> 'EquipBonusORM':
		other_attr_kwargs = (
			self.other_attribute.model_dump() if self.other_attribute else {}
		)
		effect_in_use_orm = None
		if self.eid_effect:
			effect_in_use_orm = self.eid_effect.to_orm()

		return EquipBonusORM(
			id=self.id,
			desc=self.desc,
			effect_in_use=effect_in_use_orm,
			newse_id=self.newse_id,
			attribute=EquipBonusAttrORM(**self.attribute.model_dump())
			if self.attribute
			else None,
			**other_attr_kwargs,
		)


class EquipBonusORM(EquipBonusBase, table=True):
	equip: 'EquipORM' = Relationship(
		back_populates='bonus',
	)

	effect_in_use_id: int | None = Field(foreign_key='eid_effect_in_use.id')
	effect_in_use: Optional['EidEffectInUseORM'] = Relationship(
		back_populates='equip_bonus',
	)
	newse_id: int | None = Field(default=None)
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


class SuitBonus(SuitBonusBase, EquipEffect, ConvertToORM['SuitBonusORM']):
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
		if self.eid_effect:
			effect_in_use_orm = self.eid_effect.to_orm()

		return SuitBonusORM(
			id=self.id,
			desc=self.desc,
			newse_id=self.newse_id,
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
	equip: list['EquipORM'] = Relationship(back_populates='occasion')


class SuitBonusItem(TypedDict):
	desc: str
	mon_id: list[int]
	effect_id: int | None
	effect_args: list[int]
	newse_id: int | None
	add_attr: SixAttributes | None


class EquipBonusItem(TypedDict):
	desc: str
	attribute: SixAttributes | None
	other_attribute: OtherAttribute | None
	effect_id: int | None
	effect_args: list[int]
	newse_id: int | None


if TYPE_CHECKING:
	class EquipItem(UnityEquipItem):
		occasion: int
		equip_bonus: EquipBonusItem | None
		suit_bonus: SuitBonusItem | None


EMPTY_EQUIP_BONUS_ITEM = {
	'Lv': 1,
	'Attribute': "0 0 0 0 0 0",
	'AddWay': 1,
	'BattleLv': "0 0 0 0 0 0",
	'OtherAttribute': "0 0 0",
	'EffectID': "",
	'EffectArgs': "",
	'Desc': "",
}


class EquipAnalyzer(BaseItemAnalyzer):
	"""装备数据解析器"""

	@classmethod
	def get_data_import_config(cls) -> DataImportConfig:
		return DataImportConfig(
			flash_paths=('config.xml.ItemSeXMLInfo.xml', 'config.xml.ItemXMLInfo.xml'),
			unity_paths=('suit.json', 'equip.json'),
			patch_paths=('equip_effective_occasion.json', 'equip_type.json'),
		) + super().get_data_import_config()

	def _create_equip_bonus_item(
		self,
		flash_equip: dict[str, Any]) -> EquipBonusItem | None:
		rank_data = flash_equip['Rank']
		if isinstance(rank_data, dict):
			equip_bonus_data = rank_data
		elif isinstance(rank_data, list):
			equip_bonus_data = rank_data[-1]
		else:
			raise ValueError(f'Invalid rank data: {rank_data}')

		if equip_bonus_data == EMPTY_EQUIP_BONUS_ITEM:
			return None

		add_way = bool(equip_bonus_data['AddWay'])
		other_attr_args = split_string_arg(equip_bonus_data['OtherAttribute'])
		other_attr = (
			OtherAttribute.from_list(other_attr_args)
			if any(other_attr_args)
			else None
		)
		attr_args = split_string_arg(equip_bonus_data['Attribute'])
		equip_attr = SixAttributes.from_list(attr_args, percent=add_way)
		return EquipBonusItem(
			desc=equip_bonus_data['Desc'],
			attribute=equip_attr,
			other_attribute=other_attr,
			effect_id=equip_bonus_data['EffectID'],
			effect_args=split_string_arg(equip_bonus_data['EffectArgs']),
			newse_id=equip_bonus_data.get('EquipNewseId'),
		)

	def _create_suit_bonus_item(
		self, flash_equip: dict[str, Any]
	) -> SuitBonusItem | None:
		suit_effect_id = flash_equip.get('SuitEffectID')
		suit_effect_args = split_string_arg(flash_equip.get('SuitEffectArgs', ''))
		suit_newse_id = flash_equip.get('SuitNewseId')
		if not any((suit_effect_id, suit_effect_args, suit_newse_id)):
			return None

		suit_attr = _create_suit_attribute(
			suit_effect_id,
			suit_effect_args,
			flash_equip.get('AddArgs'),
		)
		mon_id = (
			args if any(args := split_string_arg(flash_equip['MonID'])) else []
		)
		return SuitBonusItem(
			desc=flash_equip['Desc'],
			mon_id=mon_id,
			effect_id=suit_effect_id,
			effect_args=suit_effect_args,
			newse_id=suit_newse_id,
			add_attr=suit_attr,
		)

	@cached_property
	def ability_equip_map(self) -> dict[int, "EquipItem"]:
		unity_data: list["UnityEquipItem"] = self._get_data(
			'unity', 'equip.json'
		)['equips']['equip']
		flash_data = self._get_data(
			'flash', 'config.xml.ItemSeXMLInfo.xml'
		)['Equips']['Equip']
		flash_data_map = {i['ItemID']: i for i in flash_data}

		result: dict[int, "EquipItem"] = {}
		for equip in unity_data:
			flash_equip = flash_data_map[equip['item_id']]
			item_id = equip['item_id']
			equip_item: "EquipItem" = {
				**equip,
				'occasion': flash_equip['Occasion'],
				'equip_bonus': self._create_equip_bonus_item(flash_equip),
				'suit_bonus': self._create_suit_bonus_item(flash_equip),
			}
			result[item_id] = equip_item
		return result

	def _get_equip_to_suit_map(self, suit_data: "SuitConfig") -> dict[int, Suit]:
		"""
		获取装备到套装的映射关系
		"""
		suit_map: dict[int, Suit] = {}
		for suit in suit_data['root']['item']:
			suit_id = suit['id']
			suit_bonus: SuitBonus | None = None
			equip_ids = suit['cloths']
			if (
				(part_dict := self.ability_equip_map.get(equip_ids[0]))
				and (suit_bonus_dict := part_dict['suit_bonus'])
			):
				eid_effect_id = suit_bonus_dict['effect_id']
				eid_effect_args = suit_bonus_dict['effect_args']

				eid_effect = None
				if eid_effect_id and eid_effect_args:
					eid_effect = EidEffectInUse(
						effect=ResourceRef.from_model(EidEffect, id=eid_effect_id),
						effect_args=eid_effect_args,
					)
				suit_bonus = SuitBonus(
					desc=suit_bonus_dict['desc'],
					attribute=suit_bonus_dict['add_attr'],
					eid_effect=eid_effect,
					newse_id=suit_bonus_dict.get('newse_id'),
				)
			suit_obj = Suit(
				id=suit_id,
				name=suit['name'],
				suit_desc=suit['suitdes'],
				equips=[
					ResourceRef.from_model(Equip, id=equip_id)
					for equip_id in equip_ids
				],
				transform=bool(suit.get('transform')),
				tran_speed=suit.get('tran_speed'),
				bonus=suit_bonus,
			)
			suit_map[suit_id] = suit_obj

		return suit_map

	@cached_property
	def flash_equip_items_data(self) -> dict[int, dict[str, Any]]:
		flash_data = self._get_data(
			'flash', 'config.xml.ItemXMLInfo.xml'
		)['root']['items']
		return {
			item['ID']: item
			for category in flash_data
			if category['Name'] == '个人装扮'
			for item in category['item']
		}


	def _create_pk_attribute(self, equip_id: int) -> 'PkAttribute | None':
		equip = self.flash_equip_items_data[equip_id]
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

	def _get_equip_items_data(self) -> "dict[int, Item1 | Item13]":
		items_data_part1: list["Item1"] = self.get_category(1)['root']['items']
		items_data_part2: list["Item13"] = self.get_category(13)['root']['items']
		return {item['id']: item for item in items_data_part1 + items_data_part2}

	def analyze(self) -> tuple[AnalyzeResult, ...]:
		suit_data: "SuitConfig" = self._get_data('unity', 'suit.json')

		part_type_patch = self._get_data('patch', 'equip_type.json')
		occasion_patch = self._get_data('patch', 'equip_effective_occasion.json')

		equip_items_map = self._get_equip_items_data()
		suit_map = self._get_equip_to_suit_map(suit_data)
		equip_to_suit_map = {
			equip_ref.id: suit_obj
			for suit_obj in suit_map.values()
			for equip_ref in suit_obj.equips
		}

		# 处理部件
		part_type_map_for_name = {row['name']: row for row in part_type_patch.values()}
		part_type_map = create_category_map(
			part_type_patch,
			model_cls=EquipType,
			array_key='equip',
		)
		occasion_map = create_category_map(
			occasion_patch,
			model_cls=EquipEffectiveOccasion,
			array_key='equip',
		)
		equip_map: dict[int, Equip] = {}
		for equip_id, equip_dict in equip_items_map.items():
			equip_name = equip_dict['name']
			equip_ref = ResourceRef.from_model(Equip, id=equip_id)
			equip_bonus = None
			occasion = None

			# 处理部件加成
			if (
				(ability_equip := self.ability_equip_map.get(equip_id))
				and (bonus_dict := ability_equip['equip_bonus'])
			):
				occasion = ResourceRef.from_model(
					occasion_map[ability_equip['occasion']]
				)
				eid_effect_id = bonus_dict['effect_id']
				eid_effect_args = bonus_dict['effect_args']
				eid_effect = None
				if eid_effect_id and eid_effect_args:
					eid_effect = EidEffectInUse(
						effect=ResourceRef.from_model(EidEffect, id=eid_effect_id),
						effect_args=eid_effect_args,
					)
				equip_bonus = EquipBonus(
					desc=bonus_dict['desc'],
					attribute=bonus_dict['attribute'],
					other_attribute=bonus_dict['other_attribute'],
					eid_effect=eid_effect,
					newse_id=bonus_dict.get('newse_id'),
				)
				occasion_map.add_element(occasion.id, equip_ref)

			suit_ref = None
			if suit_obj := equip_to_suit_map.get(equip_id):
				suit_ref = ResourceRef.from_model(suit_obj)

			part_type_name = equip_dict.get('type')
			part_type_id = part_type_map_for_name[part_type_name]['id']
			part_type_ref = ResourceRef.from_model(part_type_map[part_type_id])

			speed = equip_dict.get('speed')  # int or null
			equip_map[equip_id] = Equip(
				id=equip_id,
				name=equip_name,
				part_type=part_type_ref,
				speed=speed,
				pk_attribute=self._create_pk_attribute(equip_id),
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

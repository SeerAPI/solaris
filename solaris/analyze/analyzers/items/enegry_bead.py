from typing import Any, Optional, cast

from sqlmodel import Field, Relationship

from solaris.analyze.base import BaseDataSourceAnalyzer, DataImportConfig
from solaris.analyze.model import (
	BaseResModel,
	ConvertToORM,
	EidEffect,
	EidEffectInUse,
	EidEffectInUseORM,
	ResourceRef,
	SixAttributes,
	SixAttributesORM,
)
from solaris.analyze.typing_ import AnalyzeResult
from solaris.utils import split_string_arg

from ._general import Item, ItemORM


class EnergyBeadBase(BaseResModel):
	id: int = Field(primary_key=True, foreign_key='item.id', description='能量珠ID')
	desc: str = Field(description='能量珠描述')
	idx: int = Field(
		description='能量珠效果索引'
	)  # TODO ：暂时不知道有什么用，需要研究下封包
	use_times: int = Field(description='使用次数')

	@classmethod
	def resource_name(cls) -> str:
		return 'energy_bead'


class EnergyBead(EnergyBeadBase, ConvertToORM['EnergyBeadORM']):
	item: ResourceRef['Item'] = Field(description='能量珠物品资源引用')
	effect: EidEffectInUse = Field(description='能量珠效果')
	ability_buff: SixAttributes | None = Field(
		default=None, description='能力加成数值，仅当能量珠效果为属性加成时有效'
	)

	@classmethod
	def get_orm_model(cls) -> type['EnergyBeadORM']:
		return EnergyBeadORM

	def to_orm(self) -> 'EnergyBeadORM':
		return EnergyBeadORM(
			id=self.id,
			desc=self.desc,
			idx=self.idx,
			effect_in_use=self.effect.to_orm(),
			use_times=self.use_times,
			ability_buff=EnergyBeadBuffAttrORM(
				**self.ability_buff.model_dump(),
			)
			if self.ability_buff
			else None,
		)


class EnergyBeadORM(EnergyBeadBase, table=True):
	effect_in_use: 'EidEffectInUseORM' = Relationship(
		back_populates='energy_bead',
		sa_relationship_kwargs={
			'primaryjoin': 'EnergyBeadORM.effect_in_use_id == EidEffectInUseORM.id',
		},
	)
	effect_in_use_id: int | None = Field(
		default=None, foreign_key='eid_effect_in_use.id'
	)
	ability_buff: Optional['EnergyBeadBuffAttrORM'] = Relationship(
		back_populates='energy_bead',
		sa_relationship_kwargs={
			'uselist': False,
			'primaryjoin': 'EnergyBeadORM.id == EnergyBeadBuffAttrORM.id',
		},
	)
	ability_buff_id: int | None = Field(
		default=None, foreign_key='energy_bead_buff_attr.id'
	)
	item: 'ItemORM' = Relationship(back_populates='energy_bead')


class EnergyBeadBuffAttrORM(SixAttributesORM, table=True):
	id: int | None = Field(
		default=None,
		primary_key=True,
		foreign_key='energy_bead.id',
		description='能量珠能力加成ID',
	)
	energy_bead: 'EnergyBeadORM' = Relationship(
		back_populates='ability_buff',
		sa_relationship_kwargs={
			'uselist': False,
			'primaryjoin': 'EnergyBeadORM.id == EnergyBeadBuffAttrORM.id',
		},
	)

	@classmethod
	def resource_name(cls) -> str:
		return 'energy_bead_buff_attr'


def _convert_beads_arg(args: list[int], primary: bool = False) -> SixAttributes:
	"""将能量珠加成项的参数转换为六维属性"""
	ability_args = [0 for _ in range(6)]
	position, value = args[0], args[1]
	# 初级能量珠表示加成项的参数与其他等级不同
	if primary:
		if position == 2:
			position = 3
		elif position == 3:
			position = 0
		elif position == 4:
			position = 2
		elif position == 5:
			position = 4
	else:
		position -= 1
	ability_args[position] = value
	return SixAttributes.from_list(ability_args)


class EnergyBeadAnalyzer(BaseDataSourceAnalyzer):
	@classmethod
	def get_data_import_config(cls) -> DataImportConfig:
		return DataImportConfig(
			html5_paths=(
				'xml/new_se.json',
				'xml/items.json',
				'xml/itemsTip.json',
			),
		)

	def analyze(self) -> tuple[AnalyzeResult, ...]:
		bead_map: dict[int, EnergyBead] = {}
		bead_effect_data: dict[int, dict[str, Any]] = {
			data['ItemId']: data
			for data in self._get_data('html5', 'xml/new_se.json')['NewSe']['NewSeIdx']
			if data['Stat'] == 2
		}

		desc_data: dict[int, str] = {
			data['id']: data['des']
			for data in self._get_data('html5', 'xml/itemsTip.json')['root']['item']
		}

		for item_id, effect in bead_effect_data.items():
			effect_obj = EidEffectInUse(
				effect=ResourceRef.from_model(EidEffect, id=effect['Eid']),
				effect_args=split_string_arg(effect['Args']),
			)

			effect_args = cast(list[int], effect_obj.effect_args).copy()
			ability_buff = None
			if effect.get('AddType') == 1:
				ability_buff = SixAttributes.from_list(effect_args, hp_first=True)
			elif effect_obj.effect.id == 26:
				ability_buff = _convert_beads_arg(
					effect_args, primary=effect['Idx'] < 1006
				)
			bead = EnergyBead(
				id=item_id,
				desc=desc_data[item_id],
				effect=effect_obj,
				idx=effect['Idx'],
				item=ResourceRef.from_model(
					Item,
					id=effect['ItemId'],
				),
				use_times=effect['Times'],
				ability_buff=ability_buff,
			)
			bead_map[bead.id] = bead

		return (
			AnalyzeResult(
				model=EnergyBead,
				data=bead_map,
			),
		)

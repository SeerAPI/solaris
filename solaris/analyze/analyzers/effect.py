from typing import Any

from sqlmodel import Field, Relationship

from solaris.analyze.base import BaseDataSourceAnalyzer, DataImportConfig
from solaris.analyze.model import (
	BaseCategoryModel,
	BaseResModel,
	ConvertToORM,
	EidEffect,
	EidEffectInUse,
	EidEffectInUseORM,
	ResourceRef,
)
from solaris.analyze.typing_ import AnalyzeResult
from solaris.utils import split_string_arg


class EffectSeDataBase(BaseResModel):
	name: str = Field(description='名称')
	desc: str = Field(description='描述')

	@classmethod
	def resource_name(cls) -> str:
		return ''


class EffectSeData(EffectSeDataBase):
	effect: EidEffectInUse = Field(description='效果')


class EffectSeDataORM(EffectSeDataBase):
	effect_in_use_id: int | None = Field(
		default=None, foreign_key='eid_effect_in_use.id'
	)


class VariationEffectBase(BaseResModel):
	@classmethod
	def resource_name(cls) -> str:
		return 'pet_variation'


class VariationEffect(
	VariationEffectBase, EffectSeData, ConvertToORM['VariationEffectORM']
):
	"""特质效果"""

	@classmethod
	def get_orm_model(cls) -> type['VariationEffectORM']:
		return VariationEffectORM

	def to_orm(self) -> 'VariationEffectORM':
		return VariationEffectORM(
			id=self.id,
			name=self.name,
			desc=self.desc,
			effect_in_use=self.effect.to_orm(),
		)


class VariationEffectORM(VariationEffectBase, EffectSeDataORM, table=True):
	effect_in_use: 'EidEffectInUseORM' = Relationship(
		back_populates='variation_effect',
	)


class PetEffectBase(EffectSeDataBase):
	star_level: int = Field(description='特性星级')

	@classmethod
	def resource_name(cls) -> str:
		return 'pet_effect'


class PetEffect(PetEffectBase, EffectSeData, ConvertToORM['PetEffectORM']):
	effect_group: ResourceRef['PetEffectGroup'] = Field(
		description='特性组资源引用，同特性的不同星级属于同一组'
	)

	@classmethod
	def get_orm_model(cls) -> type['PetEffectORM']:
		return PetEffectORM

	def to_orm(self) -> 'PetEffectORM':
		return PetEffectORM(
			id=self.id,
			name=self.name,
			desc=self.desc,
			effect_in_use=self.effect.to_orm(),
			star_level=self.star_level,
			effect_group_id=self.effect_group.id,
		)


class PetEffectORM(PetEffectBase, EffectSeDataORM, table=True):
	effect_in_use: 'EidEffectInUseORM' = Relationship(
		back_populates='pet_effect',
	)
	effect_group_id: int = Field(foreign_key='pet_effect_group.id')
	effect_group: 'PetEffectGroupORM' = Relationship(back_populates='effect')


class PetEffectGroupBase(BaseCategoryModel):
	name: str = Field(description='名称')

	@classmethod
	def resource_name(cls) -> str:
		return 'pet_effect_group'


class PetEffectGroup(PetEffectGroupBase, ConvertToORM['PetEffectGroupORM']):
	effect: list[ResourceRef[PetEffect]] = Field(
		default_factory=list, description='特性列表'
	)

	@classmethod
	def get_orm_model(cls) -> type['PetEffectGroupORM']:
		return PetEffectGroupORM

	def to_orm(self) -> 'PetEffectGroupORM':
		return PetEffectGroupORM(
			id=self.id,
			name=self.name,
		)


class PetEffectGroupORM(PetEffectGroupBase, table=True):
	effect: list['PetEffectORM'] = Relationship(
		back_populates='effect_group',
	)


class NewSeAnalyzer(BaseDataSourceAnalyzer):
	"""分析并提取特性/特质数据"""

	@classmethod
	def get_data_import_config(cls) -> DataImportConfig:
		return DataImportConfig(
			html5_paths=('xml/new_se.json',),
		)

	def analyze(self) -> tuple[AnalyzeResult, ...]:
		effect_data: list[dict[str, Any]] = self._get_data('html5', 'xml/new_se.json')[
			'NewSe'
		]['NewSeIdx']
		effect_map: dict[int, PetEffect] = {}
		effect_group_map: dict[str, PetEffectGroup] = {}

		variation_map: dict[int, VariationEffect] = {}
		group_id = 1
		for effect in effect_data:
			effect_obj = EidEffectInUse(
				effect=ResourceRef.from_model(EidEffect, id=effect['Eid']),
				effect_args=split_string_arg(effect['Args']),
			)
			base_data = EffectSeData(
				id=effect['Idx'],
				name=effect.get('Desc', ''),
				desc=effect.get('Intro') or effect.get('Des') or '',
				effect=effect_obj,
			)
			# 处理特性
			if effect['Stat'] == 1:
				name = effect['Desc']
				if name not in effect_group_map:
					effect_group_map[name] = PetEffectGroup(
						id=group_id, name=name, effect=[]
					)
					group_id += 1
				pet_effect = PetEffect(
					id=base_data.id,
					name=base_data.name,
					desc=base_data.desc,
					effect=base_data.effect,
					star_level=effect['StarLevel'],
					effect_group=ResourceRef.from_model(effect_group_map[name]),
				)
				effect_map[pet_effect.id] = pet_effect
				effect_group_map[name].effect.append(ResourceRef.from_model(base_data))
			# 处理特质
			elif effect['Stat'] == 4:
				variation = VariationEffect(
					id=base_data.id,
					name=base_data.name,
					desc=base_data.desc,
					effect=base_data.effect,
				)
				variation_map[base_data.id] = variation

		return (
			AnalyzeResult(
				model=PetEffect,
				data=effect_map,
			),
			AnalyzeResult(
				model=PetEffectGroup,
				data={group.id: group for group in effect_group_map.values()},
			),
			AnalyzeResult(
				model=VariationEffect,
				data=variation_map,
			),
		)

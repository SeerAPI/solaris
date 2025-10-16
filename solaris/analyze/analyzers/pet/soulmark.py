from typing import TYPE_CHECKING, Optional

from sqlmodel import Field, Relationship, SQLModel

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
from solaris.analyze.utils import CategoryMap, create_category_map
from solaris.utils import split_string_arg

if TYPE_CHECKING:
	from solaris.parse.parsers.effect_tag import EffectTagItem
	from solaris.parse.parsers.pet_effect_icon import PetEffectIconInfo

	from .pet import PetORM


class PetSoulmarkLink(SQLModel, table=True):
	pet_id: int | None = Field(default=None, primary_key=True, foreign_key='pet.id')
	soulmark_id: int | None = Field(
		default=None, primary_key=True, foreign_key='soulmark.id'
	)


class SoulmarkTagLink(SQLModel, table=True):
	soulmark_id: int | None = Field(
		default=None, primary_key=True, foreign_key='soulmark.id'
	)
	tag_id: int | None = Field(
		default=None, primary_key=True, foreign_key='soulmark_tag.id'
	)


class SoulmarkBase(BaseResModel):
	desc: str = Field(description='魂印描述')
	desc_formatting_adjustment: str | None = Field(
		default=None,
		description='魂印描述的"可格式化版本"，用于呈现Unity端中的描述排版形式'
	)
	pve_effective: bool | None = Field(
		default=None,
		description='该魂印是否PVE生效，如果为null则表示无法通过数据层面推断其是否生效',
	)
	intensified: bool = Field(description='是否是强化的魂印')
	is_adv: bool = Field(description='是否是神谕觉醒魂印')

	@classmethod
	def resource_name(cls) -> str:
		return 'soulmark'


class Soulmark(SoulmarkBase, ConvertToORM['SoulmarkORM']):
	pet: list[ResourceRef] = Field(description='可持有该魂印的精灵ID')
	effect: EidEffectInUse | None = Field(description='魂印效果')
	tag: list[ResourceRef['SoulmarkTagCategory']] = Field(
		description='魂印标签，例如强攻，断回合等'
	)
	intensified_to: ResourceRef['Soulmark'] | None = Field(
		description='强化后的魂印资源，该字段仅在该魂印有强化版时有效，否则为null'
	)
	from_: ResourceRef['Soulmark'] | None = Field(
		description='魂印资源，该字段仅在该魂印是强化/觉醒魂印时有效',
		schema_extra={'serialization_alias': 'from'},
	)

	@classmethod
	def get_orm_model(cls) -> type['SoulmarkORM']:
		return SoulmarkORM

	def to_orm(self) -> 'SoulmarkORM':
		return SoulmarkORM(
			id=self.id,
			desc=self.desc,
			intensified=self.intensified,
			is_adv=self.is_adv,
			effect_in_use=self.effect.to_orm() if self.effect else None,
			intensified_to_id=self.intensified_to.id if self.intensified_to else None,
			desc_formatting_adjustment=self.desc_formatting_adjustment,
			pve_effective=self.pve_effective,
		)


class SoulmarkORM(SoulmarkBase, table=True):
	pet: list['PetORM'] = Relationship(
		back_populates='soulmark', link_model=PetSoulmarkLink
	)
	tag: list['SoulmarkTagORM'] = Relationship(
		back_populates='soulmark', link_model=SoulmarkTagLink
	)
	effect_in_use_id: int | None = Field(
		default=None, foreign_key='eid_effect_in_use.id'
	)
	effect_in_use: EidEffectInUseORM | None = Relationship(
		back_populates='soulmark',
	)

	from_: Optional['SoulmarkORM'] = Relationship(
		back_populates='intensified_to',
		sa_relationship_kwargs={
			# "foreign_keys": "[SoulmarkORM.from_id]",
			# "primaryjoin": "SoulmarkORM.from_id == SoulmarkORM.id",
			# "remote_side": "SoulmarkORM.id",
			'uselist': False,
		},
	)
	intensified_to_id: int | None = Field(default=None, foreign_key='soulmark.id')
	intensified_to: Optional['SoulmarkORM'] = Relationship(
		back_populates='from_',
		sa_relationship_kwargs={
			'foreign_keys': '[SoulmarkORM.intensified_to_id]',
			'primaryjoin': 'SoulmarkORM.intensified_to_id == SoulmarkORM.id',
			'remote_side': 'SoulmarkORM.id',
			'uselist': False,
		},
	)


class SoulmarkTagBase(BaseCategoryModel):
	name: str = Field(description='魂印标签名称')

	@classmethod
	def resource_name(cls) -> str:
		return 'soulmark_tag'


class SoulmarkTagCategory(SoulmarkTagBase, ConvertToORM['SoulmarkTagORM']):
	soulmark: list[ResourceRef] = Field(default_factory=list, description='魂印列表')

	@classmethod
	def get_orm_model(cls) -> type['SoulmarkTagORM']:
		return SoulmarkTagORM

	def to_orm(self) -> 'SoulmarkTagORM':
		return SoulmarkTagORM(
			id=self.id,
			name=self.name,
		)


class SoulmarkTagORM(SoulmarkTagBase, table=True):
	soulmark: list['SoulmarkORM'] = Relationship(
		back_populates='tag', link_model=SoulmarkTagLink
	)


class SoulmarkAnalyzer(BaseDataSourceAnalyzer):
	@classmethod
	def get_data_import_config(cls) -> DataImportConfig:
		return DataImportConfig(
			unity_paths=('effectag.json', 'effectIcon.json', 'petEffectIcon.json'),
		)

	def analyze(self) -> tuple[AnalyzeResult, ...]:
		soulmark_data = self._get_data(
			'unity', 'effectIcon.json'
		)['root']['effect']
		tag_data: list[EffectTagItem] = self._get_data(
			'unity', 'effectag.json'
		)['data']
		pet_effect_icon_data: list["PetEffectIconInfo"] = self._get_data(
			'unity', 'petEffectIcon.json'
		)['data']
		pet_effect_icon_map: dict[int, "PetEffectIconInfo"] = {
			data['effecticonid']: data
			for data in pet_effect_icon_data
		}
		soulmark_map: dict[int, Soulmark] = {}
		tag_map: CategoryMap[
			int,
			SoulmarkTagCategory,
			ResourceRef['Soulmark']
		] = create_category_map(
			{data['id']: {'id': data['id'], 'name': data['tag']} for data in tag_data},
			model_cls=SoulmarkTagCategory,
			array_key='soulmark',
		)
		soulmark_intensify_map: dict[int, int] = {}

		for soulmark_dict in soulmark_data:
			id_ = soulmark_dict['id']
			if not (pet_ids := soulmark_dict.get('pet_id')):
				continue

			pet_refs = [
				ResourceRef(id=pet_id, resource_name='pet')
				for pet_id in pet_ids
			]

			pve_effective = None
			tags = []
			if tag_ids := soulmark_dict.get('kind'):
				pve_effective = 1 in tag_ids
				tags = [
					ResourceRef.from_model(tag_map[tag_id + 1])
					for tag_id in tag_ids
				]

			to_res = None
			if to_id := soulmark_dict.get('to'):
				soulmark_intensify_map[to_id] = id_
				to_res = ResourceRef.from_model(Soulmark, id=to_id)
			from_res = None
			if id_ in soulmark_intensify_map:
				from_id = soulmark_intensify_map[id_]
				from_res = ResourceRef.from_model(Soulmark, id=from_id)

			effect = None
			if effect_id := soulmark_dict.get('effect_id'):
				args_string = soulmark_dict.get('args')
				effect = EidEffectInUse(
					effect=ResourceRef.from_model(EidEffect, id=effect_id),
					effect_args=(
						split_string_arg(args_string) if args_string else None
					),
				)

			desc_formatting_adjustment = None
			if pet_effect_icon := pet_effect_icon_map.get(id_):
				desc_formatting_adjustment = pet_effect_icon['Desc']
				pve_effective = bool(pet_effect_icon['affectedBoss'])

			soulmark = Soulmark(
				id=id_,
				desc=soulmark_dict['tips'],
				pet=pet_refs,
				effect=effect,
				tag=tags,
				intensified_to=to_res,
				from_=from_res,
				intensified=bool(soulmark_dict['intensify']),
				is_adv=bool(soulmark_dict['is_adv']),
				desc_formatting_adjustment=desc_formatting_adjustment,
				pve_effective=pve_effective,
			)
			soulmark_map[soulmark.id] = soulmark
			for tag in tags:
				tag_map.add_element(tag.id, ResourceRef.from_model(soulmark))

		return (
			AnalyzeResult(model=Soulmark, data=soulmark_map),
			AnalyzeResult(model=SoulmarkTagCategory, data=tag_map),
		)

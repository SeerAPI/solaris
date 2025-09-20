from typing import TYPE_CHECKING, Optional

from sqlmodel import Field, Relationship, SQLModel

from solaris.analyze.base import BaseAnalyzer, DataImportConfig
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

if TYPE_CHECKING:
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
	intensified: bool = Field(description='是否是强化的魂印')
	is_adv: bool = Field(description='是否是神谕觉醒魂印')

	@classmethod
	def resource_name(cls) -> str:
		return 'soulmark'


class Soulmark(SoulmarkBase, ConvertToORM['SoulmarkORM']):
	pet: list[ResourceRef] = Field(description='可持有该魂印的精灵ID')
	effect: EidEffectInUse | None = Field(description='魂印效果')
	tag: list[ResourceRef] = Field(description='魂印标签，例如强攻，断回合等')
	intensified_to: None | ResourceRef = Field(
		description='强化后的魂印资源，该字段仅在该魂印有强化版时有效，否则为null'
	)
	from_: None | ResourceRef = Field(
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
			# from_id=self.from_.id if self.from_ else None,
			intensified_to_id=self.intensified_to.id if self.intensified_to else None,
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

	# from_id: int | None = Field(
	# default=None, foreign_key="soulmark.id", unique=True
	# )
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


class SoulmarkAnalyzer(BaseAnalyzer):
	@classmethod
	def get_data_import_config(cls) -> DataImportConfig:
		return DataImportConfig(
			html5_paths=('xml/effectIcon.json',),
			patch_paths=('soulmark_tag.json',),
		)

	def analyze(self) -> tuple[AnalyzeResult, ...]:
		soulmark_data = self._get_data('html5', 'xml/effectIcon.json')['root']['effect']
		tag_csv = self._get_data('patch', 'soulmark_tag.json')

		soulmark_map: dict[int, Soulmark] = {}
		tag_map: dict[int, SoulmarkTagCategory] = {
			tag_id: SoulmarkTagCategory(
				id=tag_id,
				name=tag_data['name'],
			)
			for tag_id, tag_data in tag_csv.items()
		}
		for soulmark_dict in soulmark_data:
			if not (pet_id_raw := soulmark_dict.get('petId')):
				continue

			if soulmark_dict['Id'] == 261:
				# 对'/'分割的id去重，并排序
				unique_ids = sorted(set(pet_id_raw.split('/')))
				pet_id_raw = '/'.join(unique_ids)

			pet_refs = [
				ResourceRef(
					id=pet_id,
					resource_name='pet',
				)
				for pet_id in split_string_arg(pet_id_raw, split_char='/')
			]
			tags = []
			if tag_ids := soulmark_dict.get('kind'):
				tags = [
					ResourceRef.from_model(tag_map[tag_id])
					for tag_id in split_string_arg(tag_ids)
				]
			to_res = None
			if to_id := soulmark_dict.get('to'):
				to_res = ResourceRef.from_model(
					Soulmark,
					id=to_id,
				)

			from_res = None
			if from_id := soulmark_dict.get('from'):
				from_res = ResourceRef.from_model(
					Soulmark,
					id=from_id,
				)
			effect = None
			if effect_id := soulmark_dict.get('effectId'):
				args_string = soulmark_dict.get('args')
				effect = EidEffectInUse(
					effect=ResourceRef.from_model(EidEffect, id=effect_id),
					effect_args=(
						split_string_arg(args_string) if args_string else None
					),
				)
			soulmark = Soulmark(
				id=soulmark_dict['Id'],
				desc=soulmark_dict['tips'],
				pet=pet_refs,
				effect=effect,
				tag=tags,
				intensified_to=to_res,
				from_=from_res,
				intensified='from' in soulmark_dict,
				is_adv='isAdv' in soulmark_dict,
			)
			soulmark_map[soulmark.id] = soulmark
			for tag in tags:
				tag_map[tag.id].soulmark.append(ResourceRef.from_model(soulmark))

		return (
			AnalyzeResult(model=Soulmark, data=soulmark_map),
			AnalyzeResult(model=SoulmarkTagCategory, data=tag_map),
		)

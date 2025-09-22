from typing import Any

from sqlmodel import Field, Relationship

from solaris.analyze.analyzers.items._general import Item, ItemORM
from solaris.analyze.base import BaseDataSourceAnalyzer, DataImportConfig
from solaris.analyze.model import BaseResModel, ConvertToORM, ResourceRef
from solaris.analyze.typing_ import AnalyzeResult

from ..pet.pet import Pet, SkillInPetORM
from ..skill import Skill


class SkillActivationItemBase(BaseResModel):
	id: int = Field(
		primary_key=True, foreign_key='item.id', description='技能激活道具ID'
	)
	name: str = Field(description='技能激活道具名称')
	item_number: int = Field(description='激活技能需要的该道具数量')

	@classmethod
	def resource_name(cls) -> str:
		return 'skill_activation_item'


class SkillActivationItem(
	SkillActivationItemBase, ConvertToORM['SkillActivationItemORM']
):
	item: ResourceRef['Item'] = Field(description='道具资源引用')
	skill: ResourceRef['Skill'] = Field(description='使用该道具激活的技能')
	pet: ResourceRef['Pet'] = Field(description='使用该道具的精灵')

	@classmethod
	def get_orm_model(cls) -> type['SkillActivationItemORM']:
		return SkillActivationItemORM

	def to_orm(self) -> 'SkillActivationItemORM':
		return SkillActivationItemORM(
			id=self.id,
			name=self.name,
			item_number=self.item_number,
		)


class SkillActivationItemORM(SkillActivationItemBase, table=True):
	item: 'ItemORM' = Relationship(back_populates='skill_activation_item')
	skill_in_pet: 'SkillInPetORM' = Relationship(back_populates='skill_activation_item')


class SkillActivationItemAnalyzer(BaseDataSourceAnalyzer):
	@classmethod
	def get_data_import_config(cls) -> DataImportConfig:
		return DataImportConfig(html5_paths=('xml/sp_hide_moves.json',))

	def analyze(self) -> tuple[AnalyzeResult, ...]:
		skill_activation_data: dict[int, dict[str, Any]] = {
			data['item']: data
			for data in self._get_data('html5', 'xml/sp_hide_moves.json')['config'][
				'SpMoves'
			]
		}

		skill_activation_map: dict[int, SkillActivationItem] = {}
		for item_id, data in skill_activation_data.items():
			skill_ref = ResourceRef.from_model(
				Skill,
				id=data['moves'],
			)
			pet_ref = ResourceRef.from_model(
				Pet,
				id=data['monster'],
			)
			item_ref = ResourceRef.from_model(
				Item,
				id=item_id,
			)
			skill_activation_map[item_id] = SkillActivationItem(
				id=item_id,
				name=data['itemname'],
				item_number=data['itemnumber'],
				item=item_ref,
				skill=skill_ref,
				pet=pet_ref,
			)

		return (
			AnalyzeResult(
				model=SkillActivationItem,
				data=skill_activation_map,
			),
		)

from typing import TYPE_CHECKING, Any, Optional

from sqlmodel import Field, Relationship

from solaris.analyze.model import BaseResModel, ConvertToORM

if TYPE_CHECKING:
	from .enegry_bead import EnergyBeadORM
	from .skill_activation_item import SkillActivationItemORM
	from .skill_stone import SkillStoneORM


def get_items_from_category_name(
	item_data: dict[str, Any],
	*,
	category_name: str,
) -> dict[str, Any]:
	"""
	通过Items.json中的Name字段，返回该分类下的所有物品数据，同时将分类的Max值应用到物品数据中。

	Args:
		item_data: 物品数据
		cat_name: 分类名称
	"""
	for cat in item_data['Items']['Cat']:
		if cat['Name'] == category_name:
			max_ = cat['Max']
			for item in cat['Item']:
				if 'Max' not in item:
					item['Max'] = max_

			return cat

	raise ValueError(f'Item class {category_name} not found')


class ItemBase(BaseResModel):
	name: str = Field(description='物品名称')
	desc: str = Field(description='物品描述')
	max: int = Field(description='物品最大数量')

	@classmethod
	def resource_name(cls) -> str:
		return 'item'


class Item(ItemBase, ConvertToORM['ItemORM']):
	@classmethod
	def get_orm_model(cls) -> type['ItemORM']:
		return ItemORM

	def to_orm(self) -> 'ItemORM':
		return ItemORM(
			id=self.id,
			name=self.name,
			desc=self.desc,
			max=self.max,
		)


class ItemORM(ItemBase, table=True):
	skill_stone: Optional['SkillStoneORM'] = Relationship(
		back_populates='item',
	)
	energy_bead: Optional['EnergyBeadORM'] = Relationship(
		back_populates='item',
	)
	skill_activation_item: Optional['SkillActivationItemORM'] = Relationship(
		back_populates='item',
	)

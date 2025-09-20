from typing import TYPE_CHECKING

from sqlmodel import Field, Relationship

from solaris.analyze.base import AnalyzeResult
from solaris.analyze.model import BaseResModel, ConvertToORM, ResourceRef
from solaris.analyze.analyzers.pet._general import BasePetAnalyzer
from solaris.analyze.utils import CategoryMap

if TYPE_CHECKING:
	from .pet import Pet, PetORM


class PetSkinBase(BaseResModel):
	id: int = Field(
		primary_key=True, description='皮肤ID，注意该字段不是头像/立绘等所使用的资源ID'
	)
	name: str = Field(description='皮肤名称')
	resource_id: int = Field(description='皮肤资源ID')
	enemy_resource_id: int | None = Field(
		default=None,
		description='该皮肤在对手侧时使用的资源的ID，仅少数皮肤存在这种资源',
	)

	@classmethod
	def resource_name(cls) -> str:
		return 'pet_skin'


class PetSkin(PetSkinBase, ConvertToORM['PetSkinORM']):
	pet: ResourceRef['Pet'] = Field(description='使用该皮肤的精灵')
	category: ResourceRef['PetSkinCategory'] = Field(description='该皮肤所属的系列')

	@classmethod
	def get_orm_model(cls) -> type['PetSkinORM']:
		return PetSkinORM

	def to_orm(self) -> 'PetSkinORM':
		return PetSkinORM(
			id=self.id,
			name=self.name,
			resource_id=self.resource_id,
			pet_id=self.pet.id,
			category_id=self.category.id,
		)


class PetSkinORM(PetSkinBase, table=True):
	pet_id: int = Field(foreign_key='pet.id')
	pet: 'PetORM' = Relationship(back_populates='skins')
	category_id: int = Field(foreign_key='pet_skin_category.id')
	category: 'PetSkinCategoryORM' = Relationship(back_populates='skins')


class PetSkinCategoryBase(BaseResModel):
	id: int = Field(primary_key=True, description='系列ID')
	name: str = Field(
		description='系列名称'
	)  # TODO: 该字段可能在数据中不存在，暂时忽略，等待csv补充

	@classmethod
	def resource_name(cls) -> str:
		return 'pet_skin_category'


class PetSkinCategory(PetSkinCategoryBase, ConvertToORM['PetSkinCategoryORM']):
	skins: list[ResourceRef['PetSkin']] = Field(
		default_factory=list, description='该系列的皮肤列表'
	)

	@classmethod
	def get_orm_model(cls) -> type['PetSkinCategoryORM']:
		return PetSkinCategoryORM

	def to_orm(self) -> 'PetSkinCategoryORM':
		return PetSkinCategoryORM(
			id=self.id,
			name=self.name,
		)


class PetSkinCategoryORM(PetSkinCategoryBase, table=True):
	skins: list['PetSkinORM'] = Relationship(back_populates='category')


class PetSkinAnalyzer(BasePetAnalyzer):
	def analyze(self) -> tuple[AnalyzeResult, ...]:
		pet_skin_data = self.pet_skin_data
		real_id_data = {
			pet['ID']: pet['RealId']
			for pet in self._get_data('html5', 'xml/monsters.json')['Monsters'][
				'Monster'
			]
			if pet['ID'] >= 1400000 and 'RealId' in pet
		}
		pet_skin_map: dict[int, PetSkin] = {}
		pet_skin_category_map: CategoryMap[
			int, PetSkinCategory, ResourceRef[PetSkin]
		] = CategoryMap(category_key='skins')
		for skin_id, pet_skin in pet_skin_data.items():
			pet_id = pet_skin['MonID']
			category_id = pet_skin.get('Type', 0)
			resource_id = 1400000 + skin_id
			if resource_id in real_id_data:
				resource_id = real_id_data[resource_id]
			pet_skin = PetSkin(
				id=skin_id,
				name=pet_skin['Name'],
				resource_id=resource_id,
				pet=ResourceRef(
					id=pet_id,
					resource_name='pet',
				),
				category=ResourceRef(
					id=category_id,
					resource_name='pet_skin_category',
				),
			)
			pet_skin_map[skin_id] = pet_skin
			if category_id not in pet_skin_category_map:
				pet_skin_category_map[category_id] = PetSkinCategory(
					id=category_id,
					name='',
				)
			pet_skin_category_map.add_element(
				category_id,
				ResourceRef.from_model(pet_skin),
			)

		return (
			AnalyzeResult(
				model=PetSkin,
				data=pet_skin_map,
			),
			AnalyzeResult(
				model=PetSkinCategory,
				data=pet_skin_category_map,
			),
		)

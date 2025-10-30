from seerapi_models.common import ResourceRef
from seerapi_models.pet import PetSkin, PetSkinCategory

from solaris.analyze.base import AnalyzeResult
from solaris.analyze.utils import CategoryMap

from ._general import BasePetAnalyzer


class PetSkinAnalyzer(BasePetAnalyzer):
	def analyze(self) -> tuple[AnalyzeResult, ...]:
		pet_skin_data = self.pet_skin_data
		real_id_data: dict[int, int] = {
			id_: pet['real_id']
			for id_, pet in self.pet_origin_data.items()
			if id_ >= 1400000 and pet['real_id'] != 0
		}
		pet_skin_map: dict[int, PetSkin] = {}
		pet_skin_category_map: CategoryMap[
			int, PetSkinCategory, ResourceRef[PetSkin]
		] = CategoryMap(category_key='skins')

		for skin_id, pet_skin in pet_skin_data.items():
			pet_id = pet_skin['mon_id']
			category_id = pet_skin.get('type', 0)
			resource_id = 1400000 + skin_id
			if resource_id in real_id_data:
				resource_id = real_id_data[resource_id]

			pet_skin = PetSkin(
				id=skin_id,
				name=pet_skin['name'],
				resource_id=resource_id,
				pet=ResourceRef(id=pet_id, resource_name='pet'),
				category=ResourceRef.from_model(id=category_id, model=PetSkinCategory),
			)
			pet_skin_map[skin_id] = pet_skin
			if category_id not in pet_skin_category_map:
				pet_skin_category_map[category_id] = PetSkinCategory(
					id=category_id,
				)
			pet_skin_category_map.add_element(
				category_id,
				ResourceRef.from_model(pet_skin)
			)

		return (
			AnalyzeResult(model=PetSkin, data=pet_skin_map),
			AnalyzeResult(model=PetSkinCategory, data=pet_skin_category_map),
		)

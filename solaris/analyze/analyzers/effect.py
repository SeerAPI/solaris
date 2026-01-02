from typing import Any

from seerapi_models.common import EidEffect, EidEffectInUse, ResourceRef
from seerapi_models.effect import (
	PetEffect,
	PetEffectGroup,
	VariationEffect,
)

from solaris.analyze.base import BaseDataSourceAnalyzer, DataImportConfig
from solaris.analyze.typing_ import AnalyzeResult
from solaris.utils import split_string_arg


def _generate_effect_alias(effect: EidEffectInUse) -> str | None:
	return '_'.join(
		[str(arg) for arg in [effect.effect.id, *(effect.effect_args or [])]]
	)


class NewSeAnalyzer(BaseDataSourceAnalyzer):
	"""分析并提取特性/特质数据"""

	@classmethod
	def get_data_import_config(cls) -> DataImportConfig:
		return DataImportConfig(unity_paths=('new_se.json',))

	@classmethod
	def get_result_res_models(cls):
		return (PetEffect, PetEffectGroup, VariationEffect)

	def analyze(self):
		effect_data: list[dict[str, Any]] = self._get_data('unity', 'new_se.json')[
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
			base_data = {
				'id': effect['Idx'],
				'name': effect.get('Desc', ''),
				'desc': effect.get('Intro') or effect.get('Des') or '',
				'effect': effect_obj,
				'effect_alias': _generate_effect_alias(effect_obj),
			}
			# 处理特性
			if effect['Stat'] == 1:
				name = base_data['name']
				if name not in effect_group_map:
					effect_group_map[name] = PetEffectGroup(
						id=group_id, name=name, effect=[]
					)
					group_id += 1
				pet_effect = PetEffect(
					**base_data,
					star_level=effect['StarLevel'],
					effect_group=ResourceRef.from_model(effect_group_map[name]),
				)
				effect_map[pet_effect.id] = pet_effect
				effect_group_map[name].effect.append(ResourceRef.from_model(pet_effect))
			# 处理特质
			elif effect['Stat'] == 4:
				variation = VariationEffect(**base_data)
				variation_map[variation.id] = variation

		return (
			AnalyzeResult(model=PetEffect, data=effect_map),
			AnalyzeResult(
				model=PetEffectGroup,
				data={group.id: group for group in effect_group_map.values()},
			),
			AnalyzeResult(model=VariationEffect, data=variation_map),
		)

from typing import TYPE_CHECKING

from seerapi_models.common import EidEffect, EidEffectInUse, ResourceRef
from seerapi_models.pet import Pet, Soulmark, SoulmarkTagCategory

from solaris.analyze.base import BaseDataSourceAnalyzer, DataImportConfig
from solaris.analyze.typing_ import AnalyzeResult
from solaris.analyze.utils import CategoryMap, create_category_map
from solaris.utils import split_string_arg

if TYPE_CHECKING:
	from solaris.parse.parsers.effect_tag import EffectTagItem
	from solaris.parse.parsers.pet_effect_icon import PetEffectIconInfo


class SoulmarkAnalyzer(BaseDataSourceAnalyzer):
	@classmethod
	def get_data_import_config(cls) -> DataImportConfig:
		return DataImportConfig(
			unity_paths=('effectag.json', 'effectIcon.json', 'petEffectIcon.json'),
		)

	def analyze(self) -> tuple[AnalyzeResult, ...]:
		soulmark_data = self._get_data('unity', 'effectIcon.json')['root']['effect']
		tag_data: list[EffectTagItem] = self._get_data('unity', 'effectag.json')['data']
		pet_effect_icon_data: list['PetEffectIconInfo'] = self._get_data(
			'unity', 'petEffectIcon.json'
		)['data']
		pet_effect_icon_map: dict[int, 'PetEffectIconInfo'] = {
			data['effecticonid']: data for data in pet_effect_icon_data
		}
		soulmark_map: dict[int, Soulmark] = {}
		tag_map: CategoryMap[int, SoulmarkTagCategory, ResourceRef['Soulmark']] = (
			create_category_map(
				{
					data['id']: {'id': data['id'], 'name': data['tag']}
					for data in tag_data
				},
				model_cls=SoulmarkTagCategory,
				array_key='soulmark',
			)
		)
		soulmark_intensify_map: dict[int, int] = {}

		for soulmark_dict in soulmark_data:
			id_ = soulmark_dict['id']
			if not (pet_ids := soulmark_dict.get('pet_id')):
				continue

			pet_refs = [ResourceRef.from_model(Pet, id=pet_id) for pet_id in pet_ids]

			pve_effective = None
			tags = []
			if tag_ids := soulmark_dict.get('kind'):
				pve_effective = 1 in tag_ids
				tags = [
					ResourceRef.from_model(tag_map[tag_id + 1]) for tag_id in tag_ids
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

from typing import TYPE_CHECKING, TypedDict

from seerapi_models.battle_effect import BattleEffect, BattleEffectCategory
from seerapi_models.common import ResourceRef

from ..base import BaseDataSourceAnalyzer, DataImportConfig
from ..typing_ import AnalyzeResult
from ..utils import create_category_map

if TYPE_CHECKING:
	from solaris.parse.parsers.battle_effects import SubEffectItem
	from solaris.parse.parsers.effect_des import EffectDesItem


class BattleEffectPatchTable(TypedDict):
	id: int
	name: str
	type: int
	desc: str
	is_restricted: bool


class BattleEffectAnalyzer(BaseDataSourceAnalyzer):
	"""异常状态数据解析器"""

	@classmethod
	def get_data_import_config(cls) -> DataImportConfig:
		return DataImportConfig(
			unity_paths=('battleEffects.json', 'effectDes.json'),
			patch_paths=('battle_effect_type.json', 'battle_effects_custom.json'),
		)

	@classmethod
	def get_result_res_models(cls):
		return (BattleEffect, BattleEffectCategory)

	def analyze(self):
		effect_patch: dict[int, BattleEffectPatchTable] = self._get_data(
			'patch', 'battle_effects_custom.json'
		)
		effect_data: dict[str, 'SubEffectItem'] = {
			effect['name']: effect
			for effect in self._get_data('unity', 'battleEffects.json')[
				'battle_effects'
			]['battle_effect'][0]['sub_effect']
		}
		effect_descs: dict[str, 'EffectDesItem'] = {
			effect['kinddes']: effect
			for effect in self._get_data('unity', 'effectDes.json')['root']['item']
		}
		restricted_effect_id: set[int] = {
			effect['icon']
			for effect_name, effect in effect_descs.items()
			if effect_name in effect_data and '限制类异常状态' in effect['desc']
		}

		effect_type_map = create_category_map(
			self._get_data('patch', 'battle_effect_type.json'),
			model_cls=BattleEffectCategory,
			array_key='effect',
		)
		effect_map: dict[int, BattleEffect] = {}
		for name, effect in effect_data.items():
			id_: int = effect['id']
			type_id = effect['efftype']
			if type_id is None:
				continue

			ref_list = [ResourceRef.from_model(effect_type_map[type_id])]
			if (
				effect_info := effect_descs.get(name)
			) is not None or id_ in effect_patch:
				if id_ in restricted_effect_id:
					ref_list.append(ResourceRef.from_model(effect_type_map[3]))
				desc = (
					effect_info['desc']
					if effect_info is not None
					else effect_patch[id_]['desc']
				)
				effect_map[id_] = BattleEffect(
					id=id_,
					name=name,
					type=ref_list,
					desc=desc,
				)
				for ref in ref_list:
					effect_type_map[ref.id].effect.append(
						ResourceRef.from_model(effect_map[id_])
					)

		return (
			AnalyzeResult(model=BattleEffect, data=effect_map),
			AnalyzeResult(model=BattleEffectCategory, data=effect_type_map),
		)


# TODO: 数据中缺少Boss Effect ID，需要通过分析游戏封包数据以进一步检查
# class BossEffectAnalyzer(Analyzer):
# """boss状态数据解析器"""

# @property
# def data_import_config(self) -> DataImportConfig:
# return DataImportConfig(
# h5_paths=("xml/bossEffectIcon.json",),
# )

# def analyze(self) -> tuple[AnalyzeResult, ...]:
# boss_effect: list[dict] = self._get_data(
# "html5", "xml/bossEffectIcon.json")["root"]["bossEffect"]
# effect_type_map: dict[int, dict] = {}

# def handle_eid(item: dict, _: Any) -> ResourceRef:
# eid = item["Eid"]
# ref = ResourceRef(
# id=eid,
# url=f"/api/v1/boss-effect-types/{eid}"
# )
# if eid not in effect_type_map:
# effect_type_map[eid] = {
# "id": eid,
# "name": item["tips"].split("：")[0],
# "effects": [],
# }
# effect_type_map[eid]["effects"].append(item)
# return ref

# boss_effect = replace_object(boss_effect, {
# "Args": lambda _, value: split_string_arg(value),
# "Eid": handle_eid,
# "Stat": none_factory,
# "sort": none_factory,
# "rows": none_factory,
# })
# for effect in boss_effect:
# effect["eid"] = effect.pop("Eid")
# effect["icon_id"] = effect.pop("iconId")
# effect["args"] = effect.pop("Args")
# effect_type_builder.add_object(list(effect_type_map.values()))
# return (
# AnalyzeResult("boss-effect", builder, boss_effect),
# AnalyzeResult("boss-effect-type",
# effect_type_builder, effect_type_map),
# )

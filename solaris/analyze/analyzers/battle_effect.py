from typing import TypedDict

from sqlmodel import Field, Relationship, SQLModel

from solaris.utils import get_nested_value

from ..base import BaseAnalyzer, DataImportConfig
from ..model import BaseCategoryModel, BaseResModel, ConvertToORM, ResourceRef
from ..typing_ import AnalyzeResult
from ..utils import create_category_map


class BattleEffectCsvTable(TypedDict):
	id: int
	name: str
	type: int
	desc: str
	is_restricted: bool


class BattleEffectCategoryLink(SQLModel, table=True):
	battle_effect_id: int | None = Field(
		default=None, foreign_key='battle_effect.id', primary_key=True
	)
	type_id: int | None = Field(
		default=None, foreign_key='battle_effect_type.id', primary_key=True
	)


class BattleEffectBase(BaseResModel):
	name: str = Field(description='状态名称')
	desc: str = Field(description='状态描述')

	@classmethod
	def resource_name(cls) -> str:
		return 'battle_effect'


class BattleEffect(BattleEffectBase, ConvertToORM['BattleEffectORM']):
	type: list[ResourceRef['BattleEffectCategory']] = Field(
		default_factory=list,
		description='状态类型，可能同时属于多个类型，例如瘫痪同时属于控制类和限制类异常',
	)

	@classmethod
	def get_orm_model(cls) -> 'type[BattleEffectORM]':
		return BattleEffectORM

	def to_orm(self) -> 'BattleEffectORM':
		return BattleEffectORM(
			id=self.id,
			name=self.name,
			desc=self.desc,
		)


class BattleEffectORM(BattleEffectBase, table=True):
	type: list['BattleEffectCategoryORM'] = Relationship(
		back_populates='effect', link_model=BattleEffectCategoryLink
	)


class BattleEffectCategoryBase(BaseCategoryModel):
	name: str = Field(description='状态类型名称')

	@classmethod
	def resource_name(cls) -> str:
		return 'battle_effect_type'


class BattleEffectCategory(
	BattleEffectCategoryBase, ConvertToORM['BattleEffectCategoryORM']
):
	effect: list[ResourceRef['BattleEffect']] = Field(
		default_factory=list, description='异常状态列表'
	)

	@classmethod
	def get_orm_model(cls) -> type['BattleEffectCategoryORM']:
		return BattleEffectCategoryORM

	def to_orm(self) -> 'BattleEffectCategoryORM':
		return BattleEffectCategoryORM(
			id=self.id,
			name=self.name,
		)


class BattleEffectCategoryORM(BattleEffectCategoryBase, table=True):
	effect: list['BattleEffectORM'] = Relationship(
		back_populates='type', link_model=BattleEffectCategoryLink
	)


class BattleEffectAnalyzer(BaseAnalyzer):
	"""异常状态数据解析器"""

	@classmethod
	def get_data_import_config(cls) -> DataImportConfig:
		return DataImportConfig(
			html5_paths=(
				'xml/battle_effects.json',
				'xml/effectDes.json',
				'json/helper.json',
			),
			patch_paths=('battle_effect_type.json', 'battle_effects_custom.json'),
		)

	def analyze(self) -> tuple[AnalyzeResult, ...]:
		effect_csv: dict[int, BattleEffectCsvTable] = self._get_data(
			'patch', 'battle_effects_custom.json'
		)
		effect_type_csv = self._get_data('patch', 'battle_effect_type.json')
		helper_data: list[dict] = self._get_data('html5', 'json/helper.json')['data']
		restricted_effect_names: set[str] = {
			effect['title']
			for effect in helper_data
			if '异常状态 限制类' in effect['searchword']
		}

		effect_data: dict[str, dict] = {
			effect['Name']: effect
			for effect in self._get_data('html5', 'xml/battle_effects.json')[
				'BattleEffects'
			]['BattleEffect'][0]['SubEffect']
		}
		effect_descs: dict[str, dict] = {
			effect['kinddes']: effect
			for effect in self._get_data('html5', 'xml/effectDes.json')['root']['item']
		}

		effect_type_map = create_category_map(
			effect_type_csv,
			model_cls=BattleEffectCategory,
			array_key='effect',
		)
		effect_map: dict[int, BattleEffect] = {}
		for name, effect in effect_data.items():
			id_: int = effect['ID']
			type_id = get_nested_value(effect_csv, [id_, 'type']) or effect['Efftype']
			ref_list = [ResourceRef.from_model(effect_type_map[type_id])]
			if (effect_info := effect_descs.get(name)) is not None or id_ in effect_csv:
				if name in restricted_effect_names:
					ref_list.append(
						ResourceRef.from_model(
							effect_type_map[3],
						)
					)
				desc = (
					effect_info['desc']
					if effect_info is not None
					else effect_csv[id_]['desc']
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
			AnalyzeResult(
				model=BattleEffect,
				data=effect_map,
			),
			AnalyzeResult(
				model=BattleEffectCategory,
				data=effect_type_map,
			),
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

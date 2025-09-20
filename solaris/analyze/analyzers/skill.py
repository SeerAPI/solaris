from dataclasses import KW_ONLY, dataclass
from typing import TYPE_CHECKING, Literal

from sqlmodel import JSON, Field, Relationship, SQLModel

from solaris.analyze.base import BaseAnalyzer, DataImportConfig
from solaris.analyze.model import (
	BaseCategoryModel,
	BaseResModel,
	BaseResModelWithOptionalId,
	ConvertToORM,
	ResourceRef,
	SkillEffectInUse,
	SkillEffectInUseORM,
)
from solaris.analyze.typing_ import AnalyzeResult
from solaris.analyze.utils import CategoryMap, create_category_map
from solaris.utils import split_string_arg

from .mintmark import SkillMintmark
from .pet.pet import SkillInPetORM

if TYPE_CHECKING:
	from .element_type import TypeCombination, TypeCombinationORM
	from .mintmark import MintmarkORM


def _slice_args(args_nums: list[int], args: list[int]) -> list[list[int]]:
	"""
	将args按args_nums以切片。
	最后一个切片会包含所有剩余的参数。
	"""
	if not args_nums:
		return []

	result = []
	start_index = 0

	# 处理到倒数第二个切片
	for num in args_nums[:-1]:
		end_index = start_index + num
		result.append(args[start_index:end_index])
		start_index = end_index

	# 最后一个切片包含所有剩余的参数
	result.append(args[start_index:])
	return result


@dataclass
class StatChange:
	atk: int
	def_: int
	sp_atk: int
	sp_def: int
	spd: int
	acc: int
	_: KW_ONLY
	# 字符串格式化模式：正符号、负符号、无符号、根据值、无数字
	format_mode: Literal['+', '-', 'unsigned', 'value', 'none'] = 'value'
	split_char: str = '、'

	def __post_init__(self):
		self.stat_info = [
			'攻击',
			'防御',
			'特攻',
			'特防',
			'速度',
			'命中',
		]
		self._format_func = {
			'+': lambda x: f'+{abs(x):d}',
			'-': lambda x: f'-{abs(x):d}',
			'unsigned': lambda x: f'{abs(x):d}',
			'value': lambda x: f'{x:+d}',
			'none': lambda x: '',
		}[self.format_mode]

	def __str__(self) -> str:
		return self.split_char.join(
			[
				f'{stat}{self._format_func(num)}'
				for stat, num in zip(self.stat_info, self.__dict__.values())
				if num != 0 and stat
			]
		)


class SkillEffectLink(SQLModel, table=True):
	"""技能效果链接表"""

	skill_id: int | None = Field(default=None, foreign_key='skill.id', primary_key=True)
	effect_in_use_id: int | None = Field(
		default=None, foreign_key='skill_effect_in_use.id', primary_key=True
	)


class EffectParamLink(SQLModel, table=True):
	"""技能效果参数链接表"""

	effect_id: int | None = Field(
		default=None, foreign_key='skill_effect_type.id', primary_key=True
	)
	param_in_type_id: int | None = Field(
		default=None, foreign_key='skill_effect_param_in_type.id', primary_key=True
	)


class SkillEffectParam(BaseResModel, ConvertToORM['SkillEffectParamORM']):
	infos: list[str] | None = Field(
		default=None,
		description='参数类型描述列表',
		sa_type=JSON,
	)

	@classmethod
	def resource_name(cls) -> str:
		return 'skill_effect_param'

	@classmethod
	def get_orm_model(cls) -> type['SkillEffectParamORM']:
		return SkillEffectParamORM

	def to_orm(self) -> 'SkillEffectParamORM':
		return SkillEffectParamORM(
			id=self.id,
			infos=self.infos,
		)


class SkillEffectParamORM(SkillEffectParam, table=True):
	in_type: list['SkillEffectParamInTypeORM'] = Relationship(
		back_populates='param',
	)


class SkillEffectParamInTypeBase(BaseResModelWithOptionalId):
	position: int = Field(description='参数位置')

	@classmethod
	def resource_name(cls) -> str:
		return 'skill_effect_param_in_type'


class SkillEffectParamInType(
	SkillEffectParamInTypeBase, ConvertToORM['SkillEffectParamInTypeORM']
):
	param: ResourceRef[SkillEffectParam] = Field(description='参数类型引用')

	@classmethod
	def get_orm_model(cls) -> type['SkillEffectParamInTypeORM']:
		return SkillEffectParamInTypeORM

	def to_orm(self) -> 'SkillEffectParamInTypeORM':
		return SkillEffectParamInTypeORM(
			id=self.id,
			param_id=self.param.id,
			position=self.position,
		)


class SkillEffectParamInTypeORM(SkillEffectParamInTypeBase, table=True):
	param_id: int = Field(foreign_key='skill_effect_param.id')
	param: 'SkillEffectParamORM' = Relationship(back_populates='in_type')
	effect: 'SkillEffectTypeORM' = Relationship(
		back_populates='param', link_model=EffectParamLink
	)


class SkillEffectTypeBase(BaseResModel):
	"""描述一条技能效果类型"""

	args_num: int = Field(description='参数数量')
	info: str = Field(description='效果描述')

	@classmethod
	def resource_name(cls) -> str:
		return 'skill_effect_type'


class SkillEffectType(SkillEffectTypeBase, ConvertToORM['SkillEffectTypeORM']):
	param: list[SkillEffectParamInType] | None = Field(
		default=None, description='参数类型列表，描述参数类型和参数位置'
	)
	skill: list[ResourceRef['Skill']] = Field(
		default_factory=list, description='使用该效果的技能列表'
	)
	# gem: list[ResourceRef] = Field(
	# default_factory=list, description="使用该效果的宝石列表"
	# )

	@classmethod
	def get_orm_model(cls) -> type['SkillEffectTypeORM']:
		return SkillEffectTypeORM

	def to_orm(self) -> 'SkillEffectTypeORM':
		return SkillEffectTypeORM(
			id=self.id,
			args_num=self.args_num,
			info=self.info,
		)


class SkillEffectTypeORM(SkillEffectTypeBase, table=True):
	param: list['SkillEffectParamInTypeORM'] = Relationship(
		back_populates='effect', link_model=EffectParamLink
	)
	in_use: list['SkillEffectInUseORM'] = Relationship(back_populates='effect')


class SkillCategoryBase(BaseCategoryModel):
	name: str = Field(description='技能分类名称')

	@classmethod
	def resource_name(cls) -> str:
		return 'skill_category'


class SkillCategory(SkillCategoryBase, ConvertToORM['SkillCategoryORM']):
	skill: list[ResourceRef['Skill']] = Field(
		default_factory=list, description='使用该分类的技能列表'
	)

	@classmethod
	def get_orm_model(cls) -> type['SkillCategoryORM']:
		return SkillCategoryORM

	def to_orm(self) -> 'SkillCategoryORM':
		return SkillCategoryORM(
			id=self.id,
			name=self.name,
		)


class SkillCategoryORM(SkillCategoryBase, table=True):
	skill: list['SkillORM'] = Relationship(back_populates='category')


class SkillHideEffectBase(BaseCategoryModel):
	name: str = Field(description='技能隐藏效果名称')
	description: str = Field(description='技能隐藏效果描述')

	@classmethod
	def resource_name(cls) -> str:
		return 'skill_hide_effect'


class SkillHideEffect(SkillHideEffectBase, ConvertToORM['SkillHideEffectORM']):
	skill: list[ResourceRef['Skill']] = Field(
		default_factory=list, description='使用该隐藏效果的技能列表'
	)

	@classmethod
	def get_orm_model(cls) -> type['SkillHideEffectORM']:
		return SkillHideEffectORM

	def to_orm(self) -> 'SkillHideEffectORM':
		return SkillHideEffectORM(
			id=self.id,
			name=self.name,
			description=self.description,
		)


class SkillHideEffectORM(SkillHideEffectBase, table=True):
	skill: list['SkillORM'] = Relationship(back_populates='hide_effect')


class SkillBase(BaseResModel):
	name: str = Field(description='技能名称')
	power: int = Field(description='技能威力')
	max_pp: int = Field(description='技能最大PP')
	accuracy: int = Field(description='技能命中率')
	crit_rate: int = Field(description='技能暴击率')
	priority: int = Field(description='技能优先级')
	must_hit: bool = Field(description='技能是否必定命中')
	info: str | None = Field(default=None, description='技能描述')

	@classmethod
	def resource_name(cls) -> str:
		return 'skill'


class Skill(SkillBase, ConvertToORM['SkillORM']):
	category: ResourceRef[SkillCategory] = Field(description='技能分类')
	type: ResourceRef['TypeCombination'] = Field(description='技能属性')
	learned_by_pet: list[ResourceRef] = Field(
		default_factory=list, description='可学习该技能的精灵列表'
	)
	skill_effect: list[SkillEffectInUse] = Field(
		default_factory=list, description='技能效果列表'
	)
	friend_skill_effect: list[SkillEffectInUse] = Field(
		default_factory=list,
		description='旧版伙伴系统强化后的技能效果',
	)
	hide_effect: ResourceRef[SkillHideEffect] | None = Field(
		default=None, description='技能隐藏效果'
	)
	mintmark: list[ResourceRef['SkillMintmark']] = Field(
		default_factory=list, description='技能刻印列表'
	)

	@classmethod
	def get_orm_model(cls) -> 'type[SkillORM]':
		return SkillORM

	def to_orm(self) -> 'SkillORM':
		return SkillORM(
			id=self.id,
			name=self.name,
			power=self.power,
			max_pp=self.max_pp,
			accuracy=self.accuracy,
			crit_rate=self.crit_rate,
			priority=self.priority,
			must_hit=self.must_hit,
			info=self.info,
			category_id=self.category.id,
			type_id=self.type.id,
			hide_effect_id=self.hide_effect.id if self.hide_effect else None,
		)


class SkillORM(SkillBase, table=True):
	category_id: int = Field(foreign_key='skill_category.id')
	category: SkillCategoryORM = Relationship(back_populates='skill')
	type_id: int = Field(foreign_key='element_type_combination.id')
	type: 'TypeCombinationORM' = Relationship(
		back_populates='skill',
	)
	mintmark: list['MintmarkORM'] = Relationship(
		back_populates='skill',
		sa_relationship_kwargs={
			'secondary': 'skillmintmarklink',
		},
	)
	skill_effect: list[SkillEffectInUseORM] = Relationship(
		back_populates='skill', link_model=SkillEffectLink
	)
	friend_skill_effect: list[SkillEffectInUseORM] = Relationship(
		back_populates='skill', link_model=SkillEffectLink
	)
	hide_effect_id: int | None = Field(default=None, foreign_key='skill_hide_effect.id')
	hide_effect: SkillHideEffectORM | None = Relationship(back_populates='skill')

	pet_links: list['SkillInPetORM'] = Relationship(
		back_populates='skill',
		# sa_relationship_kwargs={
		# "secondary": "pet",
		# }
	)


class SkillAnalyzer(BaseAnalyzer):
	@classmethod
	def get_data_import_config(cls) -> DataImportConfig:
		return DataImportConfig(
			html5_paths=(
				'xml/moves.json',
				'xml/side_effect.json',
				'xml/effectInfo.json',
			),
			patch_paths=(
				'effectInfo.json',
				'skill_hide_effect.json',
				'skill_category.json',
			),
		)

	def analyze(self) -> tuple[AnalyzeResult, ...]:
		SkillEffectInUse.model_rebuild(
			force=True,
			_parent_namespace_depth=2,
			_types_namespace={'SkillEffectType': SkillEffectType},
		)
		Skill.model_rebuild()
		hide_effect_csv = self._get_data('patch', 'skill_hide_effect.json')
		category_csv = self._get_data('patch', 'skill_category.json')

		skill_data: list[dict] = self._get_data('html5', 'xml/moves.json')['MovesTbl'][
			'Moves'
		]['Move']
		effect_type_data: list[dict] = self._get_data('html5', 'xml/effectInfo.json')[
			'root'
		]['Effect']
		effect_param_data: list[dict] = self._get_data('html5', 'xml/effectInfo.json')[
			'root'
		]['ParamType']

		effect_param_map: dict[int, SkillEffectParam] = {}
		for effect_param in effect_param_data:
			id_ = effect_param['id']
			infos = None
			if param_str := effect_param.get('params'):
				infos = param_str.split('|')
			effect_param_map[id_] = SkillEffectParam(
				id=id_,
				infos=infos,
			)

		effect_type_map: dict[int, SkillEffectType] = {}
		for effect_type in effect_type_data:
			if not (info := effect_type.get('info')):
				continue
			id_ = effect_type['id']
			params: list[SkillEffectParamInType] | None = None
			if param_list := effect_type.get('param'):
				param_list = param_list.split('|')
				params = [
					SkillEffectParamInType(
						position=start_index,
						param=ResourceRef.from_model(effect_param_map[id_]),
					)
					for id_, start_index, _ in [
						tuple(int(i) for i in param.split(',')) for param in param_list
					]
				]
			effect_type_map[id_] = SkillEffectType(
				id=id_,
				args_num=effect_type['argsNum'],
				param=params,
				info=info,
				skill=[],
			)

		def _create_skill_effect(
			type_ids: list[int], args: list[int]
		) -> list[SkillEffectInUse]:
			"""根据效果类型ID和参数列表，创建技能效果对象元组。

			Args:
				type_ids: 技能效果的类型ID列表。
				args: 所有技能效果的参数列表。

			Returns:
				一个包含SkillEffect对象的可变元组。如果出现未知效果类型或参数错误，则返回空元组。
			"""
			args_nums = []
			# 遍历每个效果类型ID，从effect_type_map中获取所需参数数量
			for i in type_ids:
				if i not in effect_type_map:
					return []

				args_nums.append(effect_type_map[i].args_num)

			# 使用_slice_args辅助函数，根据每个效果所需的参数数量，将扁平的args列表切分为嵌套列表
			sliced_args: list[list[int]] = _slice_args(
				args_nums,
				list(args),
			)
			results = []
			# 遍历切分后的参数和对应的效果类型ID
			format_mode_map = {16: 'none', 24: '-'}
			for type_id, effect_args in zip(type_ids, sliced_args):
				type_ = effect_type_map[type_id]
				# info_args用于格式化效果描述字符串，初始值为效果参数的副本
				info_args: list[int | StatChange | str | None] = list(effect_args)
				# 处理需要特殊格式化的参数
				for p in type_.param or []:
					param_index = p.position
					param_ref = p.param
					param = effect_param_map[param_ref.id]
					# param_id为0, 16, 24表示这是一个StatChange（状态变化）参数
					if (param_id := param.id) in (0, 16, 24):
						# 将6个参数合并为一个StatChange对象
						slice_ = slice(param_index, param_index + 6)

						kwargs = {}
						if mode := format_mode_map.get(param_id):
							kwargs['format_mode'] = mode

						info_args[slice_] = [
							StatChange(*effect_args[slice_], **kwargs)
						] + [None] * 5  # 由于状态变化占用6个参数位置，所以填充5个None
						continue
					# 如果参数有预定义的描述信息(param.infos)
					if isinstance(param_infos := param.infos, list):
						pos = effect_args[param_index]
						try:
							# 使用参数值作为索引，在infos中查找对应的描述文本并使用
							info_args[param_index] = param_infos[pos]
						except IndexError:
							return []
					# 额外处理id为14的参数
					elif param_id == 14:
						info_args[param_index] = f'{effect_args[param_index]:+d}'
						continue

				results.append(
					SkillEffectInUse(
						effect=ResourceRef.from_model(type_),
						args=effect_args,
						info=type_.info.format(*info_args),
					)
				)

			return results

		category_map: CategoryMap[int, SkillCategory, ResourceRef] = (
			create_category_map(
				category_csv,
				model_cls=SkillCategory,
				array_key='skill',
			)
		)
		hide_effect_map: CategoryMap[int, SkillHideEffect, ResourceRef] = (
			create_category_map(
				hide_effect_csv,
				model_cls=SkillHideEffect,
				array_key='skill',
			)
		)
		skill_map: dict[int, Skill] = {}
		for skill in skill_data:
			skill_id = skill['ID']
			skill_name = str(skill.get('Name', ''))  # 不知为何，有些技能的名称是int类型
			skill_type = ResourceRef(
				id=skill['Type'],
				resource_name='element_type_combination',
			)
			skill_category = ResourceRef.from_model(category_map[skill['Category']])
			skill_side_effect = _create_skill_effect(
				split_string_arg(skill.get('SideEffect', 0)),
				split_string_arg(skill.get('SideEffectArg', 0)),
			)
			skill_friend_side_effect = _create_skill_effect(
				split_string_arg(skill.get('FriendSideEffect', 0)),
				split_string_arg(skill.get('FriendSideEffectArg', 0)),
			)

			skill_model = Skill(
				id=skill_id,
				name=skill_name,
				type=skill_type,
				category=skill_category,
				skill_effect=skill_side_effect,
				friend_skill_effect=skill_friend_side_effect,
				hide_effect=None,
				power=skill.get('Power', 0),
				max_pp=skill.get('MaxPP', 0),
				accuracy=skill.get('Accuracy', 0),
				crit_rate=skill.get('CritRate', 0),
				priority=skill.get('Priority', 0),
				must_hit=bool(skill.get('MustHit', False)),
				info=skill.get('info'),
			)
			skill_map[skill_id] = skill_model
			skill_ref = ResourceRef.from_model(skill_model)
			# 将技能添加到技能效果列表
			for effect in skill_model.skill_effect:
				effect_id = effect.effect.id
				effect_type_map[effect_id].skill.append(skill_ref)

			# 将技能添加到技能分类
			category_map.add_element(skill_model.category.id, skill_ref)

			# 处理技能隐藏效果
			for id_, effect in hide_effect_csv.items():
				original_name = effect['original']
				if enum_value := skill.get(original_name, None):
					# PwrBindDv 有两种效果，对应相同字段的不同的值
					if original_name == 'PwrBindDv':
						hide_effect_id = 7 if enum_value == 1 else 8
					else:
						hide_effect_id = id_
					skill_model.hide_effect = ResourceRef.from_model(
						SkillHideEffect,
						id=hide_effect_id,
					)
					hide_effect_map.add_element(hide_effect_id, skill_ref)
					break

		return (
			AnalyzeResult(model=Skill, data=skill_map),
			AnalyzeResult(model=SkillEffectType, data=effect_type_map),
			AnalyzeResult(model=SkillEffectParam, data=effect_param_map),
			AnalyzeResult(model=SkillHideEffect, data=hide_effect_map),
			AnalyzeResult(model=SkillCategory, data=category_map),
		)

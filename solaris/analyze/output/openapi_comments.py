"""
集中式 API 注释配置

本文件包含所有模型的 OpenAPI 注释，作为统一的配置管理。
键为模型类名，值为 APIComment 对象。
"""

from pydantic import BaseModel, Field
import seerapi_models as M
from seerapi_models.build_model import BaseResModel


class APIComment(BaseModel):
	"""模型的 OpenAPI 说明注释"""

	name_en: str = Field(description='模型英文名称')
	name_cn: str = Field(description='模型中文名称，用于生成 summary 字段')
	examples: list = Field(
		description='模型对象示例，将被写入到 OpenAPI 模型中的 examples 字段中'
	)
	tags: list[str] = Field(
		description='模型所属的标签，将被写入到该模型相关请求操作 的 tags 字段中'
	)
	description: str = Field(
		description='模型描述，将被写入到该模型相关请求操作的 description 字段中'
	)


# API 注释字典：键为模型类名（字符串），值为 APIComment 对象
API_COMMENTS: dict[type[BaseResModel], APIComment] = {
	# 成就相关
	M.Achievement: APIComment(
		name_en='achievement',
		name_cn='成就',
		examples=[
			{
				'is_ability_bonus': False,
				'ability_desc': None,
				'type': {
					'id': 1,
					'url': 'https://api.seerapi.com/v1/achievement_type/1',
				},
				'branch': {
					'id': 1,
					'url': 'https://api.seerapi.com/v1/achievement_branch/1',
				},
				'next_level_achievement': {
					'id': 163,
					'url': 'https://api.seerapi.com/v1/achievement/163',
				},
				'prev_level_achievement': {
					'id': 161,
					'url': 'https://api.seerapi.com/v1/achievement/161',
				},
				'attr_bonus': None,
				'id': 162,
				'name': '收集精灵（二）',
				'point': 10,
				'desc': '收集10只精灵',
				'is_hide': False,
				'title_id': None,
				'title': None,
				'original_title': None,
				'hash': 'e23640c8',
			}
		],
		tags=['成就'],
		description='成就资源。该模型同时集成了具有能力加成的成就称号数据，通过is_ability_bonus字段区分。',
	),
	M.Title: APIComment(
		name_en='title',
		name_cn='成就称号',
		examples=[
			{
				'type': {
					'id': 5,
					'url': 'https://api.seerapi.com/v1/achievement_type/5',
				},
				'branch': {
					'id': 129,
					'url': 'https://api.seerapi.com/v1/achievement_branch/129',
				},
				'next_level_achievement': None,
				'prev_level_achievement': None,
				'attr_bonus': {
					'atk': 0,
					'def': 25,
					'sp_atk': 0,
					'sp_def': 25,
					'spd': 0,
					'hp': 100,
					'percent': False,
					'total': 150,
				},
				'is_ability_bonus': True,
				'ability_desc': '体力+100，防御+25，特防+25',
				'id': 300,
				'name': '神话',
				'point': 10,
				'desc': '成为2018年年费VIP',
				'is_hide': False,
				'achievement_id': 1013,
				'achievement_name': '神话',
				'original_name': '神话',
				'hash': '8388d45',
			}
		],
		tags=['成就', '称号'],
		description='成就称号资源，包含具有能力加成的成就称号数据。',
	),
	M.AchievementType: APIComment(
		name_en='achievement_type',
		name_cn='成就类型',
		examples=[
			{
				'id': 1,
				'name': '精灵类',
				'point_total': 795,
				'achievement': [],
				'branch': [
					{'id': 1, 'url': 'https://api.seerapi.com/v1/achievement_branch/1'},
					{
						'id': 49,
						'url': 'https://api.seerapi.com/v1/achievement_branch/49',
					},
					{
						'id': 62,
						'url': 'https://api.seerapi.com/v1/achievement_branch/62',
					},
					{
						'id': 100,
						'url': 'https://api.seerapi.com/v1/achievement_branch/100',
					},
					{
						'id': 101,
						'url': 'https://api.seerapi.com/v1/achievement_branch/101',
					},
					{
						'id': 102,
						'url': 'https://api.seerapi.com/v1/achievement_branch/102',
					},
					{'id': 9, 'url': 'https://api.seerapi.com/v1/achievement_branch/9'},
					{
						'id': 55,
						'url': 'https://api.seerapi.com/v1/achievement_branch/55',
					},
					{
						'id': 108,
						'url': 'https://api.seerapi.com/v1/achievement_branch/108',
					},
					{
						'id': 121,
						'url': 'https://api.seerapi.com/v1/achievement_branch/121',
					},
					{
						'id': 167,
						'url': 'https://api.seerapi.com/v1/achievement_branch/167',
					},
				],
				'hash': '6da999fa',
			}
		],
		tags=['成就', '分类'],
		description='成就类型分类。',
	),
	M.AchievementBranch: APIComment(
		name_en='achievement_branch',
		name_cn='成就分支',
		examples=[
			{
				'id': 62,
				'name': '特殊精灵收集',
				'point_total': 200,
				'is_series': False,
				'achievement': [
					{'id': 173, 'url': 'https://api.seerapi.com/v1/achievement/173'},
					{'id': 174, 'url': 'https://api.seerapi.com/v1/achievement/174'},
					{'id': 175, 'url': 'https://api.seerapi.com/v1/achievement/175'},
					{'id': 176, 'url': 'https://api.seerapi.com/v1/achievement/176'},
					{'id': 177, 'url': 'https://api.seerapi.com/v1/achievement/177'},
					{'id': 178, 'url': 'https://api.seerapi.com/v1/achievement/178'},
					{'id': 179, 'url': 'https://api.seerapi.com/v1/achievement/179'},
					{'id': 180, 'url': 'https://api.seerapi.com/v1/achievement/180'},
					{'id': 181, 'url': 'https://api.seerapi.com/v1/achievement/181'},
					{'id': 182, 'url': 'https://api.seerapi.com/v1/achievement/182'},
				],
				'type': {
					'id': 1,
					'url': 'https://api.seerapi.com/v1/achievement_type/1',
				},
				'hash': 'ae0c1d8',
			}
		],
		tags=['成就'],
		description='成就嵌套结构的中间层，没什么实际意义，仅用于还原游戏内数据结构。',
	),
	M.AchievementCategory: APIComment(
		name_en='achievement_category',
		name_cn='成就分类',
		examples=[
			{
				'id': 1,
				'name': 'hide_achievement',
				'achievement': [
					{
						'id': 312,
						'url': 'https://api.seerapi.com/v1/achievement/312',
					},
					{
						'id': 318,
						'url': 'https://api.seerapi.com/v1/achievement/318',
					},
					{
						'id': 320,
						'url': 'https://api.seerapi.com/v1/achievement/320',
					},
				],
				'hash': '3e9da18f',
			}
		],
		tags=['成就', '分类'],
		description='成就分类，目前只有一个隐藏成就的分类。',
	),
	# 战斗效果相关
	M.BattleEffect: APIComment(
		name_en='battle_effect',
		name_cn='状态',
		examples=[
			{
				'id': 20,
				'name': '失明',
				'desc': '弱化类异常状态，该状态下精灵使用攻击技能50%miss，若为必中技能则50%命中效果失效且无法造成攻击伤害',
				'type': [
					{
						'id': 1,
						'url': 'https://api.seerapi.com/v1/battle_effect_type/1',
					}
				],
				'hash': 'fa7cf7b',
			}
		],
		tags=['战斗状态', '异常状态'],
		description='战斗状态资源，包含所有战斗状态（也就是异常状态）数据。',
	),
	M.BattleEffectCategory: APIComment(
		name_en='battle_effect_type',
		name_cn='状态类型',
		examples=[
			{
				'id': 3,
				'name': '限制类',
				'effect': [
					{
						'id': 19,
						'url': 'https://api.seerapi.com/v1/battle_effect/19',
					},
					{
						'id': 32,
						'url': 'https://api.seerapi.com/v1/battle_effect/32',
					},
					{
						'id': 38,
						'url': 'https://api.seerapi.com/v1/battle_effect/38',
					},
				],
				'hash': 'ad1a9de2',
			}
		],
		tags=['战斗状态', '异常状态', '分类'],
		description='战斗状态分类，用于分类不同类型的战斗状态。',
	),
	# EID 效果
	M.EidEffect: APIComment(
		name_en='eid_effect',
		name_cn='eid效果',
		examples=[{'id': 400, 'args_num': 6, 'hash': '6a210819'}],
		tags=['eid效果'],
		description='该资源描述并整理了赛尔号内部实现的一种通用效果，'
		'魂印，特性，装备，能量珠效果在内部都通过 eid 描述，'
		'同一 eid 效果可视作判定完全相同的效果，即使它们的类型不同。',
	),
	# 元素类型
	M.ElementType: APIComment(
		name_en='element_type',
		name_cn='属性',
		examples=[{'id': 16, 'name': '圣灵', 'name_en': 'saint', 'hash': '9062249d'}],
		tags=['属性'],
		description='属性资源，该资源仅作为基础资源，保存属性克制关系（TODO）等数据。'
		'不包含双属性数据，实际使用时请使用 TypeCombination 资源。',
	),
	M.TypeCombination: APIComment(
		name_en='element_type_combination',
		name_cn='属性组合',
		examples=[
			{
				'id': 100,
				'name': '圣灵 地面',
				'name_en': 'saint_ground',
				'primary': {
					'id': 16,
					'url': 'https://api.seerapi.com/v1/element_type/16',
				},
				'secondary': {
					'id': 7,
					'url': 'https://api.seerapi.com/v1/element_type/7',
				},
				'is_double': True,
				'hash': '637da042',
			}
		],
		tags=['属性', '组合'],
		description='属性组合资源，所有包含所有的单属性和双属性数据。'
		'注意"第一属性"和"第二属性"仅为了区分两个属性，游戏内并无主次之分。',
	),
	# 特性和效果
	M.VariationEffect: APIComment(
		name_en='variation_effect',
		name_cn='特质效果',
		examples=[
			{
				'id': 1075,
				'name': '守护',
				'desc': '3%几率受到攻击伤害减半',
				'effect': {
					'effect_args': [3, 0],
					'effect': {
						'id': 404,
						'url': 'https://api.seerapi.com/v1/eid_effect/404',
					},
				},
				'hash': 'fd1200eb',
			}
		],
		tags=['精灵', '特质', '特性'],
		description='异能精灵特质效果，该资源的ID字段是一段为特质分配的特性ID区段，从1072开始。',
	),
	M.PetEffect: APIComment(
		name_en='pet_effect',
		name_cn='特性',
		examples=[
			{
				'id': 1009,
				'name': '飞空',
				'desc': '飞行属性技能威力增加5%',
				'effect': {
					'effect_args': [4, 5],
					'effect': {
						'id': 28,
						'url': 'https://api.seerapi.com/v1/eid_effect/28',
					},
				},
				'star_level': 0,
				'effect_group': {
					'id': 4,
					'url': 'https://api.seerapi.com/v1/pet_effect_group/4',
				},
				'hash': 'd7952756',
			}
		],
		tags=['精灵', '特性'],
		description='精灵特性，该资源的ID字段不一定连续。',
	),
	M.PetEffectGroup: APIComment(
		name_en='pet_effect_group',
		name_cn='特性组',
		examples=[
			{
				'id': 4,
				'name': '飞空',
				'effect': [
					{
						'id': 1009,
						'url': 'https://api.seerapi.com/v1/pet_effect/1009',
					},
					{
						'id': 1344,
						'url': 'https://api.seerapi.com/v1/pet_effect/1344',
					},
					{
						'id': 1345,
						'url': 'https://api.seerapi.com/v1/pet_effect/1345',
					},
					{
						'id': 1346,
						'url': 'https://api.seerapi.com/v1/pet_effect/1346',
					},
					{
						'id': 2075,
						'url': 'https://api.seerapi.com/v1/pet_effect/2075',
					},
					{
						'id': 2076,
						'url': 'https://api.seerapi.com/v1/pet_effect/2076',
					},
				],
				'hash': '67yh89pk',
			}
		],
		tags=['精灵', '特性', '分类'],
		description='特性组，用于分组同名特性（0~5星）。',
	),
	# 刻印相关
	M.AbilityMintmark: APIComment(
		name_en='ability_mintmark',
		name_cn='能力刻印',
		examples=[
			{
				'type': {
					'id': 0,
					'url': 'https://api.seerapi.com/v1/mintmark_type/0',
				},
				'rarity': {
					'id': 1,
					'url': 'https://api.seerapi.com/v1/mintmark_rarity/1',
				},
				'pet': None,
				'id': 10393,
				'name': '2016全国线下赛冠军刻印',
				'desc': '特攻+50 特防+30 速度+25 体力+60',
				'max_attr_value': {
					'atk': 0,
					'def': 0,
					'sp_atk': 50,
					'sp_def': 30,
					'spd': 25,
					'hp': 60,
					'percent': False,
					'total': 165,
				},
				'hash': '152efd24',
			}
		],
		tags=['刻印', '能力'],
		description='能力刻印资源。',
	),
	M.SkillMintmark: APIComment(
		name_en='skill_mintmark',
		name_cn='技能刻印',
		examples=[
			{
				'type': {
					'id': 1,
					'url': 'https://api.seerapi.com/v1/mintmark_type/1',
				},
				'rarity': {
					'id': 1,
					'url': 'https://api.seerapi.com/v1/mintmark_rarity/1',
				},
				'pet': [
					{'id': 70, 'url': 'https://api.seerapi.com/v1/pet/70'},
					{'id': 2394, 'url': 'https://api.seerapi.com/v1/pet/2394'},
				],
				'id': 20006,
				'name': '雷祭刻印',
				'desc': '命中率+10%',
				'effect': {'effect': 104, 'arg': 10},
				'skill': [
					{'id': 20085, 'url': 'https://api.seerapi.com/v1/skill/20085'}
				],
				'hash': '8d04328d',
			}
		],
		tags=['刻印', '技能'],
		description='技能刻印资源。',
	),
	M.UniversalMintmark: APIComment(
		name_en='universal_mintmark',
		name_cn='全能刻印',
		examples=[
			{
				'type': {
					'id': 3,
					'url': 'https://api.seerapi.com/v1/mintmark_type/3',
				},
				'rarity': {
					'id': 5,
					'url': 'https://api.seerapi.com/v1/mintmark_rarity/5',
				},
				'pet': None,
				'id': 42595,
				'name': '和平星-双鱼座',
				'desc': '攻击5/54,防御3/34,特防3/34,速度4/43,体力9/95',
				'mintmark_class': {
					'id': 91,
					'url': 'https://api.seerapi.com/v1/mintmark_class/91',
				},
				'base_attr_value': {
					'atk': 5,
					'def': 3,
					'sp_atk': 0,
					'sp_def': 3,
					'spd': 4,
					'hp': 9,
					'percent': False,
					'total': 24,
				},
				'max_attr_value': {
					'atk': 54,
					'def': 34,
					'sp_atk': 0,
					'sp_def': 34,
					'spd': 43,
					'hp': 95,
					'percent': False,
					'total': 260,
				},
				'hash': '84g9d7ak',
			}
		],
		tags=['刻印', '全能'],
		description='全能刻印资源。',
	),
	M.Mintmark: APIComment(
		name_en='mintmark',
		name_cn='刻印',
		examples=[
			{
				'type': {
					'id': 0,
					'url': 'https://api.seerapi.com/v1/mintmark_type/0',
				},
				'rarity': {
					'id': 1,
					'url': 'https://api.seerapi.com/v1/mintmark_rarity/1',
				},
				'pet': None,
				'id': 10017,
				'name': '中型速度刻印',
				'desc': '速度+10',
				'effect': None,
				'mintmark_class': None,
				'base_attr_value': None,
				'max_attr_value': {
					'atk': 0,
					'def': 0,
					'sp_atk': 0,
					'sp_def': 0,
					'spd': 10,
					'hp': 0,
					'percent': False,
					'total': 10,
				},
				'skill': [],
				'hash': '7d5f8c9e',
			}
		],
		tags=['刻印'],
		description='刻印资源。该模型同时集成了能力刻印、技能刻印和全能刻印三种类型的刻印数据，'
		'通过type字段区分，使用时请参考对应的细分模型。',
	),
	M.MintmarkRarityCategory: APIComment(
		name_en='mintmark_rarity',
		name_cn='刻印稀有度分类',
		examples=[
			{
				'id': 5,
				'mintmark': [
					{
						'id': 41700,
						'url': 'https://api.seerapi.com/v1/mintmark/41700',
					},
					{
						'id': 41701,
						'url': 'https://api.seerapi.com/v1/mintmark/41701',
					},
					{
						'id': 41702,
						'url': 'https://api.seerapi.com/v1/mintmark/41702',
					},
					{
						'id': 41703,
						'url': 'https://api.seerapi.com/v1/mintmark/41703',
					},
					{
						'id': 41704,
						'url': 'https://api.seerapi.com/v1/mintmark/41704',
					},
				],
				'hash': '8d04328d',
			}
		],
		tags=['刻印', '分类'],
		description='刻印稀有度分类，分为1~5星。',
	),
	M.MintmarkTypeCategory: APIComment(
		name_en='mintmark_type',
		name_cn='刻印类型分类',
		examples=[
			{
				'id': 3,
				'name': 'universal',
				'mintmark': [
					{
						'id': 40001,
						'url': 'https://api.seerapi.com/v1/mintmark/40001',
					},
					{
						'id': 40002,
						'url': 'https://api.seerapi.com/v1/mintmark/40002',
					},
					{
						'id': 40003,
						'url': 'https://api.seerapi.com/v1/mintmark/40003',
					},
				],
				'hash': '8opg02d2',
			}
		],
		tags=['刻印', '分类'],
		description='刻印类型分类，分类能力/技能/全能刻印。',
	),
	M.MintmarkClassCategory: APIComment(
		name_en='mintmark_class',
		name_cn='刻印系列分类',
		examples=[
			{
				'id': 91,
				'name': '和平星系列',
				'mintmark': [
					{
						'id': 42595,
						'url': 'https://api.seerapi.com/v1/mintmark/42595',
					},
					{
						'id': 42596,
						'url': 'https://api.seerapi.com/v1/mintmark/42596',
					},
					{
						'id': 42597,
						'url': 'https://api.seerapi.com/v1/mintmark/42597',
					},
					{
						'id': 42598,
						'url': 'https://api.seerapi.com/v1/mintmark/42598',
					},
					{
						'id': 42599,
						'url': 'https://api.seerapi.com/v1/mintmark/42599',
					},
					{
						'id': 42600,
						'url': 'https://api.seerapi.com/v1/mintmark/42600',
					},
				],
				'hash': '6d34ib2k',
			}
		],
		tags=['刻印', '系列', '分类'],
		description='刻印系列分类，用于分类全能刻印系列，例如和平星系列、创世兵魂系列等。',
	),
	# 性格
	M.Nature: APIComment(
		name_en='nature',
		name_cn='性格',
		examples=[
			{
				'id': 2,
				'name': '调皮',
				'des': '提升攻击 降低特防',
				'des2': '攻击+10% ,特防-10%',
				'attributes': {
					'atk': 0,
					'def': -10,
					'sp_atk': 10,
					'sp_def': 0,
					'spd': 0,
					'hp': 0,
					'percent': True,
					'total': 0,
				},
				'hash': 'c99d35ae',
			}
		],
		tags=['性格'],
		description='精灵性格，包含性格对属性的影响。',
	),
	# 精灵相关
	M.Pet: APIComment(
		name_en='pet',
		name_cn='精灵',
		examples=[
			{
				'id': 4186,
				'name': '镇世·乔特鲁德',
				'yielding_exp': 140,
				'catch_rate': 0,
				'evolving_lv': 0,
				'releaseable': False,
				'fusion_master': False,
				'fusion_sub': False,
				'has_resistance': True,
				'resource_id': 4186,
				'enemy_resource_id': None,
				'type': {
					'id': 15,
					'url': 'https://api.seerapi.com/v1/element_type_combination/15',
				},
				'gender': {
					'id': 1,
					'url': 'https://api.seerapi.com/v1/pet_gender/1',
				},
				'base_stats': {
					'atk': 70,
					'def': 116,
					'sp_atk': 138,
					'sp_def': 116,
					'spd': 135,
					'hp': 125,
					'percent': False,
					'total': 700,
				},
				'yielding_ev': {
					'atk': 0,
					'def': 0,
					'sp_atk': 3,
					'sp_def': 0,
					'spd': 0,
					'hp': 0,
					'percent': False,
					'total': 3,
				},
				'pet_class': {
					'id': 2174,
					'url': 'https://api.seerapi.com/v1/pet_class/2174',
				},
				'vipbuff': None,
				'mount_type': None,
				'evolution_from': None,
				'evolution_to': [],
				'learned_skill': [],
				'recommended_skill': [],
				'recommended_nature': [],
				'effect': [],
				'soulmark': [],
				'mintmark': [],
				'skin': [],
				'encyclopedia': None,
				'archive_story': [],
				'diy_stats': None,
				'hash': '3cb9d0bc',
			}
		],
		tags=['精灵'],
		description='精灵资源，如果要通过该资源获取立绘/头像等，请使用 resource_id 字段作为资源ID。',
	),
	M.PetClass: APIComment(
		name_en='pet_class',
		name_cn='精灵类别',
		examples=[
			{
				'id': 18,
				'is_variant_pet': False,
				'is_dark_pet': False,
				'is_shine_pet': False,
				'is_rare_pet': False,
				'is_breeding_pet': False,
				'is_fusion_pet': False,
				'evolution_chain': [
					{'id': 48, 'url': 'https://api.seerapi.com/v1/pet/48'},
					{'id': 49, 'url': 'https://api.seerapi.com/v1/pet/49'},
					{'id': 50, 'url': 'https://api.seerapi.com/v1/pet/50'},
					{'id': 1361, 'url': 'https://api.seerapi.com/v1/pet/1361'},
				],
				'hash': '69bd7249',
			}
		],
		tags=['精灵', '进化链', '分类'],
		description='精灵类别，这个资源用于分类同一"进化链"的精灵。'
		'（这里的进化链是指官方数据定义中一个已经停止维护的特殊字段，'
		'例如[索拉，赫拉斯，阿克希亚，阿克妮丝]属于同一个进化链，但女皇阿克希亚与冰之契约阿克希亚不在该进化链中）',
	),
	M.PetGenderCategory: APIComment(
		name_en='pet_gender',
		name_cn='精灵性别分类',
		examples=[
			{
				'id': 1,
				'name': '雄性',
				'pet': [
					{'id': 4, 'url': 'https://api.seerapi.com/v1/pet/4'},
					{'id': 5, 'url': 'https://api.seerapi.com/v1/pet/5'},
					{'id': 6, 'url': 'https://api.seerapi.com/v1/pet/6'},
				],
				'hash': '69bd7249',
			}
		],
		tags=['精灵', '性别', '分类'],
		description='精灵性别分类。',
	),
	M.PetVipBuffCategory: APIComment(
		name_en='pet_vipbuff',
		name_cn='精灵VIP加成分类',
		examples=[
			{
				'pet': [
					{'id': 164, 'url': 'https://api.seerapi.com/v1/pet/164'},
					{'id': 165, 'url': 'https://api.seerapi.com/v1/pet/165'},
					{'id': 166, 'url': 'https://api.seerapi.com/v1/pet/166'},
					{'id': 284, 'url': 'https://api.seerapi.com/v1/pet/284'},
				],
				'id': 1,
				'name': '闪光加成',
				'description': '闪光加成',
				'hash': '69bd7249',
			}
		],
		tags=['精灵', '分类'],
		description='精灵VIP加成分类，用于分类闪光/暗黑加成。',
	),
	M.PetMountTypeCategory: APIComment(
		name_en='pet_mount_type',
		name_cn='精灵坐骑类型分类',
		examples=[
			{
				'pet': [
					{'id': 483, 'url': 'https://api.seerapi.com/v1/pet/483'},
					{'id': 527, 'url': 'https://api.seerapi.com/v1/pet/527'},
					{'id': 504, 'url': 'https://api.seerapi.com/v1/pet/504'},
					{'id': 898, 'url': 'https://api.seerapi.com/v1/pet/898'},
					{'id': 1055, 'url': 'https://api.seerapi.com/v1/pet/1055'},
					{'id': 1115, 'url': 'https://api.seerapi.com/v1/pet/1115'},
					{'id': 1156, 'url': 'https://api.seerapi.com/v1/pet/1156'},
					{'id': 1482, 'url': 'https://api.seerapi.com/v1/pet/1482'},
					{'id': 1635, 'url': 'https://api.seerapi.com/v1/pet/1635'},
					{'id': 1763, 'url': 'https://api.seerapi.com/v1/pet/1763'},
					{'id': 1833, 'url': 'https://api.seerapi.com/v1/pet/1833'},
					{'id': 1956, 'url': 'https://api.seerapi.com/v1/pet/1956'},
					{'id': 2128, 'url': 'https://api.seerapi.com/v1/pet/2128'},
					{'id': 2284, 'url': 'https://api.seerapi.com/v1/pet/2284'},
					{'id': 3853, 'url': 'https://api.seerapi.com/v1/pet/3853'},
				],
				'id': 2,
				'name': '飞行',
				'description': '飞行坐骑精灵',
				'hash': 'cdfe6b83',
			}
		],
		tags=['精灵', '坐骑类型', '分类'],
		description='精灵坐骑类型分类。',
	),
	M.PetSkin: APIComment(
		name_en='pet_skin',
		name_cn='精灵皮肤',
		examples=[
			{
				'id': 774,
				'name': '世界之脉·圣灵谱尼',
				'resource_id': 1400774,
				'enemy_resource_id': None,
				'pet': {'id': 5000, 'url': 'https://api.seerapi.com/v1/pet/5000'},
				'category': {
					'id': 19,
					'url': 'https://api.seerapi.com/v1/pet_skin_category/19',
				},
				'hash': '1ba76eb6',
			}
		],
		tags=['皮肤', '精灵'],
		description='精灵皮肤资源，如果要通过该资源获取立绘/头像等，'
		'请使用 resource_id 字段作为资源ID。',
	),
	M.PetSkinCategory: APIComment(
		name_en='pet_skin_category',
		name_cn='精灵皮肤系列',
		examples=[
			{
				'id': 19,
				'skins': [
					{'id': 774, 'url': 'https://api.seerapi.com/v1/pet_skin/774'},
					{'id': 775, 'url': 'https://api.seerapi.com/v1/pet_skin/775'},
				],
				'hash': '50d67dd4',
			}
		],
		tags=['皮肤', '精灵', '分类'],
		description='精灵皮肤系列，用于分类不同系列的精灵皮肤。由于皮肤分类的名称在游戏内是硬编码的，暂不支持获取。',
	),
	M.Soulmark: APIComment(
		name_en='soulmark',
		name_cn='魂印',
		examples=[
			{
				'id': 2001,
				'desc': '自身登场之后首次受到攻击伤害时，记录此伤害；自身使用攻击技能后附加上述记录50%的百分比伤害，自身每携带一个攻击技能效果提升10%；自身使用属性技能后恢复上述记录50%的体力，自身每携带一个属性技能效果提升10%（boss无效）',
				'desc_formatting_adjustment': '<indent=0><sprite=0><indent=16>登场效果：\r\n<indent=16><sprite=3><indent=32>自身登场之后首次受到攻击伤害时，记录此伤害\r\n\r\n<indent=0><sprite=0><indent=16>技能额外效果：\r\n<indent=16><sprite=3><indent=32>自身使用攻击技能后<color=#64F9FA>附加</color>上述记录50%的<b>百分比伤害</b>，自身每携带一个攻击技能效果提升10%\r\n<indent=16><sprite=3><indent=32>自身使用属性技能后<color=#64F9FA>恢复</color>上述记录50%的<b>体力</b>，自身每携带一个属性技能效果提升10%',
				'pve_effective': False,
				'intensified': False,
				'is_adv': False,
				'pet': [{'id': 4810, 'url': 'https://api.seerapi.com/v1/pet/4810'}],
				'effect': {
					'effect_args': [1, 0],
					'effect': {
						'id': 2426,
						'url': 'https://api.seerapi.com/v1/eid_effect/2426',
					},
				},
				'tag': [
					{'id': 6, 'url': 'https://api.seerapi.com/v1/soulmark_tag/6'},
					{'id': 15, 'url': 'https://api.seerapi.com/v1/soulmark_tag/15'},
				],
				'intensified_to': None,
				'from': None,
				'hash': '17abd989',
			}
		],
		tags=['精灵', '魂印'],
		description='魂印资源，该资源还整理了魂印的强化关系。',
	),
	M.SoulmarkTagCategory: APIComment(
		name_en='soulmark_tag',
		name_cn='魂印标签',
		examples=[
			{
				'id': 6,
				'name': '恢复',
				'soulmark': [
					{'id': 6, 'url': 'https://api.seerapi.com/v1/soulmark/6'},
					{'id': 7, 'url': 'https://api.seerapi.com/v1/soulmark/7'},
				],
				'hash': '67yh89pk',
			},
		],
		tags=['精灵', '魂印', '分类'],
		description='魂印标签，例如强攻，断回合等。',
	),
	M.PetEncyclopediaEntry: APIComment(
		name_en='pet_encyclopedia_entry',
		name_cn='精灵图鉴条目',
		examples=[
			{
				'id': 70,
				'name': '雷伊',
				'has_sound': True,
				'height': 129,
				'weight': 35.8,
				'foundin': '赫尔卡星荒地',
				'food': '闪电能量',
				'introduction': '雷伊是赫尔卡星的神秘精灵，只有当雷雨天才会出现，全身被电流所包围，尽显王者风范。',
				'pet': {'id': 70, 'url': 'https://api.seerapi.com/v1/pet/70'},
				'hash': '6b2af886',
			}
		],
		tags=['精灵', '图鉴'],
		description='精灵图鉴条目，该资源部分字段来源于旧版图鉴。',
	),
	M.PetArchiveStoryEntry: APIComment(
		name_en='pet_archive_story_entry',
		name_cn='精灵故事条目',
		examples=[
			{
				'id': 650,
				'content': '我失去了我的厄孽提亚……',
				'pet': {'id': 4793, 'url': 'https://api.seerapi.com/v1/pet/4793'},
				'book': {
					'id': 1,
					'url': 'https://api.seerapi.com/v1/pet_archive_story_book/1',
				},
				'hash': '3249a54e',
			}
		],
		tags=['精灵', '故事', '图鉴'],
		description='精灵故事条目（永夜纪年/莱达物语）。',
	),
	M.PetArchiveStoryBook: APIComment(
		name_en='pet_archive_story_book',
		name_cn='精灵故事系列',
		examples=[
			{
				'id': 2,
				'name': '莱达物语',
				'entries': [
					{
						'id': 306,
						'url': 'https://api.seerapi.com/v1/pet_archive_story_entry/306',
					},
					{
						'id': 315,
						'url': 'https://api.seerapi.com/v1/pet_archive_story_entry/315',
					},
					{
						'id': 316,
						'url': 'https://api.seerapi.com/v1/pet_archive_story_entry/316',
					},
				],
				'hash': '726fd01',
			}
		],
		tags=['精灵', '故事', '图鉴', '分类'],
		description='精灵故事系列（永夜纪年/莱达物语）。',
	),
	# 技能相关
	M.SkillEffectParam: APIComment(
		name_en='skill_effect_param',
		name_cn='技能效果参数',
		examples=[
			{
				'id': 1,
				'infos': [
					'麻痹',
					'中毒',
					'烧伤',
					'',
					'寄生',
					'冻伤',
					'害怕',
					'疲惫',
					'睡眠',
					'石化',
					'混乱',
					'衰弱',
					'山神守护',
					'致命',
					'冰冻',
					'诅咒',
					'灼烧',
					'失明',
					'束缚',
					'虚弱',
					'血誓',
				],
				'hash': '9ad7c3f4',
			}
		],
		tags=['技能', '技能效果'],
		description='技能效果参数资源，该资源用于解析技能效果参数。',
	),
	M.SkillEffectType: APIComment(
		name_en='skill_effect_type',
		name_cn='技能效果',
		examples=[
			{
				'id': 1000,
				'args_num': 3,
				'info': '命中则{0}%使对手{1}，未触发则附加{2}点固定伤害',
				'info_formatting_adjustment': '命中则{0}%使对手{1}\r\n--><condition>未触发</condition>则附加{2}点固定伤害',
				'pve_effective': False,
				'param': [
					{
						'position': 1,
						'param': {
							'id': 1,
							'url': 'https://api.seerapi.com/v1/skill_effect_param/1',
						},
					}
				],
				'skill': [],
				'tag': [],
				'hash': 'e73d9b1e',
			}
		],
		tags=['技能', '技能效果'],
		description='技能效果资源，描述技能的额外效果。',
	),
	M.SkillCategory: APIComment(
		name_en='skill_category',
		name_cn='技能分类',
		examples=[
			{
				'id': 1,
				'name': '物理攻击',
				'skill': [
					{'id': 10001, 'url': 'https://api.seerapi.com/v1/skill/10001'},
					{'id': 10003, 'url': 'https://api.seerapi.com/v1/skill/10003'},
					{'id': 10004, 'url': 'https://api.seerapi.com/v1/skill/10004'},
				],
				'hash': '67in0p9v',
			},
		],
		tags=['技能', '分类'],
		description='技能分类，用于分类物理/特殊/属性技能。',
	),
	M.SkillHideEffect: APIComment(
		name_en='skill_hide_effect',
		name_cn='技能隐藏效果',
		examples=[
			{
				'id': 1,
				'name': 'crit_atk_first',
				'description': '先出手时必定暴击',
				'skill': [
					{'id': 10367, 'url': 'https://api.seerapi.com/v1/skill/10367'},
					{'id': 15478, 'url': 'https://api.seerapi.com/v1/skill/15478'},
					{'id': 15913, 'url': 'https://api.seerapi.com/v1/skill/15913'},
					{'id': 16040, 'url': 'https://api.seerapi.com/v1/skill/16040'},
				],
				'hash': '32045f52',
			}
		],
		tags=['技能', '技能效果'],
		description='技能隐藏效果，该资源描述了技能的特殊隐藏效果，'
		'例如精灵"速度史莱姆"的技能"迅捷撞击"，效果为"若先出手则必定打出致命一击（CritAtkFirst）"。',
	),
	M.SkillEffectTypeTag: APIComment(
		name_en='skill_effect_type_tag',
		name_cn='技能效果类型标签',
		examples=[
			{
				'id': 5734,
				'name': '消除护罩',
				'effect': [
					{
						'id': 1828,
						'url': 'https://api.seerapi.com/v1/skill_effect_type/1828',
					},
					{
						'id': 1989,
						'url': 'https://api.seerapi.com/v1/skill_effect_type/1989',
					},
					{
						'id': 2311,
						'url': 'https://api.seerapi.com/v1/skill_effect_type/2311',
					},
				],
				'hash': 'c8a9b0d3',
			}
		],
		tags=['技能', '技能效果', '标签'],
		description='技能效果类型标签，用于标记技能效果的类型。',
	),
	M.Skill: APIComment(
		name_en='skill',
		name_cn='技能',
		examples=[
			{
				'id': 38088,
				'name': '圣武·虚极拓世',
				'power': 160,
				'max_pp': 5,
				'accuracy': 95,
				'crit_rate': 6.25,
				'priority': 0,
				'must_hit': True,
				'atk_num': 1,
				'info': None,
				'category': {
					'id': 1,
					'url': 'https://api.seerapi.com/v1/skill_category/1',
				},
				'type': {
					'id': 129,
					'url': 'https://api.seerapi.com/v1/element_type_combination/129',
				},
				'learned_by_pet': [],
				'skill_effect': [],
				'hide_effect': [],
				'hash': 'c9e0b3d6',
			}
		],
		tags=['技能'],
		description='技能资源。',
	),
	# 道具相关
	M.EnergyBead: APIComment(
		name_en='energy_bead',
		name_cn='能量珠',
		examples=[
			{
				'id': 300030,
				'name': '防御能量珠',
				'desc': '增加精灵防御能力20点（赛尔间对战无效）',
				'idx': 1001,
				'use_times': 20,
				'item': {
					'id': 300030,
					'url': 'https://api.seerapi.com/v1/item/300030',
				},
				'effect': {
					'effect_args': [1, 20],
					'effect': {
						'id': 26,
						'url': 'https://api.seerapi.com/v1/eid_effect/26',
					},
				},
				'ability_buff': {
					'atk': 0,
					'def': 20,
					'sp_atk': 0,
					'sp_def': 0,
					'spd': 0,
					'hp': 0,
					'percent': False,
					'total': 20,
				},
				'hash': 'f8d9c3eb',
			}
		],
		tags=['能量珠', '道具'],
		description='能量珠资源。',
	),
	M.Suit: APIComment(
		name_en='suit',
		name_cn='套装',
		examples=[
			{
				'id': 393,
				'name': '笑傲巅峰套装',
				'transform': False,
				'tran_speed': 0,
				'suit_desc': '赛尔们在冒险中获得的套装，能够改变外观或者增强力量',
				'equips': [
					{
						'id': 1300794,
						'url': 'https://api.seerapi.com/v1/equip/1300794',
					},
					{
						'id': 1300795,
						'url': 'https://api.seerapi.com/v1/equip/1300795',
					},
					{
						'id': 1300796,
						'url': 'https://api.seerapi.com/v1/equip/1300796',
					},
					{
						'id': 1300797,
						'url': 'https://api.seerapi.com/v1/equip/1300797',
					},
				],
				'bonus': {
					'newse_id': 7745,
					'eid_effect': None,
					'desc': '战斗力+2000',
					'attribute': {
						'atk': 0,
						'def': 0,
						'sp_atk': 0,
						'sp_def': 0,
						'spd': 0,
						'hp': 0,
						'percent': False,
						'total': 0,
					},
					'other_attribute': {
						'hit_rate': 0,
						'dodge_rate': 0,
						'crit_rate': 0,
						'resistance': 0,
						'remark': '',
					},
				},
				'hash': 'c73f4be8',
			}
		],
		tags=['装备', '套装'],
		description='赛尔套装资源。',
	),
	M.Equip: APIComment(
		name_en='equip',
		name_cn='部件',
		examples=[
			{
				'id': 1300694,
				'name': '典狱长头盔',
				'speed': 0,
				'item': {
					'id': 1300694,
					'url': 'https://api.seerapi.com/v1/item/1300694',
				},
				'bonus': {
					'newse_id': None,
					'eid_effect': None,
					'desc': '背包内精灵命中+4%',
					'attribute': {
						'atk': 0,
						'def': 0,
						'sp_atk': 0,
						'sp_def': 0,
						'spd': 0,
						'hp': 0,
						'percent': True,
						'total': 0,
					},
					'other_attribute': {
						'hit_rate': 4,
						'dodge_rate': 0,
						'crit_rate': 0,
						'resistance': 0,
						'remark': '',
					},
				},
				'type': {'id': 0, 'url': 'https://api.seerapi.com/v1/equip_type/0'},
				'effective_occasion': {
					'id': 0,
					'url': 'https://api.seerapi.com/v1/equip_effective_occasion/0',
				},
				'suit': [{'id': 208, 'url': 'https://api.seerapi.com/v1/suit/208'}],
				'hash': 'd6e0c3f9',
			}
		],
		tags=['装备', '部件'],
		description='赛尔装备部件资源。',
	),
	M.EquipType: APIComment(
		name_en='equip_type',
		name_cn='部件类型',
		examples=[
			{
				'id': 4,
				'name': 'foot',
				'equip': [
					{
						'id': 100829,
						'url': 'https://api.seerapi.com/v1/equip/100829',
					},
					{
						'id': 100826,
						'url': 'https://api.seerapi.com/v1/equip/100826',
					},
				],
				'hash': '557fce0f',
			}
		],
		tags=['装备', '部件', '分类'],
		description='赛尔装备部件类型，分为头部，手部，腰部，脚部，背景，星际座驾。',
	),
	M.EquipEffectiveOccasion: APIComment(
		name_en='equip_effective_occasion',
		name_cn='部件能力加成生效场合',
		examples=[
			{
				'id': 0,
				'description': '全部战斗有效',
				'equip': [
					{
						'id': 100526,
						'url': 'https://api.seerapi.com/v1/equip/100526',
					},
					{
						'id': 100525,
						'url': 'https://api.seerapi.com/v1/equip/100525',
					},
				],
				'hash': '557fce0f',
			}
		],
		tags=['装备', '部件', '分类'],
		description='赛尔能力加成装备生效场合，分为全部，仅赛尔间对战（PVP），仅对Boss有效（PVE）。',
	),
	M.SkillStone: APIComment(
		name_en='skill_stone',
		name_cn='技能石',
		examples=[
			{
				'id': 102,
				'name': 'C级虫系技能石',
				'rank': 2,
				'power': 60,
				'max_pp': 25,
				'accuracy': 100,
				'category': {
					'id': 225,
					'url': 'https://api.seerapi.com/v1/skill_stone_category/225',
				},
				'item': {
					'id': 1100102,
					'url': 'https://api.seerapi.com/v1/item/1100102',
				},
				'effect': [
					{
						'prob': 0.15,
						'effect': [
							{
								'info': '10%降低对手所有技能1点PP值，然后若对手所选择的技能PP值为0则当回合对手无法行动',
								'args': [10, 1],
								'effect': {
									'id': 39,
									'url': 'https://api.seerapi.com/v1/skill_effect_type/39',
								},
							}
						],
					}
				],
				'hash': 'f9ea0bc4',
			}
		],
		tags=['技能石', '道具'],
		description='技能石资源。',
	),
	M.SkillStoneCategory: APIComment(
		name_en='skill_stone_category',
		name_cn='技能石分类',
		examples=[
			{
				'id': 225,
				'name': '虫系技能石',
				'skill_stone': [
					{
						'id': 105,
						'url': 'https://api.seerapi.com/v1/skill_stone/105',
					},
					{
						'id': 104,
						'url': 'https://api.seerapi.com/v1/skill_stone/104',
					},
					{
						'id': 103,
						'url': 'https://api.seerapi.com/v1/skill_stone/103',
					},
					{
						'id': 102,
						'url': 'https://api.seerapi.com/v1/skill_stone/102',
					},
					{
						'id': 101,
						'url': 'https://api.seerapi.com/v1/skill_stone/101',
					},
				],
				'type': {
					'id': 12,
					'url': 'https://api.seerapi.com/v1/element_type_combination/12',
				},
				'hash': 'e7b9c0d4',
			}
		],
		tags=['技能石', '道具', '分类'],
		description='技能石分类，按属性分类。',
	),
	M.Gem: APIComment(
		name_en='gem',
		name_cn='宝石',
		examples=[
			{
				'next_level_gem': {
					'id': 1800203,
					'url': 'https://api.seerapi.com/v1/gem/1800203',
				},
				'category': {
					'id': 101,
					'url': 'https://api.seerapi.com/v1/gem_category/101',
				},
				'effect': [
					{
						'info': '使用技能10%不消耗PP值',
						'args': [10],
						'effect': {
							'id': 1703,
							'url': 'https://api.seerapi.com/v1/skill_effect_type/1703',
						},
					}
				],
				'item': {
					'id': 1800202,
					'url': 'https://api.seerapi.com/v1/item/1800202',
				},
				'id': 1800202,
				'name': '活力维持宝石Ⅱ',
				'level': 2,
				'generation_id': 2,
				'inlay_rate': 100,
				'equivalent_level1_count': None,
				'fail_compensate_range': None,
				'upgrade_cost': 10000,
				'hash': 'fd6c4a6a',
			}
		],
		tags=['刻印宝石', '刻印', '道具'],
		description='刻印宝石，返回的模型中同时包含一代和二代宝石的相关字段，可通过generation_id字段区分。',
	),
	M.GemGen1: APIComment(
		name_en='gem_gen1',
		name_cn='一代刻印宝石',
		examples=[
			{
				'next_level_gem': {
					'id': 1800002,
					'url': 'https://api.seerapi.com/v1/gem/1800002',
				},
				'category': {
					'id': 1,
					'url': 'https://api.seerapi.com/v1/gem_category/1',
				},
				'effect': [
					{
						'info': '命中后3%令对方冻伤',
						'args': [3],
						'effect': {
							'id': 14,
							'url': 'https://api.seerapi.com/v1/skill_effect_type/14',
						},
					}
				],
				'item': {
					'id': 1800001,
					'url': 'https://api.seerapi.com/v1/item/1800001',
				},
				'id': 1800001,
				'name': '冻伤宝石Lv1',
				'level': 1,
				'inlay_rate': 0.85,
				'equivalent_level1_count': 1,
				'fail_compensate_range': [1, 1],
				'hash': 'c9a7b3ed',
			}
		],
		tags=['刻印宝石', '刻印', '道具'],
		description='一代刻印宝石资源。',
	),
	M.GemGen2: APIComment(
		name_en='gem_gen2',
		name_cn='二代刻印宝石',
		examples=[
			{
				'next_level_gem': {
					'id': 1800203,
					'url': 'https://api.seerapi.com/v1/gem/1800203',
				},
				'category': {
					'id': 101,
					'url': 'https://api.seerapi.com/v1/gem_category/101',
				},
				'effect': [
					{
						'info': '使用技能10%不消耗PP值',
						'args': [10],
						'effect': {
							'id': 1703,
							'url': 'https://api.seerapi.com/v1/skill_effect_type/1703',
						},
					}
				],
				'item': {
					'id': 1800202,
					'url': 'https://api.seerapi.com/v1/item/1800202',
				},
				'id': 1800202,
				'name': '活力维持宝石Ⅱ',
				'level': 2,
				'generation_id': 2,
				'upgrade_cost': 10000,
				'hash': '51a1a1',
			}
		],
		tags=['刻印宝石', '刻印', '道具'],
		description='二代刻印宝石资源。',
	),
	M.GemCategory: APIComment(
		name_en='gem_category',
		name_cn='宝石类别',
		examples=[
			{
				'id': 1,
				'name': '冻伤宝石',
				'generation_id': 1,
				'gem': [
					{
						'id': 1800001,
						'url': 'https://api.seerapi.com/v1/gem/1800001',
					},
					{
						'id': 1800002,
						'url': 'https://api.seerapi.com/v1/gem/1800002',
					},
					{
						'id': 1800003,
						'url': 'https://api.seerapi.com/v1/gem/1800003',
					},
					{
						'id': 1800004,
						'url': 'https://api.seerapi.com/v1/gem/1800004',
					},
					{
						'id': 1800005,
						'url': 'https://api.seerapi.com/v1/gem/1800005',
					},
				],
				'hash': 'e9c0d3f7',
			}
		],
		tags=['刻印宝石', '刻印', '道具', '分类'],
		description='宝石类别，用于分类同一效果的不同等级宝石。',
	),
	M.GemGenCategory: APIComment(
		name_en='gem_generation',
		name_cn='宝石世代类别',
		examples=[
			{
				'id': 2,
				'gem_category': [
					{
						'id': 1800201,
						'url': 'https://api.seerapi.com/v1/gem/1800201',
					},
					{
						'id': 1800202,
						'url': 'https://api.seerapi.com/v1/gem/1800202',
					},
					{
						'id': 1800203,
						'url': 'https://api.seerapi.com/v1/gem/1800203',
					},
				],
				'hash': 'b194c178',
			}
		],
		tags=['刻印宝石', '刻印', '道具', '分类'],
		description='宝石世代类别，用于分类不同世代的宝石。',
	),
	M.SkillActivationItem: APIComment(
		name_en='skill_activation_item',
		name_cn='精灵技能激活道具',
		examples=[
			{
				'id': 1725369,
				'name': '龙吟咖啡',
				'item_number': 3,
				'item': {
					'id': 1725369,
					'url': 'https://api.seerapi.com/v1/item/1725369',
				},
				'skill': {
					'id': 28355,
					'url': 'https://api.seerapi.com/v1/skill/28355',
				},
				'pet': {'id': 4401, 'url': 'https://api.seerapi.com/v1/pet/4401'},
				'hash': 'b7c9c4ef',
			}
		],
		tags=['技能激活道具', '道具', '技能', '精灵'],
		description='精灵技能激活道具，返回的模型中包含技能和精灵相关的引用，以及激活该技能所需的道具数量。',
	),
}


def get_api_comment(model_class: type[BaseResModel]) -> APIComment:
	"""
	根据模型类获取对应的 API 注释

	Args:
	    model_class: 模型类

	Returns:
	    APIComment 对象，如果未找到则返回 None
	"""
	if model_class not in API_COMMENTS:
		raise ValueError(f'模型 {model_class} 未配置 API 注释')

	return API_COMMENTS[model_class]


__all__ = ['get_api_comment']

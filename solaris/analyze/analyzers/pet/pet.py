from typing import TYPE_CHECKING, Any, Optional, cast

from pydantic import BaseModel
from sqlmodel import Field, Integer, Relationship, SQLModel

from solaris.analyze.model import (
	BaseCategoryModel,
	BaseResModel,
	ConvertToORM,
	ResourceRef,
	SixAttributes,
	SixAttributesORM,
)
from solaris.analyze.typing_ import AnalyzeResult, CsvTable
from solaris.analyze.utils import CategoryMap, create_category_map
from solaris.utils import get_nested_value

from ._general import BasePetAnalyzer

if TYPE_CHECKING:
	from ..element_type import TypeCombination, TypeCombinationORM
	from ..equip import SuitBonusORM
	from ..items.skill_activation_item import (
		SkillActivationItem,
		SkillActivationItemORM,
	)
	from ..mintmark import MintmarkORM
	from ..skill import Skill, SkillORM
	from .pet_skin import PetSkinORM
	from .petbook import (
		PetArchiveStoryEntry,
		PetArchiveStoryEntryORM,
		PetEncyclopediaEntry,
		PetEncyclopediaEntryORM,
	)
	from .soulmark import Soulmark, SoulmarkORM


def _handle_yielding_ev(value: str | int) -> SixAttributes:
	if isinstance(value, str):
		if len(value) <= 6:
			value = ' '.join(s for s in value)
		return SixAttributes.from_string(value, hp_first=True)
	return SixAttributes.from_list(
		[
			int(s) for s in str(value).ljust(6, '0')
		],  # TODO: 需要游戏内测试以检查该处理是否正确
		hp_first=True,
	)


class BaseStatORM(SixAttributesORM, table=True):
	id: int | None = Field(
		default=None,
		primary_key=True,
		foreign_key='pet.id',
	)
	pet: 'PetORM' = Relationship(
		back_populates='base_stats',
		sa_relationship_kwargs={
			'primaryjoin': 'BaseStatORM.id == PetORM.id',
		},
	)

	@classmethod
	def resource_name(cls) -> str:
		return 'pet_base_stats'


class YieldingEvORM(SixAttributesORM, table=True):
	id: int | None = Field(default=None, primary_key=True, foreign_key='pet.id')
	pet: 'PetORM' = Relationship(
		back_populates='yielding_ev',
		sa_relationship_kwargs={
			'primaryjoin': 'YieldingEvORM.id == PetORM.id',
		},
	)

	@classmethod
	def resource_name(cls) -> str:
		return 'pet_yielding_ev'


class DiyStatsRangeORM(BaseResModel, table=True):
	id: int = Field(default=None, primary_key=True, foreign_key='pet.id')
	pet: 'PetORM' = Relationship(
		back_populates='diy_stats',
		sa_relationship_kwargs={
			'primaryjoin': 'DiyStatsRangeORM.id == PetORM.id',
		},
	)
	atk_min: int = Field(description='精灵自定义种族值攻击最小值')
	def_min: int = Field(description='精灵自定义种族值防御最小值')
	sp_atk_min: int = Field(description='精灵自定义种族值特攻最小值')
	sp_def_min: int = Field(description='精灵自定义种族值特防最小值')
	spd_min: int = Field(description='精灵自定义种族值速度最小值')
	hp_min: int = Field(description='精灵自定义种族值体力最小值')
	atk_max: int = Field(description='精灵自定义种族值攻击最大值')
	def_max: int = Field(description='精灵自定义种族值防御最大值')
	sp_atk_max: int = Field(description='精灵自定义种族值特攻最大值')
	sp_def_max: int = Field(description='精灵自定义种族值特防最大值')
	spd_max: int = Field(description='精灵自定义种族值速度最大值')
	hp_max: int = Field(description='精灵自定义种族值体力最大值')

	@classmethod
	def resource_name(cls) -> str:
		return 'pet_diy_stats_range'


class DiyStats(BaseModel):
	min: SixAttributes = Field(description='精灵自定义种族值最小值')
	max: SixAttributes = Field(description='精灵自定义种族值最大值')

	def to_orm(self, pet_id: int) -> DiyStatsRangeORM:
		"""将DiyStats转换为DiyStatsRangeORM"""
		return DiyStatsRangeORM(
			id=pet_id,
			atk_min=self.min.atk,
			def_min=self.min.def_,
			sp_atk_min=self.min.sp_atk,
			sp_def_min=self.min.sp_def,
			spd_min=self.min.spd,
			hp_min=self.min.hp,
			atk_max=self.max.atk,
			def_max=self.max.def_,
			sp_atk_max=self.max.sp_atk,
			sp_def_max=self.max.sp_def,
			spd_max=self.max.spd,
			hp_max=self.max.hp,
		)


class SkillInPetBase(BaseResModel):
	id: int = Field(
		exclude=True,
		primary_key=True,
		foreign_key='skill.id',
		sa_type=Integer,
		sa_column_kwargs={
			'name': 'skill_id',
		},
		schema_extra={
			'serialization_alias': 'skill_id',
		},
	)
	pet_id: int = Field(primary_key=True, foreign_key='pet.id', exclude=True)
	learning_level: int | None = Field(
		default=None,
		description='技能的学习等级，当该技能无法通过升级获得时，该字段为null',
	)
	is_special: bool = Field(default=False, description='是否是特训技能')
	is_advanced: bool = Field(default=False, description='是否是神谕觉醒技能')
	is_fifth: bool = Field(default=False, description='是否是第五技能')

	@classmethod
	def resource_name(cls) -> str:
		return 'skill_in_pet'


class SkillInPet(SkillInPetBase, ConvertToORM['SkillInPetORM']):
	skill: ResourceRef['Skill'] = Field(description='技能资源')
	skill_activation_item: ResourceRef['SkillActivationItem'] | None = Field(
		default=None, description='学习该技能需要的激活道具'
	)

	@classmethod
	def get_orm_model(cls) -> type['SkillInPetORM']:
		return SkillInPetORM

	def to_orm(self) -> 'SkillInPetORM':
		return SkillInPetORM(
			id=self.id,
			pet_id=self.pet_id,
			learning_level=self.learning_level,
			is_special=self.is_special,
			is_advanced=self.is_advanced,
			is_fifth=self.is_fifth,
			skill_activation_item_id=(
				self.skill_activation_item.id if self.skill_activation_item else None
			),
		)


class SkillInPetORM(SkillInPetBase, table=True):
	skill: 'SkillORM' = Relationship(back_populates='pet_links')
	pet: 'PetORM' = Relationship(back_populates='skill_links')
	skill_activation_item_id: int | None = Field(
		default=None,
		foreign_key='skill_activation_item.id',
	)
	skill_activation_item: Optional['SkillActivationItemORM'] = Relationship(
		back_populates='skill_in_pet',
		sa_relationship_kwargs={
			'primaryjoin': 'SkillInPetORM.skill_activation_item_id == SkillActivationItemORM.id',
		},
	)


class PetBase(BaseResModel):
	name: str = Field(description='精灵名称')
	# 精灵基础信息
	yielding_exp: int = Field(description='击败精灵可获得的经验值')
	catch_rate: int = Field(description='精灵捕捉率')
	evolving_lv: int | None = Field(
		default=None, description='精灵进化等级，当精灵无法再通过等级进化时为null'
	)
	# 其他
	releaseable: bool = Field(description='精灵是否可放生')
	fusion_master: bool = Field(description='精灵是否可作为融合精灵的主宠')
	fusion_sub: bool = Field(description='精灵是否可作为融合精灵的副宠')
	has_resistance: bool = Field(description='精灵是否可获得抗性')

	@classmethod
	def resource_name(cls) -> str:
		return 'pet'


class Pet(PetBase, ConvertToORM['PetORM']):
	type: ResourceRef['TypeCombination'] = Field(description='精灵属性')
	gender: ResourceRef['PetGenderCategory'] = Field(description='精灵性别')
	base_stats: SixAttributes = Field(description='精灵种族值')
	pet_class: ResourceRef['PetClass'] | None = Field(
		default=None, description='精灵类别，同一进化链中的精灵属于同一类'
	)
	evolution_chain_index: int = Field(description='该精灵在进化链中的位置，从0开始')
	yielding_ev: SixAttributes = Field(description='击败精灵可获得的学习力')
	vipbuff: ResourceRef['PetVipBuffCategory'] | None = Field(
		default=None, description='精灵VIP加成，仅在闪光/暗黑精灵上使用'
	)
	mount_type: ResourceRef['PetMountTypeCategory'] | None = Field(
		default=None, description='精灵骑乘类型，仅在坐骑精灵上使用'
	)
	diy_stats: DiyStats | None = Field(
		default=None, description='精灵自定义种族值，仅在合体精灵王上使用'
	)
	skill: list['SkillInPet'] = Field(description='精灵可学习的技能')
	soulmark: list[ResourceRef['Soulmark']] | None = Field(
		default=None, description='精灵可持有的魂印'
	)
	# 其他数据
	encyclopedia_entry: ResourceRef['PetEncyclopediaEntry'] | None = Field(
		default=None, description='精灵图鉴条目'
	)
	archive_story_entry: ResourceRef['PetArchiveStoryEntry'] | None = Field(
		default=None, description='精灵故事条目'
	)

	resource_id: int = Field(description='精灵资源ID')
	enemy_resource_id: int | None = Field(
		default=None,
		description='该精灵在对手侧时使用的资源的ID，仅少数精灵存在这种资源',
	)

	@classmethod
	def get_orm_model(cls) -> 'type[PetORM]':
		return PetORM

	def to_orm(self) -> 'PetORM':
		base_stats = BaseStatORM(
			id=self.id,
			**self.base_stats.model_dump(),
		)
		yielding_ev = YieldingEvORM(
			id=self.id,
			**self.yielding_ev.model_dump(),
		)
		diy_stats = self.diy_stats.to_orm(self.id) if self.diy_stats else None
		skill_links = [skill.to_orm() for skill in self.skill]
		return PetORM(
			id=self.id,
			name=self.name,
			yielding_exp=self.yielding_exp,
			catch_rate=self.catch_rate,
			evolving_lv=self.evolving_lv,
			releaseable=self.releaseable,
			fusion_master=self.fusion_master,
			fusion_sub=self.fusion_sub,
			has_resistance=self.has_resistance,
			type_id=self.type.id,
			gender_id=self.gender.id,
			pet_class_id=self.pet_class.id if self.pet_class else None,
			base_stats_id=cast(int, base_stats.id),
			base_stats=base_stats,
			skill_links=skill_links,
			yielding_ev_id=cast(int, yielding_ev.id),
			yielding_ev=yielding_ev,
			vipbuff_id=self.vipbuff.id if self.vipbuff else None,
			mount_type_id=self.mount_type.id if self.mount_type else None,
			diy_stats_id=diy_stats.id if diy_stats else None,
			diy_stats=diy_stats,
		)


class PetORM(PetBase, table=True):
	type_id: int = Field(foreign_key='element_type_combination.id')
	type: 'TypeCombinationORM' = Relationship(
		back_populates='pet',
	)
	gender_id: int = Field(foreign_key='pet_gender.id')
	gender: 'PetGenderORM' = Relationship(
		back_populates='pet',
	)
	pet_class_id: int | None = Field(default=None, foreign_key='pet_class.id')
	pet_class: Optional['PetClassORM'] = Relationship(
		back_populates='evolution_chain',
	)
	base_stats_id: int = Field(foreign_key='pet_base_stats.id')
	base_stats: BaseStatORM = Relationship(
		back_populates='pet',
		sa_relationship_kwargs={
			'primaryjoin': 'PetORM.id == BaseStatORM.id',
		},
	)
	yielding_ev_id: int = Field(foreign_key='pet_yielding_ev.id')
	yielding_ev: YieldingEvORM = Relationship(
		back_populates='pet',
		sa_relationship_kwargs={
			'primaryjoin': 'PetORM.id == YieldingEvORM.id',
		},
	)
	# 技能，魂印
	skill_links: list['SkillInPetORM'] = Relationship(
		back_populates='pet',
	)
	soulmark: list['SoulmarkORM'] = Relationship(
		back_populates='pet',
		sa_relationship_kwargs={
			'secondary': 'petsoulmarklink',
		},
	)
	# 杂项分类
	vipbuff_id: int | None = Field(default=None, foreign_key='pet_vipbuff.id')
	vipbuff: Optional['PetVipBuffORM'] = Relationship(
		back_populates='pet',
	)
	mount_type_id: int | None = Field(default=None, foreign_key='pet_mount_type.id')
	mount_type: Optional['PetMountTypeORM'] = Relationship(
		back_populates='pet',
	)
	diy_stats_id: int | None = Field(default=None, foreign_key='pet_diy_stats_range.id')
	diy_stats: Optional['DiyStatsRangeORM'] = Relationship(
		back_populates='pet',
		sa_relationship_kwargs={
			'primaryjoin': 'PetORM.id == DiyStatsRangeORM.id',
		},
	)
	exclusive_mintmark: list['MintmarkORM'] = Relationship(
		back_populates='pet',
		sa_relationship_kwargs={
			'secondary': 'petmintmarklink',
		},
	)
	exclusive_suit_bonus: list['SuitBonusORM'] = Relationship(
		back_populates='effective_pets',
		sa_relationship_kwargs={
			'secondary': 'petsuitlink',
		},
	)
	skins: list['PetSkinORM'] = Relationship(
		back_populates='pet',
		sa_relationship_kwargs={
			'primaryjoin': 'PetORM.id == PetSkinORM.pet_id',
		},
	)
	encyclopedia: Optional['PetEncyclopediaEntryORM'] = Relationship(
		back_populates='pet',
		sa_relationship_kwargs={
			'primaryjoin': 'PetORM.id == PetEncyclopediaEntryORM.id',
		},
	)
	archive_story: Optional['PetArchiveStoryEntryORM'] = Relationship(
		back_populates='pet',
		sa_relationship_kwargs={
			'primaryjoin': 'PetORM.id == PetArchiveStoryEntryORM.pet_id',
		},
	)


class PetClassBase(BaseResModel):
	is_variant_pet: bool = Field(default=False, description='是否是异能精灵')
	is_dark_pet: bool = Field(default=False, description='是否是暗黑精灵')
	is_shine_pet: bool = Field(default=False, description='是否是闪光精灵')
	is_rare_pet: bool = Field(default=False, description='是否是稀有精灵')
	is_breeding_pet: bool = Field(default=False, description='是否是繁殖二代精灵')
	is_fusion_pet: bool = Field(default=False, description='是否是融合二代精灵')

	@classmethod
	def resource_name(cls) -> str:
		return 'pet_class'


class PetClass(PetClassBase, ConvertToORM['PetClassORM']):
	"""描述一个精灵类别，所有第一形态为同一ID的精灵为一类"""

	evolution_chain: list[ResourceRef['Pet']] = Field(
		description='精灵进化链，从第一形态到最终形态的精灵列表'
	)

	@classmethod
	def get_orm_model(cls) -> type['PetClassORM']:
		return PetClassORM

	def to_orm(self) -> 'PetClassORM':
		return PetClassORM(
			id=self.id,
			is_variant_pet=self.is_variant_pet,
			is_dark_pet=self.is_dark_pet,
			is_shine_pet=self.is_shine_pet,
			is_rare_pet=self.is_rare_pet,
			is_breeding_pet=self.is_breeding_pet,
			is_fusion_pet=self.is_fusion_pet,
		)


class PetClassORM(PetClassBase, table=True):
	evolution_chain: list['PetORM'] = Relationship(back_populates='pet_class')


class PetCategoryBase(BaseCategoryModel):
	name: str = Field(description='名称')
	description: str = Field(description='描述')


class PetCategoryRefs(SQLModel):
	pet: list[ResourceRef['Pet']] = Field(description='精灵列表')


class PetGenderBase(PetCategoryBase):
	@classmethod
	def resource_name(cls) -> str:
		return 'pet_gender'


class PetGenderCategory(PetGenderBase, PetCategoryRefs, ConvertToORM['PetGenderORM']):
	@classmethod
	def get_orm_model(cls) -> type['PetGenderORM']:
		return PetGenderORM

	def to_orm(self) -> 'PetGenderORM':
		return PetGenderORM(
			id=self.id,
			name=self.name,
			description=self.description,
		)


class PetGenderORM(PetGenderBase, table=True):
	pet: list['PetORM'] = Relationship(back_populates='gender')


class PetVipBuffBase(PetCategoryBase):
	@classmethod
	def resource_name(cls) -> str:
		return 'pet_vipbuff'


class PetVipBuffCategory(
	PetVipBuffBase, PetCategoryRefs, ConvertToORM['PetVipBuffORM']
):
	@classmethod
	def get_orm_model(cls) -> type['PetVipBuffORM']:
		return PetVipBuffORM

	def to_orm(self) -> 'PetVipBuffORM':
		return PetVipBuffORM(
			id=self.id,
			name=self.name,
			description=self.description,
		)


class PetVipBuffORM(PetVipBuffBase, table=True):
	pet: list['PetORM'] = Relationship(back_populates='vipbuff')


class PetMountTypeBase(PetCategoryBase):
	@classmethod
	def resource_name(cls) -> str:
		return 'pet_mount_type'


class PetMountTypeCategory(
	PetMountTypeBase, PetCategoryRefs, ConvertToORM['PetMountTypeORM']
):
	@classmethod
	def get_orm_model(cls) -> type['PetMountTypeORM']:
		return PetMountTypeORM

	def to_orm(self) -> 'PetMountTypeORM':
		return PetMountTypeORM(
			id=self.id,
			name=self.name,
			description=self.description,
		)


class PetMountTypeORM(PetMountTypeBase, table=True):
	pet: list['PetORM'] = Relationship(back_populates='mount_type')


class PetAnalyzer(BasePetAnalyzer):
	def get_skill_activation_item(
		self, skill_id: int, pet_id: int
	) -> ResourceRef['SkillActivationItem'] | None:
		if skill_id in self.skill_activation_data:
			data = self.skill_activation_data[skill_id]
			if data['monster'] == pet_id:
				return ResourceRef(
					id=data['item'],
					resource_name='skill_activation_item',
				)
		return None

	def extract_skills_from_list(
		self,
		pet_id: int,
		skills_data: list | dict | None,
		*,
		is_special: bool = False,
		is_advanced: bool = False,
		is_fifth: bool = False,
	) -> list[SkillInPet]:
		"""从技能数据中生成SkillInPet列表"""
		if not skills_data:
			return []

		# 确保数据是列表格式
		if isinstance(skills_data, dict):
			skills_data = [skills_data]

		result: list[SkillInPet] = []
		skill_id_set: set[int] = set()
		for skill_data in skills_data:
			skill_id = skill_data['id']
			learning_level = skill_data.get('learning_lv')
			data = SkillInPet(
				id=skill_id,
				pet_id=pet_id,
				skill=ResourceRef(id=skill_id, resource_name='skill'),
				learning_level=learning_level,
				is_special=is_special,
				is_advanced=is_advanced,
				is_fifth=is_fifth,
				skill_activation_item=self.get_skill_activation_item(skill_id, pet_id),
			)
			if data.id in skill_id_set:
				continue

			skill_id_set.add(data.id)
			result.append(data)

		return result

	def analyze(self) -> tuple[AnalyzeResult, ...]:
		pet_gender_csv: CsvTable = self._get_data('patch', 'pet_gender.json')
		mount_type_csv: CsvTable = self._get_data('patch', 'pet_mount_type.json')

		# 记录 PetClass，key为PetClass的ID，value为PetClass对象
		pet_class_map: dict[int, PetClass] = {}
		# 记录性别，key为性别id
		pet_gender_map = create_category_map(
			pet_gender_csv, model_cls=PetGenderCategory, array_key='pet'
		)
		# 记录VIP加成，key为buff id
		pet_vipbuff_map = create_category_map(
			pet_gender_csv, model_cls=PetVipBuffCategory, array_key='pet'
		)
		# 记录精灵骑乘模式
		pet_mount_type_map: CategoryMap[int, PetMountTypeCategory, Any] = (
			create_category_map(
				mount_type_csv, model_cls=PetMountTypeCategory, array_key='pet'
			)
		)

		pet_map = {}
		for pet_id, pet_dict in self.pet_origin_data.items():
			if pet_id > 9999:
				break
			pet_name = pet_dict['def_name']
			pet_ref = ResourceRef.from_model(Pet, id=pet_id)
			pet_type = ResourceRef(id=pet_dict['type'], resource_name='element-type')
			pet_gender_id = pet_dict.get('gender', 0)
			if pet_gender_id > 2:
				pet_gender_id = 0
			pet_gender_ref = ResourceRef.from_model(pet_gender_map[pet_gender_id])
			releaseable = not bool(pet_dict.get('free_forbidden', 0))
			# 处理精灵类别
			cls_info = {
				'is_rare_pet': bool(pet_dict.get('IsRareMon', False)),
				'is_variant_pet': bool(pet_dict.get('IsAbilityMon', False)),
				'is_breeding_pet': bool(pet_dict.get('BreedingMon', False)),
				'is_fusion_pet': bool(pet_dict.get('IsFuseMon', False)),
			}
			if vipbuff_id := int(pet_dict.get('VipBtlAdj', 0)):
				if vipbuff_id == 1:
					cls_info['is_shine_pet'] = True
				elif vipbuff_id == 2:
					cls_info['is_dark_pet'] = True
				else:
					raise ValueError(f'Unknown VIP buff ID: {vipbuff_id}')

			pet_cls_ref = None
			evolution_chain_index = 0
			if pet_cls_id := pet_dict.get('pet_class'):
				if pet_cls := pet_class_map.get(pet_cls_id):
					pet_cls.evolution_chain.append(pet_ref)
				else:
					pet_class_map[pet_cls_id] = PetClass(
						id=pet_cls_id,
						evolution_chain=[pet_ref],
						**cls_info,
					)
				pet_cls = pet_class_map[pet_cls_id]
				pet_cls_ref = ResourceRef.from_model(pet_cls)
				evolution_chain_index = len(pet_cls.evolution_chain) - 1

			# 转换种族值对象
			base_stats = SixAttributes(
				hp=pet_dict['hp'],
				atk=pet_dict['atk'],
				def_=pet_dict['def'],
				sp_atk=pet_dict['sp_atk'],
				sp_def=pet_dict['sp_def'],
				spd=pet_dict['spd'],
			)

			# 转换YieldingEV
			yielding_ev = _handle_yielding_ev(pet_dict['YieldingEV'])

			diy_stats: DiyStats | None = None
			if (
				(diy_min := pet_dict.get('DiyRaceMin'))
				and (diy_max := pet_dict.get('DiyRaceMax'))
			):
				diy_stats = DiyStats(
					min=SixAttributes.from_string(diy_min, hp_first=True),
					max=SixAttributes.from_string(diy_max, hp_first=True),
				)
			# 处理坐骑类型
			mount_type = 0
			if pet_dict.get('is_ride_pet', False):
				mount_type = 1
			elif pet_dict.get('is_fly_pet', False):
				mount_type = 2
			mount_type_ref = None
			if mount_type:
				mount_type_ref = ResourceRef.from_model(pet_mount_type_map[mount_type])

			# 准备处理技能相关
			pet_skill_resources: list[SkillInPet] = []
			pet_normal_skills = pet_dict.get('learnable_moves') or pet_dict.get('move')
			if pet_normal_skills:
				# 获取普通技能
				normal_moves = pet_normal_skills.get('move', [])
				pet_skill_resources.extend(
					self.extract_skills_from_list(pet_id, normal_moves)
				)

				# 获取特训技能
				moves = pet_normal_skills.get('sp_move', [])
				pet_skill_resources.extend(
					self.extract_skills_from_list(pet_id, moves, is_special=True)
				)

				# 获取觉醒技能
				moves = pet_normal_skills.get('adv_move', [])
				pet_skill_resources.extend(
					self.extract_skills_from_list(pet_id, moves, is_advanced=True)
				)

			# 获取第五技能
			if fifth_skill := get_nested_value(pet_dict, 'extra_moves.move'):
				pet_skill_resources.extend(
					self.extract_skills_from_list(
						pet_id,
						fifth_skill,
						is_fifth=True,
						is_special=True,
					)
				)

			# 获取特训/觉醒第五技能（U端特训/觉醒第五在同一个字段中，需要单独分辨）
			moves = get_nested_value(pet_dict, 'sp_extra_moves.move') or []
			for move in moves:
				if move['id'] in self.pet_advanced_skill_data:
					kw = {'is_advanced': True}
				else:
					kw = {'is_special': True}
				pet_skill_resources.extend(
					self.extract_skills_from_list(pet_id, move, is_fifth=True, **kw)
				)

			encyclopedia_entry = None
			if pet_id in self.pet_encyclopedia_data:
				encyclopedia_entry = ResourceRef(
					id=pet_id,
					resource_name='pet_encyclopedia_entry',
				)

			archive_story_entry = None
			if pet_id in self.pet_archive_story_book_data:
				archive_story_entry = ResourceRef(
					id=pet_id,
					resource_name='pet_archive_story_entry',
				)

			pet_resource = Pet(
				id=pet_id,
				name=pet_name,
				type=pet_type,
				gender=pet_gender_ref,
				base_stats=base_stats,
				evolving_lv=pet_dict.get('evolving_lv'),
				pet_class=pet_cls_ref,
				evolution_chain_index=evolution_chain_index,
				yielding_exp=pet_dict['YieldingExp'],
				yielding_ev=yielding_ev,
				catch_rate=pet_dict['CatchRate'],
				vipbuff=ResourceRef.from_model(pet_vipbuff_map[vipbuff_id])
				if vipbuff_id
				else None,
				mount_type=mount_type_ref,
				diy_stats=diy_stats,
				releaseable=releaseable,
				fusion_master=pet_dict.get('FuseMaster', False),
				fusion_sub=pet_dict.get('FuseSub', False),
				has_resistance=bool(pet_dict.get('Resist', 0)),
				skill=pet_skill_resources,
				resource_id=pet_dict.get('real_id') or pet_id,
				encyclopedia_entry=encyclopedia_entry,
				archive_story_entry=archive_story_entry,
			)
			pet_map[pet_id] = pet_resource

			pet_ref = ResourceRef.from_model(pet_resource)
			pet_gender_map.add_element(pet_gender_id, pet_ref)
			pet_vipbuff_map.add_element(vipbuff_id, pet_ref)
			pet_mount_type_map.add_element(mount_type, pet_ref)

		return (
			AnalyzeResult(model=Pet, data=pet_map),
			AnalyzeResult(model=PetClass, data=pet_class_map),
			AnalyzeResult(model=PetGenderCategory, data=pet_gender_map),
			AnalyzeResult(model=PetVipBuffCategory, data=pet_vipbuff_map),
			AnalyzeResult(model=PetMountTypeCategory, data=pet_mount_type_map),
		)

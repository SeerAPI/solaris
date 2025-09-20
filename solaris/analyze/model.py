from abc import ABC, abstractmethod
from datetime import datetime
import inspect
from typing import TYPE_CHECKING, Any, ClassVar, Generic, TypeVar, overload
from typing_extensions import Self, TypeIs

from pydantic import AnyUrl, BaseModel, GetJsonSchemaHandler, computed_field
from pydantic.json_schema import JsonSchemaValue
from pydantic_core import core_schema as cs
from sqlalchemy.orm import column_property, declared_attr
from sqlmodel import JSON, Column, Computed, Field, Integer, Relationship, SQLModel

import solaris
from solaris.settings import BaseSettings
from solaris.utils import move_to_last

if TYPE_CHECKING:
	from solaris.analyze.analyzers.effect import PetEffectORM, VariationEffectORM
	from solaris.analyze.analyzers.equip import EquipBonusORM, SuitBonusORM
	from solaris.analyze.analyzers.items.enegry_bead import EnergyBeadORM
	from solaris.analyze.analyzers.items.skill_stone import SkillStoneCategoryORM
	from solaris.analyze.analyzers.mintmark_gem import GemORM
	from solaris.analyze.analyzers.pet.soulmark import SoulmarkORM
	from solaris.analyze.analyzers.skill import SkillEffectTypeORM, SkillORM

T = TypeVar('T', bound=SQLModel)


class BaseMetadata(BaseModel):
	api_url: str = Field(description='当前API的URL')
	api_version: str = Field(description='API版本')
	generator_name: str = Field(
		default=solaris.__package_name__,
		description='生成器名称',
	)
	generator_version: str = Field(
		default=solaris.__version__,
		description='生成器版本',
	)
	generate_time: datetime = Field(
		default_factory=datetime.now,
		description='生成时间',
	)
	data_source: str = Field(
		default='',
		description='数据源，可填写git仓库地址或url',
	)
	data_version: str = Field(
		default='',
		description='数据版本',
	)
	patch_source: str = Field(
		default='',
		description='补丁源，可填写git仓库地址或url',
	)
	patch_version: str = Field(
		default='',
		description='补丁版本',
	)


class ApiMetadata(BaseMetadata, BaseSettings):
	def to_orm(self) -> 'ApiMetadataORM':
		return ApiMetadataORM(
			api_url=self.api_url,
			api_version=self.api_version,
			generator_name=self.generator_name,
			generator_version=self.generator_version,
			generate_time=self.generate_time,
			data_source=self.data_source,
			data_version=self.data_version,
			patch_source=self.patch_source,
			patch_version=self.patch_version,
		)


class ApiMetadataORM(BaseMetadata, SQLModel, table=True):
	__tablename__ = 'api_metadata'  # type: ignore
	id: int | None = Field(default=None, description='ID', primary_key=True)


class BaseModelMethods(ABC):
	@classmethod
	@abstractmethod
	def resource_name(cls) -> str:
		pass


class BaseResModel(SQLModel, BaseModelMethods, ABC):
	"""资源模型抽象基类"""

	id: int = Field(description='资源ID', primary_key=True)

	@declared_attr  # type: ignore
	def __tablename__(cls) -> str:  # type: ignore
		return cls.resource_name()


class BaseResModelWithOptionalId(SQLModel, BaseModelMethods, ABC):
	"""资源模型抽象基类"""

	id: int | None = Field(
		default=None,
		primary_key=True,
		exclude=True,
	)

	@declared_attr  # type: ignore
	def __tablename__(cls) -> str:  # type: ignore
		return cls.resource_name()


class ConvertToORM(ABC, Generic[T]):
	@classmethod
	@abstractmethod
	def get_orm_model(cls) -> type[T]:
		"""获取SQLModel ORM模型类型"""
		pass

	@abstractmethod
	def to_orm(self) -> T:
		"""将Pydantic模型转为SQLModel ORM模型"""
		pass


def is_base_general_model(cls: Any) -> TypeIs['type[BaseGeneralModel]']:
	return (
		issubclass(cls, BaseGeneralModel)
		and cls.schema_path() in BaseGeneralModel.__subclasses_dict__
	)


class _RootMark:
	pass


ROOT_MARK = _RootMark()
ROOT_MARK_KEY = 'root_mark'


class BaseGeneralModel(SQLModel, ABC):
	__subclasses_dict__: ClassVar[dict[str, type['BaseGeneralModel']]] = {}
	base_url: ClassVar[str] = ''

	@classmethod
	def __pydantic_init_subclass__(cls, **kwargs: Any) -> None:
		super().__pydantic_init_subclass__(**kwargs)
		if inspect.isabstract(cls):
			return

		schema_path = cls.schema_path()
		if schema_path not in cls.__subclasses_dict__:
			cls.__subclasses_dict__[schema_path] = cls

	@classmethod
	def __get_pydantic_json_schema__(
		cls, core_schema: cs.CoreSchema, handler: GetJsonSchemaHandler
	) -> JsonSchemaValue:
		# 如果该模型正在生成根级别 schema，则返回完整 schema
		if core_schema.get(ROOT_MARK_KEY) is ROOT_MARK:
			return handler(core_schema)

		# 关于为什么是 AnyUrl 而不是 str，见 https://github.com/pydantic/pydantic/issues/892#issuecomment-1880061542
		return {'$ref': AnyUrl(cls.schema_url())}

	@classmethod
	@abstractmethod
	def schema_path(cls) -> str: ...

	@classmethod
	def schema_url(cls) -> str:
		return '/'.join([cls.base_url, cls.schema_path()])


class BaseCategoryModel(BaseResModel, ABC, Generic[T]): ...


T = TypeVar('T', bound=BaseResModel)


class ResourceRef(BaseGeneralModel, Generic[T]):
	"""API资源类"""

	base_data_url: ClassVar[str] = ''
	id: int = Field(description='资源ID')
	resource_name: str = Field(description='资源类型名称', exclude=True)
	path: str = Field(default='', description='资源路径', exclude=True)

	@computed_field(description='资源URL')
	@property
	def url(self) -> str:
		path_parts: list[str] = [
			self.base_data_url,
			self.resource_name,
			str(self.id),
			self.path,
		]
		return '/'.join(path_parts)

	@classmethod
	def schema_path(cls) -> str:
		return 'resource_ref.json'

	@overload
	@classmethod
	def from_model(
		cls,
		model: T,
		*,
		resource_name: str | None = None,
	) -> Self: ...

	@overload
	@classmethod
	def from_model(
		cls,
		model: type[T],
		*,
		id: int,
		resource_name: str | None = None,
	) -> Self: ...

	@classmethod
	def from_model(
		cls,
		model: type[T] | T,
		*,
		id: int | None = None,
		resource_name: str | None = None,
	) -> Self:
		if not inspect.isclass(model):
			id = model.id
		if id is None:
			raise ValueError('id is required')
		resource_name = resource_name or model.resource_name()
		return cls(
			id=id,
			resource_name=resource_name,
		)


class NamedResourceRef(ResourceRef):
	name: str | None = Field(default=None, description='资源名称')

	@classmethod
	def schema_path(cls) -> str:
		return 'named_resource_ref.json'


class ApiResourceList(BaseGeneralModel):
	count: int = Field(description='资源数量')
	next: str | None = Field(default=None, description='下一页URL')
	previous: str | None = Field(default=None, description='上一页URL')
	results: list[NamedResourceRef] = Field(description='资源列表')

	@classmethod
	def schema_path(cls) -> str:
		return 'api_resource_list.json'


class EidEffect(BaseResModel, BaseGeneralModel, ConvertToORM['EidEffectORM']):
	info: str | None = Field(
		default=None,
		description='效果描述，当效果描述为空时，该字段为null',
	)

	@classmethod
	def schema_path(cls) -> str:
		return 'eid_effect.json'

	@classmethod
	def resource_name(cls) -> str:
		return 'eid_effect'

	@classmethod
	def get_orm_model(cls) -> type['EidEffectORM']:
		return EidEffectORM

	def to_orm(self) -> 'EidEffectORM':
		return EidEffectORM(
			id=self.id,
			info=self.info,
		)


class EidEffectORM(EidEffect, table=True):
	in_use: list['EidEffectInUseORM'] = Relationship(back_populates='effect')


class EidEffectInUseBase(BaseResModelWithOptionalId):
	effect_args: list[int] | None = Field(
		default=None,
		description='效果参数，当效果参数为空时，该字段为null',
		sa_type=JSON,
	)

	@classmethod
	def resource_name(cls) -> str:
		return 'eid_effect_in_use'


class EidEffectInUse(
	EidEffectInUseBase, BaseGeneralModel, ConvertToORM['EidEffectInUseORM']
):
	effect: 'ResourceRef[EidEffect]' = Field(description='效果引用')

	@classmethod
	def schema_path(cls) -> str:
		return 'eid_effect_in_use.json'

	@classmethod
	def get_orm_model(cls) -> type['EidEffectInUseORM']:
		return EidEffectInUseORM

	def to_orm(self) -> 'EidEffectInUseORM':
		return EidEffectInUseORM(
			id=self.id,
			eid=self.effect.id,
			effect_args=self.effect_args,
		)


class EidEffectInUseORM(EidEffectInUseBase, table=True):
	eid: int = Field(foreign_key='eid_effect.id')
	effect: 'EidEffectORM' = Relationship(back_populates='in_use')
	# 特性，魂印，装备效果，etc...
	energy_bead: 'EnergyBeadORM' = Relationship(back_populates='effect_in_use')
	soulmark: 'SoulmarkORM' = Relationship(back_populates='effect_in_use')
	pet_effect: 'PetEffectORM' = Relationship(back_populates='effect_in_use')
	variation_effect: 'VariationEffectORM' = Relationship(
		back_populates='effect_in_use'
	)
	equip_bonus: 'EquipBonusORM' = Relationship(back_populates='effect_in_use')
	suit_bonus: 'SuitBonusORM' = Relationship(back_populates='effect_in_use')


class SixAttributes(
	BaseResModelWithOptionalId, BaseGeneralModel, ConvertToORM['SixAttributesORM']
):
	"""六维属性类"""

	atk: int = Field(description='攻击')
	def_: int = Field(
		sa_type=Integer,
		sa_column_kwargs={'name': 'def', 'nullable': False},
		description='防御',
		schema_extra={'serialization_alias': 'def'},
	)
	sp_atk: int = Field(description='特攻')
	sp_def: int = Field(description='特防')
	spd: int = Field(description='速度')
	hp: int = Field(description='体力')

	percent: bool = Field(
		default=False,
		description='该对象描述的是否是百分比加成，如果为true，属性值为省略百分比（%）符号的加成',
	)

	@computed_field
	@property
	def total(self) -> int:
		"""总属性值"""
		return self.atk + self.def_ + self.sp_atk + self.sp_def + self.spd + self.hp

	@classmethod
	def schema_path(cls) -> str:
		return 'six_attributes.json'

	@classmethod
	def from_string(
		cls, value: str, *, hp_first: bool = False, percent: bool = False
	) -> Self:
		"""从字符串创建六维属性对象"""
		attributes = value.split(' ')
		if len(attributes) < 6:
			raise ValueError('无效的属性字符串')
		attributes = [int(attribute) for attribute in attributes[0:6]]
		return cls.from_list(attributes, hp_first=hp_first, percent=percent)

	@classmethod
	def from_list(
		cls, attributes: list[int], *, hp_first: bool = False, percent: bool = False
	) -> Self:
		if len(attributes) < 6:
			raise ValueError('无效的属性列表')
		if hp_first:
			move_to_last(attributes, 0)
		return cls(
			atk=attributes[0],
			def_=attributes[1],
			sp_atk=attributes[2],
			sp_def=attributes[3],
			spd=attributes[4],
			hp=attributes[5],
			percent=percent,
		)

	def __add__(self, other) -> Self:
		"""两个六维属性相加"""
		cls = type(self)
		if not isinstance(other, cls):
			return self
		return cls(
			atk=self.atk + other.atk,
			def_=self.def_ + other.def_,
			sp_atk=self.sp_atk + other.sp_atk,
			sp_def=self.sp_def + other.sp_def,
			spd=self.spd + other.spd,
			hp=self.hp + other.hp,
		)

	def __sub__(self, other) -> Self:
		"""两个六维属性相减"""
		cls = type(self)
		if not isinstance(other, cls):
			return self
		return cls(
			atk=self.atk - other.atk,
			def_=self.def_ - other.def_,
			sp_atk=self.sp_atk - other.sp_atk,
			sp_def=self.sp_def - other.sp_def,
			spd=self.spd - other.spd,
			hp=self.hp - other.hp,
		)

	@classmethod
	def resource_name(cls) -> str:
		return 'six_attributes'

	@classmethod
	def get_orm_model(cls) -> type['SixAttributesORM']:
		return SixAttributesORM

	def to_orm(self) -> 'SixAttributesORM':
		return SixAttributesORM(
			atk=self.atk,
			def_=self.def_,
			sp_atk=self.sp_atk,
			sp_def=self.sp_def,
			spd=self.spd,
			hp=self.hp,
			percent=self.percent,
		)


class SixAttributesORM(SixAttributes):
	@computed_field(return_type=int)
	@declared_attr
	def total(self):  # type: ignore
		return column_property(
			Column(
				Integer,
				Computed('atk + def + sp_atk + sp_def + spd + hp'),
				nullable=False,
			)
		)


class SkillEffectInUseBase(BaseResModelWithOptionalId):
	"""描述一条“使用中的”技能效果"""

	info: str = Field(description='技能效果描述')
	args: list[int | float] | list[int] | list[float] = Field(
		description='技能效果参数列表',
		sa_type=JSON,
	)

	@classmethod
	def resource_name(cls) -> str:
		return 'skill_effect_in_use'


class SkillEffectInUse(
	SkillEffectInUseBase, BaseGeneralModel, ConvertToORM['SkillEffectInUseORM']
):
	effect: 'ResourceRef'

	@classmethod
	def schema_path(cls) -> str:
		return 'skill_effect_in_use.json'

	@classmethod
	def get_orm_model(cls) -> type['SkillEffectInUseORM']:
		return SkillEffectInUseORM

	def to_orm(self) -> 'SkillEffectInUseORM':
		return SkillEffectInUseORM(
			effect_id=self.effect.id,
			args=self.args,
			info=self.info,
		)


class SkillEffectInUseORM(SkillEffectInUseBase, table=True):
	effect_id: int = Field(foreign_key='skill_effect_type.id')
	effect: 'SkillEffectTypeORM' = Relationship(back_populates='in_use')
	skill: list['SkillORM'] = Relationship(
		sa_relationship_kwargs={
			'secondary': 'skilleffectlink',
		}
	)
	gem: list['GemORM'] = Relationship(
		back_populates='skill_effect_in_use',
	)
	skill_stone_category: list['SkillStoneCategoryORM'] = Relationship(
		back_populates='hide_effect',
		sa_relationship_kwargs={
			'secondary': 'skillstoneeffectlink',
		},
	)

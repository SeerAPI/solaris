# ruff: noqa: F821, F722
from typing import Annotated, Generic, TypeVar

from pydantic import AnyHttpUrl, BaseModel, Field

from .url import UnityAssetUrl

A = Annotated

U_IMAGE_PATH = 'assets/art/ui/assets'


class Vector2DModel(BaseModel):
	x: float
	y: float


class SpineAssetModel(BaseModel):
	textures: list[A[UnityAssetUrl, '']] = Field(description='纹理')
	atlas: str = Field(description='纹理图集')
	skeleton: str = Field(description='Spine 骨骼文件')

	@classmethod
	def from_file(
		cls,
		path: str,
		name: str,
		*texture_names: str,
	) -> 'SpineAssetModel':
		if not texture_names:
			texture_names = (name,)

		texture_urls = [AnyHttpUrl(f'{path}/{name}.png') for name in texture_names]
		atlas_url = AnyHttpUrl(f'{path}/{name}.atlas')
		skeleton_url = AnyHttpUrl(f'{path}/{name}.skel')
		return cls(
			textures=texture_urls,
			atlas=atlas_url,
			skeleton=skeleton_url,
		)


class BaseAssetModel(BaseModel):
	id: int = Field(description='资源id')


# -------精灵相关开始-------


class PetSoundAssetModel(BaseAssetModel):
	crie: str | None = Field(default=None, description='叫声')
	interact: list[str] = Field(
		default_factory=list,
		description='精灵看板语音，目前全游戏仅空元行者存在该资源，且没有上线',
	)  # TODO: 需要确认命名


class PetSwfAssetModel(BaseAssetModel):
	head: str = Field(description='头像')
	follow: str = Field(description='跟随')
	body: str = Field(description='本体')


class PetUnityAssetModel(BaseAssetModel):
	head: str
	half: str
	body: str
	body_spine: SpineAssetModel = Field(description='Spine 动画资源')
	head_position: tuple[Vector2DModel, Vector2DModel] | None = Field(
		default=None, description='头像在本体中的位置，两个值分别为左上和右下位置坐标'
	)


class PetAssetModel(BaseAssetModel):
	swf: PetSwfAssetModel
	unity: PetUnityAssetModel
	sound: PetSoundAssetModel = Field(description='音效')
	soulmarks: list['SoulMarkAssetModel'] = Field(
		default_factory=list, description='魂印'
	)
	element_type: 'ElementTypeAssetModel' = Field(description='属性')


class SoulMarkAssetModel(BaseAssetModel):
	icon: str


class ElementTypeAssetModel(BaseAssetModel):
	swf_icon: str = Field(description='swf端图标')
	unity_icon: str = Field(description='unity端图标')


# -------精灵相关结束-------

# -------物品相关开始-------
ITEM_PATH = 'assets/art/ui/assets/item'

T = TypeVar('T')


class BaseItemAssetModel(BaseAssetModel, Generic[T]):
	swf_icon: str = Field(description='swf端图标')
	unity_icon: A[UnityAssetUrl, ITEM_PATH, T] = Field(description='unity端图标')  # type: ignore


# -------物品相关结束-------


# -------套装相关开始-------


class SuitAssetModel(BaseAssetModel):
	swf_icon: str = Field(description='swf端图标')
	unity_icon: A[UnityAssetUrl, U_IMAGE_PATH, 'item/cloth/suiticon'] = Field(
		description='unity端图标'
	)


class EquipmentSwfAssetModel(BaseAssetModel):
	icon: str
	preview: str
	wear: str = Field(description='装备穿戴时的资源')


class EquipmentUnityAssetModel(BaseAssetModel):
	icon: A[UnityAssetUrl, U_IMAGE_PATH, 'item/cloth/icon']
	preview: str
	wear_spine: SpineAssetModel = Field(description='Spine 动画资源')


class EquipmentAssetModel(BaseAssetModel):
	swf: EquipmentSwfAssetModel
	unity: EquipmentUnityAssetModel


# -------套装相关结束-------

# -------刻印相关开始-------


class MintmarkAssetModel(BaseAssetModel):
	swf_icon: str = Field(description='swf端图标')
	unity_icon: A[
		UnityAssetUrl,
		U_IMAGE_PATH,
		'countermark/icon',
	] = Field(description='unity端图标')


# -------刻印相关结束-------

from typing import ClassVar, NewType, TypeAlias

from pydantic import AnyHttpUrl

from solaris.typing import ClientPlatform

PlatformBaseUrlConfig: TypeAlias = dict[ClientPlatform, AnyHttpUrl]


class AssetSourceUrlFactory:
	BASE_URL_CONFIG: ClassVar[PlatformBaseUrlConfig] = {
		'unity': AnyHttpUrl(''),
		'flash': AnyHttpUrl('https://seer.61.com/'),
		'html5': AnyHttpUrl('https://seerh5.61.com/'),
	}

	def generate_url(
		self,
		source: ClientPlatform,
		path: str,
		name: str,
		ext: str,
	) -> AnyHttpUrl:
		return AnyHttpUrl(f'{self.BASE_URL_CONFIG[source]}/{path}/{name}.{ext}')


UnityAssetUrl = NewType('UnityAssetUrl', AnyHttpUrl)
FlashAssetUrl = NewType('FlashAssetUrl', AnyHttpUrl)
Html5AssetUrl = NewType('Html5AssetUrl', AnyHttpUrl)

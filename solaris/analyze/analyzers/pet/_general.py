from functools import cached_property
from typing import TYPE_CHECKING, Any, cast

from solaris.analyze.base import BaseDataSourceAnalyzer, DataImportConfig
from solaris.analyze.utils import merge_dict_item

if TYPE_CHECKING:
	from solaris.parse.parsers.monsters import MonsterItem
	from solaris.parse.parsers.pet_skin import PetSkinConfig, _SkinItem
	from solaris.parse.parsers.petbook import ArchivesStoryConfig, ArchivesStoryInfo
	from solaris.parse.parsers.sp_hide_moves import SpHideMovesConfig, SpMovesItem


general_import_config = DataImportConfig(
	unity_paths=(
		'monsters.json',
		'spHideMoves.json',
		'petbook.json',
		'archivesStory.json',
		'petSkin.json',
	),
	flash_paths=(
		'config.xml.PetXMLInfo.xml',
		'config.xml.PetBookXMLInfo.xml',
	),
	patch_paths=(
		'pet_gender.json',
		'pet_mount_type.json',
		'pet_vipbuff.json',
		'pet_archive_story_book.json',
	),
)


class BasePetAnalyzer(BaseDataSourceAnalyzer):
	@classmethod
	def get_data_import_config(cls) -> DataImportConfig:
		return general_import_config

	@cached_property
	def pet_origin_data(self) -> dict[int, dict[str, Any]]:
		flash_data = self._get_data(
			'flash', 'config.xml.PetXMLInfo.xml'
		)['Monsters']['Monster']
		unity_data: list["MonsterItem"] = self._get_data(
			'unity', 'monsters.json'
		)['monsters']['monster']
		keys = (
			'YieldingExp',
			'YieldingEV',
			'CatchRate',
			'DiyRaceMin',
			'DiyRaceMax',
			'FuseMaster',
			'FuseSub',
			'Resist',
			'IsRareMon',
			'IsAbilityMon',
			'IsFuseMon',
			'BreedingMon',
			'VipBtlAdj',
		)
		flash_map = {pet['ID']: pet for pet in flash_data}
		result = {}
		for pet in unity_data:
			pet_id = pet['id']
			if pet_id > 9999:
				break

			for key in keys:
				merge_dict_item(cast(dict, pet), flash_map.get(pet_id, {}), key)

			result[pet_id] = pet

		return result

	@cached_property
	def pet_skin_data(self) -> dict[int, '_SkinItem']:
		data: PetSkinConfig = self._get_data('unity', 'petSkin.json')
		return {
			skin['id']: skin
			for skin in data['pet_skins']['skin']
		}

	@cached_property
	def skill_activation_data(self) -> dict[int, 'SpMovesItem']:
		data: SpHideMovesConfig = self._get_data('unity', 'spHideMoves.json')
		return {
			data['moves']: data
			for data in data['config']['sp_moves']
		}

	@cached_property
	def pet_advanced_skill_data(self) -> dict[int, 'SpMovesItem']:
		data: SpHideMovesConfig = self._get_data('unity', 'spHideMoves.json')
		return {
			data['moves']: data
			for data in data['config']['show_moves']
		}

	@cached_property
	def pet_encyclopedia_data(self) -> dict[int, dict[str, Any]]:
		return {
			book['ID']: book
			for book in self._get_data(
				'flash', 'config.xml.PetBookXMLInfo.xml'
			)['root']['Monster']
		}

	@cached_property
	def pet_archive_story_book_data(self) -> dict[int, 'ArchivesStoryInfo']:
		data: ArchivesStoryConfig = self._get_data('unity', 'archivesStory.json')
		return {
			book['id']: book
			for book in data['data']
		}

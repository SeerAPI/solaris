from functools import cached_property
from typing import Any

from solaris.analyze.base import BaseDataSourceAnalyzer, DataImportConfig

general_import_config = DataImportConfig(
	html5_paths=(
		'xml/monsters.json',
		'xml/sp_hide_moves.json',
		'xml/petbook.json',
		'json/archivesStory.json',
		'xml/pet_skin.json',
		'xml/effectIcon.json',
	),
	patch_paths=(
		'pet_gender.json',
		'pet_mount_type.json',
		'pet_archive_story_book.json',
		'soulmark_tag.json',
	),
)


class BasePetAnalyzer(BaseDataSourceAnalyzer):
	@classmethod
	def get_data_import_config(cls) -> DataImportConfig:
		return general_import_config

	@cached_property
	def pet_skin_data(self) -> dict[int, dict[str, Any]]:
		return {
			skin['ID']: skin
			for skin in self._get_data('html5', 'xml/pet_skin.json')['PetSkins']['Skin']
		}

	@cached_property
	def skill_activation_data(self) -> dict[int, dict[str, Any]]:
		return {
			data['moves']: data
			for data in self._get_data('html5', 'xml/sp_hide_moves.json')['config'][
				'SpMoves'
			]
		}

	@cached_property
	def pet_encyclopedia_data(self) -> dict[int, dict[str, Any]]:
		return {
			book['ID']: book
			for book in self._get_data('html5', 'xml/petbook.json')['root']['Monster']
		}

	@cached_property
	def pet_archive_story_book_data(self) -> dict[int, dict[str, Any]]:
		return {
			book['id']: book
			for book in self._get_data('html5', 'json/archivesStory.json')['data']
		}

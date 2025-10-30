from typing import TYPE_CHECKING, Any

from solaris.analyze.base import BaseDataSourceAnalyzer, DataImportConfig

if TYPE_CHECKING:
	from solaris.parse.parsers.items_optimize.items_optimize_cat import (
		ItemsOptimizeCatConfig,
	)


def get_items_from_category_name(
	item_data: dict[str, Any],
	*,
	category_name: str,
) -> dict:
	"""
	通过Items.json中的Name字段，返回该分类下的所有物品数据，同时将分类的Max值应用到物品数据中。

	Args:
		item_data: 物品数据
		cat_name: 分类名称
	"""
	for cat in item_data['Items']['Cat']:
		if cat['Name'] == category_name:
			max_ = cat['Max']
			for item in cat['Item']:
				if 'Max' not in item:
					item['Max'] = max_

			return cat

	raise ValueError(f'Item class {category_name} not found')


class BaseItemAnalyzer(BaseDataSourceAnalyzer):
	@classmethod
	def get_data_import_config(cls) -> DataImportConfig:
		unity_paths = [f'itemsOptimizeCatItems{i}.json' for i in range(27)]
		return DataImportConfig(
			unity_paths=('itemsOptimizeCat.json', *unity_paths),
		)

	def _merge_max_value(self, max_value: int, item_data: dict) -> Any:
		for item in item_data['root']['items']:
			if 'max' not in item:
				item['max'] = max_value

		return item_data

	def get_category(self, category_id: int) -> Any:
		category_data: "ItemsOptimizeCatConfig" = self._get_data(
			'unity', 'itemsOptimizeCat.json'
		)
		for cat in category_data['root']['cats']:
			if cat['id'] == category_id:
				return self._merge_max_value(
					cat['max'],
					self._get_data(
					'unity', f'itemsOptimizeCatItems{category_id}.json'
					)
				)
		raise ValueError(f'Category {category_id} not found')

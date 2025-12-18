from datetime import datetime, timedelta, timezone
from typing import TYPE_CHECKING

from seerapi_models.common import ResourceRef
from seerapi_models.peak_pool import PeakExpertPool, PeakPool
from seerapi_models.pet import Pet

from solaris.analyze.base import BaseDataSourceAnalyzer, DataImportConfig
from solaris.analyze.typing_ import AnalyzeResult

if TYPE_CHECKING:
	from solaris.parse.parsers.pvp_ban import PvpBanConfig
	from solaris.parse.parsers.pvp_ban_expert import PvpBanExpertConfig


def parse_start_time(time_str: str) -> datetime:
	time_str = time_str[2:]
	time = datetime.strptime(time_str, '%Y%m%d')
	tz = timezone(timedelta(hours=8))
	return time.replace(hour=10, tzinfo=tz)


class PeakPoolAnalyzer(BaseDataSourceAnalyzer):
	@classmethod
	def get_data_import_config(cls) -> DataImportConfig:
		return DataImportConfig(unity_paths=('pvpBan.json', 'pvpBanExpert.json'))

	@classmethod
	def get_result_res_models(cls):
		return (PeakPool, PeakExpertPool)

	def analyze(self):
		pvp_ban_data: PvpBanConfig = self._get_data('unity', 'pvpBan.json')
		pvp_ban_expert_data: PvpBanExpertConfig = self._get_data(
			'unity', 'pvpBanExpert.json'
		)

		peak_pool_map: dict[int, PeakPool] = {}
		for item in pvp_ban_data['data']:
			count = item['quantity']
			start_time = parse_start_time(str(item['subkey']))
			peak_pool = PeakPool(
				id=count,
				count=count,
				start_time=start_time,
				end_time=start_time + timedelta(weeks=4),
				pet=[ResourceRef.from_model(Pet, id=pet_id) for pet_id in item['name']],
			)
			peak_pool_map[count] = peak_pool

		peak_expert_pool_map: dict[int, PeakExpertPool] = {}
		for item in pvp_ban_expert_data['data']:
			count = item['quantity']
			start_time = parse_start_time(str(item['subkey_month']))
			peak_expert_pool = PeakExpertPool(
				id=count,
				count=count,
				start_time=start_time,
				end_time=start_time + timedelta(weeks=4),
				pet=[
					ResourceRef.from_model(Pet, id=int(pet_id))
					for pet_id in item['name'].split(';')
				],
			)
			peak_expert_pool_map[count] = peak_expert_pool

		return (
			AnalyzeResult(model=PeakPool, data=peak_pool_map),
			AnalyzeResult(model=PeakExpertPool, data=peak_expert_pool_map),
		)

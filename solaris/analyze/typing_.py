from collections.abc import Mapping, MutableMapping
from dataclasses import dataclass
from typing import (
	Any,
	Generic,
	Literal,
	TypeAlias,
	TypedDict,
	TypeVar,
	overload,
)

from seerapi_models.build_model import BaseResModel, BaseResModelWithOptionalId

from solaris.typing import JSON, ClientPlatform, JSONObject

_MT = TypeVar('_MT', bound=MutableMapping)
CsvTable: TypeAlias = dict[int, _MT]


DataSourceType: TypeAlias = Literal[ClientPlatform, 'patch']


class Patch(TypedDict):
	type: DataSourceType
	target: str
	mode: Literal['append', 'create']
	path: str
	content: JSON


_T = TypeVar('_T')
DataMap: TypeAlias = MutableMapping[str, _T]


class AnalyzeData(TypedDict, total=False):
	unity: DataMap[JSONObject]
	flash: DataMap[JSONObject]
	html5: DataMap[JSONObject]
	patch: DataMap[Patch]


ResModel: TypeAlias = 'BaseResModel | BaseResModelWithOptionalId'


TResModelRequiredId = TypeVar('TResModelRequiredId', bound=BaseResModel)
TResModelWithOptionalId = TypeVar(
	'TResModelWithOptionalId', bound=BaseResModelWithOptionalId
)

TResModel = TypeVar('TResModel', bound=ResModel)


@dataclass(frozen=True)
class AnalyzeResult(Generic[TResModel]):
	"""分析结果数据结构

	Args:
		model: 资源模型类型
		data: 资源数据字典，键为ID，值为模型实例
		schema: JSON模式定义，用于数据验证，当为None时，使用模型的model_json_schema
		output_mode: 输出模式，控制数据的输出方式
	"""

	model: type[TResModel]
	data: Mapping[int, TResModel]
	schema: MutableMapping[str, Any] | None = None
	output_mode: Literal['all', 'not_output', 'db', 'json'] = 'all'

	@overload
	def __new__(
		cls,
		model: type[TResModelRequiredId],
		data: Mapping[int, TResModelRequiredId],
		schema: MutableMapping[str, Any] | None = None,
		output_mode: Literal['all', 'not_output', 'db', 'json'] = 'all',
	) -> 'AnalyzeResult[TResModelRequiredId]': ...

	@overload
	def __new__(
		cls,
		model: type[TResModelWithOptionalId],
		data: Mapping[int, TResModelWithOptionalId],
		schema: MutableMapping[str, Any] | None = None,
		output_mode: Literal['all', 'not_output', 'db'] = 'all',
	) -> 'AnalyzeResult[TResModelWithOptionalId]': ...

	def __new__(
		cls,
		model: type[TResModelRequiredId] | type[TResModelWithOptionalId],
		data: Mapping[int, TResModelRequiredId | TResModelWithOptionalId],
		schema: MutableMapping[str, Any] | None = None,
		output_mode: Literal['all', 'not_output', 'db', 'json'] = 'all',
	) -> 'AnalyzeResult':
		return super().__new__(cls)

	def __init__(
		self,
		model: type[TResModelRequiredId] | type[TResModelWithOptionalId],
		data: Mapping[int, TResModelRequiredId | TResModelWithOptionalId],
		schema: MutableMapping[str, Any] | None = None,
		output_mode: Literal['all', 'not_output', 'db', 'json'] = 'all',
	) -> None:
		object.__setattr__(self, 'model', model)
		object.__setattr__(self, 'data', data)
		object.__setattr__(self, 'schema', schema)
		object.__setattr__(self, 'output_mode', output_mode)

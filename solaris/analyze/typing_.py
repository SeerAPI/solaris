from collections.abc import Mapping, MutableMapping
from typing import (
	TYPE_CHECKING,
	Any,
	Generic,
	Literal,
	TypeAlias,
	TypedDict,
	TypeVar,
)
from typing_extensions import NamedTuple

from solaris.typing import JSON, ClientPlatform, JSONObject

if TYPE_CHECKING:
	from solaris.analyze.model import BaseResModel, BaseResModelWithOptionalId


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


TResModel = TypeVar('TResModel', bound=ResModel)


class AnalyzeResult(NamedTuple, Generic[TResModel]):
	"""分析结果数据结构

	Args:
		model: 资源模型类型
		data: 资源数据字典，键为ID，值为模型实例
		name: 结果名称，用于设置输出的文件名，当为None时，使用模型的resource_name
		schema: JSON模式定义，用于数据验证，当为None时，使用模型的model_json_schema
		output_mode: 输出模式，控制数据的输出方式
	"""

	model: type[TResModel]
	data: Mapping[int, TResModel]
	name: str | None = None
	schema: MutableMapping[str, Any] | None = None
	output_mode: Literal['all', 'not_output', 'db', 'json'] = 'all'

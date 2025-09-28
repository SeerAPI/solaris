"""装备相关配置解析器

解析赛尔号客户端的装备数据文件，包含装备项和等级信息。
"""

from typing import TypedDict

from ..base import BaseParser
from ..bytes_reader import BytesReader


# 装备等级项数据结构
class RankItem(TypedDict):
    """装备等级项"""
    desc: str
    lv: int


# 装备项数据结构
class EquipItem(TypedDict):
    """装备项"""
    desc: str
    name: str
    rank: list[RankItem]
    item_id: int
    quality: int
    suit_id: int


# 装备容器结构
class _Equips(TypedDict):
    """装备容器"""
    equip: list[EquipItem]


# 顶层数据结构
class _Data(TypedDict):
    """装备配置数据"""
    equips: _Equips


class EquipParser(BaseParser[_Data]):
    """装备配置解析器"""

    @classmethod
    def source_config_filename(cls) -> str:
        return 'equip.bytes'

    @classmethod
    def parsed_config_filename(cls) -> str:
        return 'equip.json'

    def parse(self, data: bytes) -> _Data:
        reader = BytesReader(data)
        result: _Data = {'equips': {'equip': []}}

        # 检查是否有装备数据
        if not reader.ReadBoolean():
            return result

        # 解析装备容器
        if reader.ReadBoolean():
            equip_count = reader.ReadSignedInt()
            for _ in range(equip_count):
                # 解析装备项 - 按C#代码顺序读取
                desc = reader.ReadUTFBytesWithLength()
                item_id = reader.ReadSignedInt()
                name = reader.ReadUTFBytesWithLength()
                quality = reader.ReadSignedInt()

                # 解析可选的等级数组
                rank_list: list[RankItem] = []
                if reader.ReadBoolean():
                    rank_count = reader.ReadSignedInt()
                    for _ in range(rank_count):
                        rank_desc = reader.ReadUTFBytesWithLength()
                        rank_lv = reader.ReadSignedInt()
                        rank_item: RankItem = {
                            'desc': rank_desc,
                            'lv': rank_lv
                        }
                        rank_list.append(rank_item)

                suit_id = reader.ReadSignedInt()

                equip_item: EquipItem = {
                    'desc': desc,
                    'name': name,
                    'rank': rank_list,
                    'item_id': item_id,
                    'quality': quality,
                    'suit_id': suit_id
                }
                result['equips']['equip'].append(equip_item)

        return result

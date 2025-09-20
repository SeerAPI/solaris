# from sqlmodel import Field, Relationship

# from ..model import BaseGeneralModel, BaseResModel, ConvertToORM, ResourceRef
# from ..base import Analyzer, DataImportConfig
# from ..typing_ import AnalyzeResult


# TREE_RESOURCE_NAME = "achievement_tree"


# class RootNodeBase(BaseResModel):
# name: str = Field(description="根节点名称")

# @classmethod
# def resource_name(cls) -> str:
# return "achievement_tree_root"


# class RootNode(RootNodeBase, ConvertToORM["RootNodeORM"]):
# branches: list["BranchNode"] = Field(
# default_factory=list, description="分支节点列表"
# )

# @classmethod
# def get_orm_model(cls) -> type["RootNodeORM"]:
# return RootNodeORM

# def to_orm(self) -> "RootNodeORM":
# return RootNodeORM(
# id=self.id, name=self.name, branches=[
# b.to_orm() for b in self.branches
# ]
# )


# class RootNodeORM(RootNodeBase, table=True):
# branches: list["BranchNodeORM"] = Relationship(back_populates="parent")


# class BranchNodeBase(BaseResModel):
# name: str = Field(description="分支节点名称")

# @classmethod
# def resource_name(cls) -> str:
# return "achievement_tree_branch"


# class BranchNode(BranchNodeBase, ConvertToORM["BranchNodeORM"]):
# parent: ResourceRef[RootNode] = Field(description="父节点（RootNode）资源引用")
# rules: list["RuleNode"] = Field(default_factory=list, description="规则节点列表")

# @classmethod
# def get_orm_model(cls) -> type["BranchNodeORM"]:
# return BranchNodeORM

# def to_orm(self) -> "BranchNodeORM":
# return BranchNodeORM(
# id=self.id,
# name=self.name,
# parent_id=self.parent.id,
# rules=[r.to_orm() for r in self.rules],
# )


# class BranchNodeORM(BranchNodeBase, table=True):
# parent_id: int | None = Field(
# default=None,
# foreign_key="achievement_tree_root.id"
# )
# parent: "RootNodeORM" = Relationship(back_populates="branches")
# rules: list["RuleNodeORM"] = Relationship(back_populates="parent")


# class RuleNodeBase(BaseResModel):
# name: str = Field(description="规则节点名称")
# intro: str | None = Field(description="规则节点简介")

# @classmethod
# def resource_name(cls) -> str:
# return "achievement_tree_rule"


# class RuleNode(RuleNodeBase, ConvertToORM["RuleNodeORM"]):
# parent: ResourceRef[BranchNode] = Field(
# description="父节点（BranchNode）资源引用"
# )
# achievements: list["AchievementNode"] = Field(
# default_factory=list, description="成就节点列表"
# )

# @classmethod
# def get_orm_model(cls) -> type["RuleNodeORM"]:
# return RuleNodeORM

# def to_orm(self) -> "RuleNodeORM":
# return RuleNodeORM(
# id=self.id,
# name=self.name,
# intro=self.intro,
# parent_id=self.parent.id,
# achievements=[a.to_orm() for a in self.achievements],
# )


# class RuleNodeORM(RuleNodeBase, table=True):
# parent_id: int | None = Field(
# default=None, foreign_key="achievement_tree_branch.id")
# parent: "BranchNodeORM" = Relationship(back_populates="rules")

# achievements: list["AchievementNodeORM"] = Relationship(
# back_populates="parent")

# @classmethod
# def resource_name(cls) -> str:
# return "achievement_tree_rule"


# class AchievementNodeBase(BaseResModel, BaseGeneralModel):
# name: str = Field(description="成就名称")
# point: int = Field(description="成就点数")
# title: str | None = Field(description="成就称号")
# desc: str = Field(description="成就描述")
# is_ability: bool = Field(description="是否是能力加成成就")
# ability_desc: str | None = Field(
# description="能力加成成就描述，仅在该成就为能力加成成就时有效"
# )

# @classmethod
# def resource_name(cls) -> str:
# return "achievement"

# @classmethod
# def schema_path(cls) -> str:
# return "achievement_node.json"


# class AchievementNode(AchievementNodeBase, ConvertToORM["AchievementNodeORM"]):
# parent: ResourceRef[RuleNode] = Field(description="父节点引用")

# @classmethod
# def get_orm_model(cls) -> type["AchievementNodeORM"]:
# return AchievementNodeORM

# def to_orm(self) -> "AchievementNodeORM":
# return AchievementNodeORM(
# id=self.id,
# name=self.name,
# point=self.point,
# title=self.title,
# desc=self.desc,
# is_ability=self.is_ability,
# ability_desc=self.ability_desc,
# parent_id=self.parent.id,
# )


# class AchievementNodeORM(AchievementNodeBase, table=True):
# parent_id: int | None = Field(
# default=None, foreign_key="achievement_tree_rule.id")
# parent: "RuleNodeORM" = Relationship(back_populates="achievements")


# class AchievementsAnalyzer(Analyzer):
# """成就数据分析器"""

# @classmethod
# def get_data_import_config(cls) -> DataImportConfig:
# return DataImportConfig(
# html5_paths=("xml/achievements.json",),
# )

# def analyze(self) -> tuple[AnalyzeResult, ...]:
# achievements_data = self._get_data('html5', 'xml/achievements.json')["AchievementRules"]["type"]
# achievement_tree: dict[int, RootNode] = {}
# all_achievements: dict[int, AchievementNode] = {}
# ability_achievements: dict[int, AchievementNode] = {}
# branch_id = 1
# rule_id = 1
# achievement_id = 1
# for ach_type in achievements_data:
# root_id = ach_type.get("ID")
# root_name = ach_type.get("Desc")
# root_node = RootNode(
# id=root_id,
# name=root_name,
# branches=[],
# )
# achievement_tree[root_id] = root_node
# for branches in ach_type.get("Branches", []):
# # branch_id = branches.get("ID")
# branch_name = branches.get("Desc")
# branch_node = BranchNode(
# id=branch_id,
# name=branch_name,
# rules=[],
# parent=ResourceRef(
# id=root_id,
# path=f'{root_id}',
# resource_name=TREE_RESOURCE_NAME,
# ),
# )
# branch_id += 1
# root_node.branches.append(branch_node)
# for branch in branches.get("Branch", []):
# # rule_id = branch.get("ID")
# rule_name = branch.get("Desc")
# rule_intro = branch.get("introl")
# rule_node = RuleNode(
# id=rule_id,
# name=rule_name,
# intro=rule_intro,
# achievements=[],
# parent=ResourceRef(
# id=branch_id,
# resource_name=TREE_RESOURCE_NAME,
# ),
# )
# rule_id += 1
# branch_node.rules.append(rule_node)
# for rule in branch.get("Rule", []):
# achievement = AchievementNode(
# id=achievement_id,
# name=rule.get("achName", rule_name),
# point=rule.get("AchievementPoint"),
# title=rule.get("title"),
# desc=rule.get("Desc"),
# is_ability=bool(rule.get("AbilityTitle")),
# ability_desc=rule.get("abtext"),
# parent=ResourceRef(
# id=rule_id,
# resource_name=TREE_RESOURCE_NAME,
# path=f'{root_id}/{branch_id}/{rule_id}',
# ),
# )
# rule_node.achievements.append(achievement)
# if achievement.is_ability:
# ability_achievements[achievement_id] = achievement
# else:
# all_achievements[achievement_id] = achievement
# achievement_id += 1

# return (
# AnalyzeResult(
# model=RootNode,
# data=achievement_tree,
# ),
# AnalyzeResult(
# model=AchievementNode,
# data=all_achievements,
# output_mode='json',
# ),
# AnalyzeResult(
# model=AchievementNode,
# data=ability_achievements,
# output_mode='json',
# ),
# )

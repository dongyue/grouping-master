from pydantic import BaseModel, field_validator, model_validator
from typing import Literal


class ConstraintRule(BaseModel):
    attribute_name: str
    allowed_values: list[str]
    constraint_type: Literal["min_diversity", "max_diversity"]
    constraint_value: int


class ActivityBaseRequest(BaseModel):
    title: str
    description: str | None = None
    group_strategy: str = "fixed_group_size"
    group_param: int = 2
    constraints: list[ConstraintRule] | None = None
    allow_want_preferences: bool = False
    max_want_count: int = 1
    allow_avoid_preferences: bool = False
    max_avoid_count: int = 1

    @field_validator("title")
    @classmethod
    def validate_title(cls, v: str) -> str:
        v = v.strip()
        if len(v) < 1 or len(v) > 100:
            raise ValueError("标题长度 1-100 位")
        return v

    @field_validator("group_strategy")
    @classmethod
    def validate_group_strategy(cls, v: str) -> str:
        if v not in ("fixed_group_size", "fixed_group_count"):
            raise ValueError("不支持的分组策略")
        return v

    @field_validator("group_param")
    @classmethod
    def validate_group_param(cls, v: int) -> int:
        if v < 2:
            raise ValueError("组参数不能小于2")
        return v

    @field_validator("constraints")
    @classmethod
    def validate_constraints(cls, v: list | None) -> list | None:
        if v is None:
            return v
        seen_names = set()
        for rule in v:
            attr_name = rule.attribute_name.strip()
            if not attr_name:
                raise ValueError("属性名不能为空")
            if attr_name in seen_names:
                raise ValueError(f"属性名「{attr_name}」已存在，不能重复")
            seen_names.add(attr_name)
            n = len(rule.allowed_values)
            if n < 2:
                raise ValueError(f"属性「{attr_name}」的枚举值至少需要2个")
            if rule.constraint_type == "min_diversity":
                if rule.constraint_value < 2:
                    raise ValueError(f"属性「{attr_name}」的『至少』限定值不能小于2")
                if rule.constraint_value > n:
                    raise ValueError(f"属性「{attr_name}」的『至少』限定值({rule.constraint_value})不能大于枚举值数量({n})")
            else:
                if rule.constraint_value < 1:
                    raise ValueError(f"属性「{attr_name}」的『最多』限定值不能小于1")
                if rule.constraint_value >= n:
                    raise ValueError(f"属性「{attr_name}」的『最多』限定值({rule.constraint_value})不能达到枚举值数量({n})")
        return v

    @field_validator("max_want_count")
    @classmethod
    def validate_max_want_count(cls, v: int) -> int:
        if v < 1 or v > 10:
            raise ValueError("「希望在一起」上限需在 1-10 之间")
        return v

    @field_validator("max_avoid_count")
    @classmethod
    def validate_max_avoid_count(cls, v: int) -> int:
        if v < 1 or v > 10:
            raise ValueError("「不希望在一起」上限需在 1-10 之间")
        return v


class ActivityCreateRequest(ActivityBaseRequest):
    pass


class ActivityUpdateRequest(ActivityBaseRequest):
    pass


class JoinActivityRequest(BaseModel):
    nickname: str
    attribute_values: dict[str, str] | None = None


class ActivityResponse(BaseModel):
    id: int
    slug: str
    title: str
    description: str | None
    group_strategy: str
    group_param: int
    constraints: list | None = None
    allow_want_preferences: bool
    max_want_count: int
    allow_avoid_preferences: bool
    max_avoid_count: int
    creator_nickname: str
    created_at: str

    model_config = {"from_attributes": True}


class MemberItem(BaseModel):
    user_id: int
    nickname: str
    avatar_path: str | None
    joined_at: str
    attributes: dict[str, str] = {}
    attribute_warnings: list[str] = []

    model_config = {"from_attributes": True}


class GroupResponse(BaseModel):
    group_number: int
    members: list[MemberItem]

    model_config = {"from_attributes": True}


class ActivityDetailResponse(ActivityResponse):
    is_member: bool
    is_creator: bool
    has_groups: bool
    members: list[MemberItem]
    groups: list[GroupResponse] = []
    ungrouped_members: list[MemberItem] = []


class ActivityLogResponse(BaseModel):
    id: int
    user_nickname: str
    action_type: str
    content: str
    detail: dict | None = None
    created_at: str

    model_config = {"from_attributes": True}

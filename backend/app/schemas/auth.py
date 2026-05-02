from pydantic import BaseModel, EmailStr, field_validator, model_validator
from typing import Literal
import re


class RegisterRequest(BaseModel):
    username: str
    nickname: str
    password: str | None = None
    password_confirm: str | None = None
    email: str | None = None

    @field_validator("username")
    @classmethod
    def validate_username(cls, v: str) -> str:
        if not re.match(r"^[a-zA-Z0-9_]{3,50}$", v):
            raise ValueError("账号名只能包含字母、数字和下划线，长度3-50位")
        return v

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str | None) -> str | None:
        if v is None or v == "":
            return None
        if len(v) < 8:
            raise ValueError("密码长度至少8位")
        return v

    @field_validator("password_confirm")
    @classmethod
    def validate_password_confirm(cls, v: str | None) -> str | None:
        if v is None or v == "":
            return None
        if len(v) < 8:
            raise ValueError("确认密码长度至少8位")
        return v

    @model_validator(mode="after")
    def validate_passwords(self):
        from app.config import REQUIRE_PASSWORD
        if self.password or self.password_confirm:
            if self.password != self.password_confirm:
                raise ValueError("两次输入的密码不一致")
        elif REQUIRE_PASSWORD:
            raise ValueError("密码不能为空")
        return self

    @field_validator("nickname")
    @classmethod
    def validate_nickname(cls, v: str) -> str:
        v = v.strip()
        if len(v) < 1 or len(v) > 50:
            raise ValueError("昵称长度1-50位")
        return v


class LoginRequest(BaseModel):
    username: str
    password: str


class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str
    new_password_confirm: str

    @field_validator("new_password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("密码长度至少8位")
        return v

    @model_validator(mode="after")
    def validate_password_confirm(self):
        if self.new_password != self.new_password_confirm:
            raise ValueError("两次输入的新密码不一致")
        return self


class ForgotPasswordRequest(BaseModel):
    email: str


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str

    @field_validator("new_password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("密码长度至少8位")
        return v


class UpdateProfileRequest(BaseModel):
    nickname: str | None = None

    @field_validator("nickname")
    @classmethod
    def validate_nickname(cls, v: str | None) -> str | None:
        if v is not None:
            v = v.strip()
            if len(v) < 1 or len(v) > 50:
                raise ValueError("昵称长度1-50位")
        return v


class UserResponse(BaseModel):
    id: int
    username: str
    nickname: str
    email: str | None
    avatar_path: str | None
    created_at: str

    model_config = {"from_attributes": True}


class MessageResponse(BaseModel):
    message: str


class ConstraintRule(BaseModel):
    attribute_name: str
    allowed_values: list[str]
    constraint_type: Literal["min_diversity", "max_diversity"]
    constraint_value: int


class ActivityCreateRequest(BaseModel):
    title: str
    description: str | None = None
    group_strategy: str = "fixed_group_size"
    group_param: int = 2
    constraints: list[ConstraintRule] | None = None

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


class ActivityUpdateRequest(BaseModel):
    title: str
    description: str | None = None
    group_strategy: str = "fixed_group_size"
    group_param: int = 2
    constraints: list[ConstraintRule] | None = None

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


class JoinActivityRequest(BaseModel):
    attribute_values: dict[str, str] | None = None


class ActivityResponse(BaseModel):
    id: int
    slug: str
    title: str
    description: str | None
    group_strategy: str
    group_param: int
    constraints: list | None = None
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


class ActivityDetailResponse(ActivityResponse):
    is_member: bool
    is_creator: bool
    has_groups: bool
    members: list[MemberItem]
    groups: list["GroupResponse"] = []
    ungrouped_members: list[MemberItem] = []


class GroupResponse(BaseModel):
    group_number: int
    members: list[MemberItem]

    model_config = {"from_attributes": True}


class ActivityLogResponse(BaseModel):
    id: int
    user_nickname: str
    action_type: str
    content: str
    detail: dict | None = None
    created_at: str

    model_config = {"from_attributes": True}


class UserAttributesResponse(BaseModel):
    attributes: dict[str, str]


class UpdateUserAttributesRequest(BaseModel):
    attributes: dict[str, str]

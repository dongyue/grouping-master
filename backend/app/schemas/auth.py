from pydantic import BaseModel, EmailStr, field_validator, model_validator
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


class UserAttributesResponse(BaseModel):
    attributes: dict[str, str]


class UpdateUserAttributesRequest(BaseModel):
    attributes: dict[str, str]

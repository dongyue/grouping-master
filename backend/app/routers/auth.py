import os
import uuid
from fastapi import APIRouter, Depends, HTTPException, Request, UploadFile, File, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.models.user_attribute import UserAttribute
from app.schemas.auth import (
    RegisterRequest,
    LoginRequest,
    ChangePasswordRequest,
    ForgotPasswordRequest,
    ResetPasswordRequest,
    UpdateProfileRequest,
    UserResponse,
    MessageResponse,
    UserAttributesResponse,
    UpdateUserAttributesRequest,
)
from app.services import auth as auth_service
from app.middleware.auth import get_current_user
from app.middleware.rate_limit import RateLimiter
from app.services.upload import validate_magic_bytes
from app.config import AVATAR_DIR, MAX_AVATAR_SIZE, SESSION_EXPIRE_DAYS, FRONTEND_URL, REQUIRE_PASSWORD

rate_limiter = RateLimiter()

router = APIRouter(prefix="/api/auth", tags=["认证"])


@router.get("/config")
def get_config():
    return {"require_password": REQUIRE_PASSWORD}


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(body: RegisterRequest, db: Session = Depends(get_db), rate: None = Depends(rate_limiter)):
    existing = db.query(User).filter(User.username == body.username).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="账号名已被注册")

    if body.email:
        email_exists = db.query(User).filter(User.email == body.email).first()
        if email_exists:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="邮箱已被注册")

    user = auth_service.create_user(db, body.username, body.nickname, body.password, body.email)
    session_id = auth_service.create_session(db, user.id)

    response = JSONResponse(
        status_code=status.HTTP_201_CREATED,
        content={
            "id": user.id,
            "username": user.username,
            "nickname": user.nickname,
            "email": user.email,
            "avatar_path": user.avatar_path,
            "created_at": user.created_at.isoformat(),
        },
    )
    response.set_cookie(
        key="session_id",
        value=session_id,
        max_age=SESSION_EXPIRE_DAYS * 24 * 3600,
        httponly=True,
        samesite="lax",
    )
    return response


@router.post("/login", response_model=UserResponse)
def login(body: LoginRequest, db: Session = Depends(get_db), rate: None = Depends(rate_limiter)):
    user = auth_service.authenticate_user(db, body.username, body.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="账号名或密码错误")

    session_id = auth_service.create_session(db, user.id)

    response = JSONResponse(
        content={
            "id": user.id,
            "username": user.username,
            "nickname": user.nickname,
            "email": user.email,
            "avatar_path": user.avatar_path,
            "created_at": user.created_at.isoformat(),
        },
    )
    response.set_cookie(
        key="session_id",
        value=session_id,
        max_age=SESSION_EXPIRE_DAYS * 24 * 3600,
        httponly=True,
        samesite="lax",
    )
    return response


@router.post("/logout", response_model=MessageResponse)
def logout(request: Request, db: Session = Depends(get_db)):
    session_id = request.cookies.get("session_id")
    if session_id:
        auth_service.delete_session(db, session_id)

    response = JSONResponse(content={"message": "已退出登录"})
    response.delete_cookie(key="session_id")
    return response


@router.get("/me", response_model=UserResponse)
def me(current_user: User = Depends(get_current_user)):
    return UserResponse(
        id=current_user.id,
        username=current_user.username,
        nickname=current_user.nickname,
        email=current_user.email,
        avatar_path=current_user.avatar_path,
        created_at=current_user.created_at.isoformat(),
    )


@router.put("/password", response_model=MessageResponse)
def change_password(
    body: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.id == current_user.id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在")
    success = auth_service.change_password(db, user, body.old_password, body.new_password)
    if not success:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="旧密码不正确")
    return {"message": "密码修改成功"}


@router.post("/forgot-password", response_model=MessageResponse)
def forgot_password(request: Request, body: ForgotPasswordRequest, db: Session = Depends(get_db), rate: None = Depends(rate_limiter)):
    user = auth_service.get_user_by_email(db, body.email)
    if not user:
        return {"message": "如果该邮箱已注册，重置密码链接已发送"}

    origin = request.headers.get("Origin") or request.headers.get("Referer", "")
    # 提取 base URL（去掉路径部分）
    frontend_url = origin.rstrip("/")

    auth_service.create_password_reset(db, user, frontend_url)

    return {"message": "如果该邮箱已注册，重置密码链接已发送"}


@router.post("/reset-password", response_model=MessageResponse)
def reset_password(body: ResetPasswordRequest, db: Session = Depends(get_db)):
    user = auth_service.reset_password_with_token(db, body.token, body.new_password)
    if not user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="重置链接无效或已过期")
    return {"message": "密码重置成功，请重新登录"}


@router.put("/profile", response_model=UserResponse)
def update_profile(
    body: UpdateProfileRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.id == current_user.id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在")
    user = auth_service.update_user_profile(db, user, body.nickname, None)
    return UserResponse(
        id=user.id,
        username=user.username,
        nickname=user.nickname,
        email=user.email,
        avatar_path=user.avatar_path,
        created_at=user.created_at.isoformat(),
    )


@router.post("/avatar", response_model=UserResponse)
async def upload_avatar(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if file.content_type not in ["image/jpeg", "image/png", "image/gif"]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="仅支持 JPG、PNG、GIF 格式")

    content = await file.read()
    if len(content) > MAX_AVATAR_SIZE:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="文件大小不能超过 2MB")

    validate_magic_bytes(content, file.content_type)

    os.makedirs(AVATAR_DIR, exist_ok=True)

    ext = os.path.splitext(file.filename or ".jpg")[1] or ".jpg"
    filename = f"{uuid.uuid4().hex}{ext}"
    filepath = os.path.join(AVATAR_DIR, filename)

    with open(filepath, "wb") as f:
        f.write(content)

    user = db.query(User).filter(User.id == current_user.id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在")
    user = auth_service.update_user_profile(db, user, None, f"uploads/avatars/{filename}")
    return UserResponse(
        id=user.id,
        username=user.username,
        nickname=user.nickname,
        email=user.email,
        avatar_path=user.avatar_path,
        created_at=user.created_at.isoformat(),
    )


@router.delete("/account", response_model=MessageResponse)
def delete_account(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.id == current_user.id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在")
    auth_service.delete_user(db, user)
    response = JSONResponse(content={"message": "账号已注销"})
    response.delete_cookie(key="session_id")
    return response


@router.get("/attributes", response_model=UserAttributesResponse)
def get_user_attributes(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    attrs = db.query(UserAttribute).filter(UserAttribute.user_id == current_user.id).all()
    return UserAttributesResponse(attributes={a.attribute_name: a.attribute_value for a in attrs})


@router.put("/attributes", response_model=UserAttributesResponse)
def update_user_attributes(
    body: UpdateUserAttributesRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    db.query(UserAttribute).filter(UserAttribute.user_id == current_user.id).delete()
    for name, value in body.attributes.items():
        db.add(UserAttribute(user_id=current_user.id, attribute_name=name.strip(), attribute_value=value.strip()))
    db.commit()
    return UserAttributesResponse(attributes=body.attributes)

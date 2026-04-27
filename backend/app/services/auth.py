import os
import sys
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
import bcrypt as _bcrypt

from app.models.user import User
from app.models.session import Session as SessionModel
from app.models.password_reset import PasswordReset
from app.config import SESSION_EXPIRE_DAYS, RESET_TOKEN_EXPIRE_MINUTES, FRONTEND_URL
from app.services.mail import send_reset_email, generate_token


def hash_password(password: str) -> str:
    return _bcrypt.hashpw(password.encode("utf-8"), _bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    return _bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))


def create_user(db: Session, username: str, nickname: str, password: str, email: str | None) -> User:
    user = User(
        username=username,
        nickname=nickname,
        password_hash=hash_password(password),
        email=email if email else None,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def authenticate_user(db: Session, username: str, password: str) -> User | None:
    user = db.query(User).filter(User.username == username).first()
    if user and verify_password(password, user.password_hash):
        return user
    return None


def create_session(db: Session, user_id: int) -> str:
    session_id = generate_token()
    expires_at = datetime.utcnow() + timedelta(days=SESSION_EXPIRE_DAYS)
    session = SessionModel(id=session_id, user_id=user_id, expires_at=expires_at)
    db.add(session)
    db.commit()
    return session_id


def get_session(db: Session, session_id: str) -> SessionModel | None:
    session = db.query(SessionModel).filter(
        SessionModel.id == session_id,
        SessionModel.expires_at > datetime.utcnow(),
    ).first()
    return session


def delete_session(db: Session, session_id: str) -> None:
    db.query(SessionModel).filter(SessionModel.id == session_id).delete()
    db.commit()


def get_user_by_id(db: Session, user_id: int) -> User | None:
    return db.query(User).filter(User.id == user_id).first()


def get_user_by_email(db: Session, email: str) -> User | None:
    return db.query(User).filter(User.email == email).first()


def change_password(db: Session, user: User, old_password: str, new_password: str) -> bool:
    if not verify_password(old_password, user.password_hash):
        return False
    user.password_hash = hash_password(new_password)
    db.commit()
    return True


def create_password_reset(db: Session, user: User, frontend_url: str = "") -> str:
    token = generate_token()
    expires_at = datetime.utcnow() + timedelta(minutes=RESET_TOKEN_EXPIRE_MINUTES)
    reset = PasswordReset(user_id=user.id, token=token, expires_at=expires_at)
    db.add(reset)
    db.commit()

    base_url = frontend_url or FRONTEND_URL
    reset_url = f"{base_url}/reset-password?token={token}"
    print(f"\n[DEV] 重置密码链接:\n    {reset_url}\n", file=sys.stderr)

    if user.email:
        try:
            send_reset_email(user.email, token, base_url)
        except Exception as e:
            print(f"[SMTP] 邮件发送失败: {e}\n", file=sys.stderr)

    return token


def reset_password_with_token(db: Session, token: str, new_password: str) -> User | None:
    reset = db.query(PasswordReset).filter(
        PasswordReset.token == token,
        PasswordReset.used == False,
        PasswordReset.expires_at > datetime.utcnow(),
    ).first()
    if not reset:
        return None

    user = db.query(User).filter(User.id == reset.user_id).first()
    if not user:
        return None

    user.password_hash = hash_password(new_password)
    reset.used = True

    # 销毁该用户所有 session，强制重新登录
    db.query(SessionModel).filter(SessionModel.user_id == user.id).delete()
    db.commit()
    return user


def update_user_profile(db: Session, user: User, nickname: str | None, avatar_path: str | None) -> User:
    if nickname is not None:
        user.nickname = nickname
    if avatar_path is not None:
        user.avatar_path = avatar_path
    db.commit()
    db.refresh(user)
    return user


def delete_user(db: Session, user: User) -> None:
    # 删除头像文件
    if user.avatar_path:
        avatar_full_path = os.path.join(os.path.dirname(__file__), "..", "..", user.avatar_path)
        if os.path.exists(avatar_full_path):
            os.remove(avatar_full_path)
    # sessions 和 password_resets 通过外键 CASCADE 自动删除
    db.delete(user)
    db.commit()

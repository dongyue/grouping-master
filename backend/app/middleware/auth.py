from fastapi import Request, HTTPException, status
from app.database import SessionLocal
from app.services.auth import get_session, get_user_by_id


async def get_current_user(request: Request):
    session_id = request.cookies.get("session_id")
    if not session_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="请先登录")

    db = SessionLocal()
    try:
        session = get_session(db, session_id)
        if not session:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="登录已过期，请重新登录")

        user = get_user_by_id(db, session.user_id)
        if not user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="用户不存在")

        return user
    finally:
        db.close()

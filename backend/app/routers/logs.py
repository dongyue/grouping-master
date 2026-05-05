import json
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.models.activity import Activity
from app.models.activity_log import ActivityLog
from app.schemas.activity import ActivityLogResponse
from app.middleware.auth import get_current_user

router = APIRouter(tags=["活动日志"])


@router.get("/{slug}/logs", response_model=list[ActivityLogResponse])
def get_activity_logs(
    slug: str,
    after_group: bool = False,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    activity = db.query(Activity).filter(Activity.slug == slug).first()
    if not activity:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="活动不存在")

    if activity.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="只有活动创建者才能查看日志")

    query = db.query(ActivityLog).filter(ActivityLog.activity_id == activity.id)

    if after_group:
        last_group = (
            query.filter(ActivityLog.action_type == "group")
            .order_by(ActivityLog.created_at.desc())
            .first()
        )
        if not last_group:
            return []
        query = query.filter(
            ActivityLog.created_at > last_group.created_at,
            ActivityLog.action_type.in_(["join", "leave", "kick"]),
        )

    logs = query.order_by(ActivityLog.created_at.desc()).all()

    return [
        ActivityLogResponse(
            id=log.id,
            user_nickname=log.user.nickname,
            action_type=log.action_type,
            content=log.content,
            detail=json.loads(log.detail) if log.detail else None,
            created_at=log.created_at.isoformat(),
        )
        for log in logs
    ]

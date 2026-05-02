import json
from sqlalchemy.orm import Session
from app.models.activity_log import ActivityLog


def add_activity_log(db: Session, activity_id: int, user_id: int, action_type: str, content: str, detail: dict | None = None):
    log = ActivityLog(
        activity_id=activity_id,
        user_id=user_id,
        action_type=action_type,
        content=content,
        detail=json.dumps(detail, ensure_ascii=False) if detail else None,
    )
    db.add(log)

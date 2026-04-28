from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.models.activity import Activity
from app.schemas.auth import ActivityCreateRequest, ActivityResponse
from app.middleware.auth import get_current_user

router = APIRouter(prefix="/api/activities", tags=["活动"])


@router.post("", response_model=ActivityResponse, status_code=status.HTTP_201_CREATED)
def create_activity(
    body: ActivityCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    activity = Activity(
        user_id=current_user.id,
        title=body.title.strip(),
        description=body.description.strip() if body.description else None,
    )
    db.add(activity)
    db.commit()
    db.refresh(activity)
    return ActivityResponse(
        id=activity.id,
        title=activity.title,
        description=activity.description,
        created_at=activity.created_at.isoformat(),
    )


@router.get("", response_model=list[ActivityResponse])
def list_activities(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    activities = (
        db.query(Activity)
        .filter(Activity.user_id == current_user.id)
        .order_by(Activity.created_at.desc())
        .all()
    )
    return [
        ActivityResponse(
            id=a.id,
            title=a.title,
            description=a.description,
            created_at=a.created_at.isoformat(),
        )
        for a in activities
    ]

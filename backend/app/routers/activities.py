from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.models.activity import Activity
from app.models.activity_member import ActivityMember
from app.schemas.auth import ActivityCreateRequest, ActivityResponse, ActivityDetailResponse, MemberItem
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
    db.flush()

    if body.join_activity:
        member = ActivityMember(activity_id=activity.id, user_id=current_user.id)
        db.add(member)

    db.commit()
    return ActivityResponse(
        id=activity.id,
        slug=activity.slug,
        title=activity.title,
        description=activity.description,
        creator_nickname=current_user.nickname,
        created_at=activity.created_at.isoformat(),
    )


@router.get("", response_model=list[ActivityResponse])
def list_activities(
    type: str = Query("created", regex="^(created|joined)$"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if type == "created":
        activities = (
            db.query(Activity)
            .filter(Activity.user_id == current_user.id)
            .order_by(Activity.created_at.desc())
            .all()
        )
    else:
        activities = (
            db.query(Activity)
            .join(ActivityMember, ActivityMember.activity_id == Activity.id)
            .filter(ActivityMember.user_id == current_user.id)
            .order_by(Activity.created_at.desc())
            .all()
        )

    return [
        ActivityResponse(
            id=a.id,
            slug=a.slug,
            title=a.title,
            description=a.description,
            creator_nickname=a.user.nickname,
            created_at=a.created_at.isoformat(),
        )
        for a in activities
    ]


@router.get("/{slug}", response_model=ActivityDetailResponse)
def get_activity(
    slug: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    activity = db.query(Activity).filter(Activity.slug == slug).first()
    if not activity:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="活动不存在")

    is_member = db.query(ActivityMember).filter(
        ActivityMember.activity_id == activity.id,
        ActivityMember.user_id == current_user.id,
    ).first() is not None

    members = (
        db.query(ActivityMember)
        .filter(ActivityMember.activity_id == activity.id)
        .order_by(ActivityMember.created_at.asc())
        .all()
    )

    members_data = [
        MemberItem(
            user_id=m.user_id,
            nickname=m.user.nickname,
            avatar_path=m.user.avatar_path,
            joined_at=m.created_at.isoformat(),
        )
        for m in members
    ]

    is_creator = activity.user_id == current_user.id

    return ActivityDetailResponse(
        id=activity.id,
        slug=activity.slug,
        title=activity.title,
        description=activity.description,
        creator_nickname=activity.user.nickname,
        created_at=activity.created_at.isoformat(),
        is_member=is_member,
        is_creator=is_creator,
        members=members_data,
    )


@router.post("/{slug}/join")
def join_activity(
    slug: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    activity = db.query(Activity).filter(Activity.slug == slug).first()
    if not activity:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="活动不存在")

    existing = db.query(ActivityMember).filter(
        ActivityMember.activity_id == activity.id,
        ActivityMember.user_id == current_user.id,
    ).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="您已加入该活动")

    member = ActivityMember(activity_id=activity.id, user_id=current_user.id)
    db.add(member)
    db.commit()
    return {"message": "加入成功"}


@router.post("/{slug}/leave")
def leave_activity(
    slug: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    activity = db.query(Activity).filter(Activity.slug == slug).first()
    if not activity:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="活动不存在")

    membership = db.query(ActivityMember).filter(
        ActivityMember.activity_id == activity.id,
        ActivityMember.user_id == current_user.id,
    ).first()
    if not membership:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="您尚未加入该活动")

    db.delete(membership)
    db.commit()
    return {"message": "已退出活动"}


@router.delete("/{slug}")
def delete_activity(
    slug: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    activity = db.query(Activity).filter(Activity.slug == slug).first()
    if not activity:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="活动不存在")

    if activity.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="只有活动创建者才能删除活动")

    db.delete(activity)
    db.commit()
    return {"message": "活动已删除"}

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.models.activity import Activity
from app.models.activity_member import ActivityMember
from app.models.group import Group
from app.models.group_member import GroupMember
from app.schemas.auth import ActivityCreateRequest, ActivityUpdateRequest, ActivityResponse, ActivityDetailResponse, MemberItem, GroupResponse
from app.middleware.auth import get_current_user
import random

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

    groups = (
        db.query(Group)
        .filter(Group.activity_id == activity.id)
        .order_by(Group.group_number.asc())
        .all()
    )

    groups_data = [
        GroupResponse(
            group_number=g.group_number,
            members=[
                MemberItem(
                    user_id=gm.user_id,
                    nickname=gm.user.nickname,
                    avatar_path=gm.user.avatar_path,
                    joined_at="",
                )
                for gm in g.members
            ],
        )
        for g in groups
    ]

    return ActivityDetailResponse(
        id=activity.id,
        slug=activity.slug,
        title=activity.title,
        description=activity.description,
        creator_nickname=activity.user.nickname,
        created_at=activity.created_at.isoformat(),
        is_member=is_member,
        is_creator=is_creator,
        has_groups=len(groups_data) > 0,
        members=members_data,
        groups=groups_data,
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

    if _activity_has_groups(db, activity.id):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="该活动已分组，无法加入")

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

    if _activity_has_groups(db, activity.id):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="该活动已分组，无法退出")

    membership = db.query(ActivityMember).filter(
        ActivityMember.activity_id == activity.id,
        ActivityMember.user_id == current_user.id,
    ).first()
    if not membership:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="您尚未加入该活动")

    db.delete(membership)
    db.commit()
    return {"message": "已退出活动"}


@router.put("/{slug}", response_model=ActivityResponse)
def update_activity(
    slug: str,
    body: ActivityUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    activity = db.query(Activity).filter(Activity.slug == slug).first()
    if not activity:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="活动不存在")

    if activity.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="只有活动创建者才能编辑活动")

    activity.title = body.title.strip()
    activity.description = body.description.strip() if body.description else None
    db.commit()

    return ActivityResponse(
        id=activity.id,
        slug=activity.slug,
        title=activity.title,
        description=activity.description,
        creator_nickname=activity.user.nickname,
        created_at=activity.created_at.isoformat(),
    )


@router.delete("/{slug}/members/{user_id}")
def kick_member(
    slug: str,
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    activity = db.query(Activity).filter(Activity.slug == slug).first()
    if not activity:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="活动不存在")

    if _activity_has_groups(db, activity.id):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="该活动已分组，无法踢出成员")

    if activity.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="只有活动创建者才能踢出成员")

    if user_id == current_user.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="创建者不能踢出自己，请使用退出活动功能")

    membership = db.query(ActivityMember).filter(
        ActivityMember.activity_id == activity.id,
        ActivityMember.user_id == user_id,
    ).first()
    if not membership:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="该用户不是本活动成员")

    db.delete(membership)
    db.commit()
    return {"message": "已将该成员移出活动"}


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


def _activity_has_groups(db: Session, activity_id: int) -> bool:
    return db.query(Group).filter(Group.activity_id == activity_id).first() is not None


@router.post("/{slug}/groups")
def create_groups(
    slug: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    activity = db.query(Activity).filter(Activity.slug == slug).first()
    if not activity:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="活动不存在")

    if activity.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="只有活动创建者才能执行分组")

    members = (
        db.query(ActivityMember)
        .filter(ActivityMember.activity_id == activity.id)
        .all()
    )

    member_user_ids = [m.user_id for m in members]
    random.shuffle(member_user_ids)

    group_number = 1
    groups_result = []

    for i in range(0, len(member_user_ids), 2):
        chunk = member_user_ids[i:i + 2]
        group = Group(activity_id=activity.id, group_number=group_number)
        db.add(group)
        db.flush()

        member_items = []
        for uid in chunk:
            gm = GroupMember(group_id=group.id, user_id=uid)
            db.add(gm)
            member = db.query(User).filter(User.id == uid).first()
            member_items.append(
                MemberItem(
                    user_id=uid,
                    nickname=member.nickname,
                    avatar_path=member.avatar_path,
                    joined_at="",
                )
            )

        groups_result.append(
            GroupResponse(group_number=group_number, members=member_items)
        )
        group_number += 1

    db.commit()
    return {"groups": groups_result}

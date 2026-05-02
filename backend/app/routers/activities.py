from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.models.activity import Activity
from app.models.activity_member import ActivityMember
from app.models.group import Group
from app.models.group_member import GroupMember
from app.schemas.activity import ActivityCreateRequest, ActivityUpdateRequest, ActivityResponse, ActivityDetailResponse, MemberItem, GroupResponse
from app.middleware.auth import get_current_user
from app.services.member import get_attribute_warnings
from app.services.log import add_activity_log

router = APIRouter(tags=["活动"])


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
        group_strategy=body.group_strategy,
        group_param=body.group_param,
        constraints=[c.model_dump() for c in body.constraints] if body.constraints else None,
    )
    db.add(activity)
    db.flush()
    add_activity_log(db, activity.id, current_user.id, "create", f"{current_user.nickname} 创建了活动")
    db.commit()
    return ActivityResponse(
        id=activity.id,
        slug=activity.slug,
        title=activity.title,
        description=activity.description,
        group_strategy=activity.group_strategy,
        group_param=activity.group_param,
        constraints=activity.constraints,
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
            group_strategy=a.group_strategy,
            group_param=a.group_param,
            constraints=a.constraints,
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
            attributes={attr.attribute_name: attr.attribute_value for attr in m.attributes},
        )
        for m in members
    ]

    constraints = activity.constraints
    for item in members_data:
        item.attribute_warnings = get_attribute_warnings(constraints, item.attributes)
    warnings_map = {m.user_id: m.attribute_warnings for m in members_data}

    is_creator = activity.user_id == current_user.id

    groups = (
        db.query(Group)
        .filter(Group.activity_id == activity.id)
        .order_by(Group.group_number.asc())
        .all()
    )

    member_attrs_map = {m.user_id: m.attributes for m in members}

    groups_data = [
        GroupResponse(
            group_number=g.group_number,
            members=[
                MemberItem(
                    user_id=gm.user_id,
                    nickname=gm.user.nickname,
                    avatar_path=gm.user.avatar_path,
                    joined_at="",
                    attributes={attr.attribute_name: attr.attribute_value for attr in member_attrs_map.get(gm.user_id, [])},
                    attribute_warnings=warnings_map.get(gm.user_id, []),
                )
                for gm in g.members
            ],
        )
        for g in groups
    ]

    grouped_user_ids = {gm.user_id for g in groups for gm in g.members}
    ungrouped_members = [m for m in members_data if m.user_id not in grouped_user_ids]

    return ActivityDetailResponse(
        id=activity.id,
        slug=activity.slug,
        title=activity.title,
        description=activity.description,
        group_strategy=activity.group_strategy,
        group_param=activity.group_param,
        constraints=activity.constraints,
        creator_nickname=activity.user.nickname,
        created_at=activity.created_at.isoformat(),
        is_member=is_member,
        is_creator=is_creator,
        has_groups=len(groups_data) > 0,
        members=members_data,
        groups=groups_data,
        ungrouped_members=ungrouped_members,
    )


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

    changes = []
    if activity.title != body.title.strip():
        changes.append(f"标题由「{activity.title}」改为「{body.title.strip()}」")
    if (activity.description or "") != (body.description or "").strip():
        changes.append("修改了描述")

    activity.title = body.title.strip()
    activity.description = body.description.strip() if body.description else None
    activity.group_strategy = body.group_strategy
    activity.group_param = body.group_param
    activity.constraints = [c.model_dump() for c in body.constraints] if body.constraints else None

    content = f"{current_user.nickname} 编辑了活动"
    if changes:
        content += "：" + "；".join(changes)
    add_activity_log(db, activity.id, current_user.id, "edit", content)
    db.commit()

    return ActivityResponse(
        id=activity.id,
        slug=activity.slug,
        title=activity.title,
        description=activity.description,
        group_strategy=activity.group_strategy,
        group_param=activity.group_param,
        constraints=activity.constraints,
        creator_nickname=activity.user.nickname,
        created_at=activity.created_at.isoformat(),
    )


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

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.models.activity import Activity
from app.models.activity_member import ActivityMember
from app.models.member_preference import MemberPreference
from app.models.group import Group
from app.models.group_member import GroupMember
from app.schemas.activity import MemberItem, GroupResponse
from app.middleware.auth import get_current_user
from app.services.log import add_activity_log
from app.services.member import get_attribute_warnings
from app.services.groups import constrained_grouping, simple_grouping

router = APIRouter(tags=["活动分组"])


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

    constraints = activity.constraints
    if constraints:
        members = (
            db.query(ActivityMember)
            .filter(ActivityMember.activity_id == activity.id)
            .all()
        )
        issue_list = []
        for m in members:
            attrs = {a.attribute_name: a.attribute_value for a in m.attributes}
            warnings = get_attribute_warnings(constraints, attrs)
            if warnings:
                issue_list.append({
                    "user_id": m.user_id,
                    "nickname": m.user.nickname,
                    "issues": warnings,
                })
        if issue_list:
            summary = "、".join(
                f"{i['nickname']}（{'；'.join(i['issues'])}）"
                for i in issue_list
            )
            return JSONResponse(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                content={
                    "detail": f"部分成员的属性值不完整——{summary}",
                    "issues": issue_list,
                },
            )

    was_regroup = _activity_has_groups(db, activity.id)
    if was_regroup:
        groups = db.query(Group).filter(Group.activity_id == activity.id).all()
        for g in groups:
            db.query(GroupMember).filter(GroupMember.group_id == g.id).delete()
            db.delete(g)

    members = (
        db.query(ActivityMember)
        .filter(ActivityMember.activity_id == activity.id)
        .all()
    )

    members_for_log = []
    for m in members:
        member_attrs = {
            attr.attribute_name: attr.attribute_value
            for attr in m.attributes
        }
        members_for_log.append({
            "user_id": m.user_id,
            "nickname": m.user.nickname,
            "attributes": member_attrs,
        })

    constraints = activity.constraints
    if constraints:
        groups_result, ungrouped_users, seed = constrained_grouping(
            db, activity.id, activity.group_strategy, activity.group_param, constraints
        )
        shuffle_order = None
    else:
        groups_result, ungrouped_users, seed, shuffle_order = simple_grouping(
            db, activity.id, activity.group_strategy, activity.group_param
        )

    # Persist groups to DB
    for g in groups_result:
        group = Group(activity_id=activity.id, group_number=g["group_number"])
        db.add(group)
        db.flush()
        for m in g["members"]:
            db.add(GroupMember(group_id=group.id, user_id=m.user_id))

    detail = {
        "activity_snapshot": {
            "group_strategy": activity.group_strategy,
            "group_param": activity.group_param,
            "constraints": activity.constraints,
        },
        "members": members_for_log,
        "groups": [
            {
                "group_number": g["group_number"],
                "members": [{"user_id": m.user_id, "nickname": m.nickname} for m in g["members"]],
            }
            for g in groups_result
        ],
        "ungrouped": [
            {"user_id": m.user_id, "nickname": m.nickname}
            for m in ungrouped_users
        ],
    }
    if seed is not None:
        detail["seed"] = seed
        detail["shuffle_order"] = shuffle_order

    pref_count = db.query(MemberPreference.member_id).filter(
        MemberPreference.member_id.in_([m.id for m in members])
    ).distinct().count()
    if pref_count > 0:
        detail["preference_summary"] = f"其中 {pref_count} 名成员设置了成员偏好"

    action_label = "重新分组" if was_regroup else "执行分组"
    add_activity_log(db, activity.id, current_user.id, "group", f"{current_user.nickname} {action_label}", detail)
    db.commit()

    built_groups = [
        GroupResponse(group_number=g["group_number"], members=g["members"])
        for g in groups_result
    ]
    return {"groups": built_groups, "ungrouped_members": ungrouped_users}


@router.delete("/{slug}/groups")
def delete_groups(
    slug: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    activity = db.query(Activity).filter(Activity.slug == slug).first()
    if not activity:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="活动不存在")

    if activity.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="只有活动创建者才能解除分组")

    groups = db.query(Group).filter(Group.activity_id == activity.id).all()
    if not groups:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="该活动尚未分组")

    for group in groups:
        db.query(GroupMember).filter(GroupMember.group_id == group.id).delete()
        db.delete(group)

    add_activity_log(db, activity.id, current_user.id, "ungroup", f"{current_user.nickname} 解除了分组")
    db.commit()
    return {"message": "已解除分组"}

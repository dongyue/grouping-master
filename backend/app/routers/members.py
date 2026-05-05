from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.models.activity import Activity
from app.models.activity_member import ActivityMember
from app.models.member_attribute import MemberAttribute
from app.models.member_preference import MemberPreference
from app.models.group import Group
from app.models.group_member import GroupMember
from app.schemas.activity import JoinActivityRequest
from app.middleware.auth import get_current_user
from app.services.log import add_activity_log
from app.services.user_attribute import sync_user_attributes

router = APIRouter(tags=["活动成员"])


def _save_preferences(db: Session, member_id: int, preferences: dict[str, list[int]] | None):
    if preferences is None:
        return
    db.query(MemberPreference).filter(MemberPreference.member_id == member_id).delete()
    for pref_type in ("want", "avoid"):
        for target_user_id in preferences.get(pref_type, []):
            db.add(MemberPreference(member_id=member_id, target_user_id=target_user_id, preference_type=pref_type))


def _validate_preferences(preferences: dict[str, list[int]], activity: Activity, current_user_id: int, db: Session):
    count_want = len(preferences.get("want", []))
    count_avoid = len(preferences.get("avoid", []))
    if activity.allow_want_preferences and count_want > activity.max_want_count:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                            detail=f"「想同组」最多可选 {activity.max_want_count} 人")
    if activity.allow_avoid_preferences and count_avoid > activity.max_avoid_count:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                            detail=f"「不想同组」最多可选 {activity.max_avoid_count} 人")
    all_targets = set(preferences.get("want", []) + preferences.get("avoid", []))
    if current_user_id in all_targets:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="不能选择自己")
    if all_targets:
        valid_ids = set(
            row[0] for row in db.query(ActivityMember.user_id).filter(
                ActivityMember.activity_id == activity.id,
                ActivityMember.user_id != current_user_id,
            ).all()
        )
        invalid = all_targets - valid_ids
        if invalid:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="所选成员不存在或非本活动成员")


@router.post("/{slug}/join")
def join_activity(
    slug: str,
    body: JoinActivityRequest,
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

    constraints = activity.constraints or []

    if constraints:
        if not body.attribute_values:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="请提供属性值")

        attr_map = {c["attribute_name"]: c["allowed_values"] for c in constraints}
        provided = set(body.attribute_values.keys())
        required = set(attr_map.keys())

        if provided != required:
            missing = required - provided
            extra = provided - required
            if missing:
                raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=f"缺少属性值：{', '.join(sorted(missing))}")
            if extra:
                raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=f"未知属性：{', '.join(sorted(extra))}")

        for attr_name, attr_value in body.attribute_values.items():
            if attr_value not in attr_map[attr_name]:
                raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=f"属性「{attr_name}」的值「{attr_value}」不在允许范围")

    if body.preferences:
        _validate_preferences(body.preferences, activity, current_user.id, db)

    member = ActivityMember(
        activity_id=activity.id,
        user_id=current_user.id,
        nickname=body.nickname.strip(),
    )
    db.add(member)
    db.flush()

    if constraints and body.attribute_values:
        for attr_name, attr_value in body.attribute_values.items():
            db.add(MemberAttribute(member_id=member.id, attribute_name=attr_name, attribute_value=attr_value))

    _save_preferences(db, member.id, body.preferences)

    # Sync nickname back to user profile
    if body.nickname.strip() != current_user.nickname:
        current_user.nickname = body.nickname.strip()

    add_activity_log(db, activity.id, current_user.id, "join", f"{current_user.nickname} 加入了活动")
    if body.attribute_values:
        sync_user_attributes(db, current_user.id, body.attribute_values)
    db.commit()
    return {"message": "加入成功"}


@router.put("/{slug}/member-info")
def update_member_info(
    slug: str,
    body: JoinActivityRequest,
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
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="您尚未加入该活动")

    constraints = activity.constraints or []

    if constraints and body.attribute_values:
        attr_map = {c["attribute_name"]: c["allowed_values"] for c in constraints}
        provided = set(body.attribute_values.keys())
        required = set(attr_map.keys())

        if provided != required:
            missing = required - provided
            extra = provided - required
            if missing:
                raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=f"缺少属性值：{', '.join(sorted(missing))}")
            if extra:
                raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=f"未知属性：{', '.join(sorted(extra))}")

        for attr_name, attr_value in body.attribute_values.items():
            if attr_value not in attr_map[attr_name]:
                raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=f"属性「{attr_name}」的值「{attr_value}」不在允许范围")

        db.query(MemberAttribute).filter(MemberAttribute.member_id == membership.id).delete()
        for attr_name, attr_value in body.attribute_values.items():
            db.add(MemberAttribute(member_id=membership.id, attribute_name=attr_name, attribute_value=attr_value))

        sync_user_attributes(db, current_user.id, body.attribute_values)

    if body.preferences is not None:
        _validate_preferences(body.preferences, activity, current_user.id, db)
        _save_preferences(db, membership.id, body.preferences)

    # Update nickname
    membership.nickname = body.nickname.strip()
    if body.nickname.strip() != current_user.nickname:
        current_user.nickname = body.nickname.strip()

    add_activity_log(db, activity.id, current_user.id, "member_edit", f"{current_user.nickname} 更新了自己在活动中的个人信息")
    db.commit()
    return {"message": "个人信息已更新"}


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

    groups = db.query(Group).filter(Group.activity_id == activity.id).all()
    for g in groups:
        db.query(GroupMember).filter(
            GroupMember.group_id == g.id,
            GroupMember.user_id == current_user.id,
        ).delete()

    db.delete(membership)
    add_activity_log(db, activity.id, current_user.id, "leave", f"{current_user.nickname} 退出了活动")
    db.commit()
    return {"message": "已退出活动"}


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

    if activity.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="只有活动创建者才能踢出成员")

    membership = db.query(ActivityMember).filter(
        ActivityMember.activity_id == activity.id,
        ActivityMember.user_id == user_id,
    ).first()
    if not membership:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="该用户不是本活动成员")

    kicked_user = db.query(User).filter(User.id == user_id).first()

    groups = db.query(Group).filter(Group.activity_id == activity.id).all()
    for g in groups:
        db.query(GroupMember).filter(
            GroupMember.group_id == g.id,
            GroupMember.user_id == user_id,
        ).delete()

    db.delete(membership)
    add_activity_log(db, activity.id, current_user.id, "kick", f"{current_user.nickname} 将 {kicked_user.nickname} 踢出了活动")
    db.commit()
    return {"message": "已将该成员移出活动"}

import random
from sqlalchemy.orm import Session
from app.models.user import User
from app.models.activity_member import ActivityMember
from app.schemas.activity import MemberItem


def _member_attrs(member):
    return {a.attribute_name: a.attribute_value for a in member.attributes}


def _distinct_count(attrs_list, constraint):
    vals = set()
    for attrs in attrs_list:
        v = attrs.get(constraint["attribute_name"])
        if v is not None:
            vals.add(v)
    return len(vals)


def _can_accept(group_attrs_list, new_attrs, constraints, is_last_slot):
    combined = group_attrs_list + [new_attrs]
    for c in constraints:
        distinct = _distinct_count(combined, c)
        if c["constraint_type"] == "max_diversity":
            if distinct > c["constraint_value"]:
                return False
        elif c["constraint_type"] == "min_diversity":
            if is_last_slot and distinct < c["constraint_value"]:
                return False
    return True


def _rarity_sort_key(member_idx, all_attrs, member_map, constraints):
    """Rarity: lower = fewer people share this member's attribute values."""
    if not constraints:
        return 0
    attrs = all_attrs[member_idx]
    min_count = float("inf")
    for c in constraints:
        name = c["attribute_name"]
        v = attrs.get(name)
        if v is None:
            return 0  # missing attribute = rarest, place first
        count = sum(1 for a in all_attrs if a.get(name) == v)
        if count < min_count:
            min_count = count
    return min_count


def constrained_grouping(
    db: Session,
    activity_id: int,
    group_strategy: str,
    group_param: int,
    constraints: list,
):
    members = (
        db.query(ActivityMember)
        .filter(ActivityMember.activity_id == activity_id)
        .all()
    )

    total = len(members)
    if total == 0:
        return [], []

    user_cache = {}
    for m in members:
        user_cache[m.user_id] = db.query(User).filter(User.id == m.user_id).first()

    all_attrs = [_member_attrs(m) for m in members]

    if group_strategy == "fixed_group_count":
        num_groups = min(group_param, total)
        target_size = total // num_groups if num_groups > 0 else 0
    else:
        target_size = group_param
        num_groups = total // group_param if group_param > 0 else 0

    if target_size < 1:
        ungrouped_members = [
            MemberItem(
                user_id=m.user_id,
                nickname=user_cache[m.user_id].nickname,
                avatar_path=user_cache[m.user_id].avatar_path,
                joined_at="",
            )
            for m in members
        ]
        return [], ungrouped_members

    indices = list(range(len(members)))
    seed = random.randint(0, 2**31 - 1)
    rng = random.Random(seed)
    rng.shuffle(indices)
    sorted_indices = sorted(
        indices,
        key=lambda i: _rarity_sort_key(i, all_attrs, {}, constraints),
    )

    groups = []  # list of lists of member indices
    ungrouped_indices = []

    for idx in sorted_indices:
        placed = False
        for g_idx, group in enumerate(groups):
            if len(group) >= target_size:
                continue
            is_last = len(group) + 1 == target_size
            g_attrs = [all_attrs[i] for i in group]
            if _can_accept(g_attrs, all_attrs[idx], constraints, is_last):
                group.append(idx)
                placed = True
                break

        if not placed:
            if len(groups) < num_groups:
                groups.append([idx])
            else:
                ungrouped_indices.append(idx)

    # backfill: try to absorb ungrouped into partially-filled groups
    for u_idx in list(ungrouped_indices):
        u_attrs = all_attrs[u_idx]
        for group in groups:
            if len(group) >= target_size:
                continue
            is_last = len(group) + 1 == target_size
            g_attrs = [all_attrs[i] for i in group]
            if _can_accept(g_attrs, u_attrs, constraints, is_last):
                group.append(u_idx)
                ungrouped_indices.remove(u_idx)
                break

    groups_result = []
    for g_num, group in enumerate(groups):
        group_members = [
            MemberItem(
                user_id=members[i].user_id,
                nickname=user_cache[members[i].user_id].nickname,
                avatar_path=user_cache[members[i].user_id].avatar_path,
                joined_at="",
            )
            for i in group
        ]
        groups_result.append({
            "group_number": g_num + 1,
            "members": group_members,
        })

    ungrouped_members = [
        MemberItem(
            user_id=members[i].user_id,
            nickname=user_cache[members[i].user_id].nickname,
            avatar_path=user_cache[members[i].user_id].avatar_path,
            joined_at="",
        )
        for i in ungrouped_indices
    ]

    return groups_result, ungrouped_members, seed


def simple_grouping(
    db: Session,
    activity_id: int,
    group_strategy: str,
    group_param: int,
):
    """Original random-shuffle grouping (no constraints)."""
    members = (
        db.query(ActivityMember)
        .filter(ActivityMember.activity_id == activity_id)
        .all()
    )

    member_user_ids = [m.user_id for m in members]
    seed = random.randint(0, 2**31 - 1)
    rng = random.Random(seed)
    rng.shuffle(member_user_ids)

    total = len(member_user_ids)

    if group_strategy == "fixed_group_count":
        num_groups = min(group_param, total)
        base_size = total // num_groups
    else:
        num_groups = total // group_param
        base_size = group_param

    groups_result = []
    ungrouped_users = []
    idx = 0

    if num_groups > 0:
        for g in range(num_groups):
            chunk = member_user_ids[idx:idx + base_size]
            idx += base_size
            member_items = []
            for uid in chunk:
                user = db.query(User).filter(User.id == uid).first()
                member_items.append(
                    MemberItem(
                        user_id=uid,
                        nickname=user.nickname,
                        avatar_path=user.avatar_path,
                        joined_at="",
                    )
                )
            groups_result.append({
                "group_number": g + 1,
                "members": member_items,
            })

    for uid in member_user_ids[idx:]:
        user = db.query(User).filter(User.id == uid).first()
        ungrouped_users.append(
            MemberItem(
                user_id=uid,
                nickname=user.nickname,
                avatar_path=user.avatar_path,
                joined_at="",
            )
        )

    return groups_result, ungrouped_users, seed, member_user_ids

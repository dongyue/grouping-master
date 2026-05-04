import random
from sqlalchemy.orm import Session
from app.models.user import User
from app.models.activity_member import ActivityMember
from app.models.member_preference import MemberPreference
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
    if not constraints:
        return True
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


def _build_preference_matrix(members: list, db: Session):
    n = len(members)
    if n == 0:
        return None

    member_ids = [m.id for m in members]
    prefs = (
        db.query(MemberPreference)
        .filter(MemberPreference.member_id.in_(member_ids))
        .all()
    )
    if not prefs:
        return None

    user_id_to_idx = {m.user_id: i for i, m in enumerate(members)}
    member_id_to_user_id = {m.id: m.user_id for m in members}

    want_from = [set() for _ in range(n)]
    avoid_from = [set() for _ in range(n)]

    for p in prefs:
        src_user_id = member_id_to_user_id.get(p.member_id)
        tgt_user_id = p.target_user_id
        if src_user_id is None:
            continue
        i = user_id_to_idx.get(src_user_id)
        j = user_id_to_idx.get(tgt_user_id)
        if i is None or j is None or i == j:
            continue
        if p.preference_type == "want":
            want_from[i].add(j)
        elif p.preference_type == "avoid":
            avoid_from[i].add(j)

    matrix = [[0] * n for _ in range(n)]
    for i in range(n):
        for j in range(n):
            if i == j:
                continue
            i_avoid_j = j in avoid_from[i]
            j_avoid_i = i in avoid_from[j]
            if i_avoid_j and j_avoid_i:
                matrix[i][j] = -6
            elif i_avoid_j or j_avoid_i:
                matrix[i][j] = -2
                continue
            i_want_j = j in want_from[i]
            j_want_i = i in want_from[j]
            if i_want_j and j_want_i:
                matrix[i][j] = 3
            elif i_want_j or j_want_i:
                matrix[i][j] = 1
    return matrix


def _best_group_by_preference(candidate_group_indices, member_idx, groups, pref_matrix, rng):
    if pref_matrix is None:
        return rng.choice(candidate_group_indices) if len(candidate_group_indices) > 1 else candidate_group_indices[0]
    scores = []
    for g_idx in candidate_group_indices:
        group = groups[g_idx]
        score = sum(pref_matrix[member_idx][i] for i in group)
        scores.append(score)
    max_score = max(scores)
    best = [candidate_group_indices[i] for i, s in enumerate(scores) if s == max_score]
    return rng.choice(best) if len(best) > 1 else best[0]


def _compute_groups(
    all_attrs: list[dict],
    group_strategy: str,
    group_param: int,
    constraints: list,
    seed: int | None = None,
    preference_matrix: list[list[int]] | None = None,
):
    total = len(all_attrs)
    if total == 0:
        return [], [], seed or 0

    if group_strategy == "fixed_group_count":
        num_groups = min(group_param, total)
        target_size = total // num_groups if num_groups > 0 else 0
    else:
        target_size = group_param
        num_groups = total // group_param if group_param > 0 else 0

    if target_size < 1:
        return [], list(range(total)), seed or 0

    indices = list(range(total))
    if seed is None:
        seed = random.randint(0, 2**31 - 1)
    rng = random.Random(seed)
    rng.shuffle(indices)
    sorted_indices = sorted(
        indices,
        key=lambda i: _rarity_sort_key(i, all_attrs, {}, constraints),
    )

    groups = []
    ungrouped_indices = []

    for idx in sorted_indices:
        candidates = []
        for g_idx, group in enumerate(groups):
            if len(group) >= target_size:
                continue
            is_last = len(group) + 1 == target_size
            g_attrs = [all_attrs[i] for i in group]
            if _can_accept(g_attrs, all_attrs[idx], constraints, is_last):
                candidates.append(g_idx)

        if candidates:
            best = _best_group_by_preference(candidates, idx, groups, preference_matrix, rng)
            groups[best].append(idx)
        elif len(groups) < num_groups:
            groups.append([idx])
        else:
            ungrouped_indices.append(idx)

    # backfill
    for u_idx in list(ungrouped_indices):
        candidates = []
        u_attrs = all_attrs[u_idx]
        for g_idx, group in enumerate(groups):
            if len(group) >= target_size:
                continue
            is_last = len(group) + 1 == target_size
            g_attrs = [all_attrs[i] for i in group]
            if _can_accept(g_attrs, u_attrs, constraints, is_last):
                candidates.append(g_idx)
        if candidates:
            best = _best_group_by_preference(candidates, u_idx, groups, preference_matrix, rng)
            groups[best].append(u_idx)
            ungrouped_indices.remove(u_idx)

    # Cleanup doomed groups
    changed = True
    while changed:
        changed = False
        doomed = []
        for g_idx, group in enumerate(groups):
            if len(group) >= target_size:
                continue
            fillable = False
            g_attrs = [all_attrs[i] for i in group]
            is_last_check = len(group) + 1 == target_size
            for u_idx in ungrouped_indices:
                if _can_accept(g_attrs, all_attrs[u_idx], constraints, is_last_check):
                    fillable = True
                    break
            if not fillable:
                doomed.append(g_idx)
        for g_idx in reversed(doomed):
            for i in groups[g_idx]:
                ungrouped_indices.append(i)
            groups.pop(g_idx)
            changed = True
        # Retry backfill
        for u_idx in list(ungrouped_indices):
            candidates = []
            u_attrs = all_attrs[u_idx]
            for g_idx, group in enumerate(groups):
                if len(group) >= target_size:
                    continue
                is_last = len(group) + 1 == target_size
                g_attrs = [all_attrs[i] for i in group]
                if _can_accept(g_attrs, u_attrs, constraints, is_last):
                    candidates.append(g_idx)
            if candidates:
                best = _best_group_by_preference(candidates, u_idx, groups, preference_matrix, rng)
                groups[best].append(u_idx)
                ungrouped_indices.remove(u_idx)
        # Rebuild
        while len(groups) < num_groups:
            candidate = []
            for u_idx in list(ungrouped_indices):
                u_attrs = all_attrs[u_idx]
                c_attrs = [all_attrs[i] for i in candidate]
                is_last = len(candidate) + 1 == target_size
                if _can_accept(c_attrs, u_attrs, constraints, is_last):
                    candidate.append(u_idx)
                    ungrouped_indices.remove(u_idx)
                    if len(candidate) == target_size:
                        groups.append(candidate)
                        changed = True
                        break
            else:
                # Cannot form a full group; return candidate members to ungrouped
                ungrouped_indices.extend(candidate)
                break

    return groups, ungrouped_indices, seed


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
    preference_matrix = _build_preference_matrix(members, db)

    groups, ungrouped_indices, seed = _compute_groups(
        all_attrs, group_strategy, group_param, constraints,
        preference_matrix=preference_matrix,
    )

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

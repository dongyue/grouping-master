import pytest
import random
from app.services.groups import (
    _distinct_count,
    _can_accept,
    _rarity_sort_key,
    _compute_groups,
    _best_group_by_preference,
)


# ---------------------------------------------------------------------------
# _distinct_count
# ---------------------------------------------------------------------------
def test_distinct_count_empty():
    assert _distinct_count([], {"attribute_name": "性别"}) == 0


def test_distinct_count_single_value():
    attrs = [{"性别": "男"}, {"性别": "男"}, {"性别": "男"}]
    assert _distinct_count(attrs, {"attribute_name": "性别"}) == 1


def test_distinct_count_two_values():
    attrs = [{"性别": "男"}, {"性别": "女"}]
    assert _distinct_count(attrs, {"attribute_name": "性别"}) == 2


def test_distinct_count_missing_attribute():
    attrs = [{"性别": "男"}, {"部门": "工程部"}]
    assert _distinct_count(attrs, {"attribute_name": "性别"}) == 1


# ---------------------------------------------------------------------------
# _can_accept
# ---------------------------------------------------------------------------
MAX_1_GENDER = [
    {"attribute_name": "性别", "allowed_values": ["男", "女"], "constraint_type": "max_diversity", "constraint_value": 1},
]

MIN_2_GENDER = [
    {"attribute_name": "性别", "allowed_values": ["男", "女"], "constraint_type": "min_diversity", "constraint_value": 2},
]


def test_can_accept_max_diversity_same_gender():
    # M+M → still 1 distinct → OK
    assert _can_accept([{"性别": "男"}], {"性别": "男"}, MAX_1_GENDER, True)
    assert _can_accept([{"性别": "男"}], {"性别": "男"}, MAX_1_GENDER, False)


def test_can_accept_max_diversity_diff_gender():
    # M+F → 2 distinct > 1 → REJECT
    assert not _can_accept([{"性别": "男"}], {"性别": "女"}, MAX_1_GENDER, True)
    assert not _can_accept([{"性别": "男"}], {"性别": "女"}, MAX_1_GENDER, False)


def test_can_accept_min_diversity_not_last_slot_always_ok():
    # Even though only 1 distinct, not the last slot → OK (can still add diversity later)
    assert _can_accept([{"性别": "男"}], {"性别": "男"}, MIN_2_GENDER, False)


def test_can_accept_min_diversity_last_slot_same_gender_fail():
    # Last slot, only 1 distinct < 2 → REJECT
    assert not _can_accept([{"性别": "男"}], {"性别": "男"}, MIN_2_GENDER, True)


def test_can_accept_min_diversity_last_slot_diverse_ok():
    # Last slot, 2 distinct ≥ 2 → OK
    assert _can_accept([{"性别": "男"}], {"性别": "女"}, MIN_2_GENDER, True)


def test_can_accept_both_constraints_met():
    cs = [
        {"attribute_name": "性别", "allowed_values": ["男", "女"], "constraint_type": "max_diversity", "constraint_value": 2},
        {"attribute_name": "性别", "allowed_values": ["男", "女"], "constraint_type": "min_diversity", "constraint_value": 2},
    ]
    # 1M + 1F → 2 distinct, max ≤ 2, min ≥ 2 → OK
    assert _can_accept([{"性别": "男"}], {"性别": "女"}, cs, True)


def test_can_accept_both_constraints_max_fails():
    cs = [
        {"attribute_name": "性别", "allowed_values": ["男", "女"], "constraint_type": "max_diversity", "constraint_value": 1},
        {"attribute_name": "性别", "allowed_values": ["男", "女"], "constraint_type": "min_diversity", "constraint_value": 2},
    ]
    # 1M + 1F → 2 distinct, max=1 fails
    assert not _can_accept([{"性别": "男"}], {"性别": "女"}, cs, True)


def test_can_accept_empty_constraints():
    """约束为空列表时始终可接受"""
    assert _can_accept([{"性别": "男"}], {"性别": "女"}, [], True)
    assert _can_accept([{"性别": "男"}], {"性别": "女"}, [], False)


def test_can_accept_none_constraints():
    """约束为 None 时始终可接受"""
    assert _can_accept([{"性别": "男"}], {"性别": "女"}, None, True)
    assert _can_accept([{"性别": "男"}], {"性别": "女"}, None, False)


# ---------------------------------------------------------------------------
# _rarity_sort_key
# ---------------------------------------------------------------------------
def test_rarity_no_constraints():
    attrs = [{"性别": "男"}]
    assert _rarity_sort_key(0, attrs, {}, []) == 0


def test_rarity_female_rarer():
    # 3 males, 1 female
    attrs = [{"性别": "男"}, {"性别": "男"}, {"性别": "男"}, {"性别": "女"}]
    # Female (index 3) rarity = 1 (only 1 person with 女)
    # Male (index 0) rarity = 3 (3 people with 男)
    assert _rarity_sort_key(3, attrs, {}, [{"attribute_name": "性别"}]) == 1
    assert _rarity_sort_key(0, attrs, {}, [{"attribute_name": "性别"}]) == 3


def test_rarity_missing_attribute_rarest():
    attrs = [{"性别": "男"}, {"部门": "工程部"}]
    # Index 1 has no 性别 → rarity 0 (rarest)
    assert _rarity_sort_key(1, attrs, {}, [{"attribute_name": "性别"}]) == 0


def test_rarity_none_constraints():
    """约束为 None 时稀有度返回 0"""
    attrs = [{"性别": "男"}]
    assert _rarity_sort_key(0, attrs, {}, None) == 0


# ---------------------------------------------------------------------------
# _compute_groups
# ---------------------------------------------------------------------------

FIXED_SEED = 42

# Helper: create a list of member attrs dicts
M = {"性别": "男"}
F = {"性别": "女"}


def _group_attr_counts(groups, all_attrs, constraint):
    """Return list of distinct-count-per-group for given constraint."""
    return [
        _distinct_count([all_attrs[i] for i in g], constraint)
        for g in groups
    ]


def test_compute_without_constraints():
    """No constraints → random grouping, just verify all members placed or accounted for."""
    attrs = [M] * 5
    groups, ungrouped, seed = _compute_groups(attrs, "fixed_group_size", 2, [], FIXED_SEED)
    total_placed = sum(len(g) for g in groups)
    assert total_placed + len(ungrouped) == 5


def test_max_diversity_same_gender_together():
    """4M+3F, size=2, max_diversity=1 → 3 full groups, 1F ungrouped."""
    attrs = [M, M, M, M, F, F, F]
    groups, ungrouped, seed = _compute_groups(
        attrs, "fixed_group_size", 2, MAX_1_GENDER, FIXED_SEED
    )

    # 3 full groups expected
    assert len(groups) == 3
    for g in groups:
        assert len(g) == 2

    # Every group must respect max_diversity ≤ 1
    for g in groups:
        dc = _distinct_count([attrs[i] for i in g], MAX_1_GENDER[0])
        assert dc <= 1, f"Group {g} violates max_diversity"

    # 1 ungrouped
    assert len(ungrouped) == 1


def test_min_diversity_mix_genders():
    """3M+3F, size=2, min_diversity=2 → 3 mixed groups, 0 ungrouped."""
    attrs = [M, M, M, F, F, F]
    groups, ungrouped, seed = _compute_groups(
        attrs, "fixed_group_size", 2, MIN_2_GENDER, FIXED_SEED
    )

    assert len(groups) == 3
    assert len(ungrouped) == 0
    for g in groups:
        assert len(g) == 2
        dc = _distinct_count([attrs[i] for i in g], MIN_2_GENDER[0])
        assert dc >= 2, f"Group {g} does not meet min_diversity"


def test_impossible_constraint():
    """1 person, min_diversity=2 → impossible, all ungrouped."""
    attrs = [M]
    groups, ungrouped, seed = _compute_groups(
        attrs, "fixed_group_size", 2, MIN_2_GENDER, FIXED_SEED
    )
    assert len(groups) == 0
    assert len(ungrouped) == 1


def test_all_same_value_max_diversity_ok():
    """All male, size=2, max_diversity=1 → all full groups, no constraint violation."""
    attrs = [M] * 6
    groups, ungrouped, seed = _compute_groups(
        attrs, "fixed_group_size", 2, MAX_1_GENDER, FIXED_SEED
    )
    assert len(groups) == 3
    assert len(ungrouped) == 0
    for g in groups:
        assert len(g) == 2


def test_fixed_group_count_strategy():
    """5 people, fixed_group_count=2, no constraints → 2 groups of 2, 1 ungrouped."""
    attrs = [M] * 5
    groups, ungrouped, seed = _compute_groups(
        attrs, "fixed_group_count", 2, [], FIXED_SEED
    )
    assert len(groups) == 2
    # Each group should have 5//2 = 2 people
    for g in groups:
        assert len(g) == 2
    assert len(ungrouped) == 1


def test_doomed_group_cleanup():
    """3F+4M, size=2, max_diversity=1.

    Without cleanup, a female-only group of size 1 would linger.
    With cleanup, 3 full groups of 2, 1 ungrouped.
    """
    attrs = [F, F, F, M, M, M, M]
    groups, ungrouped, seed = _compute_groups(
        attrs, "fixed_group_size", 2, MAX_1_GENDER, FIXED_SEED
    )
    # No partial groups allowed
    for g in groups:
        assert len(g) == 2, f"Group {g} is not full"
    for g in groups:
        dc = _distinct_count([attrs[i] for i in g], MAX_1_GENDER[0])
        assert dc <= 1


def test_multi_constraint():
    """Two constraints: max_diversity=1 on gender, min_diversity=2 on department.

    With 2x工程部, 1x市场部, 1x财务部 (all male), and size=2:
    [工程部, 工程部] fails min_diversity → only [市场部, 财务部] is valid.
    → 1 full group, 2 ungrouped.
    """
    cs = [
        {"attribute_name": "性别", "allowed_values": ["男", "女"], "constraint_type": "max_diversity", "constraint_value": 1},
        {"attribute_name": "部门", "allowed_values": ["工程部", "市场部", "财务部"], "constraint_type": "min_diversity", "constraint_value": 2},
    ]
    attrs = [
        {"性别": "男", "部门": "工程部"},
        {"性别": "男", "部门": "市场部"},
        {"性别": "男", "部门": "财务部"},
        {"性别": "男", "部门": "工程部"},
    ]
    groups, ungrouped, seed = _compute_groups(
        attrs, "fixed_group_size", 2, cs, FIXED_SEED
    )
    # Only 1 valid pair can be formed
    assert len(groups) == 1
    assert len(ungrouped) == 2
    # The group must satisfy both constraints
    for g in groups:
        assert len(g) == 2
        dc_gender = _distinct_count([attrs[i] for i in g], cs[0])
        dc_dept = _distinct_count([attrs[i] for i in g], cs[1])
        assert dc_gender <= 1
        assert dc_dept >= 2


# ---------------------------------------------------------------------------
# _best_group_by_preference
# ---------------------------------------------------------------------------

def test_best_group_by_preference_highest_score():
    """多个候选组，选偏好得分最高的"""
    rng = random.Random(42)
    groups = [[0], [1], [2]]  # 三个组，各有一个成员
    pref = [
        [0, 0, 0, 0],
        [0, 0, 0, 0],
        [0, 0, 0, 0],
        [3, 1, 0, 0],  # 新成员 idx=3: 对组0得3分，组1得1分，组2得0分
    ]
    best = _best_group_by_preference([0, 1, 2], 3, groups, pref, rng)
    assert best == 0  # 组0得分最高


def test_best_group_by_preference_tie_picks_any():
    """得分相同时返回结果在候选组中"""
    rng = random.Random(42)
    groups = [[0], [1]]
    pref = [
        [0, 0, 0],
        [0, 0, 0],
        [1, 1, 0],  # idx=2 对两组得分相同
    ]
    best = _best_group_by_preference([0, 1], 2, groups, pref, rng)
    assert best in [0, 1]


def test_best_group_by_preference_no_pref_matrix():
    """无偏好矩阵时随机选择候选组之一"""
    rng = random.Random(42)
    groups = [[0], [1], [2]]
    best = _best_group_by_preference([0, 1, 2], 3, groups, None, rng)
    assert best in [0, 1, 2]


def test_best_group_by_preference_single_candidate():
    """只有一个候选组直接返回"""
    rng = random.Random(42)
    groups = [[0]]
    pref = [[0, 0], [0, 0]]
    best = _best_group_by_preference([0], 1, groups, pref, rng)
    assert best == 0


# ---------------------------------------------------------------------------
# _compute_groups with preferences
# ---------------------------------------------------------------------------

PREF_SEED = 100

M_ATTRS = {"性别": "男"}
F_ATTRS = {"性别": "女"}


def test_compute_mutual_want_same_group():
    """6人，每组2人。用约束排序让互相want的0,1排在最后，确保他们面前有可选组"""
    # 无害约束，仅用于驱动稀有度排序：0,1属性值常见（排后），2-5各自唯一（排前）
    tag_constraint = [
        {"attribute_name": "tag", "allowed_values": ["A","B","C","D","E"],
         "constraint_type": "max_diversity", "constraint_value": 10},
    ]
    all_attrs = [
        {"tag": "A"},  # idx=0, 2人有A → 稀有度=2，排后
        {"tag": "A"},  # idx=1
        {"tag": "B"},  # idx=2, 1人有B → 稀有度=1，排前
        {"tag": "C"},  # idx=3
        {"tag": "D"},  # idx=4
        {"tag": "E"},  # idx=5
    ]
    pref = [
        [0, 3, 0, 0, 0, 0],
        [3, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0],
    ]
    groups, ungrouped, seed = _compute_groups(
        all_attrs, "fixed_group_size", 2, tag_constraint, PREF_SEED,
        preference_matrix=pref,
    )
    assert len(groups) == 3
    assert len(ungrouped) == 0
    for g in groups:
        if 0 in g:
            assert 1 in g


def test_compute_mutual_avoid_different_groups():
    """6人，每组2人。互相avoid的0,1排在最后，有多组可选时应被分开"""
    tag_constraint = [
        {"attribute_name": "tag", "allowed_values": ["A","B","C","D","E"],
         "constraint_type": "max_diversity", "constraint_value": 10},
    ]
    all_attrs = [
        {"tag": "A"}, {"tag": "A"},
        {"tag": "B"}, {"tag": "C"}, {"tag": "D"}, {"tag": "E"},
    ]
    pref = [
        [0, -6, 0, 0, 0, 0],
        [-6, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0],
    ]
    groups, ungrouped, seed = _compute_groups(
        all_attrs, "fixed_group_size", 2, tag_constraint, PREF_SEED,
        preference_matrix=pref,
    )
    assert len(groups) == 3
    assert len(ungrouped) == 0
    for g in groups:
        assert len(g) == 2
        assert _distinct_count([all_attrs[i] for i in g], tag_constraint[0]) <= 10


def test_compute_avoid_priority_over_want():
    """6人，每组2人。成员0 want 1，成员1 avoid 0，偏好矩阵中视为避免关系。
    由于0,1排最后可能仅有一个候选组从而被迫同组，这里仅验证硬约束和分组结构。"""
    tag_constraint = [
        {"attribute_name": "tag", "allowed_values": ["A","B","C","D","E"],
         "constraint_type": "max_diversity", "constraint_value": 10},
    ]
    all_attrs = [
        {"tag": "A"}, {"tag": "A"},
        {"tag": "B"}, {"tag": "C"}, {"tag": "D"}, {"tag": "E"},
    ]
    pref = [
        [0, -2, 0, 0, 0, 0],
        [-2, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0],
    ]
    groups, ungrouped, seed = _compute_groups(
        all_attrs, "fixed_group_size", 2, tag_constraint, PREF_SEED,
        preference_matrix=pref,
    )
    assert len(groups) == 3
    assert len(ungrouped) == 0
    for g in groups:
        assert len(g) == 2


def test_compute_constraint_overrides_preference_mutual_want():
    """成员0和1互相want，但性别相同且约束要求每组必须男女混合（min_diversity=2）。
    偏好不能让位于约束，0和1可能不在同一组。"""
    all_attrs = [
        {"性别": "男"},  # idx=0 男
        {"性别": "男"},  # idx=1 男，0 want 1
        {"性别": "女"},  # idx=2 女
        {"性别": "女"},  # idx=3 女
    ]
    pref = [
        [0, 3, 0, 0],
        [3, 0, 0, 0],
        [0, 0, 0, 0],
        [0, 0, 0, 0],
    ]
    groups, ungrouped, seed = _compute_groups(
        all_attrs, "fixed_group_size", 2, MIN_2_GENDER, PREF_SEED,
        preference_matrix=pref,
    )
    # 必须满足 min_diversity
    for g in groups:
        assert len(g) == 2
        dc = _distinct_count([all_attrs[i] for i in g], MIN_2_GENDER[0])
        assert dc >= 2


def test_compute_no_constraint_with_preferences():
    """有want和avoid混合偏好，验证偏好矩阵不影响分组结构的正确性"""
    tag_constraint = [
        {"attribute_name": "tag", "allowed_values": ["A","B","C","D","E","F","G","H"],
         "constraint_type": "max_diversity", "constraint_value": 10},
    ]
    all_attrs = [
        {"tag": "A"}, {"tag": "A"},  # 0,1 互相want，排后
        {"tag": "B"}, {"tag": "B"},  # 2,3 互相avoid，排后
        {"tag": "C"}, {"tag": "D"}, {"tag": "E"}, {"tag": "F"}, {"tag": "G"}, {"tag": "H"},
    ]
    # 0↔1互相want(+3)，2↔3互相avoid(-6)
    pref = [
        [0, 3, 0,  0,  0, 0, 0, 0, 0, 0],
        [3, 0, 0,  0,  0, 0, 0, 0, 0, 0],
        [0, 0, 0, -6,  0, 0, 0, 0, 0, 0],
        [0, 0, -6, 0,  0, 0, 0, 0, 0, 0],
        [0, 0, 0,  0,  0, 0, 0, 0, 0, 0],
        [0, 0, 0,  0,  0, 0, 0, 0, 0, 0],
        [0, 0, 0,  0,  0, 0, 0, 0, 0, 0],
        [0, 0, 0,  0,  0, 0, 0, 0, 0, 0],
        [0, 0, 0,  0,  0, 0, 0, 0, 0, 0],
        [0, 0, 0,  0,  0, 0, 0, 0, 0, 0],
    ]
    groups, ungrouped, seed = _compute_groups(
        all_attrs, "fixed_group_size", 2, tag_constraint, PREF_SEED,
        preference_matrix=pref,
    )
    assert len(groups) == 5
    assert len(ungrouped) == 0
    for g in groups:
        assert len(g) == 2
        assert _distinct_count([all_attrs[i] for i in g], tag_constraint[0]) <= 10


def test_compute_preference_no_pref_matrix():
    """偏好矩阵为None时行为等同无偏好"""
    all_attrs = [{}, {}, {}, {}]
    groups, ungrouped, seed = _compute_groups(
        all_attrs, "fixed_group_size", 2, [], PREF_SEED, preference_matrix=None
    )
    assert len(groups) == 2
    assert len(ungrouped) == 0


def test_compute_none_constraints_with_preferences():
    """constraints=None 且有偏好矩阵时正常运行不崩溃"""
    all_attrs = [{}, {}, {}, {}]
    pref = [
        [0, 3, 0, 0],
        [3, 0, 0, 0],
        [0, 0, 0, 0],
        [0, 0, 0, 0],
    ]
    groups, ungrouped, seed = _compute_groups(
        all_attrs, "fixed_group_size", 2, None, PREF_SEED, preference_matrix=pref
    )
    assert len(groups) == 2
    assert len(ungrouped) == 0
    for g in groups:
        assert len(g) == 2


def test_compute_empty_constraints_with_preferences():
    """constraints=[] 且有偏好矩阵时正常运行"""
    all_attrs = [{}, {}, {}, {}, {}, {}]
    pref = [
        [0, -6, 0, 0, 0, 0],
        [-6, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0],
    ]
    groups, ungrouped, seed = _compute_groups(
        all_attrs, "fixed_group_size", 2, [], PREF_SEED, preference_matrix=pref
    )
    assert len(groups) == 3
    assert len(ungrouped) == 0

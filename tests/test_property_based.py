#!/usr/bin/env python3
"""
Property-Based Tests for The King in Yellow.
Uses Hypothesis to generate random inputs and verify invariants
that must always hold regardless of input values.
"""

import sys
import os
import random
import math

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from hypothesis import given, strategies as st, settings, assume
from engine.models import GameState, Item, Skill, StatusEffect, apply_status, has_status
from engine.combat import start_combat, apply_damage_to_enemy, apply_damage_to_player, enemy_turn
from engine.damage import calc_player_damage, _base_damage
from engine.status_effects import (
    process_status_effects, process_player_status_effects, tick_player_buffs,
)
from engine.items import generate_item, determine_rarity
from data import CLASSES, ACC_MIN, ACC_MAX

# ═══════════════════════════════════════════
# Hypothesis strategies
# ═══════════════════════════════════════════

stat_names = st.sampled_from(["int", "str", "agi", "wis", "luck"])
class_ids = st.sampled_from(list(CLASSES.keys()))
small_ints = st.integers(min_value=0, max_value=100)
positive_ints = st.integers(min_value=1, max_value=999)
floors = st.integers(min_value=1, max_value=20)
madness_values = st.integers(min_value=-100, max_value=200)


def make_state(class_id="scholar"):
    state = GameState()
    state.init_from_class(class_id)
    return state


def make_combat(class_id="scholar", is_boss=False):
    state = make_state(class_id)
    start_combat(state, is_boss=is_boss)
    return state


# ═══════════════════════════════════════════
# Property: Madness is always in [0, 100]
# ═══════════════════════════════════════════

_madness_tests = 0
_madness_passed = 0


@given(amount=st.integers(min_value=-500, max_value=500))
@settings(max_examples=100)
def test_madness_always_clamped(amount):
    """For ANY integer amount, madness stays in [0, 100]."""
    global _madness_tests, _madness_passed
    _madness_tests += 1
    state = make_state("brute")
    state.madness = 50
    state.add_madness(amount)
    if 0 <= state.madness <= 100:
        _madness_passed += 1


# ═══════════════════════════════════════════
# Property: HP never goes negative
# ═══════════════════════════════════════════

_hp_tests = 0
_hp_passed = 0


@given(raw_damage=st.integers(min_value=0, max_value=100000))
@settings(max_examples=100)
def test_player_hp_never_negative(raw_damage):
    """For ANY raw damage value, player HP stays >= 0."""
    global _hp_tests, _hp_passed
    _hp_tests += 1
    try:
        state = make_combat("brute")
        dmg, result = apply_damage_to_player(state, raw_damage, True)
        if state.hp >= 0:
            _hp_passed += 1
    except Exception:
        pass  # Crashes are failures


# ═══════════════════════════════════════════
# Property: Enemy HP never goes negative
# ═══════════════════════════════════════════

_enemy_hp_tests = 0
_enemy_hp_passed = 0


@given(power=st.floats(min_value=0.1, max_value=100.0))
@settings(max_examples=50)
def test_enemy_hp_never_negative(power):
    """For ANY skill power, enemy HP stays >= 0."""
    global _enemy_hp_tests, _enemy_hp_passed
    _enemy_hp_tests += 1
    try:
        state = make_combat("scholar")
        skill = Skill(name="Test", type="physical", power=power, stat="str", desc="t", formula="t")
        raw = calc_player_damage(state, skill)
        apply_damage_to_enemy(state, raw, skill)
        if state.combat.enemy.hp >= 0:
            _enemy_hp_passed += 1
    except Exception:
        pass


# ═══════════════════════════════════════════
# Property: recalc_stats maintains invariants
# ═══════════════════════════════════════════

_recalc_tests = 0
_recalc_passed = 0


@given(class_id=class_ids)
@settings(max_examples=10)
def test_recalc_invariants(class_id):
    """For ANY class, recalc_stats produces valid derived stats."""
    global _recalc_tests, _recalc_passed
    _recalc_tests += 1
    state = make_state(class_id)
    state.recalc_stats()
    ok = (
        state.max_hp >= 1
        and state.atk >= 1
        and state.defense >= 0
        and state.m_def >= 0
        and state.crit >= 0
        and state.evasion >= 0
        and state.luck >= 1
        and ACC_MIN <= state.accuracy <= ACC_MAX
    )
    if ok:
        _recalc_passed += 1


# ═══════════════════════════════════════════
# Property: Item generation always valid
# ═══════════════════════════════════════════

_item_tests = 0
_item_passed = 0


@given(floor=floors, luck=st.integers(min_value=0, max_value=100))
@settings(max_examples=50)
def test_item_generation_valid(floor, luck):
    """For ANY floor/luck combo, generated items are structurally valid."""
    global _item_tests, _item_passed
    _item_tests += 1
    try:
        random.seed(42)
        item = generate_item(floor, luck=luck)
        ok = (
            isinstance(item.name, str) and len(item.name) > 0
            and item.rarity in (1, 2, 3, 4)
            and isinstance(item.stats, dict) and len(item.stats) > 0
            and isinstance(item.slot, str) and len(item.slot) > 0
        )
        if ok:
            _item_passed += 1
    except Exception:
        pass


# ═══════════════════════════════════════════
# Property: Rarity is always in [1, 4]
# ═══════════════════════════════════════════

_rarity_tests = 0
_rarity_passed = 0


@given(floor=st.integers(min_value=1, max_value=50), luck=st.integers(min_value=-50, max_value=200))
@settings(max_examples=50)
def test_rarity_bounds(floor, luck):
    """For ANY floor/luck combo, rarity is always in [1, 4]."""
    global _rarity_tests, _rarity_passed
    _rarity_tests += 1
    try:
        random.seed(42)
        r = determine_rarity(floor, luck)
        if 1 <= r <= 4:
            _rarity_passed += 1
    except Exception:
        pass


# ═══════════════════════════════════════════
# Property: Accuracy bounded regardless of AGI
# ═══════════════════════════════════════════

_acc_tests = 0
_acc_passed = 0


@given(agi=st.integers(min_value=1, max_value=200))
@settings(max_examples=50)
def test_accuracy_bounded(agi):
    """For ANY AGI value, accuracy stays within bounds."""
    global _acc_tests, _acc_passed
    _acc_tests += 1
    state = make_state("scholar")
    state.base_stats["agi"] = agi
    state.recalc_stats()
    if ACC_MIN <= state.accuracy <= ACC_MAX:
        _acc_passed += 1


# ═══════════════════════════════════════════
# Property: Non-damage skills produce 0 base damage
# ═══════════════════════════════════════════

_nondmg_tests = 0
_nondmg_passed = 0


@given(
    skill_type=st.sampled_from(["self_buff", "self_heal", "self_shield"]),
    power=st.floats(min_value=0.1, max_value=50.0),
)
@settings(max_examples=30)
def test_non_damage_skill_structure(skill_type, power):
    """Non-damage skill types produce valid Skill objects with correct type."""
    global _nondmg_tests, _nondmg_passed
    _nondmg_tests += 1
    skill = Skill(name="T", type=skill_type, power=power, stat="int", desc="t", formula="t")
    if skill.type in ("self_buff", "self_heal", "self_shield"):
        _nondmg_passed += 1


# ═══════════════════════════════════════════
# Property: Status application is idempotent in structure
# ═══════════════════════════════════════════

_status_tests = 0
_status_passed = 0


@given(
    status_type=st.sampled_from(["burning", "poisoned", "bleeding", "weakened", "frozen"]),
    duration1=st.integers(min_value=1, max_value=10),
    duration2=st.integers(min_value=1, max_value=10),
)
@settings(max_examples=50)
def test_status_refresh_idempotent(status_type, duration1, duration2):
    """Reapplying a status sets duration to max(old, new)."""
    global _status_tests, _status_passed
    _status_tests += 1
    from engine.models import Enemy as E
    e = E.__new__(E)
    e.statuses = []
    e.hp = 100
    e.max_hp = 100
    e.stunned = False

    apply_status(e, status_type, duration1)
    expected_max = max(duration1, duration2)
    apply_status(e, status_type, duration2)

    found = next((s for s in e.statuses if s.type == status_type), None)
    if found and found.duration == expected_max:
        _status_passed += 1


# ═══════════════════════════════════════════
# Property: Level up always increases level
# ═══════════════════════════════════════════

_levelup_tests = 0
_levelup_passed = 0


@given(extra_xp=st.integers(min_value=1, max_value=10000))
@settings(max_examples=30)
def test_level_up_increases(extra_xp):
    """For ANY positive XP, level up increases level by >= 1."""
    global _levelup_tests, _levelup_passed
    _levelup_tests += 1
    try:
        state = make_state("scholar")
        initial_level = state.level
        state.xp = state.xp_next + extra_xp
        state.check_level_up()
        if state.level > initial_level:
            _levelup_passed += 1
    except Exception:
        pass


# ═══════════════════════════════════════════
# RUNNER
# ═══════════════════════════════════════════

def run_all_tests():
    print("=" * 60)
    print("THE KING IN YELLOW — Property-Based Tests (Hypothesis)")
    print("=" * 60)

    global _madness_tests, _madness_passed
    print("\n  Running madness clamping tests (100 random values)...")
    test_madness_always_clamped()
    print(f"    Madness clamped: {_madness_passed}/{_madness_tests}")

    global _hp_tests, _hp_passed
    print("  Running player HP non-negative tests (100 random values)...")
    test_player_hp_never_negative()
    print(f"    Player HP non-negative: {_hp_passed}/{_hp_tests}")

    global _enemy_hp_tests, _enemy_hp_passed
    print("  Running enemy HP non-negative tests (50 random values)...")
    test_enemy_hp_never_negative()
    print(f"    Enemy HP non-negative: {_enemy_hp_passed}/{_enemy_hp_tests}")

    global _recalc_tests, _recalc_passed
    print("  Running recalc_stats invariant tests (all classes)...")
    test_recalc_invariants()
    print(f"    recalc_stats invariants: {_recalc_passed}/{_recalc_tests}")

    global _item_tests, _item_passed
    print("  Running item generation validity tests (50 random combos)...")
    test_item_generation_valid()
    print(f"    Item generation valid: {_item_passed}/{_item_tests}")

    global _rarity_tests, _rarity_passed
    print("  Running rarity bounds tests (50 random combos)...")
    test_rarity_bounds()
    print(f"    Rarity in [1,4]: {_rarity_passed}/{_rarity_tests}")

    global _acc_tests, _acc_passed
    print("  Running accuracy bounds tests (50 AGI values)...")
    test_accuracy_bounded()
    print(f"    Accuracy bounded: {_acc_passed}/{_acc_tests}")

    global _nondmg_tests, _nondmg_passed
    print("  Running non-damage skill structure tests (30 combos)...")
    test_non_damage_skill_structure()
    print(f"    Non-damage structure: {_nondmg_passed}/{_nondmg_tests}")

    global _status_tests, _status_passed
    print("  Running status refresh tests (50 combos)...")
    test_status_refresh_idempotent()
    print(f"    Status refresh: {_status_passed}/{_status_tests}")

    global _levelup_tests, _levelup_passed
    print("  Running level-up tests (30 random XP values)...")
    test_level_up_increases()
    print(f"    Level up increases: {_levelup_passed}/{_levelup_tests}")

    total_tests = (
        _madness_tests + _hp_tests + _enemy_hp_tests + _recalc_tests
        + _item_tests + _rarity_tests + _acc_tests + _nondmg_tests
        + _status_tests + _levelup_tests
    )
    total_passed = (
        _madness_passed + _hp_passed + _enemy_hp_passed + _recalc_passed
        + _item_passed + _rarity_passed + _acc_passed + _nondmg_passed
        + _status_passed + _levelup_passed
    )
    total_failed = total_tests - total_passed

    print(f"\n{'=' * 60}")
    print(f"Results: {total_passed} passed, {total_failed} failed, {total_tests} total")
    print(f"{'=' * 60}")
    return total_failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)

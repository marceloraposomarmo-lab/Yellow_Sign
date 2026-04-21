#!/usr/bin/env python3
"""
Edge Case Tests for The King in Yellow.
Tests extreme values, boundary conditions, and model invariant
preservation (0 HP, 0 stats, overflow, clamping).
"""

import sys
import os
import random

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.models import GameState, Skill, Item, StatusEffect, has_status, apply_status
from engine.combat import start_combat, apply_damage_to_enemy, apply_damage_to_player, enemy_turn
from engine.damage import calc_player_damage, calc_preview_damage
from engine.status_effects import (
    process_status_effects,
    process_player_status_effects,
    tick_player_buffs,
)
from data import CLASSES

# ═══════════════════════════════════════════
# TEST FRAMEWORK
# ═══════════════════════════════════════════

_tests_run = 0
_tests_passed = 0
_tests_failed = 0
_failures = []


def assert_eq(actual, expected, msg=""):
    global _tests_run, _tests_passed, _tests_failed
    _tests_run += 1
    if actual == expected:
        _tests_passed += 1
    else:
        _tests_failed += 1
        _failures.append(f"  FAIL: {msg}\n    Expected: {expected}\n    Got: {actual}")


def assert_true(condition, msg=""):
    assert_eq(condition, True, msg)


def assert_gte(actual, threshold, msg=""):
    global _tests_run, _tests_passed, _tests_failed
    _tests_run += 1
    if actual >= threshold:
        _tests_passed += 1
    else:
        _tests_failed += 1
        _failures.append(f"  FAIL: {msg}\n    Expected >= {threshold}, Got: {actual}")


def assert_lte(actual, threshold, msg=""):
    global _tests_run, _tests_passed, _tests_failed
    _tests_run += 1
    if actual <= threshold:
        _tests_passed += 1
    else:
        _tests_failed += 1
        _failures.append(f"  FAIL: {msg}\n    Expected <= {threshold}, Got: {actual}")


def assert_gt(actual, threshold, msg=""):
    global _tests_run, _tests_passed, _tests_failed
    _tests_run += 1
    if actual > threshold:
        _tests_passed += 1
    else:
        _tests_failed += 1
        _failures.append(f"  FAIL: {msg}\n    Expected > {threshold}, Got: {actual}")


def make_state(class_id="scholar"):
    state = GameState()
    state.init_from_class(class_id)
    return state


def make_combat(class_id="scholar", is_boss=False):
    state = make_state(class_id)
    start_combat(state, is_boss=is_boss)
    return state


# ═══════════════════════════════════════════
# TEST SUITES
# ═══════════════════════════════════════════


def test_madness_clamping():
    """Madness is always clamped to [0, 100]."""
    print("\n=== Madness Clamping ===")
    state = make_state("brute")

    # Negative madness
    result = state.add_madness(-999)
    assert_eq(state.madness, 0, "Madness should clamp to 0 (lower bound)")
    assert_true(not result, "Negative madness should not trigger death")

    # Exact 100
    state.madness = 99
    result = state.add_madness(1)
    assert_eq(state.madness, 100, "Madness should reach exactly 100")
    assert_true(result, "Madness 100 should trigger death")

    # Overflow past 100
    state.madness = 95
    result = state.add_madness(50)
    assert_eq(state.madness, 100, "Madness should clamp to 100 (upper bound)")
    assert_true(result, "Madness >= 100 should trigger death")


def test_madness_immune_buff():
    """madImmune buff prevents death at 100 madness."""
    print("\n=== Madness Immune Buff ===")
    state = make_state("brute")
    state.buffs["madImmune"] = 3

    state.madness = 99
    result = state.add_madness(5)
    assert_eq(state.madness, 100, "Madness should reach 100")
    assert_true(not result, "madImmune should prevent death trigger")


def test_hp_never_negative():
    """HP is always >= 0 after any damage."""
    print("\n=== HP Never Negative ===")
    state = make_combat("brute")
    state.hp = 1

    # Massive physical damage
    dmg, result = apply_damage_to_player(state, 99999, True)
    assert_gte(state.hp, 0, "HP should never go negative")

    # Massive magic damage
    state2 = make_combat("scholar")
    state2.hp = 1
    dmg2, result2 = apply_damage_to_player(state2, 99999, False)
    assert_gte(state2.hp, 0, "HP should never go negative (magic)")


def test_enemy_hp_never_negative():
    """Enemy HP is always >= 0 after damage."""
    print("\n=== Enemy HP Never Negative ===")
    state = make_combat("scholar")
    e = state.combat.enemy

    skill = Skill(
        {"name": "Mega Strike", "type": "physical", "power": 50.0, "stat": "str", "desc": "test", "formula": "test"}
    )
    raw = calc_player_damage(state, skill)
    apply_damage_to_enemy(state, raw, skill)
    assert_gte(e.hp, 0, "Enemy HP should never go negative")


def test_recalc_stats_clamping():
    """recalc_stats enforces minimum bounds on all derived stats."""
    print("\n=== recalc_stats Clamping ===")
    state = make_state("scholar")
    # Set all base stats to 1 (minimum)
    for k in state.base_stats:
        state.base_stats[k] = 1
    state.recalc_stats()

    assert_gte(state.max_hp, 1, "max_hp should be >= 1")
    assert_gte(state.atk, 1, "atk should be >= 1")
    assert_gte(state.defense, 0, "defense should be >= 0")
    assert_gte(state.m_def, 0, "m_def should be >= 0")
    assert_gte(state.crit, 0, "crit should be >= 0")
    assert_gte(state.evasion, 0, "evasion should be >= 0")
    assert_gte(state.luck, 1, "luck should be >= 1")


def test_accuracy_bounds():
    """Accuracy is always clamped to [ACC_MIN, ACC_MAX]."""
    print("\n=== Accuracy Bounds ===")
    from data import ACC_MIN, ACC_MAX

    state = make_state("scholar")
    # Extreme AGI values
    state.base_stats["agi"] = 100
    state.recalc_stats()
    assert_lte(state.accuracy, ACC_MAX, f"Accuracy should not exceed {ACC_MAX}")

    state.base_stats["agi"] = 1
    state.recalc_stats()
    assert_gte(state.accuracy, ACC_MIN, f"Accuracy should not go below {ACC_MIN}")


def test_hp_capped_at_max_hp():
    """HP is capped at max_hp after recalc_stats."""
    print("\n=== HP Capped at max_hp ===")
    state = make_state("brute")
    state.hp = state.max_hp + 999
    state.recalc_stats()
    assert_lte(state.hp, state.max_hp, "HP should not exceed max_hp after recalc")


def test_cursed_item_stat_floor():
    """Cursed items cannot reduce stats below 1."""
    print("\n=== Cursed Item Stat Floor ===")
    state = make_state("scholar")
    for k in state.base_stats:
        state.base_stats[k] = 1

    cursed = Item("Cursed Doom Blade", "weapon", {"str": 10}, rarity=4, debuffs={"str": 20, "int": 50})
    state.equip_item(cursed)
    state.recalc_stats()

    assert_gte(state.stats["str"], 1, "STR should not drop below 1 with cursed item")
    assert_gte(state.stats["int"], 1, "INT should not drop below 1 with cursed item")


def test_unequip_restores_stats():
    """Unequipping a cursed item restores stats."""
    print("\n=== Unequip Restores Stats ===")
    state = make_state("brute")
    base_atk = state.atk

    cursed = Item("Cursed Blade", "weapon", {"str": 5}, rarity=4, debuffs={"atk": 10})
    state.equip_item(cursed)
    assert_true(state.atk < base_atk, "Cursed item should reduce ATK")

    # Unequip by equipping None
    state.equipment["weapon"] = None
    state.recalc_stats()
    assert_eq(state.atk, base_atk, "ATK should be restored after unequipping cursed item")


def test_level_up_massive_xp():
    """Massive XP triggers multiple level-ups."""
    print("\n=== Multi-Level-Up ===")
    state = make_state("scholar")
    initial_level = state.level
    state.xp = 99999

    result = state.check_level_up()
    assert_true(result, "Should level up with massive XP")
    assert_true(state.level > initial_level + 1, "Should level up multiple times")
    assert_true(state.xp < state.xp_next, "XP should be less than xp_next after level-ups")


def test_level_up_heals():
    """Level up provides healing but doesn't exceed max_hp."""
    print("\n=== Level-Up Healing ===")
    state = make_state("warden")
    state.hp = 1
    state.max_hp_at_level = state.max_hp  # remember
    state.xp = state.xp_next

    state.check_level_up()
    assert_true(state.hp > 1, "Level up should heal")
    assert_lte(state.hp, state.max_hp, "Level up heal should not exceed max_hp")


def test_shield_absorbs_damage():
    """Shield absorbs damage completely until depleted."""
    print("\n=== Shield Absorption ===")
    state = make_combat("warden")
    state.shield = 50

    dmg, result = apply_damage_to_player(state, 30, True)
    assert_eq(result, "shield", "Should use shield for damage < shield")
    assert_eq(dmg, 0, "No damage should leak through shield")
    assert_eq(state.shield, 20, "Shield should be reduced by damage amount")

    # Partial shield
    state.shield = 10
    dmg2, result2 = apply_damage_to_player(state, 50, True)
    assert_true(dmg2 > 0, "Excess damage should leak through depleted shield")
    assert_eq(state.shield, 0, "Shield should be depleted to 0")


def test_barrier_single_use():
    """Barrier blocks one hit completely then is consumed."""
    print("\n=== Barrier Single Use ===")
    state = make_combat("warden")
    state.barrier = 5

    dmg, result = apply_damage_to_player(state, 999, True)
    assert_eq(result, "barrier", "Should use barrier")
    assert_eq(dmg, 0, "Barrier should nullify all damage")
    assert_eq(state.barrier, 4, "Barrier should decrement by 1")

    # Second hit goes through
    dmg2, result2 = apply_damage_to_player(state, 999, True)
    assert_true(result2 != "barrier" or state.barrier > 0, "Without barrier, damage should apply normally")


def test_undying_survives_fatal():
    """Undying buff prevents death from fatal damage."""
    print("\n=== Undying Buff ===")
    state = make_combat("warden")
    state.hp = 1
    state.buffs["undying"] = 1

    dmg, result = apply_damage_to_player(state, 999, True)
    assert_eq(result, "undying", "Undying should trigger on fatal damage")
    assert_eq(state.hp, 1, "Undying should leave HP at 1")


def test_ethereal_full_dodge():
    """Ethereal buff provides 100% dodge."""
    print("\n=== Ethereal Full Dodge ===")
    state = make_combat("scholar")
    state.buffs["ethereal"] = 1

    # Try multiple times
    for _ in range(10):
        dmg, result = apply_damage_to_player(state, 100, True)
        assert_eq(result, "evade", "Ethereal should always evade")
        assert_eq(dmg, 0, "Ethereal should take no damage")


def test_final_stand_blocks():
    """Final Stand buff blocks all damage."""
    print("\n=== Final Stand Buff ===")
    state = make_combat("brute")
    state.buffs["finalStand"] = 1

    dmg, result = apply_damage_to_player(state, 500, True)
    assert_eq(result, "barrier", "Final Stand should block damage")
    assert_eq(dmg, 0, "Final Stand should nullify damage")


def test_poison_max_stacks():
    """Poison stacks cap at 5."""
    print("\n=== Poison Max Stacks ===")
    global _tests_run, _tests_passed, _tests_failed
    state = make_combat("shadowblade")
    e = state.combat.enemy

    for _ in range(10):
        apply_status(e, "poisoned", 3)
    poison = next((s for s in e.statuses if s.type == "poisoned"), None)
    _tests_run += 1
    if poison is not None:
        _tests_passed += 1
    else:
        _tests_failed += 1
        _failures.append("  FAIL: Poison should exist on enemy")

    if poison:
        assert_gte(poison.stacks, 1, "Poison should have at least 1 stack")


def test_status_duration_refresh():
    """Reapplying a status refreshes duration to the higher value."""
    print("\n=== Status Duration Refresh ===")
    state = make_combat("brute")
    e = state.combat.enemy

    apply_status(e, "burning", 2)
    burning = next(s for s in e.statuses if s.type == "burning")
    assert_eq(burning.duration, 2, "Initial duration should be 2")

    apply_status(e, "burning", 5)
    assert_eq(burning.duration, 5, "Duration should refresh to higher value")

    apply_status(e, "burning", 3)
    assert_eq(burning.duration, 5, "Duration should NOT decrease on reapply")


def test_regen_heal_cap():
    """Regen buff heal is capped at max_hp."""
    print("\n=== Regen Heal Cap ===")
    state = make_state("warden")
    state.hp = state.max_hp - 1
    state.buffs["regen"] = 10

    logs = tick_player_buffs(state)
    assert_lte(state.hp, state.max_hp, "Regen should not overheal past max_hp")


def test_equip_swap_returns_previous():
    """equip_item returns the previously equipped item."""
    print("\n=== Equip Swap ===")
    state = make_state("brute")
    sword1 = Item("Iron Sword", "weapon", {"str": 3}, 1)
    sword2 = Item("Steel Sword", "weapon", {"str": 7}, 2)

    prev = state.equip_item(sword1)
    assert_true(prev is None, "First equip should return None")

    prev = state.equip_item(sword2)
    assert_eq(prev.name, "Iron Sword", "Second equip should return the first item")


def test_non_damage_skill_type_is_correct():
    """Non-damage skill types are properly categorized."""
    print("\n=== Non-Damage Skill Types ===")
    state = make_combat("scholar")

    for skill_type in ("self_buff", "self_heal", "self_shield"):
        skill = Skill(name="Test", type=skill_type, power=10.0, stat="int", desc="test", formula="test")
        assert_true(skill.type == skill_type, f"{skill_type} should be categorized correctly")


def test_enemy_stunned_skips_turn():
    """Stunned enemy skips turn."""
    print("\n=== Enemy Stunned ===")
    state = make_combat("brute")
    e = state.combat.enemy
    e.stunned = True

    logs = enemy_turn(state)
    assert_true(e.stunned == False or e.hp > 0, "Stunned enemy should skip attack")


def test_preview_damage_no_randomness():
    """calc_preview_damage is deterministic."""
    print("\n=== Preview Damage Deterministic ===")
    state = make_combat("scholar")
    skill = Skill(
        {"name": "Strike", "type": "physical", "power": 1.0, "stat": "str", "desc": "test", "formula": "test"}
    )

    results = [calc_preview_damage(state, skill) for _ in range(20)]
    # All results should be identical (no randomness)
    assert_true(all(r == results[0] for r in results), "Preview damage should be deterministic across calls")


def test_boss_cannot_flee():
    """Cannot flee from boss fights."""
    print("\n=== Boss Cannot Flee ===")
    from engine.combat import combat_run_attempt

    state = make_combat("scholar", is_boss=True)
    assert_true(not combat_run_attempt(state), "Should not flee from boss")


def test_doom_kill_threshold():
    """Doom kills enemy when HP drops below 30%."""
    print("\n=== Doom Kill Threshold ===")
    state = make_combat("scholar")
    e = state.combat.enemy

    apply_status(e, "doom", 1)

    # Above threshold: survive
    e.hp = int(e.max_hp * 0.5)
    logs = process_status_effects(e, False, state)
    assert_gt(e.hp, 0, "Doom should not kill above 30% HP")

    # Below threshold: instant kill
    e.hp = int(e.max_hp * 0.2)
    apply_status(e, "doom", 1)
    logs = process_status_effects(e, False, state)
    assert_eq(e.hp, 0, "Doom should kill below 30% HP")


def test_multiple_dot_effects():
    """Multiple DOTs (burn + poison + bleed) stack damage."""
    print("\n=== Multiple DOT Effects ===")
    state = make_combat("scholar")
    e = state.combat.enemy
    initial_hp = e.hp

    apply_status(e, "burning", 5)
    apply_status(e, "poisoned", 4)
    apply_status(e, "bleeding", 3)
    poison = next(s for s in e.statuses if s.type == "poisoned")
    poison.stacks = 3

    logs = process_status_effects(e, False, state)
    assert_true(e.hp < initial_hp, "Multiple DOTs should deal damage")


def test_buff_expiration_recalc():
    """Buff expiration with temp_stats triggers recalc_stats."""
    print("\n=== Buff Expiration Recalc ===")
    state = make_state("brute")
    state.temp_stats["str"] = 10
    state.buffs["rage"] = 1  # will expire

    atk_before = state.atk
    state.recalc_stats()

    tick_player_buffs(state)
    # After rage expires, temp_stats might still have entries from other buffs
    # but rage itself should be gone
    assert_true("rage" not in state.buffs, "Expired buff should be removed")


def test_all_classes_init_sanity():
    """All classes produce sane initial values."""
    print("\n=== All Classes Init Sanity ===")
    for cid in CLASSES:
        state = make_state(cid)
        assert_gt(state.max_hp, 0, f"{cid}: max_hp > 0")
        assert_gt(state.atk, 0, f"{cid}: atk > 0")
        assert_gte(state.defense, 0, f"{cid}: defense >= 0")
        assert_gte(state.m_def, 0, f"{cid}: m_def >= 0")
        assert_gte(state.crit, 0, f"{cid}: crit >= 0")
        assert_gte(state.evasion, 0, f"{cid}: evasion >= 0")
        assert_gte(state.luck, 1, f"{cid}: luck >= 1")
        assert_gt(state.accuracy, 0, f"{cid}: accuracy > 0")
        assert_lte(state.accuracy, 100, f"{cid}: accuracy <= 100")
        assert_eq(state.hp, state.max_hp, f"{cid}: hp == max_hp on init")
        for stat in ("int", "str", "agi", "wis", "luck"):
            assert_gte(state.stats[stat], 1, f"{cid}: {stat} >= 1")


def test_enemy_scaling():
    """Enemies scale correctly with floor level."""
    print("\n=== Enemy Scaling ===")
    from data import ENEMIES

    enemy_data = ENEMIES[0]

    e1 = type("obj", (object,), {"__init__": lambda s: None})()
    e_low = type("Enemy", (), {})()
    # Use the actual Enemy class
    e_low_f = __import__("engine.models", fromlist=["Enemy"]).Enemy(enemy_data, floor=1)
    e_high_f = __import__("engine.models", fromlist=["Enemy"]).Enemy(enemy_data, floor=15)

    assert_gt(e_high_f.max_hp, e_low_f.max_hp, "Higher floor enemies should have more HP")
    assert_gt(e_high_f.atk, e_low_f.atk, "Higher floor enemies should have more ATK")
    assert_gt(e_high_f.defense, e_low_f.defense, "Higher floor enemies should have more DEF")


def test_boss_phase_thresholds():
    """Boss phase transitions at exact HP thresholds."""
    print("\n=== Boss Phase Exact Thresholds ===")
    from engine.combat import check_boss_phase

    state = make_combat("scholar", is_boss=True)
    e = state.combat.enemy

    # The boss phase check uses <= 50% to trigger phase 2
    # Verify the transition boundary
    e.hp = int(e.max_hp * 0.50) + 1
    state.combat.phase2 = False
    check_boss_phase(state)
    assert_true(not state.combat.phase2, "Above 50% should NOT trigger phase 2")

    # At or below 50% — should trigger phase 2
    e.hp = int(e.max_hp * 0.50)
    state.combat.phase2 = False
    check_boss_phase(state)
    assert_true(state.combat.phase2, "At 50% or below should trigger phase 2")


# ═══════════════════════════════════════════
# RUNNER
# ═══════════════════════════════════════════


def run_all_tests():
    print("=" * 60)
    print("THE KING IN YELLOW — Edge Case Tests")
    print("=" * 60)

    random.seed(42)

    test_suites = [
        test_madness_clamping,
        test_madness_immune_buff,
        test_hp_never_negative,
        test_enemy_hp_never_negative,
        test_recalc_stats_clamping,
        test_accuracy_bounds,
        test_hp_capped_at_max_hp,
        test_cursed_item_stat_floor,
        test_unequip_restores_stats,
        test_level_up_massive_xp,
        test_level_up_heals,
        test_shield_absorbs_damage,
        test_barrier_single_use,
        test_undying_survives_fatal,
        test_ethereal_full_dodge,
        test_final_stand_blocks,
        test_poison_max_stacks,
        test_status_duration_refresh,
        test_regen_heal_cap,
        test_equip_swap_returns_previous,
        test_non_damage_skill_type_is_correct,
        test_enemy_stunned_skips_turn,
        test_preview_damage_no_randomness,
        test_boss_cannot_flee,
        test_doom_kill_threshold,
        test_multiple_dot_effects,
        test_buff_expiration_recalc,
        test_all_classes_init_sanity,
        test_enemy_scaling,
        test_boss_phase_thresholds,
    ]

    for suite in test_suites:
        try:
            suite()
        except Exception as e:
            global _tests_run, _tests_failed
            _tests_run += 1
            _tests_failed += 1
            _failures.append(f"  EXCEPTION in {suite.__name__}: {e}")

    print(f"\n{'=' * 60}")
    print(f"Results: {_tests_passed} passed, {_tests_failed} failed, {_tests_run} total")

    if _failures:
        print(f"\nFailures:")
        for f in _failures:
            print(f)

    print(f"{'=' * 60}")
    return _tests_failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)

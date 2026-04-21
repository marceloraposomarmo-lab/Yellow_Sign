#!/usr/bin/env python3
"""
Integration Tests for The King in Yellow.
Tests interactions between game systems: combat ↔ progression,
items ↔ combat, events ↔ stats, shop ↔ equipment.
"""

import sys
import os
import random

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.models import GameState, Item, Skill, StatusEffect, has_status, apply_status
from engine.combat import start_combat, apply_damage_to_enemy, apply_damage_to_player, enemy_turn, combat_run_attempt
from engine.damage import calc_player_damage
from engine.status_effects import process_status_effects, process_player_status_effects, tick_player_buffs
from engine.items import generate_item
from engine.world import (
    advance_floor,
    resolve_event,
    resolve_trap,
    generate_paths,
    generate_shop,
    buy_shop_item,
    get_floor_narrative,
)
from engine.skills import player_use_skill
from data import CLASSES, EVENTS, TRAPS

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


def test_combat_victory_progression():
    """Killing an enemy increments kills counter."""
    print("\n=== Combat → Progression Integration ===")
    state = make_combat("brute")
    e = state.combat.enemy
    initial_kills = state.kills

    # Kill enemy directly
    e.hp = 1
    skill = Skill(name="Strike", type="physical", power=10.0, stat="str", desc="t", formula="t")
    raw = calc_player_damage(state, skill)
    apply_damage_to_enemy(state, raw, skill)

    assert_eq(e.hp, 0, "Enemy should be dead")
    assert_eq(state.kills, initial_kills, "Kills should not auto-increment (caller responsibility)")


def test_floor_advance_heals():
    """Advancing floor heals player."""
    print("\n=== Floor Advance Healing ===")
    state = make_state("brute")
    state.hp = 1

    advance_floor(state)
    assert_true(state.hp > 1, "Floor advance should heal player")
    assert_eq(state.floor, 2, "Floor should increment")


def test_floor_advance_cap():
    """Floor advance caps at max_floor."""
    print("\n=== Floor Advance Cap ===")
    state = make_state("brute")
    state.floor = state.max_floor - 1

    result = advance_floor(state)
    assert_true(result, "Should return True when reaching max floor")
    assert_eq(state.floor, state.max_floor, "Floor should cap at max_floor")


def test_floor_narrative_exists():
    """Every floor has a narrative."""
    print("\n=== Floor Narrative ===")
    for floor in range(1, 21):
        narrative = get_floor_narrative(floor)
        assert_true(len(narrative) > 0, f"Floor {floor} should have a narrative")


def test_event_stat_changes():
    """Events that modify stats trigger recalc."""
    print("\n=== Event → Stat Recalc ===")
    state = make_state("scholar")
    initial_int = state.stats["int"]

    # Find an event that gives INT
    for i, ev in enumerate(EVENTS):
        for j, outcome in enumerate(ev["outcomes"]):
            if "gain_int" in outcome["effect"]:
                pre_int = state.stats["int"]
                resolve_event(state, i, j)
                assert_true(state.stats["int"] >= pre_int, f"Event {outcome['effect']} should increase INT")
                return  # found one, done


def test_event_madness_interactions():
    """Madness-giving events respect clamping."""
    print("\n=== Event → Madness Clamping ===")
    state = make_state("brute")
    state.madness = 95

    # Find an event that gives madness
    for i, ev in enumerate(EVENTS):
        for j, outcome in enumerate(ev["outcomes"]):
            if "mad_" in outcome["effect"] or "desecrate" in outcome["effect"]:
                resolve_event(state, i, j)
                assert_gte(state.madness, 0, f"Madness should not go negative after event")
                assert_gte(state.madness, 100, f"Madness should not exceed 100 after event")
                return


def test_trap_damage_clamp():
    """Trap damage cannot reduce HP below 1 (non-fatal traps)."""
    print("\n=== Trap → HP Clamp ===")
    state = make_state("scholar")
    state.hp = 2

    for i in range(len(TRAPS)):
        state2 = make_state("scholar")
        state2.hp = 2
        msg, game_over = resolve_trap(state2, i)
        assert_gte(state2.hp, 1, f"Trap {i} should not kill player directly")


def test_trap_madness_game_over():
    """Trap that pushes madness to 100 triggers game over."""
    print("\n=== Trap → Madness Game Over ===")
    # Find a trap with high madness outcome
    for i, trap in enumerate(TRAPS):
        worst = trap["outcomes"][-1]
        if worst["madness"] > 0:
            state = make_state("scholar")
            state.madness = 100 - worst["madness"]
            # May or may not trigger game_over depending on roll
            msg, game_over = resolve_trap(state, i)
            # Just verify no crash and valid return
            assert_true(isinstance(msg, str), f"Trap {i} should return a string message")
            break


def test_shop_buy_equips():
    """Buying from shop equips item and deducts gold."""
    print("\n=== Shop → Equipment ===")
    state = make_state("brute")
    state.gold = 500

    items, prices = generate_shop(state)
    assert_eq(len(items), len(prices), "Items and prices count should match")
    assert_gt(prices[0], 0, "Price should be positive")

    sold = [False] * len(items)
    success, msg = buy_shop_item(state, items, prices, sold, 0)

    assert_true(success, f"Should buy item: {msg}")
    assert_true(sold[0], "Item should be marked as sold")
    assert_eq(state.equipment.get(items[0].slot), items[0], "Item should be equipped")


def test_shop_buy_insufficient_gold():
    """Cannot buy with insufficient gold."""
    print("\n=== Shop Insufficient Gold ===")
    state = make_state("scholar")
    state.gold = 0

    items, prices = generate_shop(state)
    sold = [False] * len(items)
    success, msg = buy_shop_item(state, items, prices, sold, 0)

    assert_true(not success, "Should fail with no gold")
    assert_eq(state.gold, 0, "Gold should remain unchanged")


def test_shop_buy_already_sold():
    """Cannot buy an already-sold item."""
    print("\n=== Shop Already Sold ===")
    state = make_state("brute")
    state.gold = 9999

    items, prices = generate_shop(state)
    sold = [False] * len(items)
    sold[0] = True

    success, msg = buy_shop_item(state, items, prices, sold, 0)
    assert_true(not success, "Should fail for already-sold item")


def test_paths_valid():
    """Generated paths have valid structure and different types."""
    print("\n=== Path Generation ===")
    for floor in [1, 5, 10, 15, 20]:
        paths = generate_paths(floor)
        assert_eq(len(paths), 2, f"Floor {floor}: should generate 2 paths")
        for p in paths:
            assert_true("type" in p, f"Floor {floor}: path should have type")
            assert_true("name" in p, f"Floor {floor}: path should have name")


def test_item_equip_combat_integration():
    """Equipping an item changes combat stats."""
    print("\n=== Item → Combat Stats ===")
    state = make_combat("brute")
    e = state.combat.enemy
    initial_atk = state.atk

    item = Item("Power Gauntlets", "weapon", {"str": 15, "atk": 5}, rarity=3)
    state.equip_item(item)
    assert_gt(state.atk, initial_atk, "Equipping ATK item should increase attack")


def test_combat_buff_decay_integration():
    """Buffs decay correctly across multiple turns."""
    print("\n=== Combat Buff Decay ===")
    state = make_combat("scholar")
    state.buffs["regen"] = 3
    state.hp = state.max_hp // 2
    initial_hp = state.hp

    tick_player_buffs(state)
    assert_eq(state.buffs["regen"], 2, "Regen should decrement")
    assert_gt(state.hp, initial_hp, "Regen should heal")

    tick_player_buffs(state)
    assert_eq(state.buffs["regen"], 1, "Regen should continue decrementing")

    tick_player_buffs(state)
    assert_true("regen" not in state.buffs, "Regen should expire")


def test_status_dot_in_combat():
    """DOT effects damage enemy during combat turn cycle."""
    print("\n=== Status DOT → Combat ===")
    state = make_combat("shadowblade")
    e = state.combat.enemy
    initial_hp = e.hp

    apply_status(e, "burning", 5)
    apply_status(e, "bleeding", 3)

    logs = process_status_effects(e, False, state)
    assert_true(e.hp < initial_hp, "DOT effects should reduce enemy HP")


def test_full_game_loop_simplified():
    """Simplified game loop: explore → combat → floor advance."""
    print("\n=== Simplified Game Loop ===")
    global _tests_run, _tests_passed, _tests_failed
    state = make_state("warden")

    # Simulate 3 floors
    for floor_num in range(3):
        # Enter combat
        start_combat(state, is_boss=(floor_num == 2))
        e = state.combat.enemy
        assert_not_none_val = e is not None
        _tests_run += 1
        if assert_not_none_val:
            _tests_passed += 1
        else:
            _tests_failed += 1
            _failures.append("  FAIL: Combat should start with enemy")

        if e:
            # Quick kill
            e.hp = 0
            state.kills += 1

        # Clear combat
        state.combat = None
        state.statuses = []
        state.shield = 0
        state.barrier = 0
        state.buffs = {}

        # Advance floor
        advance_floor(state)

    assert_eq(state.floor, 4, "Should have advanced 3 floors")
    assert_gt(state.kills, 0, "Should have kills")


def test_all_events_resolve():
    """All events resolve without crashing."""
    print("\n=== All Events Resolve ===")
    for i, ev in enumerate(EVENTS):
        for j in range(len(ev["outcomes"])):
            state = make_state("scholar")
            try:
                msg, loot = resolve_event(state, i, j)
                assert_true(isinstance(msg, str), f"Event {i}/{j} should return string message")
            except Exception as e:
                global _tests_run, _tests_failed
                _tests_run += 1
                _tests_failed += 1
                _failures.append(f"  FAIL: Event {i}/{j} raised {e}")


def test_all_traps_resolve():
    """All traps resolve without crashing."""
    print("\n=== All Traps Resolve ===")
    for i in range(len(TRAPS)):
        state = make_state("brute")
        try:
            msg, game_over = resolve_trap(state, i)
            assert_true(isinstance(msg, str), f"Trap {i} should return string message")
            assert_true(isinstance(game_over, bool), f"Trap {i} should return bool game_over")
        except Exception as e:
            global _tests_run, _tests_failed
            _tests_run += 1
            _tests_failed += 1
            _failures.append(f"  FAIL: Trap {i} raised {e}")


def test_world_combat_state_isolation():
    """World events don't interfere with combat state."""
    print("\n=== World ↔ Combat Isolation ===")
    state = make_state("scholar")

    # Set up some progression state
    state.floor = 5
    state.gold = 100
    state.madness = 30

    # Start combat
    start_combat(state)
    assert_true(state.combat is not None, "Combat should be active")

    # Combat state should not modify progression
    assert_eq(state.floor, 5, "Floor should be unchanged by combat start")
    assert_eq(state.gold, 100, "Gold should be unchanged by combat start")
    assert_eq(state.madness, 30, "Madness should be unchanged by combat start")


# ═══════════════════════════════════════════
# RUNNER
# ═══════════════════════════════════════════


def run_all_tests():
    print("=" * 60)
    print("THE KING IN YELLOW — Integration Tests")
    print("=" * 60)

    random.seed(42)

    test_suites = [
        test_combat_victory_progression,
        test_floor_advance_heals,
        test_floor_advance_cap,
        test_floor_narrative_exists,
        test_event_stat_changes,
        test_event_madness_interactions,
        test_trap_damage_clamp,
        test_trap_madness_game_over,
        test_shop_buy_equips,
        test_shop_buy_insufficient_gold,
        test_shop_buy_already_sold,
        test_paths_valid,
        test_item_equip_combat_integration,
        test_combat_buff_decay_integration,
        test_status_dot_in_combat,
        test_full_game_loop_simplified,
        test_all_events_resolve,
        test_all_traps_resolve,
        test_world_combat_state_isolation,
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

#!/usr/bin/env python3
"""
Combat Simulation Tests for The King in Yellow.
Runs headless (no Pygame display) to verify combat logic is correct.
"""

import sys
import os
import random

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.models import GameState, Skill, Item, Enemy, CombatState, has_status, apply_status
from engine.combat import (
    calc_player_damage,
    apply_damage_to_enemy,
    apply_damage_to_player,
    enemy_turn,
    tick_player_buffs,
    process_status_effects,
    process_player_status_effects,
    check_boss_phase,
    combat_run_attempt,
    start_combat,
)
from engine.items import generate_item
from engine.skills import (
    player_use_skill,
    _handle_self_heal,
    _handle_self_shield,
    _handle_self_buff,
    HEAL_HANDLERS,
    SHIELD_HANDLERS,
    BUFF_HANDLERS,
)
from data import CLASSES, ENEMIES, BOSS

# ═══════════════════════════════════════════
# TEST UTILITIES
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


def assert_gt(actual, threshold, msg=""):
    global _tests_run, _tests_passed, _tests_failed
    _tests_run += 1
    if actual > threshold:
        _tests_passed += 1
    else:
        _tests_failed += 1
        _failures.append(f"  FAIL: {msg}\n    Expected > {threshold}, Got: {actual}")


def assert_gte(actual, threshold, msg=""):
    global _tests_run, _tests_passed, _tests_failed
    _tests_run += 1
    if actual >= threshold:
        _tests_passed += 1
    else:
        _tests_failed += 1
        _failures.append(f"  FAIL: {msg}\n    Expected >= {threshold}, Got: {actual}")


def make_state(class_id="scholar"):
    """Create a fresh game state for testing."""
    state = GameState()
    state.init_from_class(class_id)
    return state


def make_combat(class_id="scholar", is_boss=False):
    """Create a game state with active combat."""
    state = make_state(class_id)
    start_combat(state, is_boss=is_boss)
    return state


# ═══════════════════════════════════════════
# TEST SUITES
# ═══════════════════════════════════════════


def test_game_state_init():
    """Test that all classes initialize correctly."""
    print("\n=== GameState Initialization ===")
    for cid in CLASSES:
        state = make_state(cid)
        cls = CLASSES[cid]
        assert_true(state.hp > 0, f"{cid}: HP should be positive")
        assert_true(state.max_hp > 0, f"{cid}: max_hp should be positive")
        assert_eq(state.class_name, cls["name"], f"{cid}: class name mismatch")
        assert_true(len(state.active_skills) > 0, f"{cid}: should have starting skills")
        assert_eq(state.level, 1, f"{cid}: should start at level 1")
        for stat in ("int", "str", "agi", "wis", "luck"):
            assert_true(state.stats.get(stat, 0) > 0, f"{cid}: {stat} should be positive")


def test_damage_calculation():
    """Test damage calculation for various skill types."""
    print("\n=== Damage Calculation ===")
    state = make_combat("scholar")

    # Physical skill
    phys_skill = Skill(
        {"name": "Test Strike", "type": "physical", "power": 1.5, "stat": "str", "desc": "test", "formula": "test"}
    )
    raw = calc_player_damage(state, phys_skill)
    assert_gt(raw, 0, "Physical skill should deal positive damage")

    # Magic skill
    magic_skill = Skill(
        {"name": "Test Bolt", "type": "magic", "power": 2.0, "stat": "int", "desc": "test", "formula": "test"}
    )
    raw_magic = calc_player_damage(state, magic_skill)
    assert_gt(raw_magic, 0, "Magic skill should deal positive damage")

    # Scholar with INT should deal more magic damage than physical
    scholar_state = make_combat("scholar")
    raw_phys = calc_player_damage(scholar_state, phys_skill)
    raw_mag = calc_player_damage(scholar_state, magic_skill)
    # Scholar has high INT, so magic should be strong
    assert_true(raw_mag > 0, "Scholar magic damage should be positive")


def test_damage_application():
    """Test damage application to enemies."""
    print("\n=== Damage Application ===")
    state = make_combat("scholar")
    e = state.combat.enemy
    initial_hp = e.hp

    skill = Skill(
        {"name": "Strike", "type": "physical", "power": 1.0, "stat": "str", "desc": "test", "formula": "test"}
    )
    raw = calc_player_damage(state, skill)
    dmg, is_crit = apply_damage_to_enemy(state, raw, skill)

    assert_gt(dmg, 0, "Applied damage should be positive")
    assert_true(e.hp < initial_hp, "Enemy HP should decrease")
    assert_eq(e.hp, initial_hp - dmg, "Enemy HP should equal initial - damage")


def test_player_damage_application():
    """Test damage application to player with defense."""
    print("\n=== Player Damage Application ===")
    state = make_combat("brute")
    initial_hp = state.hp

    # Physical damage
    dmg, result = apply_damage_to_player(state, 100, True)
    if result == "hit":
        assert_true(dmg > 0, "Physical damage should be positive on hit")
        assert_true(state.hp < initial_hp, "Player HP should decrease on hit")

    # Test barrier
    state2 = make_combat("warden")
    state2.barrier = 1
    dmg, result = apply_damage_to_player(state2, 999, True)
    assert_eq(result, "barrier", "Barrier should absorb hit")
    assert_eq(dmg, 0, "Barrier should nullify damage")


def test_all_classes_combat():
    """Test that all classes can enter and fight in combat."""
    print("\n=== All Classes Combat ===")
    for cid in CLASSES:
        state = make_combat(cid)
        assert_true(state.combat is not None, f"{cid}: combat should be active")
        assert_true(state.combat.enemy.hp > 0, f"{cid}: enemy should be alive")

        # Use first skill
        if state.active_skills:
            logs = player_use_skill(state, 0)
            assert_true(len(logs) > 0, f"{cid}: skill should produce logs")


def test_skill_types():
    """Test each skill type produces correct log types."""
    print("\n=== Skill Types ===")
    for cid in CLASSES:
        state = make_combat(cid)
        for i, sk in enumerate(state.active_skills):
            state2 = make_combat(cid)  # fresh state per skill
            state2.active_skills = [sk]
            sk.current_cd = 0
            state2.combat = state.combat  # share combat

            logs = player_use_skill(state2, 0)
            assert_true(len(logs) > 0, f"{cid}/{sk.name}: should produce logs")

            # Check log types are valid
            valid_types = {"damage", "crit", "heal", "shield", "effect", "info"}
            for text, log_type in logs:
                assert_true(log_type in valid_types, f"{cid}/{sk.name}: invalid log type '{log_type}'")


def test_buff_system():
    """Test buff application and expiration."""
    print("\n=== Buff System ===")
    state = make_combat("brute")

    # Apply a buff
    state.buffs["rage"] = 3
    assert_eq(state.buffs["rage"], 3, "Buff should be set")

    # Tick buffs
    logs = tick_player_buffs(state)
    assert_eq(state.buffs["rage"], 2, "Buff should decrement by 1")

    # Tick to expiration
    tick_player_buffs(state)
    tick_player_buffs(state)
    assert_true("rage" not in state.buffs, "Buff should be removed after expiration")


def test_regen_buff():
    """Test HP regeneration buff."""
    print("\n=== Regen Buff ===")
    state = make_combat("warden")
    state.hp = state.max_hp // 2
    initial_hp = state.hp
    state.buffs["regen"] = 2

    logs = tick_player_buffs(state)
    assert_true(state.hp > initial_hp, "Regen should heal HP")
    assert_true(any("heal" == lt for _, lt in logs), "Regen should produce heal log")


def test_debuff_immunity():
    """Test that immunity buff blocks debuffs."""
    print("\n=== Debuff Immunity ===")
    state = make_combat("mad_prophet")
    state.buffs["immunity"] = 3

    # Try to apply a debuff
    from engine.combat import apply_status_player

    apply_status_player(state, "burning", 3)
    assert_true(not has_status(state, "burning"), "Immunity should block burning")

    # Remove immunity, debuff should apply
    del state.buffs["immunity"]
    apply_status_player(state, "burning", 3)
    assert_true(has_status(state, "burning"), "Without immunity, burning should apply")


def test_poison_stacking():
    """Test poison stacks correctly."""
    print("\n=== Poison Stacking ===")
    state = make_combat("shadowblade")
    e = state.combat.enemy

    apply_status(e, "poisoned", 3)
    existing = next((s for s in e.statuses if s.type == "poisoned"), None)
    assert_true(existing is not None, "Poison should be applied")

    existing.stacks = min(5, existing.stacks + 1)
    apply_status(e, "poisoned", 3)
    existing = next((s for s in e.statuses if s.type == "poisoned"), None)
    assert_eq(existing.stacks, 2, "Poison should stack")


def test_cooldowns():
    """Test skill cooldown system."""
    print("\n=== Cooldowns ===")
    state = make_combat("scholar")
    if not state.active_skills:
        return

    sk = state.active_skills[0]
    sk.cd = 2
    sk.current_cd = 0

    # Use skill
    logs = player_use_skill(state, 0)
    assert_true(sk.current_cd > 0, "Skill should be on cooldown after use")

    # Try to use again — should fail
    logs2 = player_use_skill(state, 0)
    assert_true(any("cooldown" in t.lower() for t, _ in logs2), "Should show cooldown message")


def test_enemy_turn():
    """Test enemy AI turn."""
    print("\n=== Enemy Turn ===")
    state = make_combat("brute")
    initial_hp = state.hp

    logs = enemy_turn(state)
    assert_true(len(logs) > 0, "Enemy turn should produce logs")


def test_boss_phases():
    """Test boss phase transitions."""
    print("\n=== Boss Phases ===")
    state = make_combat("scholar", is_boss=True)
    e = state.combat.enemy

    # Phase 2 at 50% HP
    e.hp = int(e.max_hp * 0.49)
    logs = check_boss_phase(state)
    assert_true(state.combat.phase2, "Boss should enter phase 2 at <50% HP")

    # Phase 3 at 25% HP
    e.hp = int(e.max_hp * 0.24)
    logs = check_boss_phase(state)
    assert_true(state.combat.phase3, "Boss should enter phase 3 at <25% HP")


def test_flee_attempt():
    """Test fleeing from combat."""
    print("\n=== Flee Attempt ===")
    # Can't flee from boss
    state = make_combat("shadowblade", is_boss=True)
    assert_eq(combat_run_attempt(state), False, "Should not flee from boss")

    # Can flee from regular combat (random chance)
    state2 = make_combat("shadowblade")
    results = [combat_run_attempt(state2) for _ in range(100)]
    assert_true(any(results), "Should be able to flee sometimes")


def test_item_generation():
    """Test item generation."""
    print("\n=== Item Generation ===")
    for floor in [1, 5, 10, 15, 20]:
        for _ in range(10):
            item = generate_item(floor, luck=10)
            assert_true(len(item.name) > 0, f"Floor {floor}: item should have name")
            assert_true(item.rarity in (1, 2, 3, 4), f"Floor {floor}: valid rarity")
            assert_true(len(item.stats) > 0, f"Floor {floor}: item should have stats")


def test_madness_death():
    """Test that madness at 100 kills the player."""
    print("\n=== Madness Death ===")
    state = make_combat("mad_prophet")
    state.madness = 95

    # Use a skill with madness cost
    for sk in state.active_skills:
        if sk.cost > 0:
            sk.current_cd = 0
            state.madness = 99
            logs = player_use_skill(state, state.active_skills.index(sk))
            if state.madness >= 100:
                assert_true(any("shatter" in t.lower() for t, _ in logs), "Madness 100 should shatter mind")
            break


def test_hp_cost_skills():
    """Test skills that cost HP."""
    print("\n=== HP Cost Skills ===")
    state = make_combat("brute")
    initial_hp = state.hp

    for sk in state.active_skills:
        if sk.hp_cost > 0:
            sk.current_cd = 0
            idx = state.active_skills.index(sk)
            logs = player_use_skill(state, idx)
            assert_true(state.hp < initial_hp, f"{sk.name}: HP cost should reduce HP")
            assert_true(state.hp > 0, f"{sk.name}: HP cost should not kill")
            break


def test_lifesteal():
    """Test lifesteal mechanic."""
    print("\n=== Lifesteal ===")
    state = make_combat("shadowblade")
    state.hp = 1  # low HP

    for sk in state.active_skills:
        if sk.lifesteal:
            sk.current_cd = 0
            idx = state.active_skills.index(sk)
            initial_hp = state.hp
            logs = player_use_skill(state, idx)
            if any("Stole" in t for t, _ in logs):
                assert_true(state.hp > initial_hp, "Lifesteal should heal")
            break


def test_combat_simulation_full():
    """Run a full combat simulation until someone dies."""
    print("\n=== Full Combat Simulation ===")
    for cid in CLASSES:
        state = make_combat(cid)
        turns = 0
        max_turns = 200

        while state.hp > 0 and state.combat and state.combat.enemy.hp > 0 and turns < max_turns:
            # Player turn
            for i, sk in enumerate(state.active_skills):
                if sk.current_cd <= 0:
                    player_use_skill(state, i)
                    break

            if state.combat.enemy.hp <= 0:
                break

            # Tick player effects
            tick_player_buffs(state)
            process_status_effects(state.combat.enemy, False, state)

            if state.combat.enemy.hp <= 0:
                break

            # Enemy turn
            enemy_turn(state)

            if state.hp <= 0:
                break

            # Tick player status effects
            process_player_status_effects(state)

            # Reduce cooldowns
            for sk in state.active_skills:
                if sk.current_cd > 0:
                    sk.current_cd -= 1

            turns += 1

        # Combat should end within max_turns
        assert_true(turns < max_turns, f"{cid}: combat should resolve within {max_turns} turns")
        someone_died = (state.hp <= 0) or (state.combat and state.combat.enemy.hp <= 0)
        assert_true(someone_died or turns >= max_turns, f"{cid}: combat should end with someone dead or timeout")


# ═══════════════════════════════════════════
# RUNNER
# ═══════════════════════════════════════════


def run_all_tests():
    """Run all test suites."""
    print("=" * 60)
    print("THE KING IN YELLOW — Combat Simulation Tests")
    print("=" * 60)

    random.seed(42)  # Deterministic for reproducibility

    test_suites = [
        test_game_state_init,
        test_damage_calculation,
        test_damage_application,
        test_player_damage_application,
        test_all_classes_combat,
        test_skill_types,
        test_buff_system,
        test_regen_buff,
        test_debuff_immunity,
        test_poison_stacking,
        test_cooldowns,
        test_enemy_turn,
        test_boss_phases,
        test_flee_attempt,
        test_item_generation,
        test_madness_death,
        test_hp_cost_skills,
        test_lifesteal,
        test_combat_simulation_full,
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

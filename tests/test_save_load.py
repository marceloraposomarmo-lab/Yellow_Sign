#!/usr/bin/env python3
"""
Save/Load Integrity Tests for The King in Yellow.
Tests round-trip serialization, corruption handling, version mismatches,
and edge cases in the JSON save system.
"""

import sys
import os
import json
import random
import tempfile
import shutil

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.models import GameState, Item, Skill, StatusEffect
from engine.items import generate_item

# ═══════════════════════════════════════════
# TEST FRAMEWORK (consistent with test_combat.py)
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


def assert_none(value, msg=""):
    global _tests_run, _tests_passed, _tests_failed
    _tests_run += 1
    if value is None:
        _tests_passed += 1
    else:
        _tests_failed += 1
        _failures.append(f"  FAIL: {msg}\n    Expected None, Got: {value}")


def assert_not_none(value, msg=""):
    global _tests_run, _tests_passed, _tests_failed
    _tests_run += 1
    if value is not None:
        _tests_passed += 1
    else:
        _tests_failed += 1
        _failures.append(f"  FAIL: {msg}\n    Expected not None, Got: None")


def make_state(class_id="scholar"):
    state = GameState()
    state.init_from_class(class_id)
    return state


# ═══════════════════════════════════════════
# Save/Load with temp directory to avoid
# polluting the real saves folder
# ═══════════════════════════════════════════

import save_system

_original_save_dir = save_system.SAVE_DIR
_tmp_dir = None


def setup_save_dir():
    global _tmp_dir
    _tmp_dir = tempfile.mkdtemp(prefix="yellow_sign_test_")
    save_system.SAVE_DIR = _tmp_dir
    save_system.ensure_save_dir()


def teardown_save_dir():
    global _tmp_dir
    save_system.SAVE_DIR = _original_save_dir
    if _tmp_dir and os.path.isdir(_tmp_dir):
        shutil.rmtree(_tmp_dir, ignore_errors=True)
        _tmp_dir = None


# ═══════════════════════════════════════════
# TEST SUITES
# ═══════════════════════════════════════════


def test_round_trip_basic():
    """Save and load a basic game state, verify all fields match."""
    print("\n=== Save/Load Round-Trip (Basic) ===")
    setup_save_dir()
    try:
        state = make_state("warden")
        state.hp = 42
        state.floor = 7
        state.gold = 133
        state.madness = 37
        state.kills = 5
        state.shield = 20
        state.barrier = 1

        filepath = save_system.save_game(state, slot=0)
        assert_true(os.path.exists(filepath), "Save file should exist on disk")

        loaded = save_system.load_game(slot=0)
        assert_not_none(loaded, "Loaded state should not be None")
        assert_eq(loaded.class_id, "warden", "Class ID should match")
        assert_eq(loaded.class_name, state.class_name, "Class name should match")
        assert_eq(loaded.level, state.level, "Level should match")
        assert_eq(loaded.floor, 7, "Floor should match")
        assert_eq(loaded.hp, 42, "HP should match")
        assert_eq(loaded.max_hp, state.max_hp, "Max HP should match")
        assert_eq(loaded.gold, 133, "Gold should match")
        assert_eq(loaded.madness, 37, "Madness should match")
        assert_eq(loaded.kills, 5, "Kills should match")
        assert_eq(loaded.shield, 20, "Shield should match")
        assert_eq(loaded.barrier, 1, "Barrier should match")
        assert_eq(loaded.accuracy, state.accuracy, "Accuracy should match")
        assert_eq(loaded.crit, state.crit, "Crit should match")
        assert_eq(loaded.evasion, state.evasion, "Evasion should match")
        assert_eq(loaded.defense, state.defense, "Defense should match")
        assert_eq(loaded.m_def, state.m_def, "MDEF should match")
        assert_eq(loaded.atk, state.atk, "ATK should match")
        assert_eq(loaded.stats, state.stats, "Stats dict should match")
        assert_eq(loaded.base_stats, state.base_stats, "Base stats should match")
    finally:
        teardown_save_dir()


def test_round_trip_equipment():
    """Save/load preserves equipped items."""
    print("\n=== Save/Load Round-Trip (Equipment) ===")
    setup_save_dir()
    try:
        random.seed(99)
        state = make_state("brute")
        item = generate_item(floor=10, luck=10)
        prev = state.equip_item(item)
        assert_not_none(item, "Generated item should not be None")

        save_system.save_game(state, slot=1)
        loaded = save_system.load_game(slot=1)

        for slot in ("weapon", "armor", "accessory", "boots", "ringL", "ringR"):
            orig = state.equipment.get(slot)
            load_e = loaded.equipment.get(slot)
            if orig is None:
                assert_true(load_e is None, f"Slot {slot}: should be None")
            else:
                assert_not_none(load_e, f"Slot {slot}: should not be None")
                assert_eq(load_e.name, orig.name, f"Slot {slot}: item name should match")
                assert_eq(load_e.slot, orig.slot, f"Slot {slot}: slot type should match")
                assert_eq(load_e.rarity, orig.rarity, f"Slot {slot}: rarity should match")
                assert_eq(load_e.stats, orig.stats, f"Slot {slot}: stats should match")
                assert_eq(load_e.debuffs, orig.debuffs, f"Slot {slot}: debuffs should match")
    finally:
        teardown_save_dir()


def test_round_trip_inventory():
    """Save/load preserves inventory items."""
    print("\n=== Save/Load Round-Trip (Inventory) ===")
    setup_save_dir()
    try:
        random.seed(77)
        state = make_state("scholar")
        for _ in range(5):
            state.inventory.append(generate_item(floor=8, luck=5))

        save_system.save_game(state, slot=2)
        loaded = save_system.load_game(slot=2)

        assert_eq(len(loaded.inventory), 5, "Inventory count should match")
        for i, (orig, load_i) in enumerate(zip(state.inventory, loaded.inventory)):
            assert_eq(load_i.name, orig.name, f"Item {i}: name should match")
            assert_eq(load_i.rarity, orig.rarity, f"Item {i}: rarity should match")
            assert_eq(load_i.stats, orig.stats, f"Item {i}: stats should match")
    finally:
        teardown_save_dir()


def test_round_trip_skills():
    """Save/load preserves active skills and all skills."""
    print("\n=== Save/Load Round-Trip (Skills) ===")
    setup_save_dir()
    try:
        state = make_state("mad_prophet")

        save_system.save_game(state, slot=0)
        loaded = save_system.load_game(slot=0)

        assert_eq(len(loaded.active_skills), len(state.active_skills), "Active skill count should match")
        assert_eq(len(loaded.all_skills), len(state.all_skills), "All skill count should match")
        for i, (orig, load_sk) in enumerate(zip(state.active_skills, loaded.active_skills)):
            assert_eq(load_sk.name, orig.name, f"Active skill {i}: name should match")
            assert_eq(load_sk.type, orig.type, f"Active skill {i}: type should match")
            assert_eq(load_sk.power, orig.power, f"Active skill {i}: power should match")
    finally:
        teardown_save_dir()


def test_round_trip_statuses_and_buffs():
    """Save/load preserves status effects and buffs."""
    print("\n=== Save/Load Round-Trip (Statuses & Buffs) ===")
    setup_save_dir()
    try:
        state = make_state("shadowblade")
        state.statuses = [StatusEffect("burning", 3), StatusEffect("poisoned", 5)]
        state.statuses[1].stacks = 3
        state.buffs = {"regen": 4, "immunity": 2}

        save_system.save_game(state, slot=0)
        loaded = save_system.load_game(slot=0)

        assert_eq(len(loaded.statuses), 2, "Status count should match")
        assert_eq(loaded.statuses[0].type, "burning", "First status type should match")
        assert_eq(loaded.statuses[0].duration, 3, "First status duration should match")
        assert_eq(loaded.statuses[1].type, "poisoned", "Second status type should match")
        assert_eq(loaded.statuses[1].stacks, 3, "Poison stacks should match")
        assert_eq(loaded.buffs.get("regen"), 4, "Regen buff should match")
        assert_eq(loaded.buffs.get("immunity"), 2, "Immunity buff should match")
    finally:
        teardown_save_dir()


def test_round_trip_pending_levelup():
    """Save/load preserves pending level-up skills."""
    print("\n=== Save/Load Round-Trip (Pending Level-Up) ===")
    setup_save_dir()
    try:
        state = make_state("warden")
        state.xp = state.xp_next + 50  # trigger level up
        state.check_level_up()

        save_system.save_game(state, slot=0)
        loaded = save_system.load_game(slot=0)

        assert_eq(len(loaded.pending_levelup_skills), len(state.pending_levelup_skills),
                  "Pending level-up skill count should match")
        for i, (orig, load_sk) in enumerate(zip(state.pending_levelup_skills, loaded.pending_levelup_skills)):
            assert_eq(load_sk.name, orig.name, f"Pending skill {i}: name should match")
    finally:
        teardown_save_dir()


def test_version_mismatch():
    """Loading a save with wrong version returns None."""
    print("\n=== Version Mismatch ===")
    setup_save_dir()
    try:
        state = make_state("scholar")
        filepath = save_system.save_game(state, slot=0)

        # Tamper with version
        with open(filepath, "r") as f:
            data = json.load(f)
        data["version"] = 1  # wrong version
        with open(filepath, "w") as f:
            json.dump(data, f)

        loaded = save_system.load_game(slot=0)
        assert_none(loaded, "Wrong version should return None")

        # Version 999 (future version)
        data["version"] = 999
        with open(filepath, "w") as f:
            json.dump(data, f)
        loaded = save_system.load_game(slot=0)
        assert_none(loaded, "Future version should return None")
    finally:
        teardown_save_dir()


def test_corrupted_json():
    """Loading corrupted JSON returns None."""
    print("\n=== Corrupted JSON ===")
    setup_save_dir()
    try:
        save_system.ensure_save_dir()
        filepath = os.path.join(save_system.SAVE_DIR, "save_0.json")
        with open(filepath, "w") as f:
            f.write("{corrupted json garbage !!!")

        loaded = save_system.load_game(slot=0)
        assert_none(loaded, "Corrupted JSON should return None")
    finally:
        teardown_save_dir()


def test_missing_slot():
    """Loading a non-existent slot returns None."""
    print("\n=== Missing Slot ===")
    setup_save_dir()
    try:
        loaded = save_system.load_game(slot=3)
        assert_none(loaded, "Non-existent slot should return None")

        loaded = save_system.load_game(slot=99)
        assert_none(loaded, "Out-of-range slot should return None")
    finally:
        teardown_save_dir()


def test_empty_file():
    """Loading an empty file returns None."""
    print("\n=== Empty File ===")
    setup_save_dir()
    try:
        save_system.ensure_save_dir()
        filepath = os.path.join(save_system.SAVE_DIR, "save_0.json")
        with open(filepath, "w") as f:
            f.write("")

        loaded = save_system.load_game(slot=0)
        assert_none(loaded, "Empty file should return None")
    finally:
        teardown_save_dir()


def test_delete_save():
    """Test delete_save functionality."""
    print("\n=== Delete Save ===")
    setup_save_dir()
    try:
        state = make_state("brute")
        save_system.save_game(state, slot=0)

        # Delete existing save
        result = save_system.delete_save(slot=0)
        assert_true(result, "Deleting existing save should return True")
        assert_true(not os.path.exists(os.path.join(save_system.SAVE_DIR, "save_0.json")),
                    "Save file should be deleted")

        # Delete non-existent save
        result = save_system.delete_save(slot=0)
        assert_true(not result, "Deleting non-existent save should return False")
    finally:
        teardown_save_dir()


def test_list_saves():
    """Test list_saves with various states."""
    print("\n=== List Saves ===")
    setup_save_dir()
    try:
        # Empty directory
        saves = save_system.list_saves()
        assert_eq(len(saves), 5, "Should always return 5 slots")
        assert_true(saves[0].get("empty"), "Empty slot should have 'empty' key")

        # Save in slot 0
        state = make_state("scholar")
        save_system.save_game(state, slot=0)
        saves = save_system.list_saves()
        assert_true(len(saves[0]["class_name"]) > 0, "Slot 0 class name should be non-empty")
        assert_eq(saves[0]["level"], 1, "Slot 0 level should match")

        # Corrupted slot
        save_system.ensure_save_dir()
        bad_path = os.path.join(save_system.SAVE_DIR, "save_2.json")
        with open(bad_path, "w") as f:
            f.write("NOT JSON")
        saves = save_system.list_saves()
        assert_true(saves[2].get("error"), "Corrupted slot should have 'error' key")
    finally:
        teardown_save_dir()


def test_multiple_save_slots():
    """Test saving to and loading from multiple independent slots."""
    print("\n=== Multiple Save Slots ===")
    setup_save_dir()
    try:
        s1 = make_state("brute")
        s1.floor = 3
        s1.gold = 100
        save_system.save_game(s1, slot=0)

        s2 = make_state("scholar")
        s2.floor = 10
        s2.gold = 500
        save_system.save_game(s2, slot=1)

        l1 = save_system.load_game(slot=0)
        l2 = save_system.load_game(slot=1)

        assert_eq(l1.class_id, "brute", "Slot 0 should load brute")
        assert_eq(l1.floor, 3, "Slot 0 floor should be 3")
        assert_eq(l1.gold, 100, "Slot 0 gold should be 100")

        assert_eq(l2.class_id, "scholar", "Slot 1 should load scholar")
        assert_eq(l2.floor, 10, "Slot 1 floor should be 10")
        assert_eq(l2.gold, 500, "Slot 1 gold should be 500")
    finally:
        teardown_save_dir()


def test_save_overwrite():
    """Saving to the same slot overwrites the previous save."""
    print("\n=== Save Overwrite ===")
    setup_save_dir()
    try:
        s1 = make_state("brute")
        s1.floor = 1
        save_system.save_game(s1, slot=0)

        s2 = make_state("scholar")
        s2.floor = 15
        save_system.save_game(s2, slot=0)

        loaded = save_system.load_game(slot=0)
        assert_eq(loaded.class_id, "scholar", "Overwritten slot should have new class")
        assert_eq(loaded.floor, 15, "Overwritten slot should have new floor")
    finally:
        teardown_save_dir()


def test_save_all_classes():
    """All classes can be saved and loaded."""
    print("\n=== Save All Classes ===")
    setup_save_dir()
    try:
        from data import CLASSES
        for cid in CLASSES:
            state = make_state(cid)
            save_system.save_game(state, slot=0)
            loaded = save_system.load_game(slot=0)
            assert_not_none(loaded, f"{cid}: loaded state should not be None")
            assert_eq(loaded.class_id, cid, f"{cid}: class ID should match")
            assert_eq(loaded.class_name, CLASSES[cid]["name"], f"{cid}: class name should match")
    finally:
        teardown_save_dir()


# ═══════════════════════════════════════════
# RUNNER
# ═══════════════════════════════════════════

def run_all_tests():
    print("=" * 60)
    print("THE KING IN YELLOW — Save/Load Integrity Tests")
    print("=" * 60)

    random.seed(42)

    test_suites = [
        test_round_trip_basic,
        test_round_trip_equipment,
        test_round_trip_inventory,
        test_round_trip_skills,
        test_round_trip_statuses_and_buffs,
        test_round_trip_pending_levelup,
        test_version_mismatch,
        test_corrupted_json,
        test_missing_slot,
        test_empty_file,
        test_delete_save,
        test_list_saves,
        test_multiple_save_slots,
        test_save_overwrite,
        test_save_all_classes,
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

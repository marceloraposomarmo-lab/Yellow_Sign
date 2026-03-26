"""
THE KING IN YELLOW — Save System
Simple JSON-based save/load.
"""

import json
import os
from game_engine import GameState, Skill, Item, StatusEffect


SAVE_DIR = os.path.join(os.path.dirname(__file__), "saves")


def ensure_save_dir():
    os.makedirs(SAVE_DIR, exist_ok=True)


def save_game(state, slot=0):
    """Save game state to JSON file."""
    ensure_save_dir()
    data = {
        "class_id": state.class_id,
        "class_name": state.class_name,
        "level": state.level,
        "floor": state.floor,
        "max_floor": state.max_floor,
        "hp": state.hp,
        "max_hp": state.max_hp,
        "shield": state.shield,
        "barrier": state.barrier,
        "stats": state.stats,
        "base_stats": state.base_stats,
        "atk": state.atk,
        "defense": state.defense,
        "m_def": state.m_def,
        "crit": state.crit,
        "evasion": state.evasion,
        "luck": state.luck,
        "accuracy": state.accuracy,
        "madness": state.madness,
        "gold": state.gold,
        "xp": state.xp,
        "xp_next": state.xp_next,
        "kills": state.kills,
        "rooms_explored": state.rooms_explored,
        "equipment": {
            k: (v.to_dict() if v else None)
            for k, v in state.equipment.items()
        },
        "inventory": [item.to_dict() for item in state.inventory],
        "active_skills": [sk.to_dict() for sk in state.active_skills],
        "all_skills": [sk.to_dict() for sk in state.all_skills],
        "statuses": [se.to_dict() for se in state.statuses],
        "buffs": state.buffs,
        "hits_taken": state.hits_taken,
        "pending_levelup_skills": [sk.to_dict() for sk in state.pending_levelup_skills],
    }
    filepath = os.path.join(SAVE_DIR, f"save_{slot}.json")
    with open(filepath, "w") as f:
        json.dump(data, f, indent=2)
    return filepath


def load_game(slot=0):
    """Load game state from JSON file. Returns GameState or None."""
    filepath = os.path.join(SAVE_DIR, f"save_{slot}.json")
    if not os.path.exists(filepath):
        return None
    try:
        with open(filepath, "r") as f:
            data = json.load(f)
    except (json.JSONDecodeError, IOError):
        return None

    state = GameState()
    state.class_id = data["class_id"]
    state.class_name = data["class_name"]
    state.level = data["level"]
    state.floor = data["floor"]
    state.max_floor = data["max_floor"]
    state.hp = data["hp"]
    state.max_hp = data["max_hp"]
    state.shield = data.get("shield", 0)
    state.barrier = data.get("barrier", 0)
    state.stats = data["stats"]
    state.base_stats = data["base_stats"]
    state.atk = data["atk"]
    state.defense = data["defense"]
    state.m_def = data["m_def"]
    state.crit = data["crit"]
    state.evasion = data["evasion"]
    state.luck = data["luck"]
    state.accuracy = data["accuracy"]
    state.madness = data["madness"]
    state.gold = data["gold"]
    state.xp = data["xp"]
    state.xp_next = data["xp_next"]
    state.kills = data["kills"]
    state.rooms_explored = data["rooms_explored"]
    state.equipment = {
        k: (Item.from_dict(v) if v else None)
        for k, v in data["equipment"].items()
    }
    state.inventory = [Item.from_dict(d) for d in data["inventory"]]
    state.active_skills = [Skill.from_dict(d) for d in data["active_skills"]]
    state.all_skills = [Skill.from_dict(d) for d in data["all_skills"]]
    state.statuses = [StatusEffect.from_dict(d) for d in data.get("statuses", [])]
    state.buffs = data.get("buffs", {})
    state.hits_taken = data.get("hits_taken", 0)
    state.pending_levelup_skills = [Skill.from_dict(d) for d in data.get("pending_levelup_skills", [])]
    return state


def list_saves():
    """List available save files with metadata."""
    ensure_save_dir()
    saves = []
    for i in range(5):  # 5 save slots
        filepath = os.path.join(SAVE_DIR, f"save_{i}.json")
        if os.path.exists(filepath):
            try:
                with open(filepath, "r") as f:
                    data = json.load(f)
                saves.append({
                    "slot": i,
                    "class_name": data.get("class_name", "Unknown"),
                    "level": data.get("level", 1),
                    "floor": data.get("floor", 1),
                    "kills": data.get("kills", 0),
                })
            except (json.JSONDecodeError, IOError, KeyError):
                saves.append({"slot": i, "error": True})
        else:
            saves.append({"slot": i, "empty": True})
    return saves


def delete_save(slot=0):
    """Delete a save file."""
    filepath = os.path.join(SAVE_DIR, f"save_{slot}.json")
    if os.path.exists(filepath):
        os.remove(filepath)
        return True
    return False

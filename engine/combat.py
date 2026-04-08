"""Combat system: orchestrates damage, status effects, and enemy AI."""

import random
from typing import List, Tuple, Dict, Any, Optional

from data import (
    ENEMIES, BOSS,
    ENEMY_VAR_LOW, ENEMY_VAR_RANGE,
    FLEE_BASE_CHANCE, FLEE_AGI_MULTIPLIER, FLEE_SUCCESS_MADNESS, FLEE_FAIL_MADNESS,
    FREEZING_PHYS_MULT, PETRIFIED_MAGIC_MULT, WEAKENED_ATK_MULT,
    SHOCK_STUN_CHANCE, BLIND_MISS_CHANCE,
    BOSS_PHASE2_HP, BOSS_PHASE3_HP, BOSS_PHASE3_ATK_MULT,
    XP_BASE, XP_PER_FLOOR, XP_BOSS_BONUS,
    GOLD_BASE, GOLD_PER_FLOOR, GOLD_BOSS_BONUS, GOLD_BASE_RANDOM_MAX,
    MADNESS_BOSS_KILL, MADNESS_NORMAL_KILL,
)
from engine.models import Enemy, CombatState, GameState, has_status
from engine.damage import (
    calc_player_damage, calc_preview_damage,
    apply_damage_to_enemy, apply_damage_to_player,
)
from engine.status_effects import (
    apply_status_effect_on_player, apply_status_player,
    process_status_effects, process_player_status_effects,
    tick_player_buffs,
)


# Re-export for backward compatibility (engine/__init__.py, tests, and skills.py import from here)
from engine.damage import _base_damage, _get_buff_defense_bonus, _get_buff_evasion_bonus
from engine.damage import calc_player_damage, calc_preview_damage, apply_damage_to_enemy, apply_damage_to_player
from engine.status_effects import tick_player_buffs, process_status_effects, process_player_status_effects
from engine.status_effects import apply_status_player, apply_status_effect_on_player


# ═══════════════════════════════════════════
# COMBAT LIFECYCLE
# ═══════════════════════════════════════════

def start_combat(state: GameState, is_boss: bool = False) -> None:
    """Initialize a combat encounter."""
    if is_boss or state.floor >= state.max_floor:
        ed = dict(BOSS)
    else:
        pool = [e for e in ENEMIES if e["level_range"][0] <= state.floor <= e["level_range"][1]]
        ed = dict(random.choice(pool)) if pool else dict(ENEMIES[0])

    enemy = Enemy(ed, state.floor)
    state.combat = CombatState(enemy, is_boss)
    state.shield = 0
    state.barrier = 0
    state.rage = False
    state.buffs = {}
    state.temp_stats = {}
    state.hits_taken = 0
    for sk in state.active_skills:
        sk.current_cd = 0
    state.combat.add_log(f"{enemy.name} appears!", "info")
    if enemy.desc:
        state.combat.add_log(enemy.desc, "info")


def _get_enemy_intent_message(skill: Dict[str, Any]) -> str:
    """Generate a descriptive intent message for the enemy's next action."""
    stype = skill.get("type", "physical")
    sname = skill.get("name", "attack")

    if stype == "self_heal":
        return f"{sname} — the enemy channels restorative energy!"
    elif "debuff" in stype:
        return f"{sname} — the enemy prepares a dark technique!"
    elif stype == "magic":
        return f"{sname} — eldritch energy crackles in the air!"
    elif stype == "physical":
        return f"{sname} — the enemy braces for a strike!"
    else:
        return f"{sname} — the enemy readies itself!"


# ═══════════════════════════════════════════
# ENEMY AI
# ═══════════════════════════════════════════

def enemy_turn(state: GameState) -> List[Tuple[str, str]]:
    """Execute enemy turn. Returns list of (text, type) log messages."""
    logs: List[Tuple[str, str]] = []
    c = state.combat
    e = c.enemy

    if e.stunned:
        e.stunned = False
        logs.append((f"{e.name} is stunned!", "effect"))
        return logs

    shocked = next((s for s in e.statuses if s.type == "shocked"), None)
    if shocked and random.random() < SHOCK_STUN_CHANCE:
        e.stunned = True
        logs.append((f"{e.name} stunned by shock!", "effect"))
        return logs

    if has_status(e, "blinded") and random.random() < BLIND_MISS_CHANCE:
        logs.append((f"{e.name} misses!", "info"))
        return logs

    if c.next_enemy_skill:
        skill = c.next_enemy_skill
        c.next_enemy_skill = None
    else:
        skill = random.choice(e.skills)
    stype = skill.get("type", "physical")
    spower = skill.get("power", 1.0)

    if stype in ("physical", "magic"):
        dmg = int(e.atk * spower * (ENEMY_VAR_LOW + random.random() * ENEMY_VAR_RANGE))
        if stype == "physical" and has_status(e, "freezing"):
            dmg = int(dmg * FREEZING_PHYS_MULT)
        if stype == "magic" and has_status(e, "petrified"):
            dmg = int(dmg * PETRIFIED_MAGIC_MULT)
        if has_status(e, "weakened"):
            dmg = int(dmg * WEAKENED_ATK_MULT)
        is_phys = stype == "physical"
        actual, result = apply_damage_to_player(state, dmg, is_phys)
        if actual > 0:
            logs.append((f"{e.name} uses {skill['name']} for {actual} damage!", "damage"))
        elif result == "evade":
            logs.append((f"You evade {e.name}'s attack!", "info"))
        elif result == "barrier":
            logs.append((f"Barrier absorbs {e.name}'s hit!", "shield"))
        elif result == "undying":
            logs.append(("Undying Fury keeps you alive!", "heal"))

    elif stype in ("physical_debuff", "magic_debuff"):
        dmg = int(e.atk * spower * (ENEMY_VAR_LOW + random.random() * ENEMY_VAR_RANGE))
        if "physical" in stype and has_status(e, "freezing"):
            dmg = int(dmg * FREEZING_PHYS_MULT)
        if "magic" in stype and has_status(e, "petrified"):
            dmg = int(dmg * PETRIFIED_MAGIC_MULT)
        if has_status(e, "weakened"):
            dmg = int(dmg * WEAKENED_ATK_MULT)
        is_phys = "physical" in stype
        actual, result = apply_damage_to_player(state, dmg, is_phys)

        if skill.get("effect"):
            apply_status_effect_on_player(state, skill["effect"], skill.get("duration", 2))

        if actual > 0:
            eff = skill.get("effect", "")
            logs.append((f"{e.name} uses {skill['name']} for {actual} + {eff}!", "damage"))
        elif result == "evade":
            logs.append((f"You evade {e.name}'s attack!", "info"))
        else:
            logs.append((f"{e.name} uses {skill['name']} — effect applied!", "effect"))

    elif stype == "self_heal":
        h = int(e.max_hp * spower)
        e.hp = min(e.max_hp, e.hp + h)
        logs.append((f"{e.name} heals {h} HP!", "heal"))

    return logs


# ═══════════════════════════════════════════
# BOSS PHASES & FLEE
# ═══════════════════════════════════════════

def check_boss_phase(state: GameState) -> List[Tuple[str, str]]:
    """Check and apply boss phase transitions."""
    c = state.combat
    if not c or not c.is_boss:
        return []
    e = c.enemy
    if e.max_hp <= 0:
        return []
    pct = e.hp / e.max_hp
    logs: List[Tuple[str, str]] = []

    if pct <= BOSS_PHASE3_HP and not c.phase3:
        c.phase3 = True
        e.atk = int(e.atk * BOSS_PHASE3_ATK_MULT)
        e.skills.append({"name": "Desperate Fury", "type": "physical", "power": 2.5})
        logs.append(("━━ HASTUR ENTERS FINAL PHASE! ATK increased! ━━", "crit"))

    elif pct <= BOSS_PHASE2_HP and not c.phase2:
        c.phase2 = True
        e.skills.append({"name": "Reality Tear", "type": "magic_debuff", "power": 2.0, "effect": "blinded", "duration": 2})
        e.skills.append({"name": "Maddening Whisper", "type": "magic_debuff", "power": 1.0, "effect": "shocked", "duration": 2})
        logs.append(("━━ THE KING UNRAVELS REALITY! New abilities! ━━", "crit"))

    return logs


def combat_run_attempt(state: GameState) -> bool:
    """Attempt to flee combat. Returns True if successful."""
    c = state.combat
    if not c:
        return False
    if c.is_boss:
        return False
    chance = FLEE_BASE_CHANCE + state.stats["agi"] * FLEE_AGI_MULTIPLIER
    if random.random() * 100 < chance:
        state.add_madness(FLEE_SUCCESS_MADNESS)
        return True
    else:
        state.add_madness(FLEE_FAIL_MADNESS)
        return False

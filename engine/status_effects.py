"""Status effect application, processing, and buff management."""

import random
from typing import List, Tuple

from data import (
    BURNING_HP_PCT,
    POISON_HP_PCT,
    BLEEDING_HP_PCT,
    POISON_MAX_STACKS,
    DOOM_HP_THRESHOLD,
    REGEN_HP_PCT,
    REGEN5_HP_PCT,
    OATH_HP_PCT,
)
from engine.models import StatusEffect, GameState

# ═══════════════════════════════════════════
# STATUS EFFECT APPLICATION
# ═══════════════════════════════════════════


def apply_status_effect_on_player(state: GameState, effect_type: str, duration: int) -> None:
    """Apply a status effect to the player."""
    if effect_type:
        apply_status_player(state, effect_type, duration)


def apply_status_player(state: GameState, effect_type: str, duration: int) -> None:
    """Apply status to player's status list."""
    if state.buffs.get("immunity", 0) > 0:
        return
    existing = next((s for s in state.statuses if s.type == effect_type), None)
    if existing:
        existing.duration = max(existing.duration, duration)
    else:
        se = StatusEffect(effect_type, duration)
        state.statuses.append(se)
        if effect_type == "poisoned":
            se.stacks = 1
    if effect_type == "poisoned":
        existing = next((s for s in state.statuses if s.type == "poisoned"), None)
        if existing:
            existing.stacks = min(POISON_MAX_STACKS, existing.stacks + 1)


# ═══════════════════════════════════════════
# STATUS EFFECT PROCESSING
# ═══════════════════════════════════════════


def process_status_effects(target, is_player: bool, state: GameState) -> List[Tuple[str, str]]:
    """Process burning, poison, bleeding, etc. on any target. Returns list of log messages."""
    logs: List[Tuple[str, str]] = []
    to_remove: List[StatusEffect] = []
    for st in target.statuses:
        if st.type == "burning":
            d = int(target.max_hp * BURNING_HP_PCT) if hasattr(target, "max_hp") else int(state.max_hp * BURNING_HP_PCT)
            target.hp = max(0, target.hp - d)
            who = "You burn" if is_player else f"{target.name} burns"
            logs.append((f"{who} for {d}!", "damage"))
        elif st.type == "poisoned":
            stacks = getattr(st, "stacks", 1)
            d = (
                int(target.max_hp * POISON_HP_PCT * stacks)
                if hasattr(target, "max_hp")
                else int(state.max_hp * POISON_HP_PCT * stacks)
            )
            target.hp = max(0, target.hp - d)
            who = "Poison" if is_player else f"Poison on {target.name}"
            logs.append((f"{who} deals {d}! ({stacks} stacks)", "damage"))
        elif st.type == "bleeding":
            d = (
                int(target.max_hp * BLEEDING_HP_PCT)
                if hasattr(target, "max_hp")
                else int(state.max_hp * BLEEDING_HP_PCT)
            )
            target.hp = max(0, target.hp - d)
            who = "You bleed" if is_player else f"{target.name} bleeds"
            logs.append((f"{who} for {d}!", "damage"))

        st.duration -= 1
        if st.duration <= 0:
            to_remove.append(st)

    for st in to_remove:
        target.statuses.remove(st)
        if st.type == "doom" and not is_player:
            hp_pct = target.hp / target.max_hp if target.max_hp > 0 else 0
            if hp_pct < DOOM_HP_THRESHOLD:
                target.hp = 0
                logs.append((f"━━ THE YELLOW SIGN CLAIMS {target.name}! ━━", "crit"))
            else:
                logs.append((f"The Pallid Mask fades... {target.name} endures.", "info"))
        elif not is_player:
            logs.append((f"{st.type} wears off from {target.name}.", "info"))
        else:
            logs.append((f"{st.type} wears off.", "info"))
    return logs


def process_player_status_effects(state: GameState) -> List[Tuple[str, str]]:
    """Process burning/poison/bleeding on the player. Thin wrapper over process_status_effects."""
    return process_status_effects(state, is_player=True, state=state)


# ═══════════════════════════════════════════
# BUFF MANAGEMENT
# ═══════════════════════════════════════════


# Buff keys that modify temporary stats. When these buffs expire,
# the corresponding stat bonuses are removed from state.temp_stats.
STAT_BUFF_KEYS: dict = {
    "permIntWis": ["int", "wis"],
    "permAtk2": ["str"],
    "permWisStr": ["wis", "str"],
    "permAgiLuk": ["agi", "luck"],
    "permAll1": ["int", "str", "agi", "wis", "luck"],
    "thickSkull": ["str", "wis"],
    "perseverance": ["wis", "str"],
    "shadowBless": ["agi", "luck"],
    "randStat2": ["int", "str", "agi", "wis", "luck"],
    "pallidMask": ["int", "str", "agi", "wis", "luck"],
    "dreadnought": ["str"],
    "innerFire": ["wis", "luck"],
    "luckyDodge": ["luck"],
}


def tick_player_buffs(state: GameState) -> List[Tuple[str, str]]:
    """Tick player buff durations and apply regen/oath effects."""
    logs: List[Tuple[str, str]] = []
    to_remove: List[str] = []
    for key in list(state.buffs.keys()):
        state.buffs[key] -= 1
        if key == "regen" and state.buffs[key] >= 0:
            h = int(state.max_hp * REGEN_HP_PCT)
            state.hp = min(state.max_hp, state.hp + h)
            logs.append((f"Regen heals {h} HP.", "heal"))
        elif key == "regen5" and state.buffs[key] >= 0:
            h = int(state.max_hp * REGEN5_HP_PCT)
            state.hp = min(state.max_hp, state.hp + h)
            logs.append((f"Regen heals {h} HP.", "heal"))
        elif key == "fadeBlack" and state.buffs[key] >= 0:
            h = int(state.max_hp * REGEN5_HP_PCT)
            state.hp = min(state.max_hp, state.hp + h)
            logs.append((f"Fade to Black regen heals {h} HP.", "heal"))
        elif key == "oath" and state.buffs[key] >= 0:
            h = int(state.max_hp * OATH_HP_PCT)
            state.hp = min(state.max_hp, state.hp + h)
            logs.append((f"Oath heals {h} HP.", "heal"))
        if state.buffs[key] <= 0:
            to_remove.append(key)

    for key in to_remove:
        del state.buffs[key]
        if key == "rage":
            # When the rage buff expires, clear the rage flag
            state.rage = False
            logs.append(("Berserker Rage fades.", "info"))
        elif key in STAT_BUFF_KEYS:
            for sk in STAT_BUFF_KEYS[key]:
                state.temp_stats.pop(sk, None)
            state.recalc_stats()
            logs.append((f"{key} — temporary stat boost expired.", "info"))
        elif key == "permCrit10":
            logs.append(("Sixth Sense — CRIT bonus expired.", "info"))
        else:
            logs.append((f"{key} expired.", "info"))
    return logs

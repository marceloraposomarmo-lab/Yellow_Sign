"""Skill handler system: heal/shield/buff registries and player skill dispatch."""

import random
from typing import List, Tuple, Dict, Any, Optional, Callable

from data import MADNESS_MAX, POISON_MAX_STACKS, MAX_BARRIER_STACKS
from engine.models import Skill, GameState, StatusEffect, has_status, apply_status

# Type aliases
LogEntry = Tuple[str, str]
HealCalcFn = Callable[[GameState, Skill], int]
ShieldCalcFn = Callable[[GameState, Skill], Optional[int]]
BuffApplyFn = Callable[[GameState, Skill], Optional[Dict[str, Any]]]


# ═══════════════════════════════════════════
# SKILL HANDLER REGISTRIES
# ═══════════════════════════════════════════


def _calc_heal_int2_buff(state: GameState, skill: Skill) -> int:
    """Calculate healing for Forbidden Knowledge skill.

    Args:
        state: Current game state
        skill: Skill being used (unused for this calculation)

    Returns:
        Amount of HP healed

    Side Effects:
        Increases base INT by 3 and recalculates stats
    """
    h = int(state.stats["int"] * 2)
    state.base_stats["int"] += 3
    state.recalc_stats()
    return h


def _calc_heal_missing_hp(state: GameState, skill: Skill) -> int:
    """Calculate healing based on missing HP percentage.

    Args:
        state: Current game state
        skill: Skill being used (unused for this calculation)

    Returns:
        Amount of HP healed (60% of missing HP)
    """
    if state.max_hp <= 0:
        return 0
    missing = 1 - state.hp / state.max_hp
    return int(missing * state.max_hp * 0.6)


def _calc_heal_wis2_10(state: GameState, skill: Skill) -> int:
    """Calculate healing as 2x WIS + 10.

    Args:
        state: Current game state
        skill: Skill being used (unused for this calculation)

    Returns:
        Amount of HP healed
    """
    return int(state.stats["wis"] * 2) + 10


def _calc_heal_wis3_int1(state: GameState, skill: Skill) -> int:
    """Calculate healing as 3x WIS + 1.5x INT.

    Args:
        state: Current game state
        skill: Skill being used (unused for this calculation)

    Returns:
        Amount of HP healed
    """
    return int(state.stats["wis"] * 3 + state.stats["int"] * 1.5)


def _calc_heal_wis2_luck1(state: GameState, skill: Skill) -> int:
    """Calculate healing as 2.5x WIS + LUCK, adds 5 madness.

    Args:
        state: Current game state
        skill: Skill being used (unused for this calculation)

    Returns:
        Amount of HP healed

    Side Effects:
        Increases madness by 5
    """
    h = int(state.stats["wis"] * 2.5 + state.luck * 1)
    state.madness = min(MADNESS_MAX, state.madness + 5)
    return h


def _calc_heal_full_heal(state: GameState, skill: Skill) -> int:
    """Full heal that restores HP to max, adds 25 madness.

    Args:
        state: Current game state
        skill: Skill being used (unused for this calculation)

    Returns:
        0 (healing handled directly via side effect)

    Side Effects:
        Sets HP to max, increases madness by 25
    """
    state.hp = state.max_hp
    state.madness = min(MADNESS_MAX, state.madness + 25)
    return 0


def _calc_heal_int2_mend(state: GameState, skill: Skill) -> int:
    """Calculate healing as 2x INT.

    Args:
        state: Current game state
        skill: Skill being used (unused for this calculation)

    Returns:
        Amount of HP healed
    """
    return int(state.stats["int"] * 2)


def _calc_heal_devour15(state: GameState, skill: Skill) -> int:
    """Calculate healing as 15% of max HP.

    Args:
        state: Current game state
        skill: Skill being used (unused for this calculation)

    Returns:
        Amount of HP healed
    """
    return int(state.max_hp * 0.15)


def _calc_heal_titanResil(state: GameState, skill: Skill) -> int:
    """Calculate healing as 40% of max HP, cleanses all debuffs.

    Args:
        state: Current game state
        skill: Skill being used (unused for this calculation)

    Returns:
        Amount of HP healed

    Side Effects:
        Clears all status effects
    """
    state.statuses.clear()
    return int(state.max_hp * 0.40)


def _calc_heal_layOnHands(state: GameState, skill: Skill) -> int:
    """Calculate healing as 3x WIS, cleanses all debuffs.

    Args:
        state: Current game state
        skill: Skill being used (unused for this calculation)

    Returns:
        Amount of HP healed

    Side Effects:
        Clears all status effects
    """
    state.statuses.clear()
    return int(state.stats["wis"] * 3)


def _calc_heal_meditation(state: GameState, skill: Skill) -> int:
    """Calculate healing as 20% of max HP, reduces madness by 10.

    Args:
        state: Current game state
        skill: Skill being used (unused for this calculation)

    Returns:
        Amount of HP healed

    Side Effects:
        Reduces madness by 10
    """
    state.madness = max(0, state.madness - 10)
    return int(state.max_hp * 0.20)


def _calc_heal_darkRegen(state: GameState, skill: Skill) -> int:
    """Calculate healing as 30% of max HP, adds dark regen buff.

    Args:
        state: Current game state
        skill: Skill being used (unused for this calculation)

    Returns:
        Amount of HP healed

    Side Effects:
        Adds darkRegenBuff for 2 turns
    """
    state.buffs["darkRegenBuff"] = 2
    return int(state.max_hp * 0.30)


def _calc_heal_hasturEmbrace(state: GameState, skill: Skill) -> int:
    """Full heal with immunity buff, adds 20 madness.

    Args:
        state: Current game state
        skill: Skill being used (unused for this calculation)

    Returns:
        0 (healing handled directly via side effect)

    Side Effects:
        Sets HP to max, adds immunity buff for 2 turns, increases madness by 20
    """
    state.hp = state.max_hp
    state.madness = min(MADNESS_MAX, state.madness + 20)
    state.buffs["immunity"] = 2
    return 0


def _calc_heal_secondWind(state: GameState, skill: Skill) -> int:
    """Calculate healing as 20% of max HP, adds regen buff.

    Args:
        state: Current game state
        skill: Skill being used (unused for this calculation)

    Returns:
        Amount of HP healed

    Side Effects:
        Adds regen buff for 2 turns
    """
    state.buffs["regen"] = 2
    return int(state.max_hp * 0.20)


def _calc_heal_nimbleRecov(state: GameState, skill: Skill) -> int:
    """Calculate healing as 25% of max HP, adds evasion buff.

    Args:
        state: Current game state
        skill: Skill being used (unused for this calculation)

    Returns:
        Amount of HP healed

    Side Effects:
        Adds evasionUp buff for 2 turns
    """
    state.buffs["evasionUp"] = 2
    return int(state.max_hp * 0.25)


def _calc_heal_default(state: GameState, skill: Skill) -> int:
    """Default healing calculation as 2x specified stat.

    Args:
        state: Current game state
        skill: Skill containing stat to use for calculation

    Returns:
        Amount of HP healed (defaults to 20 if stat not found)
    """
    return int(state.stats.get(skill.stat, 10) * 2)


# Heal handler registry: heal_calc name → (calc_fn, message)
HEAL_HANDLERS: Dict[str, Tuple[HealCalcFn, str]] = {
    "int2_buff": (_calc_heal_int2_buff, "Forbidden Knowledge heals {h} HP! INT+3!"),
    "missing_hp": (_calc_heal_missing_hp, "Adrenaline Surge heals {h} HP!"),
    "wis2_10": (_calc_heal_wis2_10, "Purifying Touch heals {h} HP!"),
    "wis3_int1_heal": (_calc_heal_wis3_int1, "Healing Light restores {h} HP!"),
    "wis2_luck1": (_calc_heal_wis2_luck1, "Laughing heals {h} HP! (+5 MAD)"),
    "full_heal": (_calc_heal_full_heal, "Carcosa's Blessing: Full heal! (+25 MAD)"),
    "int2_mend": (_calc_heal_int2_mend, "Abyssal Mend heals {h} HP!"),
    "devour15": (_calc_heal_devour15, "Devour heals {h} HP!"),
    "titanResil": (
        _calc_heal_titanResil,
        "Titanic Resilience heals {h} HP and cleanses all debuffs!",
    ),
    "layOnHands": (_calc_heal_layOnHands, "Lay on Hands heals {h} HP and cleanses!"),
    "meditation": (_calc_heal_meditation, "Blessed Meditation heals {h} HP! -10 MAD!"),
    "darkRegen": (_calc_heal_darkRegen, "Dark Regeneration heals {h} HP! EVA+20% 2t!"),
    "hasturEmbrace": (
        _calc_heal_hasturEmbrace,
        "Hastur's Embrace: Full heal! Immune debuffs 2t! (+20 MAD)",
    ),
    "secondWind": (_calc_heal_secondWind, "Second Wind heals {h} HP! Regen 3% 2t!"),
    "nimbleRecov": (
        _calc_heal_nimbleRecov,
        "Nimble Recovery heals {h} HP! EVA+15% 2t!",
    ),
}


def _handle_self_heal(state: GameState, skill: Skill) -> List[LogEntry]:
    """Handle self_heal skill type. Returns list of log messages."""
    calc_fn, msg_template = HEAL_HANDLERS.get(
        skill.heal_calc, (_calc_heal_default, "Recovered {h} HP!")
    )
    h = calc_fn(state, skill)
    if h > 0:
        state.hp = min(state.max_hp, state.hp + h)
    msg = msg_template.format(h=h) if h > 0 else msg_template
    return [(msg, "heal")]


# ── Shield handlers ──────────────────────────


def _shield_int2_wis1(state: GameState, skill: Skill) -> int:
    """Calculate shield as 2x INT + WIS.

    Args:
        state: Current game state
        skill: Skill being used (unused for this calculation)

    Returns:
        Shield value
    """
    return int(state.stats["int"] * 2 + state.stats["wis"])


def _shield_wis3_int1(state: GameState, skill: Skill) -> int:
    """Calculate shield as 3x WIS + 1.5x INT.

    Args:
        state: Current game state
        skill: Skill being used (unused for this calculation)

    Returns:
        Shield value
    """
    return int(state.stats["wis"] * 3 + state.stats["int"] * 1.5)


def _shield_wis3_hits(state: GameState, skill: Skill) -> int:
    """Calculate shield as 3x WIS + 5x hits taken.

    Args:
        state: Current game state
        skill: Skill being used (unused for this calculation)

    Returns:
        Shield value scaling with damage taken
    """
    return int(state.stats["wis"] * 3 + state.hits_taken * 5)


def _shield_sanctuary(state: GameState, skill: Skill) -> int:
    """Sanctuary: adds 3 barrier stacks, heals 2x WIS, returns 4x WIS shield.

    Args:
        state: Current game state
        skill: Skill being used (unused for this calculation)

    Returns:
        Shield value (4x WIS)

    Side Effects:
        Adds 3 barrier stacks, heals 2x WIS HP
    """
    state.barrier = min(MAX_BARRIER_STACKS, state.barrier + 3)
    h = int(state.stats["wis"] * 2)
    state.hp = min(state.max_hp, state.hp + h)
    return int(state.stats["wis"] * 4)


def _shield_glyph_1(state: GameState, skill: Skill) -> Optional[int]:
    """Warding Glyph: adds 1 barrier stack, no direct shield value.

    Args:
        state: Current game state
        skill: Skill being used (unused for this calculation)

    Returns:
        None (barrier handles absorption)

    Side Effects:
        Adds 1 barrier stack
    """
    state.barrier = min(MAX_BARRIER_STACKS, state.barrier + 1)
    return None


def _shield_fracSan(state: GameState, skill: Skill) -> int:
    """Fractured Sanity: 3x INT shield, adds 10 madness.

    Args:
        state: Current game state
        skill: Skill being used (unused for this calculation)

    Returns:
        Shield value

    Side Effects:
        Increases madness by 10
    """
    state.madness = min(MADNESS_MAX, state.madness + 10)
    return int(state.stats["int"] * 3)


def _shield_str3_hits(state: GameState, skill: Skill) -> int:
    """Bone Armor: 3x STR + 5x hits taken shield.

    Args:
        state: Current game state
        skill: Skill being used (unused for this calculation)

    Returns:
        Shield value scaling with STR and damage taken
    """
    return int(state.stats.get("str", 10) * 3 + state.hits_taken * 5)


def _shield_madShell(state: GameState, skill: Skill) -> int:
    """Madness Shell: 2x WIS + madness shield, adds 10 madness.

    Args:
        state: Current game state
        skill: Skill being used (unused for this calculation)

    Returns:
        Shield value scaling with madness

    Side Effects:
        Increases madness by 10
    """
    state.madness = min(MADNESS_MAX, state.madness + 10)
    return int(state.stats["wis"] * 2 + state.madness)


def _shield_madBarrier(state: GameState, skill: Skill) -> int:
    """Madness Barrier: 3x WIS + 2x LUCK shield.

    Args:
        state: Current game state
        skill: Skill being used (unused for this calculation)

    Returns:
        Shield value
    """
    return int(state.stats["wis"] * 3 + state.luck * 2)


def _shield_madEndur(state: GameState, skill: Skill) -> int:
    """Madman's Endurance: 2x WIS shield, regen buff, adds 8 madness.

    Args:
        state: Current game state
        skill: Skill being used (unused for this calculation)

    Returns:
        Shield value

    Side Effects:
        Adds regen buff for 2 turns, increases madness by 8
    """
    state.madness = min(MADNESS_MAX, state.madness + 8)
    state.buffs["regen"] = 2
    return int(state.stats["wis"] * 2)


SHIELD_HANDLERS: Dict[str, Tuple[ShieldCalcFn, str]] = {
    "int2_wis1": (_shield_int2_wis1, "Psychic Shield: {v} damage absorbed!"),
    "wis3_int1": (_shield_wis3_int1, "Aegis Shield: {v} damage absorbed!"),
    "wis3_hits": (_shield_wis3_hits, "Eldritch Ward: {v} shield!"),
    "sanctuary": (_shield_sanctuary, "Sanctuary! Barrier x3, Shield {v}, Heal {h}!"),
    "glyph_1": (
        _shield_glyph_1,
        "Warding Glyph! Barrier absorbs next hit! ({v} stacks)",
    ),
    "fracSan": (_shield_fracSan, "Fractured Sanity! Shield {v}! (+10 MAD)"),
    "str3_hits": (_shield_str3_hits, "Bone Armor: {v} shield!"),
    "madShell": (_shield_madShell, "Madness Shell: {v} shield! (+10 MAD)"),
    "madBarrier": (_shield_madBarrier, "Madness Barrier: {v} shield!"),
    "madEndur": (
        _shield_madEndur,
        "Madman's Endurance! Shield {v}, regen 5%! (+8 MAD)",
    ),
}


def _handle_self_shield(state: GameState, skill: Skill) -> List[LogEntry]:
    """Handle self_shield skill type. Returns list of log messages."""
    handler, msg_template = SHIELD_HANDLERS.get(skill.shield_calc, (None, None))
    if handler is None:
        return [(f"{skill.name} activated!", "shield")]

    result = handler(state, skill)
    if result is not None:
        state.shield = result

    h = int(state.stats["wis"] * 2) if skill.shield_calc == "sanctuary" else 0
    v = state.barrier if skill.shield_calc == "glyph_1" else (result or state.shield)
    msg = msg_template.format(v=v, h=h)
    return [(msg, "shield")]


# ── Buff handlers ────────────────────────────


def _buff_barrier(state: GameState, skill: Skill) -> None:
    """Add barrier stacks.

    Args:
        state: Current game state
        skill: Skill containing barrier_stacks to add

    Side Effects:
        Adds barrier stacks up to MAX_BARRIER_STACKS
    """
    state.barrier = min(MAX_BARRIER_STACKS, state.barrier + skill.barrier_stacks)


def _buff_rage(state: GameState, skill: Skill) -> Dict[str, Any]:
    """Activate Berserker Rage: +60% damage, -12% HP.

    Args:
        state: Current game state
        skill: Skill being used (unused for this calculation)

    Returns:
        Dict with hp_loss amount

    Side Effects:
        Sets rage flag, reduces HP by 12%
    """
    state.rage = True
    hp_loss = int(state.max_hp * 0.12)
    state.hp = max(1, state.hp - hp_loss)
    return {"hp_loss": hp_loss}


def _buff_warlord(state: GameState, skill: Skill) -> Dict[str, Any]:
    """Warlord's Command: all combat buffs, -20% HP.

    Args:
        state: Current game state
        skill: Skill containing buff_duration

    Returns:
        Dict with hp_loss amount

    Side Effects:
        Sets rage, adds atkCritUp and ironSkin buffs, reduces HP by 20%
    """
    state.rage = True
    state.buffs["atkCritUp"] = skill.buff_duration
    state.buffs["ironSkin"] = skill.buff_duration
    hp_loss = int(state.max_hp * 0.20)
    state.hp = max(1, state.hp - hp_loss)
    return {"hp_loss": hp_loss}


def _buff_permIntWis(state: GameState, skill: Skill) -> None:
    """Forbidden Text: INT+6, WIS+4 for duration.

    Args:
        state: Current game state
        skill: Skill containing buff_duration

    Side Effects:
        Adds temp INT and WIS, sets permIntWis buff, recalculates stats
    """
    state.temp_stats["int"] = state.temp_stats.get("int", 0) + 6
    state.temp_stats["wis"] = state.temp_stats.get("wis", 0) + 4
    state.buffs["permIntWis"] = skill.buff_duration
    state.recalc_stats()


def _buff_permAtk2(state: GameState, skill: Skill) -> None:
    """Warpaint: STR+5 for duration.

    Args:
        state: Current game state
        skill: Skill containing buff_duration

    Side Effects:
        Adds temp STR, sets permAtk2 buff, recalculates stats
    """
    state.temp_stats["str"] = state.temp_stats.get("str", 0) + 5
    state.buffs["permAtk2"] = skill.buff_duration
    state.recalc_stats()


def _buff_permWisStr(state: GameState, skill: Skill) -> None:
    """Oath of the Warden: WIS+6, STR+4 for duration.

    Args:
        state: Current game state
        skill: Skill containing buff_duration

    Side Effects:
        Adds temp WIS and STR, sets permWisStr buff, recalculates stats
    """
    state.temp_stats["wis"] = state.temp_stats.get("wis", 0) + 6
    state.temp_stats["str"] = state.temp_stats.get("str", 0) + 4
    state.buffs["permWisStr"] = skill.buff_duration
    state.recalc_stats()


def _buff_permAgiLuk(state: GameState, skill: Skill) -> None:
    """Perfect Assassin: AGI+7, LUCK+4 for duration.

    Args:
        state: Current game state
        skill: Skill containing buff_duration

    Side Effects:
        Adds temp AGI and LUCK, sets permAgiLuk buff, recalculates stats
    """
    state.temp_stats["agi"] = state.temp_stats.get("agi", 0) + 7
    state.temp_stats["luck"] = state.temp_stats.get("luck", 0) + 4
    state.buffs["permAgiLuk"] = skill.buff_duration
    state.recalc_stats()


def _buff_permCrit10(state: GameState, skill: Skill) -> None:
    """Sixth Sense: CRIT+25% for duration.

    Args:
        state: Current game state
        skill: Skill containing buff_duration

    Side Effects:
        Sets permCrit10 buff (crit bonus applied in damage calculation)
    """
    state.buffs["permCrit10"] = skill.buff_duration


def _buff_permAll1(state: GameState, skill: Skill) -> None:
    """Vision of the End: All stats +4 for duration.

    Args:
        state: Current game state
        skill: Skill containing buff_duration

    Side Effects:
        Adds +4 to all temp stats, sets permAll1 buff, recalculates stats
    """
    for stat in ("int", "str", "agi", "wis", "luck"):
        state.temp_stats[stat] = state.temp_stats.get(stat, 0) + 4
    state.buffs["permAll1"] = skill.buff_duration
    state.recalc_stats()


def _buff_resetCds(state: GameState, skill: Skill) -> None:
    """Reset all skill cooldowns.

    Args:
        state: Current game state
        skill: Skill being used (unused for this calculation)

    Side Effects:
        Sets current_cd to 0 for all active skills
    """
    for sk in state.active_skills:
        sk.current_cd = 0


def _buff_bloodRitual(state: GameState, skill: Skill) -> None:
    """Blood Ritual: -15% HP for 50 XP.

    Args:
        state: Current game state
        skill: Skill being used (unused for this calculation)

    Side Effects:
        Reduces HP by 15%, adds 50 XP
    """
    state.hp = max(1, state.hp - int(state.max_hp * 0.15))
    state.xp += 50


def _buff_randStat2(state: GameState, skill: Skill) -> Dict[str, Any]:
    """Prophetic Insight: +3 to 2 random stats for 5 turns.

    Args:
        state: Current game state
        skill: Skill being used (unused for this calculation)

    Returns:
        Dict with list of chosen stat names

    Side Effects:
        Adds +3 to 2 random stats, sets randStat2 buff for 5 turns, recalculates stats
    """
    stat_keys = ["int", "str", "agi", "wis", "luck"]
    chosen = random.sample(stat_keys, 2)
    for st in chosen:
        state.temp_stats[st] = state.temp_stats.get(st, 0) + 3
    state.buffs["randStat2"] = 5
    state.recalc_stats()
    return {"stats": chosen}


def _buff_madImmune(state: GameState, skill: Skill) -> None:
    """Madness Mastery: immunity to madness death, +15 MAD.

    Args:
        state: Current game state
        skill: Skill being used (unused for this calculation)

    Side Effects:
        Sets madImmune buff for 999 turns, increases madness by 15
    """
    state.buffs["madImmune"] = 999
    state.madness = min(MADNESS_MAX, state.madness + 15)


def _buff_calmMind(state: GameState, skill: Skill) -> None:
    """Leng's Whisper: -3 MAD.

    Args:
        state: Current game state
        skill: Skill being used (unused for this calculation)

    Side Effects:
        Reduces madness by 3 (minimum 0)
    """
    state.madness = max(0, state.madness - 3)


def _buff_eldritchBargain(state: GameState, skill: Skill) -> Dict[str, Any]:
    """Eldritch Bargain: -3 to 3 random stats, +50 gold.

    Args:
        state: Current game state
        skill: Skill being used (unused for this calculation)

    Returns:
        Dict with list of reduced stat names

    Side Effects:
        Reduces 3 random base stats by 3 each, adds 50 gold, recalculates stats
    """
    stat_keys = ["int", "str", "agi", "wis", "luck"]
    chosen = random.sample(stat_keys, 3)
    for st in chosen:
        state.base_stats[st] = max(1, state.base_stats.get(st, 1) - 3)
    state.recalc_stats()
    state.gold += 50
    return {"stats": chosen}


def _buff_foolLuck(state: GameState, skill: Skill) -> None:
    """The Fool's Luck: -10 MAD, nullify next 3 attacks.

    Args:
        state: Current game state
        skill: Skill being used (unused for this calculation)

    Side Effects:
        Reduces madness by 10, sets divineInterv buff for 3 turns
    """
    state.madness = max(0, state.madness - 10)
    state.buffs["divineInterv"] = 3


def _buff_realityAnchor(state: GameState, skill: Skill) -> None:
    """Reality Anchor: cannot die for duration.

    Args:
        state: Current game state
        skill: Skill containing buff_duration

    Side Effects:
        Sets undying buff for specified duration
    """
    state.buffs["undying"] = skill.buff_duration


def _buff_pallidMask(state: GameState, skill: Skill) -> None:
    """The Pallid Mask: +50% all stats, immune to debuffs for duration.

    Args:
        state: Current game state
        skill: Skill containing buff_duration

    Side Effects:
        Adds +50% of base stats to temp stats, sets pallidMask and immunity buffs, recalculates stats
    """
    for stat in ("int", "str", "agi", "wis", "luck"):
        state.temp_stats[stat] = state.temp_stats.get(stat, 0) + int(
            state.base_stats.get(stat, 5) * 0.5
        )
    state.buffs["pallidMask"] = skill.buff_duration
    state.buffs["immunity"] = skill.buff_duration
    state.recalc_stats()


def _buff_prophetRes(state: GameState, skill: Skill) -> None:
    """Prophet's Resilience: regen 6%/turn, +5 MAD.

    Args:
        state: Current game state
        skill: Skill containing buff_duration

    Side Effects:
        Increases madness by 5, sets regen buff for duration
    """
    state.madness = min(MADNESS_MAX, state.madness + 5)
    state.buffs["regen"] = skill.buff_duration


def _buff_thickSkull(state: GameState, skill: Skill) -> None:
    """Thick Skull: STR+4, WIS+3 for duration.

    Args:
        state: Current game state
        skill: Skill containing buff_duration

    Side Effects:
        Adds temp STR and WIS, sets thickSkull buff, recalculates stats
    """
    state.temp_stats["str"] = state.temp_stats.get("str", 0) + 4
    state.temp_stats["wis"] = state.temp_stats.get("wis", 0) + 3
    state.buffs["thickSkull"] = skill.buff_duration
    state.recalc_stats()


def _buff_perseverance(state: GameState, skill: Skill) -> None:
    """Perseverance: WIS+4, STR+3 for duration.

    Args:
        state: Current game state
        skill: Skill containing buff_duration

    Side Effects:
        Adds temp WIS and STR, sets perseverance buff, recalculates stats
    """
    state.temp_stats["wis"] = state.temp_stats.get("wis", 0) + 4
    state.temp_stats["str"] = state.temp_stats.get("str", 0) + 3
    state.buffs["perseverance"] = skill.buff_duration
    state.recalc_stats()


def _buff_shadowBless(state: GameState, skill: Skill) -> None:
    """Shadow's Blessing: AGI+4, LUCK+3 for duration.

    Args:
        state: Current game state
        skill: Skill containing buff_duration

    Side Effects:
        Adds temp AGI and LUCK, sets shadowBless buff, recalculates stats
    """
    state.temp_stats["agi"] = state.temp_stats.get("agi", 0) + 4
    state.temp_stats["luck"] = state.temp_stats.get("luck", 0) + 3
    state.buffs["shadowBless"] = skill.buff_duration
    state.recalc_stats()


def _buff_abyssFort(state: GameState, skill: Skill) -> None:
    """Abyssal Fortitude: pDEF+50%, +1 barrier.

    Args:
        state: Current game state
        skill: Skill containing buff_duration

    Side Effects:
        Sets ironSkin buff for duration, adds 1 barrier stack
    """
    state.buffs["ironSkin"] = skill.buff_duration
    state.barrier = min(MAX_BARRIER_STACKS, state.barrier + 1)


def _buff_eldritchRebirth(state: GameState, skill: Skill) -> None:
    """Eldritch Rebirth: auto-revive at 30% HP if killed.

    Args:
        state: Current game state
        skill: Skill containing buff_duration

    Side Effects:
        Sets eldritchRebirth buff for duration
    """
    state.buffs["eldritchRebirth"] = skill.buff_duration


def _buff_astral(state: GameState, skill: Skill) -> None:
    """Astral Projection: EVA+40%, mDEF+60% for duration.

    Args:
        state: Current game state
        skill: Skill containing buff_duration

    Side Effects:
        Sets astral buff for duration
    """
    state.buffs["astral"] = skill.buff_duration


def _buff_statSwap(state: GameState, skill: Skill) -> None:
    """Mind Over Matter: swap pDEF and mDEF for duration.

    Args:
        state: Current game state
        skill: Skill containing buff_duration

    Side Effects:
        Sets statSwap buff for duration
    """
    state.buffs["statSwap"] = skill.buff_duration


def _buff_dreadnought(state: GameState, skill: Skill) -> None:
    """Dreadnought: damage taken converts to ATK for duration.

    Args:
        state: Current game state
        skill: Skill containing buff_duration

    Side Effects:
        Sets dreadnought buff for duration
    """
    state.buffs["dreadnought"] = skill.buff_duration


# Static messages per buff_type
_BUFF_MESSAGES: Dict[str, str] = {
    "barrier": "Barrier! ({v} stacks)",
    "rage": "Berserker Rage! +60% damage, -{hp_loss} HP!",
    "warlord": "Warlord's Command! All buffs active! -{hp_loss} HP!",
    "permIntWis": "Forbidden Text Deciphered! INT+6, WIS+4 for 5 turns!",
    "permAtk2": "Warpaint! STR+5 for 5 turns!",
    "permWisStr": "Oath of the Warden! WIS+6, STR+4 for 5 turns!",
    "permAgiLuk": "Perfect Assassin! AGI+7, LUCK+4 for 5 turns!",
    "permCrit10": "Sixth Sense! CRIT+25% for 4 turns!",
    "permAll1": "Vision of the End! All stats +4 for 5 turns!",
    "resetCds": "All cooldowns reset!",
    "bloodRitual": "Blood Ritual! Sacrificed HP for 50 XP!",
    "randStat2": "Prophetic Insight! {stats}! for 5 turns!",
    "madImmune": "Madness Mastery! MAD no longer causes death! (+15 MAD)",
    "madPower": "Empower Madness! +25% DMG! (+15 MAD)",
    "calmMind": "Leng's Whisper muffles the madness. -3 MAD!",
    "eldritchBargain": "Eldritch Bargain! -3 to {stats}, +50 gold!",
    "foolLuck": "The Fool's Luck! -10 MAD, nullify next 3 attacks!",
    "realityAnchor": "Reality Anchor! Cannot die for 2 turns!",
    "pallidMask": "The Pallid Mask manifests! +50% all stats, immune to debuffs 3t!",
    "prophetRes": "Prophet's Resilience! Regen 6% HP/turn. (+5 MAD)",
    "thickSkull": "Thick Skull! STR+4, WIS+3 for 5 turns!",
    "perseverance": "Perseverance! WIS+4, STR+3 for 5 turns!",
    "shadowBless": "Shadow's Blessing! AGI+4, LUCK+3 for 5 turns!",
    "abyssFort": "Abyssal Fortitude! pDEF+50%, +1 barrier!",
    "eldritchRebirth": "Eldritch Rebirth! Auto-revive at 30% HP if killed! ({d} turns)",
    "astral": "Astral Projection! EVA+40%, mDEF+60% for {d} turns!",
    "statSwap": "Mind Over Matter! pDEF and mDEF swapped for {d} turns!",
    "dreadnought": "Dreadnought! Damage taken converts to ATK for {d} turns!",
}

BUFF_HANDLERS: Dict[str, BuffApplyFn] = {
    "barrier": _buff_barrier,
    "rage": _buff_rage,
    "warlord": _buff_warlord,
    "permIntWis": _buff_permIntWis,
    "permAtk2": _buff_permAtk2,
    "permWisStr": _buff_permWisStr,
    "permAgiLuk": _buff_permAgiLuk,
    "permCrit10": _buff_permCrit10,
    "permAll1": _buff_permAll1,
    "resetCds": _buff_resetCds,
    "bloodRitual": _buff_bloodRitual,
    "randStat2": _buff_randStat2,
    "madImmune": _buff_madImmune,
    "calmMind": _buff_calmMind,
    "eldritchBargain": _buff_eldritchBargain,
    "foolLuck": _buff_foolLuck,
    "realityAnchor": _buff_realityAnchor,
    "pallidMask": _buff_pallidMask,
    "prophetRes": _buff_prophetRes,
    "thickSkull": _buff_thickSkull,
    "perseverance": _buff_perseverance,
    "shadowBless": _buff_shadowBless,
    "abyssFort": _buff_abyssFort,
    "eldritchRebirth": _buff_eldritchRebirth,
    "astral": _buff_astral,
    "statSwap": _buff_statSwap,
    "dreadnought": _buff_dreadnought,
}


def _handle_self_buff(state: GameState, skill: Skill) -> List[LogEntry]:
    """Handle self_buff skill type. Returns list of log messages."""
    buff_type = skill.buff_type
    if not buff_type:
        return [(f"{skill.name} activated!", "effect")]

    handler = BUFF_HANDLERS.get(buff_type)
    if handler is None:
        state.buffs[buff_type] = skill.buff_duration
        return [(f"{skill.name} activated!", "effect")]

    extra = handler(state, skill) or {}

    msg_template = _BUFF_MESSAGES.get(buff_type, f"{skill.name} activated!")
    fmt = dict(extra)
    fmt["v"] = state.barrier
    fmt["d"] = skill.buff_duration
    if "stats" in fmt and isinstance(fmt["stats"], list):
        fmt["stats"] = ", ".join(
            s.upper() + ("+3" if buff_type == "randStat2" else "-3")
            for s in fmt["stats"]
        )
    try:
        msg = msg_template.format(**fmt)
    except (KeyError, IndexError):
        msg = msg_template

    return [(msg, "effect" if buff_type != "barrier" else "shield")]


def player_use_skill(state: GameState, skill_index: int) -> List[LogEntry]:
    """Player uses a skill. Returns list of (text, type) log messages."""
    from engine.combat import calc_player_damage, apply_damage_to_enemy

    logs: List[LogEntry] = []
    skill = state.active_skills[skill_index]
    c = state.combat
    e = c.enemy

    # --- Pre-checks ---
    if skill.current_cd > 0:
        return [("That ability is on cooldown!", "info")]

    if skill.cost > 0:
        state.madness = min(MADNESS_MAX, state.madness + skill.cost)
        if state.madness >= MADNESS_MAX:
            return [("Your mind shatters from the madness cost!", "damage")]

    if skill.madness_cost > 0:
        state.madness = max(0, state.madness - skill.madness_cost)

    if skill.hp_cost > 0:
        hp_loss = int(state.max_hp * skill.hp_cost)
        state.hp = max(1, state.hp - hp_loss)
        logs.append((f"Sacrificed {hp_loss} HP!", "damage"))

    skill.current_cd = skill.cd + 1

    # --- Non-damage skill types ---
    if skill.type == "self_heal":
        return logs + _handle_self_heal(state, skill)

    if skill.type == "self_shield":
        return logs + _handle_self_shield(state, skill)

    if skill.type == "self_buff":
        return logs + _handle_self_buff(state, skill)

    # Accuracy miss check (skip for true_strike skills)
    if not skill.true_strike:
        if random.random() * 100 >= state.accuracy:
            logs.append((f"{skill.name} misses!", "info"))
            return logs

    # Damage-dealing skill
    raw = calc_player_damage(state, skill)

    if skill.consume_shield:
        raw += state.shield
        state.shield = 0
        logs.append(("Shield consumed for extra damage!", "effect"))

    if skill.shield_scaling:
        raw += int(state.shield * skill.shield_scaling)

    dmg, is_crit = apply_damage_to_enemy(state, raw, skill)
    crit_text = " CRITICAL!" if is_crit else ""
    logs.append(
        (
            f"You use {skill.name} for {dmg} damage!{crit_text}",
            "crit" if is_crit else "damage",
        )
    )

    if skill.lifesteal and dmg > 0:
        h = int(dmg * skill.lifesteal)
        state.hp = min(state.max_hp, state.hp + h)
        logs.append((f"Stole {h} HP!", "heal"))

    # Consume ethereal buff after attack
    if state.buffs.get("ethereal", 0) > 0 and dmg > 0:
        state.buffs["ethereal"] = 0

    if state.madness >= MADNESS_MAX:
        return logs + [("Your mind shatters from the madness!", "damage")]

    # Apply effects
    if skill.effect:
        apply_status(e, skill.effect, skill.duration)
        if skill.effect == "poisoned":
            existing = next((s for s in e.statuses if s.type == "poisoned"), None)
            if existing:
                existing.stacks = min(POISON_MAX_STACKS, existing.stacks + 1)
        logs.append((f"{skill.effect} applied to {e.name}!", "effect"))

    if skill.effect2:
        apply_status(e, skill.effect2, skill.duration)
        logs.append((f"{skill.effect2} applied to {e.name}!", "effect"))

    if skill.effect3:
        apply_status(e, skill.effect3, skill.duration)
        logs.append((f"{skill.effect3} applied to {e.name}!", "effect"))

    if skill.extend_debuffs:
        for st in e.statuses:
            st.duration += 2
        if e.statuses:
            logs.append(("All debuffs extended by 2 turns!", "effect"))

    if skill.random_effect:
        choice = random.randint(0, 3)
        if choice == 0:
            h = int(state.max_hp * 0.5)
            state.hp = min(state.max_hp, state.hp + h)
            logs.append((f"Hastur heals you for {h}!", "heal"))
        elif choice == 1:
            for eff in ("burning", "petrified", "blinded", "shocked", "poisoned"):
                apply_status(e, eff, 3)
            logs.append(("Hastur curses your foe with ALL debuffs!", "effect"))
        elif choice == 2:
            raw2 = int((5 + state.stats["wis"] * 2.0) * 3.0)
            dmg2, _ = apply_damage_to_enemy(state, raw2, skill)
            logs.append((f"Hastur smites for {dmg2}!", "crit"))
        else:
            state.base_stats["luck"] = state.base_stats.get("luck", 5) + 5
            state.recalc_stats()
            logs.append(("Hastur grants LUK+5!", "effect"))

    return logs

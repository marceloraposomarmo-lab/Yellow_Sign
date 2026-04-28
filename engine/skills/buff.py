"""Buff handler functions, messages, and registry.

28 buff handler functions + _BUFF_MESSAGES dict + BUFF_HANDLERS registry
+ _handle_self_buff dispatcher.
"""

import random
from typing import List, Dict, Any, Optional

from data import MADNESS_MAX, MAX_BARRIER_STACKS
from engine.models import Skill, GameState
from engine.skills._types import LogEntry, BuffApplyFn

# ═══════════════════════════════════════════
# BUFF HANDLER FUNCTIONS
# ═══════════════════════════════════════════


def _buff_barrier(state: GameState, skill: Skill) -> None:
    """Add barrier stacks up to MAX_BARRIER_STACKS."""
    state.barrier = min(MAX_BARRIER_STACKS, state.barrier + skill.barrier_stacks)


def _buff_rage(state: GameState, skill: Skill) -> Dict[str, Any]:
    """Berserker Rage: +60% damage, -12% HP.

    The player channels their fury at the cost of their own vitality.
    Returns hp_loss for message formatting.
    """
    from data import BUFF_RAGE_HP_PCT

    state.rage = True
    state.buffs["rage"] = skill.buff_duration
    hp_loss = int(state.max_hp * BUFF_RAGE_HP_PCT)
    state.hp = max(1, state.hp - hp_loss)
    return {"hp_loss": hp_loss}


def _buff_warlord(state: GameState, skill: Skill) -> Dict[str, Any]:
    """Warlord's Command: all combat buffs, -20% HP.

    A devastating self-buff that activates rage, critical hit chance, and
    iron skin simultaneously, but drains a fifth of max HP.
    """
    from data import BUFF_WARLORD_HP_PCT

    state.rage = True
    state.buffs["rage"] = skill.buff_duration
    state.buffs["atkCritUp"] = skill.buff_duration
    state.buffs["ironSkin"] = skill.buff_duration
    hp_loss = int(state.max_hp * BUFF_WARLORD_HP_PCT)
    state.hp = max(1, state.hp - hp_loss)
    return {"hp_loss": hp_loss}


def _buff_permIntWis(state: GameState, skill: Skill) -> None:
    """Forbidden Text: INT+6, WIS+4 for duration."""
    from data import BUFF_STAT_BOOST_LARGE, BUFF_STAT_BOOST_SMALL

    state.temp_stats["int"] = state.temp_stats.get("int", 0) + BUFF_STAT_BOOST_LARGE
    state.temp_stats["wis"] = state.temp_stats.get("wis", 0) + BUFF_STAT_BOOST_SMALL
    state.buffs["permIntWis"] = skill.buff_duration
    state.recalc_stats()


def _buff_permAtk2(state: GameState, skill: Skill) -> None:
    """Warpaint: STR+5 for duration."""
    from data import BUFF_STAT_BOOST_MEDIUM

    state.temp_stats["str"] = state.temp_stats.get("str", 0) + BUFF_STAT_BOOST_MEDIUM
    state.buffs["permAtk2"] = skill.buff_duration
    state.recalc_stats()


def _buff_permWisStr(state: GameState, skill: Skill) -> None:
    """Oath of the Warden: WIS+6, STR+4 for duration."""
    from data import BUFF_STAT_BOOST_LARGE, BUFF_STAT_BOOST_SMALL

    state.temp_stats["wis"] = state.temp_stats.get("wis", 0) + BUFF_STAT_BOOST_LARGE
    state.temp_stats["str"] = state.temp_stats.get("str", 0) + BUFF_STAT_BOOST_SMALL
    state.buffs["permWisStr"] = skill.buff_duration
    state.recalc_stats()


def _buff_permAgiLuk(state: GameState, skill: Skill) -> None:
    """Perfect Assassin: AGI+7, LUCK+4 for duration."""
    from data import BUFF_STAT_BOOST_MAJOR, BUFF_STAT_BOOST_SMALL

    state.temp_stats["agi"] = state.temp_stats.get("agi", 0) + BUFF_STAT_BOOST_MAJOR
    state.temp_stats["luck"] = state.temp_stats.get("luck", 0) + BUFF_STAT_BOOST_SMALL
    state.buffs["permAgiLuk"] = skill.buff_duration
    state.recalc_stats()


def _buff_innerFire(state: GameState, skill: Skill) -> None:
    """Inner Fire / Lucky Coin Toss / Threshold Sense: WIS+3, LUCK+5."""
    from data import BUFF_STAT_BOOST_MINOR, BUFF_STAT_BOOST_MEDIUM

    state.temp_stats["wis"] = state.temp_stats.get("wis", 0) + BUFF_STAT_BOOST_MINOR
    state.temp_stats["luck"] = state.temp_stats.get("luck", 0) + BUFF_STAT_BOOST_MEDIUM
    state.buffs["innerFire"] = skill.buff_duration
    state.recalc_stats()


def _buff_luckyDodge(state: GameState, skill: Skill) -> None:
    """Lucky Dodge / Unreliable Fortune: LUCK+3."""
    from data import BUFF_STAT_BOOST_MINOR

    state.temp_stats["luck"] = state.temp_stats.get("luck", 0) + BUFF_STAT_BOOST_MINOR
    state.buffs["luckyDodge"] = skill.buff_duration
    state.recalc_stats()


def _buff_critUp(state: GameState, skill: Skill) -> None:
    """Eldritch Sight / Fate Reading / Cartographer's Eye / Collector's Eye.

    Sets critUp buff (evasion from EVASION_BUFF_TABLE, crit applied in damage calc).
    """
    state.buffs["critUp"] = skill.buff_duration


def _buff_permCrit10(state: GameState, skill: Skill) -> None:
    """Sixth Sense: CRIT+25% for duration.

    The crit bonus is applied during the damage calculation phase,
    not here — this function only registers the buff flag and duration.
    """
    state.buffs["permCrit10"] = skill.buff_duration


def _buff_permAll1(state: GameState, skill: Skill) -> None:
    """Vision of the End: All stats +4 for duration."""
    from data import BUFF_STAT_BOOST_SMALL

    for stat in ("int", "str", "agi", "wis", "luck"):
        state.temp_stats[stat] = state.temp_stats.get(stat, 0) + BUFF_STAT_BOOST_SMALL
    state.buffs["permAll1"] = skill.buff_duration
    state.recalc_stats()


def _buff_resetCds(state: GameState, skill: Skill) -> None:
    """Reset all skill cooldowns."""
    for sk in state.active_skills:
        sk.current_cd = 0


def _buff_bloodRitual(state: GameState, skill: Skill) -> None:
    """Blood Ritual: -15% HP for 50 XP."""
    from data import BUFF_BLOOD_RITUAL_HP_PCT

    state.hp = max(1, state.hp - int(state.max_hp * BUFF_BLOOD_RITUAL_HP_PCT))
    state.xp += 50


def _buff_randStat2(state: GameState, skill: Skill) -> Dict[str, Any]:
    """Prophetic Insight: +3 to 2 random stats for 5 turns.

    Returns the list of chosen stats for message formatting.
    """
    stat_keys = ["int", "str", "agi", "wis", "luck"]
    chosen = random.sample(stat_keys, 2)
    for st in chosen:
        state.temp_stats[st] = state.temp_stats.get(st, 0) + 3
    state.buffs["randStat2"] = 5
    state.recalc_stats()
    return {"stats": chosen}


def _buff_madImmune(state: GameState, skill: Skill) -> None:
    """Madness Mastery: immunity to madness death, +15 MAD."""
    from data import MADNESS_COST_MEDIUM

    state.buffs["madImmune"] = 999
    state.madness = min(MADNESS_MAX, state.madness + MADNESS_COST_MEDIUM)


def _buff_calmMind(state: GameState, skill: Skill) -> None:
    """Leng's Whisper: -3 MAD."""
    state.madness = max(0, state.madness - 3)


def _buff_eldritchBargain(state: GameState, skill: Skill) -> Dict[str, Any]:
    """Eldritch Bargain: -3 to 3 random stats, +50 gold.

    A risky trade that permanently weakens stats in exchange for
    immediate wealth. Returns the list of reduced stats for formatting.
    """
    stat_keys = ["int", "str", "agi", "wis", "luck"]
    chosen = random.sample(stat_keys, 3)
    for st in chosen:
        state.base_stats[st] = max(1, state.base_stats.get(st, 1) - 3)
    state.recalc_stats()
    state.gold += 50
    return {"stats": chosen}


def _buff_foolLuck(state: GameState, skill: Skill) -> None:
    """The Fool's Luck: -10 MAD, nullify next 3 attacks."""
    state.madness = max(0, state.madness - 10)
    state.buffs["divineInterv"] = 3


def _buff_realityAnchor(state: GameState, skill: Skill) -> None:
    """Reality Anchor: cannot die for duration."""
    state.buffs["undying"] = skill.buff_duration


def _buff_pallidMask(state: GameState, skill: Skill) -> None:
    """The Pallid Mask: +50% all stats, immune to debuffs for duration.

    The most powerful buff in the game — adds 50% of base stats as temp
    bonuses and grants complete debuff immunity.
    """
    from data import BUFF_STAT_SWAP_FACTOR

    for stat in ("int", "str", "agi", "wis", "luck"):
        state.temp_stats[stat] = state.temp_stats.get(stat, 0) + int(
            state.base_stats.get(stat, 5) * BUFF_STAT_SWAP_FACTOR
        )
    state.buffs["pallidMask"] = skill.buff_duration
    state.buffs["immunity"] = skill.buff_duration
    state.recalc_stats()


def _buff_prophetRes(state: GameState, skill: Skill) -> None:
    """Prophet's Resilience: regen 6%/turn, +5 MAD."""
    from data import MADNESS_COST_MINOR

    state.madness = min(MADNESS_MAX, state.madness + MADNESS_COST_MINOR)
    state.buffs["regen"] = skill.buff_duration


def _buff_thickSkull(state: GameState, skill: Skill) -> None:
    """Thick Skull: STR+4, WIS+3 for duration."""
    from data import BUFF_STAT_BOOST_SMALL, BUFF_STAT_BOOST_MINOR

    state.temp_stats["str"] = state.temp_stats.get("str", 0) + BUFF_STAT_BOOST_SMALL
    state.temp_stats["wis"] = state.temp_stats.get("wis", 0) + BUFF_STAT_BOOST_MINOR
    state.buffs["thickSkull"] = skill.buff_duration
    state.recalc_stats()


def _buff_perseverance(state: GameState, skill: Skill) -> None:
    """Perseverance: WIS+4, STR+3 for duration."""
    from data import BUFF_STAT_BOOST_SMALL, BUFF_STAT_BOOST_MINOR

    state.temp_stats["wis"] = state.temp_stats.get("wis", 0) + BUFF_STAT_BOOST_SMALL
    state.temp_stats["str"] = state.temp_stats.get("str", 0) + BUFF_STAT_BOOST_MINOR
    state.buffs["perseverance"] = skill.buff_duration
    state.recalc_stats()


def _buff_shadowBless(state: GameState, skill: Skill) -> None:
    """Shadow's Blessing: AGI+4, LUCK+3 for duration."""
    from data import BUFF_STAT_BOOST_SMALL, BUFF_STAT_BOOST_MINOR

    state.temp_stats["agi"] = state.temp_stats.get("agi", 0) + BUFF_STAT_BOOST_SMALL
    state.temp_stats["luck"] = state.temp_stats.get("luck", 0) + BUFF_STAT_BOOST_MINOR
    state.buffs["shadowBless"] = skill.buff_duration
    state.recalc_stats()


def _buff_abyssFort(state: GameState, skill: Skill) -> None:
    """Abyssal Fortitude: pDEF+50%, +1 barrier."""
    state.buffs["ironSkin"] = skill.buff_duration
    state.barrier = min(MAX_BARRIER_STACKS, state.barrier + 1)


def _buff_eldritchRebirth(state: GameState, skill: Skill) -> None:
    """Eldritch Rebirth: auto-revive at 30% HP if killed."""
    state.buffs["eldritchRebirth"] = skill.buff_duration


def _buff_astral(state: GameState, skill: Skill) -> None:
    """Astral Projection: EVA+40%, mDEF+60% for duration."""
    state.buffs["astral"] = skill.buff_duration


def _buff_statSwap(state: GameState, skill: Skill) -> None:
    """Mind Over Matter: swap pDEF and mDEF for duration."""
    state.buffs["statSwap"] = skill.buff_duration


def _buff_dreadnought(state: GameState, skill: Skill) -> None:
    """Dreadnought: damage taken converts to ATK for duration."""
    state.buffs["dreadnought"] = skill.buff_duration


def _buff_madPower(state: GameState, skill: Skill) -> None:
    """Empower Madness: +25% DMG, +15 MAD."""
    from data import MADNESS_COST_MEDIUM

    state.buffs["madPower"] = skill.buff_duration
    state.madness = min(MADNESS_MAX, state.madness + MADNESS_COST_MEDIUM)


def _buff_darkPact(state: GameState, skill: Skill) -> Dict[str, Any]:
    """Dark Pact: +30% DMG, debuffs extended, -15% HP.

    A dangerous pact that amplifies offense at the cost of health and
    debuff vulnerability. Returns hp_loss for message formatting.
    """
    from data import BUFF_DARK_PACT_HP_PCT

    state.buffs["darkPact"] = skill.buff_duration
    hp_loss = int(state.max_hp * BUFF_DARK_PACT_HP_PCT)
    state.hp = max(1, state.hp - hp_loss)
    return {"hp_loss": hp_loss}


def _buff_warpTime(state: GameState, skill: Skill) -> None:
    """Warp Time: reset all cooldowns, +20% DMG for duration."""
    for sk in state.active_skills:
        sk.current_cd = 0
    state.buffs["warpTime"] = skill.buff_duration


def _buff_fortress(state: GameState, skill: Skill) -> None:
    """Divine Fortress: pDEF/mDEF+80%, +2 barriers for duration."""
    state.buffs["fortress"] = skill.buff_duration
    state.barrier = min(MAX_BARRIER_STACKS, state.barrier + 2)


def _buff_undyingPact(state: GameState, skill: Skill) -> None:
    """Undying Pact: cannot die, +50% ATK for duration."""
    state.buffs["undyingPact"] = skill.buff_duration


def _buff_eclipse(state: GameState, skill: Skill) -> None:
    """Eclipse: all attacks crit, +30% DMG for duration."""
    state.buffs["eclipse"] = skill.buff_duration


# ═══════════════════════════════════════════
# BUFF MESSAGE TEMPLATES
# ═══════════════════════════════════════════

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
    "innerFire": "Inner Fire burns! WIS+3, LUCK+5 for {d} turns!",
    "luckyDodge": "Lucky Dodge! EVA+35%, LUCK+3 for {d} turns!",
    "critUp": "Eldritch Sight! EVA+15% for {d} turns!",
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
    "dreadnought": "Dreadnought! Damage taken converts to ATK for {d} turns!",
    # --- Buffs without dedicated handler functions (set directly via fallback) ---
    "atkCritUp": "Blood Scent! ATK+20%, CRIT+15% for {d} turns!",
    "bladeAura": "Aura of Blades! 15% counter-attack for {d} turns!",
    "bloodAura": "Aura of Blood! 10% lifesteal for {d} turns!",
    "bulwark": "Bulwark! pDEF+60%, mDEF+60% for {d} turns!",
    "chant": "Guttural Chant! pDEF+20%, mDEF+20% for {d} turns!",
    "copyAttack": "Living Shadow active! Copies enemy attack for {d} turns!",
    "darkPact": "Dark Pact! +30% DMG, debuffs extended! -{hp_loss} HP!",
    "divineInterv": "Divine Intervention! Next {v} attacks nullified!",
    "dreamShell": "Dream Shell! EVA+50%, mDEF+80% for {d} turns!",
    "dreamVeil": "Veil of the Dream! EVA+35% for {d} turns!",
    "evasionUp": "Evasion! EVA+40% for {d} turns!",
    "fadeBlack": "Fade to Black! EVA+20%, regen 5% for {d} turns!",
    "finalStand": "Final Stand! Cannot die this turn!",
    "flicker": "Flicker! 50% dodge next {v} attacks!",
    "fortress": "Divine Fortress! pDEF/mDEF+80%, +2 barriers for {d} turns!",
    "hallowed": "Hallowed Ground! pDEF+40%, mDEF+40% for {d} turns!",
    "ironSkin": "Iron Skin! pDEF+60%, mDEF+30% for {d} turns!",
    "mDefUp": "Arcane Ward! mDEF+50% for {d} turns!",
    "mirrorImg": "Mirror Images! 30% damage reduction for {d} turns!",
    "nimbleFingers": "Nimble Fingers! +20% loot quality for {d} floors!",
    "oath": "Oath of Protection! Shield + regen for {d} turns!",
    "regen": "Consecrated Ground! Regen 8% HP/turn for {d} turns!",
    "regen5": "Unnatural Vitality! Regen 5% HP/turn for {d} turns!",
    "retribAura": "Aura of Retribution! Reflect 30% damage for {d} turns!",
    "shadowMeld": "Shadow Meld! Invisible 1 turn, next attack +100%!",
    "skipCombat": "Shadow Step! Next combat encounter skipped!",
    "smokeScreen": "Smoke Screen! EVA+25% for {d} turns!",
    "statSwap": "Mind Over Matter! pDEF and mDEF swapped for {d} turns!",
    "thoughtform": "Thoughtform Armor! pDEF+30%, mDEF+30% for {d} turns!",
    "umbralAegis": "Umbral Aegis! EVA+60%, pDEF+40% for {d} turns!",
    "undying": "Undying Fury! Cannot die for {d} turns!",
    "undyingPact": "Undying Pact! Cannot die, +50% ATK for {d} turns!",
    "wardAura": "Aura of Warding! mDEF+30% for {d} turns!",
    "warpTime": "Warp Time! CDs reset, +20% DMG for {d} turns!",
    "ethereal": "Ethereal Jaunt! Invulnerable 1 turn, next attack +150%!",
    "looterInst": "Looter's Instinct! +10% loot quality for {d} floors!",
    "eclipse": "Eclipse! All attacks crit, +30% DMG for {d} turns!",
}


# ═══════════════════════════════════════════
# BUFF HANDLER REGISTRY
# ═══════════════════════════════════════════

BUFF_HANDLERS: Dict[str, BuffApplyFn] = {
    "barrier": _buff_barrier,
    "rage": _buff_rage,
    "warlord": _buff_warlord,
    "permIntWis": _buff_permIntWis,
    "permAtk2": _buff_permAtk2,
    "permWisStr": _buff_permWisStr,
    "permAgiLuk": _buff_permAgiLuk,
    "permCrit10": _buff_permCrit10,
    "innerFire": _buff_innerFire,
    "luckyDodge": _buff_luckyDodge,
    "critUp": _buff_critUp,
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
    "madPower": _buff_madPower,
    "darkPact": _buff_darkPact,
    "warpTime": _buff_warpTime,
    "fortress": _buff_fortress,
    "undyingPact": _buff_undyingPact,
    "eclipse": _buff_eclipse,
}


# ═══════════════════════════════════════════
# BUFF DISPATCHER
# ═══════════════════════════════════════════


def _handle_self_buff(state: GameState, skill: Skill) -> List[LogEntry]:
    """Handle self_buff skill type. Returns list of log messages.

    Looks up a handler in BUFF_HANDLERS by buff_type. If no handler exists,
    the buff is registered as a simple duration-based flag. Messages are
    formatted using _BUFF_MESSAGES with extra context from the handler.
    """
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
        fmt["stats"] = ", ".join(s.upper() + ("+3" if buff_type == "randStat2" else "-3") for s in fmt["stats"])
    try:
        msg = msg_template.format(**fmt)
    except (KeyError, IndexError):
        msg = msg_template

    return [(msg, "effect" if buff_type != "barrier" else "shield")]

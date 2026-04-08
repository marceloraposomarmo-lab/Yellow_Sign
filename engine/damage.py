"""Damage calculation and application logic."""

import random
from typing import Tuple, Optional, Dict, Any, List

from data import (
    DEFENSE_DENOM,
    CRIT_BASE_MULT,
    DMG_VARIANCE_LOW,
    DMG_VARIANCE_RANGE,
    LUCK_DMG_VARIANCE,
    EXECUTE_HP_THRESHOLD,
    EXECUTE_DAMAGE_MULT,
    COIN_FLIP_HEAL_FRAC,
    COIN_FLIP_DAMAGE_MULT,
    GAMBLE_MIN,
    GAMBLE_RANGE,
    DAMAGE_BUFF_MULTIPLIERS,
    DEFENSE_BUFF_TABLE,
    EVASION_BUFF_TABLE,
    MIRROR_IMG_REDUCTION,
    BLOOD_AURA_LS_PCT,
    RETRIB_AURA_REFLECT_PCT,
    DREADNOUGHT_CONVERSION_PCT,
    ELDRITCH_REBIRTH_HP_PCT,
    CRIT_UP_BONUS,
    ATK_CRIT_UP_BONUS,
    WEAKENED_DEF_MULT,
)
from engine.models import Skill, GameState, has_status

# ═══════════════════════════════════════════
# DAMAGE CALCULATION
# ═══════════════════════════════════════════


def _base_damage(state: GameState, skill: Skill) -> float:
    """Core damage calculation shared by player and preview paths.

    Args:
        state: Current game state with player stats and buffs
        skill: Skill being used for damage calculation

    Returns:
        Raw base damage as float (no random variance, no defense reduction)

    Raises:
        ZeroDivisionError: Prevented by max_hp > 0 checks
    """
    sv = state.stats.get(skill.stat, 10)
    s2v = state.stats.get(skill.stat2, 10) if skill.stat2 else 0

    if skill.type in ("physical", "physical_debuff", "mixed_phys"):
        bd = state.atk * (skill.power or 1) + sv * 0.8
        if skill.stat2_mult:
            bd += s2v * skill.stat2_mult
        if skill.def_scaling:
            bd += state.defense * 1.0
    elif skill.type in ("magic", "magic_debuff", "mixed_magic"):
        bd = (5 + sv * 1.5) * (skill.power or 1)
        if skill.stat2_mult:
            bd += s2v * skill.stat2_mult
    elif skill.type == "debuff":
        bd = (5 + sv * 1.5) * (skill.power or 1)
    elif skill.type in ("self_buff", "self_heal", "self_shield", "curse", "ultimate"):
        bd = 0
        if skill.type == "curse" and skill.consume_shield:
            bd = (5 + sv * 1.5) * skill.power + state.shield
        elif skill.type == "ultimate":
            bd = (5 + sv * 1.5) * skill.power
            if skill.stat2_mult:
                bd += s2v * skill.stat2_mult
        else:
            bd = (5 + sv * 1.5) * (skill.power or 1) if skill.power else 0
    else:
        bd = (5 + sv * 1.5) * (skill.power or 1)

    if skill.scaling_low_hp:
        hr = state.hp / state.max_hp if state.max_hp > 0 else 1.0
        bd *= 1 + (1 - hr) * 2.0

    if skill.madness_scaling:
        bd *= 1 + state.madness / 100

    # Apply damage buff multipliers from registry
    for buff_key, mult in DAMAGE_BUFF_MULTIPLIERS.items():
        if state.buffs.get(buff_key, 0) > 0:
            bd *= mult

    if skill.multihit and skill.multihit > 1:
        bd *= skill.multihit

    if skill.execute_bonus and state.combat:
        e = state.combat.enemy
        if e and e.max_hp > 0 and e.hp / e.max_hp < EXECUTE_HP_THRESHOLD:
            bd *= EXECUTE_DAMAGE_MULT

    if skill.luck_bonus:
        bd *= 1 + state.luck * 0.02

    return bd


def calc_player_damage(state: GameState, skill: Skill) -> int:
    """Calculate raw player damage for a skill (with random variance).

    Args:
        state: Current game state with player stats and buffs
        skill: Skill being used for damage calculation

    Returns:
        Final damage value after variance and special effects
    """
    bd = _base_damage(state, skill)

    # Random variance
    bd *= 1 + random.random() * state.luck * LUCK_DMG_VARIANCE
    bd *= DMG_VARIANCE_LOW + random.random() * DMG_VARIANCE_RANGE

    if skill.gamble:
        gm = GAMBLE_MIN + random.random() * GAMBLE_RANGE
        bd *= gm

    if skill.coin_flip:
        if random.random() < 0.5:
            bd = 0
            h = int(state.max_hp * COIN_FLIP_HEAL_FRAC)
            state.hp = min(state.max_hp, state.hp + h)
        else:
            bd *= COIN_FLIP_DAMAGE_MULT

    return int(bd)


def calc_preview_damage(state: GameState, skill: Skill) -> Tuple[int, int]:
    """Calculate deterministic preview damage for a skill (no random variance).

    Args:
        state: Current game state with player stats and buffs
        skill: Skill being used for damage calculation

    Returns:
        Tuple of (base_dmg, final_dmg_after_def) as approximate range center
    """
    bd = _base_damage(state, skill)

    base_dmg = int(bd)
    if base_dmg <= 0:
        return 0, 0

    # Apply enemy defense reduction
    final_dmg = base_dmg
    if state.combat and state.combat.enemy:
        e = state.combat.enemy
        df = e.defense
        if skill.type in ("magic", "magic_debuff", "mixed_magic"):
            df = e.m_def
        if skill.armor_pierce:
            df *= 1 - skill.armor_pierce
        if has_status(e, "weakened"):
            df *= WEAKENED_DEF_MULT
        dr = df / (df + DEFENSE_DENOM)
        final_dmg = max(1, int(base_dmg * (1 - dr)))

    return base_dmg, final_dmg


# ═══════════════════════════════════════════
# DAMAGE APPLICATION
# ═══════════════════════════════════════════


def apply_damage_to_enemy(
    state: GameState, raw: float, skill: Optional[Skill]
) -> Tuple[int, bool]:
    """Apply damage to enemy, accounting for defense and crits.

    Args:
        state: Current game state with player stats and combat info
        raw: Raw damage value before defense reduction
        skill: Optional skill used for the attack (affects damage type)

    Returns:
        Tuple of (actual_damage_dealt, is_critical_hit)
    """
    e = state.combat.enemy
    df = e.defense
    if skill and skill.type in ("magic", "magic_debuff", "mixed_magic"):
        df = e.m_def
    if skill and skill.armor_pierce:
        df *= 1 - skill.armor_pierce
    if has_status(e, "weakened"):
        df *= WEAKENED_DEF_MULT
    dr = df / (df + DEFENSE_DENOM)
    dmg = max(1, int(raw * (1 - dr)))

    is_crit = False
    cc = state.crit
    if state.buffs.get("critUp", 0) > 0:
        cc += CRIT_UP_BONUS
    if state.buffs.get("atkCritUp", 0) > 0:
        cc += ATK_CRIT_UP_BONUS
    if state.buffs.get("permCrit10", 0) > 0:
        cc += 25
    if skill and skill.flat_crit_bonus:
        cc += skill.flat_crit_bonus
    if skill and skill.guaranteed_crit:
        is_crit = True
    elif random.random() * 100 < cc:
        is_crit = True

    if is_crit:
        dmg = int(dmg * (CRIT_BASE_MULT + state.luck * 0.01))

    dmg = max(1, dmg)
    e.hp = max(0, e.hp - dmg)
    return dmg, is_crit


def _get_buff_defense_bonus(state: GameState, is_phys: bool) -> int:
    """Calculate DEF/mDEF percentage bonus from active buffs using registry.

    Args:
        state: Current game state with active buffs
        is_phys: True if physical damage, False if magic damage

    Returns:
        Percentage bonus to defense (0-100+)
    """
    pct = 0
    b = state.buffs
    for buff_key, phys_pct, magic_pct in DEFENSE_BUFF_TABLE:
        if b.get(buff_key, 0) > 0:
            pct += phys_pct if is_phys else magic_pct
    return pct


def _get_buff_evasion_bonus(state: GameState) -> int:
    """Calculate EVA bonus from active buffs using registry.

    Args:
        state: Current game state with active buffs

    Returns:
        Evasion bonus percentage
    """
    bonus = 0
    b = state.buffs
    for buff_key, eva_bonus in EVASION_BUFF_TABLE:
        if b.get(buff_key, 0) > 0:
            bonus += eva_bonus
    return bonus


def apply_damage_to_player(
    state: GameState, raw: float, is_phys: bool
) -> Tuple[int, str]:
    """Apply damage to player with shield/barrier/evasion/buffs.

    Args:
        state: Current game state with player stats and buffs
        raw: Raw damage value before mitigation
        is_phys: True if physical damage, False if magic damage

    Returns:
        Tuple of (actual_damage_taken, result_type) where result_type is one of:
        'barrier', 'shield', 'evade', 'undying', or 'hit'
    """
    if state.barrier > 0 and raw > 0:
        state.barrier -= 1
        return 0, "barrier"

    if state.shield > 0 and raw > 0:
        if state.shield >= raw:
            state.shield -= raw
            return 0, "shield"
        else:
            raw -= state.shield
            state.shield = 0

    if state.buffs.get("divineInterv", 0) > 0:
        state.buffs["divineInterv"] -= 1
        return 0, "barrier"

    if state.buffs.get("ethereal", 0) > 0:
        return 0, "evade"

    if state.buffs.get("flicker", 0) > 0:
        if random.random() < 0.5:
            state.buffs["flicker"] -= 1
            return 0, "evade"

    eva = state.evasion + _get_buff_evasion_bonus(state)
    if random.random() * 100 < eva:
        return 0, "evade"

    # DEF/mDEF with buff bonuses (statSwap swaps which defense is used)
    if state.buffs.get("statSwap", 0) > 0:
        base_df = state.m_def if is_phys else state.defense
    else:
        base_df = state.defense if is_phys else state.m_def
    bonus_pct = _get_buff_defense_bonus(state, is_phys)
    df = base_df * (1 + bonus_pct / 100)
    dr = df / (df + DEFENSE_DENOM)
    dmg = max(1, int(raw * (1 - dr)))

    if state.buffs.get("mirrorImg", 0) > 0:
        dmg = int(dmg * MIRROR_IMG_REDUCTION)

    if state.buffs.get("undying", 0) > 0 and dmg >= state.hp:
        state.hp = 1
        return dmg, "undying"

    if state.buffs.get("undyingPact", 0) > 0 and dmg >= state.hp:
        state.hp = 1
        return dmg, "undying"

    if state.buffs.get("eldritchRebirth", 0) > 0 and dmg >= state.hp:
        state.hp = max(1, int(state.max_hp * ELDRITCH_REBIRTH_HP_PCT))
        del state.buffs["eldritchRebirth"]
        return dmg, "undying"

    if state.buffs.get("finalStand", 0) > 0:
        return 0, "barrier"

    state.hp = max(0, state.hp - dmg)
    state.hits_taken += 1

    if state.buffs.get("bloodAura", 0) > 0:
        heal = int(dmg * BLOOD_AURA_LS_PCT)
        state.hp = min(state.max_hp, state.hp + heal)

    if state.buffs.get("retribAura", 0) > 0 and state.combat:
        reflected = int(dmg * RETRIB_AURA_REFLECT_PCT)
        state.combat.enemy.hp = max(0, state.combat.enemy.hp - reflected)

    if state.buffs.get("dreadnought", 0) > 0:
        atk_bonus = int(dmg * DREADNOUGHT_CONVERSION_PCT)
        state.temp_stats["str"] = state.temp_stats.get("str", 0) + atk_bonus
        state.recalc_stats()

    return dmg, "hit"

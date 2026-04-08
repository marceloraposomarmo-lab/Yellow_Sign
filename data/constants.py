"""Game constants: sprite/icon mappings, combat formulas, status effects, UI."""

MAX_ACTIVE_SKILLS = 4

# ═══════════════════════════════════════════
# COMBAT FORMULA CONSTANTS
# ═══════════════════════════════════════════

# Defense formula: damage_reduction = defense / (defense + DEFENSE_DENOM)
DEFENSE_DENOM = 50

# Crit multiplier base (modified by luck: crit_mult = CRIT_BASE_MULT + luck * 0.01)
CRIT_BASE_MULT = 1.8

# Random variance range for damage: base * (DMG_VARIANCE_LOW + random() * DMG_VARIANCE_RANGE)
DMG_VARIANCE_LOW = 0.85
DMG_VARIANCE_RANGE = 0.3

# Luck damage variance: base * (1 + random() * luck * LUCK_DMG_VARIANCE)
LUCK_DMG_VARIANCE = 0.005

# Enemy damage variance: atk * power * (ENEMY_VAR_LOW + random() * ENEMY_VAR_RANGE)
ENEMY_VAR_LOW = 0.85
ENEMY_VAR_RANGE = 0.3

# Flee base chance + agi * FLEE_AGI_MULTIPLIER
FLEE_BASE_CHANCE = 40
FLEE_AGI_MULTIPLIER = 2
FLEE_SUCCESS_MADNESS = 5
FLEE_FAIL_MADNESS = 3

# Execute threshold: bonus damage when enemy HP ratio < this
EXECUTE_HP_THRESHOLD = 0.25
EXECUTE_DAMAGE_MULT = 2.0

# Coin flip heal on tails: heals this fraction of max HP
COIN_FLIP_HEAL_FRAC = 0.25
COIN_FLIP_DAMAGE_MULT = 1.5

# Gambler damage range: multiplier = GAMBLE_MIN + random() * GAMBLE_RANGE
GAMBLE_MIN = 0.5
GAMBLE_RANGE = 2.5

# Doom kill threshold: instant kill if HP ratio < this when doom expires
DOOM_HP_THRESHOLD = 0.30

# Boss phase thresholds
BOSS_PHASE2_HP = 0.50
BOSS_PHASE3_HP = 0.25
BOSS_PHASE3_ATK_MULT = 1.4

# ═══════════════════════════════════════════
# STATUS EFFECT DOT PERCENTAGES (of max HP)
# ═══════════════════════════════════════════

BURNING_HP_PCT = 0.06
POISON_HP_PCT = 0.04
BLEEDING_HP_PCT = 0.05
POISON_MAX_STACKS = 5

# Debuff severity multipliers on enemy damage
FREEZING_PHYS_MULT = 0.75
PETRIFIED_MAGIC_MULT = 0.75
WEAKENED_ATK_MULT = 0.80
WEAKENED_DEF_MULT = 0.80

# Shock stun chance
SHOCK_STUN_CHANCE = 0.5

# Blind miss chance (enemy)
BLIND_MISS_CHANCE = 0.5

# ═══════════════════════════════════════════
# REGEN / HEAL-OVER-TIME PERCENTAGES
# ═══════════════════════════════════════════

REGEN_HP_PCT = 0.08
REGEN5_HP_PCT = 0.05
OATH_HP_PCT = 0.10
ADVANCE_FLOOR_HEAL_PCT = 0.10

# ═══════════════════════════════════════════
# DAMAGE BUFF MULTIPLIERS
# ═══════════════════════════════════════════

# Registry: buff_type → damage multiplier applied in _base_damage()
DAMAGE_BUFF_MULTIPLIERS = {
    "rage":        1.6,
    "atkCritUp":   1.4,
    "warpTime":    1.2,
    "madPower":    1.25,
    "darkPact":    1.3,
    "shadowMeld":  2.0,
    "eclipse":     1.3,
    "ethereal":    2.5,
}

# ═══════════════════════════════════════════
# DEFENSE BUFF REGISTRY
# ═══════════════════════════════════════════

# (buff_type, phys_pct, magic_pct) — applied in _get_buff_defense_bonus()
DEFENSE_BUFF_TABLE = [
    ("thoughtform",  30, 30),
    ("ironSkin",     60, 30),
    ("chant",        20, 20),
    ("innerFire",    15, 15),
    ("hallowed",     40, 40),
    ("fortress",     80, 80),
    ("bulwark",      60, 60),
    ("umbralAegis",  40,  0),
    ("mDefUp",        0, 50),
    ("wardAura",      0, 30),
    ("dreamShell",    0, 80),
    ("astral",        0, 60),
]

# (buff_type, evasion_bonus)
EVASION_BUFF_TABLE = [
    ("smokeScreen",  25),
    ("dreamVeil",    35),
    ("evasionUp",    40),
    ("dreamShell",   50),
    ("umbralAegis",  60),
    ("astral",       40),
    ("darkRegenBuff", 20),
    ("fadeBlack",    20),
    ("critUp",       15),
    ("luckyDodge",   35),
]

# ═══════════════════════════════════════════
# DEFENSE ON-TAKE-DAMAGE BUFFS
# ═══════════════════════════════════════════

# Mirror Images damage reduction multiplier
MIRROR_IMG_REDUCTION = 0.7

# Blood Aura lifesteal on damage taken
BLOOD_AURA_LS_PCT = 0.10

# Retribution Aura reflect percentage
RETRIB_AURA_REFLECT_PCT = 0.30

# Dreadnought: damage taken → STR bonus conversion
DREADNOUGHT_CONVERSION_PCT = 0.50

# Eldritch Rebirth: revive at this HP fraction
ELDRITCH_REBIRTH_HP_PCT = 0.30

# ═══════════════════════════════════════════
# CRIT BUFF BONUSES
# ═══════════════════════════════════════════

CRIT_UP_BONUS = 30
ATK_CRIT_UP_BONUS = 20

# ═══════════════════════════════════════════
# STAT / LEVEL-UP CONSTANTS
# ═══════════════════════════════════════════

XP_GROWTH_RATE = 1.3
LEVEL_UP_HP_BONUS = 15

# XP/Gold rewards per combat
XP_BASE = 12
XP_PER_FLOOR = 4
XP_BOSS_BONUS = 80
GOLD_BASE = 6
GOLD_PER_FLOOR = 2
GOLD_BOSS_BONUS = 50
GOLD_BASE_RANDOM_MAX = 8

# Madness changes
MADNESS_BOSS_KILL = -15
MADNESS_NORMAL_KILL = 3
MADNESS_MAX = 100

# Max barrier stacks
MAX_BARRIER_STACKS = 3

# Stat keys used throughout
STAT_KEYS = ("int", "str", "agi", "wis", "luck")

# ═══════════════════════════════════════════
# VISUAL DATA — Sprite & Icon mappings
# ═══════════════════════════════════════════

# Maps enemy names to their ASCII sprite keys
ENEMY_SPRITES = {
    "The All-Seeing Mass": "monster1",
    "The Skull Bearer": "monster3",
    "Storm Spawn": "monster4",
    "Carcosan Seer": "monster5",
    "Ember Horror": "monster6",
    "Hastur, The Spiral Beyond": "boss",
}

# Maps class ids to their sprite filenames
CLASS_SPRITES = {
    "scholar": "transparent-Int-basedClass",
    "brute": "transparent-Strenght-basedClass",
    "warden": "wis-character",
    "shadowblade": "transparent-Agi-basedClass",
    "mad_prophet": "transparent-luck-basedClass",
}

# Class display icons
CLASS_ICONS = {
    "scholar": "📖",
    "brute": "⚔",
    "warden": "🛡",
    "shadowblade": "🗡",
    "mad_prophet": "👁",
}

# Stat icon filenames (for rendering in stats screen / skill buttons)
STAT_ICONS = {
    "int": "Intelligence_Icon",
    "str": "Strenght_Icon",
    "agi": "Agility_Icon",
    "wis": "Wisdom_Icon",
    "luck": "Luck_Icon",
}


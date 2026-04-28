"""Game models: Item, Skill, StatusEffect, Enemy, CombatState, GameState, and item generation."""

import random
import math
from dataclasses import dataclass, field, asdict
from typing import List, Optional, Dict, Any, TypedDict
from data import (
    CLASSES,
    MAX_ACTIVE_SKILLS,
    RARITY_DATA,
    CURSED_DEBUFFS,
    ITEM_PREFIXES,
    WEAPON_TEMPLATES,
    ARMOR_TEMPLATES,
    ACCESSORY_TEMPLATES,
    BOOTS_TEMPLATES,
    RING_TEMPLATES,
    ENEMY_FLOOR_SCALING,
    ENEMY_MDEF_RATIO,
    ATK_BASE,
    ATK_STR_MULT,
    DEF_BASE,
    DEF_WIS_MULT,
    DEF_STR_MULT,
    MDEF_BASE,
    MDEF_WIS_MULT,
    MDEF_INT_MULT,
    CRIT_BASE,
    CRIT_AGI_MULT,
    EVA_BASE,
    EVA_AGI_MULT,
    ACC_BASE,
    ACC_MIN,
    ACC_MAX,
    ACC_AGI_MULT,
    HP_STR_MULT,
)

# ═══════════════════════════════════════════
# TypedDicts for data structures
# ═══════════════════════════════════════════


class ClassSkillData(TypedDict, total=False):
    """TypedDict for skill entries in CLASSES dict."""

    name: str
    icon: str
    unlock_lv: int
    desc: str
    formula: str
    type: str
    power: float
    stat: str
    stat2: Optional[str]
    stat2_mult: float
    cost: int
    cd: int
    tags: List[str]
    effect: Optional[str]
    effect2: Optional[str]
    effect3: Optional[str]
    duration: int
    armor_pierce: float
    lifesteal: float
    multihit: int
    scaling_low_hp: bool
    def_scaling: bool
    shield_calc: Optional[str]
    heal_calc: Optional[str]
    buff_type: Optional[str]
    buff_duration: int
    barrier_stacks: int
    consume_shield: bool
    shield_scaling: float
    hp_cost: float
    madness_scaling: bool
    madness_cost: int
    coin_flip: bool
    gamble: bool
    execute_bonus: bool
    guaranteed_crit: bool
    flat_crit_bonus: int
    luck_bonus: bool
    true_strike: bool
    extend_debuffs: bool
    random_effect: bool
    tier: int
    category: str
    stat_priority: List[str]
    starting: bool


class ClassData(TypedDict):
    """TypedDict for CLASSES dict entries."""

    name: str
    icon: str
    desc: str
    base_stats: Dict[str, int]
    hp_base: int
    hp_per_level: int
    skills: List[ClassSkillData]


class Item:
    """Represents an equippable item."""

    def __init__(self, name, slot, stats, rarity, debuffs=None):
        self.name = name
        self.slot = slot  # weapon, armor, accessory, boots, ringL, ringR
        self.stats = stats  # dict of stat bonuses
        self.rarity = rarity  # 1-4
        self.debuffs = debuffs or {}  # dict of stat penalties (cursed items)

    def stat_text(self):
        names = {
            "atk": "ATK",
            "def": "DEF",
            "int": "INT",
            "str": "STR",
            "agi": "AGI",
            "wis": "WIS",
            "luck": "LUK",
            "hp": "HP",
        }
        parts = [f"{names.get(k, k)}+{v}" for k, v in self.stats.items()]
        return " ".join(parts)

    def debuff_text(self):
        if not self.debuffs:
            return ""
        names = {
            "atk": "ATK",
            "def": "DEF",
            "int": "INT",
            "str": "STR",
            "agi": "AGI",
            "wis": "WIS",
            "luck": "LUK",
            "hp": "HP",
        }
        parts = [f"-{v} {names.get(k, k)}" for k, v in self.debuffs.items()]
        return " ".join(parts)

    def rarity_name(self):
        return RARITY_DATA.get(self.rarity, RARITY_DATA[1])["name"]

    def to_dict(self):
        return {
            "name": self.name,
            "slot": self.slot,
            "stats": self.stats,
            "rarity": self.rarity,
            "debuffs": self.debuffs,
        }

    @classmethod
    def from_dict(cls, d):
        return cls(d["name"], d["slot"], d["stats"], d["rarity"], d.get("debuffs"))


@dataclass
class Skill:
    """Represents a player skill/ability."""

    name: str
    icon: str = "?"
    unlock_lv: int = 1
    desc: str = ""
    formula: str = ""
    type: str = "physical"
    power: float = 1.0
    stat: str = "str"
    stat2: Optional[str] = None
    stat2_mult: float = 0
    cost: int = 0
    cd: int = 0
    current_cd: int = 0
    tags: List[str] = field(default_factory=list)
    effect: Optional[str] = None
    effect2: Optional[str] = None
    effect3: Optional[str] = None
    duration: int = 2
    armor_pierce: float = 0
    lifesteal: float = 0
    multihit: int = 1
    scaling_low_hp: bool = False
    def_scaling: bool = False
    shield_calc: Optional[str] = None
    heal_calc: Optional[str] = None
    buff_type: Optional[str] = None
    buff_duration: int = 3
    barrier_stacks: int = 0
    consume_shield: bool = False
    shield_scaling: float = 0
    hp_cost: float = 0
    madness_scaling: bool = False
    madness_cost: int = 0
    coin_flip: bool = False
    gamble: bool = False
    execute_bonus: bool = False
    guaranteed_crit: bool = False
    flat_crit_bonus: int = 0
    luck_bonus: bool = False
    true_strike: bool = False
    extend_debuffs: bool = False
    random_effect: bool = False
    tier: int = 1
    category: str = "offensive"
    stat_priority: List[str] = field(default_factory=list)
    starting: bool = False

    def to_dict(self):
        d = asdict(self)
        # Exclude transient/runtime fields from serialization
        d.pop("starting", None)
        return d

    @classmethod
    def from_dict(cls, d):
        return cls(**d)


@dataclass
class PlayerIdentity:
    """Who the player is: class choice and level."""

    class_id: Optional[str] = None
    class_name: str = ""
    level: int = 1


@dataclass
class PlayerProgression:
    """Run-level progression: floors, kills, gold, XP, madness."""

    floor: int = 1
    max_floor: int = 20
    kills: int = 0
    rooms_explored: int = 0
    gold: int = 15
    xp: int = 0
    xp_next: int = 20
    madness: float = 0


@dataclass
class CombatBuffs:
    """Combat-only ephemeral state, cleared on combat start."""

    shield: int = 0
    barrier: int = 0
    rage: bool = False
    buffs: Dict[str, int] = field(default_factory=dict)
    temp_stats: Dict[str, int] = field(default_factory=dict)
    hits_taken: int = 0


class StatusEffect:
    """Represents a status effect on player or enemy."""

    def __init__(self, effect_type, duration):
        self.type = effect_type  # burning, poisoned, shocked, blinded, frozen, petrified, weakened, bleeding
        self.duration = duration
        self.stacks = 1  # for poison stacking

    def to_dict(self):
        return {"type": self.type, "duration": self.duration, "stacks": self.stacks}

    @classmethod
    def from_dict(cls, d):
        se = cls(d["type"], d["duration"])
        se.stacks = d.get("stacks", 1)
        return se


def has_status(target, status_type):
    """Check if entity has a specific status effect."""
    return any(s.type == status_type for s in target.statuses)


def apply_status(target, effect_type, duration):
    """Apply a status effect to an entity. Refreshes duration if already present."""
    existing = next((s for s in target.statuses if s.type == effect_type), None)
    if existing:
        existing.duration = max(existing.duration, duration)
    else:
        target.statuses.append(StatusEffect(effect_type, duration))


class CombatState:
    """Holds state for a combat encounter."""

    def __init__(self, enemy, is_boss):
        self.enemy = enemy
        self.is_boss = is_boss
        self.turn = "player"
        self.log = []  # list of (text, type)
        self.phase2 = False
        self.phase3 = False
        self.turn_count = 0
        self.next_enemy_skill = None  # pre-selected enemy intent
        self.last_enemy_skill = None  # for copyAttack (Living Shadow)

    def add_log(self, text, log_type="info"):
        self.log.append((text, log_type))


class Enemy:
    """Represents an enemy in combat."""

    def __init__(self, data, floor):
        self.name = data["name"]
        self.type = data.get("type", "Unknown")
        self.desc = data.get("desc", "")
        self.level_range = data.get("level_range", [1, 20])
        ls = 1 + (floor - 1) * ENEMY_FLOOR_SCALING
        self.max_hp = int((60 + floor * 12) * data["hp_mult"] * ls)
        self.hp = self.max_hp
        self.atk = int((6 + floor * 2) * data["atk_mult"] * ls)
        self.base_atk = self.atk
        self.defense = int((2 + floor * 1.0) * data["def_mult"] * ls)
        self.m_def = int(self.defense * ENEMY_MDEF_RATIO)
        self.skills = list(data.get("skills", []))
        self.statuses = []
        self.stunned = False


class GameState:
    """Main game state container.

    Composes three sub-objects for grouped state:
      - identity: PlayerIdentity (class, name, level)
      - progression: PlayerProgression (floor, kills, gold, xp, madness)
      - combat_buffs: CombatBuffs (shield, barrier, rage, buffs, temp_stats, hits_taken)

    Backward-compatible properties delegate to sub-objects so screen code
    can keep using state.class_id, state.floor, state.gold, etc.
    """

    def __init__(self):
        # --- Sub-objects ---
        self.identity = PlayerIdentity()
        self.progression = PlayerProgression()
        self.combat_buffs = CombatBuffs()

        # --- Flat combat stats (recalculated by recalc_stats) ---
        self.hp = 0
        self.max_hp = 0
        self.stats = {}
        self.base_stats = {}
        self.atk = 0
        self.defense = 0
        self.m_def = 0
        self.crit = 0
        self.evasion = 0
        self.luck = 5
        self.accuracy = 90

        # --- Equipment & skills ---
        self.equipment = {
            "weapon": None,
            "accessory": None,
            "armor": None,
            "boots": None,
            "ringL": None,
            "ringR": None,
        }
        self.inventory = []
        self.all_skills = []
        self.active_skills = []
        self.statuses = []
        self.combat = None
        self.pending_levelup_skills = []

    # ── Identity properties ──────────────────────────────────────────

    @property
    def class_id(self):
        return self.identity.class_id

    @class_id.setter
    def class_id(self, v):
        self.identity.class_id = v

    @property
    def class_name(self):
        return self.identity.class_name

    @class_name.setter
    def class_name(self, v):
        self.identity.class_name = v

    @property
    def level(self):
        return self.identity.level

    @level.setter
    def level(self, v):
        self.identity.level = v

    # ── Progression properties ───────────────────────────────────────

    @property
    def floor(self):
        return self.progression.floor

    @floor.setter
    def floor(self, v):
        self.progression.floor = v

    @property
    def max_floor(self):
        return self.progression.max_floor

    @max_floor.setter
    def max_floor(self, v):
        self.progression.max_floor = v

    @property
    def kills(self):
        return self.progression.kills

    @kills.setter
    def kills(self, v):
        self.progression.kills = v

    @property
    def rooms_explored(self):
        return self.progression.rooms_explored

    @rooms_explored.setter
    def rooms_explored(self, v):
        self.progression.rooms_explored = v

    @property
    def gold(self):
        return self.progression.gold

    @gold.setter
    def gold(self, v):
        self.progression.gold = v

    @property
    def xp(self):
        return self.progression.xp

    @xp.setter
    def xp(self, v):
        self.progression.xp = v

    @property
    def xp_next(self):
        return self.progression.xp_next

    @xp_next.setter
    def xp_next(self, v):
        self.progression.xp_next = v

    @property
    def madness(self):
        return self.progression.madness

    @madness.setter
    def madness(self, v):
        self.progression.madness = v

    # ── Combat buff properties ───────────────────────────────────────

    @property
    def shield(self):
        return self.combat_buffs.shield

    @shield.setter
    def shield(self, v):
        self.combat_buffs.shield = v

    @property
    def barrier(self):
        return self.combat_buffs.barrier

    @barrier.setter
    def barrier(self, v):
        self.combat_buffs.barrier = v

    @property
    def rage(self):
        return self.combat_buffs.rage

    @rage.setter
    def rage(self, v):
        self.combat_buffs.rage = v

    @property
    def buffs(self):
        return self.combat_buffs.buffs

    @buffs.setter
    def buffs(self, v):
        self.combat_buffs.buffs = v

    @property
    def temp_stats(self):
        return self.combat_buffs.temp_stats

    @temp_stats.setter
    def temp_stats(self, v):
        self.combat_buffs.temp_stats = v

    @property
    def hits_taken(self):
        return self.combat_buffs.hits_taken

    @hits_taken.setter
    def hits_taken(self, v):
        self.combat_buffs.hits_taken = v

    # ── Core methods ─────────────────────────────────────────────────

    def init_from_class(self, class_id):
        """Initialize game state for a chosen class."""
        cls = CLASSES[class_id]
        self.class_id = class_id
        self.class_name = cls["name"]
        self.base_stats = dict(cls["base_stats"])
        self.stats = dict(self.base_stats)
        self.max_hp = cls["hp_base"]
        self.hp = self.max_hp
        self.all_skills = [Skill(**s) for s in cls["skills"]]
        self.active_skills = [Skill(**s) for s in cls["skills"] if s.get("starting", False)]
        self.recalc_stats()
        self.hp = self.max_hp

    def recalc_stats(self):
        """Recalculate derived stats from base stats and equipment."""
        cls = CLASSES[self.class_id]
        s = dict(self.base_stats)
        bonus_atk = 0
        bonus_def = 0
        bonus_hp = 0

        for slot in ["weapon", "accessory", "armor", "boots", "ringL", "ringR"]:
            item = self.equipment.get(slot)
            if not item:
                continue
            for k, v in item.stats.items():
                if k in ("int", "str", "agi", "wis", "luck"):
                    s[k] = s.get(k, 0) + v
                elif k == "atk":
                    bonus_atk += v
                elif k == "def":
                    bonus_def += v
                elif k == "hp":
                    bonus_hp += v
            if item.debuffs:
                for k, v in item.debuffs.items():
                    if k in ("int", "str", "agi", "wis", "luck"):
                        s[k] = max(1, s.get(k, 1) - v)
                    elif k == "atk":
                        bonus_atk -= v
                    elif k == "def":
                        bonus_def -= v
                    elif k == "hp":
                        bonus_hp -= v

        # Apply temporary combat stat bonuses
        for k, v in self.temp_stats.items():
            if k in ("int", "str", "agi", "wis", "luck"):
                s[k] = s.get(k, 0) + v

        self.stats = s
        self.max_hp = max(
            1,
            cls["hp_base"] + cls["hp_per_level"] * (self.level - 1) + int(s["str"] * HP_STR_MULT) + bonus_hp,
        )
        self.atk = max(1, ATK_BASE + int(s["str"] * ATK_STR_MULT) + bonus_atk)
        self.defense = max(0, DEF_BASE + int(s["wis"] * DEF_WIS_MULT) + int(s["str"] * DEF_STR_MULT) + bonus_def)
        self.m_def = max(0, MDEF_BASE + int(s["wis"] * MDEF_WIS_MULT) + int(s["int"] * MDEF_INT_MULT))
        self.crit = max(0, CRIT_BASE + s["agi"] * CRIT_AGI_MULT)
        self.evasion = max(0, EVA_BASE + s["agi"] * EVA_AGI_MULT)
        self.luck = max(1, s.get("luck", 5))
        self.accuracy = min(ACC_MAX, max(ACC_MIN, ACC_BASE + s["agi"] * ACC_AGI_MULT))
        if self.hp > self.max_hp:
            self.hp = self.max_hp

    def add_madness(self, amount):
        """Add madness, returning True if game over triggered."""
        self.madness = max(0, min(100, self.madness + amount))
        if self.buffs.get("madImmune", 0) > 0:
            return False
        return self.madness >= 100

    def check_level_up(self):
        """Check and process level ups. Returns True if leveled up."""
        leveled = False
        while self.xp >= self.xp_next:
            self.xp -= self.xp_next
            self.level += 1
            self.xp_next = int(self.xp_next * 1.3)
            self.recalc_stats()
            self.hp = min(self.max_hp, self.hp + 15)
            leveled = True

        if leveled:
            # Determine tier based on level
            if self.level <= 5:
                tier = 1
            elif self.level <= 10:
                tier = 2
            else:
                tier = 3

            # Filter: correct tier, not already learned
            available = [
                s for s in self.all_skills if s.tier == tier and not any(a.name == s.name for a in self.active_skills)
            ]

            if not available:
                # Fallback: any tier not already learned
                available = [s for s in self.all_skills if not any(a.name == s.name for a in self.active_skills)]

            if available:
                # Weighted selection based on class stat priorities
                cls_data = CLASSES[self.class_id]
                primary_stat = max(cls_data["base_stats"], key=cls_data["base_stats"].get)
                second_stat = sorted(cls_data["base_stats"].items(), key=lambda x: x[1], reverse=True)[1][0]

                weighted_pool = []
                for s in available:
                    weight = 1
                    if hasattr(s, "stat_priority") and s.stat_priority:
                        if primary_stat in s.stat_priority:
                            weight = 3
                        elif second_stat in s.stat_priority:
                            weight = 2
                    weighted_pool.extend([s] * weight)

                random.shuffle(weighted_pool)

                chosen = []
                for s in weighted_pool:
                    if len(chosen) >= 2:
                        break
                    if not any(c.name == s.name for c in chosen):
                        chosen.append(s)

                # Ensure we have 2 if possible
                if len(chosen) < 2 and len(available) >= 2:
                    remaining = [s for s in available if not any(c.name == s.name for c in chosen)]
                    if remaining:
                        chosen.append(random.choice(remaining))

                self.pending_levelup_skills = chosen[:2]
            else:
                self.pending_levelup_skills = []

        return leveled

    def equip_item(self, item):
        """Equip an item, returning the previously equipped item (or None)."""
        prev = self.equipment.get(item.slot)
        self.equipment[item.slot] = item
        self.recalc_stats()
        return prev

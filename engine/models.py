"""Game models: Item, Skill, StatusEffect, Enemy, CombatState, GameState, and item generation."""

import random
import math
from data import (
    CLASSES, MAX_ACTIVE_SKILLS,
    RARITY_DATA, CURSED_DEBUFFS, ITEM_PREFIXES,
    WEAPON_TEMPLATES, ARMOR_TEMPLATES, ACCESSORY_TEMPLATES,
    BOOTS_TEMPLATES, RING_TEMPLATES,
)


class Item:
    """Represents an equippable item."""
    def __init__(self, name, slot, stats, rarity, debuffs=None):
        self.name = name
        self.slot = slot  # weapon, armor, accessory, boots, ringL, ringR
        self.stats = stats  # dict of stat bonuses
        self.rarity = rarity  # 1-4
        self.debuffs = debuffs or {}  # dict of stat penalties (cursed items)

    def stat_text(self):
        names = {"atk": "ATK", "def": "DEF", "int": "INT", "str": "STR", "agi": "AGI", "wis": "WIS", "luck": "LUK", "hp": "HP"}
        parts = [f"{names.get(k, k)}+{v}" for k, v in self.stats.items()]
        return " ".join(parts)

    def debuff_text(self):
        if not self.debuffs:
            return ""
        names = {"atk": "ATK", "def": "DEF", "int": "INT", "str": "STR", "agi": "AGI", "wis": "WIS", "luck": "LUK", "hp": "HP"}
        parts = [f"-{v} {names.get(k, k)}" for k, v in self.debuffs.items()]
        return " ".join(parts)

    def rarity_name(self):
        return RARITY_DATA.get(self.rarity, RARITY_DATA[1])["name"]

    def to_dict(self):
        return {
            "name": self.name, "slot": self.slot, "stats": self.stats,
            "rarity": self.rarity, "debuffs": self.debuffs,
        }

    @classmethod
    def from_dict(cls, d):
        return cls(d["name"], d["slot"], d["stats"], d["rarity"], d.get("debuffs"))


class Skill:
    """Represents a player skill/ability."""
    def __init__(self, data):
        self.name = data["name"]
        self.icon = data.get("icon", "?")
        self.unlock_lv = data.get("unlock_lv", 1)
        self.desc = data.get("desc", "")
        self.formula = data.get("formula", "")
        self.type = data.get("type", "physical")
        self.power = data.get("power", 1.0)
        self.stat = data.get("stat", "str")
        self.stat2 = data.get("stat2")
        self.stat2_mult = data.get("stat2_mult", 0)
        self.cost = data.get("cost", 0)
        self.cd = data.get("cd", 0)
        self.current_cd = 0
        self.tags = data.get("tags", [])
        self.effect = data.get("effect")
        self.effect2 = data.get("effect2")
        self.effect3 = data.get("effect3")
        self.duration = data.get("duration", 2)
        self.armor_pierce = data.get("armor_pierce", 0)
        self.lifesteal = data.get("lifesteal", 0)
        self.multihit = data.get("multihit", 1)
        self.scaling_low_hp = data.get("scaling_low_hp", False)
        self.def_scaling = data.get("def_scaling", False)
        self.shield_calc = data.get("shield_calc")
        self.heal_calc = data.get("heal_calc")
        self.buff_type = data.get("buff_type")
        self.buff_duration = data.get("buff_duration", 3)
        self.barrier_stacks = data.get("barrier_stacks", 0)
        self.consume_shield = data.get("consume_shield", False)
        self.shield_scaling = data.get("shield_scaling", 0)
        self.hp_cost = data.get("hp_cost", 0)
        self.madness_scaling = data.get("madness_scaling", False)
        self.madness_cost = data.get("madness_cost", 0)
        self.coin_flip = data.get("coin_flip", False)
        self.gamble = data.get("gamble", False)
        self.execute_bonus = data.get("execute_bonus", False)
        self.guaranteed_crit = data.get("guaranteed_crit", False)
        self.flat_crit_bonus = data.get("flat_crit_bonus", 0)
        self.luck_bonus = data.get("luck_bonus", False)
        self.true_strike = data.get("true_strike", False)
        self.extend_debuffs = data.get("extend_debuffs", False)
        self.random_effect = data.get("random_effect", False)
        self.tier = data.get("tier", 1)
        self.category = data.get("category", "offensive")
        self.stat_priority = data.get("stat_priority", [])
        self.starting = data.get("starting", False)

    def to_dict(self):
        return {
            "name": self.name, "icon": self.icon, "unlock_lv": self.unlock_lv,
            "desc": self.desc, "formula": self.formula, "type": self.type,
            "power": self.power, "stat": self.stat, "stat2": self.stat2,
            "stat2_mult": self.stat2_mult, "cost": self.cost, "cd": self.cd,
            "current_cd": self.current_cd, "tags": self.tags,
            "effect": self.effect, "effect2": self.effect2, "effect3": self.effect3,
            "duration": self.duration, "armor_pierce": self.armor_pierce,
            "lifesteal": self.lifesteal, "multihit": self.multihit,
            "scaling_low_hp": self.scaling_low_hp, "def_scaling": self.def_scaling,
            "shield_calc": self.shield_calc, "heal_calc": self.heal_calc,
            "buff_type": self.buff_type, "buff_duration": self.buff_duration,
            "barrier_stacks": self.barrier_stacks, "consume_shield": self.consume_shield,
            "shield_scaling": self.shield_scaling, "hp_cost": self.hp_cost,
            "madness_scaling": self.madness_scaling, "madness_cost": self.madness_cost,
            "coin_flip": self.coin_flip, "gamble": self.gamble,
            "execute_bonus": self.execute_bonus, "guaranteed_crit": self.guaranteed_crit,
            "flat_crit_bonus": self.flat_crit_bonus, "luck_bonus": self.luck_bonus,
            "true_strike": self.true_strike, "extend_debuffs": self.extend_debuffs,
            "random_effect": self.random_effect,
            "tier": self.tier, "category": self.category, "stat_priority": self.stat_priority,
        }

    @classmethod
    def from_dict(cls, d):
        s = cls(d)
        s.current_cd = d.get("current_cd", 0)
        s.tier = d.get("tier", 1)
        s.category = d.get("category", "offensive")
        s.stat_priority = d.get("stat_priority", [])
        return s


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

    def add_log(self, text, log_type="info"):
        self.log.append((text, log_type))


class Enemy:
    """Represents an enemy in combat."""
    def __init__(self, data, floor):
        self.name = data["name"]
        self.type = data.get("type", "Unknown")
        self.desc = data.get("desc", "")
        self.level_range = data.get("level_range", [1, 20])
        ls = 1 + (floor - 1) * 0.08
        self.max_hp = int((60 + floor * 12) * data["hp_mult"] * ls)
        self.hp = self.max_hp
        self.atk = int((6 + floor * 2) * data["atk_mult"] * ls)
        self.base_atk = self.atk
        self.defense = int((2 + floor * 1.0) * data["def_mult"] * ls)
        self.m_def = int(self.defense * 0.8)
        self.skills = list(data.get("skills", []))
        self.statuses = []
        self.stunned = False


class GameState:
    """Main game state container."""

    def __init__(self):
        self.class_id = None
        self.class_name = ""
        self.level = 1
        self.floor = 1
        self.max_floor = 20
        self.hp = 0
        self.max_hp = 0
        self.shield = 0
        self.barrier = 0
        self.stats = {}
        self.base_stats = {}
        self.atk = 0
        self.defense = 0
        self.m_def = 0
        self.crit = 0
        self.evasion = 0
        self.luck = 5
        self.accuracy = 90
        self.madness = 0
        self.gold = 15
        self.xp = 0
        self.xp_next = 20
        self.kills = 0
        self.rooms_explored = 0
        self.equipment = {
            "weapon": None, "accessory": None, "armor": None,
            "boots": None, "ringL": None, "ringR": None,
        }
        self.inventory = []
        self.all_skills = []
        self.active_skills = []
        self.statuses = []
        self.rage = False
        self.combat = None
        self.buffs = {}  # buff_type -> remaining turns
        self.temp_stats = {}  # stat -> bonus amount (combat-only, cleared on combat end)
        self.hits_taken = 0
        self.pending_levelup_skills = []

    def init_from_class(self, class_id):
        """Initialize game state for a chosen class."""
        cls = CLASSES[class_id]
        self.class_id = class_id
        self.class_name = cls["name"]
        self.base_stats = dict(cls["base_stats"])
        self.stats = dict(self.base_stats)
        self.max_hp = cls["hp_base"]
        self.hp = self.max_hp
        self.all_skills = [Skill(s) for s in cls["skills"]]
        self.active_skills = [Skill(s) for s in cls["skills"] if s.get("starting", False)]
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
        self.max_hp = max(1, cls["hp_base"] + cls["hp_per_level"] * (self.level - 1) + int(s["str"] * 2.5) + bonus_hp)
        self.atk = max(1, 5 + int(s["str"] * 0.8) + bonus_atk)
        self.defense = max(0, 2 + int(s["wis"] * 0.3) + int(s["str"] * 0.3) + bonus_def)
        self.m_def = max(0, 3 + int(s["wis"] * 0.6) + int(s["int"] * 0.3))
        self.crit = max(0, 5 + s["agi"] * 1.5)
        self.evasion = max(0, 3 + s["agi"] * 1.2)
        self.luck = max(1, s.get("luck", 5))
        self.accuracy = min(98, max(50, 90 + s["agi"] * 0.5))
        if self.hp > self.max_hp:
            self.hp = self.max_hp

    def add_madness(self, amount):
        """Add madness, returning True if game over triggered."""
        self.madness = max(0, min(100, self.madness + amount))
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
                s for s in self.all_skills
                if s.tier == tier and
                not any(a.name == s.name for a in self.active_skills)
            ]

            if not available:
                # Fallback: any tier not already learned
                available = [
                    s for s in self.all_skills
                    if not any(a.name == s.name for a in self.active_skills)
                ]

            if available:
                # Weighted selection based on class stat priorities
                cls_data = CLASSES[self.class_id]
                primary_stat = max(cls_data["base_stats"], key=cls_data["base_stats"].get)
                second_stat = sorted(cls_data["base_stats"].items(), key=lambda x: x[1], reverse=True)[1][0]

                weighted_pool = []
                for s in available:
                    weight = 1
                    if hasattr(s, 'stat_priority') and s.stat_priority:
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



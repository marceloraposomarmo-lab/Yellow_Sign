"""
THE KING IN YELLOW — Game Engine
Core game logic: combat, leveling, skills, floor progression, items.
"""

import random
import math
from game_data import (
    CLASSES, ENEMIES, BOSS, MAX_ACTIVE_SKILLS,
    RARITY_DATA, CURSED_DEBUFFS, ITEM_PREFIXES,
    WEAPON_TEMPLATES, ARMOR_TEMPLATES, ACCESSORY_TEMPLATES,
    BOOTS_TEMPLATES, RING_TEMPLATES, EVENTS, TRAPS,
    FLOOR_NARRATIVES, PATH_TEMPLATES,
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
        self.active_skills = [Skill(s) for s in cls["skills"] if s["unlock_lv"] <= 1]
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


# ═══════════════════════════════════════════
# ITEM GENERATION
# ═══════════════════════════════════════════

def determine_rarity(floor, luck):
    r = random.random() * 100 + (luck - 5) * 1.5 + floor * 0.8
    if r >= 96:
        return 4
    elif r >= 80:
        return 3
    elif r >= 55:
        return 2
    return 1


def generate_item(floor, item_type=None, luck=5):
    """Generate a random item."""
    rarity = determine_rarity(floor, luck)
    rd = RARITY_DATA[rarity]
    fs = 1 + (floor - 1) * 0.06

    prefix = random.choice(ITEM_PREFIXES[rarity])

    # Choose template
    all_templates = {
        "weapon": WEAPON_TEMPLATES,
        "armor": ARMOR_TEMPLATES,
        "accessory": ACCESSORY_TEMPLATES,
        "boots": BOOTS_TEMPLATES,
        "ring": RING_TEMPLATES,
    }

    if item_type and item_type in all_templates:
        pool = all_templates[item_type]
    else:
        pool = []
        for templates in all_templates.values():
            pool.extend(templates)

    template = random.choice(pool)
    slot = template["slot"]
    if slot == "ring":
        slot = random.choice(["ringL", "ringR"])

    # Build stats
    stats = {}
    for k, v in template["base"].items():
        stats[k] = math.ceil(v * rd["stat_mul"] * fs)

    # Random bonus stats
    bonus_count = rd["stat_range"][0] + random.randint(0, rd["stat_range"][1] - rd["stat_range"][0])
    used = set(stats.keys())
    pool_shuffled = list(template["bonus_pool"])
    random.shuffle(pool_shuffled)
    all_stat_keys = ["int", "str", "agi", "wis", "luck", "atk", "def", "hp"]

    for i in range(bonus_count):
        if i < len(pool_shuffled):
            sk = pool_shuffled[i]
        else:
            available = [k for k in all_stat_keys if k not in used]
            sk = random.choice(available) if available else random.choice(all_stat_keys)
        used.add(sk)
        stats[sk] = stats.get(sk, 0) + math.ceil((2 + random.random() * 4) * rd["stat_mul"] * fs)

    # Cursed debuffs
    debuffs = None
    if rarity == 4:
        debuffs = {}
        dc = 1 + random.randint(0, 1)
        sd = list(CURSED_DEBUFFS)
        random.shuffle(sd)
        for i in range(dc):
            debuffs[sd[i]["stat"]] = math.ceil((3 + random.random() * 5) * fs)

    return Item(f"{prefix} {template['name']}", slot, stats, rarity, debuffs)


# ═══════════════════════════════════════════
# COMBAT SYSTEM
# ═══════════════════════════════════════════

def start_combat(state, is_boss=False):
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
    state.hits_taken = 0
    for sk in state.active_skills:
        sk.current_cd = 0
    state.combat.add_log(f"{enemy.name} appears!", "info")
    if enemy.desc:
        state.combat.add_log(enemy.desc, "info")


def calc_player_damage(state, skill):
    """Calculate raw player damage for a skill."""
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
        hr = state.hp / state.max_hp
        bd *= 1 + (1 - hr) * 2.0

    if skill.madness_scaling:
        bd *= (1 + state.madness / 100)

    if state.rage:
        bd *= 1.6
    if state.buffs.get("atkCritUp", 0) > 0:
        bd *= 1.4
    if state.buffs.get("warpTime", 0) > 0:
        bd *= 1.2
    if state.buffs.get("madPower", 0) > 0:
        bd *= 1.25
    if state.buffs.get("darkPact", 0) > 0:
        bd *= 1.3
    if state.buffs.get("shadowMeld", 0) > 0:
        bd *= 2.0
    if state.buffs.get("eclipse", 0) > 0:
        bd *= 1.3

    # Random variance
    bd *= (1 + random.random() * state.luck * 0.005)
    bd *= (0.85 + random.random() * 0.3)

    if skill.multihit and skill.multihit > 1:
        bd *= skill.multihit

    if skill.gamble:
        gm = 0.5 + random.random() * 2.5
        bd *= gm

    if skill.coin_flip:
        if random.random() < 0.5:
            bd = 0
            h = int(state.max_hp * 0.25)
            state.hp = min(state.max_hp, state.hp + h)
        else:
            bd *= 1.5

    if skill.execute_bonus and state.combat:
        e = state.combat.enemy
        if e and e.hp / e.max_hp < 0.25:
            bd *= 2.0

    if skill.luck_bonus:
        bd *= (1 + state.luck * 0.02)

    return int(bd)


def apply_damage_to_enemy(state, raw, skill):
    """Apply damage to enemy, accounting for defense and crits."""
    e = state.combat.enemy
    df = e.defense
    if skill and skill.type in ("magic", "magic_debuff", "mixed_magic"):
        df = e.m_def
    if skill and skill.armor_pierce:
        df *= (1 - skill.armor_pierce)
    dr = df / (df + 50)
    dmg = max(1, int(raw * (1 - dr)))

    is_crit = False
    cc = state.crit
    if state.buffs.get("critUp", 0) > 0:
        cc += 30
    if state.buffs.get("atkCritUp", 0) > 0:
        cc += 20
    if skill and skill.flat_crit_bonus:
        cc += skill.flat_crit_bonus
    if skill and skill.guaranteed_crit:
        is_crit = True
    elif random.random() * 100 < cc:
        is_crit = True

    if is_crit:
        dmg = int(dmg * (1.8 + state.luck * 0.01))

    dmg = max(1, dmg)
    e.hp = max(0, e.hp - dmg)
    return dmg, is_crit


def apply_damage_to_player(state, raw, is_phys):
    """Apply damage to player with shield/barrier/evasion."""
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

    if random.random() * 100 < state.evasion:
        return 0, "evade"

    df = state.defense if is_phys else state.m_def
    dr = df / (df + 50)
    dmg = max(1, int(raw * (1 - dr)))

    if state.buffs.get("undying", 0) > 0 and dmg >= state.hp:
        state.hp = 1
        return dmg, "undying"

    state.hp = max(0, state.hp - dmg)
    state.hits_taken += 1
    return dmg, "hit"


def has_status(target, status_type):
    return any(s.type == status_type for s in target.statuses)


def apply_status(target, effect_type, duration):
    existing = next((s for s in target.statuses if s.type == effect_type), None)
    if existing:
        existing.duration = max(existing.duration, duration)
    else:
        target.statuses.append(StatusEffect(effect_type, duration))


def process_status_effects(target, is_player, state):
    """Process burning, poison, bleeding, etc. Returns list of log messages."""
    logs = []
    to_remove = []
    for st in target.statuses:
        if st.type == "burning":
            d = int(target.max_hp * 0.06) if hasattr(target, 'max_hp') else int(state.max_hp * 0.06)
            target.hp = max(0, target.hp - d)
            who = "You burn" if is_player else f"{target.name} burns"
            logs.append((f"{who} for {d}!", "damage"))
        elif st.type == "poisoned":
            stacks = getattr(st, 'stacks', 1)
            d = int(target.max_hp * 0.04 * stacks) if hasattr(target, 'max_hp') else int(state.max_hp * 0.04 * stacks)
            target.hp = max(0, target.hp - d)
            who = "Poison" if is_player else f"Poison on {target.name}"
            logs.append((f"{who} deals {d}! ({stacks} stacks)", "damage"))
        elif st.type == "bleeding":
            d = int(target.max_hp * 0.05) if hasattr(target, 'max_hp') else int(state.max_hp * 0.05)
            target.hp = max(0, target.hp - d)
            who = "You bleed" if is_player else f"{target.name} bleeds"
            logs.append((f"{who} for {d}!", "damage"))

        st.duration -= 1
        if st.duration <= 0:
            to_remove.append(st)

    for st in to_remove:
        target.statuses.remove(st)
        if not is_player:
            logs.append((f"{st.type} wears off from {target.name}.", "info"))
        else:
            logs.append((f"{st.type} wears off.", "info"))
    return logs


def tick_player_buffs(state):
    """Tick player buff durations and apply regen/oath effects."""
    logs = []
    to_remove = []
    for key in list(state.buffs.keys()):
        state.buffs[key] -= 1
        if key == "regen" and state.buffs[key] >= 0:
            h = int(state.max_hp * 0.08)
            state.hp = min(state.max_hp, state.hp + h)
            logs.append((f"Regen heals {h} HP.", "heal"))
        elif key == "oath" and state.buffs[key] >= 0:
            h = int(state.max_hp * 0.10)
            state.hp = min(state.max_hp, state.hp + h)
            logs.append((f"Oath heals {h} HP.", "heal"))
        if state.buffs[key] <= 0:
            to_remove.append(key)

    for key in to_remove:
        del state.buffs[key]
        logs.append((f"{key} expired.", "info"))
    return logs


def player_use_skill(state, skill_index):
    """Player uses a skill. Returns list of (text, type) log messages."""
    logs = []
    skill = state.active_skills[skill_index]
    c = state.combat
    e = c.enemy

    if skill.current_cd > 0:
        return [("That ability is on cooldown!", "info")]

    if skill.cost > 0:
        state.madness = min(100, state.madness + skill.cost)
        if state.madness >= 100:
            return [("Your mind shatters from the madness cost!", "damage")]

    if skill.madness_cost > 0:
        state.madness = max(0, state.madness - skill.madness_cost)

    if skill.hp_cost > 0:
        hp_loss = int(state.max_hp * skill.hp_cost)
        state.hp = max(1, state.hp - hp_loss)
        logs.append((f"Sacrificed {hp_loss} HP!", "damage"))

    skill.current_cd = skill.cd + 1

    # Handle non-damage skills
    if skill.type == "self_heal":
        h = 0
        if skill.heal_calc == "int2_buff":
            h = int(state.stats["int"] * 2)
            state.hp = min(state.max_hp, state.hp + h)
            state.base_stats["int"] += 3
            state.recalc_stats()
            logs.append((f"Forbidden Knowledge heals {h} HP! INT+3!", "heal"))
        elif skill.heal_calc == "missing_hp":
            missing = 1 - state.hp / state.max_hp
            h = int(missing * state.max_hp * 0.6)
            state.hp = min(state.max_hp, state.hp + h)
            logs.append((f"Adrenaline Surge heals {h} HP!", "heal"))
        elif skill.heal_calc == "wis2_10":
            h = int(state.stats["wis"] * 2) + 10
            state.hp = min(state.max_hp, state.hp + h)
            logs.append((f"Purifying Touch heals {h} HP!", "heal"))
        elif skill.heal_calc == "wis3_int1_heal":
            h = int(state.stats["wis"] * 3 + state.stats["int"] * 1.5)
            state.hp = min(state.max_hp, state.hp + h)
            logs.append((f"Healing Light restores {h} HP!", "heal"))
        elif skill.heal_calc == "wis2_luck1":
            h = int(state.stats["wis"] * 2.5 + state.luck * 1)
            state.hp = min(state.max_hp, state.hp + h)
            state.madness = min(100, state.madness + 5)
            logs.append((f"Laughing heals {h} HP! (+5 MAD)", "heal"))
        elif skill.heal_calc == "full_heal":
            state.hp = state.max_hp
            state.madness = min(100, state.madness + 25)
            logs.append(("Carcosa's Blessing: Full heal! (+25 MAD)", "heal"))
        elif skill.heal_calc == "int2_mend":
            h = int(state.stats["int"] * 2)
            state.hp = min(state.max_hp, state.hp + h)
            logs.append((f"Abyssal Mend heals {h} HP!", "heal"))
        elif skill.heal_calc == "devour15":
            h = int(state.max_hp * 0.15)
            state.hp = min(state.max_hp, state.hp + h)
            logs.append((f"Devour heals {h} HP!", "heal"))
        elif skill.heal_calc == "titanResil":
            h = int(state.max_hp * 0.40)
            state.hp = min(state.max_hp, state.hp + h)
            state.statuses.clear()
            logs.append((f"Titanic Resilience heals {h} HP and cleanses all debuffs!", "heal"))
        elif skill.heal_calc == "layOnHands":
            h = int(state.stats["wis"] * 3)
            state.hp = min(state.max_hp, state.hp + h)
            state.statuses.clear()
            logs.append((f"Lay on Hands heals {h} HP and cleanses!", "heal"))
        elif skill.heal_calc == "meditation":
            h = int(state.max_hp * 0.20)
            state.hp = min(state.max_hp, state.hp + h)
            state.madness = max(0, state.madness - 10)
            logs.append((f"Blessed Meditation heals {h} HP! -10 MAD!", "heal"))
        elif skill.heal_calc == "darkRegen":
            h = int(state.max_hp * 0.30)
            state.hp = min(state.max_hp, state.hp + h)
            state.buffs["darkRegenBuff"] = 2
            logs.append((f"Dark Regeneration heals {h} HP! EVA+20% 2t!", "heal"))
        elif skill.heal_calc == "hasturEmbrace":
            state.hp = state.max_hp
            state.madness = min(100, state.madness + 20)
            state.buffs["immunity"] = 2
            logs.append(("Hastur's Embrace: Full heal! Immune debuffs 2t! (+20 MAD)", "heal"))
        elif skill.heal_calc == "secondWind":
            h = int(state.max_hp * 0.20)
            state.hp = min(state.max_hp, state.hp + h)
            state.buffs["regen"] = 2
            logs.append((f"Second Wind heals {h} HP! Regen 3% 2t!", "heal"))
        elif skill.heal_calc == "nimbleRecov":
            h = int(state.max_hp * 0.25)
            state.hp = min(state.max_hp, state.hp + h)
            state.buffs["evasionUp"] = 2
            logs.append((f"Nimble Recovery heals {h} HP! EVA+15% 2t!", "heal"))
        else:
            h = int(state.stats.get(skill.stat, 10) * 2)
            state.hp = min(state.max_hp, state.hp + h)
            logs.append((f"Recovered {h} HP!", "heal"))
        return logs

    if skill.type == "self_shield":
        if skill.shield_calc == "int2_wis1":
            state.shield = int(state.stats["int"] * 2 + state.stats["wis"])
            logs.append((f"Psychic Shield: {state.shield} damage absorbed!", "shield"))
        elif skill.shield_calc == "wis3_int1":
            state.shield = int(state.stats["wis"] * 3 + state.stats["int"] * 1.5)
            logs.append((f"Aegis Shield: {state.shield} damage absorbed!", "shield"))
        elif skill.shield_calc == "wis3_hits":
            state.shield = int(state.stats["wis"] * 3 + state.hits_taken * 5)
            logs.append((f"Eldritch Ward: {state.shield} shield!", "shield"))
        elif skill.shield_calc == "sanctuary":
            state.barrier = min(3, state.barrier + 3)
            state.shield = int(state.stats["wis"] * 4)
            h = int(state.stats["wis"] * 2)
            state.hp = min(state.max_hp, state.hp + h)
            logs.append((f"Sanctuary! Barrier x3, Shield {state.shield}, Heal {h}!", "shield"))
        elif skill.shield_calc == "glyph_1":
            state.barrier = min(3, state.barrier + 1)
            logs.append((f"Warding Glyph! Barrier absorbs next hit! ({state.barrier} stacks)", "shield"))
        elif skill.shield_calc == "fracSan":
            state.shield = int(state.stats["int"] * 3)
            state.madness = min(100, state.madness + 10)
            logs.append((f"Fractured Sanity! Shield {state.shield}! (+10 MAD)", "shield"))
        elif skill.shield_calc == "str3_hits":
            state.shield = int(state.stats.get("str", 10) * 3 + state.hits_taken * 5)
            logs.append((f"Bone Armor: {state.shield} shield!", "shield"))
        elif skill.shield_calc == "madShell":
            state.shield = int(state.stats["wis"] * 2 + state.madness)
            state.madness = min(100, state.madness + 10)
            logs.append((f"Madness Shell: {state.shield} shield! (+10 MAD)", "shield"))
        elif skill.shield_calc == "madBarrier":
            state.shield = int(state.stats["wis"] * 3 + state.luck * 2)
            logs.append((f"Madness Barrier: {state.shield} shield!", "shield"))
        elif skill.shield_calc == "madEndur":
            state.shield = int(state.stats["wis"] * 2)
            state.madness = min(100, state.madness + 8)
            state.buffs["regen"] = 2
            logs.append((f"Madman's Endurance! Shield {state.shield}, regen 5%! (+8 MAD)", "shield"))
        return logs

    if skill.type == "self_buff":
        if skill.buff_type == "barrier":
            state.barrier = min(3, state.barrier + skill.barrier_stacks)
            logs.append((f"Barrier! ({state.barrier} stacks)", "shield"))
        elif skill.buff_type == "rage":
            state.rage = True
            hp_loss = int(state.max_hp * 0.12)
            state.hp = max(1, state.hp - hp_loss)
            logs.append((f"Berserker Rage! +60% damage, -{hp_loss} HP!", "effect"))
        elif skill.buff_type == "warlord":
            state.rage = True
            state.buffs["atkCritUp"] = skill.buff_duration
            state.buffs["ironSkin"] = skill.buff_duration
            hp_loss = int(state.max_hp * 0.20)
            state.hp = max(1, state.hp - hp_loss)
            logs.append((f"Warlord's Command! All buffs active! -{hp_loss} HP!", "effect"))
        elif skill.buff_type == "permIntWis":
            state.base_stats["int"] = state.base_stats.get("int", 0) + 2
            state.base_stats["wis"] = state.base_stats.get("wis", 0) + 1
            state.recalc_stats()
            logs.append(("Forbidden Text Deciphered! INT+2, WIS+1 permanently!", "effect"))
        elif skill.buff_type == "permAtk2":
            state.base_stats["str"] = state.base_stats.get("str", 0) + 2
            state.recalc_stats()
            logs.append(("Warpaint! STR+2 permanently!", "effect"))
        elif skill.buff_type == "permWisStr":
            state.base_stats["wis"] = state.base_stats.get("wis", 0) + 2
            state.base_stats["str"] = state.base_stats.get("str", 0) + 1
            state.recalc_stats()
            logs.append(("Oath of the Warden! WIS+2, STR+1 permanently!", "effect"))
        elif skill.buff_type == "permAgiLuk":
            state.base_stats["agi"] = state.base_stats.get("agi", 0) + 2
            state.base_stats["luck"] = state.base_stats.get("luck", 0) + 1
            state.recalc_stats()
            logs.append(("Perfect Assassin! AGI+2, LUCK+1 permanently!", "effect"))
        elif skill.buff_type == "permCrit10":
            state.crit = min(95, state.crit + 10)
            logs.append(("Sixth Sense! Crit permanently +10%!", "effect"))
        elif skill.buff_type == "permAll1":
            for stat in ("int", "str", "agi", "wis", "luck"):
                state.base_stats[stat] = state.base_stats.get(stat, 0) + 1
            state.recalc_stats()
            logs.append(("Vision of the End! All stats +1 permanently!", "effect"))
        elif skill.buff_type == "resetCds":
            for sk in state.active_skills:
                sk.current_cd = 0
            logs.append(("All cooldowns reset!", "effect"))
        elif skill.buff_type == "bloodRitual":
            state.hp = max(1, state.hp - int(state.max_hp * 0.15))
            state.xp += 50
            logs.append(("Blood Ritual! Sacrificed HP for 50 XP!", "effect"))
        elif skill.buff_type == "randStat2":
            stat_keys = ["int", "str", "agi", "wis", "luck"]
            chosen_stats = random.sample(stat_keys, 2)
            for st in chosen_stats:
                state.base_stats[st] = state.base_stats.get(st, 0) + 2
            state.recalc_stats()
            logs.append((f"Prophetic Insight! {chosen_stats[0].upper()}+2, {chosen_stats[1].upper()}+2!", "effect"))
        elif skill.buff_type == "madImmune":
            state.buffs["madImmune"] = 999
            state.madness = min(100, state.madness + 15)
            logs.append(("Madness Mastery! MAD no longer causes death! (+15 MAD)", "effect"))
        elif skill.buff_type == "thickSkull":
            state.base_stats["str"] = state.base_stats.get("str", 0) + 1
            state.base_stats["wis"] = state.base_stats.get("wis", 0) + 1
            state.recalc_stats()
            logs.append(("Thick Skull! STR+1, WIS+1 permanently!", "effect"))
        elif skill.buff_type == "perseverance":
            state.base_stats["wis"] = state.base_stats.get("wis", 0) + 1
            state.base_stats["str"] = state.base_stats.get("str", 0) + 1
            state.recalc_stats()
            logs.append(("Perseverance! WIS+1, STR+1 permanently!", "effect"))
        elif skill.buff_type == "shadowBless":
            state.base_stats["agi"] = state.base_stats.get("agi", 0) + 1
            state.base_stats["luck"] = state.base_stats.get("luck", 0) + 1
            state.recalc_stats()
            logs.append(("Shadow's Blessing! AGI+1, LUCK+1 permanently!", "effect"))
        elif skill.buff_type == "abyssFort":
            state.buffs["ironSkin"] = skill.buff_duration
            state.barrier = min(3, state.barrier + 1)
            logs.append(("Abyssal Fortitude! pDEF+50%, +1 barrier!", "effect"))
        elif skill.buff_type:
            state.buffs[skill.buff_type] = skill.buff_duration
            logs.append((f"{skill.name} activated!", "effect"))
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
    logs.append((f"You use {skill.name} for {dmg} damage!{crit_text}", "crit" if is_crit else "damage"))

    if skill.lifesteal and dmg > 0:
        h = int(dmg * skill.lifesteal)
        state.hp = min(state.max_hp, state.hp + h)
        logs.append((f"Stole {h} HP!", "heal"))

    if state.madness >= 100:
        return logs + [("Your mind shatters from the madness!", "damage")]

    # Apply effects
    if skill.effect:
        apply_status(e, skill.effect, skill.duration)
        if skill.effect == "poisoned":
            existing = next((s for s in e.statuses if s.type == "poisoned"), None)
            if existing:
                existing.stacks = min(5, existing.stacks + 1)
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


def enemy_turn(state):
    """Execute enemy turn. Returns list of (text, type) log messages."""
    logs = []
    c = state.combat
    e = c.enemy

    if e.stunned:
        e.stunned = False
        logs.append((f"{e.name} is stunned!", "effect"))
        return logs

    # Shock stun check
    shocked = next((s for s in e.statuses if s.type == "shocked"), None)
    if shocked and random.random() < 0.5:
        e.stunned = True
        logs.append((f"{e.name} stunned by shock!", "effect"))
        return logs

    # Blind miss check
    if has_status(e, "blinded") and random.random() < 0.5:
        logs.append((f"{e.name} misses!", "info"))
        return logs

    skill = random.choice(e.skills)
    stype = skill.get("type", "physical")
    spower = skill.get("power", 1.0)

    if stype in ("physical", "magic"):
        dmg = int(e.atk * spower * (0.85 + random.random() * 0.3))
        if stype == "physical" and has_status(e, "freezing"):
            dmg = int(dmg * 0.75)
        if stype == "magic" and has_status(e, "petrified"):
            dmg = int(dmg * 0.75)
        if has_status(state, "weakened"):
            dmg = int(dmg * 0.8)
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
        dmg = int(e.atk * spower * (0.85 + random.random() * 0.3))
        if "physical" in stype and has_status(e, "freezing"):
            dmg = int(dmg * 0.75)
        if "magic" in stype and has_status(e, "petrified"):
            dmg = int(dmg * 0.75)
        if has_status(state, "weakened"):
            dmg = int(dmg * 0.8)
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


def apply_status_effect_on_player(state, effect_type, duration):
    """Apply a status effect to the player."""
    if effect_type:
        apply_status_player(state, effect_type, duration)


def apply_status_player(state, effect_type, duration):
    """Apply status to player's status list."""
    existing = next((s for s in state.statuses if s.type == effect_type), None)
    if existing:
        existing.duration = max(existing.duration, duration)
    else:
        se = StatusEffect(effect_type, duration)
        state.statuses.append(se)
        if effect_type == "poisoned":
            se.stacks = 1
    # Stack poison
    if effect_type == "poisoned":
        existing = next((s for s in state.statuses if s.type == "poisoned"), None)
        if existing:
            existing.stacks = min(5, existing.stacks + 1)


def process_player_status_effects(state):
    """Process burning/poison/bleeding on the player."""
    logs = []
    to_remove = []
    for st in state.statuses:
        if st.type == "burning":
            d = int(state.max_hp * 0.06)
            state.hp = max(0, state.hp - d)
            logs.append((f"You burn for {d}!", "damage"))
        elif st.type == "poisoned":
            stacks = getattr(st, 'stacks', 1)
            d = int(state.max_hp * 0.04 * stacks)
            state.hp = max(0, state.hp - d)
            logs.append((f"Poison deals {d}! ({stacks} stacks)", "damage"))
        elif st.type == "bleeding":
            d = int(state.max_hp * 0.05)
            state.hp = max(0, state.hp - d)
            logs.append((f"You bleed for {d}!", "damage"))
        st.duration -= 1
        if st.duration <= 0:
            to_remove.append(st)
    for st in to_remove:
        state.statuses.remove(st)
        logs.append((f"{st.type} wears off.", "info"))
    return logs


def check_boss_phase(state):
    """Check and apply boss phase transitions."""
    c = state.combat
    if not c or not c.is_boss:
        return []
    e = c.enemy
    pct = e.hp / e.max_hp
    logs = []

    if pct <= 0.25 and not c.phase3:
        c.phase3 = True
        e.atk = int(e.atk * 1.4)
        e.skills.append({"name": "Desperate Fury", "type": "physical", "power": 2.5})
        logs.append(("━━ HASTUR ENTERS FINAL PHASE! ATK increased! ━━", "crit"))

    elif pct <= 0.5 and not c.phase2:
        c.phase2 = True
        e.skills.append({"name": "Reality Tear", "type": "magic_debuff", "power": 2.0, "effect": "blinded", "duration": 2})
        e.skills.append({"name": "Maddening Whisper", "type": "magic_debuff", "power": 1.0, "effect": "shocked", "duration": 2})
        logs.append(("━━ THE KING UNRAVELS REALITY! New abilities! ━━", "crit"))

    return logs


def combat_run_attempt(state):
    """Attempt to flee combat. Returns True if successful."""
    c = state.combat
    if not c:
        return False
    if c.is_boss:
        return False  # Can't flee from boss
    chance = 40 + state.stats["agi"] * 2
    if random.random() * 100 < chance:
        state.add_madness(5)
        return True
    else:
        state.add_madness(3)
        return False


# ═══════════════════════════════════════════
# FLOOR PROGRESSION
# ═══════════════════════════════════════════

def generate_paths(floor):
    """Generate two path choices for the player."""
    weighted_pool = []
    for pt in PATH_TEMPLATES:
        w = pt["weight"]
        if pt["type"] == "shop" and floor < 3:
            w = 0
        if pt["type"] == "trap" and floor < 2:
            w = 0
        for _ in range(w):
            weighted_pool.append(pt)

    p1 = random.choice(weighted_pool)
    p2 = random.choice(weighted_pool)
    while p2["name"] == p1["name"] and len(weighted_pool) > 1:
        p2 = random.choice(weighted_pool)
    return [dict(p1), dict(p2)]


def advance_floor(state):
    """Advance to the next floor."""
    state.hp = min(state.max_hp, state.hp + int(state.max_hp * 0.1))
    state.floor += 1
    return state.floor >= state.max_floor


def get_floor_narrative(floor):
    idx = min(floor - 1, len(FLOOR_NARRATIVES) - 1)
    return FLOOR_NARRATIVES[idx]


# ═══════════════════════════════════════════
# EVENT HANDLING
# ═══════════════════════════════════════════

def resolve_event(state, event_idx, outcome_idx):
    """Resolve an event outcome. Returns (message, loot_item_or_None)."""
    ev = EVENTS[event_idx]
    outcome = ev["outcomes"][outcome_idx]
    effect = outcome["effect"]
    loot = None
    msg = outcome["text"]

    if effect == "gain_int_2_mad_10":
        state.base_stats["int"] += 2
        state.recalc_stats()
        state.add_madness(10)
    elif effect == "nothing":
        pass
    elif effect == "reason_50":
        if random.random() < 0.5:
            state.base_stats["wis"] += 2
            state.recalc_stats()
            msg = "Reason succeeds! WIS+2"
        else:
            state.add_madness(15)
            msg = "Reason fails! +15 Madness"
    elif effect == "gain_str_2_mad_8":
        state.base_stats["str"] += 2
        state.recalc_stats()
        state.add_madness(8)
    elif effect == "mad_minus_5":
        state.add_madness(-5)
    elif effect == "deface_50":
        if random.random() < 0.5:
            state.hp = min(state.max_hp, state.hp + int(state.max_hp * 0.2))
            msg = "Defaced safely! Healed 20%"
        else:
            state.add_madness(12)
            msg = "The Sign retaliates! +12 MAD"
    elif effect == "drink_60":
        if random.random() < 0.6:
            state.hp = min(state.max_hp, state.hp + int(state.max_hp * 0.3))
            msg = "Strange elixir heals 30%!"
        else:
            state.hp = max(1, state.hp - int(state.max_hp * 0.2))
            msg = "Poison! Lost 20% HP"
    elif effect == "gold_15":
        state.gold += 15
    elif effect == "help_survivor":
        state.add_madness(10)
        loot = generate_item(state.floor, luck=state.luck)
        msg = f"Survivor gives you: {loot.name}"
    elif effect == "rob_survivor":
        state.gold += 20
        state.add_madness(5)
    elif effect == "pray_full_heal":
        state.hp = state.max_hp
        state.add_madness(15)
    elif effect == "desecrate":
        state.base_stats["agi"] += 3
        state.recalc_stats()
        state.add_madness(10)
    elif effect == "offer_gold":
        if state.gold >= 20:
            state.gold -= 20
            state.base_stats["wis"] += 3
            state.recalc_stats()
            msg = "Offering accepted! WIS+3"
        else:
            msg = "Not enough gold!"
    elif effect == "listen_rats":
        stat = random.choice(["int", "str", "agi", "wis", "luck"])
        state.base_stats[stat] += 1
        state.recalc_stats()
        state.add_madness(3)
        msg = f"The rats whisper secrets. {stat.upper()}+1"
    elif effect == "mad_5":
        state.add_madness(5)
    elif effect == "attack_rats":
        state.hp = max(1, state.hp - int(state.max_hp * 0.1))
        state.base_stats["str"] += 1
        state.recalc_stats()
        msg = "Scattered the rats! STR+1, -10% HP"

    return msg, loot


# ═══════════════════════════════════════════
# TRAP HANDLING
# ═══════════════════════════════════════════

def resolve_trap(state, trap_idx):
    """Resolve a trap. Returns (message, game_over)."""
    trap = TRAPS[trap_idx]
    roll = random.random()
    outcome = trap["outcomes"][-1]  # default to worst
    for o in trap["outcomes"]:
        if roll < o["chance"]:
            outcome = o
            break

    if outcome["dmg_pct"] > 0:
        state.hp = max(1, state.hp - int(state.max_hp * outcome["dmg_pct"]))
    if outcome["madness"] > 0:
        if state.add_madness(outcome["madness"]):
            return outcome["text"], True
    return outcome["text"], False


# ═══════════════════════════════════════════
# SHOP
# ═══════════════════════════════════════════

def generate_shop(state):
    """Generate shop items and prices."""
    items = [generate_item(state.floor, luck=state.luck) for _ in range(4)]
    prices = [10 + (item.rarity or 1) * 8 + random.randint(0, 10) for item in items]
    return items, prices


def buy_shop_item(state, shop_items, shop_prices, shop_sold, idx):
    """Buy an item from the shop. Returns (success, message)."""
    if shop_sold[idx]:
        return False, "Already sold!"
    if state.gold < shop_prices[idx]:
        return False, "Not enough gold!"
    state.gold -= shop_prices[idx]
    shop_sold[idx] = True
    item = shop_items[idx]
    prev = state.equip_item(item)
    if prev:
        state.inventory.append(prev)
    return True, f"Equipped {item.name}!"

"""Combat system: damage calculation, status effects, skill usage, enemy AI."""

import random
import math
from data import ENEMIES, BOSS, RARITY_DATA, CURSED_DEBUFFS, ITEM_PREFIXES, WEAPON_TEMPLATES, ARMOR_TEMPLATES, ACCESSORY_TEMPLATES, BOOTS_TEMPLATES, RING_TEMPLATES
from engine.models import Item, StatusEffect, Enemy, CombatState

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
    state.temp_stats = {}
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
    if state.buffs.get("ethereal", 0) > 0:
        bd *= 2.5  # +150% = 2.5x total

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


def _get_buff_defense_bonus(state, is_phys):
    """Calculate DEF/mDEF percentage bonus from active buffs."""
    pct = 0
    b = state.buffs
    if is_phys:
        if b.get("thoughtform", 0) > 0:   pct += 30
        if b.get("ironSkin", 0) > 0:       pct += 60
        if b.get("chant", 0) > 0:          pct += 20
        if b.get("innerFire", 0) > 0:      pct += 15
        if b.get("hallowed", 0) > 0:       pct += 40
        if b.get("fortress", 0) > 0:       pct += 80
        if b.get("bulwark", 0) > 0:        pct += 60
        if b.get("umbralAegis", 0) > 0:    pct += 40
    else:
        if b.get("thoughtform", 0) > 0:   pct += 30
        if b.get("ironSkin", 0) > 0:       pct += 30
        if b.get("chant", 0) > 0:          pct += 20
        if b.get("innerFire", 0) > 0:      pct += 15
        if b.get("mDefUp", 0) > 0:         pct += 50
        if b.get("wardAura", 0) > 0:       pct += 30
        if b.get("hallowed", 0) > 0:       pct += 40
        if b.get("fortress", 0) > 0:       pct += 80
        if b.get("bulwark", 0) > 0:        pct += 60
        if b.get("dreamShell", 0) > 0:     pct += 80
        if b.get("astral", 0) > 0:         pct += 60
    return pct


def _get_buff_evasion_bonus(state):
    """Calculate EVA bonus from active buffs."""
    bonus = 0
    b = state.buffs
    if b.get("smokeScreen", 0) > 0:   bonus += 25
    if b.get("dreamVeil", 0) > 0:     bonus += 35
    if b.get("evasionUp", 0) > 0:     bonus += 40
    if b.get("dreamShell", 0) > 0:    bonus += 50
    if b.get("umbralAegis", 0) > 0:   bonus += 60
    if b.get("astral", 0) > 0:        bonus += 40
    return bonus


def apply_damage_to_player(state, raw, is_phys):
    """Apply damage to player with shield/barrier/evasion/buffs."""
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

    # Divine Intervention: nullify next N attacks
    if state.buffs.get("divineInterv", 0) > 0:
        state.buffs["divineInterv"] -= 1
        return 0, "barrier"

    # Ethereal: invulnerable this turn
    if state.buffs.get("ethereal", 0) > 0:
        return 0, "evade"

    # Flicker: 50% dodge per stack
    if state.buffs.get("flicker", 0) > 0:
        if random.random() < 0.5:
            state.buffs["flicker"] -= 1
            return 0, "evade"

    # Evasion with buff bonuses
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
    dr = df / (df + 50)
    dmg = max(1, int(raw * (1 - dr)))

    # Mirror Images: 30% damage reduction
    if state.buffs.get("mirrorImg", 0) > 0:
        dmg = int(dmg * 0.7)

    if state.buffs.get("undying", 0) > 0 and dmg >= state.hp:
        state.hp = 1
        return dmg, "undying"

    # Undying Pact: can't die while active
    if state.buffs.get("undyingPact", 0) > 0 and dmg >= state.hp:
        state.hp = 1
        return dmg, "undying"

    # Eldritch Rebirth: auto-revive at 30% HP once
    if state.buffs.get("eldritchRebirth", 0) > 0 and dmg >= state.hp:
        state.hp = max(1, int(state.max_hp * 0.30))
        del state.buffs["eldritchRebirth"]
        return dmg, "undying"

    # Final Stand: invulnerable
    if state.buffs.get("finalStand", 0) > 0:
        return 0, "barrier"

    state.hp = max(0, state.hp - dmg)
    state.hits_taken += 1

    # Blood Aura: lifesteal 10% on damage taken (counter-intuitive but works as passive drain)
    if state.buffs.get("bloodAura", 0) > 0:
        heal = int(dmg * 0.10)
        state.hp = min(state.max_hp, state.hp + heal)

    # Retribution Aura: reflect 30% damage back to enemy
    if state.buffs.get("retribAura", 0) > 0 and state.combat:
        reflected = int(dmg * 0.30)
        state.combat.enemy.hp = max(0, state.combat.enemy.hp - reflected)

    # Dreadnought: convert damage taken into ATK bonus
    if state.buffs.get("dreadnought", 0) > 0:
        atk_bonus = int(dmg * 0.5)
        state.temp_stats["str"] = state.temp_stats.get("str", 0) + atk_bonus
        state.recalc_stats()

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
        if st.type == "doom" and not is_player:
            # Doom triggers: instant kill if below 30% HP
            hp_pct = target.hp / target.max_hp if target.max_hp > 0 else 0
            if hp_pct < 0.30:
                target.hp = 0
                logs.append((f"━━ THE YELLOW SIGN CLAIMS {target.name}! ━━", "crit"))
            else:
                logs.append((f"The Pallid Mask fades... {target.name} endures.", "info"))
        elif not is_player:
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
        elif key == "regen5" and state.buffs[key] >= 0:
            h = int(state.max_hp * 0.05)
            state.hp = min(state.max_hp, state.hp + h)
            logs.append((f"Regen heals {h} HP.", "heal"))
        elif key == "oath" and state.buffs[key] >= 0:
            h = int(state.max_hp * 0.10)
            state.hp = min(state.max_hp, state.hp + h)
            logs.append((f"Oath heals {h} HP.", "heal"))
        if state.buffs[key] <= 0:
            to_remove.append(key)

    # Mapping of stat buff types to their temp_stats keys
    STAT_BUFF_KEYS = {
        "permIntWis": ["int", "wis"],
        "permAtk2": ["str"],
        "permWisStr": ["wis", "str"],
        "permAgiLuk": ["agi", "luck"],
        "permAll1": ["int", "str", "agi", "wis", "luck"],
        "thickSkull": ["str", "wis"],
        "perseverance": ["wis", "str"],
        "shadowBless": ["agi", "luck"],
        "randStat2": ["int", "str", "agi", "wis", "luck"],  # cleared fully on expire
        "pallidMask": ["int", "str", "agi", "wis", "luck"],
        "dreadnought": ["str"],
    }

    for key in to_remove:
        del state.buffs[key]
        # Clean up temp stats if this was a stat buff
        if key in STAT_BUFF_KEYS:
            for sk in STAT_BUFF_KEYS[key]:
                state.temp_stats.pop(sk, None)
            state.recalc_stats()
            logs.append((f"{key} — temporary stat boost expired.", "info"))
        elif key == "permCrit10":
            state.crit = max(0, state.crit - 25)
            logs.append(("Sixth Sense — CRIT bonus expired.", "info"))
        else:
            logs.append((f"{key} expired.", "info"))
    return logs


# ═══════════════════════════════════════════
# SKILL HANDLERS (extracted from player_use_skill)
# ═══════════════════════════════════════════

# Maps heal_calc names → (calc_fn, message_template, extra_fn)
# calc_fn(state, skill) → heal_amount (int)
# extra_fn(state, skill) is called after heal (optional side effects)
def _calc_heal_int2_buff(state, skill):
    h = int(state.stats["int"] * 2)
    state.base_stats["int"] += 3
    state.recalc_stats()
    return h

def _calc_heal_missing_hp(state, skill):
    missing = 1 - state.hp / state.max_hp
    return int(missing * state.max_hp * 0.6)

def _calc_heal_wis2_10(state, skill):
    return int(state.stats["wis"] * 2) + 10

def _calc_heal_wis3_int1(state, skill):
    return int(state.stats["wis"] * 3 + state.stats["int"] * 1.5)

def _calc_heal_wis2_luck1(state, skill):
    h = int(state.stats["wis"] * 2.5 + state.luck * 1)
    state.madness = min(100, state.madness + 5)
    return h

def _calc_heal_full_heal(state, skill):
    state.hp = state.max_hp
    state.madness = min(100, state.madness + 25)
    return 0  # already set to full

def _calc_heal_int2_mend(state, skill):
    return int(state.stats["int"] * 2)

def _calc_heal_devour15(state, skill):
    return int(state.max_hp * 0.15)

def _calc_heal_titanResil(state, skill):
    state.statuses.clear()
    return int(state.max_hp * 0.40)

def _calc_heal_layOnHands(state, skill):
    state.statuses.clear()
    return int(state.stats["wis"] * 3)

def _calc_heal_meditation(state, skill):
    state.madness = max(0, state.madness - 10)
    return int(state.max_hp * 0.20)

def _calc_heal_darkRegen(state, skill):
    state.buffs["darkRegenBuff"] = 2
    return int(state.max_hp * 0.30)

def _calc_heal_hasturEmbrace(state, skill):
    state.hp = state.max_hp
    state.madness = min(100, state.madness + 20)
    state.buffs["immunity"] = 2
    return 0  # already set to full

def _calc_heal_secondWind(state, skill):
    state.buffs["regen"] = 2
    return int(state.max_hp * 0.20)

def _calc_heal_nimbleRecov(state, skill):
    state.buffs["evasionUp"] = 2
    return int(state.max_hp * 0.25)

def _calc_heal_default(state, skill):
    return int(state.stats.get(skill.stat, 10) * 2)

# Heal handler registry: heal_calc name → (calc_fn, message)
HEAL_HANDLERS = {
    "int2_buff":     (_calc_heal_int2_buff,     "Forbidden Knowledge heals {h} HP! INT+3!"),
    "missing_hp":    (_calc_heal_missing_hp,     "Adrenaline Surge heals {h} HP!"),
    "wis2_10":       (_calc_heal_wis2_10,        "Purifying Touch heals {h} HP!"),
    "wis3_int1_heal":(_calc_heal_wis3_int1,      "Healing Light restores {h} HP!"),
    "wis2_luck1":    (_calc_heal_wis2_luck1,     "Laughing heals {h} HP! (+5 MAD)"),
    "full_heal":     (_calc_heal_full_heal,      "Carcosa's Blessing: Full heal! (+25 MAD)"),
    "int2_mend":     (_calc_heal_int2_mend,      "Abyssal Mend heals {h} HP!"),
    "devour15":      (_calc_heal_devour15,       "Devour heals {h} HP!"),
    "titanResil":    (_calc_heal_titanResil,     "Titanic Resilience heals {h} HP and cleanses all debuffs!"),
    "layOnHands":    (_calc_heal_layOnHands,     "Lay on Hands heals {h} HP and cleanses!"),
    "meditation":    (_calc_heal_meditation,     "Blessed Meditation heals {h} HP! -10 MAD!"),
    "darkRegen":     (_calc_heal_darkRegen,      "Dark Regeneration heals {h} HP! EVA+20% 2t!"),
    "hasturEmbrace": (_calc_heal_hasturEmbrace,  "Hastur's Embrace: Full heal! Immune debuffs 2t! (+20 MAD)"),
    "secondWind":    (_calc_heal_secondWind,     "Second Wind heals {h} HP! Regen 3% 2t!"),
    "nimbleRecov":   (_calc_heal_nimbleRecov,    "Nimble Recovery heals {h} HP! EVA+15% 2t!"),
}


def _handle_self_heal(state, skill):
    """Handle self_heal skill type. Returns list of log messages."""
    calc_fn, msg_template = HEAL_HANDLERS.get(skill.heal_calc, (_calc_heal_default, "Recovered {h} HP!"))
    h = calc_fn(state, skill)
    if h > 0:
        state.hp = min(state.max_hp, state.hp + h)
    msg = msg_template.format(h=h) if h > 0 else msg_template
    return [(msg, "heal")]


# Shield handler registry: shield_calc name → (build_fn, message)
# build_fn(state, skill) → shield_value (int), or None if custom logic
def _shield_int2_wis1(state, skill):
    return int(state.stats["int"] * 2 + state.stats["wis"])

def _shield_wis3_int1(state, skill):
    return int(state.stats["wis"] * 3 + state.stats["int"] * 1.5)

def _shield_wis3_hits(state, skill):
    return int(state.stats["wis"] * 3 + state.hits_taken * 5)

def _shield_sanctuary(state, skill):
    state.barrier = min(3, state.barrier + 3)
    h = int(state.stats["wis"] * 2)
    state.hp = min(state.max_hp, state.hp + h)
    return int(state.stats["wis"] * 4)

def _shield_glyph_1(state, skill):
    state.barrier = min(3, state.barrier + 1)
    return None  # barrier only, no shield value

def _shield_fracSan(state, skill):
    state.madness = min(100, state.madness + 10)
    return int(state.stats["int"] * 3)

def _shield_str3_hits(state, skill):
    return int(state.stats.get("str", 10) * 3 + state.hits_taken * 5)

def _shield_madShell(state, skill):
    state.madness = min(100, state.madness + 10)
    return int(state.stats["wis"] * 2 + state.madness)

def _shield_madBarrier(state, skill):
    return int(state.stats["wis"] * 3 + state.luck * 2)

def _shield_madEndur(state, skill):
    state.madness = min(100, state.madness + 8)
    state.buffs["regen"] = 2
    return int(state.stats["wis"] * 2)

SHIELD_HANDLERS = {
    "int2_wis1":  (_shield_int2_wis1,  "Psychic Shield: {v} damage absorbed!"),
    "wis3_int1":  (_shield_wis3_int1,   "Aegis Shield: {v} damage absorbed!"),
    "wis3_hits":  (_shield_wis3_hits,   "Eldritch Ward: {v} shield!"),
    "sanctuary":  (_shield_sanctuary,   "Sanctuary! Barrier x3, Shield {v}, Heal {h}!"),
    "glyph_1":    (_shield_glyph_1,     "Warding Glyph! Barrier absorbs next hit! ({v} stacks)"),
    "fracSan":    (_shield_fracSan,     "Fractured Sanity! Shield {v}! (+10 MAD)"),
    "str3_hits":  (_shield_str3_hits,   "Bone Armor: {v} shield!"),
    "madShell":   (_shield_madShell,    "Madness Shell: {v} shield! (+10 MAD)"),
    "madBarrier": (_shield_madBarrier,  "Madness Barrier: {v} shield!"),
    "madEndur":   (_shield_madEndur,    "Madman's Endurance! Shield {v}, regen 5%! (+8 MAD)"),
}


def _handle_self_shield(state, skill):
    """Handle self_shield skill type. Returns list of log messages."""
    handler, msg_template = SHIELD_HANDLERS.get(skill.shield_calc, (None, None))
    if handler is None:
        return [(f"{skill.name} activated!", "shield")]

    result = handler(state, skill)
    if result is not None:
        state.shield = result

    # Format message — use 'v' for shield value, 'h' for heal amount if sanctuary
    h = int(state.stats["wis"] * 2) if skill.shield_calc == "sanctuary" else 0
    v = state.barrier if skill.shield_calc == "glyph_1" else (result or state.shield)
    msg = msg_template.format(v=v, h=h)
    return [(msg, "shield")]


# Buff handler registry: buff_type → (apply_fn, message)
# apply_fn(state, skill) → None (mutates state directly)

def _buff_barrier(state, skill):
    state.barrier = min(3, state.barrier + skill.barrier_stacks)

def _buff_rage(state, skill):
    state.rage = True
    hp_loss = int(state.max_hp * 0.12)
    state.hp = max(1, state.hp - hp_loss)
    return {"hp_loss": hp_loss}

def _buff_warlord(state, skill):
    state.rage = True
    state.buffs["atkCritUp"] = skill.buff_duration
    state.buffs["ironSkin"] = skill.buff_duration
    hp_loss = int(state.max_hp * 0.20)
    state.hp = max(1, state.hp - hp_loss)
    return {"hp_loss": hp_loss}

def _buff_permIntWis(state, skill):
    state.temp_stats["int"] = state.temp_stats.get("int", 0) + 6
    state.temp_stats["wis"] = state.temp_stats.get("wis", 0) + 4
    state.buffs["permIntWis"] = skill.buff_duration
    state.recalc_stats()

def _buff_permAtk2(state, skill):
    state.temp_stats["str"] = state.temp_stats.get("str", 0) + 5
    state.buffs["permAtk2"] = skill.buff_duration
    state.recalc_stats()

def _buff_permWisStr(state, skill):
    state.temp_stats["wis"] = state.temp_stats.get("wis", 0) + 6
    state.temp_stats["str"] = state.temp_stats.get("str", 0) + 4
    state.buffs["permWisStr"] = skill.buff_duration
    state.recalc_stats()

def _buff_permAgiLuk(state, skill):
    state.temp_stats["agi"] = state.temp_stats.get("agi", 0) + 7
    state.temp_stats["luck"] = state.temp_stats.get("luck", 0) + 4
    state.buffs["permAgiLuk"] = skill.buff_duration
    state.recalc_stats()

def _buff_permCrit10(state, skill):
    state.crit = min(95, state.crit + 25)
    state.buffs["permCrit10"] = skill.buff_duration

def _buff_permAll1(state, skill):
    for stat in ("int", "str", "agi", "wis", "luck"):
        state.temp_stats[stat] = state.temp_stats.get(stat, 0) + 4
    state.buffs["permAll1"] = skill.buff_duration
    state.recalc_stats()

def _buff_resetCds(state, skill):
    for sk in state.active_skills:
        sk.current_cd = 0

def _buff_bloodRitual(state, skill):
    state.hp = max(1, state.hp - int(state.max_hp * 0.15))
    state.xp += 50

def _buff_randStat2(state, skill):
    stat_keys = ["int", "str", "agi", "wis", "luck"]
    chosen = random.sample(stat_keys, 2)
    for st in chosen:
        state.temp_stats[st] = state.temp_stats.get(st, 0) + 3
    state.buffs["randStat2"] = 5
    state.recalc_stats()
    return {"stats": chosen}

def _buff_madImmune(state, skill):
    state.buffs["madImmune"] = 999
    state.madness = min(100, state.madness + 15)

def _buff_calmMind(state, skill):
    state.madness = max(0, state.madness - 3)

def _buff_eldritchBargain(state, skill):
    stat_keys = ["int", "str", "agi", "wis", "luck"]
    chosen = random.sample(stat_keys, 3)
    for st in chosen:
        state.base_stats[st] = max(1, state.base_stats.get(st, 1) - 3)
    state.recalc_stats()
    state.gold += 50
    return {"stats": chosen}

def _buff_foolLuck(state, skill):
    state.madness = max(0, state.madness - 10)
    state.buffs["divineInterv"] = 3

def _buff_realityAnchor(state, skill):
    state.buffs["undying"] = skill.buff_duration

def _buff_pallidMask(state, skill):
    for stat in ("int", "str", "agi", "wis", "luck"):
        state.temp_stats[stat] = state.temp_stats.get(stat, 0) + int(state.base_stats.get(stat, 5) * 0.5)
    state.buffs["pallidMask"] = skill.buff_duration
    state.buffs["immunity"] = skill.buff_duration
    state.recalc_stats()

def _buff_prophetRes(state, skill):
    state.madness = min(100, state.madness + 5)
    state.buffs["regen"] = skill.buff_duration

def _buff_thickSkull(state, skill):
    state.temp_stats["str"] = state.temp_stats.get("str", 0) + 4
    state.temp_stats["wis"] = state.temp_stats.get("wis", 0) + 3
    state.buffs["thickSkull"] = skill.buff_duration
    state.recalc_stats()

def _buff_perseverance(state, skill):
    state.temp_stats["wis"] = state.temp_stats.get("wis", 0) + 4
    state.temp_stats["str"] = state.temp_stats.get("str", 0) + 3
    state.buffs["perseverance"] = skill.buff_duration
    state.recalc_stats()

def _buff_shadowBless(state, skill):
    state.temp_stats["agi"] = state.temp_stats.get("agi", 0) + 4
    state.temp_stats["luck"] = state.temp_stats.get("luck", 0) + 3
    state.buffs["shadowBless"] = skill.buff_duration
    state.recalc_stats()

def _buff_abyssFort(state, skill):
    state.buffs["ironSkin"] = skill.buff_duration
    state.barrier = min(3, state.barrier + 1)

def _buff_eldritchRebirth(state, skill):
    state.buffs["eldritchRebirth"] = skill.buff_duration

def _buff_astral(state, skill):
    state.buffs["astral"] = skill.buff_duration

def _buff_statSwap(state, skill):
    state.buffs["statSwap"] = skill.buff_duration

def _buff_dreadnought(state, skill):
    state.buffs["dreadnought"] = skill.buff_duration

# Static messages per buff_type (most don't need dynamic formatting)
_BUFF_MESSAGES = {
    "barrier":       "Barrier! ({v} stacks)",
    "rage":          "Berserker Rage! +60% damage, -{hp_loss} HP!",
    "warlord":       "Warlord's Command! All buffs active! -{hp_loss} HP!",
    "permIntWis":    "Forbidden Text Deciphered! INT+6, WIS+4 for 5 turns!",
    "permAtk2":      "Warpaint! STR+5 for 5 turns!",
    "permWisStr":    "Oath of the Warden! WIS+6, STR+4 for 5 turns!",
    "permAgiLuk":    "Perfect Assassin! AGI+7, LUCK+4 for 5 turns!",
    "permCrit10":    "Sixth Sense! CRIT+25% for 4 turns!",
    "permAll1":      "Vision of the End! All stats +4 for 5 turns!",
    "resetCds":      "All cooldowns reset!",
    "bloodRitual":   "Blood Ritual! Sacrificed HP for 50 XP!",
    "randStat2":     "Prophetic Insight! {stats}! for 5 turns!",
    "madImmune":     "Madness Mastery! MAD no longer causes death! (+15 MAD)",
    "calmMind":      "Leng's Whisper muffles the madness. -3 MAD!",
    "eldritchBargain":"Eldritch Bargain! -3 to {stats}, +50 gold!",
    "foolLuck":      "The Fool's Luck! -10 MAD, nullify next 3 attacks!",
    "realityAnchor": "Reality Anchor! Cannot die for 2 turns!",
    "pallidMask":    "The Pallid Mask manifests! +50% all stats, immune to debuffs 3t!",
    "prophetRes":    "Prophet's Resilience! Regen 6% HP/turn. (+5 MAD)",
    "thickSkull":    "Thick Skull! STR+4, WIS+3 for 5 turns!",
    "perseverance":  "Perseverance! WIS+4, STR+3 for 5 turns!",
    "shadowBless":   "Shadow's Blessing! AGI+4, LUCK+3 for 5 turns!",
    "abyssFort":     "Abyssal Fortitude! pDEF+50%, +1 barrier!",
    "eldritchRebirth": "Eldritch Rebirth! Auto-revive at 30% HP if killed! ({d} turns)",
    "astral":        "Astral Projection! EVA+40%, mDEF+60% for {d} turns!",
    "statSwap":      "Mind Over Matter! pDEF and mDEF swapped for {d} turns!",
    "dreadnought":   "Dreadnought! Damage taken converts to ATK for {d} turns!",
}

BUFF_HANDLERS = {
    "barrier":       _buff_barrier,
    "rage":          _buff_rage,
    "warlord":       _buff_warlord,
    "permIntWis":    _buff_permIntWis,
    "permAtk2":      _buff_permAtk2,
    "permWisStr":    _buff_permWisStr,
    "permAgiLuk":    _buff_permAgiLuk,
    "permCrit10":    _buff_permCrit10,
    "permAll1":      _buff_permAll1,
    "resetCds":      _buff_resetCds,
    "bloodRitual":   _buff_bloodRitual,
    "randStat2":     _buff_randStat2,
    "madImmune":     _buff_madImmune,
    "calmMind":      _buff_calmMind,
    "eldritchBargain":_buff_eldritchBargain,
    "foolLuck":      _buff_foolLuck,
    "realityAnchor": _buff_realityAnchor,
    "pallidMask":    _buff_pallidMask,
    "prophetRes":    _buff_prophetRes,
    "thickSkull":    _buff_thickSkull,
    "perseverance":  _buff_perseverance,
    "shadowBless":   _buff_shadowBless,
    "abyssFort":     _buff_abyssFort,
    "eldritchRebirth": _buff_eldritchRebirth,
    "astral":        _buff_astral,
    "statSwap":      _buff_statSwap,
    "dreadnought":   _buff_dreadnought,
}


def _handle_self_buff(state, skill):
    """Handle self_buff skill type. Returns list of log messages."""
    buff_type = skill.buff_type
    if not buff_type:
        return [(f"{skill.name} activated!", "effect")]

    handler = BUFF_HANDLERS.get(buff_type)
    if handler is None:
        # Generic fallback — just set the buff
        state.buffs[buff_type] = skill.buff_duration
        return [(f"{skill.name} activated!", "effect")]

    extra = handler(state, skill) or {}

    # Build message
    msg_template = _BUFF_MESSAGES.get(buff_type, f"{skill.name} activated!")
    # Format dynamic parts
    fmt = dict(extra)
    fmt["v"] = state.barrier  # for barrier type
    fmt["d"] = skill.buff_duration  # for duration in messages
    if "stats" in fmt and isinstance(fmt["stats"], list):
        fmt["stats"] = ", ".join(s.upper() + ("+3" if buff_type == "randStat2" else "-3") for s in fmt["stats"])
    try:
        msg = msg_template.format(**fmt)
    except (KeyError, IndexError):
        msg = msg_template

    return [(msg, "effect" if buff_type != "barrier" else "shield")]


# ═══════════════════════════════════════════
# MAIN SKILL DISPATCHER
# ═══════════════════════════════════════════

def player_use_skill(state, skill_index):
    """Player uses a skill. Returns list of (text, type) log messages."""
    logs = []
    skill = state.active_skills[skill_index]
    c = state.combat
    e = c.enemy

    # --- Pre-checks ---
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

    # --- Non-damage skill types ---
    if skill.type == "self_heal":
        return logs + _handle_self_heal(state, skill)

    if skill.type == "self_shield":
        return logs + _handle_self_shield(state, skill)

    if skill.type == "self_buff":
        return logs + _handle_self_buff(state, skill)

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

    # Consume ethereal buff after attack
    if state.buffs.get("ethereal", 0) > 0 and dmg > 0:
        state.buffs["ethereal"] = 0

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
    # Debuff immunity check
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


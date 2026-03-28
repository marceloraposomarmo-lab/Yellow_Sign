"""World systems: floor progression, events, traps, shop."""

import random
from data import PATH_TEMPLATES, FLOOR_NARRATIVES, EVENTS, TRAPS
from engine.models import Item
from engine.combat import generate_item

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
        loot = generate_item(state.floor, luck=state.luck, buffs=state.buffs)
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
    items = [generate_item(state.floor, luck=state.luck, buffs=state.buffs) for _ in range(4)]
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

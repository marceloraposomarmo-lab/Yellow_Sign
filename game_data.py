"""
THE KING IN YELLOW — Game Data
All classes, skills, enemies, items, events, and game constants.
"""

MAX_ACTIVE_SKILLS = 4

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

# ═══════════════════════════════════════════
# CLASSES & SKILLS (5 classes, 40 skills each)
# Each skill has: tier (1-3), category, stat_priority
# ═══════════════════════════════════════════

CLASSES = {
    "scholar": {
        "name": "Scholar of the Forbidden",
        "icon": "S",
        "desc": "Wielder of eldritch knowledge. Devastating magical bursts and crippling status effects. Fragile but deadly.",
        "base_stats": {"int": 14, "str": 6, "agi": 8, "wis": 10, "luck": 5},
        "hp_base": 70, "hp_per_level": 6,
        "skills": [
            # ── OFFENSIVE ──
            {"name": "Eldritch Blast", "icon": "*", "unlock_lv": 1, "desc": "Hurl a bolt of pure eldritch energy.", "formula": "dmg = (5 + INTx1.5) x 1.8", "type": "magic", "power": 1.8, "stat": "int", "cost": 0, "cd": 0, "tags": ["offensive"], "tier": 1, "category": "offensive", "stat_priority": ["int"]},
            {"name": "Arcane Missile", "icon": "~", "unlock_lv": 1, "desc": "Fast homing missiles of condensed thought.", "formula": "dmg = (5 + INTx1.5) x 1.2, cannot miss", "type": "magic", "power": 1.2, "stat": "int", "cost": 5, "cd": 0, "true_strike": True, "tags": ["offensive"], "tier": 1, "category": "offensive", "stat_priority": ["int"]},
            {"name": "Psionic Lash", "icon": "!", "unlock_lv": 1, "desc": "A whip of pure psychic force.", "formula": "dmg = (5 + INTx1.5) x 1.4", "type": "magic", "power": 1.4, "stat": "int", "cost": 0, "cd": 0, "tags": ["offensive"], "tier": 1, "category": "offensive", "stat_priority": ["int"]},
            {"name": "Void Bolt", "icon": "@", "unlock_lv": 6, "desc": "A bolt from between dimensions.", "formula": "dmg = (5 + INTx1.5 + WISx0.5) x 2.0", "type": "mixed_magic", "power": 2.0, "stat": "int", "stat2": "wis", "stat2_mult": 0.5, "cost": 15, "cd": 3, "tags": ["offensive", "dual-stat"], "tier": 2, "category": "offensive", "stat_priority": ["int", "wis"]},
            {"name": "Mind Shatter", "icon": "X", "unlock_lv": 8, "desc": "Shatter the enemy's psyche.", "formula": "dmg = (5 + INTx1.5) x 2.8 + Petrify 2 turns", "type": "magic_debuff", "power": 2.8, "stat": "int", "effect": "petrified", "duration": 2, "cost": 22, "cd": 5, "tags": ["offensive", "debuff"], "tier": 2, "category": "offensive", "stat_priority": ["int"]},
            {"name": "Mental Collapse", "icon": "%", "unlock_lv": 6, "desc": "Overwhelm with infinite psychic recursion.", "formula": "dmg = (5 + INTx1.5) x 1.8, scales with MAD", "type": "magic", "power": 1.8, "stat": "int", "cost": 15, "cd": 4, "madness_scaling": True, "tags": ["offensive"], "tier": 2, "category": "offensive", "stat_priority": ["int"]},
            {"name": "Entropy Wave", "icon": "-", "unlock_lv": 12, "desc": "Wave of entropic energy that corrodes all.", "formula": "dmg = (5 + INTx1.8) x 2.2, ignores 40% mDEF", "type": "magic", "power": 2.2, "stat": "int", "armor_pierce": 0.4, "cost": 18, "cd": 4, "tags": ["offensive"], "tier": 3, "category": "offensive", "stat_priority": ["int"]},
            {"name": "Void Rift", "icon": "=", "unlock_lv": 12, "desc": "Open a tear in reality itself.", "formula": "dmg = (5 + INTx2.0 + WISx1.0) x 2.5", "type": "mixed_magic", "power": 2.5, "stat": "int", "stat2": "wis", "stat2_mult": 1.0, "cost": 22, "cd": 5, "tags": ["offensive", "dual-stat"], "tier": 3, "category": "offensive", "stat_priority": ["int", "wis"]},
            {"name": "Gaze of the Cosmos", "icon": "O", "unlock_lv": 14, "desc": "Peer beyond. The cosmos stares back with terrible force.", "formula": "dmg = (5 + INTx2.0) x 2.5, ignores 50% mDEF", "type": "magic", "power": 2.5, "stat": "int", "armor_pierce": 0.5, "cost": 20, "cd": 5, "tags": ["offensive"], "tier": 3, "category": "offensive", "stat_priority": ["int"]},
            {"name": "Thought Spiral", "icon": "?", "unlock_lv": 16, "desc": "Infinite recursive thought made weapon.", "formula": "dmg = (5 + INTx1.8) x 2.2, scales with MAD", "type": "magic", "power": 2.2, "stat": "int", "cost": 18, "cd": 4, "madness_scaling": True, "tags": ["offensive"], "tier": 3, "category": "offensive", "stat_priority": ["int"]},

            # ── DEFENSIVE ──
            {"name": "Psychic Shield", "icon": "#", "unlock_lv": 2, "desc": "Erect a barrier of crystallized thought.", "formula": "shield = INTx2 + WISx1, absorbs damage", "type": "self_shield", "cost": 8, "cd": 3, "shield_calc": "int2_wis1", "tags": ["defensive"], "tier": 1, "category": "defensive", "stat_priority": ["int", "wis"]},
            {"name": "Warding Glyph", "icon": "^", "unlock_lv": 1, "desc": "A sigil that absorbs one incoming attack.", "formula": "Gain 1 barrier stack (absorbs any hit)", "type": "self_shield", "cost": 5, "cd": 3, "shield_calc": "glyph_1", "tags": ["defensive"], "tier": 1, "category": "defensive", "stat_priority": ["wis"]},
            {"name": "Fractured Sanity", "icon": "&", "unlock_lv": 2, "desc": "+10 MAD for a powerful shield.", "formula": "shield = INTx3, +10 MAD", "type": "self_shield", "cost": 0, "cd": 4, "shield_calc": "fracSan", "tags": ["defensive"], "tier": 1, "category": "defensive", "stat_priority": ["int"]},
            {"name": "Abyssal Mend", "icon": "+", "unlock_lv": 4, "desc": "Dark energies knit flesh.", "formula": "Heal = INTx2 HP", "type": "self_heal", "cost": 10, "cd": 4, "heal_calc": "int2_mend", "tags": ["defensive"], "tier": 2, "category": "defensive", "stat_priority": ["int"]},
            {"name": "Eldritch Ward", "icon": ";", "unlock_lv": 14, "desc": "Protective aura that grows with each hit taken.", "formula": "shield = WISx3 + hits_taken x 5", "type": "self_shield", "cost": 15, "cd": 5, "shield_calc": "wis3_hits", "tags": ["defensive"], "tier": 2, "category": "defensive", "stat_priority": ["wis"]},
            {"name": "Thoughtform Armor", "icon": "[", "unlock_lv": 6, "desc": "Conjured psychic armor. DEF+30%, mDEF+30% 3t.", "formula": "Self: pDEF+30%, mDEF+30% for 3 turns", "type": "self_buff", "cost": 10, "cd": 5, "buff_type": "thoughtform", "buff_duration": 3, "tags": ["defensive"], "tier": 2, "category": "defensive", "stat_priority": ["int", "wis"]},
            {"name": "Veil of the Dream", "icon": "]", "unlock_lv": 4, "desc": "EVA+35% 2t. Phase partially.", "formula": "Self: EVA+35% for 2 turns", "type": "self_buff", "cost": 8, "cd": 3, "buff_type": "dreamVeil", "buff_duration": 2, "tags": ["defensive"], "tier": 2, "category": "defensive", "stat_priority": ["agi"]},
            {"name": "Forbidden Knowledge", "icon": "+", "unlock_lv": 10, "desc": "Channel cosmic truth. Heal and boost INT.", "formula": "Heal INTx2 HP, INT +3 for 5 turns", "type": "self_heal", "cost": 12, "cd": 6, "heal_calc": "int2_buff", "tags": ["support", "defensive"], "tier": 3, "category": "defensive", "stat_priority": ["int"]},
            {"name": "Eldritch Rebirth", "icon": "R", "unlock_lv": 16, "desc": "If killed, revive at 30% HP. Lasts 3 turns.", "formula": "Self: auto-revive at 30% HP once, 3 turns", "type": "self_buff", "cost": 20, "cd": 10, "buff_type": "eldritchRebirth", "buff_duration": 3, "tags": ["defensive", "ultimate"], "tier": 3, "category": "defensive", "stat_priority": ["int", "wis"]},
            {"name": "Dream Shell", "icon": "D", "unlock_lv": 16, "desc": "Phase partially out of reality. EVA+50%, mDEF+80% 2t.", "formula": "Self: EVA+50%, mDEF+80% for 2 turns", "type": "self_buff", "cost": 15, "cd": 6, "buff_type": "dreamShell", "buff_duration": 2, "tags": ["defensive"], "tier": 3, "category": "defensive", "stat_priority": ["int", "wis"]},

            # ── UTILITY ──
            {"name": "Leng's Whisper", "icon": "w", "unlock_lv": 1, "desc": "Muffle the madness. -3 MAD.", "formula": "Self: reduce MAD by 3", "type": "self_buff", "cost": 0, "cd": 4, "buff_type": "calmMind", "buff_duration": 0, "tags": ["utility"], "tier": 1, "category": "utility", "stat_priority": ["wis"]},
            {"name": "Eldritch Siphon", "icon": "s", "unlock_lv": 2, "desc": "Steal an enemy buff for yourself.", "formula": "Steal 1 enemy buff, 2 turns", "type": "debuff", "power": 0, "stat": "int", "cost": 8, "cd": 4, "tags": ["utility"], "tier": 1, "category": "utility", "stat_priority": ["int"]},
            {"name": "Eldritch Sight", "icon": "O", "unlock_lv": 6, "desc": "See the enemy's weakness. +30% crit 3 turns.", "formula": "Self: CRIT +30% for 3 turns", "type": "self_buff", "cost": 8, "cd": 5, "buff_type": "critUp", "buff_duration": 3, "tags": ["support"], "tier": 2, "category": "utility", "stat_priority": ["int"]},
            {"name": "Mind Over Matter", "icon": "m", "unlock_lv": 6, "desc": "Swap pDEF and mDEF for 3 turns.", "formula": "Self: swap physical and magic DEF for 3 turns", "type": "self_buff", "cost": 8, "cd": 5, "buff_type": "statSwap", "buff_duration": 3, "tags": ["utility"], "tier": 2, "category": "utility", "stat_priority": ["int", "wis"]},
            {"name": "Temporal Glimpse", "icon": "t", "unlock_lv": 8, "desc": "Peer through time. Reset all cooldowns.", "formula": "All skill CDs reset to 0", "type": "self_buff", "cost": 15, "cd": 8, "buff_type": "resetCds", "buff_duration": 0, "tags": ["support"], "tier": 2, "category": "utility", "stat_priority": ["int"]},
            {"name": "Cartographer's Eye", "icon": "c", "unlock_lv": 4, "desc": "+15% loot quality for the next 5 floors.", "formula": "Self: +15% loot quality 5 floors", "type": "self_buff", "cost": 0, "cd": 0, "buff_type": "lootSight", "buff_duration": 99, "tags": ["utility"], "tier": 2, "category": "utility", "stat_priority": ["wis", "luck"]},
            {"name": "Forbidden Text Deciphered", "icon": "f", "unlock_lv": 14, "desc": "Permanent INT+2, WIS+1.", "formula": "Self: INT+2, WIS+1 permanently", "type": "self_buff", "cost": 0, "cd": 0, "buff_type": "permIntWis", "buff_duration": 0, "tags": ["utility"], "tier": 3, "category": "utility", "stat_priority": ["int", "wis"]},
            {"name": "Liminal Step", "icon": "l", "unlock_lv": 12, "desc": "30% chance to skip combat encounters.", "formula": "Passive: 30% skip combat on encounter", "type": "self_buff", "cost": 0, "cd": 0, "buff_type": "liminalStep", "buff_duration": 99, "tags": ["utility"], "tier": 3, "category": "utility", "stat_priority": ["agi", "wis"]},
            {"name": "Astral Projection", "icon": "&", "unlock_lv": 16, "desc": "Phase out of reality. EVA +40%, mDEF +60% 3t.", "formula": "Self: EVA+40%, mDEF+60% for 3 turns", "type": "self_buff", "cost": 12, "cd": 6, "buff_type": "astral", "buff_duration": 3, "tags": ["defensive", "support"], "tier": 3, "category": "utility", "stat_priority": ["int", "wis"]},
            {"name": "Warp Time", "icon": "(", "unlock_lv": 18, "desc": "Bend time. Reset all cooldowns + 20% damage 2t.", "formula": "All skill CDs reset. Gain +20% damage 2 turns", "type": "self_buff", "cost": 20, "cd": 8, "buff_type": "warpTime", "buff_duration": 2, "tags": ["support"], "tier": 3, "category": "utility", "stat_priority": ["int"]},

            # ── AURAS/CURSES ──
            {"name": "Mind Spike", "icon": "!", "unlock_lv": 2, "desc": "Psychic jab that saps the enemy's will.", "formula": "dmg = (5 + INTx1.5) x 1.0, weaken 2 turns", "type": "magic_debuff", "power": 1.0, "stat": "int", "effect": "weakened", "duration": 2, "cost": 8, "cd": 2, "tags": ["offensive", "debuff"], "tier": 1, "category": "auras_curses", "stat_priority": ["int"]},
            {"name": "Burning Sigil", "icon": "^", "unlock_lv": 4, "desc": "Brands the enemy with a searing sigil.", "formula": "dmg = (5 + INTx1.5) x 0.8 + Burn 6% HP/turn 3 turns", "type": "debuff", "effect": "burning", "duration": 3, "power": 0.8, "stat": "int", "cost": 10, "cd": 3, "tags": ["offensive", "debuff"], "tier": 1, "category": "auras_curses", "stat_priority": ["int"]},
            {"name": "Corrosive Hex", "icon": "%", "unlock_lv": 8, "desc": "Poison that eats at body and mind.", "formula": "dmg = (5 + INTx1.5) x 0.6 + Poison stacking to 5", "type": "magic_debuff", "power": 0.6, "stat": "int", "effect": "poisoned", "duration": 3, "cost": 12, "cd": 3, "tags": ["offensive", "debuff"], "tier": 2, "category": "auras_curses", "stat_priority": ["int"]},
            {"name": "Flash Freeze", "icon": "v", "unlock_lv": 4, "desc": "Snap-freeze the air around the foe.", "formula": "dmg = (5 + INTx1.5) x 1.3 + Freeze 2 turns", "type": "magic_debuff", "power": 1.3, "stat": "int", "effect": "freezing", "duration": 2, "cost": 12, "cd": 3, "tags": ["offensive", "debuff"], "tier": 2, "category": "auras_curses", "stat_priority": ["int"]},
            {"name": "Yellow Sign Curse", "icon": "Y", "unlock_lv": 8, "desc": "Brand the enemy with the Yellow Sign. -15% all stats 3t.", "formula": "Enemy: -15% all stats for 3 turns", "type": "debuff", "power": 0, "stat": "int", "cost": 12, "cd": 5, "effect": "weakened", "duration": 3, "tags": ["debuff"], "tier": 2, "category": "auras_curses", "stat_priority": ["int", "wis"]},
            {"name": "Aura of Madness", "icon": "A", "unlock_lv": 8, "desc": "Enemy loses 5% max HP/turn + Shock 3t.", "formula": "Enemy: 5% maxHP/turn drain + Shock 3 turns", "type": "debuff", "power": 0, "stat": "int", "cost": 15, "cd": 5, "effect": "shocked", "duration": 3, "tags": ["debuff"], "tier": 2, "category": "auras_curses", "stat_priority": ["int"]},
            {"name": "Dominate Mind", "icon": "|", "unlock_lv": 14, "desc": "Seize control. Enemy skips turn + takes damage.", "formula": "Enemy stunned 1 turn + dmg = INTx1.5", "type": "magic_debuff", "power": 1.5, "stat": "int", "effect": "shocked", "duration": 1, "cost": 18, "cd": 5, "tags": ["offensive", "debuff"], "tier": 3, "category": "auras_curses", "stat_priority": ["int"]},
            {"name": "Nether Storm", "icon": "$", "unlock_lv": 16, "desc": "Storm of dark energy. Hits hard and blinds.", "formula": "dmg = (5 + INTx2.0) x 2.6 + Blind 3 turns", "type": "magic_debuff", "power": 2.6, "stat": "int", "effect": "blinded", "duration": 3, "cost": 25, "cd": 6, "tags": ["offensive", "debuff"], "tier": 3, "category": "auras_curses", "stat_priority": ["int"]},
            {"name": "Curse of the Pallid Mask", "icon": "P", "unlock_lv": 18, "desc": "Doom. After 3 turns, instant kill if below 30% HP.", "formula": "After 3t: kill if enemy below 30% HP", "type": "debuff", "power": 0, "stat": "int", "cost": 25, "cd": 8, "effect": "doom", "duration": 3, "tags": ["debuff", "ultimate"], "tier": 3, "category": "auras_curses", "stat_priority": ["int", "wis"]},
            {"name": "The Yellow Sign", "icon": "Y", "unlock_lv": 19, "desc": "Invoke the Unspeakable. Massive damage + all debuffs.", "formula": "dmg = (5 + INTx1.5 + WISx1.0) x 3.0 + Burn+Petrify", "type": "mixed_magic", "power": 3.0, "stat": "int", "stat2": "wis", "stat2_mult": 1.0, "effect": "burning", "effect2": "petrified", "duration": 3, "cost": 30, "cd": 7, "tags": ["offensive", "ultimate"], "tier": 3, "category": "auras_curses", "stat_priority": ["int", "wis"]},

            # ── Extra existing skills ──
            {"name": "Reality Warp", "icon": "?", "unlock_lv": 10, "desc": "Warp spacetime around the target.", "formula": "dmg = (5 + INTx1.5 + WISx0.8) x 2.0 + Blind 2t", "type": "mixed_magic", "power": 2.0, "stat": "int", "stat2": "wis", "stat2_mult": 0.8, "effect": "blinded", "duration": 2, "cost": 20, "cd": 5, "tags": ["offensive", "dual-stat"], "tier": 3, "category": "offensive", "stat_priority": ["int", "wis"]},
        ],
    },

    "brute": {
        "name": "Brute of the Depths",
        "icon": "B",
        "desc": "Unstoppable force of raw power. High health, devastating physical attacks that grow stronger as you weaken.",
        "base_stats": {"int": 6, "str": 14, "agi": 8, "wis": 8, "luck": 5},
        "hp_base": 110, "hp_per_level": 10,
        "skills": [
            # ── OFFENSIVE ──
            {"name": "Crushing Blow", "icon": "*", "unlock_lv": 1, "desc": "A devastating overhead strike.", "formula": "dmg = ATKx1.6 + STRx0.8 physical", "type": "physical", "power": 1.6, "stat": "str", "cost": 0, "cd": 0, "tags": ["offensive"], "tier": 1, "category": "offensive", "stat_priority": ["str"]},
            {"name": "Quick Slash", "icon": "~", "unlock_lv": 1, "desc": "A fast, agile cut.", "formula": "dmg = ATKx1.2 + AGIx0.6, fast recovery", "type": "physical", "power": 1.2, "stat": "agi", "cost": 0, "cd": 0, "tags": ["offensive"], "tier": 1, "category": "offensive", "stat_priority": ["agi"]},
            {"name": "Savage Cleave", "icon": "C", "unlock_lv": 1, "desc": "Wild swing that cleaves through defenses.", "formula": "dmg = ATKx1.3 + STRx0.5", "type": "physical", "power": 1.3, "stat": "str", "cost": 0, "cd": 0, "tags": ["offensive"], "tier": 1, "category": "offensive", "stat_priority": ["str"]},
            {"name": "Piercing Strike", "icon": "#", "unlock_lv": 2, "desc": "Strike that ignores half defense.", "formula": "dmg = ATKx1.4 + STRx0.6, ignores 50% pDEF", "type": "physical", "power": 1.4, "stat": "str", "armor_pierce": 0.5, "cost": 8, "cd": 2, "tags": ["offensive"], "tier": 2, "category": "offensive", "stat_priority": ["str"]},
            {"name": "Last Stand", "icon": "@", "unlock_lv": 6, "desc": "Lower HP = harder you hit.", "formula": "dmg = ATKx1.0 + STRx1.0, x(1+(1-HP%)x2.0)", "type": "physical", "power": 1.0, "stat": "str", "scaling_low_hp": True, "cost": 10, "cd": 3, "tags": ["offensive"], "tier": 2, "category": "offensive", "stat_priority": ["str"]},
            {"name": "Blood Frenzy", "icon": "F", "unlock_lv": 6, "desc": "Damage increases as HP drops.", "formula": "dmg = ATKx1.5, scales with missing HP", "type": "physical", "power": 1.5, "stat": "str", "cost": 10, "cd": 3, "scaling_low_hp": True, "tags": ["offensive"], "tier": 2, "category": "offensive", "stat_priority": ["str"]},
            {"name": "Thunderclap", "icon": "-", "unlock_lv": 8, "desc": "Earth-shaking force with lightning.", "formula": "dmg = (ATKx1.2 + STRx0.8 + AGIx0.4), Shock 2t", "type": "mixed_phys", "power": 1.2, "stat": "str", "stat2": "agi", "stat2_mult": 0.4, "effect": "shocked", "duration": 2, "cost": 15, "cd": 4, "tags": ["offensive", "dual-stat"], "tier": 2, "category": "offensive", "stat_priority": ["str", "agi"]},
            {"name": "Rampage", "icon": "$", "unlock_lv": 12, "desc": "Unleash three wild strikes.", "formula": "dmg = ATKx0.9 x 3 hits + STRx0.5 each", "type": "physical", "power": 0.9, "stat": "str", "multihit": 3, "cost": 15, "cd": 4, "tags": ["offensive"], "tier": 3, "category": "offensive", "stat_priority": ["str"]},
            {"name": "Seismic Wave", "icon": "]", "unlock_lv": 16, "desc": "Channel fury through the ground.", "formula": "dmg = (ATKx1.5 + STRx1.2 + AGIx0.6) x 2.0", "type": "mixed_phys", "power": 2.0, "stat": "str", "stat2": "agi", "stat2_mult": 0.6, "cost": 22, "cd": 5, "tags": ["offensive", "dual-stat"], "tier": 3, "category": "offensive", "stat_priority": ["str", "agi"]},
            {"name": "Apocalypse Strike", "icon": "}", "unlock_lv": 19, "desc": "Channel all rage into one cataclysmic blow.", "formula": "dmg = (ATKx1.5 + STRx1.5 + AGIx0.8) x 3.5", "type": "mixed_phys", "power": 3.5, "stat": "str", "stat2": "agi", "stat2_mult": 0.8, "armor_pierce": 0.3, "cost": 30, "cd": 7, "tags": ["offensive", "ultimate"], "tier": 3, "category": "offensive", "stat_priority": ["str", "agi"]},

            # ── DEFENSIVE ──
            {"name": "Unnatural Vitality", "icon": "V", "unlock_lv": 1, "desc": "Regenerate 5% HP/turn for 3 turns.", "formula": "Self: regen 5% maxHP/turn for 3 turns", "type": "self_buff", "cost": 5, "cd": 4, "buff_type": "regen5", "buff_duration": 3, "tags": ["defensive"], "tier": 1, "category": "defensive", "stat_priority": ["str", "wis"]},
            {"name": "Iron Skin", "icon": ";", "unlock_lv": 10, "desc": "Harden your body against all harm.", "formula": "Self: pDEF+60%, mDEF+30% for 4 turns", "type": "self_buff", "cost": 10, "cd": 5, "buff_type": "ironSkin", "buff_duration": 4, "tags": ["defensive"], "tier": 2, "category": "defensive", "stat_priority": ["str", "wis"]},
            {"name": "Adrenaline Surge", "icon": "|", "unlock_lv": 10, "desc": "Heal based on missing HP. Huge recovery.", "formula": "Heal = (1 - HP%) x maxHP x 0.6", "type": "self_heal", "cost": 8, "cd": 5, "heal_calc": "missing_hp", "tags": ["defensive"], "tier": 2, "category": "defensive", "stat_priority": ["str"]},
            {"name": "Vampiric Strike", "icon": "+", "unlock_lv": 6, "desc": "Steal life from the enemy.", "formula": "dmg = ATKx1.5 + STRx0.5, heal 40% dealt", "type": "physical", "power": 1.5, "stat": "str", "lifesteal": 0.4, "cost": 12, "cd": 4, "tags": ["offensive", "defensive"], "tier": 2, "category": "defensive", "stat_priority": ["str"]},
            {"name": "Dreadnought", "icon": "N", "unlock_lv": 8, "desc": "Convert damage taken into ATK for 2 turns.", "formula": "Self: +ATK based on damage taken 2t", "type": "self_buff", "cost": 10, "cd": 5, "buff_type": "dreadnought", "buff_duration": 2, "tags": ["defensive", "support"], "tier": 2, "category": "defensive", "stat_priority": ["str"]},
            {"name": "Undying Fury", "icon": "[", "unlock_lv": 16, "desc": "Cannot die this turn. If <30% HP, full rage.", "formula": "Self: cannot die 1 turn. HP<30%: +100% DMG", "type": "self_buff", "cost": 15, "cd": 7, "buff_type": "undying", "buff_duration": 1, "tags": ["defensive", "support"], "tier": 3, "category": "defensive", "stat_priority": ["str"]},
            {"name": "Titanic Resilience", "icon": "T", "unlock_lv": 14, "desc": "Heal 40% maxHP + immune to debuffs 2t.", "formula": "Heal 40% maxHP, immune debuffs 2t", "type": "self_heal", "cost": 15, "cd": 7, "heal_calc": "titanResil", "tags": ["defensive"], "tier": 3, "category": "defensive", "stat_priority": ["str", "wis"]},
            {"name": "Bone Armor", "icon": "K", "unlock_lv": 12, "desc": "Shield that grows with each hit taken.", "formula": "shield = STRx3 + hits_takenx5", "type": "self_shield", "cost": 12, "cd": 5, "shield_calc": "str3_hits", "tags": ["defensive"], "tier": 3, "category": "defensive", "stat_priority": ["str"]},

            # ── UTILITY ──
            {"name": "Devour", "icon": "d", "unlock_lv": 1, "desc": "Consume fallen essence. Heal 15% maxHP.", "formula": "Heal 15% maxHP", "type": "self_heal", "cost": 0, "cd": 3, "heal_calc": "devour15", "tags": ["utility"], "tier": 1, "category": "utility", "stat_priority": ["str"]},
            {"name": "Guttural Chant", "icon": "g", "unlock_lv": 2, "desc": "pDEF+20%, mDEF+20% 3t.", "formula": "Self: pDEF+20%, mDEF+20% 3 turns", "type": "self_buff", "cost": 5, "cd": 4, "buff_type": "chant", "buff_duration": 3, "tags": ["utility"], "tier": 1, "category": "utility", "stat_priority": ["str", "wis"]},
            {"name": "Blood Ritual", "icon": "b", "unlock_lv": 6, "desc": "Sacrifice 15% HP. Gain +50 XP.", "formula": "Lose 15% HP, gain 50 XP", "type": "self_buff", "cost": 0, "cd": 8, "buff_type": "bloodRitual", "buff_duration": 0, "tags": ["utility"], "tier": 2, "category": "utility", "stat_priority": ["str"]},
            {"name": "Warpaint", "icon": "w", "unlock_lv": 4, "desc": "ATK permanently +2.", "formula": "Self: STR+2 permanently", "type": "self_buff", "cost": 0, "cd": 0, "buff_type": "permAtk2", "buff_duration": 0, "tags": ["utility"], "tier": 2, "category": "utility", "stat_priority": ["str"]},
            {"name": "Blood Scent", "icon": "S", "unlock_lv": 4, "desc": "+15% loot quality for 5 floors.", "formula": "Passive: +15% loot quality 5 floors", "type": "self_buff", "cost": 0, "cd": 0, "buff_type": "bloodScent", "buff_duration": 99, "tags": ["utility"], "tier": 2, "category": "utility", "stat_priority": ["luck"]},
            {"name": "Terrifying Presence", "icon": "t", "unlock_lv": 6, "desc": "Enemy ATK-25% 3t.", "formula": "Enemy: ATK-25% for 3 turns", "type": "debuff", "power": 0, "stat": "str", "cost": 8, "cd": 4, "effect": "weakened", "duration": 3, "tags": ["utility"], "tier": 2, "category": "utility", "stat_priority": ["str"]},
            {"name": "Undying Pact", "icon": "u", "unlock_lv": 16, "desc": "Cannot die 2t. +50% ATK. Heal 30% after.", "formula": "Self: undying 2t, +50% ATK, heal 30% after", "type": "self_buff", "cost": 15, "cd": 8, "buff_type": "undyingPact", "buff_duration": 2, "tags": ["utility", "ultimate"], "tier": 3, "category": "utility", "stat_priority": ["str"]},
            {"name": "Terror of the Deep", "icon": "D", "unlock_lv": 14, "desc": "Enemy ATK-30%, DEF-20% 3t.", "formula": "Enemy: ATK-30%, DEF-20% for 3 turns", "type": "debuff", "power": 0, "stat": "str", "cost": 12, "cd": 5, "effect": "weakened", "duration": 3, "tags": ["utility"], "tier": 3, "category": "utility", "stat_priority": ["str"]},

            # ── AURAS/CURSES ──
            {"name": "Intimidate", "icon": "!", "unlock_lv": 2, "desc": "Your roar shakes the enemy.", "formula": "No dmg. -20% enemy ATK 3 turns", "type": "debuff", "effect": "weakened", "duration": 3, "power": 0, "stat": "str", "cost": 5, "cd": 3, "tags": ["debuff"], "tier": 1, "category": "auras_curses", "stat_priority": ["str"]},
            {"name": "Ground Pound", "icon": "v", "unlock_lv": 4, "desc": "Slam the earth. Physical AoE pressure.", "formula": "dmg = ATKx1.3 + STRx0.9, Shock 2 turns", "type": "physical_debuff", "power": 1.3, "stat": "str", "effect": "shocked", "duration": 2, "cost": 10, "cd": 3, "tags": ["offensive", "debuff"], "tier": 2, "category": "auras_curses", "stat_priority": ["str"]},
            {"name": "Berserker Rage", "icon": "^", "unlock_lv": 4, "desc": "Embrace fury. +60% damage, lose 12% HP.", "formula": "Self: +60% DMG 1 turn, costs 12% max HP", "type": "self_buff", "cost": 5, "cd": 3, "buff_type": "rage", "buff_duration": 1, "tags": ["support"], "tier": 2, "category": "auras_curses", "stat_priority": ["str"]},
            {"name": "War Cry", "icon": "=", "unlock_lv": 8, "desc": "Rally yourself. +40% ATK, +20% crit 4 turns.", "formula": "Self: ATK+40%, CRIT+20% for 4 turns", "type": "self_buff", "cost": 10, "cd": 5, "buff_type": "atkCritUp", "buff_duration": 4, "tags": ["support"], "tier": 2, "category": "auras_curses", "stat_priority": ["str"]},
            {"name": "Aura of Blood", "icon": "A", "unlock_lv": 8, "desc": "Passive lifesteal 10% on all attacks 3t.", "formula": "Self: 10% lifesteal on all attacks 3t", "type": "self_buff", "cost": 10, "cd": 5, "buff_type": "bloodAura", "buff_duration": 3, "tags": ["support"], "tier": 2, "category": "auras_curses", "stat_priority": ["str"]},
            {"name": "Colossus Smash", "icon": "&", "unlock_lv": 12, "desc": "A blow that cracks defenses open.", "formula": "dmg = ATKx2.2 + STRx1.0, enemy pDEF-30% 3t", "type": "physical_debuff", "power": 2.2, "stat": "str", "effect": "weakened", "duration": 3, "cost": 18, "cd": 5, "tags": ["offensive", "debuff"], "tier": 3, "category": "auras_curses", "stat_priority": ["str"]},
            {"name": "Blood Price", "icon": ")", "unlock_lv": 14, "desc": "Sacrifice HP for devastating power.", "formula": "dmg = ATKx3.0 + STRx1.5, costs 25% max HP", "type": "physical", "power": 3.0, "stat": "str", "hp_cost": 0.25, "cost": 5, "cd": 5, "tags": ["offensive"], "tier": 3, "category": "auras_curses", "stat_priority": ["str"]},
            {"name": "Titan Slam", "icon": "(", "unlock_lv": 14, "desc": "The earth splits beneath your blow.", "formula": "dmg = ATKx2.8 + STRx1.2, Shock 2t (50% stun)", "type": "physical_debuff", "power": 2.8, "stat": "str", "effect": "shocked", "duration": 2, "cost": 20, "cd": 5, "tags": ["offensive", "debuff"], "tier": 3, "category": "auras_curses", "stat_priority": ["str"]},
            {"name": "Warlord's Command", "icon": "{", "unlock_lv": 18, "desc": "All buffs active: rage, war cry, iron skin.", "formula": "Apply rage + atkCritUp + ironSkin, costs 20% HP", "type": "self_buff", "cost": 15, "cd": 8, "buff_type": "warlord", "buff_duration": 3, "tags": ["support", "ultimate"], "tier": 3, "category": "auras_curses", "stat_priority": ["str"]},
            {"name": "Blood Curse of Yuggoth", "icon": "Y", "unlock_lv": 18, "desc": "Poison 5 stacks. All DoT +50% 3t.", "formula": "Enemy: Poison 5 stacks, all DoT +50% 3t", "type": "debuff", "power": 0.5, "stat": "str", "cost": 20, "cd": 6, "effect": "poisoned", "duration": 3, "tags": ["debuff"], "tier": 3, "category": "auras_curses", "stat_priority": ["str", "luck"]},

            # ── FILLER: Brute defensive/utility ──
            {"name": "Second Wind", "icon": "2", "unlock_lv": 4, "desc": "Gasp of life. Heal 20% maxHP + regen 3% 2t.", "formula": "Heal 20% maxHP, regen 3%/turn 2t", "type": "self_heal", "cost": 8, "cd": 5, "heal_calc": "secondWind", "tags": ["defensive"], "tier": 2, "category": "defensive", "stat_priority": ["str"]},
            {"name": "Abyssal Fortitude", "icon": "f", "unlock_lv": 14, "desc": "pDEF+50%, +1 barrier. 3t.", "formula": "Self: pDEF+50%, +1 barrier for 3 turns", "type": "self_buff", "cost": 12, "cd": 5, "buff_type": "abyssFort", "buff_duration": 3, "tags": ["defensive"], "tier": 3, "category": "defensive", "stat_priority": ["str", "wis"]},
            {"name": "Collector's Eye", "icon": "e", "unlock_lv": 2, "desc": "+10% loot quality 5 floors.", "formula": "Passive: +10% loot quality 5 floors", "type": "self_buff", "cost": 0, "cd": 0, "buff_type": "collectEye", "buff_duration": 99, "tags": ["utility"], "tier": 1, "category": "utility", "stat_priority": ["luck"]},
            {"name": "Thick Skull", "icon": "k", "unlock_lv": 10, "desc": "Permanent STR+1, WIS+1.", "formula": "Self: STR+1, WIS+1 permanently", "type": "self_buff", "cost": 0, "cd": 0, "buff_type": "thickSkull", "buff_duration": 0, "tags": ["utility"], "tier": 2, "category": "utility", "stat_priority": ["str", "wis"]},
        ],
    },

    "warden": {
        "name": "Warden of Thresholds",
        "icon": "W",
        "desc": "Master of shields and barriers. Absorb punishment, curse foes, and turn defense into devastating offense.",
        "base_stats": {"int": 8, "str": 6, "agi": 8, "wis": 14, "luck": 5},
        "hp_base": 90, "hp_per_level": 8,
        "skills": [
            # ── OFFENSIVE ──
            {"name": "Holy Strike", "icon": "~", "unlock_lv": 1, "desc": "Channel divine wrath into a smite.", "formula": "dmg = (5 + WISx1.3) x 1.4 eldritch", "type": "magic", "power": 1.4, "stat": "wis", "cost": 0, "cd": 0, "tags": ["offensive"], "tier": 1, "category": "offensive", "stat_priority": ["wis"]},
            {"name": "Shield Bash", "icon": "#", "unlock_lv": 2, "desc": "Strike with your shield. Scales with DEF.", "formula": "dmg = DEFx2.0 + WISx0.5, physical", "type": "physical", "power": 2.0, "stat": "wis", "def_scaling": True, "cost": 5, "cd": 2, "tags": ["offensive", "dual-stat"], "tier": 1, "category": "offensive", "stat_priority": ["wis", "str"]},
            {"name": "Smite the Unworthy", "icon": "S", "unlock_lv": 1, "desc": "Pure divine judgement. Pure WIS damage.", "formula": "dmg = (5 + WISx1.8) x 1.8", "type": "magic", "power": 1.8, "stat": "wis", "cost": 0, "cd": 0, "tags": ["offensive"], "tier": 1, "category": "offensive", "stat_priority": ["wis"]},
            {"name": "Divine Smite", "icon": "@", "unlock_lv": 6, "desc": "Holy fire that burns undead and eldritch.", "formula": "dmg = (5 + WISx1.5 + INTx0.5) x 2.0", "type": "mixed_magic", "power": 2.0, "stat": "wis", "stat2": "int", "stat2_mult": 0.5, "cost": 15, "cd": 3, "tags": ["offensive", "dual-stat"], "tier": 2, "category": "offensive", "stat_priority": ["wis", "int"]},
            {"name": "Retribution", "icon": "=", "unlock_lv": 8, "desc": "Damage scales with current shield.", "formula": "dmg = (5 + WISx1.2) x 1.0 + shieldx0.5", "type": "mixed_magic", "power": 1.0, "stat": "wis", "shield_scaling": 0.5, "cost": 12, "cd": 4, "tags": ["offensive", "dual-stat"], "tier": 2, "category": "offensive", "stat_priority": ["wis"]},
            {"name": "Sacrificial Curse", "icon": "-", "unlock_lv": 8, "desc": "Convert shield into devastating damage.", "formula": "dmg = (5 + WISx1.5) x 1.5 + consumed shield", "type": "curse", "power": 1.5, "stat": "wis", "cost": 0, "cd": 4, "consume_shield": True, "tags": ["offensive"], "tier": 2, "category": "offensive", "stat_priority": ["wis"]},
            {"name": "Pillar of Radiance", "icon": "P", "unlock_lv": 8, "desc": "A pillar of holy fire descends. Freeze 2t.", "formula": "dmg = (5 + WISx2.0) x 2.2 + Freeze 2t", "type": "magic_debuff", "power": 2.2, "stat": "wis", "effect": "freezing", "duration": 2, "cost": 15, "cd": 4, "tags": ["offensive", "debuff"], "tier": 2, "category": "offensive", "stat_priority": ["wis"]},
            {"name": "Banishment", "icon": "&", "unlock_lv": 12, "desc": "Smite with the power of the threshold.", "formula": "dmg = (5 + WISx2.0) x 2.8 + Shock 2 turns", "type": "magic_debuff", "power": 2.8, "stat": "wis", "effect": "shocked", "duration": 2, "cost": 20, "cd": 5, "tags": ["offensive", "debuff"], "tier": 3, "category": "offensive", "stat_priority": ["wis"]},
            {"name": "Hammer of Judgement", "icon": "(", "unlock_lv": 14, "desc": "A massive hammer of pure willpower.", "formula": "dmg = (5 + WISx2.0 + STRx0.8) x 2.5", "type": "mixed_magic", "power": 2.5, "stat": "wis", "stat2": "str", "stat2_mult": 0.8, "cost": 22, "cd": 5, "tags": ["offensive", "dual-stat"], "tier": 3, "category": "offensive", "stat_priority": ["wis", "str"]},
            {"name": "Wrath of the Threshold", "icon": "]", "unlock_lv": 16, "desc": "Channel all defensive power into offense.", "formula": "dmg = (5 + WISx2.5 + shieldx0.3) x 2.5", "type": "mixed_magic", "power": 2.5, "stat": "wis", "shield_scaling": 0.3, "cost": 22, "cd": 6, "tags": ["offensive"], "tier": 3, "category": "offensive", "stat_priority": ["wis"]},

            # ── DEFENSIVE ──
            {"name": "Warding Light", "icon": "*", "unlock_lv": 1, "desc": "Shimmer of protective light. Blocks 1 hit.", "formula": "Gain 1 barrier stack (max 3). Absorbs any hit.", "type": "self_buff", "cost": 0, "cd": 0, "buff_type": "barrier", "barrier_stacks": 1, "tags": ["defensive"], "tier": 1, "category": "defensive", "stat_priority": ["wis"]},
            {"name": "Purifying Touch", "icon": "!", "unlock_lv": 2, "desc": "Cleanse wounds with sacred power.", "formula": "Heal = WISx2 + 10 HP", "type": "self_heal", "cost": 5, "cd": 2, "heal_calc": "wis2_10", "tags": ["defensive"], "tier": 1, "category": "defensive", "stat_priority": ["wis"]},
            {"name": "Aegis Shield", "icon": "^", "unlock_lv": 4, "desc": "Summon a massive protective barrier.", "formula": "shield = WISx3 + INTx1.5, until broken", "type": "self_shield", "cost": 10, "cd": 4, "shield_calc": "wis3_int1", "tags": ["defensive"], "tier": 2, "category": "defensive", "stat_priority": ["wis", "int"]},
            {"name": "Consecrated Ground", "icon": "v", "unlock_lv": 4, "desc": "Heal over time while standing firm.", "formula": "Heal 8% maxHP/turn for 3 turns", "type": "self_buff", "cost": 10, "cd": 5, "buff_type": "regen", "buff_duration": 3, "tags": ["defensive", "support"], "tier": 2, "category": "defensive", "stat_priority": ["wis"]},
            {"name": "Arcane Ward", "icon": "+", "unlock_lv": 6, "desc": "Increase magic defense significantly.", "formula": "Self: mDEF+50% for 4 turns", "type": "self_buff", "cost": 8, "cd": 5, "buff_type": "mDefUp", "buff_duration": 4, "tags": ["defensive"], "tier": 2, "category": "defensive", "stat_priority": ["wis"]},
            {"name": "Lay on Hands", "icon": "L", "unlock_lv": 6, "desc": "Heal WISx3. Cleanse all debuffs.", "formula": "Heal = WISx3, remove all debuffs", "type": "self_heal", "cost": 12, "cd": 5, "heal_calc": "layOnHands", "tags": ["defensive"], "tier": 2, "category": "defensive", "stat_priority": ["wis"]},
            {"name": "Bulwark", "icon": ";", "unlock_lv": 10, "desc": "Become immovable. Massive defense boost.", "formula": "Self: pDEF+60%, mDEF+60% for 4 turns", "type": "self_buff", "cost": 12, "cd": 5, "buff_type": "bulwark", "buff_duration": 4, "tags": ["defensive"], "tier": 3, "category": "defensive", "stat_priority": ["wis"]},
            {"name": "Healing Light", "icon": "|", "unlock_lv": 10, "desc": "Burst of healing energy.", "formula": "Heal = WISx3 + INTx1.5 HP", "type": "self_heal", "cost": 12, "cd": 4, "heal_calc": "wis3_int1_heal", "tags": ["defensive"], "tier": 3, "category": "defensive", "stat_priority": ["wis", "int"]},
            {"name": "Divine Fortress", "icon": "$", "unlock_lv": 12, "desc": "Ultimate defense. +80% DEF, barriers.", "formula": "Self: pDEF/mDEF+80%, +2 barrier 3 turns", "type": "self_buff", "cost": 15, "cd": 6, "buff_type": "fortress", "buff_duration": 3, "tags": ["defensive", "ultimate"], "tier": 3, "category": "defensive", "stat_priority": ["wis"]},
            {"name": "Sanctuary", "icon": "[", "unlock_lv": 16, "desc": "Create a zone of absolute protection.", "formula": "Full barrier(3), shield=WISx4, heal WISx2", "type": "self_shield", "cost": 20, "cd": 7, "shield_calc": "sanctuary", "tags": ["defensive", "ultimate"], "tier": 3, "category": "defensive", "stat_priority": ["wis"]},

            # ── UTILITY ──
            {"name": "Threshold Sense", "icon": "q", "unlock_lv": 1, "desc": "+10% loot quality for 5 floors.", "formula": "Passive: +10% loot quality 5 floors", "type": "self_buff", "cost": 0, "cd": 0, "buff_type": "threshSense", "buff_duration": 99, "tags": ["utility"], "tier": 1, "category": "utility", "stat_priority": ["wis", "luck"]},
            {"name": "Inner Fire", "icon": "i", "unlock_lv": 2, "desc": "ATK+15%, DEF+15% 3t.", "formula": "Self: ATK+15%, DEF+15% for 3 turns", "type": "self_buff", "cost": 5, "cd": 4, "buff_type": "innerFire", "buff_duration": 3, "tags": ["utility"], "tier": 1, "category": "utility", "stat_priority": ["wis"]},
            {"name": "Divine Intervention", "icon": "I", "unlock_lv": 6, "desc": "Nullify next 2 attacks completely.", "formula": "Self: nullify next 2 incoming attacks", "type": "self_buff", "cost": 12, "cd": 6, "buff_type": "divineInterv", "buff_duration": 99, "tags": ["utility"], "tier": 2, "category": "utility", "stat_priority": ["wis"]},
            {"name": "Blessed Meditation", "icon": "M", "unlock_lv": 6, "desc": "Heal 20% HP + reduce 10 MAD.", "formula": "Heal 20% maxHP, -10 MAD", "type": "self_heal", "cost": 8, "cd": 5, "heal_calc": "meditation", "tags": ["utility"], "tier": 2, "category": "utility", "stat_priority": ["wis"]},
            {"name": "Hallowed Ground", "icon": "H", "unlock_lv": 8, "desc": "pDEF+40%, mDEF+40% 3t.", "formula": "Self: pDEF+40%, mDEF+40% for 3 turns", "type": "self_buff", "cost": 10, "cd": 5, "buff_type": "hallowed", "buff_duration": 3, "tags": ["utility"], "tier": 2, "category": "utility", "stat_priority": ["wis"]},
            {"name": "Martyr's Sacrifice", "icon": "R", "unlock_lv": 14, "desc": "Deal massive damage at cost of your own blood.", "formula": "dmg = WISx4, take 30% maxHP", "type": "mixed_magic", "power": 4.0, "stat": "wis", "hp_cost": 0.3, "cost": 10, "cd": 6, "tags": ["offensive"], "tier": 3, "category": "utility", "stat_priority": ["wis"]},
            {"name": "Voice of Command", "icon": "V", "unlock_lv": 14, "desc": "Enemy ATK-25%, DEF-25% 3t.", "formula": "Enemy: ATK-25%, DEF-25% for 3 turns", "type": "debuff", "power": 0, "stat": "wis", "cost": 12, "cd": 5, "effect": "weakened", "duration": 3, "tags": ["utility"], "tier": 3, "category": "utility", "stat_priority": ["wis"]},
            {"name": "Oath of the Warden", "icon": "O", "unlock_lv": 16, "desc": "Permanent WIS+2, STR+1.", "formula": "Self: WIS+2, STR+1 permanently", "type": "self_buff", "cost": 0, "cd": 0, "buff_type": "permWisStr", "buff_duration": 0, "tags": ["utility"], "tier": 3, "category": "utility", "stat_priority": ["wis", "str"]},

            # ── AURAS/CURSES ──
            {"name": "Curse of Frailty", "icon": "c", "unlock_lv": 1, "desc": "Enemy DEF-25% 3t.", "formula": "Enemy: DEF-25% for 3 turns", "type": "debuff", "power": 0, "stat": "wis", "cost": 5, "cd": 3, "effect": "weakened", "duration": 3, "tags": ["debuff"], "tier": 1, "category": "auras_curses", "stat_priority": ["wis"]},
            {"name": "Aura of Warding", "icon": "A", "unlock_lv": 4, "desc": "mDEF+30% 3t.", "formula": "Self: mDEF+30% for 3 turns", "type": "self_buff", "cost": 10, "cd": 5, "buff_type": "wardAura", "buff_duration": 3, "tags": ["support"], "tier": 2, "category": "auras_curses", "stat_priority": ["wis"]},
            {"name": "Hex of Silence", "icon": "h", "unlock_lv": 6, "desc": "Enemy stunned 1t.", "formula": "Enemy stunned for 1 turn", "type": "debuff", "power": 0, "stat": "wis", "cost": 12, "cd": 5, "effect": "shocked", "duration": 1, "tags": ["debuff"], "tier": 2, "category": "auras_curses", "stat_priority": ["wis"]},
            {"name": "Mark of Judgment", "icon": "J", "unlock_lv": 8, "desc": "Enemy takes +20% all damage 3t.", "formula": "Enemy: +20% damage taken for 3 turns", "type": "debuff", "power": 0, "stat": "wis", "cost": 10, "cd": 4, "effect": "judgmentMark", "duration": 3, "tags": ["debuff"], "tier": 2, "category": "auras_curses", "stat_priority": ["wis"]},
            {"name": "Oath of Protection", "icon": "{", "unlock_lv": 18, "desc": "Linked defense. Shield + regen for 3 turns.", "formula": "shield=WISx3, regen 10% HP/turn, barrier+1 for 3t", "type": "self_buff", "cost": 18, "cd": 7, "buff_type": "oath", "buff_duration": 3, "tags": ["defensive", "support", "ultimate"], "tier": 3, "category": "auras_curses", "stat_priority": ["wis"]},
            {"name": "Seal of Carcosa", "icon": "}", "unlock_lv": 19, "desc": "The ultimate ward. Full heal + massive shield + damage.", "formula": "Full heal, shield=WISx5, barrier x3, dmg WISx3", "type": "ultimate", "power": 3.0, "stat": "wis", "cost": 30, "cd": 8, "tags": ["offensive", "defensive", "ultimate"], "tier": 3, "category": "auras_curses", "stat_priority": ["wis"]},
            {"name": "Aura of Retribution", "icon": "r", "unlock_lv": 14, "desc": "Reflect 30% damage taken back. 3t.", "formula": "Self: reflect 30% damage taken for 3 turns", "type": "self_buff", "cost": 15, "cd": 6, "buff_type": "retribAura", "buff_duration": 3, "tags": ["support"], "tier": 3, "category": "auras_curses", "stat_priority": ["wis"]},
            {"name": "Curse of Waning", "icon": "w", "unlock_lv": 16, "desc": "Enemy loses 2 to random stat each turn 3t.", "formula": "Enemy: -2 random stat/turn for 3 turns", "type": "debuff", "power": 0, "stat": "wis", "cost": 18, "cd": 6, "effect": "waning", "duration": 3, "tags": ["debuff"], "tier": 3, "category": "auras_curses", "stat_priority": ["wis"]},
            {"name": "The Warden's Final Stand", "icon": "F", "unlock_lv": 18, "desc": "Invulnerable 1t. Full heal + barrier x3.", "formula": "Self: invulnerable 1t, full heal, barrier x3", "type": "self_buff", "cost": 25, "cd": 10, "buff_type": "finalStand", "buff_duration": 1, "tags": ["defensive", "ultimate"], "tier": 3, "category": "auras_curses", "stat_priority": ["wis"]},
            {"name": "Martyr's Wrath", "icon": ")", "unlock_lv": 14, "desc": "Sacrifice HP for devastating power.", "formula": "dmg = (5 + WISx2.0 + INTx1.0) x 2.5, 20% HP", "type": "mixed_magic", "power": 2.5, "stat": "wis", "stat2": "int", "stat2_mult": 1.0, "hp_cost": 0.2, "cost": 10, "cd": 5, "tags": ["offensive", "dual-stat"], "tier": 3, "category": "auras_curses", "stat_priority": ["wis", "int"]},

            # ── FILLER: Warden utility ──
            {"name": "Warden's Insight", "icon": "W", "unlock_lv": 4, "desc": "+10% loot quality 5 floors.", "formula": "Passive: +10% loot quality 5 floors", "type": "self_buff", "cost": 0, "cd": 0, "buff_type": "wardenInsight", "buff_duration": 99, "tags": ["utility"], "tier": 1, "category": "utility", "stat_priority": ["wis", "luck"]},
            {"name": "Perseverance", "icon": "Q", "unlock_lv": 12, "desc": "Permanent WIS+1, STR+1.", "formula": "Self: WIS+1, STR+1 permanently", "type": "self_buff", "cost": 0, "cd": 0, "buff_type": "perseverance", "buff_duration": 0, "tags": ["utility"], "tier": 3, "category": "utility", "stat_priority": ["wis", "str"]},
        ],
    },

    "shadowblade": {
        "name": "Shadowblade of Carcosa",
        "icon": "D",
        "desc": "Swift and deadly. Critical strikes, evasion, and poison. Glass cannon that dances on the edge of death.",
        "base_stats": {"int": 7, "str": 7, "agi": 14, "wis": 7, "luck": 8},
        "hp_base": 75, "hp_per_level": 7,
        "skills": [
            # ── OFFENSIVE ──
            {"name": "Shadow Strike", "icon": "*", "unlock_lv": 1, "desc": "A swift strike from the shadows.", "formula": "dmg = ATKx1.5 + AGIx1.0 physical", "type": "physical", "power": 1.5, "stat": "agi", "cost": 0, "cd": 0, "tags": ["offensive"], "tier": 1, "category": "offensive", "stat_priority": ["agi"]},
            {"name": "Backstab", "icon": "#", "unlock_lv": 2, "desc": "Strike from behind. +50% crit chance.", "formula": "dmg = ATKx1.8 + AGIx0.5, +50% CRIT", "type": "physical", "power": 1.8, "stat": "agi", "flat_crit_bonus": 50, "cost": 8, "cd": 2, "tags": ["offensive"], "tier": 1, "category": "offensive", "stat_priority": ["agi"]},
            {"name": "Quick Stab", "icon": "Q", "unlock_lv": 1, "desc": "Fast strike. 2 rapid hits.", "formula": "dmg = ATKx1.2 + AGIx0.5, 2 hits", "type": "physical", "power": 1.2, "stat": "agi", "multihit": 2, "cost": 0, "cd": 0, "tags": ["offensive"], "tier": 1, "category": "offensive", "stat_priority": ["agi"]},
            {"name": "Blade Dance", "icon": "v", "unlock_lv": 4, "desc": "Unleash a flurry of precise strikes.", "formula": "dmg = ATKx0.7 x 4 hits", "type": "physical", "power": 0.7, "stat": "agi", "multihit": 4, "cost": 12, "cd": 3, "tags": ["offensive"], "tier": 2, "category": "offensive", "stat_priority": ["agi"]},
            {"name": "Siphon Life", "icon": "@", "unlock_lv": 6, "desc": "Drain the enemy's vitality.", "formula": "dmg = ATKx1.4 + AGIx0.6, heal 50% dealt", "type": "physical", "power": 1.4, "stat": "agi", "lifesteal": 0.5, "cost": 12, "cd": 3, "tags": ["offensive", "defensive"], "tier": 2, "category": "offensive", "stat_priority": ["agi"]},
            {"name": "Assassinate", "icon": "|", "unlock_lv": 10, "desc": "Instant kill attempt on weakened foes.", "formula": "dmg = ATKx3.0 + AGIx2.0 if <25% HP", "type": "physical", "power": 3.0, "stat": "agi", "execute_bonus": True, "cost": 20, "cd": 5, "tags": ["offensive", "ultimate"], "tier": 2, "category": "offensive", "stat_priority": ["agi"]},
            {"name": "Shuriken Storm", "icon": "=", "unlock_lv": 8, "desc": "Hurl shuriken in all directions.", "formula": "dmg = ATKx0.5 x 5 hits + LUK scaling", "type": "physical", "power": 0.5, "stat": "agi", "multihit": 5, "luck_bonus": True, "cost": 15, "cd": 4, "tags": ["offensive"], "tier": 2, "category": "offensive", "stat_priority": ["agi", "luck"]},
            {"name": "Crimson Flurry", "icon": "(", "unlock_lv": 14, "desc": "Six rapid strikes, each more deadly.", "formula": "dmg = ATKx0.6 x 6 + STRx0.3", "type": "mixed_phys", "power": 0.6, "stat": "agi", "stat2": "str", "stat2_mult": 0.3, "multihit": 6, "cost": 22, "cd": 5, "tags": ["offensive"], "tier": 3, "category": "offensive", "stat_priority": ["agi", "str"]},
            {"name": "Phantom Blades", "icon": "{", "unlock_lv": 18, "desc": "Ethereal blades that bypass all defense.", "formula": "dmg = ATKx1.0 x 4, ignores 100% DEF", "type": "physical", "power": 1.0, "stat": "agi", "multihit": 4, "armor_pierce": 1.0, "cost": 25, "cd": 6, "tags": ["offensive"], "tier": 3, "category": "offensive", "stat_priority": ["agi"]},
            {"name": "Death's Embrace", "icon": "}", "unlock_lv": 19, "desc": "The final dance. Massive damage + all debuffs.", "formula": "dmg = (ATKx1.5 + AGIx2.0) x 3.0 + Bleed+Poison", "type": "mixed_phys", "power": 3.0, "stat": "agi", "stat2": "str", "stat2_mult": 0.5, "effect": "bleeding", "effect2": "poisoned", "duration": 3, "cost": 30, "cd": 7, "tags": ["offensive", "ultimate"], "tier": 3, "category": "offensive", "stat_priority": ["agi", "str"]},

            # ── DEFENSIVE ──
            {"name": "Smoke Screen", "icon": "!", "unlock_lv": 2, "desc": "Vanish in smoke. EVA +25% 2 turns.", "formula": "Self: EVA+25% for 2 turns", "type": "self_buff", "cost": 5, "cd": 3, "buff_type": "smokeScreen", "buff_duration": 2, "tags": ["defensive"], "tier": 1, "category": "defensive", "stat_priority": ["agi"]},
            {"name": "Flicker", "icon": "F", "unlock_lv": 1, "desc": "50% to dodge next 2 attacks.", "formula": "Self: 50% dodge next 2 attacks", "type": "self_buff", "cost": 5, "cd": 3, "buff_type": "flicker", "buff_duration": 2, "tags": ["defensive"], "tier": 1, "category": "defensive", "stat_priority": ["agi"]},
            {"name": "Evasion", "icon": "+", "unlock_lv": 6, "desc": "Become nearly untouchable. EVA+40% 3t.", "formula": "Self: EVA+40% for 3 turns", "type": "self_buff", "cost": 8, "cd": 5, "buff_type": "evasionUp", "buff_duration": 3, "tags": ["defensive"], "tier": 2, "category": "defensive", "stat_priority": ["agi"]},
            {"name": "Shadow Meld", "icon": ";", "unlock_lv": 10, "desc": "Become one with shadow. Invisible 1 turn.", "formula": "Self: cannot be hit 1 turn, next attack +100%", "type": "self_buff", "cost": 12, "cd": 5, "buff_type": "shadowMeld", "buff_duration": 1, "tags": ["defensive", "support"], "tier": 2, "category": "defensive", "stat_priority": ["agi"]},
            {"name": "Mirror Images", "icon": "I", "unlock_lv": 6, "desc": "Create illusory copies. 30% damage reduction 2t.", "formula": "Self: 30% DMG reduction for 2 turns", "type": "self_buff", "cost": 10, "cd": 4, "buff_type": "mirrorImg", "buff_duration": 2, "tags": ["defensive"], "tier": 2, "category": "defensive", "stat_priority": ["agi"]},
            {"name": "Ethereal Jaunt", "icon": "E", "unlock_lv": 14, "desc": "Cannot be hit 1 turn. Next attack +150%.", "formula": "Self: invulnerable 1t, next attack +150%", "type": "self_buff", "cost": 15, "cd": 6, "buff_type": "ethereal", "buff_duration": 1, "tags": ["defensive"], "tier": 3, "category": "defensive", "stat_priority": ["agi"]},
            {"name": "Umbral Aegis", "icon": "U", "unlock_lv": 14, "desc": "EVA+60%, pDEF+40% 2t.", "formula": "Self: EVA+60%, pDEF+40% for 2 turns", "type": "self_buff", "cost": 12, "cd": 5, "buff_type": "umbralAegis", "buff_duration": 2, "tags": ["defensive"], "tier": 3, "category": "defensive", "stat_priority": ["agi"]},
            {"name": "Dark Regeneration", "icon": "R", "unlock_lv": 12, "desc": "Heal 30% + EVA+20% 2t.", "formula": "Heal 30% maxHP, EVA+20% 2 turns", "type": "self_heal", "cost": 10, "cd": 5, "heal_calc": "darkRegen", "tags": ["defensive"], "tier": 3, "category": "defensive", "stat_priority": ["agi"]},

            # ── UTILITY ──
            {"name": "Sixth Sense", "icon": "6", "unlock_lv": 1, "desc": "Crit permanently +10%.", "formula": "Self: CRIT+10% permanently", "type": "self_buff", "cost": 0, "cd": 0, "buff_type": "permCrit10", "buff_duration": 0, "tags": ["utility"], "tier": 1, "category": "utility", "stat_priority": ["agi", "luck"]},
            {"name": "Nimble Fingers", "icon": "n", "unlock_lv": 1, "desc": "+20% loot quality for 5 floors.", "formula": "Passive: +20% loot quality 5 floors", "type": "self_buff", "cost": 0, "cd": 0, "buff_type": "nimbleFingers", "buff_duration": 99, "tags": ["utility"], "tier": 1, "category": "utility", "stat_priority": ["agi", "luck"]},
            {"name": "Adrenaline Rush", "icon": "a", "unlock_lv": 6, "desc": "Reset all cooldowns.", "formula": "All skill CDs reset to 0", "type": "self_buff", "cost": 10, "cd": 8, "buff_type": "resetCds", "buff_duration": 0, "tags": ["support"], "tier": 2, "category": "utility", "stat_priority": ["agi"]},
            {"name": "Shadow Step (Utility)", "icon": "s", "unlock_lv": 4, "desc": "Skip next combat encounter.", "formula": "Passive: skip next combat", "type": "self_buff", "cost": 0, "cd": 0, "buff_type": "skipCombat", "buff_duration": 99, "tags": ["utility"], "tier": 2, "category": "utility", "stat_priority": ["agi"]},
            {"name": "Dark Pact", "icon": ")", "unlock_lv": 14, "desc": "Trade HP for devastating poison mastery.", "formula": "All debuffs +2 duration, +30% dmg, costs 15% HP", "type": "self_buff", "cost": 8, "cd": 6, "buff_type": "darkPact", "buff_duration": 3, "tags": ["support"], "tier": 2, "category": "utility", "stat_priority": ["agi"]},
            {"name": "Perfect Assassin", "icon": "P", "unlock_lv": 16, "desc": "Permanent AGI+2, LUCK+1.", "formula": "Self: AGI+2, LUCK+1 permanently", "type": "self_buff", "cost": 0, "cd": 0, "buff_type": "permAgiLuk", "buff_duration": 0, "tags": ["utility"], "tier": 3, "category": "utility", "stat_priority": ["agi", "luck"]},
            {"name": "Living Shadow", "icon": "L", "unlock_lv": 16, "desc": "Copy enemy's last attack for 3t.", "formula": "Self: copy enemy attack for 3 turns", "type": "self_buff", "cost": 12, "cd": 5, "buff_type": "copyAttack", "buff_duration": 3, "tags": ["utility"], "tier": 3, "category": "utility", "stat_priority": ["agi"]},

            # ── AURAS/CURSES ──
            {"name": "Venom Blade", "icon": "~", "unlock_lv": 1, "desc": "Coat your blade in eldritch poison.", "formula": "dmg = ATKx1.2 + Poison 3 turns", "type": "physical_debuff", "power": 1.2, "stat": "agi", "effect": "poisoned", "duration": 3, "cost": 5, "cd": 2, "tags": ["offensive", "debuff"], "tier": 1, "category": "auras_curses", "stat_priority": ["agi"]},
            {"name": "Poison Cloud", "icon": "^", "unlock_lv": 4, "desc": "Envelop the enemy in toxic gas.", "formula": "dmg = ATKx0.5 + Poison stacking to 5", "type": "debuff", "power": 0.5, "stat": "agi", "effect": "poisoned", "duration": 3, "cost": 10, "cd": 3, "tags": ["debuff"], "tier": 2, "category": "auras_curses", "stat_priority": ["agi"]},
            {"name": "Wound", "icon": "-", "unlock_lv": 8, "desc": "Deep cut that bleeds profusely.", "formula": "dmg = ATKx1.0 + Bleed 5% HP/turn 3t", "type": "physical_debuff", "power": 1.0, "stat": "agi", "effect": "bleeding", "duration": 3, "cost": 10, "cd": 3, "tags": ["offensive", "debuff"], "tier": 2, "category": "auras_curses", "stat_priority": ["agi"]},
            {"name": "Curse of Vulnerability", "icon": "c", "unlock_lv": 6, "desc": "Enemy pDEF-30%, mDEF-25% 3t.", "formula": "Enemy: pDEF-30%, mDEF-25% for 3 turns", "type": "debuff", "power": 0, "stat": "agi", "cost": 10, "cd": 4, "effect": "weakened", "duration": 3, "tags": ["debuff"], "tier": 2, "category": "auras_curses", "stat_priority": ["agi"]},
            {"name": "Garrote", "icon": "G", "unlock_lv": 4, "desc": "Choke hold. Shock 2t.", "formula": "dmg = ATKx1.5 + Shock 2 turns", "type": "physical_debuff", "power": 1.5, "stat": "agi", "effect": "shocked", "duration": 2, "cost": 10, "cd": 3, "tags": ["offensive", "debuff"], "tier": 2, "category": "auras_curses", "stat_priority": ["agi"]},
            {"name": "Toxic Blade", "icon": "$", "unlock_lv": 12, "desc": "Deadly poison that ignores resist.", "formula": "dmg = ATKx1.5 + Poison 5 stacks, ignores 30% DEF", "type": "physical_debuff", "power": 1.5, "stat": "agi", "effect": "poisoned", "duration": 3, "armor_pierce": 0.3, "cost": 15, "cd": 4, "tags": ["offensive", "debuff"], "tier": 3, "category": "auras_curses", "stat_priority": ["agi"]},
            {"name": "Nightmare", "icon": "[", "unlock_lv": 16, "desc": "Plunge enemy into waking nightmare.", "formula": "dmg = ATKx2.0 + Blind+Shocked 3 turns", "type": "physical_debuff", "power": 2.0, "stat": "agi", "effect": "blinded", "effect2": "shocked", "duration": 3, "cost": 25, "cd": 6, "tags": ["offensive", "debuff"], "tier": 3, "category": "auras_curses", "stat_priority": ["agi"]},
            {"name": "Eclipse", "icon": "]", "unlock_lv": 16, "desc": "Eclipse of light. All attacks crit 2 turns.", "formula": "Self: 100% CRIT, +30% DMG 2 turns", "type": "self_buff", "cost": 15, "cd": 6, "buff_type": "eclipse", "buff_duration": 2, "tags": ["support"], "tier": 3, "category": "auras_curses", "stat_priority": ["agi"]},
            {"name": "Aura of Blades", "icon": "A", "unlock_lv": 14, "desc": "15% chance counter for 30% ATK. 3t.", "formula": "Self: 15% counter 30% ATK for 3 turns", "type": "self_buff", "cost": 12, "cd": 5, "buff_type": "bladeAura", "buff_duration": 3, "tags": ["support"], "tier": 3, "category": "auras_curses", "stat_priority": ["agi"]},
            {"name": "Death Mark", "icon": "M", "unlock_lv": 18, "desc": "Mark enemy. All hits crit for 3 turns.", "formula": "Enemy: all hits crit against them for 3t", "type": "debuff", "power": 0, "stat": "agi", "cost": 20, "cd": 8, "effect": "deathMark", "duration": 3, "tags": ["debuff", "ultimate"], "tier": 3, "category": "auras_curses", "stat_priority": ["agi", "luck"]},

            # ── Extra existing ──
            {"name": "Shadow Step", "icon": "&", "unlock_lv": 12, "desc": "Teleport behind enemy. Guaranteed crit.", "formula": "dmg = ATKx2.0 + AGIx1.0, guaranteed crit", "type": "physical", "power": 2.0, "stat": "agi", "guaranteed_crit": True, "cost": 18, "cd": 4, "tags": ["offensive"], "tier": 3, "category": "offensive", "stat_priority": ["agi"]},

            # ── FILLER: Shadowblade defensive/utility ──
            {"name": "Fade to Black", "icon": "B", "unlock_lv": 4, "desc": "EVA+20%, regen 5% 2t.", "formula": "Self: EVA+20%, regen 5% HP/turn 2t", "type": "self_buff", "cost": 8, "cd": 4, "buff_type": "fadeBlack", "buff_duration": 2, "tags": ["defensive"], "tier": 2, "category": "defensive", "stat_priority": ["agi"]},
            {"name": "Nimble Recovery", "icon": "N", "unlock_lv": 14, "desc": "Heal 25% + EVA+15% 2t.", "formula": "Heal 25% maxHP, EVA+15% 2t", "type": "self_heal", "cost": 10, "cd": 5, "heal_calc": "nimbleRecov", "tags": ["defensive"], "tier": 3, "category": "defensive", "stat_priority": ["agi"]},
            {"name": "Looter's Instinct", "icon": "l", "unlock_lv": 2, "desc": "+10% loot quality 5 floors.", "formula": "Passive: +10% loot quality 5 floors", "type": "self_buff", "cost": 0, "cd": 0, "buff_type": "looterInst", "buff_duration": 99, "tags": ["utility"], "tier": 1, "category": "utility", "stat_priority": ["agi", "luck"]},
            {"name": "Shadow's Blessing", "icon": "b", "unlock_lv": 10, "desc": "Permanent AGI+1, LUCK+1.", "formula": "Self: AGI+1, LUCK+1 permanently", "type": "self_buff", "cost": 0, "cd": 0, "buff_type": "shadowBless", "buff_duration": 0, "tags": ["utility"], "tier": 2, "category": "utility", "stat_priority": ["agi", "luck"]},
        ],
    },

    "mad_prophet": {
        "name": "Mad Prophet of Hastur",
        "icon": "P",
        "desc": "Blessed and cursed by visions. Powerful debuffs, madness manipulation, and chaos. High risk, high reward.",
        "base_stats": {"int": 10, "str": 5, "agi": 7, "wis": 12, "luck": 9},
        "hp_base": 80, "hp_per_level": 7,
        "skills": [
            # ── OFFENSIVE ──
            {"name": "Prophetic Vision", "icon": "*", "unlock_lv": 1, "desc": "A flash of terrible insight, weaponized.", "formula": "dmg = (5 + WISx1.5) x 1.3 magic", "type": "magic", "power": 1.3, "stat": "wis", "cost": 0, "cd": 0, "tags": ["offensive"], "tier": 1, "category": "offensive", "stat_priority": ["wis"]},
            {"name": "Channel Madness", "icon": "#", "unlock_lv": 2, "desc": "Convert madness into power.", "formula": "dmg = WISx2.0 x (1 + MAD/100), costs 5 MAD", "type": "magic", "power": 1.0, "stat": "wis", "madness_scaling": True, "madness_cost": 5, "cost": 0, "cd": 2, "tags": ["offensive"], "tier": 1, "category": "offensive", "stat_priority": ["wis"]},
            {"name": "Coin of Chaos", "icon": "C", "unlock_lv": 1, "desc": "Flip a coin of cosmic fate.", "formula": "50%: 2x damage OR heal enemy 10%", "type": "magic", "power": 1.5, "stat": "wis", "coin_flip": True, "cost": 5, "cd": 2, "tags": ["offensive"], "tier": 1, "category": "offensive", "stat_priority": ["wis", "luck"]},
            {"name": "Visions of Carcosa", "icon": "v", "unlock_lv": 4, "desc": "Show the enemy the truth. Petrify + damage.", "formula": "dmg = (5 + WISx1.5) x 1.5 + Petrify 2t", "type": "magic_debuff", "power": 1.5, "stat": "wis", "effect": "petrified", "duration": 2, "cost": 12, "cd": 3, "tags": ["offensive", "debuff"], "tier": 2, "category": "offensive", "stat_priority": ["wis"]},
            {"name": "Scream of Madness", "icon": "=", "unlock_lv": 8, "desc": "AoE scream that damages and debuffs.", "formula": "dmg = (5 + WISx1.5) x 1.8 + Weaken 3t", "type": "magic_debuff", "power": 1.8, "stat": "wis", "effect": "weakened", "duration": 3, "cost": 18, "cd": 4, "tags": ["offensive", "debuff"], "tier": 2, "category": "offensive", "stat_priority": ["wis"]},
            {"name": "Unstable Bolt", "icon": "U", "unlock_lv": 6, "desc": "Damage between 0.3x and 2.5x.", "formula": "dmg = (5 + WISx2.0) x 0.3~2.5 random", "type": "magic", "power": 1.8, "stat": "wis", "gamble": True, "cost": 12, "cd": 3, "tags": ["offensive"], "tier": 2, "category": "offensive", "stat_priority": ["wis"]},
            {"name": "Gamble of Fate", "icon": "$", "unlock_lv": 12, "desc": "Random damage between 0.5x and 3.0x.", "formula": "dmg = (5 + WISx2.0) x 0.5~3.0 random", "type": "magic", "power": 2.0, "stat": "wis", "gamble": True, "cost": 12, "cd": 3, "tags": ["offensive"], "tier": 3, "category": "offensive", "stat_priority": ["wis"]},
            {"name": "Madness Nova", "icon": "(", "unlock_lv": 14, "desc": "Explode with eldritch energy.", "formula": "dmg = (5 + WISx2.0) x 2.5 + Burn 3t", "type": "magic_debuff", "power": 2.5, "stat": "wis", "effect": "burning", "duration": 3, "cost": 22, "cd": 5, "tags": ["offensive", "debuff"], "tier": 3, "category": "offensive", "stat_priority": ["wis"]},
            {"name": "Apocalyptic Dream", "icon": "[", "unlock_lv": 16, "desc": "The world ends in your dream. Massive damage.", "formula": "dmg = (5 + WISx2.5 + INTx1.0) x 2.8", "type": "mixed_magic", "power": 2.8, "stat": "wis", "stat2": "int", "stat2_mult": 1.0, "cost": 25, "cd": 6, "tags": ["offensive"], "tier": 3, "category": "offensive", "stat_priority": ["wis", "int"]},
            {"name": "Hastur's Decree", "icon": "}", "unlock_lv": 19, "desc": "Invoke the King himself. Ultimate destruction.", "formula": "dmg = (5 + WISx2.0 + INTx1.5) x 3.5 + ALL debuffs", "type": "mixed_magic", "power": 3.5, "stat": "wis", "stat2": "int", "stat2_mult": 1.5, "effect": "burning", "effect2": "petrified", "effect3": "blinded", "duration": 3, "cost": 35, "cd": 8, "tags": ["offensive", "ultimate"], "tier": 3, "category": "offensive", "stat_priority": ["wis", "int"]},

            # ── DEFENSIVE ──
            {"name": "Healing Hysteria", "icon": "+", "unlock_lv": 6, "desc": "Laugh until you're healed. Or scream.", "formula": "Heal = WISx2.5 + LUKx1, +5 MAD", "type": "self_heal", "cost": 0, "cd": 3, "heal_calc": "wis2_luck1", "tags": ["defensive"], "tier": 1, "category": "defensive", "stat_priority": ["wis", "luck"]},
            {"name": "Lucky Dodge", "icon": "L", "unlock_lv": 1, "desc": "EVA+35% 2t. Luck scaling.", "formula": "Self: EVA+35% for 2 turns", "type": "self_buff", "cost": 5, "cd": 3, "buff_type": "luckyDodge", "buff_duration": 2, "tags": ["defensive"], "tier": 1, "category": "defensive", "stat_priority": ["luck"]},
            {"name": "Carcosa's Blessing", "icon": "|", "unlock_lv": 10, "desc": "Full heal but gain +25 MAD.", "formula": "Full HP restore, +25 MAD", "type": "self_heal", "cost": 0, "cd": 8, "heal_calc": "full_heal", "tags": ["defensive"], "tier": 2, "category": "defensive", "stat_priority": ["wis"]},
            {"name": "Madness Shell", "icon": "S", "unlock_lv": 4, "desc": "shield=WISx2 + current MAD. +10 MAD.", "formula": "shield = WISx2 + current MAD, +10 MAD", "type": "self_shield", "cost": 0, "cd": 4, "shield_calc": "madShell", "tags": ["defensive"], "tier": 2, "category": "defensive", "stat_priority": ["wis"]},
            {"name": "The Fool's Luck", "icon": "f", "unlock_lv": 6, "desc": "Nullify next 3 attacks. -10 MAD.", "formula": "Self: nullify next 3 attacks, -10 MAD", "type": "self_buff", "cost": 8, "cd": 6, "buff_type": "foolLuck", "buff_duration": 99, "tags": ["defensive"], "tier": 2, "category": "defensive", "stat_priority": ["luck"]},
            {"name": "Hastur's Embrace", "icon": "H", "unlock_lv": 16, "desc": "Full heal + immune debuffs 2t. +20 MAD.", "formula": "Full heal, immune debuffs 2t, +20 MAD", "type": "self_heal", "cost": 0, "cd": 8, "heal_calc": "hasturEmbrace", "tags": ["defensive"], "tier": 3, "category": "defensive", "stat_priority": ["wis"]},
            {"name": "Reality Anchor", "icon": "A", "unlock_lv": 16, "desc": "Cannot die 2 turns.", "formula": "Self: cannot die for 2 turns", "type": "self_buff", "cost": 15, "cd": 8, "buff_type": "realityAnchor", "buff_duration": 2, "tags": ["defensive"], "tier": 3, "category": "defensive", "stat_priority": ["wis"]},
            {"name": "Madness Barrier", "icon": "B", "unlock_lv": 12, "desc": "shield=WISx3 + LUCKx2.", "formula": "shield = WISx3 + LUCKx2", "type": "self_shield", "cost": 15, "cd": 5, "shield_calc": "madBarrier", "tags": ["defensive"], "tier": 3, "category": "defensive", "stat_priority": ["wis", "luck"]},

            # ── UTILITY ──
            {"name": "Prophetic Insight", "icon": "p", "unlock_lv": 1, "desc": "+2 to a random stat.", "formula": "Self: +2 to 2 random stats", "type": "self_buff", "cost": 0, "cd": 0, "buff_type": "randStat2", "buff_duration": 0, "tags": ["utility"], "tier": 1, "category": "utility", "stat_priority": ["wis"]},
            {"name": "Fate Reading", "icon": "r", "unlock_lv": 1, "desc": "Preview paths 2 floors ahead.", "formula": "Passive: see upcoming paths", "type": "self_buff", "cost": 0, "cd": 0, "buff_type": "fateRead", "buff_duration": 99, "tags": ["utility"], "tier": 1, "category": "utility", "stat_priority": ["wis", "luck"]},
            {"name": "Empower Madness", "icon": "@", "unlock_lv": 6, "desc": "Gain power from madness. +MAD = +DMG.", "formula": "Self: +25% DMG, +15 MAD 3 turns", "type": "self_buff", "cost": 0, "cd": 4, "buff_type": "madPower", "buff_duration": 3, "tags": ["support"], "tier": 2, "category": "utility", "stat_priority": ["wis"]},
            {"name": "Lucky Coin Toss", "icon": "t", "unlock_lv": 4, "desc": "Reroll next loot drop quality.", "formula": "Passive: reroll next loot quality", "type": "self_buff", "cost": 5, "cd": 0, "buff_type": "rerollLoot", "buff_duration": 99, "tags": ["utility"], "tier": 2, "category": "utility", "stat_priority": ["luck"]},
            {"name": "Eldritch Bargain", "icon": "b", "unlock_lv": 6, "desc": "Lose 3 random stats. Gain +50 gold.", "formula": "Self: -3 to 3 random stats, +50 gold", "type": "self_buff", "cost": 0, "cd": 0, "buff_type": "eldritchBargain", "buff_duration": 0, "tags": ["utility"], "tier": 2, "category": "utility", "stat_priority": ["luck"]},
            {"name": "Hastur's Whim", "icon": "w", "unlock_lv": 8, "desc": "Random powerful effect.", "formula": "Random: Heal/debuff/max dmg/LUK+5", "type": "mixed_magic", "power": 2.0, "stat": "wis", "random_effect": True, "cost": 10, "cd": 4, "tags": ["utility"], "tier": 2, "category": "utility", "stat_priority": ["wis", "luck"]},
            {"name": "Vision of the End", "icon": "V", "unlock_lv": 14, "desc": "All stats permanently +1.", "formula": "Self: all stats +1 permanently", "type": "self_buff", "cost": 0, "cd": 0, "buff_type": "permAll1", "buff_duration": 0, "tags": ["utility"], "tier": 3, "category": "utility", "stat_priority": ["wis"]},
            {"name": "Commune with Hastur", "icon": "]", "unlock_lv": 16, "desc": "Ask Hastur for aid. Random powerful effect.", "formula": "Random: Heal/Full debuff/Max damage/LUK+5", "type": "mixed_magic", "power": 3.0, "stat": "wis", "random_effect": True, "cost": 15, "cd": 6, "tags": ["offensive", "defensive", "support"], "tier": 3, "category": "utility", "stat_priority": ["wis", "luck"]},
            {"name": "Madness Mastery", "icon": "m", "unlock_lv": 18, "desc": "MAD no longer causes game over. +15 MAD.", "formula": "Passive: MAD cannot kill you, +15 MAD", "type": "self_buff", "cost": 0, "cd": 0, "buff_type": "madImmune", "buff_duration": 0, "tags": ["utility"], "tier": 3, "category": "utility", "stat_priority": ["wis"]},

            # ── AURAS/CURSES ──
            {"name": "Madness Touch", "icon": "~", "unlock_lv": 1, "desc": "Inflict your madness on the enemy.", "formula": "dmg = (5 + WISx1.0) x 0.8 + Shock 2t", "type": "magic_debuff", "power": 0.8, "stat": "wis", "effect": "shocked", "duration": 2, "cost": 5, "cd": 2, "tags": ["offensive", "debuff"], "tier": 1, "category": "auras_curses", "stat_priority": ["wis"]},
            {"name": "Dark Prophecy", "icon": "!", "unlock_lv": 2, "desc": "Curse the enemy with dark foresight.", "formula": "Enemy: -20% ATK, -15% DEF 3 turns", "type": "debuff", "effect": "weakened", "duration": 3, "power": 0, "stat": "wis", "cost": 8, "cd": 3, "tags": ["debuff"], "tier": 2, "category": "auras_curses", "stat_priority": ["wis"]},
            {"name": "Yellow Haze", "icon": "^", "unlock_lv": 4, "desc": "Envelop the area in madness-inducing fog.", "formula": "Enemy: Blind 3t + Poison 2t", "type": "debuff", "effect": "blinded", "effect2": "poisoned", "duration": 3, "power": 0, "stat": "wis", "cost": 12, "cd": 4, "tags": ["debuff"], "tier": 2, "category": "auras_curses", "stat_priority": ["wis"]},
            {"name": "Prophecy of Doom", "icon": "-", "unlock_lv": 8, "desc": "Doom falls in 3 turns. Massive delayed damage.", "formula": "Enemy takes WISx4 damage after 3 turns", "type": "debuff", "effect": "doom", "duration": 3, "power": 0, "stat": "wis", "cost": 15, "cd": 6, "tags": ["debuff"], "tier": 2, "category": "auras_curses", "stat_priority": ["wis"]},
            {"name": "Terrifying Visage", "icon": "&", "unlock_lv": 12, "desc": "Show your madness. Mass debuff.", "formula": "Enemy: Weaken+Blind+Shocked 2 turns", "type": "debuff", "effect": "weakened", "effect2": "blinded", "effect3": "shocked", "duration": 2, "power": 0, "stat": "wis", "cost": 20, "cd": 5, "tags": ["debuff"], "tier": 3, "category": "auras_curses", "stat_priority": ["wis"]},
            {"name": "Reality Glitch", "icon": ")", "unlock_lv": 14, "desc": "Bend reality. All debuffs +2 duration.", "formula": "Extend all enemy debuffs by 2, dmg WISx1.0", "type": "mixed_magic", "power": 1.0, "stat": "wis", "extend_debuffs": True, "cost": 18, "cd": 5, "tags": ["offensive", "debuff"], "tier": 3, "category": "auras_curses", "stat_priority": ["wis"]},
            {"name": "The Pallid Mask", "icon": "{", "unlock_lv": 18, "desc": "Become the Pallid Mask. 3 turns of power.", "formula": "Self: +50% all stats, immune to debuffs 3t", "type": "self_buff", "cost": 20, "cd": 8, "buff_type": "pallidMask", "buff_duration": 3, "tags": ["support", "ultimate"], "tier": 3, "category": "auras_curses", "stat_priority": ["wis"]},
            {"name": "The King's Gaze", "icon": "K", "unlock_lv": 16, "desc": "Enemy ATK-40%, DEF-30%, Blind 3t.", "formula": "Enemy: ATK-40%, DEF-30%, Blind 3 turns", "type": "debuff", "power": 0, "stat": "wis", "cost": 20, "cd": 6, "effect": "blinded", "duration": 3, "tags": ["debuff"], "tier": 3, "category": "auras_curses", "stat_priority": ["wis"]},
            {"name": "Mark of Hastur", "icon": "Y", "unlock_lv": 18, "desc": "All debuffs deal 50% more damage. 3t.", "formula": "Enemy: all debuffs +50% damage 3 turns", "type": "debuff", "power": 0, "stat": "wis", "cost": 18, "cd": 6, "effect": "hasturMark", "duration": 3, "tags": ["debuff"], "tier": 3, "category": "auras_curses", "stat_priority": ["wis"]},
            {"name": "Scream of Azathoth", "icon": "Z", "unlock_lv": 19, "desc": "Enemy hit with ALL debuffs 3t + damage.", "formula": "dmg + Burn+Shocked+Blind 3 turns", "type": "magic_debuff", "power": 2.0, "stat": "wis", "effect": "burning", "effect2": "shocked", "effect3": "blinded", "duration": 3, "cost": 28, "cd": 7, "tags": ["offensive", "debuff", "ultimate"], "tier": 3, "category": "auras_curses", "stat_priority": ["wis"]},

            # ── FILLER: Mad Prophet defensive/utility ──
            {"name": "Prophet's Resilience", "icon": "x", "unlock_lv": 4, "desc": "Regen 6% HP/turn 2t. +5 MAD.", "formula": "Self: regen 6% HP/turn 2t, +5 MAD", "type": "self_buff", "cost": 0, "cd": 4, "buff_type": "prophetRes", "buff_duration": 2, "tags": ["defensive"], "tier": 2, "category": "defensive", "stat_priority": ["wis"]},
            {"name": "Madman's Endurance", "icon": "E", "unlock_lv": 14, "desc": "Shield=WISx2, regen 5% 2t. +8 MAD.", "formula": "shield=WISx2, regen 5%/turn 2t, +8 MAD", "type": "self_shield", "cost": 0, "cd": 5, "shield_calc": "madEndur", "tags": ["defensive"], "tier": 3, "category": "defensive", "stat_priority": ["wis"]},
            {"name": "Unreliable Fortune", "icon": "u", "unlock_lv": 2, "desc": "+10% loot quality 5 floors.", "formula": "Passive: +10% loot quality 5 floors", "type": "self_buff", "cost": 0, "cd": 0, "buff_type": "unrelFort", "buff_duration": 99, "tags": ["utility"], "tier": 1, "category": "utility", "stat_priority": ["luck"]},
        ],
    },
}


# ═══════════════════════════════════════════
# ENEMIES
# ═══════════════════════════════════════════

ENEMIES = [
    {
        "name": "The All-Seeing Mass",
        "type": "Eldritch Horror",
        "desc": "A writhing sphere of eyes and tentacles. It sees everything.",
        "hp_mult": 1.2, "atk_mult": 1.0, "def_mult": 0.9,
        "skills": [
            {"name": "Tentacle Lash", "type": "physical", "power": 1.3},
            {"name": "Gaze of Madness", "type": "magic_debuff", "power": 1.0, "effect": "blinded", "duration": 2},
            {"name": "Regenerate", "type": "self_heal", "power": 0.06},
        ],
        "level_range": [1, 6],
    },
    {
        "name": "The Skull Bearer",
        "type": "Undead Horror",
        "desc": "A towering figure draped in bone. Each skull whispers a name.",
        "hp_mult": 1.0, "atk_mult": 1.3, "def_mult": 1.0,
        "skills": [
            {"name": "Bone Crush", "type": "physical", "power": 1.5},
            {"name": "Skull Storm", "type": "physical_debuff", "power": 1.2, "effect": "shocked", "duration": 2},
            {"name": "Life Drain", "type": "magic", "power": 1.0, "lifesteal": 0.3},
        ],
        "level_range": [3, 10],
    },
    {
        "name": "Storm Spawn",
        "type": "Elemental Aberration",
        "desc": "Lightning given form and malice. The air crackles around it.",
        "hp_mult": 0.8, "atk_mult": 1.4, "def_mult": 0.7,
        "skills": [
            {"name": "Lightning Bolt", "type": "magic", "power": 1.6},
            {"name": "Static Charge", "type": "magic_debuff", "power": 1.0, "effect": "shocked", "duration": 2},
            {"name": "Thunder Roar", "type": "physical_debuff", "power": 1.1, "effect": "weakened", "duration": 2},
        ],
        "level_range": [5, 12],
    },
    {
        "name": "Carcosan Seer",
        "type": "Humanoid Cultist",
        "desc": "A robed figure whose eyes burn with yellow fire. They know what you're thinking.",
        "hp_mult": 0.7, "atk_mult": 1.5, "def_mult": 0.8,
        "skills": [
            {"name": "Eldritch Bolt", "type": "magic", "power": 1.8},
            {"name": "Mind Rend", "type": "magic_debuff", "power": 1.2, "effect": "petrified", "duration": 2},
            {"name": "Dark Barrier", "type": "self_heal", "power": 0.08},
        ],
        "level_range": [7, 15],
    },
    {
        "name": "Ember Horror",
        "type": "Fire Elemental",
        "desc": "A being of living flame that screams as it burns. The smell of charred flesh lingers.",
        "hp_mult": 0.9, "atk_mult": 1.5, "def_mult": 0.8,
        "skills": [
            {"name": "Flame Strike", "type": "magic", "power": 1.7},
            {"name": "Inferno", "type": "magic_debuff", "power": 1.3, "effect": "burning", "duration": 3},
            {"name": "Cauterize", "type": "self_heal", "power": 0.07},
        ],
        "level_range": [10, 18],
    },
]

BOSS = {
    "name": "Hastur, The Spiral Beyond",
    "type": "???",
    "desc": "The Tattered King rises. Reality unravels at his presence.",
    "hp_mult": 4.0, "atk_mult": 1.6, "def_mult": 1.4,
    "skills": [
        {"name": "Yellow Sign", "type": "magic_debuff", "power": 1.5, "effect": "petrified", "duration": 3},
        {"name": "Carcosa's Embrace", "type": "magic", "power": 2.2},
        {"name": "The King's Madness", "type": "magic_debuff", "power": 1.3, "effect": "shocked", "duration": 2},
        {"name": "Tattered Reality", "type": "magic", "power": 2.8},
        {"name": "Restoration", "type": "self_heal", "power": 0.08},
        {"name": "Pallid Mask", "type": "magic_debuff", "power": 1.0, "effect": "blinded", "duration": 3},
    ],
    "level_range": [20, 20],
}


# ═══════════════════════════════════════════
# ITEM SYSTEM
# ═══════════════════════════════════════════

RARITY_DATA = {
    1: {"name": "Common", "color": "white", "stat_range": (1, 2), "stat_mul": 0.7},
    2: {"name": "Uncommon", "color": "green", "stat_range": (2, 3), "stat_mul": 1.0},
    3: {"name": "Rare", "color": "cyan", "stat_range": (3, 3), "stat_mul": 1.35},
    4: {"name": "Cursed", "color": "red", "stat_range": (2, 4), "stat_mul": 1.6},
}

CURSED_DEBUFFS = [
    {"stat": "str", "name": "Frailty"},
    {"stat": "int", "name": "Idiocy"},
    {"stat": "agi", "name": "Lethargy"},
    {"stat": "wis", "name": "Doubt"},
    {"stat": "luck", "name": "Misfortune"},
]

ITEM_PREFIXES = {
    1: ["Rusted", "Cracked", "Worn", "Faded", "Old"],
    2: ["Tainted", "Eldritch", "Whispering", "Forgotten", "Glowing"],
    3: ["Enchanted", "Void-touched", "Carcosan", "Arcane", "Mythic"],
    4: ["Cursed", "Bloodied", "Hollow", "Blighted", "Damned"],
}

WEAPON_TEMPLATES = [
    {"name": "Blade", "slot": "weapon", "base": {"atk": 5}, "bonus_pool": ["int", "str", "agi", "luck"]},
    {"name": "Tome", "slot": "weapon", "base": {"atk": 3, "int": 3}, "bonus_pool": ["int", "wis"]},
    {"name": "Cudgel", "slot": "weapon", "base": {"atk": 6, "str": 1}, "bonus_pool": ["str", "wis"]},
    {"name": "Dagger", "slot": "weapon", "base": {"atk": 4, "agi": 2}, "bonus_pool": ["agi", "luck"]},
    {"name": "Staff", "slot": "weapon", "base": {"atk": 3, "wis": 3}, "bonus_pool": ["wis", "int"]},
]

ARMOR_TEMPLATES = [
    {"name": "Robes", "slot": "armor", "base": {"def": 3, "int": 2}, "bonus_pool": ["int", "wis"]},
    {"name": "Chainmail", "slot": "armor", "base": {"def": 6, "str": 1}, "bonus_pool": ["str", "luck"]},
    {"name": "Leather", "slot": "armor", "base": {"def": 4, "agi": 2}, "bonus_pool": ["agi"]},
    {"name": "Mantle", "slot": "armor", "base": {"def": 4, "wis": 2}, "bonus_pool": ["wis", "int"]},
]

ACCESSORY_TEMPLATES = [
    {"name": "Brooch", "slot": "accessory", "base": {"def": 2, "int": 1}, "bonus_pool": ["int", "wis", "luck"]},
    {"name": "Cloak", "slot": "accessory", "base": {"def": 3, "agi": 1}, "bonus_pool": ["agi", "wis"]},
    {"name": "Sash", "slot": "accessory", "base": {"hp": 8, "str": 1}, "bonus_pool": ["str", "luck", "hp"]},
    {"name": "Talisman", "slot": "accessory", "base": {"wis": 2, "int": 1}, "bonus_pool": ["wis", "int", "luck"]},
]

BOOTS_TEMPLATES = [
    {"name": "Sandals", "slot": "boots", "base": {"agi": 3, "def": 1}, "bonus_pool": ["agi", "luck", "hp"]},
    {"name": "Greaves", "slot": "boots", "base": {"def": 3, "str": 1}, "bonus_pool": ["str", "agi"]},
    {"name": "Boots", "slot": "boots", "base": {"agi": 2, "def": 2}, "bonus_pool": ["agi", "wis"]},
    {"name": "Treads", "slot": "boots", "base": {"def": 2, "hp": 6}, "bonus_pool": ["str", "luck", "hp"]},
]

RING_TEMPLATES = [
    {"name": "Band", "slot": "ring", "base": {}, "bonus_pool": ["int", "str", "agi", "wis", "luck"]},
    {"name": "Seal", "slot": "ring", "base": {"def": 1}, "bonus_pool": ["wis", "int", "luck"]},
    {"name": "Signet", "slot": "ring", "base": {"atk": 2}, "bonus_pool": ["str", "agi", "luck"]},
    {"name": "Loop", "slot": "ring", "base": {"hp": 5}, "bonus_pool": ["luck", "wis", "hp"]},
]


# ═══════════════════════════════════════════
# FLOOR EVENTS
# ═══════════════════════════════════════════

EVENTS = [
    {
        "title": "Whispers in the Dark",
        "icon": "?",
        "text": "A voice speaks from nowhere. It offers forbidden knowledge for sanity.",
        "outcomes": [
            {"text": "Accept (INT+2, +10 Madness)", "effect": "gain_int_2_mad_10"},
            {"text": "Refuse", "effect": "nothing"},
            {"text": "Reason (50%: WIS+2 or +15 MAD)", "effect": "reason_50"},
        ],
    },
    {
        "title": "The Yellow Sign",
        "icon": "!",
        "text": "The Yellow Sign carved into the wall. Looking too long makes thoughts slippery.",
        "outcomes": [
            {"text": "Study (STR+2, +8 Madness)", "effect": "gain_str_2_mad_8"},
            {"text": "Avert eyes (-5 Madness)", "effect": "mad_minus_5"},
            {"text": "Deface (50%: Heal 20% or +12 MAD)", "effect": "deface_50"},
        ],
    },
    {
        "title": "Abandoned Laboratory",
        "icon": "#",
        "text": "Shattered beakers and strange chemicals. Some might still be useful... or poisonous.",
        "outcomes": [
            {"text": "Drink (60%: Heal 30% or take 20%)", "effect": "drink_60"},
            {"text": "Search (+15 gold)", "effect": "gold_15"},
            {"text": "Leave it", "effect": "nothing"},
        ],
    },
    {
        "title": "The Survivor",
        "icon": "+",
        "text": 'Another patient, barely alive. They mumble about "the way out."',
        "outcomes": [
            {"text": "Help (+10 MAD, receive item)", "effect": "help_survivor"},
            {"text": "Take from them (+20 gold, +5 MAD)", "effect": "rob_survivor"},
            {"text": "Walk away", "effect": "nothing"},
        ],
    },
    {
        "title": "Shrine to Hastur",
        "icon": "-",
        "text": "A crude altar of yellow cloth and bone. The air hums with power.",
        "outcomes": [
            {"text": "Pray (Full heal, +15 MAD)", "effect": "pray_full_heal"},
            {"text": "Desecrate (AGI+3, +10 MAD)", "effect": "desecrate"},
            {"text": "Offer 20g (WIS+3)", "effect": "offer_gold"},
        ],
    },
    {
        "title": "Rats... or Are They?",
        "icon": "=",
        "text": "A swarm of rats watches with intelligent eyes. One speaks your name.",
        "outcomes": [
            {"text": "Listen (Random stat+1, +3 MAD)", "effect": "listen_rats"},
            {"text": "Flee (+5 MAD)", "effect": "mad_5"},
            {"text": "Attack (-10% HP, STR+1)", "effect": "attack_rats"},
        ],
    },
]

TRAPS = [
    {
        "name": "Collapsing Floor",
        "desc": "The floor gives way!",
        "outcomes": [
            {"chance": 0.5, "text": "Catch yourself! 10% damage.", "dmg_pct": 0.1, "madness": 0},
            {"chance": 1.0, "text": "Fall! 25% damage.", "dmg_pct": 0.25, "madness": 5},
        ],
    },
    {
        "name": "Yellow Mist",
        "desc": "Thick yellow fog whispers things.",
        "outcomes": [
            {"chance": 0.4, "text": "Hold breath. Safe.", "dmg_pct": 0, "madness": 0},
            {"chance": 1.0, "text": "Mist seeps in. +12 MAD.", "dmg_pct": 0, "madness": 12},
        ],
    },
    {
        "name": "Trap of Madness",
        "desc": "Walls covered in maddening symbols.",
        "outcomes": [
            {"chance": 0.3, "text": "Steel your mind. Resist.", "dmg_pct": 0, "madness": 0},
            {"chance": 1.0, "text": "Symbols burn in. +18 MAD.", "dmg_pct": 0, "madness": 18},
        ],
    },
]


# ═══════════════════════════════════════════
# FLOOR NARRATIVES
# ═══════════════════════════════════════════

FLOOR_NARRATIVES = [
    "The ground floor of the asylum. Flickering lights cast long shadows. Something scratched 'PH'NGLUI on the wall.",
    "The wards. Patients' cells stand open, empty. Wet footprints lead deeper inside.",
    "The infirmary. Medicine cabinets shattered. A yellow glow pulses from the operating theater.",
    "The basement. Pipes groan and hiss. The air tastes of copper and old prayers.",
    "Sub-level one. The architecture doesn't make sense anymore. Corridors bend wrong.",
    "The catacombs beneath. Ancient stonework meets modern concrete. Both are cracking.",
    "Deeper still. The walls are damp with something that isn't water. It smells of the sea.",
    "A vast chamber. Pillars of impossible height support a ceiling you cannot see.",
    "The walls here are carved with symbols that make your eyes hurt to look at.",
    "The Ritual Hall. Yellow banners hang from impossible heights. Candles burn without flame.",
    "The air vibrates. You can hear chanting in a language that predates humanity.",
    "The Threshold. Reality thins here. You can see through walls to places that shouldn't exist.",
    "Something is following you. You can hear it breathing when you stop moving.",
    "The corridors twist and fold. You've been walking in circles — or have you?",
    "Carcosa's influence grows. The yellow tint in everything is unmistakable now.",
    "The walls bleed light. Shadows move independently. The end is near.",
    "You can feel the King's presence. The air crackles with ancient power.",
    "The final corridors. Every step echoes with the weight of millennia.",
    "Carcosa's Gate. The walls are no longer walls. They breathe. They watch.",
    "The throne room of the King in Yellow. There is no escape but through.",
]


# ═══════════════════════════════════════════
# PATH TYPES FOR EXPLORATION
# ═══════════════════════════════════════════

PATH_TEMPLATES = [
    {"type": "combat", "icon": "!", "name": "Dark Passage", "desc": "Something stirs in the shadows",
     "desc2": "A creature lurks ahead. Steel yourself — blood will be spilled.", "hint": "Enemy", "weight": 3},
    {"type": "combat", "icon": "+", "name": "Blood Trail", "desc": "A trail of blood leads into the dark",
     "desc2": "Fresh crimson stains mark the floor. Something wounded — or something feeding.", "hint": "Enemy", "weight": 3},
    {"type": "combat", "icon": "~", "name": "Lurking Horror", "desc": "Eyes watch from the darkness",
     "desc2": "Dozens of unblinking eyes pierce the gloom. The beast is patient. You are not safe.", "hint": "Enemy", "weight": 2},
    {"type": "event", "icon": "?", "name": "Strange Sound", "desc": "An unearthly melody echoes",
     "desc2": "A haunting tune drifts through the corridors. Approach, and face the unknown.", "hint": "Unknown", "weight": 1},
    {"type": "event", "icon": "#", "name": "Forbidden Text", "desc": "A tome lies open, pages turning",
     "desc2": "Knowledge or madness — the pages whisper secrets no mortal should hear.", "hint": "Knowledge or madness", "weight": 1},
    {"type": "loot", "icon": "=", "name": "Supply Room", "desc": "An untouched closet, door ajar",
     "desc2": "Someone abandoned their belongings here. Take what you can — you will need it.", "hint": "Equipment", "weight": 1},
    {"type": "loot", "icon": "$", "name": "Offering", "desc": "Something glitters on a stone altar",
     "desc2": "An offering to forgotten gods. The treasure is yours — if you dare claim it.", "hint": "Equipment", "weight": 1},
    {"type": "rest", "icon": "-", "name": "Safe Haven", "desc": "A moment of calm in the storm",
     "desc2": "A rare sanctuary. Tend your wounds, clear your mind, or prepare your body.", "hint": "Healing", "weight": 1},
    {"type": "shop", "icon": "@", "name": "Mad Trader", "desc": "A figure deals in strange wares",
     "desc2": "Eyes wild, smile crooked. Their goods are real — the price, however, is never simple.", "hint": "Items", "weight": 1},
    {"type": "trap", "icon": "^", "name": "Suspicious Hallway", "desc": "Uneven floor, thick dread",
     "desc2": "The stones shift beneath your feet. Every step could be your last. Tread carefully.", "hint": "Danger", "weight": 1},
]

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
# CLASSES & SKILLS (5 classes, 20 skills each)
# ═══════════════════════════════════════════

CLASSES = {
    "scholar": {
        "name": "Scholar of the Forbidden",
        "icon": "S",
        "desc": "Wielder of eldritch knowledge. Devastating magical bursts and crippling status effects. Fragile but deadly.",
        "base_stats": {"int": 14, "str": 6, "agi": 8, "wis": 10, "luck": 5},
        "hp_base": 70, "hp_per_level": 6,
        "skills": [
            {"name": "Eldritch Blast", "icon": "*", "unlock_lv": 1, "desc": "Hurl a bolt of pure eldritch energy.", "formula": "dmg = (5 + INTx1.5) x 1.8", "type": "magic", "power": 1.8, "stat": "int", "cost": 0, "cd": 0, "tags": ["offensive"]},
            {"name": "Arcane Missile", "icon": "~", "unlock_lv": 1, "desc": "Fast homing missiles of condensed thought.", "formula": "dmg = (5 + INTx1.5) x 1.2, cannot miss", "type": "magic", "power": 1.2, "stat": "int", "cost": 5, "cd": 0, "true_strike": True, "tags": ["offensive"]},
            {"name": "Mind Spike", "icon": "!", "unlock_lv": 2, "desc": "Psychic jab that saps the enemy's will.", "formula": "dmg = (5 + INTx1.5) x 1.0, weaken 2 turns", "type": "magic_debuff", "power": 1.0, "stat": "int", "effect": "weakened", "duration": 2, "cost": 8, "cd": 2, "tags": ["offensive", "debuff"]},
            {"name": "Psychic Shield", "icon": "#", "unlock_lv": 2, "desc": "Erect a barrier of crystallized thought.", "formula": "shield = INTx2 + WISx1, absorbs damage", "type": "self_shield", "cost": 8, "cd": 3, "shield_calc": "int2_wis1", "tags": ["defensive"]},
            {"name": "Burning Sigil", "icon": "^", "unlock_lv": 4, "desc": "Brands the enemy with a searing sigil.", "formula": "dmg = (5 + INTx1.5) x 0.8 + Burn 6% HP/turn 3 turns", "type": "debuff", "effect": "burning", "duration": 3, "power": 0.8, "stat": "int", "cost": 10, "cd": 3, "tags": ["offensive", "debuff"]},
            {"name": "Flash Freeze", "icon": "v", "unlock_lv": 4, "desc": "Snap-freeze the air around the foe.", "formula": "dmg = (5 + INTx1.5) x 1.3 + Freeze 2 turns", "type": "magic_debuff", "power": 1.3, "stat": "int", "effect": "freezing", "duration": 2, "cost": 12, "cd": 3, "tags": ["offensive", "debuff"]},
            {"name": "Void Bolt", "icon": "@", "unlock_lv": 6, "desc": "A bolt from between dimensions.", "formula": "dmg = (5 + INTx1.5 + WISx0.5) x 2.0", "type": "mixed_magic", "power": 2.0, "stat": "int", "stat2": "wis", "stat2_mult": 0.5, "cost": 15, "cd": 3, "tags": ["offensive", "dual-stat"]},
            {"name": "Eldritch Sight", "icon": "O", "unlock_lv": 6, "desc": "See the enemy's weakness. +30% crit 3 turns.", "formula": "Self: CRIT +30% for 3 turns", "type": "self_buff", "cost": 8, "cd": 5, "buff_type": "critUp", "buff_duration": 3, "tags": ["support"]},
            {"name": "Corrosive Hex", "icon": "%", "unlock_lv": 8, "desc": "Poison that eats at body and mind.", "formula": "dmg = (5 + INTx1.5) x 0.6 + Poison stacking to 5", "type": "magic_debuff", "power": 0.6, "stat": "int", "effect": "poisoned", "duration": 3, "cost": 12, "cd": 3, "tags": ["offensive", "debuff"]},
            {"name": "Mind Shatter", "icon": "X", "unlock_lv": 8, "desc": "Shatter the enemy's psyche.", "formula": "dmg = (5 + INTx1.5) x 2.8 + Petrify 2 turns", "type": "magic_debuff", "power": 2.8, "stat": "int", "effect": "petrified", "duration": 2, "cost": 22, "cd": 5, "tags": ["offensive", "debuff"]},
            {"name": "Reality Warp", "icon": "?", "unlock_lv": 10, "desc": "Warp spacetime around the target.", "formula": "dmg = (5 + INTx1.5 + WISx0.8) x 2.0 + Blind 2t", "type": "mixed_magic", "power": 2.0, "stat": "int", "stat2": "wis", "stat2_mult": 0.8, "effect": "blinded", "duration": 2, "cost": 20, "cd": 5, "tags": ["offensive", "dual-stat"]},
            {"name": "Forbidden Knowledge", "icon": "+", "unlock_lv": 10, "desc": "Channel cosmic truth. Heal and boost INT.", "formula": "Heal INTx2 HP, INT +3 for 5 turns", "type": "self_heal", "cost": 12, "cd": 6, "heal_calc": "int2_buff", "tags": ["support", "defensive"]},
            {"name": "Entropy Wave", "icon": "-", "unlock_lv": 12, "desc": "Wave of entropic energy that corrodes all.", "formula": "dmg = (5 + INTx1.8) x 2.2, ignores 40% mDEF", "type": "magic", "power": 2.2, "stat": "int", "armor_pierce": 0.4, "cost": 18, "cd": 4, "tags": ["offensive"]},
            {"name": "Void Rift", "icon": "=", "unlock_lv": 12, "desc": "Open a tear in reality itself.", "formula": "dmg = (5 + INTx2.0 + WISx1.0) x 2.5", "type": "mixed_magic", "power": 2.5, "stat": "int", "stat2": "wis", "stat2_mult": 1.0, "cost": 22, "cd": 5, "tags": ["offensive", "dual-stat"]},
            {"name": "Eldritch Ward", "icon": ";", "unlock_lv": 14, "desc": "Protective aura that grows stronger with each hit taken.", "formula": "shield = WISx3 + hits_taken x 5, stacks", "type": "self_shield", "cost": 15, "cd": 5, "shield_calc": "wis3_hits", "tags": ["defensive"]},
            {"name": "Dominate Mind", "icon": "|", "unlock_lv": 14, "desc": "Seize control. Enemy skips turn + takes damage.", "formula": "Enemy stunned 1 turn + dmg = INTx1.5", "type": "magic_debuff", "power": 1.5, "stat": "int", "effect": "shocked", "duration": 1, "cost": 18, "cd": 5, "tags": ["offensive", "debuff"]},
            {"name": "Nether Storm", "icon": "$", "unlock_lv": 16, "desc": "Storm of dark energy. Hits hard and blinds.", "formula": "dmg = (5 + INTx2.0) x 2.6 + Blind 3 turns", "type": "magic_debuff", "power": 2.6, "stat": "int", "effect": "blinded", "duration": 3, "cost": 25, "cd": 6, "tags": ["offensive", "debuff"]},
            {"name": "Astral Projection", "icon": "&", "unlock_lv": 16, "desc": "Phase out of reality. EVA +40%, mDEF +60% 3t.", "formula": "Self: EVA+40%, mDEF+60% for 3 turns", "type": "self_buff", "cost": 12, "cd": 6, "buff_type": "astral", "buff_duration": 3, "tags": ["defensive", "support"]},
            {"name": "Warp Time", "icon": "(", "unlock_lv": 18, "desc": "Bend time. Reset all cooldowns.", "formula": "All skill CDs reset. Gain +20% damage 2 turns.", "type": "self_buff", "cost": 20, "cd": 8, "buff_type": "warpTime", "buff_duration": 2, "tags": ["support"]},
            {"name": "The Yellow Sign", "icon": "Y", "unlock_lv": 19, "desc": "Invoke the Unspeakable. Massive damage + all debuffs.", "formula": "dmg = (5 + INTx1.5 + WISx1.0) x 3.0 + Burn+Petrify", "type": "mixed_magic", "power": 3.0, "stat": "int", "stat2": "wis", "stat2_mult": 1.0, "effect": "burning", "effect2": "petrified", "duration": 3, "cost": 30, "cd": 7, "tags": ["offensive", "ultimate"]},
        ],
    },
    "brute": {
        "name": "Brute of the Depths",
        "icon": "B",
        "desc": "Unstoppable force of raw power. High health, devastating physical attacks that grow stronger as you weaken.",
        "base_stats": {"int": 6, "str": 14, "agi": 8, "wis": 8, "luck": 5},
        "hp_base": 110, "hp_per_level": 10,
        "skills": [
            {"name": "Crushing Blow", "icon": "*", "unlock_lv": 1, "desc": "A devastating overhead strike.", "formula": "dmg = ATKx1.6 + STRx0.8 physical", "type": "physical", "power": 1.6, "stat": "str", "cost": 0, "cd": 0, "tags": ["offensive"]},
            {"name": "Quick Slash", "icon": "~", "unlock_lv": 1, "desc": "A fast, agile cut.", "formula": "dmg = ATKx1.2 + AGIx0.6, fast recovery", "type": "physical", "power": 1.2, "stat": "agi", "cost": 0, "cd": 0, "tags": ["offensive"]},
            {"name": "Intimidate", "icon": "!", "unlock_lv": 2, "desc": "Your roar shakes the enemy.", "formula": "No dmg. -20% enemy ATK 3 turns", "type": "debuff", "effect": "weakened", "duration": 3, "power": 0, "stat": "str", "cost": 5, "cd": 3, "tags": ["debuff"]},
            {"name": "Piercing Strike", "icon": "#", "unlock_lv": 2, "desc": "Strike that ignores half defense.", "formula": "dmg = ATKx1.4 + STRx0.6, ignores 50% pDEF", "type": "physical", "power": 1.4, "stat": "str", "armor_pierce": 0.5, "cost": 8, "cd": 2, "tags": ["offensive"]},
            {"name": "Berserker Rage", "icon": "^", "unlock_lv": 4, "desc": "Embrace fury. +60% damage, lose 12% HP.", "formula": "Self: +60% DMG 1 turn, costs 12% max HP", "type": "self_buff", "cost": 5, "cd": 3, "buff_type": "rage", "buff_duration": 1, "tags": ["support"]},
            {"name": "Ground Pound", "icon": "v", "unlock_lv": 4, "desc": "Slam the earth. Physical AoE pressure.", "formula": "dmg = ATKx1.3 + STRx0.9, Shock 2 turns", "type": "physical_debuff", "power": 1.3, "stat": "str", "effect": "shocked", "duration": 2, "cost": 10, "cd": 3, "tags": ["offensive", "debuff"]},
            {"name": "Last Stand", "icon": "@", "unlock_lv": 6, "desc": "Lower HP = harder you hit.", "formula": "dmg = ATKx1.0 + STRx1.0, x(1+(1-HP%)x2.0)", "type": "physical", "power": 1.0, "stat": "str", "scaling_low_hp": True, "cost": 10, "cd": 3, "tags": ["offensive"]},
            {"name": "Vampiric Strike", "icon": "+", "unlock_lv": 6, "desc": "Steal life from the enemy.", "formula": "dmg = ATKx1.5 + STRx0.5, heal 40% dealt", "type": "physical", "power": 1.5, "stat": "str", "lifesteal": 0.4, "cost": 12, "cd": 4, "tags": ["offensive", "defensive"]},
            {"name": "Thunderclap", "icon": "-", "unlock_lv": 8, "desc": "Earth-shaking force with lightning.", "formula": "dmg = (ATKx1.2 + STRx0.8 + AGIx0.4), Shock 2t", "type": "mixed_phys", "power": 1.2, "stat": "str", "stat2": "agi", "stat2_mult": 0.4, "effect": "shocked", "duration": 2, "cost": 15, "cd": 4, "tags": ["offensive", "dual-stat"]},
            {"name": "War Cry", "icon": "=", "unlock_lv": 8, "desc": "Rally yourself. +40% ATK, +20% crit 4 turns.", "formula": "Self: ATK+40%, CRIT+20% for 4 turns", "type": "self_buff", "cost": 10, "cd": 5, "buff_type": "atkCritUp", "buff_duration": 4, "tags": ["support"]},
            {"name": "Iron Skin", "icon": ";", "unlock_lv": 10, "desc": "Harden your body against all harm.", "formula": "Self: pDEF+60%, mDEF+30% for 4 turns", "type": "self_buff", "cost": 10, "cd": 5, "buff_type": "ironSkin", "buff_duration": 4, "tags": ["defensive"]},
            {"name": "Adrenaline Surge", "icon": "|", "unlock_lv": 10, "desc": "Heal based on missing HP. Huge recovery.", "formula": "Heal = (1 - HP%) x maxHP x 0.6", "type": "self_heal", "cost": 8, "cd": 5, "heal_calc": "missing_hp", "tags": ["defensive"]},
            {"name": "Rampage", "icon": "$", "unlock_lv": 12, "desc": "Unleash three wild strikes.", "formula": "dmg = ATKx0.9 x 3 hits + STRx0.5 each", "type": "physical", "power": 0.9, "stat": "str", "multihit": 3, "cost": 15, "cd": 4, "tags": ["offensive"]},
            {"name": "Colossus Smash", "icon": "&", "unlock_lv": 12, "desc": "A blow that cracks defenses open.", "formula": "dmg = ATKx2.2 + STRx1.0, enemy pDEF-30% 3t", "type": "physical_debuff", "power": 2.2, "stat": "str", "effect": "weakened", "duration": 3, "cost": 18, "cd": 5, "tags": ["offensive", "debuff"]},
            {"name": "Titan Slam", "icon": "(", "unlock_lv": 14, "desc": "The earth splits beneath your blow.", "formula": "dmg = ATKx2.8 + STRx1.2, Shock 2t (50% stun)", "type": "physical_debuff", "power": 2.8, "stat": "str", "effect": "shocked", "duration": 2, "cost": 20, "cd": 5, "tags": ["offensive", "debuff"]},
            {"name": "Blood Price", "icon": ")", "unlock_lv": 14, "desc": "Sacrifice HP for devastating power.", "formula": "dmg = ATKx3.0 + STRx1.5, costs 25% max HP", "type": "physical", "power": 3.0, "stat": "str", "hp_cost": 0.25, "cost": 5, "cd": 5, "tags": ["offensive"]},
            {"name": "Undying Fury", "icon": "[", "unlock_lv": 16, "desc": "Cannot die this turn. If <30% HP, full rage.", "formula": "Self: cannot die 1 turn. HP<30%: +100% DMG", "type": "self_buff", "cost": 15, "cd": 7, "buff_type": "undying", "buff_duration": 1, "tags": ["defensive", "support"]},
            {"name": "Seismic Wave", "icon": "]", "unlock_lv": 16, "desc": "Channel fury through the ground.", "formula": "dmg = (ATKx1.5 + STRx1.2 + AGIx0.6) x 2.0", "type": "mixed_phys", "power": 2.0, "stat": "str", "stat2": "agi", "stat2_mult": 0.6, "cost": 22, "cd": 5, "tags": ["offensive", "dual-stat"]},
            {"name": "Warlord's Command", "icon": "{", "unlock_lv": 18, "desc": "All buffs active: rage, war cry, iron skin.", "formula": "Apply rage + atkCritUp + ironSkin, costs 20% HP", "type": "self_buff", "cost": 15, "cd": 8, "buff_type": "warlord", "buff_duration": 3, "tags": ["support", "ultimate"]},
            {"name": "Apocalypse Strike", "icon": "}", "unlock_lv": 19, "desc": "Channel all rage into one cataclysmic blow.", "formula": "dmg = (ATKx1.5 + STRx1.5 + AGIx0.8) x 3.5", "type": "mixed_phys", "power": 3.5, "stat": "str", "stat2": "agi", "stat2_mult": 0.8, "armor_pierce": 0.3, "cost": 30, "cd": 7, "tags": ["offensive", "ultimate"]},
        ],
    },
    "warden": {
        "name": "Warden of Thresholds",
        "icon": "W",
        "desc": "Master of shields and barriers. Absorb punishment, curse foes, and turn defense into devastating offense.",
        "base_stats": {"int": 8, "str": 6, "agi": 8, "wis": 14, "luck": 5},
        "hp_base": 90, "hp_per_level": 8,
        "skills": [
            {"name": "Warding Light", "icon": "*", "unlock_lv": 1, "desc": "Shimmer of protective light. Blocks 1 hit.", "formula": "Gain 1 barrier stack (max 3). Absorbs any hit.", "type": "self_buff", "cost": 0, "cd": 0, "buff_type": "barrier", "barrier_stacks": 1, "tags": ["defensive"]},
            {"name": "Holy Strike", "icon": "~", "unlock_lv": 1, "desc": "Channel divine wrath into a smite.", "formula": "dmg = (5 + WISx1.3) x 1.4 eldritch", "type": "magic", "power": 1.4, "stat": "wis", "cost": 0, "cd": 0, "tags": ["offensive"]},
            {"name": "Purifying Touch", "icon": "!", "unlock_lv": 2, "desc": "Cleanse wounds with sacred power.", "formula": "Heal = WISx2 + 10 HP", "type": "self_heal", "cost": 5, "cd": 2, "heal_calc": "wis2_10", "tags": ["defensive"]},
            {"name": "Shield Bash", "icon": "#", "unlock_lv": 2, "desc": "Strike with your shield. Scales with DEF.", "formula": "dmg = DEFx2.0 + WISx0.5, physical", "type": "physical", "power": 2.0, "stat": "wis", "def_scaling": True, "cost": 5, "cd": 2, "tags": ["offensive", "dual-stat"]},
            {"name": "Aegis Shield", "icon": "^", "unlock_lv": 4, "desc": "Summon a massive protective barrier.", "formula": "shield = WISx3 + INTx1.5, until broken", "type": "self_shield", "cost": 10, "cd": 4, "shield_calc": "wis3_int1", "tags": ["defensive"]},
            {"name": "Consecrated Ground", "icon": "v", "unlock_lv": 4, "desc": "Heal over time while standing firm.", "formula": "Heal 8% maxHP/turn for 3 turns", "type": "self_buff", "cost": 10, "cd": 5, "buff_type": "regen", "buff_duration": 3, "tags": ["defensive", "support"]},
            {"name": "Divine Smite", "icon": "@", "unlock_lv": 6, "desc": "Holy fire that burns undead and eldritch.", "formula": "dmg = (5 + WISx1.5 + INTx0.5) x 2.0", "type": "mixed_magic", "power": 2.0, "stat": "wis", "stat2": "int", "stat2_mult": 0.5, "cost": 15, "cd": 3, "tags": ["offensive", "dual-stat"]},
            {"name": "Arcane Ward", "icon": "+", "unlock_lv": 6, "desc": "Increase magic defense significantly.", "formula": "Self: mDEF+50% for 4 turns", "type": "self_buff", "cost": 8, "cd": 5, "buff_type": "mDefUp", "buff_duration": 4, "tags": ["defensive"]},
            {"name": "Sacrificial Curse", "icon": "-", "unlock_lv": 8, "desc": "Convert shield into devastating damage.", "formula": "dmg = (5 + WISx1.5) x 1.5 + consumed shield", "type": "curse", "power": 1.5, "stat": "wis", "cost": 0, "cd": 4, "consume_shield": True, "tags": ["offensive"]},
            {"name": "Retribution", "icon": "=", "unlock_lv": 8, "desc": "Damage scales with current shield.", "formula": "dmg = (5 + WISx1.2) x 1.0 + shieldx0.5", "type": "mixed_magic", "power": 1.0, "stat": "wis", "shield_scaling": 0.5, "cost": 12, "cd": 4, "tags": ["offensive", "dual-stat"]},
            {"name": "Bulwark", "icon": ";", "unlock_lv": 10, "desc": "Become immovable. Massive defense boost.", "formula": "Self: pDEF+60%, mDEF+60% for 4 turns", "type": "self_buff", "cost": 12, "cd": 5, "buff_type": "bulwark", "buff_duration": 4, "tags": ["defensive"]},
            {"name": "Healing Light", "icon": "|", "unlock_lv": 10, "desc": "Burst of healing energy.", "formula": "Heal = WISx3 + INTx1.5 HP", "type": "self_heal", "cost": 12, "cd": 4, "heal_calc": "wis3_int1_heal", "tags": ["defensive"]},
            {"name": "Divine Fortress", "icon": "$", "unlock_lv": 12, "desc": "Ultimate defense. +80% DEF, barriers.", "formula": "Self: pDEF/mDEF+80%, +2 barrier 3 turns", "type": "self_buff", "cost": 15, "cd": 6, "buff_type": "fortress", "buff_duration": 3, "tags": ["defensive", "ultimate"]},
            {"name": "Banishment", "icon": "&", "unlock_lv": 12, "desc": "Smite with the power of the threshold.", "formula": "dmg = (5 + WISx2.0) x 2.8 + Shock 2 turns", "type": "magic_debuff", "power": 2.8, "stat": "wis", "effect": "shocked", "duration": 2, "cost": 20, "cd": 5, "tags": ["offensive", "debuff"]},
            {"name": "Hammer of Judgement", "icon": "(", "unlock_lv": 14, "desc": "A massive hammer of pure willpower.", "formula": "dmg = (5 + WISx2.0 + STRx0.8) x 2.5", "type": "mixed_magic", "power": 2.5, "stat": "wis", "stat2": "str", "stat2_mult": 0.8, "cost": 22, "cd": 5, "tags": ["offensive", "dual-stat"]},
            {"name": "Martyr's Wrath", "icon": ")", "unlock_lv": 14, "desc": "Sacrifice HP for devastating power.", "formula": "dmg = (5 + WISx2.0 + INTx1.0) x 2.5, 20% HP", "type": "mixed_magic", "power": 2.5, "stat": "wis", "stat2": "int", "stat2_mult": 1.0, "hp_cost": 0.2, "cost": 10, "cd": 5, "tags": ["offensive", "dual-stat"]},
            {"name": "Sanctuary", "icon": "[", "unlock_lv": 16, "desc": "Create a zone of absolute protection.", "formula": "Full barrier(3), shield=WISx4, heal WISx2", "type": "self_shield", "cost": 20, "cd": 7, "shield_calc": "sanctuary", "tags": ["defensive", "ultimate"]},
            {"name": "Wrath of the Threshold", "icon": "]", "unlock_lv": 16, "desc": "Channel all defensive power into offense.", "formula": "dmg = (5 + WISx2.5 + shieldx0.3) x 2.5", "type": "mixed_magic", "power": 2.5, "stat": "wis", "shield_scaling": 0.3, "cost": 22, "cd": 6, "tags": ["offensive"]},
            {"name": "Oath of Protection", "icon": "{", "unlock_lv": 18, "desc": "Linked defense. Shield + regen for 3 turns.", "formula": "shield=WISx3, regen 10% HP/turn, barrier+1 for 3t", "type": "self_buff", "cost": 18, "cd": 7, "buff_type": "oath", "buff_duration": 3, "tags": ["defensive", "support", "ultimate"]},
            {"name": "Seal of Carcosa", "icon": "}", "unlock_lv": 19, "desc": "The ultimate ward. Full heal + massive shield + damage.", "formula": "Full heal, shield=WISx5, barrier x3, dmg WISx3", "type": "ultimate", "power": 3.0, "stat": "wis", "cost": 30, "cd": 8, "tags": ["offensive", "defensive", "ultimate"]},
        ],
    },
    "shadowblade": {
        "name": "Shadowblade of Carcosa",
        "icon": "D",
        "desc": "Swift and deadly. Critical strikes, evasion, and poison. Glass cannon that dances on the edge of death.",
        "base_stats": {"int": 7, "str": 7, "agi": 14, "wis": 7, "luck": 8},
        "hp_base": 75, "hp_per_level": 7,
        "skills": [
            {"name": "Shadow Strike", "icon": "*", "unlock_lv": 1, "desc": "A swift strike from the shadows.", "formula": "dmg = ATKx1.5 + AGIx1.0 physical", "type": "physical", "power": 1.5, "stat": "agi", "cost": 0, "cd": 0, "tags": ["offensive"]},
            {"name": "Venom Blade", "icon": "~", "unlock_lv": 1, "desc": "Coat your blade in eldritch poison.", "formula": "dmg = ATKx1.2 + Poison 3 turns", "type": "physical_debuff", "power": 1.2, "stat": "agi", "effect": "poisoned", "duration": 3, "cost": 5, "cd": 2, "tags": ["offensive", "debuff"]},
            {"name": "Smoke Screen", "icon": "!", "unlock_lv": 2, "desc": "Vanish in smoke. EVA +25% 2 turns.", "formula": "Self: EVA+25% for 2 turns", "type": "self_buff", "cost": 5, "cd": 3, "buff_type": "smokeScreen", "buff_duration": 2, "tags": ["defensive"]},
            {"name": "Backstab", "icon": "#", "unlock_lv": 2, "desc": "Strike from behind. +50% crit chance.", "formula": "dmg = ATKx1.8 + AGIx0.5, +50% CRIT", "type": "physical", "power": 1.8, "stat": "agi", "flat_crit_bonus": 50, "cost": 8, "cd": 2, "tags": ["offensive"]},
            {"name": "Poison Cloud", "icon": "^", "unlock_lv": 4, "desc": "Envelop the enemy in toxic gas.", "formula": "dmg = ATKx0.5 + Poison stacking to 5", "type": "debuff", "power": 0.5, "stat": "agi", "effect": "poisoned", "duration": 3, "cost": 10, "cd": 3, "tags": ["debuff"]},
            {"name": "Blade Dance", "icon": "v", "unlock_lv": 4, "desc": "Unleash a flurry of precise strikes.", "formula": "dmg = ATKx0.7 x 4 hits", "type": "physical", "power": 0.7, "stat": "agi", "multihit": 4, "cost": 12, "cd": 3, "tags": ["offensive"]},
            {"name": "Siphon Life", "icon": "@", "unlock_lv": 6, "desc": "Drain the enemy's vitality.", "formula": "dmg = ATKx1.4 + AGIx0.6, heal 50% dealt", "type": "physical", "power": 1.4, "stat": "agi", "lifesteal": 0.5, "cost": 12, "cd": 3, "tags": ["offensive", "defensive"]},
            {"name": "Evasion", "icon": "+", "unlock_lv": 6, "desc": "Become nearly untouchable. EVA+40% 3t.", "formula": "Self: EVA+40% for 3 turns", "type": "self_buff", "cost": 8, "cd": 5, "buff_type": "evasionUp", "buff_duration": 3, "tags": ["defensive"]},
            {"name": "Wound", "icon": "-", "unlock_lv": 8, "desc": "Deep cut that bleeds profusely.", "formula": "dmg = ATKx1.0 + Bleed 5% HP/turn 3t", "type": "physical_debuff", "power": 1.0, "stat": "agi", "effect": "bleeding", "duration": 3, "cost": 10, "cd": 3, "tags": ["offensive", "debuff"]},
            {"name": "Shuriken Storm", "icon": "=", "unlock_lv": 8, "desc": "Hurl shuriken in all directions.", "formula": "dmg = ATKx0.5 x 5 hits + LUK scaling", "type": "physical", "power": 0.5, "stat": "agi", "multihit": 5, "luck_bonus": True, "cost": 15, "cd": 4, "tags": ["offensive"]},
            {"name": "Shadow Meld", "icon": ";", "unlock_lv": 10, "desc": "Become one with shadow. Invisible 1 turn.", "formula": "Self: cannot be hit 1 turn, next attack +100%", "type": "self_buff", "cost": 12, "cd": 5, "buff_type": "shadowMeld", "buff_duration": 1, "tags": ["defensive", "support"]},
            {"name": "Assassinate", "icon": "|", "unlock_lv": 10, "desc": "Instant kill attempt on weakened foes.", "formula": "dmg = ATKx3.0 + AGIx2.0 if <25% HP", "type": "physical", "power": 3.0, "stat": "agi", "execute_bonus": True, "cost": 20, "cd": 5, "tags": ["offensive", "ultimate"]},
            {"name": "Toxic Blade", "icon": "$", "unlock_lv": 12, "desc": "Deadly poison that ignores resist.", "formula": "dmg = ATKx1.5 + Poison 5 stacks, ignores 30% DEF", "type": "physical_debuff", "power": 1.5, "stat": "agi", "effect": "poisoned", "duration": 3, "armor_pierce": 0.3, "cost": 15, "cd": 4, "tags": ["offensive", "debuff"]},
            {"name": "Shadow Step", "icon": "&", "unlock_lv": 12, "desc": "Teleport behind enemy. Guaranteed crit.", "formula": "dmg = ATKx2.0 + AGIx1.0, guaranteed crit", "type": "physical", "power": 2.0, "stat": "agi", "guaranteed_crit": True, "cost": 18, "cd": 4, "tags": ["offensive"]},
            {"name": "Crimson Flurry", "icon": "(", "unlock_lv": 14, "desc": "Six rapid strikes, each more deadly.", "formula": "dmg = ATKx0.6 x 6 + STRx0.3", "type": "mixed_phys", "power": 0.6, "stat": "agi", "stat2": "str", "stat2_mult": 0.3, "multihit": 6, "cost": 22, "cd": 5, "tags": ["offensive"]},
            {"name": "Dark Pact", "icon": ")", "unlock_lv": 14, "desc": "Trade HP for devastating poison mastery.", "formula": "All debuffs +2 duration, +30% dmg, costs 15% HP", "type": "self_buff", "cost": 8, "cd": 6, "buff_type": "darkPact", "buff_duration": 3, "tags": ["support"]},
            {"name": "Nightmare", "icon": "[", "unlock_lv": 16, "desc": "Plunge enemy into waking nightmare.", "formula": "dmg = ATKx2.0 + Blind+Shocked 3 turns", "type": "physical_debuff", "power": 2.0, "stat": "agi", "effect": "blinded", "effect2": "shocked", "duration": 3, "cost": 25, "cd": 6, "tags": ["offensive", "debuff"]},
            {"name": "Eclipse", "icon": "]", "unlock_lv": 16, "desc": "Eclipse of light. All attacks crit 2 turns.", "formula": "Self: 100% CRIT, +30% DMG 2 turns", "type": "self_buff", "cost": 15, "cd": 6, "buff_type": "eclipse", "buff_duration": 2, "tags": ["support"]},
            {"name": "Phantom Blades", "icon": "{", "unlock_lv": 18, "desc": "Ethereal blades that bypass all defense.", "formula": "dmg = ATKx1.0 x 4, ignores 100% DEF", "type": "physical", "power": 1.0, "stat": "agi", "multihit": 4, "armor_pierce": 1.0, "cost": 25, "cd": 6, "tags": ["offensive"]},
            {"name": "Death's Embrace", "icon": "}", "unlock_lv": 19, "desc": "The final dance. Massive damage + all debuffs.", "formula": "dmg = (ATKx1.5 + AGIx2.0) x 3.0 + Bleed+Poison", "type": "mixed_phys", "power": 3.0, "stat": "agi", "stat2": "str", "stat2_mult": 0.5, "effect": "bleeding", "effect2": "poisoned", "duration": 3, "cost": 30, "cd": 7, "tags": ["offensive", "ultimate"]},
        ],
    },
    "mad_prophet": {
        "name": "Mad Prophet of Hastur",
        "icon": "P",
        "desc": "Blessed and cursed by visions. Powerful debuffs, madness manipulation, and chaos. High risk, high reward.",
        "base_stats": {"int": 10, "str": 5, "agi": 7, "wis": 12, "luck": 9},
        "hp_base": 80, "hp_per_level": 7,
        "skills": [
            {"name": "Prophetic Vision", "icon": "*", "unlock_lv": 1, "desc": "A flash of terrible insight, weaponized.", "formula": "dmg = (5 + WISx1.5) x 1.3 magic", "type": "magic", "power": 1.3, "stat": "wis", "cost": 0, "cd": 0, "tags": ["offensive"]},
            {"name": "Madness Touch", "icon": "~", "unlock_lv": 1, "desc": "Inflict your madness on the enemy.", "formula": "dmg = (5 + WISx1.0) x 0.8 + Shock 2t", "type": "magic_debuff", "power": 0.8, "stat": "wis", "effect": "shocked", "duration": 2, "cost": 5, "cd": 2, "tags": ["offensive", "debuff"]},
            {"name": "Dark Prophecy", "icon": "!", "unlock_lv": 2, "desc": "Curse the enemy with dark foresight.", "formula": "Enemy: -20% ATK, -15% DEF 3 turns", "type": "debuff", "effect": "weakened", "duration": 3, "power": 0, "stat": "wis", "cost": 8, "cd": 3, "tags": ["debuff"]},
            {"name": "Channel Madness", "icon": "#", "unlock_lv": 2, "desc": "Convert madness into power.", "formula": "dmg = WISx2.0 x (1 + MAD/100), costs 5 MAD", "type": "magic", "power": 1.0, "stat": "wis", "madness_scaling": True, "madness_cost": 5, "cost": 0, "cd": 2, "tags": ["offensive"]},
            {"name": "Yellow Haze", "icon": "^", "unlock_lv": 4, "desc": "Envelop the area in madness-inducing fog.", "formula": "Enemy: Blind 3t + Poison 2t", "type": "debuff", "effect": "blinded", "effect2": "poisoned", "duration": 3, "power": 0, "stat": "wis", "cost": 12, "cd": 4, "tags": ["debuff"]},
            {"name": "Visions of Carcosa", "icon": "v", "unlock_lv": 4, "desc": "Show the enemy the truth. Petrify + damage.", "formula": "dmg = (5 + WISx1.5) x 1.5 + Petrify 2t", "type": "magic_debuff", "power": 1.5, "stat": "wis", "effect": "petrified", "duration": 2, "cost": 12, "cd": 3, "tags": ["offensive", "debuff"]},
            {"name": "Empower Madness", "icon": "@", "unlock_lv": 6, "desc": "Gain power from madness. +MAD = +DMG.", "formula": "Self: +25% DMG, +15 MAD 3 turns", "type": "self_buff", "cost": 0, "cd": 4, "buff_type": "madPower", "buff_duration": 3, "tags": ["support"]},
            {"name": "Healing Hysteria", "icon": "+", "unlock_lv": 6, "desc": "Laugh until you're healed. Or scream.", "formula": "Heal = WISx2.5 + LUKx1, +5 MAD", "type": "self_heal", "cost": 0, "cd": 3, "heal_calc": "wis2_luck1", "tags": ["defensive"]},
            {"name": "Prophecy of Doom", "icon": "-", "unlock_lv": 8, "desc": "Doom falls in 3 turns. Massive delayed damage.", "formula": "Enemy takes WISx4 damage after 3 turns", "type": "debuff", "effect": "doom", "duration": 3, "power": 0, "stat": "wis", "cost": 15, "cd": 6, "tags": ["debuff"]},
            {"name": "Scream of Madness", "icon": "=", "unlock_lv": 8, "desc": "AoE scream that damages and debuffs.", "formula": "dmg = (5 + WISx1.5) x 1.8 + Weaken 3t", "type": "magic_debuff", "power": 1.8, "stat": "wis", "effect": "weakened", "duration": 3, "cost": 18, "cd": 4, "tags": ["offensive", "debuff"]},
            {"name": "Fate's Coin", "icon": ";", "unlock_lv": 10, "desc": "Flip a coin. Heads: heal 25%. Tails: 1.5x dmg.", "formula": "50%: Heal 25% HP OR deal 1.5x damage", "type": "mixed_magic", "power": 1.5, "stat": "wis", "coin_flip": True, "cost": 10, "cd": 3, "tags": ["offensive", "defensive"]},
            {"name": "Carcosa's Blessing", "icon": "|", "unlock_lv": 10, "desc": "Full heal but gain +25 MAD.", "formula": "Full HP restore, +25 MAD", "type": "self_heal", "cost": 0, "cd": 8, "heal_calc": "full_heal", "tags": ["defensive"]},
            {"name": "Gamble of Fate", "icon": "$", "unlock_lv": 12, "desc": "Random damage between 0.5x and 3.0x.", "formula": "dmg = (5 + WISx2.0) x 0.5~3.0 random", "type": "magic", "power": 2.0, "stat": "wis", "gamble": True, "cost": 12, "cd": 3, "tags": ["offensive"]},
            {"name": "Terrifying Visage", "icon": "&", "unlock_lv": 12, "desc": "Show your madness. Mass debuff.", "formula": "Enemy: Weaken+Blind+Shocked 2 turns", "type": "debuff", "effect": "weakened", "effect2": "blinded", "effect3": "shocked", "duration": 2, "power": 0, "stat": "wis", "cost": 20, "cd": 5, "tags": ["debuff"]},
            {"name": "Madness Nova", "icon": "(", "unlock_lv": 14, "desc": "Explode with eldritch energy.", "formula": "dmg = (5 + WISx2.0) x 2.5 + Burn 3t", "type": "magic_debuff", "power": 2.5, "stat": "wis", "effect": "burning", "duration": 3, "cost": 22, "cd": 5, "tags": ["offensive", "debuff"]},
            {"name": "Reality Glitch", "icon": ")", "unlock_lv": 14, "desc": "Bend reality. All debuffs +2 duration.", "formula": "Extend all enemy debuffs by 2, dmg WISx1.0", "type": "mixed_magic", "power": 1.0, "stat": "wis", "extend_debuffs": True, "cost": 18, "cd": 5, "tags": ["offensive", "debuff"]},
            {"name": "Apocalyptic Dream", "icon": "[", "unlock_lv": 16, "desc": "The world ends in your dream. Massive damage.", "formula": "dmg = (5 + WISx2.5 + INTx1.0) x 2.8", "type": "mixed_magic", "power": 2.8, "stat": "wis", "stat2": "int", "stat2_mult": 1.0, "cost": 25, "cd": 6, "tags": ["offensive"]},
            {"name": "Commune with Hastur", "icon": "]", "unlock_lv": 16, "desc": "Ask Hastur for aid. Random powerful effect.", "formula": "Random: Heal/Full debuff/Max damage/LUK+5", "type": "mixed_magic", "power": 3.0, "stat": "wis", "random_effect": True, "cost": 15, "cd": 6, "tags": ["offensive", "defensive", "support"]},
            {"name": "The Pallid Mask", "icon": "{", "unlock_lv": 18, "desc": "Become the Pallid Mask. 3 turns of power.", "formula": "Self: +50% all stats, immune to debuffs 3t", "type": "self_buff", "cost": 20, "cd": 8, "buff_type": "pallidMask", "buff_duration": 3, "tags": ["support", "ultimate"]},
            {"name": "Hastur's Decree", "icon": "}", "unlock_lv": 19, "desc": "Invoke the King himself. Ultimate destruction.", "formula": "dmg = (5 + WISx2.0 + INTx1.5) x 3.5 + ALL debuffs", "type": "mixed_magic", "power": 3.5, "stat": "wis", "stat2": "int", "stat2_mult": 1.5, "effect": "burning", "effect2": "petrified", "effect3": "blinded", "duration": 3, "cost": 35, "cd": 8, "tags": ["offensive", "ultimate"]},
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
    {"type": "combat", "icon": "!", "name": "Dark Passage", "desc": "Something stirs in the shadows", "hint": "Enemy", "weight": 3},
    {"type": "combat", "icon": "+", "name": "Blood Trail", "desc": "A trail of blood leads into the dark", "hint": "Enemy", "weight": 3},
    {"type": "combat", "icon": "~", "name": "Lurking Horror", "desc": "Eyes watch from the darkness", "hint": "Enemy", "weight": 2},
    {"type": "event", "icon": "?", "name": "Strange Sound", "desc": "An unearthly melody echoes", "hint": "Unknown", "weight": 1},
    {"type": "event", "icon": "#", "name": "Forbidden Text", "desc": "A tome lies open, pages turning", "hint": "Knowledge or madness", "weight": 1},
    {"type": "loot", "icon": "=", "name": "Supply Room", "desc": "An untouched closet, door ajar", "hint": "Equipment", "weight": 1},
    {"type": "loot", "icon": "$", "name": "Offering", "desc": "Something glitters on a stone altar", "hint": "Equipment", "weight": 1},
    {"type": "rest", "icon": "-", "name": "Safe Haven", "desc": "A moment of calm in the storm", "hint": "Healing", "weight": 1},
    {"type": "shop", "icon": "@", "name": "Mad Trader", "desc": "A figure deals in strange wares", "hint": "Items", "weight": 1},
    {"type": "trap", "icon": "^", "name": "Suspicious Hallway", "desc": "Uneven floor, thick dread", "hint": "Danger", "weight": 1},
]

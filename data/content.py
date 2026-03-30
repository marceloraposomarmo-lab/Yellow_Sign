"""Static game content: events, traps, path templates, and floor narratives."""

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

# ═══════════════════════════════════════════
# TRAPS
# ═══════════════════════════════════════════

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
# PATH TYPES FOR EXPLORATION
# ═══════════════════════════════════════════

PATH_TEMPLATES = [
    {"type": "combat", "icon": "!", "name": "Dark Passage", "desc": "Something stirs in the shadows", "desc2": "A creature lurks ahead. Steel yourself \u2014 blood will be spilled.", "hint": "Enemy", "weight": 3},
    {"type": "combat", "icon": "+", "name": "Blood Trail", "desc": "A trail of blood leads into the dark", "desc2": "Fresh crimson stains mark the floor. Something wounded \u2014 or something feeding.", "hint": "Enemy", "weight": 3},
    {"type": "combat", "icon": "~", "name": "Lurking Horror", "desc": "Eyes watch from the darkness", "desc2": "Dozens of unblinking eyes pierce the gloom. The beast is patient. You are not safe.", "hint": "Enemy", "weight": 2},
    {"type": "event", "icon": "?", "name": "Strange Sound", "desc": "An unearthly melody echoes", "desc2": "A haunting tune drifts through the corridors. Approach, and face the unknown.", "hint": "Unknown", "weight": 1},
    {"type": "event", "icon": "#", "name": "Forbidden Text", "desc": "A tome lies open, pages turning", "desc2": "Knowledge or madness \u2014 the pages whisper secrets no mortal should hear.", "hint": "Knowledge or madness", "weight": 1},
    {"type": "loot", "icon": "=", "name": "Supply Room", "desc": "An untouched closet, door ajar", "desc2": "Someone abandoned their belongings here. Take what you can \u2014 you will need it.", "hint": "Equipment", "weight": 1},
    {"type": "loot", "icon": "$", "name": "Offering", "desc": "Something glitters on a stone altar", "desc2": "An offering to forgotten gods. The treasure is yours \u2014 if you dare claim it.", "hint": "Equipment", "weight": 1},
    {"type": "rest", "icon": "-", "name": "Safe Haven", "desc": "A moment of calm in the storm", "desc2": "A rare sanctuary. Tend your wounds, clear your mind, or prepare your body.", "hint": "Healing", "weight": 1},
    {"type": "shop", "icon": "@", "name": "Mad Trader", "desc": "A figure deals in strange wares", "desc2": "Eyes wild, smile crooked. Their goods are real \u2014 the price, however, is never simple.", "hint": "Items", "weight": 1},
    {"type": "trap", "icon": "^", "name": "Suspicious Hallway", "desc": "Uneven floor, thick dread", "desc2": "The stones shift beneath your feet. Every step could be your last. Tread carefully.", "hint": "Danger", "weight": 1},
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
    "The corridors twist and fold. You've been walking in circles \u2014 or have you?",
    "Carcosa's influence grows. The yellow tint in everything is unmistakable now.",
    "The walls bleed light. Shadows move independently. The end is near.",
    "You can feel the King's presence. The air crackles with ancient power.",
    "The final corridors. Every step echoes with the weight of millennia.",
    "Carcosa's Gate. The walls are no longer walls. They breathe. They watch.",
    "The throne room of the King in Yellow. There is no escape but through.",
]

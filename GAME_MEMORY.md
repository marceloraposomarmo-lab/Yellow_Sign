# GAME PROJECT — Persistent Memory

## Project Overview
- **Title**: "The King in Yellow — A Lovecraftian Dungeon Crawler"
- **Genre**: Dungeon crawler, text RPG (inspired by Buried Bornes)
- **Theme**: Lovecraftian mythos, The King in Yellow / Carcosa
- **Engine**: Pygame (Python)
- **Resolution**: 1280×720 (windowed), supports fullscreen (F11)
- **Palette**: Dark purples, golds, bone whites — ornate gothic style
- **Design reference**: `transparent-Text-box-Sample.png` shows the ornate gold-trim dark panel style

## File Structure (Refactored 2026-03-28)
```
game/
├── pygame_game.py        ← Main graphical game (THE FILE WE EDIT) — 3157 lines
├── save_system.py        ← Save/load functionality (JSON, 5 slots)
├── data/                 ← Game data package (replaces old game_data.py)
│   ├── __init__.py       ← Re-exports everything
│   ├── constants.py      ← MAX_ACTIVE_SKILLS, sprite/icon mappings
│   ├── classes.py        ← 5 classes + ~40 skills each (308 lines)
│   ├── enemies.py        ← Enemy definitions + boss (86 lines)
│   ├── items.py          ← Rarity, prefixes, equipment templates (65 lines)
│   ├── events.py         ← Floor events + traps (97 lines)
│   └── narratives.py     ← Floor narratives + path templates (56 lines)
├── engine/               ← Game logic package (replaces old game_engine.py)
│   ├── __init__.py       ← Re-exports everything
│   ├── models.py         ← Item, Skill, StatusEffect, Enemy, GameState (372 lines)
│   ├── combat.py         ← Combat system, item generation, damage calc (835 lines)
│   └── world.py          ← Floor progression, events, traps, shop (175 lines)
├── ROADMAP.md            ← Visual overhaul progress tracker
├── GAME_MEMORY.md        ← This file
├── images/               ← ALL sprite/background/icon assets (47 files)
├── fonts/                ← Custom fonts (CinzelDecorative, Cinzel)
└── saves/                ← Save files directory (auto-created)
```

## Image Assets (41 files in images/)
### Backgrounds
- `Dungeon_background.jfif` — dungeon floors 1-19 (1376×768 JPEG)
- `Game_Over_Screen.jfif` — game over (1024×1024 JPEG)

### Class Sprites (5)
- `transparent-Int-basedClass.png` — Scholar (1024×1024 RGBA)
- `transparent-Strenght-basedClass.png` — Brute (1024×1024 RGBA)
- `wis-character.png` — Warden (1024×1024 RGBA)
- `transparent-Agi-basedClass.png` — Shadowblade (1024×1024 RGBA)
- `transparent-luck-basedClass.png` — Mad Prophet (1024×1024 RGBA)

### Enemy Sprites (6 + Boss)
- `transparent-lovecraftian-monster[1,3-7].png` — 6 enemy sprites (1024×1024 RGBA)
- `Boss_F.png` — Boss/Hastur source (1024×1024 RGBA)
- `transparent-Boss.png` — Boss sprite (loaded by game, may need rename)

### Stat Icons (5 stats × multiple sizes)
- Source `_F.png` files: 1024×1024 RGBA
- Resized variants: `_32.png`, `_36.png`, `_48.png`, `_64.png`
- `Intelligence_Icon`, `Strenght_Icon`, `Agility_Icon`, `Wisdom_Icon`, `Luck_Icon`

### UI
- `transparent-Cursor.png` — custom cursor (72×72, palette mode)
- `transparent-Text-box-Sample.png` — UI design reference (1200×896 RGBA)
- `Ingame_Font.jpg` — font style reference screenshot

### Path Choice Icons (6) — Loaded at 64×64 in Assets
- `Enemy_Ahead_F.png` — combat rooms (1024×1024 RGBA)
- `Boss_Ahead_F.png` — boss room (1024×1024 RGBA, loaded for future use)
- `Shop_Ahead_F.png` — shop rooms (578×432 RGBA)
- `Item_Ahead.png` — loot rooms (1024×1024 RGBA)
- `Rest_Ahead_F.jfif` — safe/rest rooms (1200×896 RGB)
- `Decision_Ahead.png` — events & traps (1024×1024 RGBA)

## Key Technical Notes
- CinzelDecorative-Regular.ttf + Cinzel.ttf downloaded to `fonts/` — Victorian/occult title + body fonts active
- `fit_text()` and `draw_text_fitted()` for pixel-width text truncation
- Screen class hierarchy: `Screen` base → individual screen classes → registered in `Game.screens` dict
- HUD is drawn by `draw_hud()` function (not a screen class), called at top of explore/combat screens
- `hover_idx` + `update_hover()` on Screen base class — all screens use hover effects

## Visual Overhaul Status
- ✅ Steps 0-9: Complete (fullscreen, fonts, icons, polish)
- ✅ Step 10: Class Selection Overhaul — one class per page with arrow navigation
- ✅ Step 11: Removed stat icons from combat skill buttons (kept in level-up + stats)
- ✅ Step 12: Parchment Text Box Overhaul — all content panels now use procedural aged parchment texture with ornate gold frames, ink-colored text with glow effects, improved readability across all screens
- ✅ Step 13: Asset Restore + Spacing Fix — all 36 assets restored, fonts downloaded, stat icon variants generated, spacing fixes across Game Over / Explore / Shop / Event / Loot screens
- ✅ Step 14: Exploration Path Icons + Two-Line Descriptions — 6 new path choice icons loaded at 64×64, PATH_TEMPLATES expanded with desc2, ExploreScreen redesigned with icon + name + description per path button
- ✅ Step 15: Side-by-Side Path Layout + Bigger Icons — icons scaled to 150×150, stacked layout → side-by-side cards (560×260), description text word-wrapped
- ✅ Step 16: Luck Icon Fix + Card Rendering Cleanup — replaced Luck_Icon_F with correct version, regenerated variants, cleaner card rendering

## Refactoring Notes (2026-03-28)
- Split `game_data.py` (650 lines) → `data/` package (6 files, biggest is 308 lines)
- Split `game_engine.py` (1361 lines) → `engine/` package (3 logic files + init)
- `pygame_game.py` kept as single file (splitting UI code = high risk, low reward)
- All imports updated: `from data import ...` / `from engine import ...`
- `main.py` removed (depended on nonexistent `ui` module, was dead code)
- Backward-compatible: `data/__init__.py` and `engine/__init__.py` re-export everything
- Old `game_data.py` and `game_engine.py` removed
- Fixed ClassSelectScreen crash: `ability_btns`/`future_btns` not initialized in `__init__`
- Fixed 38 broken buff types (see Buff System section below)
- Fixed 6 madness/instant-effect skills with buff_duration=0 (calmMind, eldritchBargain, foolLuck, realityAnchor, pallidMask, prophetRes)
- `apply_status_player()` now checks immunity buff — debuff immunity works

## Buff System (engine/combat.py)
67 buff types defined across 5 classes. Most are simple "store name + duration" with effects checked elsewhere:

### Defensive Buffs (handled by `_get_buff_defense_bonus` + `_get_buff_evasion_bonus`)
- **EVA buffs**: smokeScreen(+25), dreamVeil(+35), evasionUp(+40), dreamShell(+50), umbralAegis(+60)
- **pDEF buffs**: thoughtform(+30), ironSkin(+60), chant(+20), innerFire(+15), hallowed(+40), fortress(+80), bulwark(+60), umbralAegis(+40)
- **mDEF buffs**: thoughtform(+30), ironSkin(+30), mDefUp(+50), chant(+20), wardAura(+30), innerFire(+15), hallowed(+40), fortress(+80), bulwark(+60), dreamShell(+80)

### Special Defensive (handled in `apply_damage_to_player`)
- divineInterv: nullify next N attacks (stacks decrement on proc)
- ethereal: invulnerable while active, +150% damage on next attack (consumed)
- flicker: 50% dodge chance per stack (decrement on proc)
- mirrorImg: 30% damage reduction
- undying/undyingPact: can't die (set HP to 1)
- finalStand: invulnerable
- bloodAura: 10% lifesteal on damage taken
- retribAura: reflect 30% damage to attacker

### Damage Buffs (checked in `calc_player_damage`)
- rage: +60% damage
- atkCritUp: +40% damage, +20% crit
- warpTime: +20% damage
- madPower: +25% damage
- darkPact: +30% damage
- shadowMeld: +100% damage
- eclipse: +30% damage
- ethereal: +150% damage (consumed after attack)

### Tick Effects (handled in `tick_player_buffs`)
- regen: heal 8% HP/turn
- regen5: heal 5% HP/turn
- oath: heal 10% HP/turn
- calmMind: -3 MAD/turn

### Stat Buffs (via temp_stats, handled in `tick_player_buffs` expire cleanup)
- permIntWis: INT+6, WIS+4
- permAtk2: STR+5
- permWisStr: WIS+6, STR+4
- permAgiLuk: AGI+7, LUCK+4
- permAll1: all stats +4
- thickSkull: STR+4, WIS+3
- perseverance: WIS+4, STR+3
- shadowBless: AGI+4, LUCK+3
- randStat2: random 2 stats +3

### Utility Buffs (checked in `player_use_skill`)
- resetCds: reset all cooldowns
- bloodRitual: -15% HP, +50 XP
- madImmune: madness no longer causes death
- permCrit10: +25% crit (cleaned on expire)
- calmMind: instant -3 MAD (Leng's Whisper)
- eldritchBargain: instant -3 to 3 random stats, +50 gold
- foolLuck: instant -10 MAD + divineInterv 3 stacks
- realityAnchor: maps to undying for 2 turns
- pallidMask: +50% all stats (temp) + immunity to debuffs 3 turns
- prophetRes: +5 MAD, maps to regen for 2 turns

### Debuff Immunity
- `immunity` buff checked in `apply_status_player()` — blocks all debuffs
- Applied by: Hastur's Embrace (2t), The Pallid Mask (3t)

## Crash Prevention Protocol
1. ONE task per prompt
2. Save code file after EVERY step
3. Save ROADMAP.md after EVERY step
4. Save GAME_MEMORY.md after EVERY step with new learnings
5. Verify syntax with `python3 -c "import py_compile; py_compile.compile(...)"`

## Bug Fixes (Session 11 — 2026-03-28)
### Combat → Inventory/Save Bug (Fixed)
- **Symptom**: Opening inventory or save screen from combat immediately exited combat, losing all combat state
- **Root cause**: `InventoryScreen.enter()` set `self.prev_screen = "combat" if self.game.state.combat else "explore"` but this ran BEFORE the screen name was set in the game's `_current_screen_name`. Also, the combat screen called `self.game.switch_screen("inventory")` but the inventory didn't know the previous screen was combat.
- **Fix in InventoryScreen.enter()**: Now reads `self.game._current_screen_name` first, then overrides to "combat" if combat is active
- **Fix in SaveScreen**: Added `self.prev_screen` tracking and `_get_return_screen()` helper that checks combat state. All return paths (back button, escape key, after save) use this helper.
- **LoadScreen**: Inherits from SaveScreen, loading always transitions to explore (correct behavior — loaded games start in explore)

## Refactoring: player_use_skill() Handler Architecture (2026-03-28)
- **Before**: 300+ line if/elif chain in `player_use_skill()` — one typo breaks combat silently
- **After**: Three handler modules with registries:
  - `HEAL_HANDLERS` dict: heal_calc name → (calc_fn, message_template). 15 heal types.
  - `SHIELD_HANDLERS` dict: shield_calc name → (build_fn, message_template). 10 shield types.
  - `BUFF_HANDLERS` dict: buff_type → apply_fn. `BUFF_MESSAGES` dict: buff_type → message template. 23 buff types.
  - `player_use_skill()` now: pre-checks → dispatch to handler → damage path. ~30 lines.
- Adding a new skill: write one small function, add one dict entry. No risk to existing code.
- All existing behaviors preserved: tested by compilation + line-by-line comparison.

## Known Issues / Future Work
- Some buff types still unimplemented (bladeAura, copyAttack, skipCombat, etc.) — low priority, not used by any current skill
- ~~`draw_text_with_glow()` renders text 9× per call~~ → FIXED: now uses glow surface cache (2 blits on cache hit vs 25 renders). Cache: `_glow_text_cache` dict, 4096 entry limit, evicts 25% on overflow. Keyed by (text, font_id, color, glow_color, glow_radius).
- `pygame_game.py` at 3,200 lines — screens could be split into modules
- Parchment texture cache by (w,h) tuple — could use atlas or tile approach
- No automated tests
- `draw_text_with_glow()` renders text 8+ times per call — performance bottleneck, consider caching
- ~~No automated tests — one bad number in skill dict can break combat silently~~ → FIXED: `tests/test_combat.py` — 19 suites, 271 assertions. Covers state init, damage calc, all 5 classes, skill types, buffs, regen, immunity, poison, cooldowns, enemy AI, boss phases, flee, item gen, madness death, HP cost, lifesteal, full combat sim. Run: `python3 tests/test_combat.py`

## Class Select Overhaul Details (Step 10)
- Redesigned from all-5-at-once to one-class-per-page
- Layout: 400×400 sprite (left), info panel (right)
- Right panel: class name → description → stats → starting abilities (lv1) → future abilities (top 3 by power) → Choose button
- Hover tooltip: damage formula shown in popup above the ability button
- Navigation: Left/Right arrow keys, page indicator "1/5"

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
├── pygame_game.py        ← Game class + entry point (237 lines)
├── shared.py             ← Constants, Assets, all drawing functions (892 lines)
├── screens/              ← Screen modules (one per screen)
│   ├── __init__.py       ← Re-exports all screen classes
│   ├── base.py           ← Screen base class (37 lines)
│   ├── title.py          ← TitleScreen (134 lines)
│   ├── class_select.py   ← ClassSelectScreen (200 lines)
│   ├── explore.py        ← ExploreScreen (195 lines)
│   ├── combat.py         ← CombatScreen (385 lines) — biggest
│   ├── inventory.py      ← InventoryScreen (119 lines)
│   ├── shop.py           ← ShopScreen (105 lines)
│   ├── rest.py           ← RestScreen (88 lines)
│   ├── loot.py           ← LootScreen (95 lines)
│   ├── event.py          ← EventScreen (92 lines)
│   ├── trap_result.py    ← TrapResultScreen (37 lines)
│   ├── combat_result.py  ← CombatResultScreen (117 lines)
│   ├── levelup.py        ← LevelUpScreen (180 lines)
│   ├── gameover.py       ← GameOverScreen (49 lines)
│   ├── victory.py        ← VictoryScreen (84 lines)
│   ├── stats.py          ← StatsScreen (186 lines)
│   └── save.py           ← SaveScreen + LoadScreen (113 lines)
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
- Screen class hierarchy: `Screen` base (screens/base.py) → individual screen classes (screens/*.py) → registered in `Game.screens` dict
- HUD is drawn by `draw_hud()` function (in pygame_game.py), called at top of explore/combat screens
- `hover_idx` + `update_hover()` on Screen base class — all screens use hover effects
- All shared drawing/texture code in `shared.py` — screens import from it, no circular deps

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
- Split `pygame_game.py` (3,225 lines) → `shared.py` (892) + `screens/` (17 files) + `pygame_game.py` (237)
- All imports updated: `from data import ...` / `from engine import ...` / `from shared import ...` / `from screens import ...`
- `main.py` removed (depended on nonexistent `ui` module, was dead code)
- Backward-compatible: `data/__init__.py`, `engine/__init__.py`, `screens/__init__.py` re-export everything
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
- ~~No automated tests~~ → FIXED: `tests/test_combat.py` — 19 suites, 271 assertions.
- `draw_text_with_glow()` renders text 8+ times per call — performance bottleneck, consider caching
- ~~No automated tests — one bad number in skill dict can break combat silently~~ → FIXED: `tests/test_combat.py` — 19 suites, 271 assertions. Covers state init, damage calc, all 5 classes, skill types, buffs, regen, immunity, poison, cooldowns, enemy AI, boss phases, flee, item gen, madness death, HP cost, lifesteal, full combat sim. Run: `python3 tests/test_combat.py`

## Bug Fixes (Session 13 — 2026-03-28)
### Doom Effect Not Triggering (Fixed — Step 29)
- **Symptom**: Scholar's "Curse of the Pallid Mask" applies `doom` debuff (3 turns), but when it expires nothing happens
- **Root cause**: `process_status_effects()` had no handler for `doom` — it just logged "doom wears off"
- **Fix**: Added doom-specific logic in the `to_remove` loop. When doom expires on enemy and HP < 30%: instant kill with dramatic log message. Otherwise: "The Pallid Mask fades..." flavor text.

### 4 Unimplemented Buff Types (Fixed — Step 30)
- **Symptom**: Skills referencing `eldritchRebirth`, `astral`, `statSwap`, `dreadnought` had no actual effect
- **Fix**: Added handler functions + messages + combat logic for each:
  - `eldritchRebirth`: `apply_damage_to_player()` checks buff before death → revives at 30% HP, consumes buff
  - `astral`: Added to `_get_buff_evasion_bonus()` (+40 EVA) and `_get_buff_defense_bonus()` (+60% mDEF)
  - `statSwap`: `apply_damage_to_player()` swaps which defense stat is used when buff active
  - `dreadnought`: `apply_damage_to_player()` adds 50% of damage taken as temp STR bonus; cleaned up on expire via STAT_BUFF_KEYS
  - Added `{d}` (duration) to message format dict for all new buff messages

### Weakened Debuff Bug Fix + Defense Reduction (Fixed — Step 31, Session 14)
- **Bug**: `enemy_turn()` checked `has_status(state, "weakened")` — this checked the *player's* status list instead of the enemy's. Player debuffs had no effect on enemy damage.
- **Fix**: Changed to `has_status(e, "weakened")` in both physical and debuff attack paths
- **Feature**: Added defense reduction — when enemy has `weakened`, their DEF/mDEF is reduced by 20% in `apply_damage_to_player()` (making player deal ~10-15% more damage depending on enemy defenses)
- **Effect**: "weakened" now reduces enemy ATK damage by 20% AND reduces enemy defense by 20% (matching skill descriptions like "Curse of Frailty: DEF-25%", "Terrifying Presence: ATK-25%", "Terror of the Deep: ATK-30%, DEF-20%")
- All 271 combat tests pass

### Accuracy Stat Implemented (Step 32, Session 14)
- **Symptom**: `self.accuracy` was calculated (50-98 range based on AGI) but never used — dead variable
- **Fix**: Added miss chance check in `player_use_skill()` before damage calculation
  - Miss chance = `(100 - accuracy)%` — ranges from 2% (high AGI) to 50% (extremely low AGI)
  - Formula: `accuracy = min(98, max(50, 90 + agi * 0.5))` (from recalc_stats)
  - `true_strike` skills bypass the check entirely (Arcane Missile already has this)
  - Miss displays "{skill.name} misses!" in the combat log
  - Miss chance is low enough to not feel punishing but gives AGI a real combat value
- All 271 combat tests pass

### Enemy Intent Indicator (Step 33, Session 14)
- **Feature**: Before each player turn, the combat log now shows what the enemy will do next
- **Implementation**:
  - Added `next_enemy_skill` field to `CombatState` — stores pre-selected enemy action
  - Added `_get_enemy_intent_message(skill)` — generates flavor text based on skill type:
    - Physical: "the enemy braces for a strike!"
    - Magic: "eldritch energy crackles in the air!"
    - Debuff: "the enemy prepares a dark technique!"
    - Self-heal: "the enemy channels restorative energy!"
  - Pre-selection happens at end of enemy turn (before player gets control)
  - Also pre-selects at combat start (first intent shown immediately)
  - `enemy_turn()` uses pre-selected skill if available, falls back to random
- **UX**: Players can now plan defensively — see "the enemy prepares a dark technique!" and choose to heal/shield instead of attacking
- All 271 combat tests pass



## Damage Preview on Skill Hover (Step 34 — 2026-03-28)
### Feature: calc_preview_damage()
- Added `calc_preview_damage(state, skill)` to `engine/combat.py` — deterministic damage calculator
- Mirrors `calc_player_damage()` exactly but skips all RNG: no `random.random()` variance, no gamble, no coin flip
- Returns `(base_dmg, final_dmg_after_def)` — raw damage and post-defense damage
- Applies enemy DEF/mDEF, armor pierce, weakened debuff reduction (same formula as `apply_damage_to_enemy`)
- Buff multipliers included: rage, atkCritUp, warpTime, madPower, darkPact, shadowMeld, eclipse, ethereal
- Scaling included: low HP scaling, madness scaling, multihit, execute bonus, luck bonus
- Returns (0, 0) for non-damage skills (buffs, heals, shields)

### UI: Combat Tooltip Damage Preview
- `_draw_skill_tooltip()` in `screens/combat.py` now shows damage preview as last line
- Format: `~{lo}-{hi} dmg (after DEF)` where lo/hi = final_dmg × 0.75/1.25 (±25% range)
- If final_dmg=0 but base_dmg>0 (no enemy context): shows `~{lo}-{hi} raw dmg`
- If both 0 (buff/heal/shield): no extra line shown
- Miss chance intentionally excluded from preview (gameplay surprise)
- C.PARCHMENT_EDGE color for the preview line (matches formula line styling)

### Files Changed
- `engine/combat.py` — added `calc_preview_damage()` (~80 lines after `calc_player_damage`)
- `engine/__init__.py` — added `calc_preview_damage` to re-exports
- `screens/combat.py` — added import, replaced `_draw_skill_tooltip()` with damage preview line


## Split shared.py into Package (Step 35 — 2026-03-28)
### Refactoring: shared.py → shared/ package
- **Before**: single `shared.py` file (987 lines) — constants, asset loading, drawing, textures, glow text, HUD all in one file
- **After**: `shared/` package with 4 modules (937 total lines):
  - `shared/constants.py` (98 lines) — Pure constants: SCREEN_W/H, FPS, directory paths, `class C` (50+ colors), CLASS_COLORS, CLASS_PRIMARY_STAT, CLASS_SPRITE_FILES, PATH_ICON_FILES
  - `shared/assets.py` (273 lines) — `Assets` class: image loading (class sprites, enemy sprites, backgrounds, cursor, stat icons, path icons), font loading (Cinzel Decorative + Cinzel with fallback chain), helper methods (get_background, get_sprite, get_class_sprite)
  - `shared/rendering.py` (533 lines) — All drawing functions (draw_text, draw_text_wrapped, fit_text, draw_text_fitted, draw_bar, draw_panel, draw_ornate_panel, draw_ornate_button, draw_gold_divider, hp_color, mad_color, rarity_color), obsidian texture system (_generate_obsidian_tile + generate_parchment_texture with tiling), glow text system (cached draw_text_with_glow + wrapped/fitted variants), HUD (draw_hud)
  - `shared/__init__.py` (33 lines) — Re-exports everything from submodules + CLASS_ICONS from data
- **Backward compatibility**: `from shared import C, draw_hud, Assets, ...` all work unchanged
- **Zero screen file changes**: all 17 screen files + pygame_game.py import from shared with no modifications
- ASSETS_DIR/FONTS_DIR paths updated: `os.path.dirname(os.path.dirname(__file__))` to go up one level from shared/ to project root
- **Verification**: all 22 .py files compile clean, AST analysis confirms all definitions present and re-exported

### Files Changed
- `shared.py` → deleted (replaced by package)
- `shared/__init__.py` — new (re-export hub)
- `shared/constants.py` — new
- `shared/assets.py` — new
- `shared/rendering.py` — new
- All screen files — unchanged (backward compatible)



## Events/Traps/Narratives to JSON (Step 36 — 2026-03-28)
### Content Externalization
- **Before**: All event/trap/narrative/path data hardcoded in Python dicts/lists inside `data/events.py` and `data/narratives.py`
- **After**: Data lives in `data/json/*.json` files, Python modules are thin loaders
- **New files**:
  - `data/json/events.json` — 6 floor events (title, icon, text, outcomes with effect string identifiers)
  - `data/json/traps.json` — 3 traps (name, desc, outcomes with chance/dmg_pct/madness)
  - `data/json/narratives.json` — 20 floor narrative strings (one per floor)
  - `data/json/paths.json` — 10 path templates (type, icon, name, desc, desc2, hint, weight)
- **Updated files**:
  - `data/events.py` — replaced 65 lines of hardcoded dicts with 5-line JSON loader using `_load_json()`
  - `data/narratives.py` — replaced 50 lines of hardcoded lists with 5-line JSON loader
- **Unchanged**: `engine/world.py` — `resolve_event()` and `resolve_trap()` use effect strings as identifiers, no changes needed
- `data/__init__.py` — unchanged (EVENTS, TRAPS, FLOOR_NARRATIVES, PATH_TEMPLATES still re-exported from same modules)
- **Benefit**: Adding new events/traps/narratives = edit a JSON file, no Python compilation needed
- **Runtime verified**: all 4 JSON files load correctly, structure matches engine expectations

### Files Changed
- `data/events.py` — rewritten (hardcoded dicts → JSON loader)
- `data/narratives.py` — rewritten (hardcoded lists → JSON loader)
- `data/json/events.json` — new
- `data/json/traps.json` — new
- `data/json/narratives.json` — new
- `data/json/paths.json` — new

## Class Select Overhaul Details (Step 10)
- Redesigned from all-5-at-once to one-class-per-page
- Layout: 400×400 sprite (left), info panel (right)
- Right panel: class name → description → stats → starting abilities (lv1) → future abilities (top 3 by power) → Choose button
- Hover tooltip: damage formula shown in popup above the ability button
- Navigation: Left/Right arrow keys, page indicator "1/5"

## Victory Animation (Step 40 — Session 14, 2026-03-28, Fixed 21:42)
### 3-Phase End-of-Combat Animation + Smooth Fade-Out
Replaces the instant screen switch on combat win with a satisfying animation sequence.

**Phase 1 — HP Drain** (~1s):
- Enemy HP bar drains from max_hp → 0 with accelerating speed (150→700 HP/s)
- Starts SLOW (watching HP tick down), accelerates as it approaches zero
- Red pulsing tint on enemy sprite (sin wave, alpha 40-80)
- Screen shake on trigger (intensity=12, 0.5s)
- Damage numbers fly off randomly (yellow/crimson/bone, ~0.25/frame chance)

**Phase 2 — Disintegration** (~2s):
- Enemy sprite split into 8×6px fragments (vertical strips × horizontal chunks)
- Each fragment: outward velocity from center, upward bias, gravity, random rotation
- Fragments fade over 1.2s, fall under gravity (80-150 px/s²)
- Eldritch energy burst from center: 60 particles (gold/purple/amber, size 2-6)
- Sharp burst: 30 white spark particles (fast, short-lived 0.3-0.8s)
- Ongoing wisps during disintegration (gold/purple, 0.2/frame chance)

**Phase 3 — Dramatic Pause** (~1.8s):
- "D E F E A T E D" fades in (heading font, gold parchment color, alpha = timer×500)
- Growing gold underline divider (width = timer×300, max 300px)
- Combat log panel replaced with victory narrative (different for boss vs regular)
- Boss: "The Spiral collapses. Hastur screams as reality reasserts itself."
- Regular: "The creature dissolves into shadow. The air grows still."
- Fading ghost of enemy sprite (alpha 60, fades over 0.5s)
- Final golden particles drift upward

**Phase 4 — Fade Out** (1.0s):
- Smooth fade-to-black overlay (alpha 0→255 over 1s)
- "DEFEATED" text and gold divider remain visible during fade
- Screen switch to combat_result/levelup happens AFTER fade completes
- Avoids jarring double-fade (victory fade + global screen transition fade)

**Bug Fix (21:42)**:
- **Root cause**: `_start_victory_animation()` set `_victory_hp_display = float(c.enemy.hp)` — but enemy HP was already ≤0 from the killing blow, so the HP drain phase instantly skipped
- **Fix**: Changed to `float(c.enemy.max_hp)` so drain always starts from full HP
- **Drain speed formula fix**: Old formula `(1.0 - x/(x+1)) * 400` was always 0, making speed constant 600. New formula uses true fraction for smooth acceleration 150→700 HP/s
- **Added fade_out phase**: New 1.0s smooth fade-to-black. Old code called `_finish_victory()` directly at end of dramatic_pause, causing instant screen switch

**Implementation Details**:
- State machine: `self._victory_state` (None → "hp_drain" → "disintegrate" → "dramatic_pause" → "fade_out" → done)
- Input fully blocked during all phases (`handle_event` returns early)
- UI hidden: skills, commands, status icons all hidden when `_victory_state` is set
- `_finish_victory()` guarded against double-call (sets `_victory_state = None` first)
- `s.combat` preserved until `_finish_victory()` so draw can read enemy data
- Fragments use sprite pixel sampling with alpha < 20 skip (transparent pixels)
- `import math` added for `math.cos`/`math.sin` in particle burst


## Refactoring (Session 15 — 2026-03-29)

### data/classes.py Split
- Old: `data/classes.py` (74 KB, 308 lines, 201 skills in one dict)
- New: `data/classes/` package (5 per-class files + `__init__.py`)
  - `data/classes/scholar.py` — 41 skills
  - `data/classes/brute.py` — 40 skills
  - `data/classes/warden.py` — 40 skills
  - `data/classes/shadowblade.py` — 40 skills
  - `data/classes/mad_prophet.py` — 40 skills
  - `data/classes/__init__.py` — re-exports CLASSES dict
- Extraction method: `repr()` on each class dict — lossless, byte-identical
- `data/__init__.py` unchanged (`from data.classes import CLASSES` resolves to package)

### engine/combat.py Split
- Old: `engine/combat.py` (1,275 lines, 47 KB)
- New structure:
  - `engine/items.py` (83 lines) — `determine_rarity()`, `generate_item()`
  - `engine/skills.py` (525 lines) — handler registries (HEAL_HANDLERS, SHIELD_HANDLERS, BUFF_HANDLERS) + `player_use_skill()` dispatch
  - `engine/combat.py` (692 lines) — damage calc, status effects, enemy AI, combat init
- Circular dep solution: `player_use_skill()` uses lazy import `from engine.combat import calc_player_damage, apply_damage_to_enemy` inside function body
- `has_status` and `apply_status` duplicated in skills.py (both are 1-5 lines, pure logic)
- `engine/__init__.py` re-exports from all files — no screen imports changed
- `engine/world.py` updated to import `generate_item` from `engine.items`
- `tests/test_combat.py` updated: split imports across 3 modules

### Code Deduplication (Session 15 — 2026-03-29)
- `_base_damage(state, skill)` extracted to engine/combat.py — shared base damage calculation used by both `calc_player_damage` (variance path) and `calc_preview_damage` (deterministic path)
- `has_status()` and `apply_status()` moved to engine/models.py — single definition, imported by combat.py and skills.py. Eliminates circular dep workaround and 3x duplication.
- combat.py reduced from 692 → 614 lines
- Net -77 lines across codebase

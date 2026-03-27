# Visual Overhaul Roadmap

## Status: ✅ COMPLETE + Code Refactoring
Last updated: 2026-03-28 06:08

## Workflow
**ONE task per prompt. Save code + roadmap + memory after each step.**

## Steps

### ✅ Step 0: Asset download + roadmap creation
### ✅ Step 1: Fullscreen toggle (F11 + button)
### ✅ Step 2: Title screen text/button overlap fix
### ✅ Step 3: Combat enemy sprite repositioning
### ✅ Step 4: Font/text box sizing fixes
- `fit_text()` + `draw_text_fitted()` helpers for pixel-width truncation
- Fixed shop, inventory, class select, combat log/skills text overflow

### ✅ Step 5: Additional visual polish — COMPLETE
- Hover effects on ALL interactive screens
- Ornate panels, gold dividers, styled buttons
- 18 image assets verified present

### ✅ Step 6: Font replacement (Session 2)
- Replaced Nosifer → Cinzel Decorative (Victorian/occult serif)
- Cinzel.ttf for body/UI text
- Removed enemy type/ATK/DEF labels from combat
- Fixed loot/event hover overlap (bigger buttons, more spacing)
- Increased explore path box sizes (500→600px wide, 50→56px tall)

### ✅ Step 7: Stat Icons (Session 3)
- Downloaded 5 stat icons (INT/STR/AGI/WIS/LUCK)
- Background removal + resize to 32/48px
- Icons on stats screen (48px), combat skills (32px), level-up (32px)
- STAT_ICONS mapping in game_data.py

### ✅ Step 8: Icon Size & BG Fix (Session 4)
- Increased sizes: stats screen 48→64px, combat/levelup 32→48px
- Fixed Intelligence, Agility, Wisdom background removal (non-white bgs)
- Regenerated all icons at 32/48/64px

### ✅ Step 9: New Stat Icons + Asset Refresh (Session 5 — 2026-03-26)
- User provided 5 new stat icons (1024×1024 RGBA, backgrounds already removed)
- Generated 32/36/48/64px variants from source `_F.png` files
- Fixed combat skill button icon overflow: 48px → 36px (fits 44px-tall buttons)
- Fixed level-up screen icon overflow: 48px → 36px (fits 40-50px-tall buttons)
- Stats screen keeps 64px icons
- 16 base image assets re-downloaded and verified
- Exploration path icons pending (user's next batch)

### ✅ Step 10: Class Selection Overhaul (Session 6 — 2026-03-26)
- Redesigned from all-5-at-once list to one-class-per-page layout
- Large 400×400 class sprite on the left side
- Right panel: class name, description, base stats with color coding
- Starting abilities (lv1) shown with name, description, and ornate button
- Hover over any ability shows damage formula in a popup tooltip
- "Abilities Await" section shows top 3 future abilities (sorted by power)
- Left/Right arrow keys to navigate between classes
- "Choose" button to confirm selection
- Primary stat icon (48px) next to class name
- All 36 assets downloaded and verified (including Boss_F.png)

### ✅ Step 11: Remove Stat Icons from Combat (Session 6 — 2026-03-26)
- Removed stat icon rendering from combat skill buttons
- Increased label text width (was btn.w-64, now btn.w-20) to fill the space
- Level-up and stats screens keep their stat icons unchanged

### ✅ Step 12: Parchment Text Box Overhaul (Session 7 — 2026-03-27)
- All in-game content panels converted from dark purple to aged parchment texture
- Procedural texture generator: warm beige base, paper grain noise, aged spots, vignette edges
- Ornate gold frame borders with corner diamond ornaments on all panels
- Ink-colored text (dark brown) replaces bone/white on parchment backgrounds
- `draw_text_with_glow()` — subtle warm glow/shadow behind all text for readability
- `draw_text_wrapped_glow()` and `draw_text_fitted_glow()` — wrapped/fitted variants
- `draw_parchment_panel()` — new panel renderer with texture + gold frame
- `draw_ornate_button()` — parchment-filled buttons with glow text
- All 14+ screens updated: Explore, Combat, Inventory, Shop, Rest, Loot, Event, Trap, CombatResult, LevelUp, GameOver, Victory, Stats, Save/Load, ClassSelect
- TitleScreen kept dark (dramatic landing page), HUD kept dark (overlay)
- Text colors: C.INK (45,25,10), C.PARCHMENT_EDGE (90,65,35), C.INK_LIGHT (80,55,25)
- Cached parchment textures by size for performance

### ✅ Step 13: Asset Restore + Spacing Fix (Session 8 — 2026-03-27)
- Restored all 36 image assets (class sprites, enemy sprites, stat icons, backgrounds)
- Generated missing `transparent-Boss.png` from `Boss_F.png`
- Downloaded Cinzel + Cinzel Decorative fonts (Google Fonts, static TTF)
- Generated all stat icon size variants: 32/36/48/64px from `_F.png` sources (20 files)
- Fixed Game Over screen: title overlap with divider (y=50→40, divider 110→120, panel 200→220, stats 215→235, buttons 440→460)
- Fixed Explore screen: increased gap between narrative panel and path choices (start_y 340→350, text 318→325)
- Fixed Shop screen: divider/items gap (y 100→102, items 115→125)
- Fixed Event screen: result text spacing (400→425, loot 430→458, continue 470→498)
- Fixed Loot screen: stat text inside buttons respects button bounds
- Verified: 35/35 expected assets present, 2/2 fonts loaded, all code compiles clean

### ✅ Step 21: Fix Combat → Inventory/Save Bug (Session 11 — 2026-03-28)
- Bug: Opening inventory or save from combat immediately left combat, losing all combat state
- Root cause: InventoryScreen defaulted `prev_screen = "explore"`, SaveScreen hardcoded "explore" return
- Fix: InventoryScreen now tracks `self.game._current_screen_name` and checks combat state
- Fix: SaveScreen now tracks where it was opened from and uses `_get_return_screen()` helper
- Save/Load from combat now correctly returns to combat screen after closing

### ✅ Step 22: Refactor player_use_skill() into Handler Functions (Session 11 — 2026-03-28)
- Extracted 300-line if/elif block into three handler modules:
  - `_handle_self_heal()` — 15 heal types via HEAL_HANDLERS registry (calc_fn + message template)
  - `_handle_self_shield()` — 10 shield types via SHIELD_HANDLERS registry
  - `_handle_self_buff()` — 23 buff types via BUFF_HANDLERS registry + _BUFF_MESSAGES
- Each handler is a small function: takes (state, skill), returns effect-specific data
- `player_use_skill()` reduced from ~300 lines to ~30 lines of dispatch
- Adding a new skill type = one function + one registry entry (no touching the main function)
- All 48 existing skill behaviors preserved exactly (heal, shield, buff handlers)
- Damage-dealing path unchanged

### ✅ Step 23: Cache draw_text_with_glow() — Pre-render Glow Surfaces (Session 11 — 2026-03-28)
- Problem: Each `draw_text_with_glow()` call did ~25 `font.render()` calls (8 glow layers + main)
- Fix: `_render_glow_surface()` pre-composites all glow offsets into one RGBA surface
- Cache keyed by (text, font_id, color, glow_color, glow_radius) → (glow_surf, main_surf, ...)
- Cache hit: 2 blits instead of 25 font.render() calls (12x reduction in render work)
- Cache limited to 4096 entries, evicts 25% oldest on overflow
- `draw_text_wrapped_glow()` and `draw_text_fitted_glow()` automatically benefit (they call the cached version per line)
- Huge performance win on screens with lots of text (inventory, class select, shop)

### Pending
- #10: Add automated combat simulation tests
- #11: Split `pygame_game.py` screens into separate modules
- #12: Improve texture caching (atlas or tile-based approach)
- #9: Cache `draw_text_with_glow()` — pre-render glow surfaces per unique string+font+color
- #10: Add automated combat simulation tests
- #11: Split `pygame_game.py` screens into separate modules
- #12: Improve texture caching (atlas or tile-based approach)
- Further text spacing polish if needed (exploration, equipment, general cleanup)

### ✅ Step 14: Exploration Path Icons + Two-Line Descriptions (Session 9 — 2026-03-27)
- Added 6 new path choice icons: Enemy_Ahead_F.png, Boss_Ahead_F.png, Shop_Ahead_F.png, Item_Ahead.png, Rest_Ahead_F.jfif, Decision_Ahead.png
- PATH_ICON_FILES mapping in pygame_game.py: combat→Enemy, shop→Shop, rest→Rest, loot→Item, event/trap→Decision, boss→Boss
- All 6 icons loaded at 64×64 in Assets.load() as `path_{type}` keys
- PATH_TEMPLATES updated with `desc2` field — two-line descriptions for each path (10 templates)
- ExploreScreen redesigned: buttons 600×56 → 620×80, spacing 68→92px
- Each path button now shows: 64px icon (left) + path name (line 1, body font, INK) + elaborated description (line 2, small font, INK_LIGHT)
- draw_ornate_button used for background, icon + text drawn on top
- 41 total image assets now (36 original + 6 new path icons - 1 overlap = 41 unique)

### ✅ Step 15: Side-by-Side Path Layout + Bigger Icons (Session 9 — 2026-03-27)
- Path icons scaled from 64×64 to 150×150
- Layout changed from stacked vertical to side-by-side (left/right cards)
- Each card: 560×260, icon centered on top, name + wrapped description below
- "Choose your path:" uses title_sm font for bolder header
- Description text word-wrapped for readability

### ✅ Step 16: Luck Icon Fix + Card Rendering Cleanup (Session 9 — 2026-03-27)
- Replaced Luck_Icon_F.png with correct version from user
- Regenerated all luck icon size variants (32/36/48/64)
- Path cards use draw_parchment_panel directly (no draw_ornate_button with empty text)
- Explicit gold/yellow border on hover, separate glow layer

### ✅ Step 17: Code Refactoring — Package Split (Session 10 — 2026-03-28)
- Split `game_data.py` (650 lines) → `data/` package (6 files):
  - `constants.py` (45 lines) — MAX_ACTIVE_SKILLS, sprite/icon mappings
  - `classes.py` (308 lines) — 5 classes + ~40 skills each
  - `enemies.py` (86 lines) — enemy pool + boss
  - `items.py` (65 lines) — rarity, prefixes, equipment templates
  - `events.py` (97 lines) — floor events + traps
  - `narratives.py` (56 lines) — floor stories + path templates
- Split `game_engine.py` (1361 lines) → `engine/` package (3 files):
  - `models.py` (372 lines) — Item, Skill, StatusEffect, Enemy, GameState
  - `combat.py` (823 lines) — damage calc, item gen, status effects
  - `world.py` (175 lines) — floor progression, events, shop
- Both packages use `__init__.py` for backward-compatible re-exports
- `pygame_game.py` kept as single file (splitting UI = high risk, low reward)
- Removed `main.py` (depended on nonexistent `ui` module)
- Removed unused imports from `pygame_game.py`: ENEMIES, PATH_TEMPLATES, get_floor_narrative

### ✅ Step 18: ClassSelectScreen Crash Fix (Session 10 — 2026-03-28)
- Fixed AttributeError: `ability_btns` and `future_btns` not initialized in `__init__`
- These lists were created in `draw()` but accessed in `handle_event()` before first draw
- Added `self.ability_btns = []` and `self.future_btns = []` to `__init__`

### ✅ Step 19: 38 Broken Buff Types Fixed (Session 10 — 2026-03-28)
- Buff system audit: 67 buff types defined in skills, only 13 had working logic
- Added `_get_buff_defense_bonus(state, is_phys)` — handles 11 DEF/mDEF buffs:
  thoughtform, ironSkin, chant, innerFire, mDefUp, wardAura, hallowed, fortress, bulwark, umbralAegis, dreamShell
- Added `_get_buff_evasion_bonus(state)` — handles 5 EVA buffs:
  smokeScreen, dreamVeil, evasionUp, dreamShell, umbralAegis
- `apply_damage_to_player()` now handles:
  - EVA buff bonuses (stacking with base evasion stat)
  - DEF/mDEF buff bonuses (percentage increase to damage reduction)
  - divineInterv: nullify N attacks (decrement stacks on proc)
  - ethereal: invulnerable while buff active
  - flicker: 50% dodge per stack (decrement on proc)
  - mirrorImg: 30% damage reduction
  - undyingPact: can't die while active (like undying)
  - finalStand: invulnerable while active
  - bloodAura: 10% lifesteal on damage taken
  - retribAura: reflect 30% damage back to enemy
- `calc_player_damage()`: ethereal gives 2.5x damage, consumed after attack
- `tick_player_buffs()`: added regen5 (5% HP/turn), calmMind (-3 MAD/turn)
- Full integration test suite passed

### ✅ Step 20: Madness-Reducing Skills Fixed (Session 10 — 2026-03-28)
- Bug: buff_duration=0 skills fell through to generic handler, stored buff as 0,
  then tick_player_buffs decremented to -1 before effect could fire
- Fixed 6 skills with instant-effect handlers:
  - Leng's Whisper (Scholar, calmMind): -3 MAD instantly
  - Eldritch Bargain (Prophet): -3 to 3 random stats, +50 gold instantly
  - The Fool's Luck (Prophet, foolLuck): -10 MAD + divineInterv 3 stacks
  - Reality Anchor (Prophet): maps to undying buff for 2 turns
  - The Pallid Mask (Prophet): +50% all stats (temp) + debuff immunity 3 turns
  - Prophet's Resilience (Prophet): +5 MAD, regen 8% for 2 turns
- apply_status_player() now checks immunity buff before applying debuffs
- Added pallidMask to STAT_BUFF_KEYS for proper temp_stats cleanup on expire

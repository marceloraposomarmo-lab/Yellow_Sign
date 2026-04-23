# The King in Yellow — Development Roadmap

> Single living document tracking architecture, completed work, and future plans.

---

## Game Identity

- **Title**: "The King in Yellow — A Lovecraftian Dungeon Crawler"
- **Genre**: Turn-based dungeon crawler / text RPG (inspired by Buried Bornes)
- **Theme**: Lovecraftian mythos, The King in Yellow / Carcosa
- **Engine**: Python + Pygame | 1280x720 (fullscreen via F11)
- **Visual Style**: Dark purples, golds, bone whites — ornate gothic/Victorian aesthetic with procedural parchment textures

---

## Core Architecture

```
pygame_game.py          Game class + HUD + entry point (~237 lines)
save_system.py          JSON save/load (5 slots, version 2)

shared/                 Rendering & constants
  constants.py          Colors (C class), screen dims, paths, icon/sprite mappings
  assets.py             Image/font/cursor loading (Assets class)
  rendering.py          All draw functions, obsidian texture, glow text cache, HUD
  surface_pool.py       SurfacePool (acquire/release) + RenderCache (LRU)
  lighting.py           Full-screen scratch surface pooling
  game_context.py       GameContext service locator (dependency injection)
  logger.py             Logging utilities

engine/                 Game logic
  models.py             Item, Skill (@dataclass), StatusEffect, Enemy, CombatState,
                         GameState (composed: PlayerIdentity + PlayerProgression + CombatBuffs)
  damage.py             _base_damage(), calc_player_damage(), calc_preview_damage(),
                         apply_damage_to_enemy(), apply_damage_to_player(), buff defense/evasion registries
  skills/               Skill handler package
    _types.py           Shared type aliases (LogEntry, HealCalcFn, ShieldCalcFn, BuffApplyFn)
    heal.py             15 heal calculation functions + HEAL_HANDLERS registry + dispatcher
    shield.py           10 shield calculation functions + SHIELD_HANDLERS registry + dispatcher
    buff.py             28 buff handlers + _BUFF_MESSAGES (67 entries) + BUFF_HANDLERS registry + dispatcher
    dispatch.py         player_use_skill() — main skill usage orchestrator
    __init__.py         Re-exports all public symbols
  status_effects.py     Status application, DOT processing, buff ticking/expiry
  items.py              determine_rarity(), generate_item()
  world.py              Floor progression, events, traps, shop

data/                   Game content (data-driven)
  constants.py          60+ named combat/gameplay constants, DAMAGE_BUFF_MULTIPLIERS,
                         DEFENSE_BUFF_TABLE, EVASION_BUFF_TABLE
  classes/              5 class files (scholar, brute, warden, shadowblade, mad_prophet) — ~40 skills each
  enemies.py            Enemy pool + boss definitions
  items.py              Rarity, prefixes, equipment templates
  events.py             JSON loader for floor events
  narratives.py         JSON loader for floor narratives + path templates
  buff_debuff_data.py   All buff/debuff icon/color/desc definitions
  content.py            Misc game content
  json/                 events.json, traps.json, narratives.json, paths.json

screens/                17 screen modules (combat split into package)
  base.py               Screen base class (hover, transitions) — accepts GameContext
  title.py, class_select.py, explore.py, inventory.py, shop.py, rest.py
  combat/               Combat screen package
    __init__.py         Re-exports CombatScreen
    particles.py        ParticleType class + PARTICLE_TYPES registry + factory functions
    screen.py           CombatScreen class — all logic (input, combat, victory, update)
    renderer.py         CombatRendererMixin — all draw methods (tooltips, intent, main draw)
  loot.py, event.py, trap_result.py, combat_result.py, levelup.py
  gameover.py, victory.py, stats.py, save.py

config/                 Settings
  settings.json         User-configurable game settings
  settings_manager.py   Settings loader/saver

tests/                  Test suites (1,156 total tests)
  test_combat.py        19 suites, 271 tests — all classes, damage, buffs, debuffs, AI, boss phases
  test_edge_cases.py    161 tests — madness clamping, HP invariants, buff edge cases, poison stacking
  test_property_based.py 515 tests — Hypothesis-generated random inputs for 10 invariants
  test_save_load.py     104 tests — round-trip integrity, version mismatch, corruption, multi-slot
  test_integration.py   105 tests — combat-progression, floor advance, events, DOT, game loop
  run_all.py            Unified test runner for CI (exit code 0/1)

.github/workflows/
  ci.yml                GitHub Actions CI pipeline (lint + test + coverage)
```

---

## Playable Classes (5)

| Class | Primary Stat | Archetype |
|-------|-------------|-----------|
| Scholar | INT | Magic DPS + debuffs |
| Brute | STR | Physical DPS + rage |
| Warden | WIS | Healer + tank + shields |
| Shadowblade | AGI | Dodge + crit + burst |
| Mad Prophet | LUCK | Chaos + madness + gamble |

Each class has ~40 skills spread across self-heal, self-shield, self-buff, physical, magic, and debuff types.

---

## Combat System

- **Turn-based**: Player picks skill -> enemy acts -> status effects tick -> repeat
- **Damage types**: Physical (ATK-based), Magic (stat-based), Curse, Ultimate
- **Defense**: pDEF/mDEF with percentage reduction (df / (df + 50) formula), armor pierce
- **Crits**: Base crit + buff bonuses (critUp, atkCritUp, permCrit10, eclipse guaranteed crit)
- **Accuracy**: Miss chance = (100 - accuracy)%, based on AGI; true_strike skills bypass
- **Shields & Barriers**: Shield absorbs flat damage, barrier absorbs entire hits
- **Evasion**: Base EVA + buff bonuses (smokeScreen, dreamVeil, evasionUp, etc.)
- **Enemy Intent**: Pre-selected enemy action shown in combat log each turn
- **Damage Preview**: Hover tooltip shows ~dmg range after enemy defense
- **Boss Phases**: 3 phases with escalating ATK at HP thresholds
- **Victory Animation**: 4-phase sequence (HP drain -> disintegration -> dramatic pause -> fade out)
- **Flee**: AGI-based chance, failure adds madness

---

## Buff/Debuff System (67+ buff types)

### Implemented & Working
- **Defensive**: ironSkin, fortress, bulwark, chant, hallowed, wardAura, thoughtform, innerFire, mDefUp, dreamShell, umbralAegis
- **Evasion**: smokeScreen, dreamVeil, evasionUp, dreamShell, umbralAegis, astral
- **Damage**: rage, atkCritUp, warpTime, madPower, darkPact, shadowMeld, eclipse, ethereal, undyingPact
- **Special**: divineInterv, flicker, mirrorImg, undying, undyingPact, finalStand, bloodAura, retribAura, bladeAura, eldritchRebirth, statSwap, dreadnought, immunity
- **Stat Boosts**: permIntWis, permAtk2, permWisStr, permAgiLuk, permAll1, thickSkull, perseverance, shadowBless, randStat2, pallidMask, innerFire, luckyDodge
- **Regen**: regen (8%/turn), regen5 (5%/turn), oath (10%/turn), fadeBlack (5%/turn + EVA)
- **Instant Effects**: calmMind (-3 MAD), eldritchBargain (-3 stats, +50 gold), foolLuck (-10 MAD, divineInterv 3), realityAnchor (undying 2t), prophetRes (regen, +5 MAD)
- **Utility**: resetCds, bloodRitual, madImmune, permCrit10, skipCombat, copyAttack, nimbleFingers, looterInst
- **Debuffs**: burning, poisoned (stacking), bleeding, weakened (ATK -20%, DEF -20%), freezing, petrified, doom (execute at <30% HP on expiry)

### Data-Driven Registries
- `DAMAGE_BUFF_MULTIPLIERS`: buff_key -> damage multiplier (8 entries)
- `DEFENSE_BUFF_TABLE`: buff_key -> (phys_pct, magic_pct) (12 entries)
- `EVASION_BUFF_TABLE`: buff_key -> eva_bonus (6 entries)
- `HEAL_HANDLERS`: 15 heal calculation functions
- `SHIELD_HANDLERS`: 10 shield calculation functions
- `BUFF_HANDLERS`: 36 buff application functions (28 custom + 8 fallback-only)

---

## Visual & UX Features

- Parchment texture panels with ornate gold frames on all 17 screens
- Cinzel Decorative (titles) + Cinzel (body) Victorian fonts
- Cached glow text rendering (12x faster than naive)
- Tile-based obsidian texture caching (256x256 master tile)
- Fade-to-black screen transitions (0.3s each direction)
- Particle effects: dust (explore), eldritch energy (combat), blood splatter (damage)
- Animated hover effects: pulsing glow, gold border, shimmer sweep
- Side-by-side exploration path cards (150x150 icons, two-line descriptions)
- One-class-per-page class selection with ability tooltips
- Stat icons on stats + level-up screens (64px / 36px)
- 6 path choice icons (enemy, boss, shop, item, rest, decision)
- Screen shake on hits, enemy intent indicator, damage preview on hover
- Typewriter text effect, madness vignette overlay, eldritch aura on sprites
- Floating combat damage numbers with Victorian styling
- **Surface pooling**: all per-frame Surface allocations eliminated from draw paths
- **Parchment texture full caching**: zero per-frame allocation for all parchment panels

---

## Completed Improvements

### Phase 1 — Visual Overhaul (Steps 0-49)

| Step | Description | Commit |
|------|-------------|--------|
| 0 | Asset download + roadmap creation | — |
| 1 | Fullscreen toggle (F11 + button) | — |
| 2 | Title screen text/button overlap fix | — |
| 3 | Combat enemy sprite repositioning | — |
| 4 | Font/text box sizing fixes (fit_text helpers) | — |
| 5 | Hover effects on all interactive screens | — |
| 6 | Font replacement (Nosidian -> Cinzel Decorative) | — |
| 7 | Stat icons (INT/STR/AGI/WIS/LUCK, 32/48px) | — |
| 8 | Icon size & background fixes | — |
| 9 | New stat icons + asset refresh (1024x1024 sources) | — |
| 10 | Class selection overhaul (one-class-per-page) | — |
| 11 | Remove stat icons from combat | — |
| 12 | Parchment text box overhaul (all 14+ screens) | — |
| 13 | Asset restore + spacing fixes | — |
| 14 | Exploration path icons + two-line descriptions | — |
| 15 | Side-by-side path layout + bigger icons | — |
| 16 | Luck icon fix + card rendering cleanup | — |
| 17 | Package split (game_data.py -> data/, game_engine.py -> engine/) | — |
| 18 | ClassSelectScreen crash fix | — |
| 19 | 38 broken buff types fixed | — |
| 20 | Madness-reducing skills fixed (6 instant-effect handlers) | — |
| 21 | Fix combat -> inventory/save bug | — |
| 22 | Refactor player_use_skill() into handler functions | — |
| 23 | Cache draw_text_with_glow() (12x faster) | — |
| 24 | Automated combat simulation tests (271 tests) | — |
| 25 | Split pygame_game.py screens into separate modules (21 files) | — |
| 26 | Tile-based obsidian texture caching | — |
| 26b | Fade-to-screen transitions | — |
| 27 | Particle effects (dust, eldritch, blood) | — |
| 28 | Animated hover effects (pulsing glow, shimmer) | — |
| 29 | Fix doom effect (instant-kill at <30% HP on expiry) | — |
| 30 | Implement unimplemented buff types (eldritchRebirth, astral, statSwap, dreadnought) | — |
| 31 | Differentiate weakened debuff (ATK -20%, DEF -20%) | — |
| 32 | Implement accuracy stat | — |
| 33 | Enemy intent indicator | — |
| 35 | Split shared.py into modules (4 files) | — |
| 36 | Move events/traps/narratives to JSON | — |
| 37 | Screen shake on hits (already done) | — |
| 40 | Victory animation (3-phase: drain, disintegrate, pause) | — |
| 41 | Split data/classes.py into per-class package | 3424977 |
| 42 | Split engine/combat.py into 3 modules | 18c9816 |
| 43 | Deduplicate damage calc + move status utilities | b9e885c |
| 44 | Refactor Skill to @dataclass | 9e7d7c7 |
| 45 | Decompose GameState into composed components (v2 saves) | 9e7d7c7 |
| 46 | Replace Warden class sprite | 9d9e432 |
| 47 | Centralize combat constants (60+ named constants) | — |
| 48 | Buff damage multiplier registry | — |
| 49 | Type hints on engine + save system | — |

### Phase 2 — Code Quality (Priority 1-3)

| Priority | Description | Commit |
|----------|-------------|--------|
| P1 | Division-by-zero fixes in damage.py and skills.py | e7e2d1e |
| P1b | Division-by-zero guards in combat.py (boss phase) + heal.py (missing HP) | 83affec |
| P2 | 100% docstring coverage in engine/skills.py (57/57 functions) | — |
| P3 | Automated linting (black, flake8), 302 flake8 warnings resolved | 81092fb |

### Phase 2b — Code Hygiene (2026-04-23)

| # | Improvement | Commit | Description |
|---|-------------|--------|-------------|
| #10 | Division-by-zero guards | 83affec | Guarded 2 remaining unguarded divisions: `engine/combat.py:224` (boss phase HP ratio) and `engine/skills/heal.py:48` (missing HP heal calc). Both now safe when max_hp == 0. |
| #11 | camelCase → snake_case renames | 83affec | Renamed 8 private helper functions to snake_case: `_calc_heal_titanResil` → `_calc_heal_titan_resil`, `_calc_heal_layOnHands` → `_calc_heal_lay_on_hands`, `_calc_heal_darkRegen` → `_calc_heal_dark_regen`, `_calc_heal_hasturEmbrace` → `_calc_heal_hastur_embrace`, `_calc_heal_secondWind` → `_calc_heal_second_wind`, `_calc_heal_nimbleRecov` → `_calc_heal_nimble_recov`, `_shield_fracSan` → `_shield_frac_san`. All registry references updated. |
| #12 | Magic number extraction (30+ constants) | 83affec | Extracted hardcoded numeric literals to named constants in `data/constants.py`: 7 madness cost tiers (`MADNESS_COST_TINY` through `MADNESS_COST_HEAVY`), 6 heal fractions (`HEAL_TITAN_RESIL_FRAC`, `HEAL_DEVOUR_FRAC`, etc.), 6 stat boost tiers (`BUFF_STAT_BOOST_TINY` through `BUFF_STAT_BOOST_MAJOR`), HP cost constants (`BUFF_RAGE_HP_PCT`, `BUFF_WARLORD_HP_PCT`). Applied across `engine/skills/heal.py`, `shield.py`, and `buff.py`. |
| #13 | TypedDict for class data structures | 83affec | Added `ClassSkillData` (40+ fields) and `ClassData` TypedDicts to `engine/models.py`. Provides type safety for the CLASSES dict consumed by `init_from_class()` and `recalc_stats()`. |
| #14 | Game analysis document | 83affec | Generated comprehensive 15-page analysis (`Yellow_Sign_Analysis.docx`) with Lovecraftian color palette styling. Covers all sectors: architecture, combat, classes, visual, content, audio, persistence, testing. Includes prioritized improvement list with impact/difficulty ratings. |

### Phase 3 — Architecture & Performance Improvements (#5-#9)

| # | Improvement | Commit | Description |
|---|-------------|--------|-------------|
| #5 | Dependency Injection / Service Locator | d14ffdc | Created GameContext service locator in shared/game_context.py. Replaced 145 self.game.* references with self.ctx.* across all 17 screen files + CombatRendererMixin. Screens fully decoupled from Game class — unit testing now possible without Pygame. |
| #5-fix | Circular import fix | 311d5e1 | Fixed ImportError from circular dependency between shared and screens packages. Moved ScreenName import behind TYPE_CHECKING guard. |
| #6 | Surface Pooling & Caching | 61b1114 | Eliminated all per-frame pygame.Surface allocations from draw paths across 9 files. Created SurfacePool (acquire/release) for temporary surfaces and RenderCache (LRU) for static outputs. ~21 MB/frame saved in worst case (lighting). |
| #6-fix | Visual bug fix (static particles) | 6c50178 | Fixed parchment symbols frozen at fixed positions by caching only the base texture (tiling + edge glow + vignette) and drawing random symbols per frame. Fixed surface leak in combat glitch_vanish. |
| #7 | Full Parchment Texture Caching | b962f2e | Upgraded to single-level full cache by (width, height). Eliminates per-frame Surface.copy() and redundant symbol drawing for all parchment textures. Zero per-frame allocation on cache hit. |
| #8 | Test Coverage Expansion | f986516 | Expanded from 271 to 1,156 tests (4.3x increase). Added 4 new test suites: test_save_load.py (104), test_edge_cases.py (161), test_property_based.py (515 with Hypothesis), test_integration.py (105). New dependency: hypothesis. |
| #9 | CI/CD Pipeline (GitHub Actions) | 1583f99 | Created .github/workflows/ci.yml with 3-job pipeline: lint (black + flake8), test (Python 3.10/3.11/3.12 matrix), coverage report (PR comment). Concurrency groups cancel redundant runs. pytest-cov added to dev dependencies. |

---

## Systems To Build (Prioritized)

### P1 — Core Combat Expansion

#### Limb Loss System
- [ ] Create `engine/limbs.py` — Limb enum, limb slot definitions, debuff mappings per limb loss
- [ ] Extend `GameState` with `lost_limbs: Dict[str, bool]` + limb-related debuffs
- [ ] Modify `player_use_skill()` to check limb availability before skill use
- [ ] Modify `recalc_stats()` to apply limb-loss debuffs
- [ ] Add combat events that can cause limb loss (specific enemy attacks, traps, curse effects)
- [ ] Add visual representation on stats screen (limb indicators)
- [ ] Save/load compatibility (SAVE_VERSION bump)
- [ ] Tests for limb-loss combat scenarios

#### Madness Overhaul
- [ ] Create `engine/madness.py` — Madness threshold system with escalating effects
- [ ] Define madness tiers: 0-25 (stable), 25-50 (unstable), 50-75 (delirious), 75-100 (madness)
- [ ] Per-tier effects: hallucination chance, random debuff application, stat distortion, forced actions
- [ ] Class-specific madness interactions (Mad Prophet benefits, Scholar knowledge at a cost, etc.)
- [ ] Visual distortion handlers — screen warping, color shifts, text corruption at high madness
- [ ] Slow build/decay mechanics — madness naturally decays between combats
- [ ] Integrate with existing madness vignette overlay (expand thresholds)

#### Curse System
- [ ] Create `engine/curses.py` — Curse types: limb curse, body curse, essence curse
- [ ] Curse application/removal logic with warning signs (1-2 turns before full effect)
- [ ] Counterplay mechanics — specific actions/items that can break curses
- [ ] Integration with doom debuff (expand existing mechanic)
- [ ] Curse-themed skills for Mad Prophet class

### P2 — New Systems

#### Eight-God Religion System
- [ ] Create `data/religion_data.py` — 8 god definitions with names, domains, mechanics
- [ ] Create `engine/religion.py` — Faith tracking, god-specific mechanic handlers, discovery/unlock system
- [ ] Extend `GameState` with `faith: Dict[str, int]` and `patron_god: Optional[str]`
- [ ] Domain-specific bonuses/penalties that interact with existing buff system
- [ ] Shrine events on exploration floors (discover gods, make offerings)
- [ ] UI: religion tab on stats screen

#### Skill Evolution / Mastery
- [ ] Skill experience system — skills level up with use (upgrade damage/healing/shield values)
- [ ] Skill branching — at certain levels, choose between two upgrade paths
- [ ] Visual skill tree on a dedicated screen
- [ ] Persist skill mastery in save system

### P3 — Polish & Content

#### Audio System
- [ ] Create `shared/audio.py` — AudioManager class with SFX/music/ambient layers
- [ ] UI sounds: hover, click, confirm, cancel
- [ ] Combat audio: hit, crit, spell cast, block, enemy death
- [ ] Ambient soundscapes per floor type
- [ ] Dynamic music layers that intensify during combat or at low HP

#### Visual Enhancements
- [ ] Dynamic lighting — HP bars/status icons emit subtle light, flickering torches
- [ ] Vignette effect — darken screen edges at low HP or high madness (expand existing)
- [ ] Screen transitions — context-aware (red for danger, purple for eldritch, slide for explore->combat)
- [ ] Enemy presence effects — boss intimidation aura distorting screen edges
- [ ] Character expression variants — attack, hurt, idle breathing animation
- [ ] Progressive blur — background blurs when modal panels open

#### Content Expansion
- [ ] More enemy variety (currently 6 + boss) — add floor-specific enemies
- [ ] More events and traps (currently 6 events, 3 traps in JSON)
- [ ] Floor-specific narratives and atmosphere changes
- [ ] Item set bonuses
- [ ] Additional class skills at higher levels

### P4 — Technical Debt & Infrastructure

#### Code Refactoring — Completed
- [x] Split `engine/skills.py` (~1,347 lines) into `engine/skills/` package (6 files)
- [x] Split `screens/combat.py` (~1,415 lines) into `screens/combat/` package (4 files)
- [x] Add TypedDict definitions for rarity data, event/trap structures (mypy 0 errors)
- [x] Add input validation in skill handlers (None checks before registry lookup)
- [x] Extract magic numbers to `data/constants.py` (60+ named constants)
- [x] Dependency Injection / Service Locator (GameContext decouples screens from Game)
- [x] Surface pooling & caching (all per-frame allocations eliminated)
- [x] Division-by-zero guards on all HP/max_hp divisions (combat.py, heal.py, damage.py, status_effects.py)
- [x] Rename camelCase helpers to snake_case (8 functions in heal.py and shield.py)
- [x] Extract skill-specific magic numbers to constants (30+ literals: madness costs, heal fractions, stat boosts, HP costs)
- [x] Add TypedDict for class data structures (ClassSkillData, ClassData in engine/models.py)

#### Testing — Completed
- [x] 271 combat tests (all classes, damage, buffs, debuffs, AI, boss phases)
- [x] Edge case tests: 0 HP, 0 stats, buff stacking, poison, doom, boss phases (161 tests)
- [x] Save/load integrity tests: round-trip, version mismatch, corruption, multi-slot (104 tests)
- [x] Property-based testing for combat balance via Hypothesis (515 tests)
- [x] Integration tests: combat-progression, floor advance, events, DOT, game loop (105 tests)
- [ ] Performance benchmarks for particle systems and glow text cache

#### DevOps — Completed
- [x] Pre-commit hooks (black + flake8 via .pre-commit-config.yaml)
- [x] CI/CD pipeline (GitHub Actions: lint + test across Python 3.10/3.11/3.12)
- [x] Coverage reporting (coverage.xml artifact + PR comment via pytest-cov)
- [ ] Consider `ruff` as faster linter replacement

---

## Quality Baseline

- **1,156 tests passing** — combat (271) + edge cases (161) + property-based (515) + save/load (104) + integration (105)
- **0 flake8 errors** (strict checks)
- **0 mypy errors** (all 17 warnings resolved with TypedDict + cast)
- **90+ named constants** in `data/constants.py` (60+ original + 30+ extracted from skill handlers)
- **Pre-commit hooks** configured (black + flake8)
- **CI/CD pipeline** via GitHub Actions (lint + test matrix + coverage)
- **100% docstring coverage** in `engine/skills/` package and `engine/damage.py`
- **All engine functions type-annotated**
- **Save system v2** with backward compatibility
- **Surface pooling** — zero per-frame allocations in draw paths
- **Dependency injection** — screens decoupled from Game via GameContext
- **Zero unguarded divisions** — all HP/max_hp ratios guarded against zero
- **Consistent naming** — all private helpers use snake_case
- **TypedDict coverage** — ClassSkillData, ClassData, EnemyData, RarityData, ItemTemplate, PathTemplate, Event, Trap

---

## Development Guidelines

1. **One system per commit** — keep changes focused and testable
2. **Registry pattern** — new effects = one function + one dict entry (no engine changes)
3. **Data-driven** — new content goes in JSON/Python data files, not engine code
4. **Test before merge** — run `python tests/run_all.py` after every change
5. **Lint before commit** — `black --check` + `flake8` (or use pre-commit hooks)
6. **No breaking save compatibility** — bump SAVE_VERSION when adding new fields
7. **Backward-compatible imports** — `__init__.py` re-exports for all packages
8. **CI runs automatically** — GitHub Actions runs lint + tests on every push/PR to main

---

*Last updated: 2026-04-23 (Improvements #10-#14: division-by-zero guards, camelCase→snake_case, magic number extraction, TypedDict additions, game analysis document)*

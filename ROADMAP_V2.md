# The King in Yellow — Development Roadmap v2

> Living document updated with each commit. Tracks what remains to be built, not what was already done.

---

## Game Identity

- **Title**: "The King in Yellow — A Lovecraftian Dungeon Crawler"
- **Genre**: Turn-based dungeon crawler / text RPG (inspired by Buried Bornes)
- **Theme**: Lovecraftian mythos, The King in Yellow / Carcosa
- **Engine**: Python + Pygame | 1280×720 (fullscreen via F11)
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

engine/                 Game logic
  models.py             Item, Skill (@dataclass), StatusEffect, Enemy, CombatState, GameState (composed: PlayerIdentity + PlayerProgression + CombatBuffs)
  damage.py             _base_damage(), calc_player_damage(), calc_preview_damage(), apply_damage_to_enemy(), apply_damage_to_player(), buff defense/evasion registries
  skills.py             Heal/Shield/Buff handler registries + player_use_skill() dispatcher
  status_effects.py     Status application, DOT processing, buff ticking/expiry
  items.py              determine_rarity(), generate_item()
  world.py              Floor progression, events, traps, shop

data/                   Game content (data-driven)
  constants.py          60+ named combat/gameplay constants, DAMAGE_BUFF_MULTIPLIERS, DEFENSE_BUFF_TABLE, EVASION_BUFF_TABLE
  classes/              5 class files (scholar, brute, warden, shadowblade, mad_prophet) — ~40 skills each
  enemies.py            Enemy pool + boss definitions
  items.py              Rarity, prefixes, equipment templates
  events.py             JSON loader for floor events
  narratives.py         JSON loader for floor narratives + path templates
  buff_debuff_data.py   All buff/debuff icon/color/desc definitions
  content.py            Misc game content
  json/                 events.json, traps.json, narratives.json, paths.json

screens/                17 screen modules (one per screen)
  base.py               Screen base class (hover, transitions)
  title.py, class_select.py, explore.py, combat.py (~900 lines)
  inventory.py, shop.py, rest.py, loot.py, event.py, trap_result.py
  combat_result.py, levelup.py, gameover.py, victory.py, stats.py, save.py

tests/
  test_combat.py        19 suites, 271 assertions — covers all 5 classes, damage, buffs, debuffs, cooldowns, enemy AI, boss phases, flee, items, madness
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

Each class has ~40 skills spread across self-heal, self-shield, self-buff, physical, magic, and debuff types. Skills are loaded from `data/classes/<class>.py` dicts.

---

## Combat System

- **Turn-based**: Player picks skill → enemy acts → status effects tick → repeat
- **Damage types**: Physical (ATK-based), Magic (stat-based), Curse, Ultimate
- **Defense**: pDEF/mDEF with percentage reduction (df / (df + 50) formula), armor pierce
- **Crits**: Base crit + buff bonuses (critUp, atkCritUp, permCrit10, eclipse guaranteed crit)
- **Accuracy**: Miss chance = (100 - accuracy)%, based on AGI; true_strike skills bypass
- **Shields & Barriers**: Shield absorbs flat damage, barrier absorbs entire hits
- **Evasion**: Base EVA + buff bonuses (smokeScreen, dreamVeil, evasionUp, etc.)
- **Enemy Intent**: Pre-selected enemy action shown in combat log each turn
- **Damage Preview**: Hover tooltip shows ~dmg range after enemy defense
- **Boss Phases**: 3 phases with escalating ATK at HP thresholds
- **Victory Animation**: 4-phase sequence (HP drain → disintegration → dramatic pause → fade out)
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
- `DAMAGE_BUFF_MULTIPLIERS`: buff_key → damage multiplier (8 entries)
- `DEFENSE_BUFF_TABLE`: buff_key → (phys_pct, magic_pct) (12 entries)
- `EVASION_BUFF_TABLE`: buff_key → eva_bonus (6 entries)
- `HEAL_HANDLERS`: 15 heal calculation functions
- `SHIELD_HANDLERS`: 10 shield calculation functions
- `BUFF_HANDLERS`: 27 buff application functions
- All registries: add one entry = new effect works, no engine code changes

---

## Visual & UX Features (Already Implemented)

- Parchment texture panels with ornate gold frames on all 17 screens
- Cinzel Decorative (titles) + Cinzel (body) Victorian fonts
- Cached glow text rendering (12x faster than naive)
- Tile-based obsidian texture caching (256×256 master tile)
- Fade-to-black screen transitions (0.3s each direction)
- Particle effects: dust (explore), eldritch energy (combat), blood splatter (damage)
- Animated hover effects: pulsing glow, gold border, shimmer sweep
- Side-by-side exploration path cards (150×150 icons, two-line descriptions)
- One-class-per-page class selection with ability tooltips
- Stat icons on stats + level-up screens (64px / 36px)
- 6 path choice icons (enemy, boss, shop, item, rest, decision)
- Screen shake on hits, enemy intent indicator, damage preview on hover
- Typewriter text effect, madness vignette overlay, eldritch aura on sprites
- Floating combat damage numbers with Victorian styling

---

## Engine/Skills System — Recent Improvements (Commit 61817b6)

### Bug Fixes
- Fixed duplicate `statSwap` key in `_BUFF_MESSAGES` (second silently overwrote first)
- Fixed `_handle_self_heal` not displaying message when h=0 (full_heal, hasturEmbrace)
- Fixed `_buff_rage` never tracking duration in `state.buffs` — rage would never expire
- Fixed `_buff_warlord` not tracking rage duration in `state.buffs`
- Fixed `_shield_madShell` calculating shield AFTER adding madness (inflated shield value)
- Fixed `_base_damage` unreachable code path for self_buff/self_heal/self_shield types producing non-zero damage
- Fixed None-check for `skill.heal_calc`/`skill.shield_calc` before registry lookup (type safety)
- Added rage expiry handling in `tick_player_buffs` — clears `state.rage` flag when buff expires

### Missing Buff Handler Implementations
- Added `_buff_madPower`: +25% DMG +15 MAD side effect (was broken — no handler)
- Added `_buff_darkPact`: +30% DMG, debuffs extended, -15% HP cost (was broken — no handler)
- Added `_buff_warpTime`: reset all cooldowns + +20% DMG (was broken — no handler)
- Added `_buff_fortress`: +80% pDEF/mDEF, +2 barriers (was broken — no handler)
- Added `_buff_undyingPact`: cannot die + +50% ATK (was broken — no handler)
- Added `_buff_eclipse`: guaranteed crit + +30% DMG (was broken — no handler)
- Added `undyingPact` to `DAMAGE_BUFF_MULTIPLIERS` (+50% ATK was not applied)
- Added eclipse guaranteed crit check in `apply_damage_to_enemy`

---

## Systems To Build (Prioritized)

### P1 — Core Combat Expansion

#### Limb Loss System
- [ ] Create `engine/limbs.py` — Limb enum (LEFT_ARM, RIGHT_ARM, LEFT_LEG, RIGHT_LEG), limb slot definitions, debuff mappings per limb loss
- [ ] Extend `GameState` with `lost_limbs: Dict[str, bool]` + limb-related debuffs
- [ ] Modify `player_use_skill()` to check limb availability before skill use (arms = attack skills, legs = evasion skills)
- [ ] Modify `recalc_stats()` to apply limb-loss debuffs (arm loss = -ATK/DEF, leg loss = -EVA/AGI)
- [ ] Add combat events that can cause limb loss (specific enemy attacks, traps, curse effects)
- [ ] Add visual representation on stats screen (limb indicators)
- [ ] Save/load compatibility (SAVE_VERSION bump)
- [ ] Tests for limb-loss combat scenarios

#### Madness Overhaul
- [ ] Create `engine/madness.py` — Madness threshold system with escalating effects
- [ ] Define madness tiers: 0-25 (stable), 25-50 (unstable), 50-75 (delirious), 75-100 (madness)
- [ ] Per-tier effects: hallucination chance, random debuff application, stat distortion, forced actions
- [ ] Class-specific madness interactions (Mad Prophet: benefits from high madness; Scholar: knowledge at a cost; etc.)
- [ ] Visual distortion handlers — screen warping, color shifts, text corruption at high madness
- [ ] Slow build/decay mechanics — madness doesn't just accumulate, it naturally decays between combats
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
- [ ] Screen transitions — context-aware (red for danger, purple for eldritch, slide for explore→combat)
- [ ] Enemy presence effects — boss intimidation aura distorting screen edges
- [ ] Character expression variants — attack, hurt, idle breathing animation
- [ ] Progressive blur — background blurs when modal panels open

#### Content Expansion
- [ ] More enemy variety (currently 6 + boss) — add floor-specific enemies
- [ ] More events and traps (currently 6 events, 3 traps in JSON)
- [ ] Floor-specific narratives and atmosphere changes
- [ ] Item set bonuses
- [ ] Additional class skills at higher levels (classes have ~40 skills, room for more)

### P4 — Technical Debt & Infrastructure

#### Code Refactoring Opportunities
- [ ] Split `engine/skills.py` (~1,200 lines) into `engine/skills/` package (handlers.py, heal_calcs.py, shield_calcs.py, buff_calcs.py, dispatcher.py)
- [ ] Split `screens/combat.py` (~900 lines) into `screens/combat/` package (screen.py, renderer.py, input_handler.py, animations.py)
- [ ] Add TypedDict definitions for rarity data, event/trap structures (fix 17 mypy warnings)
- [ ] Add input validation in skill handlers (None checks before registry lookup with logging)
- [ ] Extract remaining magic numbers to `data/constants.py`

#### Testing Expansion
- [ ] Edge case tests: 0 HP, 0 stats, concurrent status effect stacking
- [ ] Save/load integrity tests
- [ ] Property-based testing for combat balance (hypothesis)
- [ ] Performance benchmarks for particle systems and glow text cache

#### DevOps
- [ ] Pre-commit hooks (black + flake8)
- [ ] CI/CD pipeline for automated test runs
- [ ] Coverage reporting (pytest-cov)
- [ ] Consider `ruff` as faster linter replacement

---

## Quality Baseline

- **271 combat tests passing** — covers all classes, damage, buffs, debuffs, cooldowns, AI, boss phases, flee, items, madness
- **0 flake8 errors** (strict checks)
- **17 mypy warnings** (non-critical Dict typing — recommend TypedDict fix)
- **100% docstring coverage** in `engine/skills.py` and `engine/damage.py`
- **All engine functions type-annotated**
- **Save system v2** with backward compatibility

---

## Development Guidelines

1. **One system per commit** — keep changes focused and testable
2. **Registry pattern** — new effects = one function + one dict entry (no engine changes)
3. **Data-driven** — new content goes in JSON/Python data files, not engine code
4. **Test before merge** — run `python3 tests/test_combat.py` after every change
5. **Lint before commit** — `black engine/ && flake8 engine/ --max-line-length=120`
6. **No breaking save compatibility** — bump SAVE_VERSION when adding new fields
7. **Backward-compatible imports** — `__init__.py` re-exports for all packages

---

*Last updated: 2026-04-19 (Commit 61817b6)*

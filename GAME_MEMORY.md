# GAME PROJECT — Persistent Memory

## Project Overview
- **Title**: "The King in Yellow — A Lovecraftian Dungeon Crawler"
- **Genre**: Dungeon crawler, text RPG (inspired by Buried Bornes)
- **Theme**: Lovecraftian mythos, The King in Yellow / Carcosa
- **Engine**: Pygame (Python)
- **Resolution**: 1280×720 (windowed), supports fullscreen (F11)
- **Palette**: Dark purples, golds, bone whites — ornate gothic style
- **Design reference**: `transparent-Text-box-Sample.png` shows the ornate gold-trim dark panel style

## File Structure
```
game/
├── pygame_game.py        ← Main graphical game (THE FILE WE EDIT)
├── game_data.py          ← All game data (classes, enemies, items, events)
├── game_engine.py        ← Core logic (combat, leveling, items)
├── save_system.py        ← Save/load functionality
├── main.py               ← Terminal-based entry point (separate)
├── ROADMAP.md            ← Visual overhaul progress tracker
├── GAME_MEMORY.md        ← This file
├── images/               ← ALL sprite/background/icon assets (36 files)
├── fonts/                ← Custom fonts (CinzelDecorative, Cinzel)
└── saves/                ← Save files directory (auto-created)
```

## Image Assets (36 files in images/)
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

## Crash Prevention Protocol
1. ONE task per prompt
2. Save code file after EVERY step
3. Save ROADMAP.md after EVERY step
4. Save GAME_MEMORY.md after EVERY step with new learnings
5. Verify syntax with `python3 -c "import py_compile; py_compile.compile(...)"`

## Class Select Overhaul Details (Step 10)
- Redesigned from all-5-at-once to one-class-per-page
- Layout: 400×400 sprite (left), info panel (right)
- Right panel: class name → description → stats → starting abilities (lv1) → future abilities (top 3 by power) → Choose button
- Hover tooltip: damage formula shown in popup above the ability button
- Navigation: Left/Right arrow keys, page indicator "1/5"

# Visual Overhaul Roadmap

## Status: ✅ COMPLETE + Ongoing Polish
Last updated: 2026-03-26 23:58

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

### Pending
- Further text spacing polish if needed (exploration, equipment, general cleanup)

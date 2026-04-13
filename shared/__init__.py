"""
THE KING IN YELLOW — Shared Package
Re-exports everything for backward compatibility. Existing code using
`from shared import ...` continues to work unchanged.

Submodules:
  constants  — Screen dimensions, colors, class mappings
  assets     — Asset loader (images, fonts, cursor)
  rendering  — Drawing helpers, textures, glow text, HUD
"""

# Constants
from shared.constants import (
    SCREEN_W, SCREEN_H, FPS, ASSETS_DIR, FONTS_DIR,
    C, CLASS_COLORS, CLASS_PRIMARY_STAT, CLASS_SPRITE_FILES, PATH_ICON_FILES,
)

# Assets
from shared.assets import Assets

# Rendering — all drawing functions, textures, glow text, HUD
from shared.rendering import (
    draw_text, draw_text_wrapped, fit_text, draw_text_fitted,
    draw_bar, draw_panel, draw_ornate_panel, draw_ornate_button,
    draw_gold_divider, hp_color, mad_color, rarity_color,
    generate_parchment_texture, draw_parchment_panel,
    draw_text_with_glow, draw_text_wrapped_glow, draw_text_fitted_glow,
    draw_hud,
    draw_status_icon, draw_status_icons_row, draw_status_tooltip,
    # Easing functions and animation utilities
    ease_out_quad, ease_in_quad, ease_in_out_quad,
    ease_out_cubic, ease_in_cubic, ease_in_out_cubic,
    ease_out_bounce, lerp, animate_value,
)

# Also re-export data imports that were previously in shared.py's namespace
# (screens import these from shared, not from data directly)
from data import CLASS_ICONS

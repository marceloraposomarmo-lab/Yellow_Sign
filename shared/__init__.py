"""
THE KING IN YELLOW — Shared Package
Re-exports everything for backward compatibility. Existing code using
`from shared import ...` continues to work unchanged.

Submodules:
  constants    — Screen dimensions, colors, class mappings
  assets       — Asset loader (images, fonts, cursor)
  rendering    — Drawing helpers, textures, glow text, HUD
  lighting     — Dynamic lighting system (vignette, torch flicker, status glow)
  logger       — Centralized logging system (replaces print() calls)
  game_context — Service locator / dependency injection for screen decoupling
"""

# Constants
from shared.constants import (
    SCREEN_W,
    SCREEN_H,
    FPS,
    ASSETS_DIR,
    FONTS_DIR,
    C,
    CLASS_COLORS,
    CLASS_PRIMARY_STAT,
    CLASS_SPRITE_FILES,
    PATH_ICON_FILES,
)

# Assets
from shared.assets import Assets

# Rendering — all drawing functions, textures, glow text, HUD
from shared.rendering import (
    draw_text,
    draw_text_wrapped,
    fit_text,
    draw_text_fitted,
    draw_bar,
    draw_panel,
    draw_ornate_panel,
    draw_ornate_button,
    draw_gold_divider,
    hp_color,
    mad_color,
    rarity_color,
    generate_parchment_texture,
    draw_parchment_panel,
    draw_text_with_glow,
    draw_text_wrapped_glow,
    draw_text_fitted_glow,
    draw_hud,
    draw_status_icon,
    draw_status_icons_row,
    draw_status_tooltip,
    # Easing functions and animation utilities
    ease_out_quad,
    ease_in_quad,
    ease_in_out_quad,
    ease_out_cubic,
    ease_in_cubic,
    ease_in_out_cubic,
    ease_out_bounce,
    lerp,
    animate_value,
    # Typewriter text effect
    TypewriterText,
    # Madness vignette and eldritch aura effects
    draw_madness_vignette,
    draw_eldritch_aura,
)

# Dynamic lighting system
from shared.lighting import (
    LightingSystem,
    LightSource,
    TorchFlicker,
    create_combat_lighting,
)

# Logging system — available for all modules
from shared.logger import get_logger, configure_logging, set_level, shutdown as shutdown_logging

# Service locator / dependency injection
from shared.game_context import GameContext

# Audio manager — procedural UI sound effects
from shared.audio import AudioManager

# Also re-export data imports that were previously in shared.py's namespace
# (screens import these from shared, not from data directly)
from data import CLASS_ICONS

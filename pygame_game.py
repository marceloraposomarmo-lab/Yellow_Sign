#!/usr/bin/env python3
"""
THE KING IN YELLOW — Pygame Graphical Edition (Visual Overhaul)
A Lovecraftian Dungeon Crawler with custom art assets.
"""

import os
import sys
import math
import random
import time

os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'
import pygame

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from game_data import (
    CLASSES, ENEMIES, BOSS, ENEMY_SPRITES, CLASS_ICONS, STAT_ICONS,
    EVENTS, TRAPS, RARITY_DATA, FLOOR_NARRATIVES, MAX_ACTIVE_SKILLS,
    PATH_TEMPLATES,
)
from game_engine import (
    GameState, generate_item, start_combat, player_use_skill,
    enemy_turn, process_status_effects, process_player_status_effects,
    tick_player_buffs, check_boss_phase, combat_run_attempt,
    generate_paths, advance_floor, get_floor_narrative,
    resolve_event, resolve_trap, generate_shop, buy_shop_item,
)
from save_system import save_game, load_game, list_saves


# ═══════════════════════════════════════════
# CONSTANTS
# ═══════════════════════════════════════════

SCREEN_W, SCREEN_H = 1280, 720
FPS = 60
ASSETS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "images")
FONTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fonts")

# Lovecraftian color palette
class C:
    VOID       = (26, 10, 46)
    SHADOW     = (45, 27, 78)
    ELDRITCH   = (74, 14, 78)
    YELLOW     = (212, 160, 23)
    AMBER      = (184, 134, 11)
    BONE       = (212, 197, 169)
    CRIMSON    = (139, 0, 0)
    BLOOD      = (196, 30, 58)
    MIST       = (143, 188, 143)
    FROST      = (70, 130, 180)
    EMBER      = (255, 69, 0)
    MADNESS    = (255, 99, 71)
    GOLD       = (241, 196, 15)
    ASH        = (105, 105, 105)
    LIGHTNING  = (0, 191, 255)
    BLACK      = (0, 0, 0)
    WHITE      = (255, 255, 255)
    DARK_BG    = (12, 6, 24)
    PANEL_BG   = (20, 12, 38)
    HP_GREEN   = (46, 204, 113)
    HP_YELLOW  = (243, 156, 18)
    HP_RED     = (231, 76, 60)
    XP_PURPLE  = (155, 89, 182)
    SHIELD_BLUE = (52, 152, 219)
    GOLD_TRIM  = (218, 165, 32)
    GOLD_DIM   = (139, 101, 20)
    # Obsidian / dark stone aesthetic
    OBSIDIAN         = (16, 12, 28)    # Deep dark base
    OBSIDIAN_DARK    = (10, 8, 20)     # Near-black for dark spots
    OBSIDIAN_MID     = (28, 20, 45)    # Mid-range surface color
    OBSIDIAN_EDGE    = (50, 35, 75)    # Edge/crack color (purple)
    OBSIDIAN_GLOW    = (80, 50, 130)   # Faint purple glow in edges
    # Eldritch text colors (on obsidian)
    ELDRITCH_GOLD    = (232, 185, 45)  # Primary text — eldritch gold
    ELDRITCH_GOLD_DIM = (180, 140, 35) # Dimmer gold for secondary text
    ELDRITCH_PURPLE  = (175, 130, 225) # Accent text — eldritch purple
    # Legacy aliases (point to obsidian/eldritch)
    PARCHMENT       = OBSIDIAN
    PARCHMENT_DARK  = OBSIDIAN_MID
    PARCHMENT_EDGE  = ELDRITCH_GOLD
    INK             = ELDRITCH_GOLD
    INK_LIGHT       = ELDRITCH_GOLD_DIM

# Class-specific colors
CLASS_COLORS = {
    "scholar": (180, 100, 230),    # bright violet — was ELDRITCH (too dark)
    "brute": (220, 50, 50),        # bright crimson — was CRIMSON (too dark)
    "warden": C.FROST,
    "shadowblade": C.MIST,
    "mad_prophet": C.MADNESS,
}

# Each class's thematic primary stat (used for icon display, not derived from max)
CLASS_PRIMARY_STAT = {
    "scholar": "int",
    "brute": "str",
    "warden": "wis",
    "shadowblade": "agi",
    "mad_prophet": "luck",
}

# Map class_id → sprite filename
CLASS_SPRITE_FILES = {
    "scholar": "transparent-Int-basedClass.png",
    "brute": "transparent-Strenght-basedClass.png",
    "warden": "wis-character.png",
    "shadowblade": "transparent-Agi-basedClass.png",
    "mad_prophet": "transparent-luck-basedClass.png",
}

# Path type → icon filename for exploration path choices
PATH_ICON_FILES = {
    "combat": "Enemy_Ahead_F.png",
    "shop": "Shop_Ahead_F.png",
    "rest": "Rest_Ahead_F.jfif",
    "loot": "Item_Ahead.png",
    "event": "Decision_Ahead.png",
    "trap": "Decision_Ahead.png",
    "boss": "Boss_Ahead_F.png",
}


# ═══════════════════════════════════════════
# ASSET LOADER
# ═══════════════════════════════════════════

class Assets:
    def __init__(self):
        self.images = {}
        self.fonts = {}
        self.cursor = None
        try:
            self.load()
        except Exception as e:
            print(f"FATAL: Asset loading failed: {e}")
            import traceback
            traceback.print_exc()
            raise

    def load(self):
        # --- Class sprites (for class select & combat) ---
        for class_id, filename in CLASS_SPRITE_FILES.items():
            path = os.path.join(ASSETS_DIR, filename)
            if os.path.exists(path):
                try:
                    img = pygame.image.load(path).convert_alpha()
                    self.images[f"class_{class_id}"] = img
                    # Combat size
                    self.images[f"class_{class_id}_combat"] = pygame.transform.scale(img, (220, 220))
                    # Class select thumbnail
                    self.images[f"class_{class_id}_thumb"] = pygame.transform.scale(img, (90, 90))
                    print(f"  ✓ Class sprite loaded: {class_id} ({img.get_width()}x{img.get_height()})")
                except Exception as e:
                    print(f"  ✗ Warning: failed to load {path}: {e}")
            else:
                print(f"Warning: {path} not found")

        # --- Enemy sprites ---
        sprite_map = {
            "monster1": "transparent-lovecraftian-monster1.png",
            "monster3": "transparent-lovecraftian-monster3.png",
            "monster4": "transparent-lovecraftian-monster4.png",
            "monster5": "transparent-lovecraftian-monster5.png",
            "monster6": "transparent-lovecraftian-monster6.png",
            "monster7": "transparent-lovecraftian-monster7.png",
            "boss": "transparent-Boss.png",
        }
        for key, filename in sprite_map.items():
            path = os.path.join(ASSETS_DIR, filename)
            if os.path.exists(path):
                try:
                    img = pygame.image.load(path).convert_alpha()
                    self.images[key] = img
                    self.images[f"{key}_combat"] = pygame.transform.scale(img, (240, 240))
                    self.images[f"{key}_small"] = pygame.transform.scale(img, (80, 80))
                except Exception as e:
                    print(f"Warning: failed to load {path}: {e}")
            else:
                print(f"Warning: {path} not found")

        # --- Backgrounds ---
        # Dungeon background (used for explore + combat floors 1-19)
        path = os.path.join(ASSETS_DIR, "Dungeon_background.jfif")
        if os.path.exists(path):
            try:
                img = pygame.image.load(path).convert()
                self.images["bg_dungeon"] = pygame.transform.scale(img, (SCREEN_W, SCREEN_H))
            except Exception as e:
                print(f"Warning: failed to load dungeon bg: {e}")
        else:
            print(f"Warning: {path} not found")

        # Game over background
        path = os.path.join(ASSETS_DIR, "Game_Over_Screen.jfif")
        if os.path.exists(path):
            try:
                img = pygame.image.load(path).convert()
                self.images["bg_gameover"] = pygame.transform.scale(img, (SCREEN_W, SCREEN_H))
            except Exception as e:
                print(f"Warning: failed to load gameover bg: {e}")
        else:
            print(f"Warning: {path} not found")

        # Boss background (the old bg_boss if it exists, or reuse dungeon)
        path = os.path.join(ASSETS_DIR, "bg_boss.jpg")
        if os.path.exists(path):
            img = pygame.image.load(path).convert()
            self.images["bg_boss"] = pygame.transform.scale(img, (SCREEN_W, SCREEN_H))
        else:
            self.images["bg_boss"] = self.images.get("bg_dungeon")

        # Title background (the old bg_title if it exists, or reuse dungeon)
        path = os.path.join(ASSETS_DIR, "bg_title.jpg")
        if os.path.exists(path):
            img = pygame.image.load(path).convert()
            self.images["bg_title"] = pygame.transform.scale(img, (SCREEN_W, SCREEN_H))
        else:
            self.images["bg_title"] = self.images.get("bg_dungeon")

        # --- Custom cursor ---
        path = os.path.join(ASSETS_DIR, "transparent-Cursor.png")
        if os.path.exists(path):
            try:
                img = pygame.image.load(path).convert_alpha()
                cursor_scaled = pygame.transform.scale(img, (32, 32))
                cursors = pygame.cursors.Cursor((0, 0), cursor_scaled)
                self.cursor = cursors
            except Exception as e:
                print(f"Warning: failed to load cursor: {e}")

        # --- Text box sample (kept for reference/styling) ---
        path = os.path.join(ASSETS_DIR, "transparent-Text-box-Sample.png")
        if os.path.exists(path):
            try:
                img = pygame.image.load(path).convert_alpha()
                self.images["text_box_sample"] = img
            except Exception as e:
                print(f"Warning: failed to load text box sample: {e}")

        # --- Stat icons (for stats screen + skill buttons) ---
        for stat_key, filename in STAT_ICONS.items():
            for size_suffix, size_px in [("32", 32), ("36", 36), ("48", 48), ("64", 64)]:
                path = os.path.join(ASSETS_DIR, f"{filename}_{size_suffix}.png")
                if os.path.exists(path):
                    try:
                        img = pygame.image.load(path).convert_alpha()
                        self.images[f"stat_{stat_key}_{size_suffix}"] = img
                    except Exception as e:
                        print(f"Warning: failed to load {path}: {e}")

        # --- Path choice icons (for explore screen) ---
        for ptype, filename in PATH_ICON_FILES.items():
            path = os.path.join(ASSETS_DIR, filename)
            if os.path.exists(path):
                try:
                    img = pygame.image.load(path).convert_alpha()
                    self.images[f"path_{ptype}"] = pygame.transform.scale(img, (150, 150))
                    print(f"  ✓ Path icon loaded: {ptype} ({filename})")
                except Exception as e:
                    print(f"Warning: failed to load path icon {path}: {e}")
            else:
                print(f"Warning: path icon not found: {path}")

        # --- Fonts ---
        self._load_fonts()

    def _load_fonts(self):
        # Title font: Cinzel Decorative (ornate Victorian/occult style)
        decor_path = os.path.join(FONTS_DIR, "CinzelDecorative-Regular.ttf")
        decor_bold_path = os.path.join(FONTS_DIR, "CinzelDecorative-Bold.ttf")
        cinzel_path = os.path.join(FONTS_DIR, "Cinzel.ttf")

        # Ensure we always have valid fonts
        fallback_sizes = {"title": 60, "title_sm": 40, "heading": 30,
                          "subheading": 28, "body": 24, "small": 20, "tiny": 17}

        def _test_font(font_obj):
            """Test if a font can actually render text. Returns True if valid."""
            try:
                surf = font_obj.render("Test", True, (255, 255, 255))
                return surf is not None
            except Exception:
                return False

        def _try_load_font(path, size, label):
            """Try loading a font from path. Returns valid font or None."""
            try:
                f = pygame.font.Font(path, size)
                if _test_font(f):
                    return f
                else:
                    print(f"  ✗ Font loaded but cannot render: {path} (size {size})")
                    return None
            except Exception as e:
                print(f"  ✗ Font load error: {path} — {e}")
                return None

        try:
            # Try CinzelDecorative for title/heading
            decor_loaded = False
            if os.path.exists(decor_path):
                f_title = _try_load_font(decor_path, 56, "title")
                f_title_sm = _try_load_font(decor_path, 36, "title_sm")
                f_heading = _try_load_font(decor_path, 28, "heading")
                if f_title and f_title_sm and f_heading:
                    self.fonts["title"] = f_title
                    self.fonts["title_sm"] = f_title_sm
                    self.fonts["heading"] = f_heading
                    decor_loaded = True
                    print(f"  ✓ Decorative font loaded: {decor_path}")

            if not decor_loaded:
                # Try bold variant
                if os.path.exists(decor_bold_path):
                    f_title = _try_load_font(decor_bold_path, 56, "title")
                    if f_title:
                        self.fonts["title"] = f_title
                        self.fonts["title_sm"] = _try_load_font(decor_bold_path, 36, "title_sm") or f_title
                        self.fonts["heading"] = _try_load_font(decor_bold_path, 28, "heading") or f_title
                        decor_loaded = True
                        print(f"  ✓ Decorative bold font loaded: {decor_bold_path}")

            if not decor_loaded:
                print(f"  ✗ No decorative font available, using system fallback")
                self.fonts["title"] = pygame.font.SysFont("serif", 62, bold=True)
                self.fonts["title_sm"] = pygame.font.SysFont("serif", 38, bold=True)
                self.fonts["heading"] = pygame.font.SysFont("serif", 32, bold=True)
        except Exception as e:
            print(f"  ✗ Decorative font section error: {e}")

        try:
            # Try Cinzel for body/UI
            cinzel_loaded = False
            if os.path.exists(cinzel_path):
                f_body = _try_load_font(cinzel_path, 22, "body")
                if f_body:
                    self.fonts["subheading"] = _try_load_font(cinzel_path, 26, "subheading") or f_body
                    self.fonts["body"] = f_body
                    self.fonts["small"] = _try_load_font(cinzel_path, 18, "small") or f_body
                    self.fonts["tiny"] = _try_load_font(cinzel_path, 15, "tiny") or f_body
                    cinzel_loaded = True
                    print(f"  ✓ Body font loaded: {cinzel_path}")

            if not cinzel_loaded:
                print(f"  ✗ No body font available, using system fallback")
                self.fonts["subheading"] = pygame.font.SysFont("georgia", 28, bold=True)
                self.fonts["body"] = pygame.font.SysFont("georgia", 22)
                self.fonts["small"] = pygame.font.SysFont("georgia", 18)
                self.fonts["tiny"] = pygame.font.SysFont("georgia", 15)
        except Exception as e:
            print(f"  ✗ Body font section error: {e}")

        # Final fallback — ensure ALL required fonts exist and can render
        for key, size in fallback_sizes.items():
            if key not in self.fonts or self.fonts[key] is None or not _test_font(self.fonts[key]):
                try:
                    fallback = pygame.font.Font(None, size)
                    if _test_font(fallback):
                        self.fonts[key] = fallback
                        print(f"  ✗ Font '{key}' using emergency default")
                    else:
                        # Absolute last resort
                        self.fonts[key] = pygame.font.SysFont("arial", size)
                        print(f"  ✗ Font '{key}' using arial fallback")
                except Exception:
                    self.fonts[key] = pygame.font.SysFont("arial", size)
                    print(f"  ✗ Font '{key}' using arial fallback (last resort)")

    def get_background(self, floor=1, max_floor=20, screen="explore"):
        """Get appropriate background for current context."""
        if screen == "title":
            bg = self.images.get("bg_title")
        elif screen == "gameover":
            bg = self.images.get("bg_gameover")
        elif screen == "boss" or floor >= max_floor:
            bg = self.images.get("bg_boss")
        else:
            bg = self.images.get("bg_dungeon")
        if not bg:
            return None
        # Darken overlay for readability
        overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        if screen == "gameover":
            overlay.fill((0, 0, 0, 100))
        else:
            overlay.fill((0, 0, 0, 140))
        result = bg.copy()
        result.blit(overlay, (0, 0))
        return result

    def get_sprite(self, enemy_name):
        """Get combat sprite by enemy name."""
        sprite_key = ENEMY_SPRITES.get(enemy_name)
        if sprite_key:
            return self.images.get(f"{sprite_key}_combat")
        return None

    def get_class_sprite(self, class_id, size="combat"):
        """Get class sprite for class select or combat."""
        key = f"class_{class_id}_{size}"
        return self.images.get(key)

    def get_class_combat(self, class_id):
        return self.images.get(f"class_{class_id}_combat")


# ═══════════════════════════════════════════
# DRAWING HELPERS
# ═══════════════════════════════════════════

def draw_text(surface, text, font, color, x, y, align="left"):
    """Draw text with alignment options."""
    rendered = font.render(text, True, color)
    rect = rendered.get_rect()
    if align == "center":
        rect.centerx = x
        rect.top = y
    elif align == "right":
        rect.right = x
        rect.top = y
    else:
        rect.topleft = (x, y)
    surface.blit(rendered, rect)
    return rect

def draw_text_wrapped(surface, text, font, color, x, y, max_width, line_height=None):
    """Draw text with word wrapping. Returns total height drawn."""
    if line_height is None:
        line_height = font.get_linesize()
    words = text.split(' ')
    lines = []
    current_line = ""
    for word in words:
        test = current_line + (" " if current_line else "") + word
        if font.size(test)[0] > max_width:
            if current_line:
                lines.append(current_line)
            current_line = word
        else:
            current_line = test
    if current_line:
        lines.append(current_line)

    for i, line_text in enumerate(lines):
        draw_text(surface, line_text, font, color, x, y + i * line_height)
    return len(lines) * line_height

def fit_text(font, text, max_pixel_width, suffix="…"):
    """Truncate text to fit within max_pixel_width pixels. Uses pixel-width measurement."""
    if font.size(text)[0] <= max_pixel_width:
        return text
    while len(text) > 0 and font.size(text + suffix)[0] > max_pixel_width:
        text = text[:-1]
    return text + suffix if text else suffix

def draw_text_fitted(surface, text, font, color, x, y, max_width, align="left"):
    """Draw text, auto-truncating to fit max_width pixels."""
    fitted = fit_text(font, text, max_width)
    draw_text(surface, fitted, font, color, x, y, align)

def draw_bar(surface, x, y, w, h, current, maximum, fg_color, bg_color=C.SHADOW, border_color=C.ASH):
    """Draw a horizontal bar (HP, XP, etc.)."""
    pygame.draw.rect(surface, border_color, (x - 1, y - 1, w + 2, h + 2), border_radius=3)
    pygame.draw.rect(surface, bg_color, (x, y, w, h), border_radius=2)
    if maximum > 0:
        fill_w = max(0, int(w * min(1, current / maximum)))
        if fill_w > 0:
            pygame.draw.rect(surface, fg_color, (x, y, fill_w, h), border_radius=2)

def draw_panel(surface, x, y, w, h, bg_color=None, border_color=C.GOLD_DIM, border_width=2):
    """Draw an obsidian panel with border."""
    texture = generate_parchment_texture(w, h)
    texture.set_alpha(235)
    surface.blit(texture, (x, y))
    pygame.draw.rect(surface, border_color, (x, y, w, h), border_width, border_radius=4)

def draw_ornate_panel(surface, x, y, w, h, title=None, title_color=None, title_font=None):
    """Draw an obsidian-textured panel with ornate gold frame."""
    draw_parchment_panel(surface, x, y, w, h, title=title, title_font=title_font)

def draw_ornate_button(surface, rect, text, font, hover=False, color=C.INK, disabled=False):
    """Draw a button styled with obsidian and gold trim borders."""
    # Obsidian fill for button
    btn_tex = generate_parchment_texture(rect.w, rect.h)
    btn_tex.set_alpha(240 if not hover else 255)
    surface.blit(btn_tex, (rect.x, rect.y))

    border_color = color if not disabled else C.ASH
    text_color = color if not disabled else C.ASH

    # Gold trim border
    pygame.draw.rect(surface, border_color, rect, 2, border_radius=4)
    # Inner line
    inner_rect = pygame.Rect(rect.x + 3, rect.y + 3, rect.w - 6, rect.h - 6)
    dim_border = tuple(max(0, c - 60) for c in border_color)
    pygame.draw.rect(surface, dim_border, inner_rect, 1, border_radius=3)
    # Text with glow
    draw_text_with_glow(surface, text, font, text_color, rect.centerx,
                         rect.centery - font.get_height() // 2, align="center")
    # Hover glow effect
    if hover:
        glow = pygame.Surface((rect.w + 10, rect.h + 10), pygame.SRCALPHA)
        glow.fill((120, 80, 200, 40))
        surface.blit(glow, (rect.x - 5, rect.y - 5))

def draw_gold_divider(surface, x, y, width):
    """Draw a decorative gold divider line with end caps."""
    mid = width // 2
    pygame.draw.line(surface, C.GOLD_DIM, (x, y), (x + mid - 15, y), 1)
    pygame.draw.line(surface, C.GOLD_DIM, (x + mid + 15, y), (x + width, y), 1)
    # Center diamond
    pygame.draw.polygon(surface, C.GOLD_TRIM, [
        (x + mid, y - 4), (x + mid + 4, y),
        (x + mid, y + 4), (x + mid - 4, y)
    ])
    # End caps
    for ex in [x, x + width]:
        pygame.draw.circle(surface, C.GOLD_DIM, (ex, y), 2)

def hp_color(current, maximum):
    """Get HP bar color based on percentage."""
    if maximum <= 0:
        return C.HP_RED
    pct = current / maximum
    if pct > 0.6: return C.HP_GREEN
    elif pct > 0.3: return C.HP_YELLOW
    else: return C.HP_RED

def mad_color(madness):
    if madness < 30: return C.MIST
    elif madness < 60: return C.HP_YELLOW
    else: return C.HP_RED

def rarity_color(rarity):
    return {1: C.ASH, 2: C.MIST, 3: C.FROST, 4: C.CRIMSON}.get(rarity, C.ASH)


# ═══════════════════════════════════════════
# PARCHMENT TEXTURE & GLOW TEXT
# ═══════════════════════════════════════════

_obsidian_cache = {}

def _draw_yellow_sign(surf, cx, cy, size, alpha=18):
    """Draw a faded Yellow Sign (spiral + cross) — eldritch watermark."""
    s = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
    color = (200, 160, 40, alpha)
    import math
    points = []
    for a in range(0, 360 * 3, 5):
        rad = math.radians(a)
        r = (a / (360 * 3)) * size * 0.8
        px = size + int(r * math.cos(rad))
        py = size + int(r * math.sin(rad))
        points.append((px, py))
    if len(points) > 1:
        pygame.draw.lines(s, color, False, points, 1)
    bar = size // 3
    pygame.draw.line(s, color, (size - bar, size), (size + bar, size), 1)
    pygame.draw.line(s, color, (size, size - bar), (size, size + bar), 1)
    surf.blit(s, (cx - size, cy - size))

def _draw_elder_sign(surf, cx, cy, size, alpha=15):
    """Draw a faded Elder Sign (star in circle)."""
    s = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
    color = (140, 100, 200, alpha)
    import math
    pygame.draw.circle(s, color, (size, size), size - 2, 1)
    pts = []
    for i in range(10):
        rad = math.radians(i * 36 - 90)
        r = (size * 0.8) if i % 2 == 0 else (size * 0.35)
        pts.append((size + int(r * math.cos(rad)), size + int(r * math.sin(rad))))
    pygame.draw.polygon(s, color, pts, 1)
    surf.blit(s, (cx - size, cy - size))

def _draw_alchemical_circle(surf, cx, cy, size, alpha=12):
    """Draw a faded alchemical circle with triangle."""
    s = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
    color = (160, 120, 220, alpha)
    import math
    pygame.draw.circle(s, color, (size, size), size - 2, 1)
    pygame.draw.circle(s, color, (size, size), size - 6, 1)
    pts = []
    for i in range(3):
        rad = math.radians(i * 120 - 90)
        pts.append((size + int((size - 4) * math.cos(rad)), size + int((size - 4) * math.sin(rad))))
    pygame.draw.polygon(s, color, pts, 1)
    for angle in [0, 90, 180, 270]:
        rad = math.radians(angle)
        dx = size + int((size - 2) * math.cos(rad))
        dy = size + int((size - 2) * math.sin(rad))
        pygame.draw.circle(s, color, (dx, dy), 2)
    surf.blit(s, (cx - size, cy - size))

def _draw_crack(surf, x, y, length, alpha=25):
    """Draw a random hairline crack."""
    color = (60, 40, 90, alpha)
    points = [(x, y)]
    cx, cy = x, y
    import math
    angle = random.uniform(0, 360)
    for _ in range(random.randint(3, 7)):
        angle += random.uniform(-40, 40)
        dist = random.randint(length // 3, length)
        rad = math.radians(angle)
        cx += int(dist * math.cos(rad))
        cy += int(dist * math.sin(rad))
        points.append((cx, cy))
    if len(points) > 1:
        pygame.draw.lines(surf, color, False, points, 1)

def generate_parchment_texture(width, height):
    """Generate a procedural obsidian/dark stone texture with eldritch symbols."""
    key = (width, height)
    if key in _obsidian_cache:
        return _obsidian_cache[key]

    try:
        return _generate_obsidian_inner(width, height, key)
    except Exception as e:
        print(f"Warning: texture generation failed ({width}x{height}): {e}")
        # Emergency fallback — solid dark surface
        surf = pygame.Surface((width, height), pygame.SRCALPHA)
        surf.fill((*C.OBSIDIAN, 250))
        _obsidian_cache[key] = surf
        return surf

def _generate_obsidian_inner(width, height, key):
    """Internal obsidian texture generation."""

    surf = pygame.Surface((width, height), pygame.SRCALPHA)
    base = C.OBSIDIAN

    # Fill base — deep obsidian
    surf.fill((*base, 250))

    # Layer 1: Fine crystalline grain noise
    for _ in range(width * height // 3):
        px = random.randint(0, width - 1)
        py = random.randint(0, height - 1)
        v = random.randint(-12, 12)
        r = max(0, min(255, base[0] + v))
        g = max(0, min(255, base[1] + v))
        b = max(0, min(255, base[2] + v))
        surf.set_at((px, py), (r, g, b, 255))

    # Layer 2: Purple/indigo color variation patches
    for _ in range(max(4, width * height // 3000)):
        cx = random.randint(0, width)
        cy = random.randint(0, height)
        radius = random.randint(20, 60)
        spot = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
        for ring in range(radius, 0, -1):
            alpha = int(12 * (1 - ring / radius))
            purple_tint = (random.randint(20, 45), random.randint(10, 30), random.randint(40, 70))
            pygame.draw.circle(spot, (*purple_tint, alpha), (radius, radius), ring)
        surf.blit(spot, (cx - radius, cy - radius))

    # Layer 3: Bright crystalline sparkle points
    for _ in range(max(5, width * height // 2000)):
        sx = random.randint(0, width - 1)
        sy = random.randint(0, height - 1)
        sparkle = random.choice([
            (200, 160, 50, random.randint(15, 35)),   # Gold sparkle
            (140, 100, 190, random.randint(10, 25)),   # Purple sparkle
            (180, 170, 160, random.randint(8, 18)),    # Silver/white
        ])
        sz = random.randint(1, 3)
        pygame.draw.circle(surf, sparkle, (sx, sy), sz)

    # Layer 4: Deep cracks/veins in the stone
    for _ in range(random.randint(3, 7)):
        edge = random.choice(['top', 'bottom', 'left', 'right'])
        if edge == 'top':
            _draw_crack(surf, random.randint(0, width), 0, random.randint(40, 100))
        elif edge == 'bottom':
            _draw_crack(surf, random.randint(0, width), height - 1, random.randint(40, 100))
        elif edge == 'left':
            _draw_crack(surf, 0, random.randint(0, height), random.randint(40, 100))
        else:
            _draw_crack(surf, width - 1, random.randint(0, height), random.randint(40, 100))

    # Layer 5: Eldritch symbols — watermarks
    if width > 200 and height > 150:
        _draw_yellow_sign(surf, random.randint(width // 4, 3 * width // 4),
                         random.randint(height // 4, 3 * height // 4),
                         random.randint(25, 45), alpha=20)
        _draw_elder_sign(surf, random.randint(30, width - 30),
                        random.randint(30, height - 30),
                        random.randint(18, 30), alpha=16)
        if width > 400:
            _draw_alchemical_circle(surf, random.randint(50, width - 50),
                                   random.randint(50, height - 50),
                                   random.randint(20, 35), alpha=14)
        for _ in range(random.randint(2, 4)):
            sx = random.randint(15, width - 15)
            sy = random.randint(15, height - 15)
            if random.random() < 0.5:
                _draw_elder_sign(surf, sx, sy, random.randint(8, 14), alpha=10)
            else:
                _draw_alchemical_circle(surf, sx, sy, random.randint(10, 16), alpha=8)

    # Layer 6: Purple edge glow — eldritch energy seeping through
    glow = pygame.Surface((width, height), pygame.SRCALPHA)
    for i in range(25):
        alpha = int(35 * (1 - i / 25))
        edge_c = C.OBSIDIAN_GLOW
        pygame.draw.line(glow, (*edge_c, alpha), (0, i), (width, i))
        pygame.draw.line(glow, (*edge_c, alpha), (0, height - 1 - i), (width, height - 1 - i))
    for i in range(15):
        alpha = int(25 * (1 - i / 15))
        edge_c = C.OBSIDIAN_GLOW
        pygame.draw.line(glow, (*edge_c, alpha), (i, 0), (i, height))
        pygame.draw.line(glow, (*edge_c, alpha), (width - 1 - i, 0), (width - 1 - i, height))
    surf.blit(glow, (0, 0))

    # Layer 7: Very dark vignette on top
    vig = pygame.Surface((width, height), pygame.SRCALPHA)
    for i in range(15):
        alpha = int(50 * (1 - i / 15))
        pygame.draw.line(vig, (0, 0, 0, alpha), (0, i), (width, i))
        pygame.draw.line(vig, (0, 0, 0, alpha), (0, height - 1 - i), (width, height - 1 - i))
    surf.blit(vig, (0, 0))

    _obsidian_cache[key] = surf
    return surf


def draw_parchment_panel(surface, x, y, w, h, title=None, title_font=None):
    """Draw an obsidian-textured panel with ornate gold frame borders."""
    # Generate and blit obsidian texture
    texture = generate_parchment_texture(w, h)
    surface.blit(texture, (x, y))

    # Outer frame — dark obsidian edge
    pygame.draw.rect(surface, C.OBSIDIAN_EDGE, (x, y, w, h), 3, border_radius=4)
    # Gold trim — outer
    pygame.draw.rect(surface, C.GOLD_TRIM, (x + 4, y + 4, w - 8, h - 8), 2, border_radius=3)
    # Gold trim — inner (dimmer)
    pygame.draw.rect(surface, C.GOLD_DIM, (x + 7, y + 7, w - 14, h - 14), 1, border_radius=2)

    # Corner ornaments (small gold diamonds)
    corners = [(x + 11, y + 11), (x + w - 11, y + 11),
               (x + 11, y + h - 11), (x + w - 11, y + h - 11)]
    for cx, cy in corners:
        pygame.draw.polygon(surface, C.GOLD_TRIM, [
            (cx, cy - 3), (cx + 3, cy), (cx, cy + 3), (cx - 3, cy)
        ])

    # Title bar
    if title and title_font:
        title_w = title_font.size(title)[0] + 30
        tx = x + w // 2 - title_w // 2
        # Small parchment strip behind title
        strip = generate_parchment_texture(title_w, 24)
        strip.set_alpha(200)
        surface.blit(strip, (tx, y - 2))
        pygame.draw.rect(surface, C.GOLD_DIM, (tx, y - 2, title_w, 24), 1, border_radius=2)
        draw_text_with_glow(surface, title, title_font, C.INK,
                            x + w // 2, y + 3, align="center")


def draw_text_with_glow(surface, text, font, color, x, y, align="left",
                         glow_color=None, glow_radius=2):
    """Draw text with an ethereal purple glow/shadow for readability on obsidian."""
    if glow_color is None:
        # Ethereal purple glow for eldritch text
        glow_color = (100, 60, 160)

    # Draw glow layers (offset in 8 directions)
    for dx in range(-glow_radius, glow_radius + 1):
        for dy in range(-glow_radius, glow_radius + 1):
            if dx == 0 and dy == 0:
                continue
            dist = (dx * dx + dy * dy) ** 0.5
            if dist > glow_radius:
                continue
            alpha = max(1, int(60 / (dist + 1)))
            glow_surf = font.render(text, True, glow_color)
            glow_surf.set_alpha(alpha)
            rect = glow_surf.get_rect()
            if align == "center":
                rect.centerx = x + dx
                rect.top = y + dy
            elif align == "right":
                rect.right = x + dx
                rect.top = y + dy
            else:
                rect.topleft = (x + dx, y + dy)
            surface.blit(glow_surf, rect)

    # Draw main text
    rendered = font.render(text, True, color)
    rect = rendered.get_rect()
    if align == "center":
        rect.centerx = x
        rect.top = y
    elif align == "right":
        rect.right = x
        rect.top = y
    else:
        rect.topleft = (x, y)
    surface.blit(rendered, rect)
    return rect


def draw_text_wrapped_glow(surface, text, font, color, x, y, max_width,
                            line_height=None, glow_color=None):
    """Word-wrapped text with glow effect."""
    if line_height is None:
        line_height = font.get_linesize()
    words = text.split(' ')
    lines = []
    current_line = ""
    for word in words:
        test = current_line + (" " if current_line else "") + word
        if font.size(test)[0] > max_width:
            if current_line:
                lines.append(current_line)
            current_line = word
        else:
            current_line = test
    if current_line:
        lines.append(current_line)
    for i, line_text in enumerate(lines):
        draw_text_with_glow(surface, line_text, font, color, x, y + i * line_height,
                             glow_color=glow_color)
    return len(lines) * line_height


def draw_text_fitted_glow(surface, text, font, color, x, y, max_width,
                           align="left", glow_color=None):
    """Fitted (truncated) text with glow effect."""
    fitted = fit_text(font, text, max_width)
    draw_text_with_glow(surface, fitted, font, color, x, y, align, glow_color=glow_color)


# ═══════════════════════════════════════════
# SCREEN BASE CLASS
# ═══════════════════════════════════════════

class Screen:
    def __init__(self, game):
        self.game = game
        self.assets = game.assets
        self.hover_idx = -1  # which button/option is currently hovered (-1 = none)

    def enter(self):
        self.hover_idx = -1

    def handle_event(self, event):
        pass

    def update(self, dt):
        pass

    def draw(self, surface):
        pass

    def update_hover(self, event, buttons):
        """Track hover state from a list of pygame.Rect buttons. Call in handle_event()."""
        if event.type == pygame.MOUSEMOTION:
            self.hover_idx = -1
            for i, btn in enumerate(buttons):
                if btn.collidepoint(event.pos):
                    self.hover_idx = i
                    break
        elif event.type == pygame.WINDOWLEAVE:
            self.hover_idx = -1


# ═══════════════════════════════════════════
# TITLE SCREEN
# ═══════════════════════════════════════════

class TitleScreen(Screen):
    def __init__(self, game):
        super().__init__(game)
        self.particles = []
        self.selected = 0
        self.options = ["New Adventure", "Load Game", "Fullscreen", "Quit"]
        self.buttons = []
        self._init_buttons()

    def _init_buttons(self):
        bw, bh = 320, 50
        cx = SCREEN_W // 2
        start_y = 470
        self.buttons = []
        for i in range(len(self.options)):
            self.buttons.append(pygame.Rect(cx - bw // 2, start_y + i * 55, bw, bh))

    def enter(self):
        self.particles = []
        for _ in range(80):
            self.particles.append({
                "x": random.randint(0, SCREEN_W),
                "y": random.randint(0, SCREEN_H),
                "vx": random.uniform(-0.3, 0.3),
                "vy": random.uniform(-1.5, -0.3),
                "size": random.randint(1, 4),
                "color": random.choice([C.YELLOW, C.ELDRITCH, C.AMBER]),
                "alpha": random.randint(80, 255),
                "life": random.uniform(2, 8),
            })

    def update(self, dt):
        for p in self.particles:
            p["x"] += p["vx"]
            p["y"] += p["vy"]
            p["life"] -= dt
            p["alpha"] = max(0, p["alpha"] - dt * 20)
            if p["life"] <= 0 or p["y"] < -10:
                p["x"] = random.randint(0, SCREEN_W)
                p["y"] = SCREEN_H + random.randint(0, 50)
                p["life"] = random.uniform(2, 8)
                p["alpha"] = random.randint(80, 255)

    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            for i, btn in enumerate(self.buttons):
                if btn.collidepoint(event.pos):
                    self.selected = i
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for i, btn in enumerate(self.buttons):
                if btn.collidepoint(event.pos):
                    self._select(i)
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                self.selected = (self.selected - 1) % len(self.options)
            elif event.key == pygame.K_DOWN:
                self.selected = (self.selected + 1) % len(self.options)
            elif event.key == pygame.K_RETURN:
                self._select(self.selected)

    def _select(self, idx):
        if idx == 0:
            self.game.switch_screen("class_select")
        elif idx == 1:
            self.game.switch_screen("load")
        elif idx == 2:
            self.game.toggle_fullscreen()
        elif idx == 3:
            self.game.running = False

    def draw(self, surface):
        # Particles
        for p in self.particles:
            s = pygame.Surface((p["size"] * 2, p["size"] * 2), pygame.SRCALPHA)
            s.fill((*p["color"], int(p["alpha"])))
            surface.blit(s, (int(p["x"]), int(p["y"])))

        # ── Title & Subtitle (top) ──
        draw_text(surface, "THE KING IN YELLOW", self.assets.fonts["title"],
                  C.YELLOW, SCREEN_W // 2, 40, align="center")
        draw_text(surface, "A Lovecraftian Dungeon Crawler", self.assets.fonts["subheading"],
                  C.BONE, SCREEN_W // 2, 110, align="center")
        draw_gold_divider(surface, SCREEN_W // 2 - 200, 145, 400)

        # ── Character sprite (upper-middle) ──
        char = self.assets.get_class_sprite("scholar")
        if char:
            # Scale down slightly so it fits the tighter layout
            char_scaled = pygame.transform.scale(char, (180, 180))
            cx = SCREEN_W // 2 - char_scaled.get_width() // 2
            surface.blit(char_scaled, (cx, 160))

        # ── Poem (right below sprite) ──
        poem_lines = [
            '"Along the shore the cloud waves break,',
            'The twin suns sink behind the lake,',
            'The shadows lengthen',
            'In Carcosa."',
        ]
        poem_start_y = 355
        for i, line in enumerate(poem_lines):
            color = C.YELLOW if i == 3 else C.BONE
            draw_text(surface, line, self.assets.fonts["small"],
                      color, SCREEN_W // 2, poem_start_y + i * 22, align="center")

        # ── Divider above buttons ──
        draw_gold_divider(surface, SCREEN_W // 2 - 160, 450, 320)

        # ── Buttons (below poem, no overlap) ──
        for i, btn in enumerate(self.buttons):
            label = self.options[i]
            if i == 2:  # Fullscreen button
                state = "[ON]" if self.game.fullscreen else "[OFF]"
                label = f"Fullscreen {state}"
            color = C.MIST if i == 2 else C.PARCHMENT_EDGE
            draw_ornate_button(surface, btn, label, self.assets.fonts["body"],
                               hover=(i == self.selected), color=color)

        # ── Footer ──
        draw_text(surface, "Ph'nglui mglw'nafh Cthulhu R'lyeh wgah'nagl fhtagn.",
                  self.assets.fonts["tiny"], C.ASH, SCREEN_W // 2, SCREEN_H - 28, align="center")


# ═══════════════════════════════════════════
# CLASS SELECT SCREEN
# ═══════════════════════════════════════════
# CLASS SELECT SCREEN (One class per page)
# ═══════════════════════════════════════════

class ClassSelectScreen(Screen):
    def __init__(self, game):
        super().__init__(game)
        self.class_ids = list(CLASSES.keys())
        self.selected = 0
        self.hovered_ability = -1
        self.hovered_future = -1
        self.start_btn = None

    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            mx, my = event.pos
            self.hovered_ability = -1
            self.hovered_future = -1
            if self.start_btn and self.start_btn.collidepoint(mx, my):
                return
            # Check ability hover
            for i, btn in enumerate(self.ability_btns):
                if btn.collidepoint(mx, my):
                    self.hovered_ability = i
                    return
            # Check future ability hover
            for i, btn in enumerate(self.future_btns):
                if btn.collidepoint(mx, my):
                    self.hovered_future = i
                    return
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.start_btn and self.start_btn.collidepoint(event.pos):
                self._pick_class()
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_LEFT:
                self.selected = (self.selected - 1) % len(self.class_ids)
            elif event.key == pygame.K_RIGHT:
                self.selected = (self.selected + 1) % len(self.class_ids)
            elif event.key == pygame.K_RETURN:
                self._pick_class()
            elif event.key == pygame.K_ESCAPE:
                self.game.switch_screen("title")

    def _pick_class(self):
        state = GameState()
        state.init_from_class(self.class_ids[self.selected])
        self.game.state = state
        self.game.switch_screen("explore")

    def _draw_ability_tooltip(self, surface, formula, btn_rect):
        """Draw a tooltip popup above an ability button showing its damage formula."""
        font = self.assets.fonts["tiny"]
        padding = 8
        text_w = font.size(formula)[0] + padding * 2
        tip_w = max(text_w + 20, 180)
        tip_h = 34
        tip_x = btn_rect.x
        tip_y = btn_rect.y - tip_h - 4
        if tip_y < 72:
            tip_y = btn_rect.bottom + 4
        tip_rect = pygame.Rect(tip_x, tip_y, tip_w, tip_h)
        draw_panel(surface, tip_x, tip_y, tip_w, tip_h, None, C.PARCHMENT_EDGE, 1)
        draw_text_with_glow(surface, formula, font, C.PARCHMENT_EDGE, tip_x + padding, tip_y + (tip_h - font.get_height()) // 2)

    def draw(self, surface):
        cid = self.class_ids[self.selected]
        cls = CLASSES[cid]
        color = CLASS_COLORS.get(cid, C.PARCHMENT_EDGE)

        # --- Header with page navigation ---
        draw_text(surface, "CHOOSE YOUR FATE", self.assets.fonts["heading"],
                  C.YELLOW, SCREEN_W // 2, 18, align="center")
        page_text = f"<  {self.selected + 1} / {len(self.class_ids)}  >"
        draw_text(surface, page_text, self.assets.fonts["tiny"],
                  C.ASH, SCREEN_W // 2, 52, align="center")

        # --- Main panel ---
        panel_x, panel_y = 20, 72
        panel_w, panel_h = SCREEN_W - 40, SCREEN_H - 82
        draw_parchment_panel(surface, panel_x, panel_y, panel_w, panel_h)

        # --- Large class sprite (left side) ---
        sprite = self.assets.get_class_sprite(cid)
        if sprite:
            sprite_scaled = pygame.transform.scale(sprite, (400, 400))
            sprite_x = 40
            sprite_y = 90
            surface.blit(sprite_scaled, (sprite_x, sprite_y))

        # --- Right panel layout ---
        rx = 520
        ry = 90

        # Class name with primary stat icon
        primary_stat = CLASS_PRIMARY_STAT.get(cid, max(cls["base_stats"], key=cls["base_stats"].get))
        stat_icon = self.assets.images.get(f"stat_{primary_stat}_48")
        name_text = cls["name"].upper()
        name_w = self.assets.fonts["title_sm"].size(name_text)[0]
        if stat_icon:
            draw_text_with_glow(surface, name_text, self.assets.fonts["title_sm"], color, rx, ry)
            surface.blit(stat_icon, (rx + name_w + 12, ry + 2))
        else:
            draw_text_with_glow(surface, name_text, self.assets.fonts["title_sm"], color, rx, ry)
        ry += 48

        # Description (word-wrapped to 3 lines max)
        draw_text_wrapped_glow(surface, cls["desc"], self.assets.fonts["small"],
                          C.INK, rx, ry, 600, line_height=20)
        ry += 68

        # Stats line
        stat_parts = []
        for stat_name, stat_val in cls["base_stats"].items():
            sc = C.PARCHMENT_EDGE if stat_val >= 14 else (C.CRIMSON if stat_val <= 6 else C.INK)
            stat_parts.append((f"{stat_name.upper()}:{stat_val}", sc))
        stat_parts.append((f"HP:{cls['hp_base']}+{cls['hp_per_level']}/lv", C.HP_GREEN))
        sx = rx
        for text, sc in stat_parts:
            draw_text_with_glow(surface, text, self.assets.fonts["small"], sc, sx, ry)
            sx += self.assets.fonts["small"].size(text)[0] + 14
        ry += 40

        # Section: Starting Abilities
        draw_text_with_glow(surface, "— Starting Abilities —", self.assets.fonts["small"], C.PARCHMENT_EDGE, rx, ry)
        ry += 28

        starting = [sk for sk in cls["skills"] if sk["unlock_lv"] == 1]
        self.ability_btns = []
        for sk in starting:
            btn = pygame.Rect(rx, ry, 280, 44)
            self.ability_btns.append(btn)
            hovered = (len(self.ability_btns) - 1 == self.hovered_ability)
            label = fit_text(self.assets.fonts["small"], sk["name"], 268)
            draw_ornate_button(surface, btn, label, self.assets.fonts["small"],
                               hover=hovered, color=color)
            draw_text_with_glow(surface, sk["desc"], self.assets.fonts["tiny"], C.INK,
                      rx + 290, ry + (44 - self.assets.fonts["tiny"].get_height()) // 2)
            if hovered:
                self._draw_ability_tooltip(surface, sk["formula"], btn)
            ry += 52

        # Section: Future Abilities (top 3 by power)
        ry += 8
        draw_text_with_glow(surface, "— Abilities Await —", self.assets.fonts["small"], C.PARCHMENT_EDGE, rx, ry)
        ry += 28

        future = sorted(
            [sk for sk in cls["skills"] if sk["unlock_lv"] > 1],
            key=lambda s: -s.get("power", 0)
        )[:3]
        self.future_btns = []
        for sk in future:
            btn = pygame.Rect(rx, ry, 280, 36)
            self.future_btns.append(btn)
            hovered = (len(self.future_btns) - 1 == self.hovered_future)
            label = f"Lv{sk['unlock_lv']} — {fit_text(self.assets.fonts['tiny'], sk['name'], 220)}"
            draw_ornate_button(surface, btn, label, self.assets.fonts["tiny"],
                               hover=hovered, color=C.PARCHMENT_EDGE)
            draw_text_with_glow(surface, sk["desc"], self.assets.fonts["tiny"], C.INK_LIGHT,
                      rx + 290, ry + (36 - self.assets.fonts["tiny"].get_height()) // 2)
            if hovered:
                self._draw_ability_tooltip(surface, sk["formula"], btn)
            ry += 42

        # Start button
        self.start_btn = pygame.Rect(rx, 576, 220, 40)
        draw_ornate_button(surface, self.start_btn, "Choose", self.assets.fonts["body"],
                           hover=self.start_btn.collidepoint(pygame.mouse.get_pos()),
                           color=color)

    def _draw_intro(self, surface):
        """Draw the initial overview screen (not used in one-per-page mode, kept for reference)."""
        draw_text(surface, "CHOOSE YOUR FATE", self.assets.fonts["heading"],
                  C.YELLOW, SCREEN_W // 2, 25, align="center")
        draw_text(surface, "Each path leads deeper into madness.", self.assets.fonts["tiny"],
                  C.BONE, SCREEN_W // 2, 60, align="center")
        draw_gold_divider(surface, SCREEN_W // 2 - 200, 78, 400)
        for i, cid in enumerate(self.class_ids):
            cls = CLASSES[cid]
            color = CLASS_COLORS.get(cid, C.ASH)
            card_y = 90 + i * 125
            card_w = SCREEN_W - 80
            is_selected = (i == self.selected)
            if is_selected:
                draw_ornate_panel(surface, 40, card_y, card_w, 115)
            else:
                draw_panel(surface, 40, card_y, card_w, 115, (16, 8, 30), C.ASH, 1)
            sprite = self.assets.get_class_sprite(cid, "thumb")
            if sprite:
                surface.blit(sprite, (52, card_y + 12))


# ═══════════════════════════════════════════
# EXPLORE SCREEN
# ═══════════════════════════════════════════

class ExploreScreen(Screen):
    def __init__(self, game):
        super().__init__(game)
        self.paths = []
        self.path_buttons = []
        self.cmd_buttons = {}
        self.narrative = ""

    def enter(self):
        s = self.game.state
        self.narrative = FLOOR_NARRATIVES[min(s.floor - 1, len(FLOOR_NARRATIVES) - 1)]
        is_boss = s.floor >= s.max_floor
        if is_boss:
            self.paths = []
            start_combat(s, is_boss=True)
            self.game.switch_screen("combat")
            return
        # Only generate new paths if we don't have any (don't regenerate on inventory/stats visit)
        if not self.paths:
            self.paths = generate_paths(s.floor)
        self._build_buttons()

    def _build_buttons(self):
        # Side-by-side layout: left and right cards
        card_w, card_h = 560, 260
        gap = 40
        left_x = SCREEN_W // 2 - card_w - gap // 2
        right_x = SCREEN_W // 2 + gap // 2
        start_y = 340
        self.path_buttons = []
        positions = [(left_x, start_y), (right_x, start_y)]
        for i in range(len(self.paths)):
            if i < len(positions):
                self.path_buttons.append(pygame.Rect(positions[i][0], positions[i][1], card_w, card_h))
            else:
                self.path_buttons.append(pygame.Rect(positions[0][0], start_y, card_w, card_h))

        # Command buttons
        cx = SCREEN_W // 2
        self.cmd_buttons = {
            "inventory": pygame.Rect(cx - 310, SCREEN_H - 70, 120, 40),
            "stats": pygame.Rect(cx - 120, SCREEN_H - 70, 120, 40),
            "save": pygame.Rect(cx + 70, SCREEN_H - 70, 120, 40),
            "menu": pygame.Rect(cx + 260, SCREEN_H - 70, 120, 40),
        }

    def handle_event(self, event):
        # Track hover for all buttons
        all_btns = self.path_buttons + list(self.cmd_buttons.values())
        self.update_hover(event, all_btns)

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for i, btn in enumerate(self.path_buttons):
                if btn.collidepoint(event.pos):
                    self._choose_path(i)
            for name, btn in self.cmd_buttons.items():
                if btn.collidepoint(event.pos):
                    if name == "inventory":
                        self.game.switch_screen("inventory")
                    elif name == "stats":
                        self.game.switch_screen("stats")
                    elif name == "save":
                        self.game.switch_screen("save")
                    elif name == "menu":
                        self.game.switch_screen("title")
        elif event.type == pygame.KEYDOWN:
            if pygame.K_1 <= event.key <= pygame.K_9:
                idx = event.key - pygame.K_1
                if idx < len(self.paths):
                    self._choose_path(idx)
            elif event.key == pygame.K_i:
                self.game.switch_screen("inventory")
            elif event.key == pygame.K_t:
                self.game.switch_screen("stats")
            elif event.key == pygame.K_s:
                self.game.switch_screen("save")

    def _choose_path(self, idx):
        s = self.game.state
        path = self.paths[idx]
        # Clear paths so next room generates fresh ones
        self.paths = []
        s.rooms_explored += 1
        if s.add_madness(2):
            self.game.gameover_msg = "Your mind shatters. The Yellow Sign consumes your last rational thought."
            self.game.switch_screen("gameover")
            return

        ptype = path["type"]
        if ptype == "combat":
            start_combat(s, is_boss=False)
            self.game.switch_screen("combat")
        elif ptype == "event":
            event = random.choice(EVENTS)
            self.game.pending_event = event
            self.game.switch_screen("event")
        elif ptype == "loot":
            self.game.switch_screen("loot")
        elif ptype == "rest":
            self.game.switch_screen("rest")
        elif ptype == "shop":
            items, prices = generate_shop(s)
            self.game.shop_items = items
            self.game.shop_prices = prices
            self.game.shop_sold = [False] * len(items)
            self.game.switch_screen("shop")
        elif ptype == "trap":
            trap = random.choice(TRAPS)
            trap_idx = TRAPS.index(trap)
            msg, game_over = resolve_trap(s, trap_idx)
            self.game.trap_msg = msg
            self.game.trap_name = trap["name"]
            self.game.trap_desc = trap["desc"]
            if game_over:
                self.game.gameover_msg = "The trap claims your life."
                self.game.switch_screen("gameover")
            else:
                self.game.switch_screen("trap_result")

    def draw(self, surface):
        s = self.game.state
        draw_hud(surface, s, self.assets)

        is_boss = s.floor >= s.max_floor

        # Floor info with parchment panel
        panel_w, panel_h = 600, 180
        panel_x = SCREEN_W // 2 - panel_w // 2
        draw_parchment_panel(surface, panel_x, 130, panel_w, panel_h)

        draw_text_wrapped_glow(surface, self.narrative, self.assets.fonts["small"],
                          C.INK, SCREEN_W // 2 - 270, 155, 540, line_height=22)

        # Path choices — side by side cards
        if self.paths:
            for i, (path, btn) in enumerate(zip(self.paths, self.path_buttons)):
                hovered = (i == self.hover_idx)
                ptype = path["type"]

                # Draw parchment card background with hover effect
                draw_parchment_panel(surface, btn.x, btn.y, btn.w, btn.h)
                border_col = C.YELLOW if hovered else C.PARCHMENT_EDGE
                pygame.draw.rect(surface, border_col, btn, 2, border_radius=4)
                if hovered:
                    glow = pygame.Surface((btn.w + 10, btn.h + 10), pygame.SRCALPHA)
                    glow.fill((120, 80, 200, 40))
                    surface.blit(glow, (btn.x - 5, btn.y - 5))

                # Icon on top-center of the card
                icon_key = f"path_{ptype}"
                icon = self.assets.images.get(icon_key)
                icon_size = 150
                icon_x = btn.x + (btn.width - icon_size) // 2
                icon_y = btn.y + 12
                if icon:
                    surface.blit(icon, (icon_x, icon_y))

                # Text area: below the icon, centered
                text_center_x = btn.x + btn.width // 2
                text_max_w = btn.width - 40
                text_top = icon_y + icon_size + 8

                # Line 1: path name
                name_text = path["name"]
                name_font = self.assets.fonts["body"]
                name_text = fit_text(name_font, name_text, text_max_w)
                draw_text_with_glow(surface, name_text, name_font,
                                    C.INK, text_center_x, text_top, align="center")

                # Line 2: elaborated description (wrapped if needed)
                desc_text = path.get("desc2", path["desc"])
                desc_font = self.assets.fonts["small"]
                desc_y = text_top + 24
                draw_text_wrapped_glow(surface, desc_text, desc_font,
                                       C.INK_LIGHT, btn.x + 20, desc_y, text_max_w, line_height=18)

        # Bottom commands
        cmd_names = list(self.cmd_buttons.keys())
        for ci, (name, btn) in enumerate(self.cmd_buttons.items()):
            labels = {"inventory": "Inventory [I]", "stats": "Stats [T]", "save": "Save [S]", "menu": "Menu"}
            draw_ornate_button(surface, btn, labels[name], self.assets.fonts["small"],
                               hover=((len(self.path_buttons) + ci) == self.hover_idx), color=C.PARCHMENT_EDGE)


# ═══════════════════════════════════════════
# COMBAT SCREEN
# ═══════════════════════════════════════════

class CombatScreen(Screen):
    def __init__(self, game):
        super().__init__(game)
        self.skill_buttons = []
        self.cmd_buttons = {}
        self.damage_numbers = []  # [text, x, y, color, timer, vy]
        self.shake_timer = 0
        self.shake_intensity = 0
        self.turn_message = ""
        self.turn_msg_timer = 0

    def enter(self):
        self.damage_numbers = []
        self.shake_timer = 0
        self._build_buttons()
        self.turn_message = ""
        self.turn_msg_timer = 0

    def _build_buttons(self):
        s = self.game.state
        if not s.combat:
            return
        bw, bh = 280, 44
        start_x = 30
        start_y = 460
        cols = 2
        self.skill_buttons = []
        for i, sk in enumerate(s.active_skills):
            col = i % cols
            row = i // cols
            x = start_x + col * (bw + 20)
            y = start_y + row * (bh + 8)
            self.skill_buttons.append(pygame.Rect(x, y, bw, bh))

        # Command buttons below skills
        cmd_y = start_y + ((len(s.active_skills) + 1) // cols) * (bh + 8) + 15
        self.cmd_buttons = {
            "run": pygame.Rect(30, cmd_y, 120, 36),
            "inventory": pygame.Rect(160, cmd_y, 120, 36),
            "save": pygame.Rect(290, cmd_y, 120, 36),
        }

    def add_damage_number(self, text, x, y, color):
        self.damage_numbers.append([text, x, y, color, 1.5, -60])

    def trigger_shake(self, intensity=8, duration=0.3):
        self.shake_intensity = intensity
        self.shake_timer = duration

    def update(self, dt):
        for dn in self.damage_numbers:
            dn[2] += dn[5] * dt
            dn[4] -= dt
        self.damage_numbers = [dn for dn in self.damage_numbers if dn[4] > 0]
        if self.shake_timer > 0:
            self.shake_timer -= dt
        if self.turn_msg_timer > 0:
            self.turn_msg_timer -= dt

    def handle_event(self, event):
        s = self.game.state
        c = s.combat
        if not c:
            return

        # Track hover for all buttons
        all_btns = self.skill_buttons + list(self.cmd_buttons.values())
        self.update_hover(event, all_btns)

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for i, btn in enumerate(self.skill_buttons):
                if btn.collidepoint(event.pos):
                    if i < len(s.active_skills):
                        self._use_skill(i)
            for name, btn in self.cmd_buttons.items():
                if btn.collidepoint(event.pos):
                    if name == "run":
                        self._try_run()
                    elif name == "inventory":
                        self.game.switch_screen("inventory")
                    elif name == "save":
                        self.game.switch_screen("save")
        elif event.type == pygame.KEYDOWN:
            if pygame.K_1 <= event.key <= pygame.K_9:
                idx = event.key - pygame.K_1
                if idx < len(s.active_skills):
                    self._use_skill(idx)
            elif event.key == pygame.K_r:
                self._try_run()
            elif event.key == pygame.K_i:
                self.game.switch_screen("inventory")
            elif event.key == pygame.K_s:
                self.game.switch_screen("save")

    def _use_skill(self, idx):
        s = self.game.state
        c = s.combat
        if not c or c.turn != "player":
            return
        sk = s.active_skills[idx]
        if sk.current_cd > 0:
            self.turn_message = f"{sk.name} is on cooldown!"
            self.turn_msg_timer = 1.5
            return

        logs = player_use_skill(s, idx)
        for text, log_type in logs:
            c.add_log(text, log_type)
            if log_type in ("damage", "crit"):
                color = C.YELLOW if log_type == "crit" else C.BONE
                dmg_val = text.split()[-1] if any(ch.isdigit() for ch in text) else ""
                # Damage number floats above enemy sprite (right side)
                self.add_damage_number(dmg_val, 1120, 200, color)

        phase_logs = check_boss_phase(s)
        for text, log_type in phase_logs:
            c.add_log(text, log_type)

        buff_logs = tick_player_buffs(s)
        for text, log_type in buff_logs:
            c.add_log(text, log_type)

        se_logs = process_status_effects(c.enemy, False, s)
        for text, log_type in se_logs:
            c.add_log(text, log_type)

        if c.enemy.hp <= 0:
            self._end_combat(victory=True)
            return

        c.turn = "enemy"
        self._do_enemy_turn()

    def _do_enemy_turn(self):
        s = self.game.state
        c = s.combat
        if not c:
            return

        logs = enemy_turn(s)
        for text, log_type in logs:
            c.add_log(text, log_type)
            if log_type == "damage":
                self.trigger_shake()
                dmg_val = text.split()[-1] if any(ch.isdigit() for ch in text) else ""
                # Damage number floats above player sprite (left side)
                self.add_damage_number(dmg_val, 140, 250, C.CRIMSON)

        if s.hp <= 0:
            self._end_combat(victory=False)
            return

        se_logs = process_player_status_effects(s)
        for text, log_type in se_logs:
            c.add_log(text, log_type)

        if s.hp <= 0:
            self._end_combat(victory=False)
            return

        for sk in s.active_skills:
            if sk.current_cd > 0:
                sk.current_cd -= 1

        buff_logs = tick_player_buffs(s)
        for text, log_type in buff_logs:
            c.add_log(text, log_type)

        c.turn = "player"
        c.turn_count += 1
        self._build_buttons()

    def _try_run(self):
        s = self.game.state
        c = s.combat
        if not c or c.is_boss:
            self.turn_message = "Cannot flee from the Spiral!"
            self.turn_msg_timer = 1.5
            return
        if combat_run_attempt(s):
            s.combat = None
            advance_floor(s)
            self.game.switch_screen("explore")
        else:
            self.turn_message = "Failed to escape!"
            self.turn_msg_timer = 1.5
            c.turn = "enemy"
            self._do_enemy_turn()

    def _end_combat(self, victory):
        s = self.game.state
        c = s.combat
        if not c:
            return

        if victory:
            s.kills += 1
            xp_g = 12 + s.floor * 4 + (80 if c.is_boss else 0)
            gold_g = 6 + random.randint(0, 8) + s.floor * 2 + (50 if c.is_boss else 0)
            s.xp += xp_g
            s.gold += gold_g
            s.add_madness(-15 if c.is_boss else 3)
            loot = generate_item(s.floor, luck=s.luck)
            leveled = s.check_level_up()

            self.game.combat_result = {
                "victory": True, "xp": xp_g, "gold": gold_g,
                "loot": loot, "is_boss": c.is_boss, "leveled": leveled,
            }
            s.combat = None
            if leveled:
                self.game.switch_screen("levelup")
            else:
                self.game.switch_screen("combat_result")
        else:
            s.combat = None
            self.game.gameover_msg = "Your body crumples. The last thing you see is the Yellow Sign, burning brighter than ever."
            self.game.switch_screen("gameover")

    def _draw_skill_tooltip(self, surface, sk, btn_rect):
        """Draw a popup tooltip above a skill button showing description and formula."""
        font = self.assets.fonts["tiny"]
        padding = 10
        max_w = 380

        # Build tooltip lines
        lines = []
        # Description (word-wrap if needed)
        desc_words = sk.desc.split()
        line = ""
        for w in desc_words:
            test = f"{line} {w}".strip()
            if font.size(test)[0] > max_w - padding * 2:
                lines.append(line)
                line = w
            else:
                line = test
        if line:
            lines.append(line)
        # Formula line
        lines.append(sk.formula)

        line_h = font.get_height() + 3
        tip_w = max_w
        tip_h = padding * 2 + len(lines) * line_h
        tip_x = btn_rect.x
        tip_y = btn_rect.y - tip_h - 6
        if tip_y < 10:
            tip_y = btn_rect.bottom + 6

        # Background + border
        bg = pygame.Surface((tip_w, tip_h), pygame.SRCALPHA)
        bg.fill((10, 8, 20, 230))
        surface.blit(bg, (tip_x, tip_y))
        pygame.draw.rect(surface, C.PARCHMENT_EDGE, (tip_x, tip_y, tip_w, tip_h), 1, border_radius=3)

        for i, l in enumerate(lines):
            color = C.PARCHMENT_EDGE if i == len(lines) - 1 else C.INK
            draw_text_with_glow(surface, l, font, color,
                                tip_x + padding, tip_y + padding + i * line_h)

    def draw(self, surface):
        s = self.game.state
        c = s.combat
        if not c:
            return
        e = c.enemy

        ox, oy = 0, 0
        if self.shake_timer > 0:
            ox = random.randint(-self.shake_intensity, self.shake_intensity)
            oy = random.randint(-self.shake_intensity, self.shake_intensity)

        draw_hud(surface, s, self.assets)

        # --- Enemy info panel (compact nameplate above sprite) ---
        e_hp_pct = max(0, e.hp / e.max_hp * 100)
        panel_w = 495
        panel_h = 75
        sprite_w = 240
        sprite_x = SCREEN_W - sprite_w - 40 + ox
        sprite_y = 202 + oy
        # Panel right-aligned to sprite's right edge (panel wider than sprite)
        panel_x = sprite_x + sprite_w - panel_w
        panel_y = 120
        draw_parchment_panel(surface, panel_x, panel_y, panel_w, panel_h)

        if c.is_boss:
            draw_text_with_glow(surface, "BOSS", self.assets.fonts["tiny"], C.CRIMSON, panel_x + 12, panel_y + 5)
        draw_text_with_glow(surface, e.name, self.assets.fonts["small"], C.PARCHMENT_EDGE, panel_x + 12, panel_y + 22)

        # Enemy HP bar
        draw_bar(surface, panel_x + 12, panel_y + 44, 330, 14, e.hp, e.max_hp,
                 hp_color(e.hp, e.max_hp))
        draw_text_with_glow(surface, f"{e.hp}/{e.max_hp}", self.assets.fonts["tiny"],
                  C.INK, panel_x + 350, panel_y + 44)

        # Enemy statuses (inline next to HP bar)
        est = []
        for st in e.statuses:
            est.append(f"{st.type.upper()}:{st.duration}")
        if e.stunned:
            est.append("STUNNED")
        if est:
            draw_text_with_glow(surface, " ".join(est), self.assets.fonts["tiny"],
                      C.CRIMSON, panel_x + 200, panel_y + 60)

        # --- Enemy sprite (right side, below panel, fully visible) ---
        enemy_sprite = self.assets.get_sprite(e.name)
        if enemy_sprite:
            surface.blit(enemy_sprite, (sprite_x, sprite_y))

        # --- Character sprite (left side) ---
        class_sprite = self.assets.get_class_combat(s.class_id)
        if class_sprite:
            surface.blit(class_sprite, (30 + ox, 250 + oy))

        # --- Combat log (center, parchment panel) ---
        log_x, log_y = 280, 250
        log_w, log_h = 560, 180
        draw_parchment_panel(surface, log_x, log_y, log_w, log_h)
        draw_text_with_glow(surface, "Combat Log", self.assets.fonts["tiny"], C.PARCHMENT_EDGE, log_x + 15, log_y + 8)
        draw_gold_divider(surface, log_x + 15, log_y + 26, log_w - 30)
        if c.log:
            for i, (text, log_type) in enumerate(c.log[-5:]):
                colors = {"damage": C.CRIMSON, "crit": C.PARCHMENT_EDGE, "heal": C.MIST,
                          "shield": C.FROST, "effect": C.ELDRITCH, "info": C.INK_LIGHT}
                color = colors.get(log_type, C.INK)
                text = fit_text(self.assets.fonts["tiny"], text, log_w - 30)
                draw_text_with_glow(surface, text, self.assets.fonts["tiny"], color,
                          log_x + 15, log_y + 32 + i * 26)

        # --- Skills panel ---
        draw_text_with_glow(surface, "Your Abilities", self.assets.fonts["small"], C.INK, 30, 440)
        for i, (sk, btn) in enumerate(zip(s.active_skills, self.skill_buttons)):
            on_cd = sk.current_cd > 0

            label = f"[{i+1}] {sk.name}"
            if on_cd:
                label += f" (CD:{sk.current_cd})"
            if sk.cost > 0:
                label += f" ({sk.cost} MAD)"
            label = fit_text(self.assets.fonts["small"], label, btn.w - 20)
            draw_ornate_button(surface, btn, label, self.assets.fonts["small"],
                               hover=(i == self.hover_idx and not on_cd),
                               color=C.CRIMSON if on_cd else C.PARCHMENT_EDGE, disabled=on_cd)

        # Skill tooltip popup on hover (above the button, like class select)
        if 0 <= self.hover_idx < len(s.active_skills):
            sk = s.active_skills[self.hover_idx]
            self._draw_skill_tooltip(surface, sk, self.skill_buttons[self.hover_idx])

        # Command buttons
        can_run = not c.is_boss
        cmd_names = list(self.cmd_buttons.keys())
        for ci, (name, btn) in enumerate(self.cmd_buttons.items()):
            labels = {"run": "Run [R]", "inventory": "[I]", "save": "[S]"}
            draw_ornate_button(surface, btn, labels[name], self.assets.fonts["tiny"],
                               hover=((len(s.active_skills) + ci) == self.hover_idx),
                               color=C.CRIMSON if name == "run" else C.PARCHMENT_EDGE,
                               disabled=(name == "run" and not can_run))

        # Turn message popup
        if self.turn_msg_timer > 0 and self.turn_message:
            draw_text_with_glow(surface, self.turn_message, self.assets.fonts["body"],
                      C.CRIMSON, SCREEN_W // 2, 245, align="center")

        # Damage numbers
        for dn in self.damage_numbers:
            text, x, y, color, timer, vy = dn
            draw_text(surface, text, self.assets.fonts["heading"], color, int(x) + ox, int(y) + oy)


# ═══════════════════════════════════════════
# INVENTORY SCREEN
# ═══════════════════════════════════════════

class InventoryScreen(Screen):
    def __init__(self, game):
        super().__init__(game)
        self.back_btn = None
        self.item_buttons = []
        self.prev_screen = "explore"

    def enter(self):
        self.prev_screen = "combat" if self.game.state.combat else "explore"

    def handle_event(self, event):
        s = self.game.state
        all_btns = self.item_buttons + ([self.back_btn] if self.back_btn else [])
        self.update_hover(event, all_btns)
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE or event.key == pygame.K_q:
                self.game.switch_screen(self.prev_screen)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.back_btn and self.back_btn.collidepoint(event.pos):
                self.game.switch_screen(self.prev_screen)
            for i, btn in enumerate(self.item_buttons):
                if btn.collidepoint(event.pos) and i < len(s.inventory):
                    item = s.inventory[i]
                    prev = s.equip_item(item)
                    s.inventory.pop(i)
                    if prev:
                        s.inventory.append(prev)

    def draw(self, surface):
        s = self.game.state

        draw_parchment_panel(surface, 30, 10, SCREEN_W - 60, SCREEN_H - 80)
        draw_text_with_glow(surface, "INVENTORY", self.assets.fonts["heading"],
                  C.PARCHMENT_EDGE, SCREEN_W // 2, 22, align="center")
        draw_gold_divider(surface, SCREEN_W // 2 - 150, 55, 300)

        # Equipped items
        slots = ["weapon", "accessory", "armor", "boots", "ringL", "ringR"]
        slot_names = {"weapon": "WEAPON", "accessory": "ACCESSORY", "armor": "ARMOR",
                      "boots": "BOOTS", "ringL": "LEFT RING", "ringR": "RIGHT RING"}

        draw_text_with_glow(surface, "Equipped", self.assets.fonts["body"], C.INK, 55, 68)
        y = 98
        label_max_w = SCREEN_W - 180  # leave room for margins
        for slot in slots:
            item = s.equipment.get(slot)
            if item:
                color = rarity_color(item.rarity)
                # Line 1: slot + item name (pixel-width truncated)
                label = f"{slot_names[slot]}: {item.name}"
                draw_text_fitted_glow(surface, label, self.assets.fonts["small"],
                                 color, 70, y, label_max_w)
                # Line 2: stats (indented)
                stat_line = item.stat_text()
                draw_text_fitted_glow(surface, stat_line, self.assets.fonts["tiny"],
                                 C.INK, 90, y + 18, label_max_w - 20)
                # Line 3: debuffs (if any, separate line)
                if item.debuffs:
                    draw_text_fitted_glow(surface, item.debuff_text(), self.assets.fonts["tiny"],
                                     C.CRIMSON, 90, y + 34, label_max_w - 20)
                    y += 52
                else:
                    y += 42
            else:
                draw_text_with_glow(surface, f"{slot_names[slot]}: — empty —", self.assets.fonts["small"], C.INK_LIGHT, 70, y)
                y += 30

        # Backpack
        y += 8
        draw_gold_divider(surface, 55, y, SCREEN_W - 120)
        y += 10
        draw_text_with_glow(surface, f"Backpack ({len(s.inventory)}/20)", self.assets.fonts["body"], C.INK, 55, y)
        y += 28
        self.item_buttons = []
        if not s.inventory:
            draw_text_with_glow(surface, "Your pack is empty.", self.assets.fonts["small"], C.INK_LIGHT, 70, y)
        else:
            item_h = 48
            for i, item in enumerate(s.inventory):
                color = rarity_color(item.rarity)
                btn = pygame.Rect(60, y, SCREEN_W - 130, item_h)
                self.item_buttons.append(btn)
                # Hover highlight on item row
                if i == self.hover_idx:
                    row_bg = pygame.Surface((btn.w, btn.h), pygame.SRCALPHA)
                    row_bg.fill((212, 160, 23, 30))
                    surface.blit(row_bg, (btn.x, btn.y))
                    pygame.draw.rect(surface, C.GOLD_TRIM, btn, 1, border_radius=3)
                # Line 1: item name + slot (pixel-width truncated)
                label = f"{i+1}. {item.name} ({item.slot.upper()})"
                draw_text_fitted_glow(surface, label, self.assets.fonts["small"],
                                 color, 70, y, 500)
                # Line 2: stats + debuffs
                stat_line = item.stat_text()
                if item.debuffs:
                    stat_line += "  " + item.debuff_text()
                draw_text_fitted_glow(surface, stat_line, self.assets.fonts["tiny"],
                                 C.INK, 90, y + 20, 480)
                y += item_h + 4

        # Back button
        self.back_btn = pygame.Rect(SCREEN_W // 2 - 60, SCREEN_H - 65, 120, 40)
        back_hover = (len(self.item_buttons) == self.hover_idx)
        draw_ornate_button(surface, self.back_btn, "Back [Q]", self.assets.fonts["body"],
                           hover=back_hover, color=C.PARCHMENT_EDGE)


# ═══════════════════════════════════════════
# SHOP SCREEN
# ═══════════════════════════════════════════

class ShopScreen(Screen):
    def __init__(self, game):
        super().__init__(game)
        self.buy_buttons = []
        self.leave_btn = None

    def update(self, dt):
        if self.game.shop_msg_timer > 0:
            self.game.shop_msg_timer -= dt

    def handle_event(self, event):
        s = self.game.state
        # Track hover
        all_btns = self.buy_buttons + ([self.leave_btn] if self.leave_btn else [])
        self.update_hover(event, all_btns)

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                if advance_floor(s):
                    self.game.switch_screen("victory")
                else:
                    self.game.switch_screen("explore")
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for i, btn in enumerate(self.buy_buttons):
                if btn.collidepoint(event.pos) and i < len(self.game.shop_items):
                    ok, msg = buy_shop_item(s, self.game.shop_items,
                                            self.game.shop_prices,
                                            self.game.shop_sold, i)
                    self.game.shop_message = msg
                    self.game.shop_msg_ok = ok
                    self.game.shop_msg_timer = 1.5
            if self.leave_btn and self.leave_btn.collidepoint(event.pos):
                if advance_floor(s):
                    self.game.switch_screen("victory")
                else:
                    self.game.switch_screen("explore")

    def draw(self, surface):
        s = self.game.state

        draw_parchment_panel(surface, 30, 10, SCREEN_W - 60, SCREEN_H - 80)
        draw_text_with_glow(surface, "THE MAD TRADER", self.assets.fonts["heading"],
                  C.PARCHMENT_EDGE, SCREEN_W // 2, 22, align="center")
        draw_text_with_glow(surface, '"Everything has a price. Especially knowledge."',
                  self.assets.fonts["tiny"], C.INK_LIGHT, SCREEN_W // 2, 58, align="center")
        draw_text_with_glow(surface, f"Gold: {s.gold}", self.assets.fonts["body"],
                  C.PARCHMENT_EDGE, SCREEN_W // 2, 80, align="center")
        draw_gold_divider(surface, SCREEN_W // 2 - 150, 102, 300)

        self.buy_buttons = []
        y = 125
        card_h = 90
        for i, item in enumerate(self.game.shop_items):
            color = rarity_color(item.rarity)
            rd = RARITY_DATA[item.rarity]
            btn = pygame.Rect(55, y, SCREEN_W - 120, card_h)
            self.buy_buttons.append(btn)

            sold = self.game.shop_sold[i]
            draw_panel(surface, 55, y, SCREEN_W - 120, card_h, C.PANEL_BG,
                       C.CRIMSON if sold else C.GOLD_DIM, 1 if sold else 2)

            # Line 1: item name — pixel-width truncated to leave room for price
            name_text = f"{item.name} ({item.slot.upper()}, {rd['name']})"
            if sold:
                name_text += " SOLD"
            name_max_w = SCREEN_W - 200  # leave ~130px for price on right + margins
            draw_text_fitted_glow(surface, name_text, self.assets.fonts["body"],
                             color if not sold else C.INK_LIGHT, 70, y + 6, name_max_w)

            # Line 2: stats
            stat_text = item.stat_text()
            draw_text_fitted_glow(surface, stat_text, self.assets.fonts["tiny"],
                             C.INK, 70, y + 34, SCREEN_W - 200)

            # Line 3: debuffs (separate line below stats)
            if item.debuffs:
                draw_text_fitted_glow(surface, item.debuff_text(), self.assets.fonts["tiny"],
                                 C.CRIMSON, 70, y + 56, SCREEN_W - 200)

            # Price on the right (vertically centered in card)
            draw_text_with_glow(surface, f"{self.game.shop_prices[i]}g", self.assets.fonts["body"],
                      C.PARCHMENT_EDGE, SCREEN_W - 75, y + card_h // 2 - 11, align="right")
            y += card_h + 10

        self.leave_btn = pygame.Rect(SCREEN_W // 2 - 80, y + 15, 160, 45)
        leave_hover = (len(self.buy_buttons) == self.hover_idx)
        draw_ornate_button(surface, self.leave_btn, "Leave Shop", self.assets.fonts["body"],
                           hover=leave_hover, color=C.PARCHMENT_EDGE)

        if hasattr(self.game, 'shop_msg_timer') and self.game.shop_msg_timer > 0:
            color = C.MIST if self.game.shop_msg_ok else C.CRIMSON
            draw_text_with_glow(surface, self.game.shop_message, self.assets.fonts["body"],
                      color, SCREEN_W // 2, y + 75, align="center")


# ═══════════════════════════════════════════
# REST SCREEN
# ═══════════════════════════════════════════

class RestScreen(Screen):
    def __init__(self, game):
        super().__init__(game)
        self.options = [
            ("REST", "Heal 40% HP", "rest"),
            ("MEDITATE", "Reduce Madness by 15", "meditate"),
            ("TRAIN", "+1 to all base stats", "train"),
        ]
        self.buttons = []
        self.result_msg = ""
        self.result_timer = 0

    def enter(self):
        bw, bh = 400, 55
        cx = SCREEN_W // 2
        self.buttons = [pygame.Rect(cx - bw // 2, 330 + i * 70, bw, bh) for i in range(3)]
        self.result_msg = ""
        self.result_timer = 0

    def handle_event(self, event):
        s = self.game.state
        # Don't accept new inputs while showing result
        if self.result_timer > 0:
            return
        self.update_hover(event, self.buttons)
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for i, btn in enumerate(self.buttons):
                if btn.collidepoint(event.pos):
                    self._do_rest(i)
        elif event.type == pygame.KEYDOWN:
            if pygame.K_1 <= event.key <= pygame.K_3:
                self._do_rest(event.key - pygame.K_1)

    def _do_rest(self, idx):
        s = self.game.state
        if idx == 0:
            h = int(s.max_hp * 0.4)
            s.hp = min(s.max_hp, s.hp + h)
            self.result_msg = f"Rested. Healed {h} HP."
        elif idx == 1:
            s.add_madness(-15)
            self.result_msg = "Meditated. Madness reduced."
        elif idx == 2:
            for k in s.base_stats:
                s.base_stats[k] += 1
            s.recalc_stats()
            self.result_msg = "Trained. All stats +1."
        self.result_timer = 2.0

    def update(self, dt):
        if self.result_timer > 0:
            self.result_timer -= dt
            if self.result_timer <= 0:
                if advance_floor(self.game.state):
                    self.game.switch_screen("victory")
                else:
                    self.game.switch_screen("explore")

    def draw(self, surface):
        draw_hud(surface, self.game.state, self.assets)

        panel_w, panel_h = 500, 200
        panel_x = SCREEN_W // 2 - panel_w // 2
        draw_parchment_panel(surface, panel_x, 135, panel_w, panel_h)

        draw_text_with_glow(surface, "A MOMENT OF RESPITE", self.assets.fonts["heading"],
                  C.PARCHMENT_EDGE, SCREEN_W // 2, 145, align="center")
        draw_text_with_glow(surface, "You find a quiet corner. The madness recedes, briefly.",
                  self.assets.fonts["tiny"], C.INK, SCREEN_W // 2, 185, align="center")

        for i, (name, desc, _) in enumerate(self.options):
            draw_ornate_button(surface, self.buttons[i], f"[{i+1}] {name} — {desc}",
                               self.assets.fonts["body"], hover=(i == self.hover_idx), color=C.PARCHMENT_EDGE)

        if self.result_msg:
            draw_text_with_glow(surface, self.result_msg, self.assets.fonts["body"],
                      C.MIST, SCREEN_W // 2, 560, align="center")


# ═══════════════════════════════════════════
# LOOT SCREEN
# ═══════════════════════════════════════════

class LootScreen(Screen):
    def __init__(self, game):
        super().__init__(game)
        self.items = []
        self.gold_found = 0
        self.pick_buttons = []
        self.leave_btn = None

    def enter(self):
        s = self.game.state
        count = 1 + (1 if random.random() < 0.3 else 0)
        self.items = [generate_item(s.floor, luck=s.luck) for _ in range(count)]
        self.gold_found = 5 + random.randint(0, 10) + s.floor * 2
        s.gold += self.gold_found
        cx = SCREEN_W // 2
        self.pick_buttons = []
        y = 130
        for item in self.items:
            # Taller buttons for items with debuffs
            bh = 90 if item.debuffs else 70
            self.pick_buttons.append(pygame.Rect(cx - 250, y, 500, bh))
            y += bh + 12
        self.leave_btn = pygame.Rect(cx - 100, y + 8, 200, 40)

    def handle_event(self, event):
        s = self.game.state
        all_btns = self.pick_buttons + ([self.leave_btn] if self.leave_btn else [])
        self.update_hover(event, all_btns)
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for i, btn in enumerate(self.pick_buttons):
                if btn.collidepoint(event.pos) and i < len(self.items):
                    if len(s.inventory) < 20:
                        s.inventory.append(self.items[i])
                    else:
                        prev = s.equip_item(self.items[i])
                        if prev:
                            s.inventory.append(prev)
                    self.game.switch_screen("explore")
                    return
            if self.leave_btn and self.leave_btn.collidepoint(event.pos):
                self.game.switch_screen("explore")

    def draw(self, surface):
        # Dynamic panel height based on actual button positions
        panel_w = 560
        if self.pick_buttons:
            last_btn = self.pick_buttons[-1]
            panel_h = min(last_btn.bottom + 70, SCREEN_H - 20)
        else:
            panel_h = 300
        panel_x = SCREEN_W // 2 - panel_w // 2
        draw_parchment_panel(surface, panel_x, 10, panel_w, panel_h)

        draw_text_with_glow(surface, "SALVAGE FOUND", self.assets.fonts["heading"],
                  C.PARCHMENT_EDGE, SCREEN_W // 2, 25, align="center")
        draw_gold_divider(surface, SCREEN_W // 2 - 120, 58, 240)
        draw_text_with_glow(surface, f"+{self.gold_found} Gold", self.assets.fonts["body"],
                  C.PARCHMENT_EDGE, SCREEN_W // 2, 70, align="center")

        for i, (item, btn) in enumerate(zip(self.items, self.pick_buttons)):
            color = rarity_color(item.rarity)
            rd = RARITY_DATA[item.rarity]
            # Button background with hover
            draw_ornate_button(surface, btn, "", self.assets.fonts["tiny"],
                               hover=(i == self.hover_idx), color=color)
            # Item name + slot + rarity on line 1
            label = f"{item.name}  ({item.slot.upper()}, {rd['name']})"
            label = fit_text(self.assets.fonts["small"], label, btn.w - 30)
            draw_text_with_glow(surface, label, self.assets.fonts["small"], color,
                                btn.x + 15, btn.y + 8)
            # Stats on line 2 (full, not truncated)
            stat_line = item.stat_text()
            draw_text_with_glow(surface, stat_line, self.assets.fonts["tiny"],
                                C.INK, btn.x + 15, btn.y + 32)
            # Debuffs on line 3 (if cursed)
            if item.debuffs:
                debuff_line = item.debuff_text()
                draw_text_with_glow(surface, debuff_line, self.assets.fonts["tiny"],
                                    C.CRIMSON, btn.x + 15, btn.y + 52)

        leave_hover = (len(self.pick_buttons) == self.hover_idx)
        draw_ornate_button(surface, self.leave_btn, "Leave it", self.assets.fonts["body"],
                           hover=leave_hover, color=C.PARCHMENT_EDGE)


# ═══════════════════════════════════════════
# EVENT SCREEN
# ═══════════════════════════════════════════

class EventScreen(Screen):
    def __init__(self, game):
        super().__init__(game)
        self.outcome_buttons = []
        self.result_msg = ""
        self.result_loot = None
        self.showing_result = False

    def enter(self):
        self.showing_result = False
        self.result_msg = ""
        event = self.game.pending_event
        n = len(event["outcomes"])
        bw, bh = 500, 50
        cx = SCREEN_W // 2
        self.outcome_buttons = [pygame.Rect(cx - bw // 2, 360 + i * 62, bw, bh) for i in range(n)]

    def handle_event(self, event):
        s = self.game.state
        if self.showing_result:
            if event.type == pygame.KEYDOWN or (event.type == pygame.MOUSEBUTTONDOWN):
                if s.hp <= 0:
                    self.game.gameover_msg = "The asylum claims another victim."
                    self.game.switch_screen("gameover")
                else:
                    self.game.switch_screen("explore")
            return

        self.update_hover(event, self.outcome_buttons)
        pe = self.game.pending_event
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for i, btn in enumerate(self.outcome_buttons):
                if btn.collidepoint(event.pos) and i < len(pe["outcomes"]):
                    self._resolve(i)
        elif event.type == pygame.KEYDOWN:
            if pygame.K_1 <= event.key <= pygame.K_9:
                idx = event.key - pygame.K_1
                if idx < len(pe["outcomes"]):
                    self._resolve(idx)

    def _resolve(self, idx):
        s = self.game.state
        pe = self.game.pending_event
        msg, loot = resolve_event(s, EVENTS.index(pe), idx)
        self.result_msg = msg
        self.result_loot = loot
        if loot:
            s.inventory.append(loot)
        self.showing_result = True

    def draw(self, surface):
        pe = self.game.pending_event

        panel_w, panel_h = 600, 280
        panel_x = SCREEN_W // 2 - panel_w // 2
        draw_parchment_panel(surface, panel_x, 130, panel_w, panel_h)

        draw_text_with_glow(surface, pe["title"], self.assets.fonts["heading"],
                  C.PARCHMENT_EDGE, SCREEN_W // 2, 145, align="center")
        draw_gold_divider(surface, SCREEN_W // 2 - 180, 178, 360)
        draw_text_wrapped_glow(surface, pe["text"], self.assets.fonts["body"],
                          C.INK, SCREEN_W // 2 - 270, 195, 540)

        if self.showing_result:
            color = C.MIST if "heal" in self.result_msg.lower() or "+" not in self.result_msg else C.CRIMSON
            draw_text_with_glow(surface, self.result_msg, self.assets.fonts["body"],
                      color, SCREEN_W // 2, 425, align="center")
            if self.result_loot:
                loot_text = fit_text(self.assets.fonts["small"],
                                     f"Received: {self.result_loot.name}", 500)
                draw_text_with_glow(surface, loot_text,
                          self.assets.fonts["small"], rarity_color(self.result_loot.rarity),
                          SCREEN_W // 2, 458, align="center")
            draw_text_with_glow(surface, "Click to continue...", self.assets.fonts["tiny"],
                      C.INK_LIGHT, SCREEN_W // 2, 498, align="center")
        else:
            for i, (o, btn) in enumerate(zip(pe["outcomes"], self.outcome_buttons)):
                draw_ornate_button(surface, btn, f"[{i+1}] {o['text']}",
                                   self.assets.fonts["body"], hover=(i == self.hover_idx), color=C.PARCHMENT_EDGE)


# ═══════════════════════════════════════════
# TRAP RESULT SCREEN
# ═══════════════════════════════════════════

class TrapResultScreen(Screen):
    def __init__(self, game):
        super().__init__(game)
        self.continue_btn = None

    def handle_event(self, event):
        self.update_hover(event, [self.continue_btn] if self.continue_btn else [])
        if event.type == pygame.KEYDOWN or (event.type == pygame.MOUSEBUTTONDOWN and
                                            self.continue_btn and self.continue_btn.collidepoint(event.pos)):
            self.game.switch_screen("explore")

    def draw(self, surface):
        panel_w, panel_h = 500, 180
        panel_x = SCREEN_W // 2 - panel_w // 2
        draw_parchment_panel(surface, panel_x, 200, panel_w, panel_h)

        draw_text_with_glow(surface, f"TRAP: {self.game.trap_name}", self.assets.fonts["heading"],
                  C.CRIMSON, SCREEN_W // 2, 215, align="center")
        draw_text_with_glow(surface, self.game.trap_desc, self.assets.fonts["small"],
                  C.INK_LIGHT, SCREEN_W // 2, 252, align="center")
        draw_gold_divider(surface, SCREEN_W // 2 - 150, 270, 300)
        draw_text_wrapped_glow(surface, self.game.trap_msg, self.assets.fonts["body"],
                          C.INK, SCREEN_W // 2 - 220, 285, 440)

        self.continue_btn = pygame.Rect(SCREEN_W // 2 - 80, 345, 160, 35)
        draw_ornate_button(surface, self.continue_btn, "Continue", self.assets.fonts["small"],
                           hover=(self.hover_idx == 0), color=C.PARCHMENT_EDGE)


# ═══════════════════════════════════════════
# COMBAT RESULT SCREEN
# ═══════════════════════════════════════════

class CombatResultScreen(Screen):
    def __init__(self, game):
        super().__init__(game)
        self.equip_btn = None
        self.backpack_btn = None
        self.chosen = False

    def enter(self):
        self.chosen = False

    def handle_event(self, event):
        s = self.game.state
        r = self.game.combat_result
        if self.chosen:
            if event.type == pygame.KEYDOWN or (event.type == pygame.MOUSEBUTTONDOWN):
                if r["is_boss"]:
                    self.game.switch_screen("victory")
                elif advance_floor(s):
                    self.game.switch_screen("victory")
                else:
                    self.game.switch_screen("explore")
            return

        btns = []
        if self.equip_btn:
            btns.append(self.equip_btn)
        if self.backpack_btn:
            btns.append(self.backpack_btn)
        self.update_hover(event, btns)

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_1:
                self._equip_loot()
            elif event.key == pygame.K_2:
                self._store_loot()
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.equip_btn and self.equip_btn.collidepoint(event.pos):
                self._equip_loot()
            elif self.backpack_btn and self.backpack_btn.collidepoint(event.pos):
                self._store_loot()

    def _equip_loot(self):
        s = self.game.state
        r = self.game.combat_result
        prev = s.equip_item(r["loot"])
        if prev:
            s.inventory.append(prev)
        self.chosen = True

    def _store_loot(self):
        s = self.game.state
        r = self.game.combat_result
        if len(s.inventory) < 20:
            s.inventory.append(r["loot"])
        self.chosen = True

    def draw(self, surface):
        r = self.game.combat_result

        loot = r["loot"]
        # Taller panel for cursed items with debuffs
        panel_h = 250 if loot.debuffs else 220
        panel_w = 520
        panel_y = 40
        panel_h = 250 if loot.debuffs else 220
        panel_x = SCREEN_W // 2 - panel_w // 2
        draw_parchment_panel(surface, panel_x, panel_y, panel_w, panel_h)

        title = "VICTORY" if r["victory"] else "DEFEAT"
        title_color = C.PARCHMENT_EDGE if r["victory"] else C.CRIMSON
        draw_text_with_glow(surface, title, self.assets.fonts["heading"],
                  title_color, SCREEN_W // 2, 55, align="center")
        draw_gold_divider(surface, SCREEN_W // 2 - 120, 88, 240)

        draw_text_with_glow(surface, f"+{r['gold']} Gold    +{r['xp']} XP",
                  self.assets.fonts["body"], C.PARCHMENT_EDGE, SCREEN_W // 2, 100, align="center")

        color = rarity_color(loot.rarity)
        rd = RARITY_DATA[loot.rarity]
        drop_text = f"Dropped: {loot.name} ({loot.slot.upper()}, {rd['name']})"
        drop_text = fit_text(self.assets.fonts["body"], drop_text, panel_w - 40)
        draw_text_with_glow(surface, drop_text,
                  self.assets.fonts["body"], color, SCREEN_W // 2, 140, align="center")
        # Full stat line (not truncated)
        stat_text = loot.stat_text()
        draw_text_with_glow(surface, stat_text, self.assets.fonts["small"],
                  C.INK, SCREEN_W // 2, 170, align="center")
        # Debuff line (if cursed)
        if loot.debuffs:
            debuff_text = loot.debuff_text()
            draw_text_with_glow(surface, debuff_text, self.assets.fonts["small"],
                      C.CRIMSON, SCREEN_W // 2, 194, align="center")

        if not self.chosen:
            btn_y = panel_y + panel_h - 55
            cx = SCREEN_W // 2
            self.equip_btn = pygame.Rect(cx - 210, btn_y, 200, 45)
            self.backpack_btn = pygame.Rect(cx + 10, btn_y, 200, 45)
            draw_ornate_button(surface, self.equip_btn, "[1] Equip", self.assets.fonts["body"],
                               hover=(0 == self.hover_idx), color=C.PARCHMENT_EDGE)
            draw_ornate_button(surface, self.backpack_btn, "[2] Backpack", self.assets.fonts["body"],
                               hover=(1 == self.hover_idx), color=C.PARCHMENT_EDGE)
        else:
            draw_text_with_glow(surface, "Click or press any key to continue...",
                      self.assets.fonts["small"], C.INK_LIGHT, SCREEN_W // 2, 280, align="center")


# ═══════════════════════════════════════════
# LEVEL UP SCREEN
# ═══════════════════════════════════════════

class LevelUpScreen(Screen):
    def __init__(self, game):
        super().__init__(game)
        self.skill_buttons = []
        self.skip_btn = None
        self.replace_mode = False
        self.replace_buttons = []

    def enter(self):
        self.replace_mode = False
        self._build_skill_buttons()

    def _build_skill_buttons(self):
        s = self.game.state
        bw, bh = 500, 50
        cx = SCREEN_W // 2
        skills = s.pending_levelup_skills
        self.skill_buttons = [pygame.Rect(cx - bw // 2, 200 + i * 80, bw, bh) for i in range(len(skills))]
        self.skip_btn = pygame.Rect(cx - 100, 200 + len(skills) * 80 + 10, 200, 40)

    def handle_event(self, event):
        s = self.game.state
        if not s.pending_levelup_skills:
            if event.type == pygame.KEYDOWN or (event.type == pygame.MOUSEBUTTONDOWN):
                self.game.switch_screen("explore")
            return

        if self.replace_mode:
            self.update_hover(event, self.replace_buttons)
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                for i, btn in enumerate(self.replace_buttons):
                    if btn.collidepoint(event.pos):
                        if i < len(s.active_skills):
                            chosen = s.pending_levelup_skills[0]
                            s.active_skills[i] = chosen
                            s.pending_levelup_skills = []
                            self.replace_mode = False
                            return
                        else:
                            s.pending_levelup_skills = []
                            self.replace_mode = False
                            return
            elif event.type == pygame.KEYDOWN:
                if pygame.K_1 <= event.key <= pygame.K_9:
                    idx = event.key - pygame.K_1
                    if idx < len(s.active_skills):
                        chosen = s.pending_levelup_skills[0]
                        s.active_skills[idx] = chosen
                        s.pending_levelup_skills = []
                        self.replace_mode = False
                    elif idx == len(s.active_skills):
                        s.pending_levelup_skills = []
                        self.replace_mode = False
            return

        all_btns = self.skill_buttons + ([self.skip_btn] if self.skip_btn else [])
        self.update_hover(event, all_btns)

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for i, btn in enumerate(self.skill_buttons):
                if btn.collidepoint(event.pos) and i < len(s.pending_levelup_skills):
                    self._pick_skill(i)
            if self.skip_btn and self.skip_btn.collidepoint(event.pos):
                s.pending_levelup_skills = []
                self.game.switch_screen("explore")
        elif event.type == pygame.KEYDOWN:
            if pygame.K_1 <= event.key <= pygame.K_9:
                idx = event.key - pygame.K_1
                if idx < len(s.pending_levelup_skills):
                    self._pick_skill(idx)
                elif idx == len(s.pending_levelup_skills):
                    s.pending_levelup_skills = []
                    self.game.switch_screen("explore")

    def _pick_skill(self, idx):
        s = self.game.state
        chosen = s.pending_levelup_skills[idx]
        if len(s.active_skills) >= MAX_ACTIVE_SKILLS:
            self.replace_mode = True
            s.pending_levelup_skills = [chosen]
            bw, bh = 500, 40
            cx = SCREEN_W // 2
            self.replace_buttons = [pygame.Rect(cx - bw // 2, 230 + i * 45, bw, bh)
                                    for i in range(len(s.active_skills) + 1)]
        else:
            s.active_skills.append(chosen)
            s.pending_levelup_skills = []
            self.game.switch_screen("explore")

    def draw(self, surface):
        s = self.game.state

        panel_w, panel_h = 600, 400
        panel_x = SCREEN_W // 2 - panel_w // 2
        draw_parchment_panel(surface, panel_x, 15, panel_w, panel_h)

        draw_text_with_glow(surface, "LEVEL UP!", self.assets.fonts["heading"],
                  C.PARCHMENT_EDGE, SCREEN_W // 2, 28, align="center")
        draw_text_with_glow(surface, f"{s.class_name} is now Level {s.level}!",
                  self.assets.fonts["body"], C.INK, SCREEN_W // 2, 65, align="center")
        draw_text_with_glow(surface, f"HP: {s.max_hp}  ATK: {s.atk}  DEF: {s.defense}/{s.m_def}",
                  self.assets.fonts["tiny"], C.INK_LIGHT, SCREEN_W // 2, 90, align="center")
        draw_gold_divider(surface, SCREEN_W // 2 - 180, 108, 360)

        if self.replace_mode:
            draw_text_with_glow(surface, "CHOOSE ABILITY TO REPLACE", self.assets.fonts["body"],
                      C.CRIMSON, SCREEN_W // 2, 130, align="center")
            for i, (sk, btn) in enumerate(zip(s.active_skills, self.replace_buttons)):
                draw_ornate_button(surface, btn, f"{i+1}. {sk.name} — {sk.desc}",
                                   self.assets.fonts["small"], hover=(i == self.hover_idx), color=C.PARCHMENT_EDGE)
            cancel_btn = self.replace_buttons[-1] if self.replace_buttons else None
            if cancel_btn:
                draw_ornate_button(surface, cancel_btn, f"{len(s.active_skills)+1}. Cancel",
                                   self.assets.fonts["small"], hover=(len(s.active_skills) == self.hover_idx), color=C.PARCHMENT_EDGE)
        elif s.pending_levelup_skills:
            draw_text_with_glow(surface, "CHOOSE A NEW ABILITY", self.assets.fonts["body"],
                      C.PARCHMENT_EDGE, SCREEN_W // 2, 125, align="center")
            if len(s.active_skills) >= MAX_ACTIVE_SKILLS:
                draw_text_with_glow(surface, "(Skill slots full — will replace an existing ability)",
                          self.assets.fonts["tiny"], C.CRIMSON, SCREEN_W // 2, 152, align="center")

            for i, (sk, btn) in enumerate(zip(s.pending_levelup_skills, self.skill_buttons)):
                draw_ornate_button(surface, btn, f"[{i+1}] {sk.name}", self.assets.fonts["body"],
                                   hover=(i == self.hover_idx), color=C.PARCHMENT_EDGE)
                draw_text_with_glow(surface, sk.desc, self.assets.fonts["tiny"], C.INK,
                          btn.centerx, btn.bottom + 2, align="center")

            draw_ornate_button(surface, self.skip_btn, "Skip", self.assets.fonts["small"],
                               hover=(len(s.pending_levelup_skills) == self.hover_idx), color=C.PARCHMENT_EDGE)
        else:
            draw_text_with_glow(surface, "Press any key to continue...", self.assets.fonts["small"],
                      C.INK_LIGHT, SCREEN_W // 2, 200, align="center")


# ═══════════════════════════════════════════
# GAME OVER SCREEN
# ═══════════════════════════════════════════

class GameOverScreen(Screen):
    def __init__(self, game):
        super().__init__(game)
        self.restart_btn = None
        self.menu_btn = None

    def handle_event(self, event):
        btns = []
        if self.restart_btn:
            btns.append(self.restart_btn)
        if self.menu_btn:
            btns.append(self.menu_btn)
        self.update_hover(event, btns)
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.restart_btn and self.restart_btn.collidepoint(event.pos):
                self.game.switch_screen("class_select")
            elif self.menu_btn and self.menu_btn.collidepoint(event.pos):
                self.game.switch_screen("title")
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_r:
                self.game.switch_screen("class_select")
            elif event.key == pygame.K_q:
                self.game.switch_screen("title")

    def draw(self, surface):
        # The Game_Over_Screen background is already drawn by main loop
        draw_text_with_glow(surface, "GAME OVER", self.assets.fonts["title"],
                  C.CRIMSON, SCREEN_W // 2, 40, align="center")
        draw_gold_divider(surface, SCREEN_W // 2 - 180, 120, 360)
        draw_text_wrapped_glow(surface, self.game.gameover_msg, self.assets.fonts["body"],
                          C.INK, SCREEN_W // 2 - 300, 140, 600)

        cx = SCREEN_W // 2
        self.restart_btn = pygame.Rect(cx - 170, 300, 160, 45)
        self.menu_btn = pygame.Rect(cx + 10, 300, 160, 45)
        draw_ornate_button(surface, self.restart_btn, "[R] Retry", self.assets.fonts["body"],
                           hover=(0 == self.hover_idx), color=C.PARCHMENT_EDGE)
        draw_ornate_button(surface, self.menu_btn, "[Q] Menu", self.assets.fonts["body"],
                           hover=(1 == self.hover_idx), color=C.PARCHMENT_EDGE)


# ═══════════════════════════════════════════
# VICTORY SCREEN
# ═══════════════════════════════════════════

class VictoryScreen(Screen):
    def __init__(self, game):
        super().__init__(game)
        self.restart_btn = None
        self.menu_btn = None

    def handle_event(self, event):
        btns = []
        if self.restart_btn:
            btns.append(self.restart_btn)
        if self.menu_btn:
            btns.append(self.menu_btn)
        self.update_hover(event, btns)
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.restart_btn and self.restart_btn.collidepoint(event.pos):
                self.game.switch_screen("class_select")
            elif self.menu_btn and self.menu_btn.collidepoint(event.pos):
                self.game.switch_screen("title")
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_r:
                self.game.switch_screen("class_select")
            elif event.key == pygame.K_q:
                self.game.switch_screen("title")

    def draw(self, surface):
        s = self.game.state

        # Boss sprite
        boss_sprite = self.assets.get_sprite("Hastur, The Spiral Beyond")
        if boss_sprite:
            surface.blit(boss_sprite, (SCREEN_W // 2 - boss_sprite.get_width() // 2, 90))

        draw_text_with_glow(surface, "VICTORY", self.assets.fonts["title"],
                  C.PARCHMENT_EDGE, SCREEN_W // 2, 25, align="center")
        draw_text_with_glow(surface, "You emerge into pale dawn light.",
                  self.assets.fonts["body"], C.INK, SCREEN_W // 2, 340, align="center")

        if s.madness > 70:
            mt = "But your mind is fractured. Carcosa follows in your dreams."
        elif s.madness > 40:
            mt = "Your mind holds, barely. The scars will never fully heal."
        else:
            mt = "Against all odds, your mind remains whole. The Spiral is unraveled. For now."
        draw_text_wrapped_glow(surface, mt, self.assets.fonts["small"],
                          C.INK, SCREEN_W // 2 - 300, 370, 600)

        # Stats panel
        panel_w, panel_h = 320, 200
        panel_x = SCREEN_W // 2 - panel_w // 2
        draw_parchment_panel(surface, panel_x, 410, panel_w, panel_h)

        stats = [
            ("Level", str(s.level)),
            ("Kills", str(s.kills)),
            ("Rooms explored", str(s.rooms_explored)),
            ("Madness", f"{int(s.madness)}%"),
            ("Gold", str(s.gold)),
        ]
        y = 425
        for label, value in stats:
            draw_text_with_glow(surface, f"{label}:", self.assets.fonts["body"], C.INK_LIGHT,
                      SCREEN_W // 2 - 90, y, align="right")
            color = mad_color(s.madness) if label == "Madness" else C.PARCHMENT_EDGE if label == "Gold" else C.INK
            draw_text_with_glow(surface, value, self.assets.fonts["body"], color,
                      SCREEN_W // 2 + 10, y)
            y += 30

        cx = SCREEN_W // 2
        self.restart_btn = pygame.Rect(cx - 170, 625, 160, 45)
        self.menu_btn = pygame.Rect(cx + 10, 625, 160, 45)
        draw_ornate_button(surface, self.restart_btn, "[R] Play Again", self.assets.fonts["body"],
                           hover=(0 == self.hover_idx), color=C.PARCHMENT_EDGE)
        draw_ornate_button(surface, self.menu_btn, "[Q] Menu", self.assets.fonts["body"],
                           hover=(1 == self.hover_idx), color=C.PARCHMENT_EDGE)


# ═══════════════════════════════════════════
# STATS SCREEN
# ═══════════════════════════════════════════

class StatsScreen(Screen):
    def __init__(self, game):
        super().__init__(game)
        self.back_btn = None

    def handle_event(self, event):
        self.update_hover(event, [self.back_btn] if self.back_btn else [])
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE or event.key == pygame.K_q:
                self.game.switch_screen("explore")
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.back_btn and self.back_btn.collidepoint(event.pos):
                self.game.switch_screen("explore")

    def draw(self, surface):
        s = self.game.state
        color = CLASS_COLORS.get(s.class_id, C.PARCHMENT_EDGE)

        draw_parchment_panel(surface, 30, 10, SCREEN_W - 60, SCREEN_H - 80)
        draw_text_with_glow(surface, "CHARACTER STATS", self.assets.fonts["heading"],
                  C.PARCHMENT_EDGE, SCREEN_W // 2, 22, align="center")
        draw_text_with_glow(surface, f"{CLASS_ICONS.get(s.class_id, '?')} {s.class_name}  —  Level {s.level}",
                  self.assets.fonts["body"], color, SCREEN_W // 2, 58, align="center")
        draw_gold_divider(surface, SCREEN_W // 2 - 150, 84, 300)

        # Class sprite
        sprite = self.assets.get_class_sprite(s.class_id, "thumb")
        if sprite:
            big_sprite = pygame.transform.scale(sprite, (120, 120))
            surface.blit(big_sprite, (50, 100))

        # Core stats (left side)
        lx = 210
        y = 100
        draw_text_with_glow(surface, "Primary Stats", self.assets.fonts["body"], C.INK, lx - 20, y)
        y += 32
        stat_colors = {"int": C.ELDRITCH, "str": C.CRIMSON, "agi": C.MIST, "wis": C.FROST, "luck": C.PARCHMENT_EDGE}
        for stat_name in ["int", "str", "agi", "wis", "luck"]:
            val = s.stats.get(stat_name, 0)
            base = s.base_stats.get(stat_name, 0)
            bonus = val - base
            sc = stat_colors.get(stat_name, C.INK)

            # Stat icon
            icon = self.assets.images.get(f"stat_{stat_name}_64")
            if icon:
                surface.blit(icon, (lx - 20, y - 12))

            text = f"{stat_name.upper()}: {val}"
            if bonus > 0:
                text += f"  ({base}+{bonus})"
            draw_text_with_glow(surface, text, self.assets.fonts["body"], sc, lx + 56, y + 2)
            y += 58

        # Combat stats (right side)
        rx = SCREEN_W // 2 + 60
        ry = 100
        draw_text_with_glow(surface, "Combat Stats", self.assets.fonts["body"], C.INK, rx, ry)
        ry += 32
        combat_stats = [
            ("HP", f"{s.hp}/{s.max_hp}", hp_color(s.hp, s.max_hp)),
            ("ATK", str(s.atk), C.CRIMSON),
            ("DEF", str(s.defense), C.FROST),
            ("M.DEF", str(s.m_def), C.ELDRITCH),
            ("CRIT", f"{s.crit:.1f}%", C.PARCHMENT_EDGE),
            ("EVA", f"{s.evasion:.1f}%", C.MIST),
            ("ACC", f"{s.accuracy:.1f}%", C.INK),
        ]
        for label, val, sc in combat_stats:
            draw_text_with_glow(surface, f"{label}:", self.assets.fonts["small"], C.INK_LIGHT, rx, ry)
            draw_text_with_glow(surface, val, self.assets.fonts["small"], sc, rx + 80, ry)
            ry += 26

        # Progress & misc (below primary stats)
        y += 10
        draw_text_with_glow(surface, "Progress", self.assets.fonts["body"], C.INK, lx, y)
        y += 28
        draw_bar(surface, lx, y, 200, 14, s.xp, s.xp_next, C.XP_PURPLE)
        draw_text_with_glow(surface, f"XP: {s.xp}/{s.xp_next}", self.assets.fonts["tiny"], C.XP_PURPLE, lx + 210, y)
        y += 24
        draw_text_with_glow(surface, f"Floor: {s.floor}/{s.max_floor}", self.assets.fonts["small"], C.INK, lx, y)
        y += 24
        draw_text_with_glow(surface, f"Gold: {s.gold}g", self.assets.fonts["small"], C.PARCHMENT_EDGE, lx, y)
        y += 24
        draw_text_with_glow(surface, f"Kills: {s.kills}", self.assets.fonts["small"], C.INK, lx, y)
        y += 24
        draw_text_with_glow(surface, f"Rooms: {s.rooms_explored}", self.assets.fonts["small"], C.INK, lx, y)

        # Madness (right side, below combat stats)
        ry += 15
        draw_text_with_glow(surface, "Madness", self.assets.fonts["body"], C.INK, rx, ry)
        ry += 28
        draw_bar(surface, rx, ry, 200, 14, s.madness, 100, mad_color(s.madness))
        draw_text_with_glow(surface, f"{int(s.madness)}%", self.assets.fonts["tiny"], mad_color(s.madness), rx + 210, ry)
        ry += 28

        # Shield & Barrier
        if s.shield > 0 or s.barrier > 0:
            draw_text_with_glow(surface, "Defense", self.assets.fonts["body"], C.INK, rx, ry)
            ry += 28
            if s.shield > 0:
                draw_text_with_glow(surface, f"Shield: {int(s.shield)}", self.assets.fonts["small"], C.SHIELD_BLUE, rx, ry)
                ry += 24
            if s.barrier > 0:
                draw_text_with_glow(surface, f"Barrier: x{s.barrier}", self.assets.fonts["small"], C.FROST, rx, ry)
                ry += 24

        # Active skills list — compact, inside the panel
        skills_y = max(y, ry) + 8
        draw_gold_divider(surface, 50, skills_y, SCREEN_W - 110)
        skills_y += 10
        draw_text_with_glow(surface, f"Active Skills ({len(s.active_skills)}/{MAX_ACTIVE_SKILLS})",
                  self.assets.fonts["small"], C.INK, 55, skills_y)
        skills_y += 24
        max_y = SCREEN_H - 100  # keep within panel bounds
        for sk in s.active_skills:
            if skills_y + 18 > max_y:
                break
            label = f"  {sk.name} — {sk.desc}"
            label = fit_text(self.assets.fonts["tiny"], label, SCREEN_W - 120)
            draw_text_with_glow(surface, label, self.assets.fonts["tiny"], C.INK, 55, skills_y)
            skills_y += 18

        # Back button
        self.back_btn = pygame.Rect(SCREEN_W // 2 - 60, SCREEN_H - 65, 120, 40)
        draw_ornate_button(surface, self.back_btn, "Back [Q]", self.assets.fonts["body"],
                           hover=(self.hover_idx == 0), color=C.PARCHMENT_EDGE)


# ═══════════════════════════════════════════
# SAVE SCREEN
# ═══════════════════════════════════════════

class SaveScreen(Screen):
    def __init__(self, game):
        super().__init__(game)
        self.slot_buttons = []
        self.back_btn = None
        self.mode = "save"

    def enter(self):
        self.mode = "save" if self.game.state else "load"
        bw, bh = 400, 50
        cx = SCREEN_W // 2
        self.slot_buttons = [pygame.Rect(cx - bw // 2, 140 + i * 65, bw, bh) for i in range(5)]
        self.back_btn = pygame.Rect(cx - 60, 140 + 5 * 65 + 10, 120, 40)

    def handle_event(self, event):
        all_btns = self.slot_buttons + ([self.back_btn] if self.back_btn else [])
        self.update_hover(event, all_btns)
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.game.switch_screen("explore" if self.game.state else "title")
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.back_btn and self.back_btn.collidepoint(event.pos):
                self.game.switch_screen("explore" if self.game.state else "title")
                return
            for i, btn in enumerate(self.slot_buttons):
                if btn.collidepoint(event.pos):
                    self._do_slot(i)

    def _do_slot(self, slot):
        s = self.game.state
        if self.mode == "save" and s:
            save_game(s, slot)
            self.game.switch_screen("explore")
        else:
            loaded = load_game(slot)
            if loaded:
                self.game.state = loaded
                self.game.switch_screen("explore")

    def draw(self, surface):
        saves = list_saves()

        title = "SAVE GAME" if self.mode == "save" else "LOAD GAME"
        panel_w, panel_h = 500, 430
        panel_x = SCREEN_W // 2 - panel_w // 2
        draw_parchment_panel(surface, panel_x, 20, panel_w, panel_h)
        draw_text_with_glow(surface, title, self.assets.fonts["heading"],
                  C.PARCHMENT_EDGE, SCREEN_W // 2, 35, align="center")
        draw_gold_divider(surface, SCREEN_W // 2 - 120, 68, 240)

        for i, (sv, btn) in enumerate(zip(saves, self.slot_buttons)):
            if sv.get("empty"):
                label = f"Slot {sv['slot']}: — empty —"
                color = C.INK_LIGHT
            elif sv.get("error"):
                label = f"Slot {sv['slot']}: Corrupted"
                color = C.CRIMSON
            else:
                label = f"Slot {sv['slot']}: {sv['class_name']} Lv.{sv['level']} Floor {sv['floor']}"
                color = C.INK
            draw_ornate_button(surface, btn, label, self.assets.fonts["body"],
                               hover=(i == self.hover_idx), color=color)

        draw_ornate_button(surface, self.back_btn, "Back", self.assets.fonts["body"],
                           hover=(len(self.slot_buttons) == self.hover_idx), color=C.PARCHMENT_EDGE)


class LoadScreen(SaveScreen):
    def enter(self):
        self.mode = "load"
        bw, bh = 400, 50
        cx = SCREEN_W // 2
        self.slot_buttons = [pygame.Rect(cx - bw // 2, 140 + i * 65, bw, bh) for i in range(5)]
        self.back_btn = pygame.Rect(cx - 60, 140 + 5 * 65 + 10, 120, 40)

    def handle_event(self, event):
        all_btns = self.slot_buttons + ([self.back_btn] if self.back_btn else [])
        self.update_hover(event, all_btns)
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.game.switch_screen("title")
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.back_btn and self.back_btn.collidepoint(event.pos):
                self.game.switch_screen("title")
                return
            for i, btn in enumerate(self.slot_buttons):
                if btn.collidepoint(event.pos):
                    self._do_slot(i)


# ═══════════════════════════════════════════
# HUD DRAWING
# ═══════════════════════════════════════════

def draw_hud(surface, s, assets):
    """Draw the persistent HUD bar at the top with ornate styling."""
    # Background bar
    hud_h = 120
    hud_surf = pygame.Surface((SCREEN_W, hud_h), pygame.SRCALPHA)
    hud_surf.fill((12, 6, 24, 220))
    surface.blit(hud_surf, (0, 0))
    # Gold trim bottom border
    pygame.draw.line(surface, C.GOLD_TRIM, (10, hud_h - 2), (SCREEN_W - 10, hud_h - 2), 2)
    pygame.draw.line(surface, C.GOLD_DIM, (10, hud_h - 5), (SCREEN_W - 10, hud_h - 5), 1)

    # Class + Floor + Level
    icon = CLASS_ICONS.get(s.class_id, "?")
    class_color = CLASS_COLORS.get(s.class_id, C.YELLOW)
    draw_text(surface, f"{icon} {s.class_name}", assets.fonts["body"], class_color, 15, 8)
    depth_names = ["The Asylum", "The Depths Below", "The Descent", "Approaching the Threshold", "The Spiral"]
    depth_idx = min(s.floor * len(depth_names) // s.max_floor, len(depth_names) - 1)
    draw_text(surface, depth_names[depth_idx], assets.fonts["body"], C.YELLOW, 420, 8)
    draw_text(surface, f"Lv.{s.level}", assets.fonts["body"], C.BONE, 680, 8)

    # HP bar
    draw_text(surface, "HP", assets.fonts["small"], C.BONE, 15, 42)
    draw_bar(surface, 55, 42, 250, 20, s.hp, s.max_hp, hp_color(s.hp, s.max_hp))
    draw_text(surface, f"{s.hp}/{s.max_hp}", assets.fonts["tiny"],
              hp_color(s.hp, s.max_hp), 315, 44)
    if s.shield > 0:
        draw_text(surface, f"Shield:{int(s.shield)}", assets.fonts["tiny"], C.SHIELD_BLUE, 410, 44)

    # XP bar
    draw_text(surface, "XP", assets.fonts["small"], C.BONE, 15, 68)
    draw_bar(surface, 55, 68, 250, 14, s.xp, s.xp_next, C.XP_PURPLE)
    draw_text(surface, f"{s.xp}/{s.xp_next}", assets.fonts["tiny"], C.XP_PURPLE, 315, 68)

    # Stats
    stats_display = [
        ("INT", s.stats.get("int", 0), C.ELDRITCH),
        ("STR", s.stats.get("str", 0), C.CRIMSON),
        ("AGI", s.stats.get("agi", 0), C.MIST),
        ("WIS", s.stats.get("wis", 0), C.FROST),
        ("LUK", s.luck, C.YELLOW),
    ]
    x = 480
    for name, val, color in stats_display:
        draw_text(surface, f"{name}:{val}", assets.fonts["tiny"], color, x, 42)
        x += 60
    draw_text(surface, f"ATK:{s.atk} DEF:{s.defense}", assets.fonts["tiny"], C.ASH, x, 42)

    # Gold + Madness
    draw_text(surface, f"Gold: {s.gold}g", assets.fonts["small"], C.GOLD, 480, 68)
    draw_text(surface, f"Madness: {int(s.madness)}%", assets.fonts["small"],
              mad_color(s.madness), 620, 68)

    # Status effects
    statuses = []
    for st in s.statuses:
        statuses.append(f"{st.type.upper()}:{st.duration}")
    if s.barrier > 0:
        statuses.append(f"BARRIER:x{s.barrier}")
    if statuses:
        draw_text(surface, " ".join(statuses), assets.fonts["tiny"], C.MADNESS, 480, 92)


# ═══════════════════════════════════════════
# MAIN GAME CLASS
# ═══════════════════════════════════════════

class Game:
    def __init__(self):
        pygame.init()
        self.fullscreen = False
        try:
            self.screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
        except pygame.error as e:
            print(f"Display error: {e}")
            print("Try: export SDL_VIDEODRIVER=x11 (or wayland, windows, cocoa)")
            sys.exit(1)
        pygame.display.set_caption("The King in Yellow — A Lovecraftian Dungeon Crawler")
        self.clock = pygame.time.Clock()
        self.running = True

        self.assets = Assets()

        # Apply custom cursor if available
        if self.assets.cursor:
            try:
                pygame.mouse.set_cursor(self.assets.cursor)
            except Exception:
                pass  # Cursor format might not be supported on all platforms

        self.state = None

        # Shared state between screens
        self.gameover_msg = ""
        self.combat_result = {}
        self.pending_event = None
        self.shop_items = []
        self.shop_prices = []
        self.shop_sold = []
        self.shop_message = ""
        self.shop_msg_ok = True
        self.shop_msg_timer = 0
        self.trap_msg = ""
        self.trap_name = ""
        self.trap_desc = ""

        # Screens
        self.screens = {
            "title": TitleScreen(self),
            "class_select": ClassSelectScreen(self),
            "explore": ExploreScreen(self),
            "combat": CombatScreen(self),
            "inventory": InventoryScreen(self),
            "shop": ShopScreen(self),
            "rest": RestScreen(self),
            "loot": LootScreen(self),
            "event": EventScreen(self),
            "trap_result": TrapResultScreen(self),
            "combat_result": CombatResultScreen(self),
            "levelup": LevelUpScreen(self),
            "gameover": GameOverScreen(self),
            "victory": VictoryScreen(self),
            "save": SaveScreen(self),
            "load": LoadScreen(self),
            "stats": StatsScreen(self),
        }
        self.current_screen = self.screens["title"]
        self.current_screen.enter()

    def toggle_fullscreen(self):
        """Toggle between fullscreen and windowed mode."""
        self.fullscreen = not self.fullscreen
        if self.fullscreen:
            info = pygame.display.Info()
            self.screen = pygame.display.set_mode((info.current_w, info.current_h), pygame.FULLSCREEN)
        else:
            self.screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))

    def get_bg(self, screen_name=None):
        """Get context-appropriate background, scaled to current window size."""
        if screen_name is None:
            screen_name = getattr(self, '_current_screen_name', "title")
        floor = self.state.floor if self.state else 1
        max_floor = self.state.max_floor if self.state else 20
        bg = self.assets.get_background(floor, max_floor, screen_name)
        if bg:
            sw, sh = self.screen.get_size()
            bw, bh = bg.get_size()
            if bw != sw or bh != sh:
                bg = pygame.transform.scale(bg, (sw, sh))
        return bg

    def switch_screen(self, name):
        if name in self.screens:
            self._current_screen_name = name
            self.current_screen = self.screens[name]
            self.current_screen.enter()

    def run(self):
        while self.running:
            dt = self.clock.tick(FPS) / 1000.0

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_F11:
                    self.toggle_fullscreen()
                else:
                    self.current_screen.handle_event(event)

            self.current_screen.update(dt)

            # Draw background
            bg = self.get_bg()
            if bg:
                self.screen.blit(bg, (0, 0))
            else:
                self.screen.fill(C.DARK_BG)
            self.current_screen.draw(self.screen)

            pygame.display.flip()

        pygame.quit()


# ═══════════════════════════════════════════
# ENTRY POINT
# ═══════════════════════════════════════════

if __name__ == "__main__":
    try:
        game = Game()
        game.run()
    except Exception as e:
        import traceback
        print("\n" + "=" * 50)
        print("CRASH REPORT — The King in Yellow")
        print("=" * 50)
        traceback.print_exc()
        print("=" * 50)
        try:
            input("\nPress Enter to exit...")
        except EOFError:
            pass
    except KeyboardInterrupt:
        print("\n\nThe Yellow Sign fades. For now.")
        sys.exit(0)

"""
THE KING IN YELLOW — Asset Loader
Loads images, fonts, cursor. Handles fallbacks gracefully.
Uses the logging system instead of print() for all diagnostics.
"""

import os
import pygame
from shared.constants import (
    SCREEN_W,
    SCREEN_H,
    ASSETS_DIR,
    FONTS_DIR,
    C,
    CLASS_SPRITE_FILES,
    PATH_ICON_FILES,
)
from data import ENEMY_SPRITES, STAT_ICONS
from shared.logger import get_logger
from shared.surface_pool import render_cache

logger = get_logger("assets")


class Assets:
    def __init__(self):
        self.images = {}
        self.fonts = {}
        self.cursor = None
        self._font_paths = {}  # Store font file paths for dynamic scaling
        self._bg_cache: dict[str, pygame.Surface] = {}  # Cached darkened backgrounds
        try:
            self.load()
        except Exception as e:
            logger.critical("FATAL: Asset loading failed: %s", e, exc_info=True)
            raise

    def load(self):
        # --- Class sprites (for class select & combat) ---
        for class_id, filename in CLASS_SPRITE_FILES.items():
            path = os.path.join(ASSETS_DIR, filename)
            if os.path.exists(path):
                try:
                    img = pygame.image.load(path).convert_alpha()
                    self.images[f"class_{class_id}"] = img
                    self.images[f"class_{class_id}_combat"] = pygame.transform.scale(img, (220, 220))
                    self.images[f"class_{class_id}_thumb"] = pygame.transform.scale(img, (90, 90))
                    logger.debug("Class sprite loaded: %s (%dx%d)", class_id, img.get_width(), img.get_height())
                except Exception as e:
                    logger.warning("Failed to load class sprite: %s — %s", path, e)
            else:
                logger.warning("Class sprite not found: %s", path)

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
                    logger.warning("Failed to load enemy sprite: %s — %s", path, e)
            else:
                logger.warning("Enemy sprite not found: %s", path)

        # --- Backgrounds ---
        path = os.path.join(ASSETS_DIR, "Dungeon_background.jfif")
        if os.path.exists(path):
            try:
                img = pygame.image.load(path).convert()
                self.images["bg_dungeon"] = pygame.transform.scale(img, (SCREEN_W, SCREEN_H))
            except Exception as e:
                logger.warning("Failed to load dungeon background: %s", e)
        else:
            logger.warning("Dungeon background not found: %s", path)

        path = os.path.join(ASSETS_DIR, "Game_Over_Screen.jfif")
        if os.path.exists(path):
            try:
                img = pygame.image.load(path).convert()
                self.images["bg_gameover"] = pygame.transform.scale(img, (SCREEN_W, SCREEN_H))
            except Exception as e:
                logger.warning("Failed to load gameover background: %s", e)
        else:
            logger.warning("Gameover background not found: %s", path)

        path = os.path.join(ASSETS_DIR, "bg_boss.jpg")
        if os.path.exists(path):
            img = pygame.image.load(path).convert()
            self.images["bg_boss"] = pygame.transform.scale(img, (SCREEN_W, SCREEN_H))
        else:
            self.images["bg_boss"] = self.images.get("bg_dungeon")

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
                self.cursor = pygame.cursors.Cursor((0, 0), cursor_scaled)
                logger.debug("Custom cursor loaded")
            except Exception as e:
                logger.warning("Failed to load cursor: %s", e)

        # --- Text box sample ---
        path = os.path.join(ASSETS_DIR, "transparent-Text-box-Sample.png")
        if os.path.exists(path):
            try:
                img = pygame.image.load(path).convert_alpha()
                self.images["text_box_sample"] = img
            except Exception as e:
                logger.warning("Failed to load text box sample: %s", e)

        # --- Stat icons ---
        for stat_key, filename in STAT_ICONS.items():
            for size_suffix, size_px in [("32", 32), ("36", 36), ("48", 48), ("64", 64)]:
                path = os.path.join(ASSETS_DIR, f"{filename}_{size_suffix}.png")
                if os.path.exists(path):
                    try:
                        img = pygame.image.load(path).convert_alpha()
                        self.images[f"stat_{stat_key}_{size_suffix}"] = img
                    except Exception as e:
                        logger.warning("Failed to load stat icon: %s — %s", path, e)

        # --- Path choice icons ---
        for ptype, filename in PATH_ICON_FILES.items():
            path = os.path.join(ASSETS_DIR, filename)
            if os.path.exists(path):
                try:
                    img = pygame.image.load(path).convert_alpha()
                    self.images[f"path_{ptype}"] = pygame.transform.scale(img, (150, 150))
                    logger.debug("Path icon loaded: %s (%s)", ptype, filename)
                except Exception as e:
                    logger.warning("Failed to load path icon: %s — %s", path, e)
            else:
                logger.warning("Path icon not found: %s", path)

        # --- Fonts ---
        self._load_fonts()

    def _load_fonts(self):
        decor_path = os.path.join(FONTS_DIR, "CinzelDecorative-Regular.ttf")
        decor_bold_path = os.path.join(FONTS_DIR, "CinzelDecorative-Bold.ttf")
        cinzel_path = os.path.join(FONTS_DIR, "Cinzel.ttf")

        fallback_sizes = {
            "title": 60,
            "title_sm": 40,
            "heading": 30,
            "subheading": 28,
            "body": 24,
            "small": 20,
            "tiny": 17,
        }

        def _test_font(font_obj):
            try:
                surf = font_obj.render("Test", True, (255, 255, 255))
                return surf is not None
            except Exception:
                return False

        def _try_load_font(path, size, label):
            try:
                f = pygame.font.Font(path, size)
                if _test_font(f):
                    return f
                else:
                    logger.warning("Font loaded but cannot render: %s (size %d)", path, size)
                    return None
            except Exception as e:
                logger.warning("Font load error: %s — %s", path, e)
                return None

        try:
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
                    logger.info("Decorative font loaded: %s", decor_path)

            if not decor_loaded:
                if os.path.exists(decor_bold_path):
                    f_title = _try_load_font(decor_bold_path, 56, "title")
                    if f_title:
                        self.fonts["title"] = f_title
                        self.fonts["title_sm"] = _try_load_font(decor_bold_path, 36, "title_sm") or f_title
                        self.fonts["heading"] = _try_load_font(decor_bold_path, 28, "heading") or f_title
                        decor_loaded = True
                        logger.info("Decorative bold font loaded: %s", decor_bold_path)

            if not decor_loaded:
                logger.warning("No decorative font available, using system fallback")
                self.fonts["title"] = pygame.font.SysFont("serif", 62, bold=True)
                self.fonts["title_sm"] = pygame.font.SysFont("serif", 38, bold=True)
                self.fonts["heading"] = pygame.font.SysFont("serif", 32, bold=True)
        except Exception as e:
            logger.error("Decorative font section error: %s", e)

        try:
            cinzel_loaded = False
            if os.path.exists(cinzel_path):
                f_body = _try_load_font(cinzel_path, 22, "body")
                if f_body:
                    self.fonts["subheading"] = _try_load_font(cinzel_path, 26, "subheading") or f_body
                    self.fonts["body"] = f_body
                    self.fonts["small"] = _try_load_font(cinzel_path, 18, "small") or f_body
                    self.fonts["tiny"] = _try_load_font(cinzel_path, 15, "tiny") or f_body
                    cinzel_loaded = True
                    logger.info("Body font loaded: %s", cinzel_path)

            if not cinzel_loaded:
                logger.warning("No body font available, using system fallback")
                self.fonts["subheading"] = pygame.font.SysFont("georgia", 28, bold=True)
                self.fonts["body"] = pygame.font.SysFont("georgia", 22)
                self.fonts["small"] = pygame.font.SysFont("georgia", 18)
                self.fonts["tiny"] = pygame.font.SysFont("georgia", 15)
        except Exception as e:
            logger.error("Body font section error: %s", e)

        # Final fallback
        for key, size in fallback_sizes.items():
            if key not in self.fonts or self.fonts[key] is None or not _test_font(self.fonts[key]):
                try:
                    fallback = pygame.font.Font(None, size)
                    if _test_font(fallback):
                        self.fonts[key] = fallback
                        logger.debug("Font '%s' using emergency default", key)
                    else:
                        self.fonts[key] = pygame.font.SysFont("arial", size)
                        logger.debug("Font '%s' using arial fallback", key)
                except Exception:
                    self.fonts[key] = pygame.font.SysFont("arial", size)
                    logger.debug("Font '%s' using arial fallback (last resort)", key)

        # ── Eldritch Combat Fonts ──
        # Slender Victorian serif for menacing, elegant damage numbers
        try:
            # Use DejaVu Serif Condensed for a slender, elegant, Victorian look
            eld_path = "/usr/share/fonts/truetype/dejavu/DejaVuSerifCondensed-Bold.ttf"
            if os.path.exists(eld_path):
                self._font_paths["eldritch"] = eld_path
                self.fonts["eldritch_crit"] = _try_load_font(eld_path, 28, "eldritch_crit") or self.fonts.get("heading")
                self.fonts["eldritch"] = _try_load_font(eld_path, 22, "eldritch") or self.fonts.get("heading")
                self.fonts["eldritch_rune"] = _try_load_font(eld_path, 12, "eldritch_rune") or self.fonts.get("small")
                logger.debug("Victorian combat fonts loaded from %s", eld_path)
            else:
                # Fallback to Cinzel Decorative Bold if condensed serif unavailable
                eld_path = decor_bold_path if os.path.exists(decor_bold_path) else None
                if eld_path:
                    self._font_paths["eldritch"] = eld_path
                    self.fonts["eldritch_crit"] = _try_load_font(eld_path, 28, "eldritch_crit") or self.fonts.get(
                        "heading"
                    )
                    self.fonts["eldritch"] = _try_load_font(eld_path, 22, "eldritch") or self.fonts.get("heading")
                    self.fonts["eldritch_rune"] = _try_load_font(eld_path, 12, "eldritch_rune") or self.fonts.get(
                        "small"
                    )
                    logger.debug("Combat fonts loaded from %s", eld_path)
                else:
                    self._font_paths["eldritch"] = None
                    self.fonts["eldritch_crit"] = self.fonts.get("heading")
                    self.fonts["eldritch"] = self.fonts.get("heading")
                    self.fonts["eldritch_rune"] = self.fonts.get("small")
                    logger.debug("Combat fonts using heading fallback")
        except Exception as e:
            logger.warning("Combat font error: %s", e)
            self.fonts["eldritch_crit"] = self.fonts.get("heading")
            self.fonts["eldritch"] = self.fonts.get("heading")
            self.fonts["eldritch_rune"] = self.fonts.get("small")

    def get_background(self, floor=1, max_floor=20, screen="explore"):
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

        # Cache the darkened background by screen type
        cache_key = f"bg_{screen}"
        cached = self._bg_cache.get(cache_key)
        if cached is not None:
            return cached

        overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        if screen == "gameover":
            overlay.fill((0, 0, 0, 100))
        else:
            overlay.fill((0, 0, 0, 140))
        result = bg.copy()
        result.blit(overlay, (0, 0))
        self._bg_cache[cache_key] = result
        return result

    def get_sprite(self, enemy_name):
        sprite_key = ENEMY_SPRITES.get(enemy_name)
        if sprite_key:
            return self.images.get(f"{sprite_key}_combat")
        return None

    def get_class_sprite(self, class_id, size="combat"):
        key = f"class_{class_id}_{size}"
        return self.images.get(key)

    def get_class_combat(self, class_id):
        return self.images.get(f"class_{class_id}_combat")

#!/usr/bin/env python3
"""
THE KING IN YELLOW — Pygame Graphical Edition (Visual Overhaul)
A Lovecraftian Dungeon Crawler with custom art assets.
"""

import os
import sys
import random

os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "1"
import pygame

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from shared.logger import configure_logging, get_logger, shutdown as shutdown_logging
from shared.game_context import GameContext
from shared.transitions import TransitionType, get_transition_for, get_transition_durations, render_transition
from config import get_settings

# ═══════════════════════════════════════════
# EARLY INITIALIZATION
# ═══════════════════════════════════════════

# Load settings and configure logging BEFORE importing heavy modules
settings = get_settings()

configure_logging(
    level=settings.get("logging.level", "INFO"),
    log_to_file=settings.get("logging.log_to_file", False),
    log_file=settings.get("logging.log_file", "logs/game.log"),
    console_format=settings.get("logging.console_format"),
    file_format=settings.get("logging.file_format"),
)

logger = get_logger("main")

# Now import game modules (they will use the configured logger)
from shared import (
    C,
    SCREEN_W,
    SCREEN_H,
    FPS,
    Assets,
    draw_hud,
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
    CLASS_COLORS,
    CLASS_ICONS,
)
from screens import (
    Screen,
    ScreenName,
    TitleScreen,
    ClassSelectScreen,
    ExploreScreen,
    CombatScreen,
    InventoryScreen,
    ShopScreen,
    RestScreen,
    LootScreen,
    EventScreen,
    TrapResultScreen,
    CombatResultScreen,
    LevelUpScreen,
    GameOverScreen,
    VictoryScreen,
    StatsScreen,
    SaveScreen,
    LoadScreen,
)

# ═══════════════════════════════════════════
# MAIN GAME CLASS
# ═══════════════════════════════════════════


class Game:
    def __init__(self):
        logger.info("The King in Yellow — Initializing...")

        pygame.init()

        # Read display settings from config
        self.fullscreen = settings.get("display.fullscreen", False)

        try:
            if self.fullscreen:
                info = pygame.display.Info()
                self.screen = pygame.display.set_mode((info.current_w, info.current_h), pygame.FULLSCREEN)
                logger.info("Display: fullscreen mode (%dx%d)", info.current_w, info.current_h)
            else:
                screen_w = settings.get("display.screen_width", SCREEN_W)
                screen_h = settings.get("display.screen_height", SCREEN_H)
                self.screen = pygame.display.set_mode((screen_w, screen_h))
                logger.info("Display: windowed mode (%dx%d)", screen_w, screen_h)
        except pygame.error as e:
            logger.error("Display initialization failed: %s", e)
            logger.error("Try: export SDL_VIDEODRIVER=x11 (or wayland, windows, cocoa)")
            sys.exit(1)

        pygame.display.set_caption("The King in Yellow — A Lovecraftian Dungeon Crawler")

        fps = settings.get("display.fps", FPS)
        self.clock = pygame.time.Clock()
        self.running = True

        # Load assets
        logger.info("Loading assets...")
        self.assets = Assets()
        logger.info("Assets loaded successfully")

        # Track total game time for animations
        self.time_seconds = 0.0

        # Apply custom cursor if available
        if self.assets.cursor:
            try:
                pygame.mouse.set_cursor(self.assets.cursor)
                logger.debug("Custom cursor applied")
            except Exception:
                logger.debug("Custom cursor not supported on this platform")

        self.state = None

        # ── Service Locator / Dependency Injection ─────────────────────────
        # Create a GameContext that decouples screens from this Game class.
        # Screens receive the context instead of a direct Game reference,
        # enabling unit testing without instantiating the full game.
        self.ctx = GameContext(
            get_state=lambda: self.state,
            set_state=lambda s: setattr(self, "state", s),
            assets=self.assets,
            navigate_callback=self.switch_screen,
            toggle_fullscreen_callback=self.toggle_fullscreen,
            quit_callback=lambda: setattr(self, "running", False),
            get_prev_screen=lambda: getattr(self, "_prev_screen_name", None),
            get_time_seconds=lambda: self.time_seconds,
            get_fullscreen=lambda: self.fullscreen,
        )

        # Screens — keyed by ScreenName enum for type safety
        # Each screen now receives the GameContext instead of the Game instance
        self.screens = {
            ScreenName.TITLE: TitleScreen(self.ctx),
            ScreenName.CLASS_SELECT: ClassSelectScreen(self.ctx),
            ScreenName.EXPLORE: ExploreScreen(self.ctx),
            ScreenName.COMBAT: CombatScreen(self.ctx),
            ScreenName.INVENTORY: InventoryScreen(self.ctx),
            ScreenName.SHOP: ShopScreen(self.ctx),
            ScreenName.REST: RestScreen(self.ctx),
            ScreenName.LOOT: LootScreen(self.ctx),
            ScreenName.EVENT: EventScreen(self.ctx),
            ScreenName.TRAP_RESULT: TrapResultScreen(self.ctx),
            ScreenName.COMBAT_RESULT: CombatResultScreen(self.ctx),
            ScreenName.LEVELUP: LevelUpScreen(self.ctx),
            ScreenName.GAMEOVER: GameOverScreen(self.ctx),
            ScreenName.VICTORY: VictoryScreen(self.ctx),
            ScreenName.SAVE: SaveScreen(self.ctx),
            ScreenName.LOAD: LoadScreen(self.ctx),
            ScreenName.STATS: StatsScreen(self.ctx),
        }
        self.current_screen = self.screens[ScreenName.TITLE]
        self.current_screen.enter()

        # ── Context-aware screen transitions ──
        self.transition = None          # None, "fadeOut", "fadeIn"
        self.transition_timer = 0
        self.transition_out_duration = 0.25  # overwritten per-type
        self.transition_in_duration = 0.25
        self.transition_type = TransitionType.FADE_BLACK
        self._pending_screen = None

        logger.info("Game initialized — entering title screen")

    def toggle_fullscreen(self):
        """Toggle between fullscreen and windowed mode."""
        self.fullscreen = not self.fullscreen
        if self.fullscreen:
            info = pygame.display.Info()
            self.screen = pygame.display.set_mode((info.current_w, info.current_h), pygame.FULLSCREEN)
            logger.info("Switched to fullscreen (%dx%d)", info.current_w, info.current_h)
        else:
            screen_w = settings.get("display.screen_width", SCREEN_W)
            screen_h = settings.get("display.screen_height", SCREEN_H)
            self.screen = pygame.display.set_mode((screen_w, screen_h))
            logger.info("Switched to windowed (%dx%d)", screen_w, screen_h)

        # Recreate transition surface for new size
        sw, sh = self.screen.get_size()
        self._transition_surface = pygame.Surface((sw, sh), pygame.SRCALPHA)

    def get_bg(self, screen_name=None):
        """Get context-appropriate background, scaled to current window size."""
        if screen_name is None:
            screen_name = getattr(self, "_current_screen_name", ScreenName.TITLE)
        floor = self.state.floor if self.state else 1
        max_floor = self.state.max_floor if self.state else 20
        bg = self.assets.get_background(floor, max_floor, screen_name)
        if bg:
            sw, sh = self.screen.get_size()
            bw, bh = bg.get_size()
            if bw != sw or bh != sh:
                bg = pygame.transform.scale(bg, (sw, sh))
        return bg

    def switch_screen(self, name: ScreenName):
        """Transition to the screen identified by *name* (a ``ScreenName`` enum).

        The transition type is determined automatically based on the source
        and target screens.  Three clean effects are available:
        - FADE_BLACK: general navigation
        - MENU_REVEAL: inventory, shop, save/load, stats
        - COMBAT_DIVE: entering combat

        Parameters
        ----------
        name:
            The target screen.  Must be a :class:`ScreenName` member.
        """
        if name not in self.screens:
            logger.warning("Attempted to switch to unknown screen: %s", name)
            return
        if self.transition is not None:
            self._finish_transition(name)
            return

        # Determine context-aware transition type and per-type durations
        current_name = getattr(self, "_current_screen_name", ScreenName.TITLE)
        self.transition_type = get_transition_for(current_name, name)
        out_dur, in_dur = get_transition_durations(self.transition_type)
        self.transition_out_duration = out_dur
        self.transition_in_duration = in_dur

        self.transition = "fadeOut"
        self.transition_timer = 0
        self._pending_screen = name
        logger.debug("Screen transition: %s → %s [%s]",
                      current_name.value, name.value, self.transition_type.value)

    def _finish_transition(self, name=None):
        """Immediately complete a pending or forced transition."""
        target = name or self._pending_screen
        if target and target in self.screens:
            self._prev_screen_name = getattr(self, "_current_screen_name", ScreenName.TITLE)
            self._current_screen_name = target
            self.current_screen = self.screens[target]
            self.current_screen.enter()
            logger.debug("Screen entered: %s", target.value)
        self.transition = None
        self.transition_timer = 0
        self._pending_screen = None

    def run(self):
        fps = settings.get("display.fps", FPS)
        while self.running:
            dt = self.clock.tick(fps) / 1000.0

            # Handle transition timing
            if self.transition:
                self.transition_timer += dt
                if self.transition == "fadeOut" and self.transition_timer >= self.transition_out_duration:
                    # Fade-out complete — switch screen and start fade-in
                    self._finish_transition()
                    self.transition = "fadeIn"
                    self.transition_timer = 0
                elif self.transition == "fadeIn" and self.transition_timer >= self.transition_in_duration:
                    # Fade-in complete
                    self.transition = None
                    self.transition_timer = 0

            # During fade-out block input to the old screen
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_F11:
                    self.toggle_fullscreen()
                elif not self.transition:
                    self.current_screen.handle_event(event)

            if not self.transition or self.transition == "fadeIn":
                self.current_screen.update(dt)

            # Update total game time for animations
            self.time_seconds += dt

            # Draw background
            bg = self.get_bg()
            if bg:
                self.screen.blit(bg, (0, 0))
            else:
                self.screen.fill(C.DARK_BG)
            self.current_screen.draw(self.screen)

            # Draw context-aware transition overlay
            if self.transition:
                if self.transition == "fadeOut":
                    progress = min(1.0, self.transition_timer / self.transition_out_duration)
                else:
                    progress = min(1.0, self.transition_timer / self.transition_in_duration)
                render_transition(
                    surface=self.screen,
                    transition_type=self.transition_type,
                    phase=self.transition,
                    progress=progress,
                    time_seconds=self.time_seconds,
                )

            pygame.display.flip()

        logger.info("Game loop ended — shutting down")
        pygame.quit()
        shutdown_logging()


# ═══════════════════════════════════════════
# ENTRY POINT
# ═══════════════════════════════════════════

if __name__ == "__main__":
    try:
        game = Game()
        game.run()
    except Exception as e:
        import traceback

        logger.critical("CRASH REPORT — The King in Yellow")
        logger.critical("Fatal exception: %s", e, exc_info=True)
        try:
            input("\nPress Enter to exit...")
        except EOFError:
            pass
        shutdown_logging()
    except KeyboardInterrupt:
        logger.info("The Yellow Sign fades. For now.")
        shutdown_logging()
        sys.exit(0)

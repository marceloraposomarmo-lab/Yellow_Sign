import pygame
from shared import (
    C,
    SCREEN_W,
    SCREEN_H,
    Assets,
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
)
from shared.game_context import GameContext


class Screen:
    def __init__(self, ctx: GameContext):
        self.ctx = ctx
        self.assets = ctx.assets
        self.hover_idx = -1  # which button/option is currently hovered (-1 = none)

    def enter(self):
        self.hover_idx = -1

    def handle_event(self, event):
        pass

    def update(self, dt):
        pass

    def draw(self, surface):
        pass

    # ── Audio helpers ─────────────────────────────────────────────────────────

    def _play_sound(self, name: str, volume: float = None) -> None:
        """Play a UI sound effect via the audio manager (no-op if unavailable)."""
        if self.ctx.audio:
            self.ctx.audio.play(name, volume=volume)

    def play_click(self) -> None:
        """Play the button click sound."""
        self._play_sound("click")

    def play_confirm(self) -> None:
        """Play the confirm/accept sound."""
        self._play_sound("confirm")

    def play_cancel(self) -> None:
        """Play the cancel/back sound."""
        self._play_sound("cancel")

    def play_error(self) -> None:
        """Play the error/invalid sound."""
        self._play_sound("error")

    def play_game_over(self) -> None:
        """Play the game over sound."""
        self._play_sound("game_over")

    def play_level_up(self) -> None:
        """Play the level up sound."""
        self._play_sound("level_up")

    def play_transition(self) -> None:
        """Play the screen transition sound."""
        self._play_sound("transition")

    def play_boss_start(self) -> None:
        """Play the boss encounter start sound."""
        self._play_sound("boss_start")

    def play_loot(self) -> None:
        """Play the loot/chest opening sound."""
        self._play_sound("loot")

    def play_equip(self) -> None:
        """Play the weapon/item equip sound."""
        self._play_sound("equip")

    def play_purchase(self) -> None:
        """Play the shop purchase/transaction sound."""
        self._play_sound("purchase")

    def play_combat_start(self) -> None:
        """Play the ominous combat encounter sound."""
        self._play_sound("combat_start")

    def play_event_mystery(self) -> None:
        """Play the mysterious event discovery sound."""
        self._play_sound("event_mystery")

    def play_trap_trigger(self) -> None:
        """Play the ominous trap activation sound."""
        self._play_sound("trap_trigger")

    # ── Music helpers ─────────────────────────────────────────────────────────

    def play_music(self, context: str, fade_ms: int = 1000) -> None:
        """Start background music for a context (no-op if unavailable)."""
        if self.ctx.audio:
            self.ctx.audio.play_music(context, fade_ms=fade_ms)

    def stop_music(self, fade_ms: int = 1000) -> None:
        """Fade out and stop background music (no-op if unavailable)."""
        if self.ctx.audio:
            self.ctx.audio.stop_music(fade_ms=fade_ms)

    def crossfade_music(self, context: str, fade_ms: int = 2000) -> None:
        """Crossfade to a new music context (no-op if unavailable)."""
        if self.ctx.audio:
            self.ctx.audio.crossfade_music(context, fade_ms=fade_ms)

    # ── Hover tracking ────────────────────────────────────────────────────────

    def update_hover(self, event, buttons):
        """Track hover state from a list of pygame.Rect buttons. Call in handle_event().

        Updates visual hover state only — no sound on hover.
        """
        if event.type == pygame.MOUSEMOTION:
            self.hover_idx = -1
            for i, btn in enumerate(buttons):
                if btn.collidepoint(event.pos):
                    self.hover_idx = i
                    break
        elif event.type == pygame.WINDOWLEAVE:
            self.hover_idx = -1

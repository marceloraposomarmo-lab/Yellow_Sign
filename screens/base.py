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

    def _play_sound(self, name: str) -> None:
        """Play a UI sound effect via the audio manager (no-op if unavailable)."""
        if self.ctx.audio:
            self.ctx.audio.play(name)

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

    # ── Hover tracking ────────────────────────────────────────────────────────

    def update_hover(self, event, buttons):
        """Track hover state from a list of pygame.Rect buttons. Call in handle_event().

        Automatically plays a hover sound when the hovered button changes.
        """
        if event.type == pygame.MOUSEMOTION:
            old_idx = self.hover_idx
            self.hover_idx = -1
            for i, btn in enumerate(buttons):
                if btn.collidepoint(event.pos):
                    self.hover_idx = i
                    break
            if self.hover_idx != old_idx and self.hover_idx >= 0:
                self._play_sound("hover")
        elif event.type == pygame.WINDOWLEAVE:
            self.hover_idx = -1

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

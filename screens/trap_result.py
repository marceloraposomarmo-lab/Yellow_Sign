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
from screens.base import Screen
from screens.screen_enum import ScreenName


class TrapResultScreen(Screen):
    def __init__(self, ctx):
        super().__init__(ctx)
        self.continue_btn = None

    def handle_event(self, event):
        self.update_hover(event, [self.continue_btn] if self.continue_btn else [])
        if event.type == pygame.KEYDOWN or (
            event.type == pygame.MOUSEBUTTONDOWN and self.continue_btn and self.continue_btn.collidepoint(event.pos)
        ):
            self.play_confirm()
            self.ctx.navigate(ScreenName.EXPLORE)

    def draw(self, surface):
        panel_w, panel_h = 500, 180
        panel_x = SCREEN_W // 2 - panel_w // 2
        draw_parchment_panel(surface, panel_x, 200, panel_w, panel_h)

        draw_text_with_glow(
            surface,
            f"TRAP: {self.ctx.screen_data['trap_name']}",
            self.assets.fonts["heading"],
            C.CRIMSON,
            SCREEN_W // 2,
            215,
            align="center",
        )
        draw_text_with_glow(
            surface,
            self.ctx.screen_data["trap_desc"],
            self.assets.fonts["small"],
            C.INK_LIGHT,
            SCREEN_W // 2,
            252,
            align="center",
        )
        draw_gold_divider(surface, SCREEN_W // 2 - 150, 270, 300)
        draw_text_wrapped_glow(
            surface, self.ctx.screen_data["trap_msg"], self.assets.fonts["body"], C.INK, SCREEN_W // 2 - 220, 285, 440
        )

        self.continue_btn = pygame.Rect(SCREEN_W // 2 - 80, 345, 160, 35)
        draw_ornate_button(
            surface,
            self.continue_btn,
            "Continue",
            self.assets.fonts["small"],
            hover=(self.hover_idx == 0),
            color=C.PARCHMENT_EDGE,
        )

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


class GameOverScreen(Screen):
    def __init__(self, ctx):
        super().__init__(ctx)
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
                self.play_click()
                self.ctx.navigate(ScreenName.CLASS_SELECT)
            elif self.menu_btn and self.menu_btn.collidepoint(event.pos):
                self.play_click()
                self.ctx.navigate(ScreenName.TITLE)
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_r:
                self.play_click()
                self.ctx.navigate(ScreenName.CLASS_SELECT)
            elif event.key == pygame.K_q:
                self.play_click()
                self.ctx.navigate(ScreenName.TITLE)

    def draw(self, surface):
        # The Game_Over_Screen background is already drawn by main loop
        draw_text_with_glow(
            surface, "GAME OVER", self.assets.fonts["title"], C.CRIMSON, SCREEN_W // 2, 40, align="center"
        )
        draw_gold_divider(surface, SCREEN_W // 2 - 180, 120, 360)
        draw_text_wrapped_glow(
            surface,
            self.ctx.screen_data["gameover_msg"],
            self.assets.fonts["body"],
            C.INK,
            SCREEN_W // 2 - 300,
            140,
            600,
        )

        cx = SCREEN_W // 2
        self.restart_btn = pygame.Rect(cx - 170, 300, 160, 45)
        self.menu_btn = pygame.Rect(cx + 10, 300, 160, 45)
        draw_ornate_button(
            surface,
            self.restart_btn,
            "[R] Retry",
            self.assets.fonts["body"],
            hover=(0 == self.hover_idx),
            color=C.PARCHMENT_EDGE,
        )
        draw_ornate_button(
            surface,
            self.menu_btn,
            "[Q] Menu",
            self.assets.fonts["body"],
            hover=(1 == self.hover_idx),
            color=C.PARCHMENT_EDGE,
        )

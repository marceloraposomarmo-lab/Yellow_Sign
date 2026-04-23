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


class VictoryScreen(Screen):
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
        s = self.ctx.state

        # Boss sprite
        boss_sprite = self.assets.get_sprite("Hastur, The Spiral Beyond")
        if boss_sprite:
            surface.blit(boss_sprite, (SCREEN_W // 2 - boss_sprite.get_width() // 2, 90))

        draw_text_with_glow(
            surface, "VICTORY", self.assets.fonts["title"], C.PARCHMENT_EDGE, SCREEN_W // 2, 25, align="center"
        )
        draw_text_with_glow(
            surface,
            "You emerge into pale dawn light.",
            self.assets.fonts["body"],
            C.INK,
            SCREEN_W // 2,
            340,
            align="center",
        )

        if s.madness > 70:
            mt = "But your mind is fractured. Carcosa follows in your dreams."
        elif s.madness > 40:
            mt = "Your mind holds, barely. The scars will never fully heal."
        else:
            mt = "Against all odds, your mind remains whole. The Spiral is unraveled. For now."
        draw_text_wrapped_glow(surface, mt, self.assets.fonts["small"], C.INK, SCREEN_W // 2 - 300, 370, 600)

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
            draw_text_with_glow(
                surface, f"{label}:", self.assets.fonts["body"], C.INK_LIGHT, SCREEN_W // 2 - 90, y, align="right"
            )
            color = mad_color(s.madness) if label == "Madness" else C.PARCHMENT_EDGE if label == "Gold" else C.INK
            draw_text_with_glow(surface, value, self.assets.fonts["body"], color, SCREEN_W // 2 + 10, y)
            y += 30

        cx = SCREEN_W // 2
        self.restart_btn = pygame.Rect(cx - 170, 625, 160, 45)
        self.menu_btn = pygame.Rect(cx + 10, 625, 160, 45)
        draw_ornate_button(
            surface,
            self.restart_btn,
            "[R] Play Again",
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

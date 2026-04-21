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
from screens.base import Screen
from screens.screen_enum import ScreenName
from data import RARITY_DATA
from engine import generate_shop, buy_shop_item, advance_floor


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
                    self.game.switch_screen(ScreenName.VICTORY)
                else:
                    self.game.switch_screen(ScreenName.EXPLORE)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for i, btn in enumerate(self.buy_buttons):
                if btn.collidepoint(event.pos) and i < len(self.game.shop_items):
                    ok, msg = buy_shop_item(s, self.game.shop_items, self.game.shop_prices, self.game.shop_sold, i)
                    self.game.shop_message = msg
                    self.game.shop_msg_ok = ok
                    self.game.shop_msg_timer = 1.5
            if self.leave_btn and self.leave_btn.collidepoint(event.pos):
                if advance_floor(s):
                    self.game.switch_screen(ScreenName.VICTORY)
                else:
                    self.game.switch_screen(ScreenName.EXPLORE)

    def draw(self, surface):
        s = self.game.state

        draw_parchment_panel(surface, 30, 10, SCREEN_W - 60, SCREEN_H - 80)
        draw_text_with_glow(
            surface, "THE MAD TRADER", self.assets.fonts["heading"], C.PARCHMENT_EDGE, SCREEN_W // 2, 22, align="center"
        )
        draw_text_with_glow(
            surface,
            '"Everything has a price. Especially knowledge."',
            self.assets.fonts["tiny"],
            C.INK_LIGHT,
            SCREEN_W // 2,
            58,
            align="center",
        )
        draw_text_with_glow(
            surface, f"Gold: {s.gold}", self.assets.fonts["body"], C.PARCHMENT_EDGE, SCREEN_W // 2, 80, align="center"
        )
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
            draw_panel(
                surface, 55, y, SCREEN_W - 120, card_h, C.PANEL_BG, C.CRIMSON if sold else C.GOLD_DIM, 1 if sold else 2
            )

            # Line 1: item name — pixel-width truncated to leave room for price
            name_text = f"{item.name} ({item.slot.upper()}, {rd['name']})"
            if sold:
                name_text += " SOLD"
            name_max_w = SCREEN_W - 200  # leave ~130px for price on right + margins
            draw_text_fitted_glow(
                surface, name_text, self.assets.fonts["body"], color if not sold else C.INK_LIGHT, 70, y + 6, name_max_w
            )

            # Line 2: stats
            stat_text = item.stat_text()
            draw_text_fitted_glow(surface, stat_text, self.assets.fonts["tiny"], C.INK, 70, y + 34, SCREEN_W - 200)

            # Line 3: debuffs (separate line below stats)
            if item.debuffs:
                draw_text_fitted_glow(
                    surface, item.debuff_text(), self.assets.fonts["tiny"], C.CRIMSON, 70, y + 56, SCREEN_W - 200
                )

            # Price on the right (vertically centered in card)
            draw_text_with_glow(
                surface,
                f"{self.game.shop_prices[i]}g",
                self.assets.fonts["body"],
                C.PARCHMENT_EDGE,
                SCREEN_W - 75,
                y + card_h // 2 - 11,
                align="right",
            )
            y += card_h + 10

        self.leave_btn = pygame.Rect(SCREEN_W // 2 - 80, y + 15, 160, 45)
        leave_hover = len(self.buy_buttons) == self.hover_idx
        draw_ornate_button(
            surface, self.leave_btn, "Leave Shop", self.assets.fonts["body"], hover=leave_hover, color=C.PARCHMENT_EDGE
        )

        if hasattr(self.game, "shop_msg_timer") and self.game.shop_msg_timer > 0:
            color = C.MIST if self.game.shop_msg_ok else C.CRIMSON
            draw_text_with_glow(
                surface, self.game.shop_message, self.assets.fonts["body"], color, SCREEN_W // 2, y + 75, align="center"
            )

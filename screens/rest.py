import pygame
from shared import (
    C,
    SCREEN_W,
    SCREEN_H,
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
)
from screens.base import Screen
from screens.screen_enum import ScreenName
from engine import advance_floor


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
                    self.game.switch_screen(ScreenName.VICTORY)
                else:
                    self.game.switch_screen(ScreenName.EXPLORE)

    def draw(self, surface):
        draw_hud(surface, self.game.state, self.assets)

        panel_w, panel_h = 500, 200
        panel_x = SCREEN_W // 2 - panel_w // 2
        draw_parchment_panel(surface, panel_x, 135, panel_w, panel_h)

        draw_text_with_glow(
            surface,
            "A MOMENT OF RESPITE",
            self.assets.fonts["heading"],
            C.PARCHMENT_EDGE,
            SCREEN_W // 2,
            145,
            align="center",
        )
        draw_text_with_glow(
            surface,
            "You find a quiet corner. The madness recedes, briefly.",
            self.assets.fonts["tiny"],
            C.INK,
            SCREEN_W // 2,
            185,
            align="center",
        )

        for i, (name, desc, _) in enumerate(self.options):
            draw_ornate_button(
                surface,
                self.buttons[i],
                f"[{i+1}] {name} — {desc}",
                self.assets.fonts["body"],
                hover=(i == self.hover_idx),
                color=C.PARCHMENT_EDGE,
            )

        if self.result_msg:
            draw_text_with_glow(
                surface, self.result_msg, self.assets.fonts["body"], C.MIST, SCREEN_W // 2, 560, align="center"
            )

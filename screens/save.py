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
from save_system import save_game, load_game, list_saves


class SaveScreen(Screen):
    def __init__(self, game):
        super().__init__(game)
        self.slot_buttons = []
        self.back_btn = None
        self.mode = "save"
        self.prev_screen = ScreenName.EXPLORE

    def enter(self):
        self.mode = "save" if self.game.state else "load"
        # Track where we came from (set by switch_screen before enter() is called)
        self.prev_screen = getattr(self.game, "_prev_screen_name", ScreenName.EXPLORE)
        if self.game.state and self.game.state.combat:
            self.prev_screen = ScreenName.COMBAT
        elif not self.game.state:
            self.prev_screen = ScreenName.TITLE
        bw, bh = 400, 50
        cx = SCREEN_W // 2
        self.slot_buttons = [pygame.Rect(cx - bw // 2, 140 + i * 65, bw, bh) for i in range(5)]
        self.back_btn = pygame.Rect(cx - 60, 140 + 5 * 65 + 10, 120, 40)

    def _get_return_screen(self):
        """Return to the correct screen after save/load actions."""
        if self.game.state and self.game.state.combat:
            return ScreenName.COMBAT
        return self.prev_screen

    def handle_event(self, event):
        all_btns = self.slot_buttons + ([self.back_btn] if self.back_btn else [])
        self.update_hover(event, all_btns)
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.game.switch_screen(self._get_return_screen())
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.back_btn and self.back_btn.collidepoint(event.pos):
                self.game.switch_screen(self._get_return_screen())
                return
            for i, btn in enumerate(self.slot_buttons):
                if btn.collidepoint(event.pos):
                    self._do_slot(i)

    def _do_slot(self, slot):
        s = self.game.state
        if self.mode == "save" and s:
            save_game(s, slot)
            self.game.switch_screen(self._get_return_screen())
        else:
            loaded = load_game(slot)
            if loaded:
                self.game.state = loaded
                self.game.switch_screen(ScreenName.EXPLORE)

    def draw(self, surface):
        saves = list_saves()

        title = "SAVE GAME" if self.mode == "save" else "LOAD GAME"
        panel_w, panel_h = 500, 430
        panel_x = SCREEN_W // 2 - panel_w // 2
        draw_parchment_panel(surface, panel_x, 20, panel_w, panel_h)
        draw_text_with_glow(
            surface, title, self.assets.fonts["heading"], C.PARCHMENT_EDGE, SCREEN_W // 2, 35, align="center"
        )
        draw_gold_divider(surface, SCREEN_W // 2 - 120, 68, 240)

        for i, (sv, btn) in enumerate(zip(saves, self.slot_buttons)):
            if sv.get("empty"):
                label = f"Slot {sv['slot']}: — empty —"
                color = C.INK_LIGHT
            elif sv.get("error"):
                label = f"Slot {sv['slot']}: Corrupted"
                color = C.CRIMSON
            else:
                label = f"Slot {sv['slot']}: {sv['class_name']} Lv.{sv['level']} Floor {sv['floor']}"
                color = C.INK
            draw_ornate_button(surface, btn, label, self.assets.fonts["body"], hover=(i == self.hover_idx), color=color)

        draw_ornate_button(
            surface,
            self.back_btn,
            "Back",
            self.assets.fonts["body"],
            hover=(len(self.slot_buttons) == self.hover_idx),
            color=C.PARCHMENT_EDGE,
        )


class LoadScreen(SaveScreen):
    def enter(self):
        self.mode = "load"
        bw, bh = 400, 50
        cx = SCREEN_W // 2
        self.slot_buttons = [pygame.Rect(cx - bw // 2, 140 + i * 65, bw, bh) for i in range(5)]
        self.back_btn = pygame.Rect(cx - 60, 140 + 5 * 65 + 10, 120, 40)

    def handle_event(self, event):
        all_btns = self.slot_buttons + ([self.back_btn] if self.back_btn else [])
        self.update_hover(event, all_btns)
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.game.switch_screen(ScreenName.TITLE)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.back_btn and self.back_btn.collidepoint(event.pos):
                self.game.switch_screen(ScreenName.TITLE)
                return
            for i, btn in enumerate(self.slot_buttons):
                if btn.collidepoint(event.pos):
                    self._do_slot(i)

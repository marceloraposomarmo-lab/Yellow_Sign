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
from engine import advance_floor


class CombatResultScreen(Screen):
    def __init__(self, game):
        super().__init__(game)
        self.equip_btn = None
        self.backpack_btn = None
        self.chosen = False

    def enter(self):
        self.chosen = False

    def handle_event(self, event):
        s = self.game.state
        r = self.game.combat_result
        if self.chosen:
            if event.type == pygame.KEYDOWN or (event.type == pygame.MOUSEBUTTONDOWN):
                if r["is_boss"]:
                    self.game.switch_screen(ScreenName.VICTORY)
                elif advance_floor(s):
                    self.game.switch_screen(ScreenName.VICTORY)
                else:
                    self.game.switch_screen(ScreenName.EXPLORE)
            return

        btns = []
        if self.equip_btn:
            btns.append(self.equip_btn)
        if self.backpack_btn:
            btns.append(self.backpack_btn)
        self.update_hover(event, btns)

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_1:
                self._equip_loot()
            elif event.key == pygame.K_2:
                self._store_loot()
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.equip_btn and self.equip_btn.collidepoint(event.pos):
                self._equip_loot()
            elif self.backpack_btn and self.backpack_btn.collidepoint(event.pos):
                self._store_loot()

    def _equip_loot(self):
        s = self.game.state
        r = self.game.combat_result
        prev = s.equip_item(r["loot"])
        if prev:
            s.inventory.append(prev)
        self.chosen = True

    def _store_loot(self):
        s = self.game.state
        r = self.game.combat_result
        if len(s.inventory) < 20:
            s.inventory.append(r["loot"])
        self.chosen = True

    def draw(self, surface):
        r = self.game.combat_result

        loot = r["loot"]
        # Taller panel for cursed items with debuffs
        panel_h = 250 if loot.debuffs else 220
        panel_w = 520
        panel_y = 40
        panel_h = 250 if loot.debuffs else 220
        panel_x = SCREEN_W // 2 - panel_w // 2
        draw_parchment_panel(surface, panel_x, panel_y, panel_w, panel_h)

        title = "VICTORY" if r["victory"] else "DEFEAT"
        title_color = C.PARCHMENT_EDGE if r["victory"] else C.CRIMSON
        draw_text_with_glow(
            surface, title, self.assets.fonts["heading"], title_color, SCREEN_W // 2, 55, align="center"
        )
        draw_gold_divider(surface, SCREEN_W // 2 - 120, 88, 240)

        draw_text_with_glow(
            surface,
            f"+{r['gold']} Gold    +{r['xp']} XP",
            self.assets.fonts["body"],
            C.PARCHMENT_EDGE,
            SCREEN_W // 2,
            100,
            align="center",
        )

        color = rarity_color(loot.rarity)
        rd = RARITY_DATA[loot.rarity]
        drop_text = f"Dropped: {loot.name} ({loot.slot.upper()}, {rd['name']})"
        drop_text = fit_text(self.assets.fonts["body"], drop_text, panel_w - 40)
        draw_text_with_glow(surface, drop_text, self.assets.fonts["body"], color, SCREEN_W // 2, 140, align="center")
        # Full stat line (not truncated)
        stat_text = loot.stat_text()
        draw_text_with_glow(surface, stat_text, self.assets.fonts["small"], C.INK, SCREEN_W // 2, 170, align="center")
        # Debuff line (if cursed)
        if loot.debuffs:
            debuff_text = loot.debuff_text()
            draw_text_with_glow(
                surface, debuff_text, self.assets.fonts["small"], C.CRIMSON, SCREEN_W // 2, 194, align="center"
            )

        if not self.chosen:
            btn_y = panel_y + panel_h - 55
            cx = SCREEN_W // 2
            self.equip_btn = pygame.Rect(cx - 210, btn_y, 200, 45)
            self.backpack_btn = pygame.Rect(cx + 10, btn_y, 200, 45)
            draw_ornate_button(
                surface,
                self.equip_btn,
                "[1] Equip",
                self.assets.fonts["body"],
                hover=(0 == self.hover_idx),
                color=C.PARCHMENT_EDGE,
            )
            draw_ornate_button(
                surface,
                self.backpack_btn,
                "[2] Backpack",
                self.assets.fonts["body"],
                hover=(1 == self.hover_idx),
                color=C.PARCHMENT_EDGE,
            )
        else:
            draw_text_with_glow(
                surface,
                "Click or press any key to continue...",
                self.assets.fonts["small"],
                C.INK_LIGHT,
                SCREEN_W // 2,
                280,
                align="center",
            )

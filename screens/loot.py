import pygame
from shared import C, SCREEN_W, SCREEN_H, Assets, draw_text, draw_text_wrapped, fit_text, draw_text_fitted, draw_bar, draw_panel, draw_ornate_panel, draw_ornate_button, draw_gold_divider, hp_color, mad_color, rarity_color, generate_parchment_texture, draw_parchment_panel, draw_text_with_glow, draw_text_wrapped_glow, draw_text_fitted_glow
import random
from screens.base import Screen
from data import RARITY_DATA
from engine import generate_item

class LootScreen(Screen):
    def __init__(self, game):
        super().__init__(game)
        self.items = []
        self.gold_found = 0
        self.pick_buttons = []
        self.leave_btn = None

    def enter(self):
        s = self.game.state
        count = 1 + (1 if random.random() < 0.3 else 0)
        self.items = [generate_item(s.floor, luck=s.luck, buffs=s.buffs) for _ in range(count)]
        self.gold_found = 5 + random.randint(0, 10) + s.floor * 2
        s.gold += self.gold_found
        cx = SCREEN_W // 2
        self.pick_buttons = []
        y = 130
        for item in self.items:
            # Taller buttons for items with debuffs
            bh = 90 if item.debuffs else 70
            self.pick_buttons.append(pygame.Rect(cx - 250, y, 500, bh))
            y += bh + 12
        self.leave_btn = pygame.Rect(cx - 100, y + 8, 200, 40)

    def handle_event(self, event):
        s = self.game.state
        all_btns = self.pick_buttons + ([self.leave_btn] if self.leave_btn else [])
        self.update_hover(event, all_btns)
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for i, btn in enumerate(self.pick_buttons):
                if btn.collidepoint(event.pos) and i < len(self.items):
                    if len(s.inventory) < 20:
                        s.inventory.append(self.items[i])
                    else:
                        prev = s.equip_item(self.items[i])
                        if prev:
                            s.inventory.append(prev)
                    self.game.switch_screen("explore")
                    return
            if self.leave_btn and self.leave_btn.collidepoint(event.pos):
                self.game.switch_screen("explore")

    def draw(self, surface):
        # Dynamic panel height based on actual button positions
        panel_w = 560
        if self.pick_buttons:
            last_btn = self.pick_buttons[-1]
            panel_h = min(last_btn.bottom + 70, SCREEN_H - 20)
        else:
            panel_h = 300
        panel_x = SCREEN_W // 2 - panel_w // 2
        draw_parchment_panel(surface, panel_x, 10, panel_w, panel_h)

        draw_text_with_glow(surface, "SALVAGE FOUND", self.assets.fonts["heading"],
                  C.PARCHMENT_EDGE, SCREEN_W // 2, 25, align="center")
        draw_gold_divider(surface, SCREEN_W // 2 - 120, 58, 240)
        draw_text_with_glow(surface, f"+{self.gold_found} Gold", self.assets.fonts["body"],
                  C.PARCHMENT_EDGE, SCREEN_W // 2, 70, align="center")

        for i, (item, btn) in enumerate(zip(self.items, self.pick_buttons)):
            color = rarity_color(item.rarity)
            rd = RARITY_DATA[item.rarity]
            # Button background with hover
            draw_ornate_button(surface, btn, "", self.assets.fonts["tiny"],
                               hover=(i == self.hover_idx), color=color)
            # Item name + slot + rarity on line 1
            label = f"{item.name}  ({item.slot.upper()}, {rd['name']})"
            label = fit_text(self.assets.fonts["small"], label, btn.w - 30)
            draw_text_with_glow(surface, label, self.assets.fonts["small"], color,
                                btn.x + 15, btn.y + 8)
            # Stats on line 2 (full, not truncated)
            stat_line = item.stat_text()
            draw_text_with_glow(surface, stat_line, self.assets.fonts["tiny"],
                                C.INK, btn.x + 15, btn.y + 32)
            # Debuffs on line 3 (if cursed)
            if item.debuffs:
                debuff_line = item.debuff_text()
                draw_text_with_glow(surface, debuff_line, self.assets.fonts["tiny"],
                                    C.CRIMSON, btn.x + 15, btn.y + 52)

        leave_hover = (len(self.pick_buttons) == self.hover_idx)
        draw_ornate_button(surface, self.leave_btn, "Leave it", self.assets.fonts["body"],
                           hover=leave_hover, color=C.PARCHMENT_EDGE)

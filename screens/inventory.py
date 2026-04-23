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
from shared.surface_pool import surface_pool
from screens.base import Screen
from screens.screen_enum import ScreenName


class InventoryScreen(Screen):
    def __init__(self, ctx: GameContext):
        super().__init__(ctx)
        self.back_btn = None
        self.item_buttons = []
        self.prev_screen = ScreenName.EXPLORE

    def enter(self):
        # Read where we came from (set by navigate before enter() is called)
        prev = self.ctx.prev_screen_name
        self.prev_screen = prev if prev is not None else ScreenName.EXPLORE
        # If we were just in combat, go back to combat
        if self.ctx.state and self.ctx.state.combat:
            self.prev_screen = ScreenName.COMBAT

    def handle_event(self, event):
        s = self.ctx.state
        all_btns = self.item_buttons + ([self.back_btn] if self.back_btn else [])
        self.update_hover(event, all_btns)
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE or event.key == pygame.K_q:
                self.play_cancel()
                self.ctx.navigate(self.prev_screen)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.back_btn and self.back_btn.collidepoint(event.pos):
                self.play_cancel()
                self.ctx.navigate(self.prev_screen)
            for i, btn in enumerate(self.item_buttons):
                if btn.collidepoint(event.pos) and i < len(s.inventory):
                    self.play_equip()
                    item = s.inventory[i]
                    prev = s.equip_item(item)
                    s.inventory.pop(i)
                    if prev:
                        s.inventory.append(prev)

    def draw(self, surface):
        s = self.ctx.state

        draw_parchment_panel(surface, 15, 10, SCREEN_W - 30, SCREEN_H - 80)
        draw_text_with_glow(
            surface, "INVENTORY", self.assets.fonts["heading"], C.PARCHMENT_EDGE, SCREEN_W // 2, 20, align="center"
        )
        draw_gold_divider(surface, SCREEN_W // 2 - 150, 55, 300)

        # Equipped items
        slots = ["weapon", "accessory", "armor", "boots", "ringL", "ringR"]
        slot_names = {
            "weapon": "WEAPON",
            "accessory": "ACCESSORY",
            "armor": "ARMOR",
            "boots": "BOOTS",
            "ringL": "LEFT RING",
            "ringR": "RIGHT RING",
        }

        draw_text_with_glow(surface, "Equipped", self.assets.fonts["body"], C.INK, 55, 68)
        y = 98
        label_max_w = SCREEN_W - 180  # leave room for margins
        for slot in slots:
            item = s.equipment.get(slot)
            if item:
                color = rarity_color(item.rarity)
                # Line 1: slot + item name (pixel-width truncated)
                label = f"{slot_names[slot]}: {item.name}"
                draw_text_fitted_glow(surface, label, self.assets.fonts["small"], color, 70, y, label_max_w)
                # Line 2: stats (indented)
                stat_line = item.stat_text()
                draw_text_fitted_glow(
                    surface, stat_line, self.assets.fonts["tiny"], C.INK, 90, y + 18, label_max_w - 20
                )
                # Line 3: debuffs (if any, separate line)
                if item.debuffs:
                    draw_text_fitted_glow(
                        surface, item.debuff_text(), self.assets.fonts["tiny"], C.CRIMSON, 90, y + 34, label_max_w - 20
                    )
                    y += 52
                else:
                    y += 42
            else:
                draw_text_with_glow(
                    surface, f"{slot_names[slot]}: — empty —", self.assets.fonts["small"], C.INK_LIGHT, 70, y
                )
                y += 30

        # Backpack
        y += 8
        draw_gold_divider(surface, 55, y, SCREEN_W - 120)
        y += 10
        draw_text_with_glow(surface, f"Backpack ({len(s.inventory)}/20)", self.assets.fonts["body"], C.INK, 55, y)
        y += 28
        self.item_buttons = []
        if not s.inventory:
            draw_text_with_glow(surface, "Your pack is empty.", self.assets.fonts["small"], C.INK_LIGHT, 70, y)
        else:
            item_h = 48
            for i, item in enumerate(s.inventory):
                color = rarity_color(item.rarity)
                btn = pygame.Rect(60, y, SCREEN_W - 130, item_h)
                self.item_buttons.append(btn)
                # Hover highlight on item row — use pooled surface
                if i == self.hover_idx:
                    row_bg = surface_pool.acquire(btn.w, btn.h)
                    row_bg.fill((212, 160, 23, 30))
                    surface.blit(row_bg, (btn.x, btn.y))
                    surface_pool.release(row_bg)
                    pygame.draw.rect(surface, C.GOLD_TRIM, btn, 1, border_radius=3)
                # Line 1: item name + slot (pixel-width truncated)
                label = f"{i+1}. {item.name} ({item.slot.upper()})"
                draw_text_fitted_glow(surface, label, self.assets.fonts["small"], color, 70, y, 500)
                # Line 2: stats + debuffs
                stat_line = item.stat_text()
                if item.debuffs:
                    stat_line += "  " + item.debuff_text()
                draw_text_fitted_glow(surface, stat_line, self.assets.fonts["tiny"], C.INK, 90, y + 20, 480)
                y += item_h + 4

        # Back button
        self.back_btn = pygame.Rect(SCREEN_W // 2 - 60, SCREEN_H - 65, 120, 40)
        back_hover = len(self.item_buttons) == self.hover_idx
        draw_ornate_button(
            surface, self.back_btn, "Back [Q]", self.assets.fonts["body"], hover=back_hover, color=C.PARCHMENT_EDGE
        )

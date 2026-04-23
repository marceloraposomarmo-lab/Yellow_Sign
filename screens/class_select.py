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
    CLASS_COLORS,
    CLASS_PRIMARY_STAT,
)
from shared.game_context import GameContext
from screens.base import Screen
from screens.screen_enum import ScreenName
from data import CLASSES
from engine import GameState


class ClassSelectScreen(Screen):
    def __init__(self, ctx: GameContext):
        super().__init__(ctx)
        self.class_ids = list(CLASSES.keys())
        self.selected = 0
        self.hovered_ability = -1
        self.hovered_future = -1
        self.start_btn = None
        self.ability_btns = []
        self.future_btns = []

    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            mx, my = event.pos
            old_ability = self.hovered_ability
            old_future = self.hovered_future
            self.hovered_ability = -1
            self.hovered_future = -1
            if self.start_btn and self.start_btn.collidepoint(mx, my):
                return
            # Check ability hover
            for i, btn in enumerate(self.ability_btns):
                if btn.collidepoint(mx, my):
                    self.hovered_ability = i
                    break
            # Check future ability hover
            for i, btn in enumerate(self.future_btns):
                if btn.collidepoint(mx, my):
                    self.hovered_future = i
                    break
            if self.hovered_ability != old_ability or self.hovered_future != old_future:
                if self.hovered_ability >= 0 or self.hovered_future >= 0:
                    self._play_sound("hover")
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.start_btn and self.start_btn.collidepoint(event.pos):
                self.play_confirm()
                self._pick_class()
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_LEFT:
                self.selected = (self.selected - 1) % len(self.class_ids)
                self._play_sound("hover")
            elif event.key == pygame.K_RIGHT:
                self.selected = (self.selected + 1) % len(self.class_ids)
                self._play_sound("hover")
            elif event.key == pygame.K_RETURN:
                self.play_confirm()
                self._pick_class()
            elif event.key == pygame.K_ESCAPE:
                self.play_cancel()
                self.ctx.navigate(ScreenName.TITLE)

    def _pick_class(self):
        state = GameState()
        state.init_from_class(self.class_ids[self.selected])
        self.ctx.state = state
        self.ctx.navigate(ScreenName.EXPLORE)

    def _draw_ability_tooltip(self, surface, formula, btn_rect):
        """Draw a tooltip popup above an ability button showing its damage formula."""
        font = self.assets.fonts["tiny"]
        padding = 8
        text_w = font.size(formula)[0] + padding * 2
        tip_w = max(text_w + 20, 180)
        tip_h = 34
        tip_x = btn_rect.x
        tip_y = btn_rect.y - tip_h - 4
        if tip_y < 72:
            tip_y = btn_rect.bottom + 4
        tip_rect = pygame.Rect(tip_x, tip_y, tip_w, tip_h)
        draw_panel(surface, tip_x, tip_y, tip_w, tip_h, None, C.PARCHMENT_EDGE, 1)
        draw_text_with_glow(
            surface, formula, font, C.PARCHMENT_EDGE, tip_x + padding, tip_y + (tip_h - font.get_height()) // 2
        )

    def draw(self, surface):
        cid = self.class_ids[self.selected]
        cls = CLASSES[cid]
        color = CLASS_COLORS.get(cid, C.PARCHMENT_EDGE)

        # --- Header with page navigation ---
        draw_text(
            surface, "CHOOSE YOUR FATE", self.assets.fonts["heading"], C.YELLOW, SCREEN_W // 2, 18, align="center"
        )
        page_text = f"<  {self.selected + 1} / {len(self.class_ids)}  >"
        draw_text(surface, page_text, self.assets.fonts["tiny"], C.ASH, SCREEN_W // 2, 52, align="center")

        # --- Main panel ---
        panel_x, panel_y = 20, 72
        panel_w, panel_h = SCREEN_W - 40, SCREEN_H - 82
        draw_parchment_panel(surface, panel_x, panel_y, panel_w, panel_h)

        # --- Large class sprite (left side) ---
        sprite = self.assets.get_class_sprite(cid)
        if sprite:
            sprite_scaled = pygame.transform.scale(sprite, (400, 400))
            sprite_x = 40
            sprite_y = 90
            surface.blit(sprite_scaled, (sprite_x, sprite_y))

        # --- Right panel layout ---
        rx = 520
        ry = 90

        # Class name with primary stat icon
        primary_stat = CLASS_PRIMARY_STAT.get(cid, max(cls["base_stats"], key=cls["base_stats"].get))
        stat_icon = self.assets.images.get(f"stat_{primary_stat}_48")
        name_text = cls["name"].upper()
        name_w = self.assets.fonts["title_sm"].size(name_text)[0]
        if stat_icon:
            draw_text_with_glow(surface, name_text, self.assets.fonts["title_sm"], color, rx, ry)
            surface.blit(stat_icon, (rx + name_w + 12, ry + 2))
        else:
            draw_text_with_glow(surface, name_text, self.assets.fonts["title_sm"], color, rx, ry)
        ry += 48

        # Description (word-wrapped to 3 lines max)
        draw_text_wrapped_glow(surface, cls["desc"], self.assets.fonts["small"], C.INK, rx, ry, 600, line_height=20)
        ry += 68

        # Stats line
        stat_parts = []
        for stat_name, stat_val in cls["base_stats"].items():
            sc = C.PARCHMENT_EDGE if stat_val >= 14 else (C.CRIMSON if stat_val <= 6 else C.INK)
            stat_parts.append((f"{stat_name.upper()}:{stat_val}", sc))
        stat_parts.append((f"HP:{cls['hp_base']}+{cls['hp_per_level']}/lv", C.HP_GREEN))
        sx = rx
        for text, sc in stat_parts:
            draw_text_with_glow(surface, text, self.assets.fonts["small"], sc, sx, ry)
            sx += self.assets.fonts["small"].size(text)[0] + 14
        ry += 40

        # Section: Starting Abilities
        draw_text_with_glow(surface, "— Starting Abilities —", self.assets.fonts["small"], C.PARCHMENT_EDGE, rx, ry)
        ry += 28

        starting = [sk for sk in cls["skills"] if sk.get("starting", False)]
        self.ability_btns = []
        for sk in starting:
            btn = pygame.Rect(rx, ry, 280, 44)
            self.ability_btns.append(btn)
            hovered = len(self.ability_btns) - 1 == self.hovered_ability
            label = fit_text(self.assets.fonts["small"], sk["name"], 268)
            draw_ornate_button(surface, btn, label, self.assets.fonts["small"], hover=hovered, color=color)
            draw_text_with_glow(
                surface,
                sk["desc"],
                self.assets.fonts["tiny"],
                C.INK,
                rx + 290,
                ry + (44 - self.assets.fonts["tiny"].get_height()) // 2,
            )
            if hovered:
                self._draw_ability_tooltip(surface, sk["formula"], btn)
            ry += 52

        # Section: Future Abilities (top 3 by power)
        ry += 8
        draw_text_with_glow(surface, "— Abilities Await —", self.assets.fonts["small"], C.PARCHMENT_EDGE, rx, ry)
        ry += 28

        future = sorted(
            [sk for sk in cls["skills"] if sk.get("tier", 1) == 3 and not sk.get("starting", False)],
            key=lambda s: s.get("unlock_lv", 1),
        )[:3]
        self.future_btns = []
        for sk in future:
            btn = pygame.Rect(rx, ry, 280, 36)
            self.future_btns.append(btn)
            hovered = len(self.future_btns) - 1 == self.hovered_future
            label = f"Lv{sk['unlock_lv']} — {fit_text(self.assets.fonts['tiny'], sk['name'], 220)}"
            draw_ornate_button(surface, btn, label, self.assets.fonts["tiny"], hover=hovered, color=C.PARCHMENT_EDGE)
            draw_text_with_glow(
                surface,
                sk["desc"],
                self.assets.fonts["tiny"],
                C.INK_LIGHT,
                rx + 290,
                ry + (36 - self.assets.fonts["tiny"].get_height()) // 2,
            )
            if hovered:
                self._draw_ability_tooltip(surface, sk["formula"], btn)
            ry += 42

        # Start button
        self.start_btn = pygame.Rect(rx, 576, 220, 40)
        draw_ornate_button(
            surface,
            self.start_btn,
            "Choose",
            self.assets.fonts["body"],
            hover=self.start_btn.collidepoint(pygame.mouse.get_pos()),
            color=color,
        )

    def _draw_intro(self, surface):
        """Draw the initial overview screen (not used in one-per-page mode, kept for reference)."""
        draw_text(
            surface, "CHOOSE YOUR FATE", self.assets.fonts["heading"], C.YELLOW, SCREEN_W // 2, 25, align="center"
        )
        draw_text(
            surface,
            "Each path leads deeper into madness.",
            self.assets.fonts["tiny"],
            C.BONE,
            SCREEN_W // 2,
            60,
            align="center",
        )
        draw_gold_divider(surface, SCREEN_W // 2 - 200, 78, 400)
        for i, cid in enumerate(self.class_ids):
            cls = CLASSES[cid]
            color = CLASS_COLORS.get(cid, C.ASH)
            card_y = 90 + i * 125
            card_w = SCREEN_W - 80
            is_selected = i == self.selected
            if is_selected:
                draw_ornate_panel(surface, 40, card_y, card_w, 115)
            else:
                draw_panel(surface, 40, card_y, card_w, 115, (16, 8, 30), C.ASH, 1)
            sprite = self.assets.get_class_sprite(cid, "thumb")
            if sprite:
                surface.blit(sprite, (52, card_y + 12))

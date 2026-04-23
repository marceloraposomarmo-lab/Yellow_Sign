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
from shared import CLASS_COLORS, CLASS_ICONS
from data import MAX_ACTIVE_SKILLS


class StatsScreen(Screen):
    def __init__(self, ctx):
        super().__init__(ctx)
        self.back_btn = None
        self.skill_buttons = []

    def handle_event(self, event):
        all_btns = self.skill_buttons + ([self.back_btn] if self.back_btn else [])
        self.update_hover(event, all_btns)
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE or event.key == pygame.K_q:
                self.play_cancel()
                self.ctx.navigate(ScreenName.EXPLORE)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.back_btn and self.back_btn.collidepoint(event.pos):
                self.play_cancel()
                self.ctx.navigate(ScreenName.EXPLORE)

    def draw(self, surface):
        s = self.ctx.state
        color = CLASS_COLORS.get(s.class_id, C.PARCHMENT_EDGE)

        draw_parchment_panel(surface, 30, 10, SCREEN_W - 60, SCREEN_H - 80)
        draw_text_with_glow(
            surface,
            "CHARACTER STATS",
            self.assets.fonts["heading"],
            C.PARCHMENT_EDGE,
            SCREEN_W // 2,
            22,
            align="center",
        )
        draw_text_with_glow(
            surface,
            f"{CLASS_ICONS.get(s.class_id, '?')} {s.class_name}  —  Level {s.level}",
            self.assets.fonts["body"],
            color,
            SCREEN_W // 2,
            58,
            align="center",
        )
        draw_gold_divider(surface, SCREEN_W // 2 - 150, 84, 300)

        # Class sprite
        sprite = self.assets.get_class_sprite(s.class_id, "thumb")
        if sprite:
            big_sprite = pygame.transform.scale(sprite, (120, 120))
            surface.blit(big_sprite, (50, 100))

        # Core stats (left side)
        lx = 210
        y = 100
        draw_text_with_glow(surface, "Primary Stats", self.assets.fonts["body"], C.INK, lx - 20, y)
        y += 32
        stat_colors = {"int": C.ELDRITCH, "str": C.CRIMSON, "agi": C.MIST, "wis": C.FROST, "luck": C.PARCHMENT_EDGE}
        for stat_name in ["int", "str", "agi", "wis", "luck"]:
            val = s.stats.get(stat_name, 0)
            base = s.base_stats.get(stat_name, 0)
            bonus = val - base
            sc = stat_colors.get(stat_name, C.INK)

            # Stat icon
            icon = self.assets.images.get(f"stat_{stat_name}_64")
            if icon:
                surface.blit(icon, (lx - 20, y - 12))

            text = f"{stat_name.upper()}: {val}"
            if bonus > 0:
                text += f"  ({base}+{bonus})"
            draw_text_with_glow(surface, text, self.assets.fonts["body"], sc, lx + 56, y + 2)
            y += 58

        # Combat stats (right side)
        rx = SCREEN_W // 2 + 60
        ry = 100
        draw_text_with_glow(surface, "Combat Stats", self.assets.fonts["body"], C.INK, rx, ry)
        ry += 32
        combat_stats = [
            ("HP", f"{s.hp}/{s.max_hp}", hp_color(s.hp, s.max_hp)),
            ("ATK", str(s.atk), C.CRIMSON),
            ("DEF", str(s.defense), C.FROST),
            ("M.DEF", str(s.m_def), C.ELDRITCH),
            ("CRIT", f"{s.crit:.1f}%", C.PARCHMENT_EDGE),
            ("EVA", f"{s.evasion:.1f}%", C.MIST),
            ("ACC", f"{s.accuracy:.1f}%", C.INK),
        ]
        for label, val, sc in combat_stats:
            draw_text_with_glow(surface, f"{label}:", self.assets.fonts["small"], C.INK_LIGHT, rx, ry)
            draw_text_with_glow(surface, val, self.assets.fonts["small"], sc, rx + 80, ry)
            ry += 26

        # Progress & misc (below primary stats)
        y += 10
        draw_text_with_glow(surface, "Progress", self.assets.fonts["body"], C.INK, lx, y)
        y += 28
        draw_bar(surface, lx, y, 200, 14, s.xp, s.xp_next, C.XP_PURPLE)
        draw_text_with_glow(surface, f"XP: {s.xp}/{s.xp_next}", self.assets.fonts["tiny"], C.XP_PURPLE, lx + 210, y)
        y += 24
        draw_text_with_glow(surface, f"Floor: {s.floor}/{s.max_floor}", self.assets.fonts["small"], C.INK, lx, y)
        y += 24
        draw_text_with_glow(surface, f"Gold: {s.gold}g", self.assets.fonts["small"], C.PARCHMENT_EDGE, lx, y)
        y += 24
        draw_text_with_glow(surface, f"Kills: {s.kills}", self.assets.fonts["small"], C.INK, lx, y)
        y += 24
        draw_text_with_glow(surface, f"Rooms: {s.rooms_explored}", self.assets.fonts["small"], C.INK, lx, y)

        # Madness (right side, below combat stats)
        ry += 15
        draw_text_with_glow(surface, "Madness", self.assets.fonts["body"], C.INK, rx, ry)
        ry += 28
        draw_bar(surface, rx, ry, 200, 14, s.madness, 100, mad_color(s.madness))
        draw_text_with_glow(
            surface, f"{int(s.madness)}%", self.assets.fonts["tiny"], mad_color(s.madness), rx + 210, ry
        )
        ry += 28

        # Shield & Barrier
        if s.shield > 0 or s.barrier > 0:
            draw_text_with_glow(surface, "Defense", self.assets.fonts["body"], C.INK, rx, ry)
            ry += 28
            if s.shield > 0:
                draw_text_with_glow(
                    surface, f"Shield: {int(s.shield)}", self.assets.fonts["small"], C.SHIELD_BLUE, rx, ry
                )
                ry += 24
            if s.barrier > 0:
                draw_text_with_glow(surface, f"Barrier: x{s.barrier}", self.assets.fonts["small"], C.FROST, rx, ry)
                ry += 24

        # Active skills list — compact buttons with hover tooltips
        skills_y = max(y, ry) + 8
        draw_gold_divider(surface, 50, skills_y, SCREEN_W - 110)
        skills_y += 10
        draw_text_with_glow(
            surface,
            f"Active Skills ({len(s.active_skills)}/{MAX_ACTIVE_SKILLS})",
            self.assets.fonts["small"],
            C.INK,
            55,
            skills_y,
        )
        skills_y += 28

        self.skill_buttons = []
        max_y = SCREEN_H - 100
        for i, sk in enumerate(s.active_skills):
            if skills_y + 28 > max_y:
                break
            btn = pygame.Rect(55, skills_y, 350, 28)
            self.skill_buttons.append(btn)
            hovered = i == self.hover_idx
            label = fit_text(self.assets.fonts["tiny"], f"{sk.name}", 338)
            draw_ornate_button(surface, btn, label, self.assets.fonts["tiny"], hover=hovered, color=C.PARCHMENT_EDGE)
            # Show desc on same line to the right of the button
            desc_text = fit_text(self.assets.fonts["tiny"], sk.desc, SCREEN_W - 440)
            draw_text_with_glow(surface, desc_text, self.assets.fonts["tiny"], C.INK_LIGHT, 415, skills_y + 5)
            # Tooltip on hover
            if hovered:
                self._draw_skill_tooltip(surface, sk, btn)
            skills_y += 34

    def _draw_skill_tooltip(self, surface, sk, btn_rect):
        """Draw a popup tooltip showing skill description and formula."""
        font = self.assets.fonts["tiny"]
        padding = 8
        max_w = 380
        lines = []
        desc_words = sk.desc.split()
        line = ""
        for w in desc_words:
            test = f"{line} {w}".strip()
            if font.size(test)[0] > max_w - padding * 2:
                lines.append(line)
                line = w
            else:
                line = test
        if line:
            lines.append(line)
        lines.append(sk.formula)
        line_h = font.get_height() + 3
        tip_h = padding * 2 + len(lines) * line_h
        tip_w = max_w
        tip_x = btn_rect.x
        tip_y = btn_rect.y - tip_h - 4
        if tip_y < 10:
            tip_y = btn_rect.bottom + 4
        bg = surface_pool.acquire(tip_w, tip_h)
        bg.fill((10, 8, 20, 230))
        surface.blit(bg, (tip_x, tip_y))
        surface_pool.release(bg)
        pygame.draw.rect(surface, C.PARCHMENT_EDGE, (tip_x, tip_y, tip_w, tip_h), 1, border_radius=3)
        for i, l in enumerate(lines):
            lc = C.PARCHMENT_EDGE if i == len(lines) - 1 else C.INK
            draw_text_with_glow(surface, l, font, lc, tip_x + padding, tip_y + padding + i * line_h)

        # Back button
        self.back_btn = pygame.Rect(SCREEN_W // 2 - 60, SCREEN_H - 65, 120, 40)
        draw_ornate_button(
            surface,
            self.back_btn,
            "Back [Q]",
            self.assets.fonts["body"],
            hover=(self.hover_idx == 0),
            color=C.PARCHMENT_EDGE,
        )

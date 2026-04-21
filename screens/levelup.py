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
from data import MAX_ACTIVE_SKILLS


class LevelUpScreen(Screen):
    def __init__(self, game):
        super().__init__(game)
        self.skill_buttons = []
        self.skip_btn = None
        self.replace_mode = False
        self.replace_buttons = []

    def enter(self):
        self.replace_mode = False
        self._build_skill_buttons()

    def _build_skill_buttons(self):
        s = self.game.state
        bw, bh = 500, 50
        cx = SCREEN_W // 2
        skills = s.pending_levelup_skills
        self.skill_buttons = [pygame.Rect(cx - bw // 2, 200 + i * 80, bw, bh) for i in range(len(skills))]
        self.skip_btn = pygame.Rect(cx - 100, 200 + len(skills) * 80 + 10, 200, 40)

    def handle_event(self, event):
        s = self.game.state
        if not s.pending_levelup_skills:
            if event.type == pygame.KEYDOWN or (event.type == pygame.MOUSEBUTTONDOWN):
                self.game.switch_screen(ScreenName.EXPLORE)
            return

        if self.replace_mode:
            self.update_hover(event, self.replace_buttons)
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                for i, btn in enumerate(self.replace_buttons):
                    if btn.collidepoint(event.pos):
                        if i < len(s.active_skills):
                            chosen = s.pending_levelup_skills[0]
                            s.active_skills[i] = chosen
                            s.pending_levelup_skills = []
                            self.replace_mode = False
                            return
                        else:
                            s.pending_levelup_skills = []
                            self.replace_mode = False
                            return
            elif event.type == pygame.KEYDOWN:
                if pygame.K_1 <= event.key <= pygame.K_9:
                    idx = event.key - pygame.K_1
                    if idx < len(s.active_skills):
                        chosen = s.pending_levelup_skills[0]
                        s.active_skills[idx] = chosen
                        s.pending_levelup_skills = []
                        self.replace_mode = False
                    elif idx == len(s.active_skills):
                        s.pending_levelup_skills = []
                        self.replace_mode = False
            return

        all_btns = self.skill_buttons + ([self.skip_btn] if self.skip_btn else [])
        self.update_hover(event, all_btns)

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for i, btn in enumerate(self.skill_buttons):
                if btn.collidepoint(event.pos) and i < len(s.pending_levelup_skills):
                    self._pick_skill(i)
            if self.skip_btn and self.skip_btn.collidepoint(event.pos):
                s.pending_levelup_skills = []
                self.game.switch_screen(ScreenName.EXPLORE)
        elif event.type == pygame.KEYDOWN:
            if pygame.K_1 <= event.key <= pygame.K_9:
                idx = event.key - pygame.K_1
                if idx < len(s.pending_levelup_skills):
                    self._pick_skill(idx)
                elif idx == len(s.pending_levelup_skills):
                    s.pending_levelup_skills = []
                    self.game.switch_screen(ScreenName.EXPLORE)

    def _pick_skill(self, idx):
        s = self.game.state
        chosen = s.pending_levelup_skills[idx]
        if len(s.active_skills) >= MAX_ACTIVE_SKILLS:
            self.replace_mode = True
            s.pending_levelup_skills = [chosen]
            bw, bh = 500, 40
            cx = SCREEN_W // 2
            self.replace_buttons = [
                pygame.Rect(cx - bw // 2, 230 + i * 45, bw, bh) for i in range(len(s.active_skills) + 1)
            ]
        else:
            s.active_skills.append(chosen)
            s.pending_levelup_skills = []
            self.game.switch_screen(ScreenName.EXPLORE)

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
        bg = pygame.Surface((tip_w, tip_h), pygame.SRCALPHA)
        bg.fill((10, 8, 20, 230))
        surface.blit(bg, (tip_x, tip_y))
        pygame.draw.rect(surface, C.PARCHMENT_EDGE, (tip_x, tip_y, tip_w, tip_h), 1, border_radius=3)
        for i, l in enumerate(lines):
            lc = C.PARCHMENT_EDGE if i == len(lines) - 1 else C.INK
            draw_text_with_glow(surface, l, font, lc, tip_x + padding, tip_y + padding + i * line_h)

    def draw(self, surface):
        s = self.game.state

        panel_w, panel_h = 600, 400
        panel_x = SCREEN_W // 2 - panel_w // 2
        draw_parchment_panel(surface, panel_x, 15, panel_w, panel_h)

        draw_text_with_glow(
            surface, "LEVEL UP!", self.assets.fonts["heading"], C.PARCHMENT_EDGE, SCREEN_W // 2, 28, align="center"
        )
        draw_text_with_glow(
            surface,
            f"{s.class_name} is now Level {s.level}!",
            self.assets.fonts["body"],
            C.INK,
            SCREEN_W // 2,
            65,
            align="center",
        )
        draw_text_with_glow(
            surface,
            f"HP: {s.max_hp}  ATK: {s.atk}  DEF: {s.defense}/{s.m_def}",
            self.assets.fonts["tiny"],
            C.INK_LIGHT,
            SCREEN_W // 2,
            90,
            align="center",
        )
        draw_gold_divider(surface, SCREEN_W // 2 - 180, 108, 360)

        if self.replace_mode:
            draw_text_with_glow(
                surface,
                "CHOOSE ABILITY TO REPLACE",
                self.assets.fonts["body"],
                C.CRIMSON,
                SCREEN_W // 2,
                130,
                align="center",
            )
            for i, (sk, btn) in enumerate(zip(s.active_skills, self.replace_buttons)):
                hovered = i == self.hover_idx
                draw_ornate_button(
                    surface, btn, f"{i+1}. {sk.name}", self.assets.fonts["small"], hover=hovered, color=C.PARCHMENT_EDGE
                )
                if hovered:
                    self._draw_skill_tooltip(surface, sk, btn)
            cancel_btn = self.replace_buttons[-1] if self.replace_buttons else None
            if cancel_btn:
                draw_ornate_button(
                    surface,
                    cancel_btn,
                    f"{len(s.active_skills)+1}. Cancel",
                    self.assets.fonts["small"],
                    hover=(len(s.active_skills) == self.hover_idx),
                    color=C.PARCHMENT_EDGE,
                )
        elif s.pending_levelup_skills:
            draw_text_with_glow(
                surface,
                "CHOOSE A NEW ABILITY",
                self.assets.fonts["body"],
                C.PARCHMENT_EDGE,
                SCREEN_W // 2,
                125,
                align="center",
            )
            if len(s.active_skills) >= MAX_ACTIVE_SKILLS:
                draw_text_with_glow(
                    surface,
                    "(Skill slots full — will replace an existing ability)",
                    self.assets.fonts["tiny"],
                    C.CRIMSON,
                    SCREEN_W // 2,
                    152,
                    align="center",
                )

            for i, (sk, btn) in enumerate(zip(s.pending_levelup_skills, self.skill_buttons)):
                hovered = i == self.hover_idx
                draw_ornate_button(
                    surface, btn, f"[{i+1}] {sk.name}", self.assets.fonts["body"], hover=hovered, color=C.PARCHMENT_EDGE
                )
                if hovered:
                    self._draw_skill_tooltip(surface, sk, btn)

            draw_ornate_button(
                surface,
                self.skip_btn,
                "Skip",
                self.assets.fonts["small"],
                hover=(len(s.pending_levelup_skills) == self.hover_idx),
                color=C.PARCHMENT_EDGE,
            )
        else:
            draw_text_with_glow(
                surface,
                "Press any key to continue...",
                self.assets.fonts["small"],
                C.INK_LIGHT,
                SCREEN_W // 2,
                200,
                align="center",
            )

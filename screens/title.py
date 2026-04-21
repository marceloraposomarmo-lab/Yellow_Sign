import random
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


class TitleScreen(Screen):
    def __init__(self, game):
        super().__init__(game)
        self.particles = []
        self.selected = 0
        self.options = ["New Adventure", "Load Game", "Fullscreen", "Quit"]
        self.buttons = []
        self._init_buttons()

    def _init_buttons(self):
        bw, bh = 320, 50
        cx = SCREEN_W // 2
        start_y = 470
        self.buttons = []
        for i in range(len(self.options)):
            self.buttons.append(pygame.Rect(cx - bw // 2, start_y + i * 55, bw, bh))

    def enter(self):
        self.particles = []
        for _ in range(80):
            self.particles.append(
                {
                    "x": random.randint(0, SCREEN_W),
                    "y": random.randint(0, SCREEN_H),
                    "vx": random.uniform(-0.3, 0.3),
                    "vy": random.uniform(-1.5, -0.3),
                    "size": random.randint(1, 4),
                    "color": random.choice([C.YELLOW, C.ELDRITCH, C.AMBER]),
                    "alpha": random.randint(80, 255),
                    "life": random.uniform(2, 8),
                }
            )

    def update(self, dt):
        for p in self.particles:
            p["x"] += p["vx"]
            p["y"] += p["vy"]
            p["life"] -= dt
            p["alpha"] = max(0, p["alpha"] - dt * 20)
            if p["life"] <= 0 or p["y"] < -10:
                p["x"] = random.randint(0, SCREEN_W)
                p["y"] = SCREEN_H + random.randint(0, 50)
                p["life"] = random.uniform(2, 8)
                p["alpha"] = random.randint(80, 255)

    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            for i, btn in enumerate(self.buttons):
                if btn.collidepoint(event.pos):
                    self.selected = i
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for i, btn in enumerate(self.buttons):
                if btn.collidepoint(event.pos):
                    self._select(i)
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                self.selected = (self.selected - 1) % len(self.options)
            elif event.key == pygame.K_DOWN:
                self.selected = (self.selected + 1) % len(self.options)
            elif event.key == pygame.K_RETURN:
                self._select(self.selected)

    def _select(self, idx):
        if idx == 0:
            self.game.switch_screen(ScreenName.CLASS_SELECT)
        elif idx == 1:
            self.game.switch_screen(ScreenName.LOAD)
        elif idx == 2:
            self.game.toggle_fullscreen()
        elif idx == 3:
            self.game.running = False

    def draw(self, surface):
        # Particles
        for p in self.particles:
            s = pygame.Surface((p["size"] * 2, p["size"] * 2), pygame.SRCALPHA)
            s.fill((*p["color"], int(p["alpha"])))
            surface.blit(s, (int(p["x"]), int(p["y"])))

        # ── Title & Subtitle (top) ──
        draw_text(
            surface, "THE KING IN YELLOW", self.assets.fonts["title"], C.YELLOW, SCREEN_W // 2, 40, align="center"
        )
        draw_text(
            surface,
            "A Lovecraftian Dungeon Crawler",
            self.assets.fonts["subheading"],
            C.BONE,
            SCREEN_W // 2,
            110,
            align="center",
        )
        draw_gold_divider(surface, SCREEN_W // 2 - 200, 145, 400)

        # ── Character sprite (upper-middle) ──
        char = self.assets.get_class_sprite("scholar")
        if char:
            # Scale down slightly so it fits the tighter layout
            char_scaled = pygame.transform.scale(char, (180, 180))
            cx = SCREEN_W // 2 - char_scaled.get_width() // 2
            surface.blit(char_scaled, (cx, 160))

        # ── Poem (right below sprite) ──
        poem_lines = [
            '"Along the shore the cloud waves break,',
            "The twin suns sink behind the lake,",
            "The shadows lengthen",
            'In Carcosa."',
        ]
        poem_start_y = 355
        for i, line in enumerate(poem_lines):
            color = C.YELLOW if i == 3 else C.BONE
            draw_text(
                surface, line, self.assets.fonts["small"], color, SCREEN_W // 2, poem_start_y + i * 22, align="center"
            )

        # ── Divider above buttons ──
        draw_gold_divider(surface, SCREEN_W // 2 - 160, 450, 320)

        # ── Buttons (below poem, no overlap) ──
        for i, btn in enumerate(self.buttons):
            label = self.options[i]
            if i == 2:  # Fullscreen button
                state = "[ON]" if self.game.fullscreen else "[OFF]"
                label = f"Fullscreen {state}"
            color = C.MIST if i == 2 else C.PARCHMENT_EDGE
            draw_ornate_button(surface, btn, label, self.assets.fonts["body"], hover=(i == self.selected), color=color)

        # ── Footer ──
        draw_text(
            surface,
            "Ph'nglui mglw'nafh Cthulhu R'lyeh wgah'nagl fhtagn.",
            self.assets.fonts["tiny"],
            C.ASH,
            SCREEN_W // 2,
            SCREEN_H - 28,
            align="center",
        )

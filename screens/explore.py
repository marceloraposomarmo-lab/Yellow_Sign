import pygame
from shared import C, SCREEN_W, SCREEN_H, Assets, draw_hud, draw_text, draw_text_wrapped, fit_text, draw_text_fitted, draw_bar, draw_panel, draw_ornate_panel, draw_ornate_button, draw_gold_divider, hp_color, mad_color, rarity_color, generate_parchment_texture, draw_parchment_panel, draw_text_with_glow, draw_text_wrapped_glow, draw_text_fitted_glow
import random
from screens.base import Screen
from data import EVENTS, TRAPS, FLOOR_NARRATIVES
from engine import start_combat, generate_paths, resolve_trap, generate_shop, advance_floor

class ExploreScreen(Screen):
    def __init__(self, game):
        super().__init__(game)
        self.paths = []
        self.path_buttons = []
        self.cmd_buttons = {}
        self.narrative = ""
        self.particles = []

    def enter(self):
        s = self.game.state
        self.narrative = FLOOR_NARRATIVES[min(s.floor - 1, len(FLOOR_NARRATIVES) - 1)]
        is_boss = s.floor >= s.max_floor
        if is_boss:
            self.paths = []
            start_combat(s, is_boss=True)
            self.game.switch_screen("combat")
            return
        # Only generate new paths if we don't have any (don't regenerate on inventory/stats visit)
        if not self.paths:
            self.paths = generate_paths(s.floor)
        self._build_buttons()
        # Spawn dust particles
        if not self.particles:
            for _ in range(40):
                self.particles.append(self._new_dust_particle())

    def _new_dust_particle(self):
        return {
            "x": random.uniform(0, SCREEN_W),
            "y": random.uniform(130, SCREEN_H),
            "vx": random.uniform(-0.2, 0.2),
            "vy": random.uniform(-0.8, -0.1),
            "size": random.randint(1, 3),
            "alpha": random.randint(30, 80),
            "life": random.uniform(3, 10),
        }

    def _build_buttons(self):
        # Side-by-side layout: left and right cards
        card_w, card_h = 560, 260
        gap = 40
        left_x = SCREEN_W // 2 - card_w - gap // 2
        right_x = SCREEN_W // 2 + gap // 2
        start_y = 340
        self.path_buttons = []
        positions = [(left_x, start_y), (right_x, start_y)]
        for i in range(len(self.paths)):
            if i < len(positions):
                self.path_buttons.append(pygame.Rect(positions[i][0], positions[i][1], card_w, card_h))
            else:
                self.path_buttons.append(pygame.Rect(positions[0][0], start_y, card_w, card_h))

        # Command buttons
        cx = SCREEN_W // 2
        self.cmd_buttons = {
            "inventory": pygame.Rect(cx - 310, SCREEN_H - 70, 120, 40),
            "stats": pygame.Rect(cx - 120, SCREEN_H - 70, 120, 40),
            "save": pygame.Rect(cx + 70, SCREEN_H - 70, 120, 40),
            "menu": pygame.Rect(cx + 260, SCREEN_H - 70, 120, 40),
        }

    def update(self, dt):
        for p in self.particles:
            p["x"] += p["vx"]
            p["y"] += p["vy"]
            p["life"] -= dt
            p["alpha"] = max(0, p["alpha"] - dt * 8)
            if p["life"] <= 0 or p["y"] < 120:
                new_p = self._new_dust_particle()
                p.update(new_p)

    def handle_event(self, event):
        # Track hover for all buttons
        all_btns = self.path_buttons + list(self.cmd_buttons.values())
        self.update_hover(event, all_btns)

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for i, btn in enumerate(self.path_buttons):
                if btn.collidepoint(event.pos):
                    self._choose_path(i)
            for name, btn in self.cmd_buttons.items():
                if btn.collidepoint(event.pos):
                    if name == "inventory":
                        self.game.switch_screen("inventory")
                    elif name == "stats":
                        self.game.switch_screen("stats")
                    elif name == "save":
                        self.game.switch_screen("save")
                    elif name == "menu":
                        self.game.switch_screen("title")
        elif event.type == pygame.KEYDOWN:
            if pygame.K_1 <= event.key <= pygame.K_9:
                idx = event.key - pygame.K_1
                if idx < len(self.paths):
                    self._choose_path(idx)
            elif event.key == pygame.K_i:
                self.game.switch_screen("inventory")
            elif event.key == pygame.K_t:
                self.game.switch_screen("stats")
            elif event.key == pygame.K_s:
                self.game.switch_screen("save")

    def _choose_path(self, idx):
        s = self.game.state
        path = self.paths[idx]
        # Clear paths so next room generates fresh ones
        self.paths = []
        s.rooms_explored += 1
        if s.add_madness(2):
            self.game.gameover_msg = "Your mind shatters. The Yellow Sign consumes your last rational thought."
            self.game.switch_screen("gameover")
            return

        ptype = path["type"]
        if ptype == "combat":
            if s.buffs.get("skipCombat", 0) > 0:
                s.buffs["skipCombat"] = 0
                # Skip this combat, generate a loot room instead
                self.game.switch_screen("loot")
            else:
                start_combat(s, is_boss=False)
                self.game.switch_screen("combat")
        elif ptype == "event":
            event = random.choice(EVENTS)
            self.game.pending_event = event
            self.game.switch_screen("event")
        elif ptype == "loot":
            self.game.switch_screen("loot")
        elif ptype == "rest":
            self.game.switch_screen("rest")
        elif ptype == "shop":
            items, prices = generate_shop(s)
            self.game.shop_items = items
            self.game.shop_prices = prices
            self.game.shop_sold = [False] * len(items)
            self.game.switch_screen("shop")
        elif ptype == "trap":
            trap = random.choice(TRAPS)
            trap_idx = TRAPS.index(trap)
            msg, game_over = resolve_trap(s, trap_idx)
            self.game.trap_msg = msg
            self.game.trap_name = trap["name"]
            self.game.trap_desc = trap["desc"]
            if game_over:
                self.game.gameover_msg = "The trap claims your life."
                self.game.switch_screen("gameover")
            else:
                self.game.switch_screen("trap_result")

    def draw(self, surface):
        s = self.game.state
        draw_hud(surface, s, self.assets)

        # Dust particles (drawn behind UI)
        for p in self.particles:
            ps = pygame.Surface((p["size"] * 2, p["size"] * 2), pygame.SRCALPHA)
            ps.fill((180, 170, 150, int(p["alpha"])))
            surface.blit(ps, (int(p["x"]), int(p["y"])))

        is_boss = s.floor >= s.max_floor

        # Floor info with parchment panel
        panel_w, panel_h = 600, 180
        panel_x = SCREEN_W // 2 - panel_w // 2
        draw_parchment_panel(surface, panel_x, 130, panel_w, panel_h)

        draw_text_wrapped_glow(surface, self.narrative, self.assets.fonts["small"],
                          C.INK, SCREEN_W // 2 - 270, 155, 540, line_height=22)

        # Path choices — side by side cards
        if self.paths:
            for i, (path, btn) in enumerate(zip(self.paths, self.path_buttons)):
                hovered = (i == self.hover_idx)
                ptype = path["type"]

                # Draw parchment card background with hover effect
                draw_parchment_panel(surface, btn.x, btn.y, btn.w, btn.h)
                border_col = C.YELLOW if hovered else C.PARCHMENT_EDGE
                pygame.draw.rect(surface, border_col, btn, 2, border_radius=4)
                if hovered:
                    glow = pygame.Surface((btn.w + 10, btn.h + 10), pygame.SRCALPHA)
                    glow.fill((120, 80, 200, 40))
                    surface.blit(glow, (btn.x - 5, btn.y - 5))

                # Icon on top-center of the card
                icon_key = f"path_{ptype}"
                icon = self.assets.images.get(icon_key)
                icon_size = 150
                icon_x = btn.x + (btn.width - icon_size) // 2
                icon_y = btn.y + 12
                if icon:
                    surface.blit(icon, (icon_x, icon_y))

                # Text area: below the icon, centered
                text_center_x = btn.x + btn.width // 2
                text_max_w = btn.width - 40
                text_top = icon_y + icon_size + 8

                # Line 1: path name
                name_text = path["name"]
                name_font = self.assets.fonts["body"]
                name_text = fit_text(name_font, name_text, text_max_w)
                draw_text_with_glow(surface, name_text, name_font,
                                    C.INK, text_center_x, text_top, align="center")

                # Line 2: elaborated description (wrapped if needed)
                desc_text = path.get("desc2", path["desc"])
                desc_font = self.assets.fonts["small"]
                desc_y = text_top + 24
                draw_text_wrapped_glow(surface, desc_text, desc_font,
                                       C.INK_LIGHT, btn.x + 20, desc_y, text_max_w, line_height=18)

        # Bottom commands
        cmd_names = list(self.cmd_buttons.keys())
        for ci, (name, btn) in enumerate(self.cmd_buttons.items()):
            labels = {"inventory": "Inventory [I]", "stats": "Stats [T]", "save": "Save [S]", "menu": "Menu"}
            draw_ornate_button(surface, btn, labels[name], self.assets.fonts["small"],
                               hover=((len(self.path_buttons) + ci) == self.hover_idx), color=C.PARCHMENT_EDGE)

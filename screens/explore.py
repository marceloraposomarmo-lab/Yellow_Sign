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
    TypewriterText,
    draw_madness_vignette,
)
from shared.game_context import GameContext
from shared.surface_pool import surface_pool
import random
from screens.base import Screen
from screens.screen_enum import ScreenName
from data import EVENTS, TRAPS, FLOOR_NARRATIVES
from engine import start_combat, generate_paths, resolve_trap, generate_shop, advance_floor


class ExploreScreen(Screen):
    def __init__(self, ctx: GameContext):
        super().__init__(ctx)
        self.paths = []
        self.path_buttons = []
        self.cmd_buttons = {}
        self.narrative = ""
        self.particles = []
        self.typewriter = None  # TypewriterText for floor narrative
        self.narrative_complete = False

    def enter(self):
        s = self.ctx.state
        self.narrative = FLOOR_NARRATIVES[min(s.floor - 1, len(FLOOR_NARRATIVES) - 1)]
        # Initialize typewriter effect for floor narrative
        self.typewriter = TypewriterText(self.narrative, reveal_speed=48.0)
        self.narrative_complete = False

        is_boss = s.floor >= s.max_floor
        if is_boss:
            self.paths = []
            start_combat(s, is_boss=True)
            self.ctx.navigate(ScreenName.COMBAT)
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
        """Update particles and typewriter animation."""
        for p in self.particles:
            p["x"] += p["vx"]
            p["y"] += p["vy"]
            p["life"] -= dt
            p["alpha"] = max(0, p["alpha"] - dt * 8)
            if p["life"] <= 0 or p["y"] < 120:
                new_p = self._new_dust_particle()
                p.update(new_p)

        # Update typewriter animation
        if self.typewriter and not self.typewriter.complete:
            self.typewriter.update(dt)
            self.narrative_complete = self.typewriter.complete
        else:
            self.narrative_complete = True

    def handle_event(self, event):
        # Allow skipping typewriter animation with any input
        if self.typewriter and not self.typewriter.complete:
            if event.type == pygame.KEYDOWN or (event.type == pygame.MOUSEBUTTONDOWN and event.button == 1):
                self.typewriter.skip()
                return  # Consume the event

        # Track hover for all buttons
        all_btns = self.path_buttons + list(self.cmd_buttons.values())
        self.update_hover(event, all_btns)

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            # Only allow interaction when narrative is complete
            if self.narrative_complete:
                for i, btn in enumerate(self.path_buttons):
                    if btn.collidepoint(event.pos):
                        self._choose_path(i)
                for name, btn in self.cmd_buttons.items():
                    if btn.collidepoint(event.pos):
                        if name == "inventory":
                            self.ctx.navigate(ScreenName.INVENTORY)
                        elif name == "stats":
                            self.ctx.navigate(ScreenName.STATS)
                        elif name == "save":
                            self.ctx.navigate(ScreenName.SAVE)
                        elif name == "menu":
                            self.ctx.navigate(ScreenName.TITLE)
        elif event.type == pygame.KEYDOWN:
            # Only allow keyboard interaction when narrative is complete
            if self.narrative_complete:
                if pygame.K_1 <= event.key <= pygame.K_9:
                    idx = event.key - pygame.K_1
                    if idx < len(self.paths):
                        self._choose_path(idx)
                elif event.key == pygame.K_i:
                    self.ctx.navigate(ScreenName.INVENTORY)
                elif event.key == pygame.K_t:
                    self.ctx.navigate(ScreenName.STATS)
                elif event.key == pygame.K_s:
                    self.ctx.navigate(ScreenName.SAVE)

    def _choose_path(self, idx):
        s = self.ctx.state
        path = self.paths[idx]
        # Clear paths so next room generates fresh ones
        self.paths = []
        s.rooms_explored += 1
        if s.add_madness(2):
            self.ctx.screen_data["gameover_msg"] = "Your mind shatters. The Yellow Sign consumes your last rational thought."
            self.ctx.navigate(ScreenName.GAMEOVER)
            return

        ptype = path["type"]
        if ptype == "combat":
            if s.buffs.get("skipCombat", 0) > 0:
                s.buffs["skipCombat"] = 0
                # Skip this combat, generate a loot room instead
                self.ctx.navigate(ScreenName.LOOT)
            else:
                start_combat(s, is_boss=False)
                self.ctx.navigate(ScreenName.COMBAT)
        elif ptype == "event":
            event = random.choice(EVENTS)
            self.ctx.screen_data["pending_event"] = event
            self.ctx.navigate(ScreenName.EVENT)
        elif ptype == "loot":
            self.ctx.navigate(ScreenName.LOOT)
        elif ptype == "rest":
            self.ctx.navigate(ScreenName.REST)
        elif ptype == "shop":
            items, prices = generate_shop(s)
            self.ctx.screen_data["shop_items"] = items
            self.ctx.screen_data["shop_prices"] = prices
            self.ctx.screen_data["shop_sold"] = [False] * len(items)
            self.ctx.navigate(ScreenName.SHOP)
        elif ptype == "trap":
            trap = random.choice(TRAPS)
            trap_idx = TRAPS.index(trap)
            msg, game_over = resolve_trap(s, trap_idx)
            self.ctx.screen_data["trap_msg"] = msg
            self.ctx.screen_data["trap_name"] = trap["name"]
            self.ctx.screen_data["trap_desc"] = trap["desc"]
            if game_over:
                self.ctx.screen_data["gameover_msg"] = "The trap claims your life."
                self.ctx.navigate(ScreenName.GAMEOVER)
            else:
                self.ctx.navigate(ScreenName.TRAP_RESULT)

    def draw(self, surface):
        s = self.ctx.state
        draw_hud(surface, s, self.assets)

        # Dust particles (drawn behind UI) — use pooled surfaces
        for p in self.particles:
            sz = p["size"] * 2
            ps = surface_pool.acquire(sz, sz)
            ps.fill((180, 170, 150, int(p["alpha"])))
            surface.blit(ps, (int(p["x"]), int(p["y"])))
            surface_pool.release(ps)

        is_boss = s.floor >= s.max_floor

        # Floor info with parchment panel
        panel_w, panel_h = 600, 180
        panel_x = SCREEN_W // 2 - panel_w // 2
        draw_parchment_panel(surface, panel_x, 130, panel_w, panel_h)

        # Draw narrative text with typewriter effect
        if self.typewriter:
            visible_text = self.typewriter.get_visible_text()
            draw_text_wrapped_glow(
                surface, visible_text, self.assets.fonts["small"], C.INK, SCREEN_W // 2 - 270, 155, 540, line_height=22
            )

            # Show "click to skip" hint if still typing
            if not self.typewriter.complete:
                skip_hint = "Click to skip..."
                draw_text_with_glow(
                    surface, skip_hint, self.assets.fonts["tiny"], C.ASH, SCREEN_W // 2, 310, align="center"
                )
        else:
            draw_text_wrapped_glow(
                surface,
                self.narrative,
                self.assets.fonts["small"],
                C.INK,
                SCREEN_W // 2 - 270,
                155,
                540,
                line_height=22,
            )

        # Path choices — side by side cards
        if self.paths:
            for i, (path, btn) in enumerate(zip(self.paths, self.path_buttons)):
                hovered = i == self.hover_idx
                ptype = path["type"]

                # Draw parchment card background with hover effect
                draw_parchment_panel(surface, btn.x, btn.y, btn.w, btn.h)
                border_col = C.YELLOW if hovered else C.PARCHMENT_EDGE
                pygame.draw.rect(surface, border_col, btn, 2, border_radius=4)
                if hovered:
                    glow = surface_pool.acquire(btn.w + 10, btn.h + 10)
                    glow.fill((120, 80, 200, 40))
                    surface.blit(glow, (btn.x - 5, btn.y - 5))
                    surface_pool.release(glow)

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
                draw_text_with_glow(surface, name_text, name_font, C.INK, text_center_x, text_top, align="center")

                # Line 2: elaborated description (wrapped if needed)
                desc_text = path.get("desc2", path["desc"])
                desc_font = self.assets.fonts["small"]
                desc_y = text_top + 24
                draw_text_wrapped_glow(
                    surface, desc_text, desc_font, C.INK_LIGHT, btn.x + 20, desc_y, text_max_w, line_height=18
                )

        # Bottom commands
        cmd_names = list(self.cmd_buttons.keys())
        for ci, (name, btn) in enumerate(self.cmd_buttons.items()):
            labels = {"inventory": "Inventory [I]", "stats": "Stats [T]", "save": "Save [S]", "menu": "Menu"}
            draw_ornate_button(
                surface,
                btn,
                labels[name],
                self.assets.fonts["small"],
                hover=((len(self.path_buttons) + ci) == self.hover_idx),
                color=C.PARCHMENT_EDGE,
            )

        # Draw madness vignette effect (darkness at screen edges based on madness level)
        draw_madness_vignette(surface, s.madness, 0.016, self.ctx.time_seconds)

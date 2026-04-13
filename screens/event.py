import pygame
from shared import C, SCREEN_W, SCREEN_H, Assets, draw_text, draw_text_wrapped, fit_text, draw_text_fitted, draw_bar, draw_panel, draw_ornate_panel, draw_ornate_button, draw_gold_divider, hp_color, mad_color, rarity_color, generate_parchment_texture, draw_parchment_panel, draw_text_with_glow, draw_text_wrapped_glow, draw_text_fitted_glow, TypewriterText
import random
from screens.base import Screen
from data import EVENTS
from engine import resolve_event

class EventScreen(Screen):
    def __init__(self, game):
        super().__init__(game)
        self.outcome_buttons = []
        self.result_msg = ""
        self.result_loot = None
        self.showing_result = False
        self.typewriter = None  # TypewriterText instance for narrative text
        self.narrative_complete = False  # Track if typewriter animation is done

    def enter(self):
        self.showing_result = False
        self.result_msg = ""
        self.narrative_complete = False
        # Initialize typewriter effect for narrative text
        event = self.game.pending_event
        self.typewriter = TypewriterText(event["text"], reveal_speed=42.0)
        
        n = len(event["outcomes"])
        bw, bh = 500, 50
        cx = SCREEN_W // 2
        self.outcome_buttons = [pygame.Rect(cx - bw // 2, 360 + i * 62, bw, bh) for i in range(n)]

    def update(self, dt):
        """Update typewriter animation."""
        if self.typewriter and not self.typewriter.complete:
            self.typewriter.update(dt)
            # Only allow interaction when text is complete
            self.narrative_complete = self.typewriter.complete
        else:
            self.narrative_complete = True

    def handle_event(self, event):
        s = self.game.state
        if self.showing_result:
            if event.type == pygame.KEYDOWN or (event.type == pygame.MOUSEBUTTONDOWN):
                if s.hp <= 0:
                    self.game.gameover_msg = "The asylum claims another victim."
                    self.game.switch_screen("gameover")
                else:
                    self.game.switch_screen("explore")
            return

        # Allow skipping typewriter animation with any input
        if self.typewriter and not self.typewriter.complete:
            if event.type == pygame.KEYDOWN or (event.type == pygame.MOUSEBUTTONDOWN and event.button == 1):
                self.typewriter.skip()
                return  # Consume the event
        
        self.update_hover(event, self.outcome_buttons)
        pe = self.game.pending_event
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            # Only allow button clicks when narrative is complete
            if self.narrative_complete:
                for i, btn in enumerate(self.outcome_buttons):
                    if btn.collidepoint(event.pos) and i < len(pe["outcomes"]):
                        self._resolve(i)
        elif event.type == pygame.KEYDOWN:
            # Only allow keyboard selection when narrative is complete
            if self.narrative_complete:
                if pygame.K_1 <= event.key <= pygame.K_9:
                    idx = event.key - pygame.K_1
                    if idx < len(pe["outcomes"]):
                        self._resolve(idx)

    def _resolve(self, idx):
        s = self.game.state
        pe = self.game.pending_event
        msg, loot = resolve_event(s, EVENTS.index(pe), idx)
        self.result_msg = msg
        self.result_loot = loot
        if loot:
            s.inventory.append(loot)
        self.showing_result = True

    def draw(self, surface):
        pe = self.game.pending_event

        panel_w, panel_h = 600, 280
        panel_x = SCREEN_W // 2 - panel_w // 2
        draw_parchment_panel(surface, panel_x, 130, panel_w, panel_h)

        draw_text_with_glow(surface, pe["title"], self.assets.fonts["heading"],
                  C.PARCHMENT_EDGE, SCREEN_W // 2, 145, align="center")
        draw_gold_divider(surface, SCREEN_W // 2 - 180, 178, 360)
        
        # Draw narrative text with typewriter effect
        if self.typewriter:
            visible_text = self.typewriter.get_visible_text()
            draw_text_wrapped_glow(surface, visible_text, self.assets.fonts["body"],
                              C.INK, SCREEN_W // 2 - 270, 195, 540)
            
            # Show "click to skip" hint if still typing
            if not self.typewriter.complete:
                skip_hint = "Click to skip..."
                draw_text_with_glow(surface, skip_hint, self.assets.fonts["tiny"],
                          C.ASH, SCREEN_W // 2, 340, align="center")
        else:
            draw_text_wrapped_glow(surface, pe["text"], self.assets.fonts["body"],
                              C.INK, SCREEN_W // 2 - 270, 195, 540)

        if self.showing_result:
            color = C.MIST if "heal" in self.result_msg.lower() or "+" not in self.result_msg else C.CRIMSON
            draw_text_with_glow(surface, self.result_msg, self.assets.fonts["body"],
                      color, SCREEN_W // 2, 425, align="center")
            if self.result_loot:
                loot_text = fit_text(self.assets.fonts["small"],
                                     f"Received: {self.result_loot.name}", 500)
                draw_text_with_glow(surface, loot_text,
                          self.assets.fonts["small"], rarity_color(self.result_loot.rarity),
                          SCREEN_W // 2, 458, align="center")
            draw_text_with_glow(surface, "Click to continue...", self.assets.fonts["tiny"],
                      C.INK_LIGHT, SCREEN_W // 2, 498, align="center")
        else:
            for i, (o, btn) in enumerate(zip(pe["outcomes"], self.outcome_buttons)):
                draw_ornate_button(surface, btn, f"[{i+1}] {o['text']}",
                                   self.assets.fonts["body"], hover=(i == self.hover_idx), color=C.PARCHMENT_EDGE)

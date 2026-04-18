import pygame
import math
import random
from shared import (C, SCREEN_W, SCREEN_H, draw_text, draw_text_wrapped, draw_text_fitted,
                    fit_text, draw_bar, draw_ornate_panel, draw_ornate_button,
                    draw_gold_divider, hp_color, mad_color, draw_parchment_panel,
                    draw_text_with_glow, draw_status_icons_row, draw_status_tooltip,
                    generate_parchment_texture, draw_hud)
from engine import calc_preview_damage, _get_enemy_intent_message
from screens.combat.particles import create_particle, PARTICLE_TYPES


class CombatRendererMixin:
    """Mixin providing all draw/render methods for CombatScreen.

    This mixin assumes ``self`` has the full CombatScreen attribute set
    (game, assets, particles, damage_numbers, etc.) so it can be mixed
    into CombatScreen without changing its public interface.
    """

    # ── Skill tooltip ──────────────────────────────────────────────────────────

    def _draw_skill_tooltip(self, surface, sk, btn_rect):
        """Draw a popup tooltip above a skill button showing description, formula, and damage preview."""
        font = self.assets.fonts["tiny"]
        padding = 10
        max_w = 380

        # Build tooltip lines
        lines = []
        # Description (word-wrap if needed)
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
        # Formula line
        lines.append(sk.formula)
        # Damage preview line (only for damage-dealing skills)
        base_dmg, final_dmg = calc_preview_damage(self.game.state, sk)
        if final_dmg > 0:
            # Show range: center ± 25% accounts for the 0.85-1.15 random variance
            lo = max(1, int(final_dmg * 0.75))
            hi = int(final_dmg * 1.25)
            lines.append(f"~{lo}-{hi} dmg (after DEF)")
        elif base_dmg > 0:
            lo = max(1, int(base_dmg * 0.75))
            hi = int(base_dmg * 1.25)
            lines.append(f"~{lo}-{hi} raw dmg")

        line_h = font.get_height() + 3
        tip_w = max_w
        tip_h = padding * 2 + len(lines) * line_h
        tip_x = btn_rect.x
        tip_y = btn_rect.y - tip_h - 6
        if tip_y < 10:
            tip_y = btn_rect.bottom + 6

        # Background + border
        bg = pygame.Surface((tip_w, tip_h), pygame.SRCALPHA)
        bg.fill((10, 8, 20, 230))
        surface.blit(bg, (tip_x, tip_y))
        pygame.draw.rect(surface, C.PARCHMENT_EDGE, (tip_x, tip_y, tip_w, tip_h), 1, border_radius=3)

        for i, l in enumerate(lines):
            color = C.PARCHMENT_EDGE if i == len(lines) - 1 else C.INK
            draw_text_with_glow(surface, l, font, color,
                                tip_x + padding, tip_y + padding + i * line_h)

    # ── Status tooltips ────────────────────────────────────────────────────────

    def _draw_status_tooltips(self, surface):
        """Check hover over status icons and draw tooltips for both enemy and player."""
        mx, my = pygame.mouse.get_pos()

        # Check enemy status icons
        for rect, effect_type in self._enemy_status_rects:
            if rect.collidepoint(mx, my):
                draw_status_tooltip(surface, effect_type, rect, self.assets.fonts["tiny"])
                return  # Only show one tooltip at a time

        # Check player status icons
        for rect, effect_type in self._player_status_rects:
            if rect.collidepoint(mx, my):
                draw_status_tooltip(surface, effect_type, rect, self.assets.fonts["tiny"])
                return

    # ── Enemy intent panel ─────────────────────────────────────────────────────

    def _draw_enemy_intent(self, surface, panel_x, panel_y, ox, oy):
        """Draw the enemy intent panel showing what the enemy will do next turn.

        Displays:
        - Intent icon (based on skill type)
        - Skill name
        - Estimated damage or effect description

        Position: Above the enemy info panel for clear visibility.
        """
        c = self.game.state.combat
        skill = c.next_enemy_skill
        if not skill:
            return

        # Main enemy panel dimensions (must match values in draw method)
        panel_w = 495
        panel_h = 100

        # Intent panel positioning - ABOVE the main enemy panel for clear visibility
        intent_w = 220
        intent_h = 55
        intent_x = panel_x + panel_w - intent_w + ox
        intent_y = panel_y - intent_h - 10 + oy  # Position above enemy panel

        # Determine intent type and colors
        skill_type = skill.get("type", "")
        if "magic" in skill_type or "spell" in skill_type:
            intent_color = C.ELDRITCH
            intent_icon = "*"
            intent_label = "Magic"
        elif "buff" in skill_type or "heal" in skill_type:
            intent_color = C.MIST
            intent_icon = "+"
            intent_label = "Buff"
        elif "debuff" in skill_type:
            intent_color = C.HP_YELLOW
            intent_icon = "!"
            intent_label = "Debuff"
        else:
            intent_color = C.CRIMSON
            intent_icon = "!"
            intent_label = "Attack"

        # Pulsing animation
        pulse = abs(math.sin(self._intent_pulse * 3))
        glow_alpha = int(40 + 30 * pulse)

        # Draw intent panel background with glow
        intent_bg = pygame.Surface((intent_w, intent_h), pygame.SRCALPHA)
        intent_bg.fill((10, 8, 20, 200))
        # Glow effect
        glow_surf = pygame.Surface((intent_w + 16, intent_h + 16), pygame.SRCALPHA)
        glow_r, glow_g, glow_b = intent_color
        for i in range(8):
            alpha = int((8 - i) * 4 + glow_alpha * 0.5)
            pygame.draw.rect(glow_surf, (glow_r, glow_g, glow_b, alpha),
                           (8 - i, 8 - i, intent_w + i * 2, intent_h + i * 2), 1)
        surface.blit(glow_surf, (intent_x - 8, intent_y - 8))
        surface.blit(intent_bg, (intent_x, intent_y))
        pygame.draw.rect(surface, intent_color, (intent_x, intent_y, intent_w, intent_h), 2, border_radius=4)

        # Intent label at top
        draw_text_with_glow(surface, f"NEXT: {intent_label}", self.assets.fonts["tiny"],
                           intent_color, intent_x + 8, intent_y + 4, glow_color=intent_color)

        # Skill name
        skill_name = fit_text(self.assets.fonts["small"], skill.get("name", "Unknown"), intent_w - 16)
        draw_text_with_glow(surface, skill_name, self.assets.fonts["small"],
                           C.PARCHMENT_EDGE, intent_x + intent_w // 2, intent_y + 24,
                           align="center", glow_color=intent_color)

        # Draw small intent indicator icon
        icon_x = intent_x + intent_w - 28
        icon_y = intent_y + 8
        icon_radius = 10
        pygame.draw.circle(surface, intent_color, (icon_x + icon_radius, icon_y + icon_radius), icon_radius)
        pygame.draw.circle(surface, tuple(min(255, c + 60) for c in intent_color),
                         (icon_x + icon_radius, icon_y + icon_radius), icon_radius, 2)
        # Icon letter - use light color for contrast
        icon_font = self.assets.fonts["tiny"]
        icon_text = icon_font.render(intent_icon, True, C.BONE)
        icon_rect = icon_text.get_rect(center=(icon_x + icon_radius, icon_y + icon_radius))
        surface.blit(icon_text, icon_rect)

    # ── Main draw method ───────────────────────────────────────────────────────

    def draw(self, surface):
        s = self.game.state
        c = s.combat
        if not c:
            return
        e = c.enemy

        # Enhanced directional screen shake
        ox, oy = 0, 0
        if self.shake_timer > 0:
            if self.shake_direction == 1:  # Horizontal only
                ox = random.randint(-self.shake_intensity, self.shake_intensity)
                oy = 0
            elif self.shake_direction == 2:  # Vertical only
                ox = 0
                oy = random.randint(-self.shake_intensity, self.shake_intensity)
            else:  # Random (default)
                ox = random.randint(-self.shake_intensity, self.shake_intensity)
                oy = random.randint(-self.shake_intensity, self.shake_intensity)

        draw_hud(surface, s, self.assets)

        # Particles (behind UI elements)
        for p in self.particles:
            ps = pygame.Surface((p["size"] * 2, p["size"] * 2), pygame.SRCALPHA)
            ps.fill((*p["color"], int(p["alpha"])))
            surface.blit(ps, (int(p["x"]) + ox, int(p["y"]) + oy))

        # --- Enemy info panel (compact nameplate above sprite) ---
        # During victory, HP bar shows draining animation
        if self._victory_state == "hp_drain":
            e_hp_pct = max(0, self._victory_hp_display / e.max_hp * 100)
        elif self._victory_state:
            e_hp_pct = 0  # Zero during disintegrate/pause
        else:
            e_hp_pct = max(0, e.hp / e.max_hp * 100)

        panel_w = 495
        panel_h = 100
        sprite_w = 240
        sprite_x = SCREEN_W - sprite_w - 40 + ox
        sprite_y = 202 + oy
        panel_x = sprite_x + sprite_w - panel_w
        panel_y = 120
        draw_parchment_panel(surface, panel_x, panel_y, panel_w, panel_h)

        if c.is_boss:
            draw_text_with_glow(surface, "BOSS", self.assets.fonts["tiny"], C.CRIMSON, panel_x + 12, panel_y + 5)
        draw_text_with_glow(surface, e.name, self.assets.fonts["small"], C.PARCHMENT_EDGE, panel_x + 12, panel_y + 22)

        # Enemy HP bar — during victory animation, show draining HP
        if self._victory_state == "hp_drain":
            display_hp = max(0, int(self._victory_hp_display))
            draw_bar(surface, panel_x + 12, panel_y + 44, 330, 14, display_hp, e.max_hp,
                     hp_color(display_hp, e.max_hp))
            draw_text_with_glow(surface, f"{display_hp}/{e.max_hp}", self.assets.fonts["tiny"],
                      C.INK, panel_x + 350, panel_y + 44)
        elif self._victory_state:
            # Empty bar during disintegrate/pause
            draw_bar(surface, panel_x + 12, panel_y + 44, 330, 14, 0, e.max_hp, C.CRIMSON)
            draw_text_with_glow(surface, f"0/{e.max_hp}", self.assets.fonts["tiny"],
                      C.CRIMSON, panel_x + 350, panel_y + 44)
        else:
            draw_bar(surface, panel_x + 12, panel_y + 44, 330, 14, e.hp, e.max_hp,
                     hp_color(e.hp, e.max_hp))
            draw_text_with_glow(surface, f"{e.hp}/{e.max_hp}", self.assets.fonts["tiny"],
                      C.INK, panel_x + 350, panel_y + 44)

        # Enemy status icons — below HP bar, left side (hide during victory)
        if not self._victory_state:
            enemy_statuses = list(e.statuses)
            if e.stunned:
                from engine.models import StatusEffect
                stun_se = StatusEffect("stunned", 1)
                enemy_statuses = [stun_se] + enemy_statuses
            self._enemy_status_rects = draw_status_icons_row(
                surface, panel_x + 12, panel_y + 65, enemy_statuses, {},
                size=26, gap=5
            )

        # ─────────────────────────────────────────────────────────────────────────────
        # ENEMY INTENT DISPLAY PANEL
        # Shows what the enemy will do on their next turn
        # ─────────────────────────────────────────────────────────────────────────────
        if not self._victory_state and c.next_enemy_skill:
            self._draw_enemy_intent(surface, panel_x, panel_y, ox, oy)

        # --- Enemy sprite rendering ---
        if self._victory_state == "disintegrate":
            # Draw disintegration fragments
            for f in self._fragments:
                if f["alpha"] <= 0:
                    continue
                frag_surf = pygame.Surface((f["w"], f["h"]), pygame.SRCALPHA)
                r, g, b = f["color"]
                a = max(0, min(255, int(f["alpha"])))
                frag_surf.fill((r, g, b, a))
                # Apply rotation
                if abs(f["rot"]) > 0.5:
                    frag_surf = pygame.transform.rotate(frag_surf, f["rot"])
                surface.blit(frag_surf, (int(f["x"]) + ox - f["w"] // 2, int(f["y"]) + oy - f["h"] // 2))
        elif self._victory_state == "dramatic_pause":
            # No sprite — just particles, maybe a faint ghostly outline
            if self._victory_timer < 0.5:
                # Brief ghost flash of the enemy sprite
                enemy_sprite = self.assets.get_sprite(e.name)
                if enemy_sprite:
                    ghost = enemy_sprite.copy()
                    ghost.set_alpha(int(60 * (1.0 - self._victory_timer * 2)))
                    surface.blit(ghost, (sprite_x, sprite_y))
        elif self._victory_state == "hp_drain":
            # Normal sprite, but with red flash during drain
            enemy_sprite = self.assets.get_sprite(e.name)
            if enemy_sprite:
                # Pulsing red tint during drain
                pulse = abs(math.sin(self._victory_timer * 8))
                flash_alpha = int(40 + 40 * pulse)
                flash = enemy_sprite.copy()
                flash_overlay = pygame.Surface(flash.get_size(), pygame.SRCALPHA)
                flash_overlay.fill((255, 30, 30, flash_alpha))
                flash.blit(flash_overlay, (0, 0))
                surface.blit(flash, (sprite_x, sprite_y))
        else:
            # Normal combat sprite
            enemy_sprite = self.assets.get_sprite(e.name)
            if enemy_sprite:
                # Flash overlay when enemy acts
                if self._enemy_flash_timer > 0:
                    flash = enemy_sprite.copy()
                    flash_overlay = pygame.Surface(flash.get_size(), pygame.SRCALPHA)
                    flash_overlay.fill((255, 60, 60, int(80 * (self._enemy_flash_timer / 0.25))))
                    flash.blit(flash_overlay, (0, 0))
                    surface.blit(flash, (sprite_x, sprite_y))
                else:
                    surface.blit(enemy_sprite, (sprite_x, sprite_y))

        # Enemy action floating text — eldritch styled
        if self._enemy_action_text:
            text, fx, fy, color, timer, vy = self._enemy_action_text
            # Fade alpha based on remaining time
            alpha_ratio = min(1.0, timer / 0.5) if timer < 0.5 else 1.0
            font = self.assets.fonts["small"]
            # Wave distortion for otherworldly feel
            wave_offset = math.sin(self._time * 5.0 + fx * 0.02) * 4
            # Eldritch purple tint
            eld_action_color = (
                max(0, min(255, color[0] + 30)),
                max(0, min(255, color[1] + 10)),
                max(0, min(255, color[2] + 60)),
            )
            # Ghostly trailing shadow
            shadow_surf = font.render(text, True, (80, 30, 120))
            shadow_surf.set_alpha(int(120 * alpha_ratio))
            shadow_rect = shadow_surf.get_rect(center=(int(fx) + wave_offset + 3, int(fy) + 3))
            surface.blit(shadow_surf, shadow_rect)
            # Main text
            text_surf = font.render(text, True, eld_action_color)
            text_surf.set_alpha(int(255 * alpha_ratio))
            text_rect = text_surf.get_rect(center=(int(fx) + wave_offset, int(fy)))
            surface.blit(text_surf, text_rect)

        # --- Character sprite (left side) — hidden during dramatic pause ---
        if not self._victory_state or self._victory_state == "hp_drain":
            class_sprite = self.assets.get_class_combat(s.class_id)
            if class_sprite:
                # Player hit flash effect - red flash when taking damage
                if self._player_hit_flash > 0:
                    flash = class_sprite.copy()
                    flash_overlay = pygame.Surface(flash.get_size(), pygame.SRCALPHA)
                    # Directional flash based on damage source (enemy is on the right)
                    if self._player_hit_direction == 1:  # Damage from right
                        flash_overlay.fill((255, 30, 30, int(100 * (self._player_hit_flash / 0.3))))
                    else:  # Damage from left
                        flash_overlay.fill((255, 50, 50, int(80 * (self._player_hit_flash / 0.3))))
                    flash.blit(flash_overlay, (0, 0))
                    surface.blit(flash, (30 + ox, 250 + oy))
                else:
                    surface.blit(class_sprite, (30 + ox, 250 + oy))

        # --- Combat log (center, parchment panel) — dimmed during victory ---
        log_x, log_y = 280, 250
        log_w, log_h = 560, 180
        draw_parchment_panel(surface, log_x, log_y, log_w, log_h)
        if self._victory_state == "dramatic_pause":
            # Show dramatic victory text in the log panel
            alpha = min(255, int(self._victory_timer * 400))
            if self._victory_is_boss:
                victory_lines = [
                    "The Spiral collapses.",
                    "Hastur screams as reality reasserts itself.",
                    "The Yellow Sign fades to a whisper.",
                ]
            else:
                victory_lines = [
                    "The creature dissolves into shadow.",
                    "The air grows still. You survive.",
                ]
            draw_text_with_glow(surface, "— VICTORY —", self.assets.fonts["body"],
                      C.PARCHMENT_EDGE, log_x + log_w // 2, log_y + 40, align="center")
            for i, line in enumerate(victory_lines):
                line_alpha = min(255, max(0, alpha - i * 60))
                if line_alpha > 0:
                    draw_text_with_glow(surface, line, self.assets.fonts["tiny"],
                              C.INK_LIGHT, log_x + log_w // 2, log_y + 70 + i * 24, align="center")
        else:
            draw_text_with_glow(surface, "Combat Log", self.assets.fonts["tiny"], C.PARCHMENT_EDGE, log_x + 15, log_y + 8)
            draw_gold_divider(surface, log_x + 15, log_y + 26, log_w - 30)
            if c.log:
                for i, (text, log_type) in enumerate(c.log[-5:]):
                    colors = {"damage": C.CRIMSON, "crit": C.PARCHMENT_EDGE, "heal": C.MIST,
                              "shield": C.FROST, "effect": C.ELDRITCH, "info": C.INK_LIGHT}
                    color = colors.get(log_type, C.INK)
                    text = fit_text(self.assets.fonts["tiny"], text, log_w - 30)
                    draw_text_with_glow(surface, text, self.assets.fonts["tiny"], color,
                              log_x + 15, log_y + 32 + i * 26)

        # --- Skills panel (hidden during victory animation) ---
        if not self._victory_state:
            draw_text_with_glow(surface, "Your Abilities", self.assets.fonts["small"], C.INK, 30, 440)
            for i, (sk, btn) in enumerate(zip(s.active_skills, self.skill_buttons)):
                on_cd = sk.current_cd > 0

                label = f"[{i+1}] {sk.name}"
                if on_cd:
                    label += f" (CD:{sk.current_cd})"
                if sk.cost > 0:
                    label += f" ({sk.cost} MAD)"
                label = fit_text(self.assets.fonts["small"], label, btn.w - 20)
                draw_ornate_button(surface, btn, label, self.assets.fonts["small"],
                                   hover=(i == self.hover_idx and not on_cd),
                                   color=C.CRIMSON if on_cd else C.PARCHMENT_EDGE, disabled=on_cd)

            # Skill tooltip popup on hover (above the button, like class select)
            if 0 <= self.hover_idx < len(s.active_skills):
                sk = s.active_skills[self.hover_idx]
                self._draw_skill_tooltip(surface, sk, self.skill_buttons[self.hover_idx])

            # Player status icons — vertical column to the right of skills
            icon_x = 620
            icon_y = 460
            icon_size = 28
            icon_gap = 6
            self._player_status_rects = []
            # Debuffs first, then buffs
            all_player_effects = []
            for st in s.statuses:
                all_player_effects.append((st.type, st.duration))
            for bt, dur in sorted(s.buffs.items()):
                if dur <= 0 or bt in ("darkRegenBuff",):
                    continue
                all_player_effects.append((bt, dur))
            if s.barrier > 0:
                all_player_effects.append(("barrier", s.barrier))
            # Draw in vertical column, wrapping to second column if needed
            col_max = 5  # icons per column before wrapping
            for idx, (etype, dur) in enumerate(all_player_effects):
                col = idx // col_max
                row = idx % col_max
                cx = icon_x + col * (icon_size + icon_gap)
                cy = icon_y + row * (icon_size + icon_gap)
                from shared.rendering import draw_status_icon
                rect = draw_status_icon(surface, cx, cy, etype, dur, icon_size)
                self._player_status_rects.append((rect, etype))

            # Command buttons
            can_run = not c.is_boss
            cmd_names = list(self.cmd_buttons.keys())
            for ci, (name, btn) in enumerate(self.cmd_buttons.items()):
                labels = {"run": "Run [R]", "inventory": "[I]", "save": "[S]"}
                draw_ornate_button(surface, btn, labels[name], self.assets.fonts["tiny"],
                                   hover=((len(s.active_skills) + ci) == self.hover_idx),
                                   color=C.CRIMSON if name == "run" else C.PARCHMENT_EDGE,
                                   disabled=(name == "run" and not can_run))

        # Turn message popup
        if self.turn_msg_timer > 0 and self.turn_message:
            draw_text_with_glow(surface, self.turn_message, self.assets.fonts["body"],
                      C.CRIMSON, SCREEN_W // 2, 245, align="center")

        # --- "DEFEATED" text overlay during dramatic pause and fade ---
        if self._victory_state in ("dramatic_pause", "fade_out"):
            alpha = min(255, int(self._victory_timer * 500)) if self._victory_state == "dramatic_pause" else 255
            if alpha > 0:
                # Render "DEFEATED" with glow, centered on screen
                defeated_surf = self.assets.fonts["heading"].render("D E F E A T E D", True, C.PARCHMENT_EDGE)
                defeated_surf.set_alpha(alpha)
                defeated_rect = defeated_surf.get_rect(center=(SCREEN_W // 2, 150))
                surface.blit(defeated_surf, defeated_rect)
                # Gold underline that grows
                line_w = min(300, int(self._victory_timer * 300)) if self._victory_state == "dramatic_pause" else 300
                if line_w > 0:
                    draw_gold_divider(surface, SCREEN_W // 2 - line_w // 2, 175, line_w)

        # --- Victory fade-to-black overlay ---
        if self._victory_fade_alpha > 0:
            fade_surf = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
            fade_surf.fill((0, 0, 0, self._victory_fade_alpha))
            surface.blit(fade_surf, (0, 0))

        # ═══════════════════════════════════════════════════════════════════════════════
        # ELDRITCH FLOATING DAMAGE NUMBERS — Victorian Writhe System
        # Restrained menace: purple, red, and yellow only.
        # Cinzel Decorative Bold — refined, elegant, wrong.
        # ═══════════════════════════════════════════════════════════════════════════════

        # Palette: dark menacing Victorian colors - deep purples, blood crimsons, tarnished golds
        _PURPLE = (90, 40, 110)           # Deep dark purple
        _PURPLE_DEEP = (50, 15, 80)        # Even darker purple shadow
        _PURPLE_VOID = (30, 5, 50)         # Near-black purple void
        _CRIMSON = (120, 20, 35)           # Dark blood red
        _CRIMSON_DARK = (70, 10, 20)       # Dried blood crimson
        _GOLD = (160, 120, 20)             # Dark tarnished gold
        _GOLD_BRIGHT = (190, 150, 30)      # Slightly brighter dark gold

        # Victorian decorative runes
        _ELDRITCH_RUNES = ["\u2020", "\u2726", "\u263D", "\u2694", "\u2736", "\u2625", "\u271D"]

        for dn in self.damage_numbers:
            text, x, y, color, timer, vy, scale, is_crit = dn[:8]

            # ── Font selection ──
            if is_crit:
                base_font = self.assets.fonts.get("eldritch_crit") or self.assets.fonts["heading"]
            else:
                base_font = self.assets.fonts.get("eldritch") or self.assets.fonts["heading"]

            # No scaling - static, stark presentation
            scaled_font = base_font

            # ── NO wave distortion - completely static, menacing presence ──
            base_draw_x = int(x) + ox
            base_draw_y = int(y) + oy

            # ── NO flickering - solid, unwavering display ──
            alpha_mod = 255

            # ── SIMPLE RENDERING - no per-character effects, just cold numbers ──
            text_surface = scaled_font.render(text, True, color)

            # Add simple shadow for depth (no fancy trails)
            shadow_color = (30, 5, 50)  # Deep purple void
            shadow_surface = scaled_font.render(text, True, shadow_color)
            shadow_offset = 2 if is_crit else 1

            # Draw shadow
            surface.blit(shadow_surface, (base_draw_x - text_surface.get_width()//2 + shadow_offset,
                                          base_draw_y - text_surface.get_height()//2 + shadow_offset))

            # Draw main text
            surface.blit(text_surface, (base_draw_x - text_surface.get_width()//2,
                                        base_draw_y - text_surface.get_height()//2))

            # For crits only: add a subtle crimson glow pulse
            if is_crit:
                glow_alpha = int(60 + 40 * math.sin(self._time * 6.0))
                glow_surface = scaled_font.render(text, True, (120, 20, 35))  # Dark blood red
                glow_surface.set_alpha(glow_alpha)
                surface.blit(glow_surface, (base_draw_x - text_surface.get_width()//2,
                                            base_draw_y - text_surface.get_height()//2))

        # Status effect tooltips on hover
        self._draw_status_tooltips(surface)

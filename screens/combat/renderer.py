import pygame
import math
import random
from shared import (
    C,
    SCREEN_W,
    SCREEN_H,
    draw_text,
    draw_text_wrapped,
    draw_text_fitted,
    fit_text,
    draw_bar,
    draw_ornate_panel,
    draw_ornate_button,
    draw_gold_divider,
    hp_color,
    mad_color,
    draw_parchment_panel,
    draw_text_with_glow,
    draw_status_icons_row,
    draw_status_tooltip,
    generate_parchment_texture,
    draw_hud,
)
from shared.game_context import GameContext
from shared.rendering import ease_out_cubic, ease_in_cubic, ease_in_quad
from shared.surface_pool import surface_pool, render_cache
from engine import calc_preview_damage, _get_enemy_intent_message
from screens.combat.particles import create_particle, PARTICLE_TYPES


class CombatRendererMixin:
    """Mixin providing all draw/render methods for CombatScreen.

    This mixin assumes ``self`` has the full CombatScreen attribute set
    (ctx, assets, particles, damage_numbers, etc.) so it can be mixed
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
        base_dmg, final_dmg = calc_preview_damage(self.ctx.state, sk)
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

        # Background + border — use pooled surface
        bg = surface_pool.acquire(tip_w, tip_h)
        bg.fill((10, 8, 20, 230))
        surface.blit(bg, (tip_x, tip_y))
        surface_pool.release(bg)
        pygame.draw.rect(surface, C.PARCHMENT_EDGE, (tip_x, tip_y, tip_w, tip_h), 1, border_radius=3)

        for i, l in enumerate(lines):
            color = C.PARCHMENT_EDGE if i == len(lines) - 1 else C.INK
            draw_text_with_glow(surface, l, font, color, tip_x + padding, tip_y + padding + i * line_h)

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
        c = self.ctx.state.combat
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

        # Draw intent panel background with glow — use pooled surfaces
        intent_bg = surface_pool.acquire(intent_w, intent_h)
        intent_bg.fill((10, 8, 20, 200))
        # Glow effect — use pooled surface
        glow_surf = surface_pool.acquire(intent_w + 16, intent_h + 16)
        glow_r, glow_g, glow_b = intent_color
        for i in range(8):
            alpha = int((8 - i) * 4 + glow_alpha * 0.5)
            pygame.draw.rect(
                glow_surf, (glow_r, glow_g, glow_b, alpha), (8 - i, 8 - i, intent_w + i * 2, intent_h + i * 2), 1
            )
        surface.blit(glow_surf, (intent_x - 8, intent_y - 8))
        surface.blit(intent_bg, (intent_x, intent_y))
        surface_pool.release(glow_surf)
        surface_pool.release(intent_bg)
        pygame.draw.rect(surface, intent_color, (intent_x, intent_y, intent_w, intent_h), 2, border_radius=4)

        # Intent label at top
        draw_text_with_glow(
            surface,
            f"NEXT: {intent_label}",
            self.assets.fonts["tiny"],
            intent_color,
            intent_x + 8,
            intent_y + 4,
            glow_color=intent_color,
        )

        # Skill name
        skill_name = fit_text(self.assets.fonts["small"], skill.get("name", "Unknown"), intent_w - 16)
        draw_text_with_glow(
            surface,
            skill_name,
            self.assets.fonts["small"],
            C.PARCHMENT_EDGE,
            intent_x + intent_w // 2,
            intent_y + 24,
            align="center",
            glow_color=intent_color,
        )

        # Draw small intent indicator icon
        icon_x = intent_x + intent_w - 28
        icon_y = intent_y + 8
        icon_radius = 10
        pygame.draw.circle(surface, intent_color, (icon_x + icon_radius, icon_y + icon_radius), icon_radius)
        pygame.draw.circle(
            surface,
            tuple(min(255, c + 60) for c in intent_color),
            (icon_x + icon_radius, icon_y + icon_radius),
            icon_radius,
            2,
        )
        # Icon letter - use light color for contrast
        icon_font = self.assets.fonts["tiny"]
        icon_text = icon_font.render(intent_icon, True, C.BONE)
        icon_rect = icon_text.get_rect(center=(icon_x + icon_radius, icon_y + icon_radius))
        surface.blit(icon_text, icon_rect)

    # ── Main draw method ───────────────────────────────────────────────────────

    def draw(self, surface):
        s = self.ctx.state
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

        # Particles (behind UI elements) — use pooled surfaces
        for p in self.particles:
            sz = p["size"] * 2
            ps = surface_pool.acquire(sz, sz)
            ps.fill((*p["color"], int(p["alpha"])))
            surface.blit(ps, (int(p["x"]) + ox, int(p["y"]) + oy))
            surface_pool.release(ps)

        # --- Enemy info panel (compact nameplate above sprite) ---
        # During horror death animation, panel glitches
        panel_w = 495
        panel_h = 100
        sprite_w = 240
        sprite_x = SCREEN_W - sprite_w - 40 + ox
        sprite_y = 202 + oy
        panel_x = sprite_x + sprite_w - panel_w
        panel_y = 120

        # Panel position jitter during glitch phases
        panel_ox, panel_oy = 0, 0
        if self._victory_state in ("glitch_onset", "reality_break"):
            panel_ox = int(self._glitch_bar_flicker)
            panel_oy = int(random.uniform(-2, 2) * self._glitch_intensity)

        draw_parchment_panel(surface, panel_x + panel_ox, panel_y + panel_oy, panel_w, panel_h)

        if c.is_boss:
            draw_text_with_glow(
                surface, "BOSS", self.assets.fonts["tiny"], C.CRIMSON, panel_x + 12 + panel_ox, panel_y + 5 + panel_oy
            )

        # Enemy name — corrupted during glitch phases
        if self._victory_state in ("glitch_onset", "reality_break"):
            display_name = self._glitch_name_corrupted
            # RGB split on the name text
            name_x = panel_x + 12 + panel_ox
            name_y = panel_y + 22 + panel_oy
            name_font = self.assets.fonts["small"]
            # Red channel offset
            red_offset = int(self._glitch_intensity * random.uniform(2, 6))
            # Blue channel offset
            blue_offset = int(self._glitch_intensity * random.uniform(2, 6))
            # Render RGB split layers
            red_surf = name_font.render(display_name, True, (200, 0, 0))
            blue_surf = name_font.render(display_name, True, (0, 0, 200))
            main_surf = name_font.render(display_name, True, C.ELDRITCH_PURPLE)
            surface.blit(red_surf, (name_x + red_offset, name_y))
            surface.blit(blue_surf, (name_x - blue_offset, name_y))
            surface.blit(main_surf, (name_x, name_y))
        else:
            draw_text_with_glow(
                surface,
                e.name,
                self.assets.fonts["small"],
                C.PARCHMENT_EDGE,
                panel_x + 12 + panel_ox,
                panel_y + 22 + panel_oy,
            )

        # Enemy HP bar — glitch effects during death animation
        bar_x = panel_x + 12 + panel_ox
        bar_y = panel_y + 44 + panel_oy
        bar_w = 330
        bar_h = 14

        if self._victory_state in ("glitch_onset", "reality_break"):
            if self._glitch_bar_snap:
                # Bar has snapped to 0 — show empty with glitch
                draw_bar(surface, bar_x, bar_y, bar_w, bar_h, 0, e.max_hp, C.CRIMSON)
                # Glitch text: scrambled numbers
                glitch_text = f"{''.join(random.choice('0123456789-!?') for _ in range(3))}/{e.max_hp}"
                draw_text_with_glow(
                    surface, glitch_text, self.assets.fonts["tiny"], C.CRIMSON, panel_x + 350 + panel_ox, bar_y
                )
            else:
                # Flickering bar — random value jumps
                if random.random() < self._glitch_intensity * 0.3:
                    # Brief flash to wrong value
                    flicker_hp = random.randint(0, e.max_hp)
                    bar_color = C.ELDRITCH_PURPLE if random.random() < 0.3 else hp_color(flicker_hp, e.max_hp)
                    draw_bar(surface, bar_x, bar_y, bar_w, bar_h, flicker_hp, e.max_hp, bar_color)
                    draw_text_with_glow(
                        surface,
                        f"{flicker_hp}/{e.max_hp}",
                        self.assets.fonts["tiny"],
                        C.ELDRITCH_PURPLE,
                        panel_x + 350 + panel_ox,
                        bar_y,
                    )
                else:
                    # Normal HP display but with jitter offset
                    draw_bar(surface, bar_x, bar_y, bar_w, bar_h, e.hp, e.max_hp, hp_color(e.hp, e.max_hp))
                    draw_text_with_glow(
                        surface, f"{e.hp}/{e.max_hp}", self.assets.fonts["tiny"], C.INK, panel_x + 350 + panel_ox, bar_y
                    )
            # Horizontal scanline glitch on bar
            if random.random() < self._glitch_intensity * 0.4:
                glitch_y = bar_y + random.randint(0, bar_h)
                glitch_w = random.randint(30, bar_w)
                glitch_x = bar_x + random.randint(0, bar_w - glitch_w)
                glitch_surf = surface_pool.acquire(glitch_w, 2)
                glitch_surf.fill((140, 60, 180, int(180 * self._glitch_intensity)))
                surface.blit(glitch_surf, (glitch_x, glitch_y))
                surface_pool.release(glitch_surf)
        elif self._victory_state:
            # After reality_break: empty bar
            draw_bar(surface, bar_x, bar_y, bar_w, bar_h, 0, e.max_hp, (30, 5, 50))
            draw_text_with_glow(
                surface, f"0/{e.max_hp}", self.assets.fonts["tiny"], (30, 5, 50), panel_x + 350 + panel_ox, bar_y
            )
        else:
            # Normal combat
            draw_bar(surface, bar_x, bar_y, bar_w, bar_h, e.hp, e.max_hp, hp_color(e.hp, e.max_hp))
            draw_text_with_glow(
                surface, f"{e.hp}/{e.max_hp}", self.assets.fonts["tiny"], C.INK, panel_x + 350 + panel_ox, bar_y
            )

        # Enemy status icons — below HP bar, left side (hide during victory)
        if not self._victory_state:
            enemy_statuses = list(e.statuses)
            if e.stunned:
                from engine.models import StatusEffect

                stun_se = StatusEffect("stunned", 1)
                enemy_statuses = [stun_se] + enemy_statuses
            self._enemy_status_rects = draw_status_icons_row(
                surface, panel_x + 12, panel_y + 65, enemy_statuses, {}, size=26, gap=5
            )

        # ─────────────────────────────────────────────────────────────────────────────
        # ENEMY INTENT DISPLAY PANEL
        # Shows what the enemy will do on their next turn
        # ─────────────────────────────────────────────────────────────────────────────
        if not self._victory_state and c.next_enemy_skill:
            self._draw_enemy_intent(surface, panel_x, panel_y, ox, oy)

        # --- Enemy sprite rendering ---
        if self._victory_state == "glitch_onset":
            # Sprite with subtle flicker/distortion
            enemy_sprite = self.assets.get_sprite(e.name)
            if enemy_sprite:
                # Scale to combat size
                sw, sh = enemy_sprite.get_size()
                if sw != sprite_w:
                    enemy_sprite = pygame.transform.scale(enemy_sprite, (sprite_w, int(sh * sprite_w / sw)))
                # Occasional color flicker
                if random.random() < self._glitch_intensity * 0.15:
                    # Flash purple tint
                    flash = enemy_sprite.copy()
                    flash_overlay = surface_pool.acquire(flash.get_width(), flash.get_height())
                    flash_overlay.fill((140, 60, 180, int(60 * self._glitch_intensity)))
                    flash.blit(flash_overlay, (0, 0))
                    surface.blit(flash, (sprite_x + int(random.uniform(-2, 2) * self._glitch_intensity), sprite_y))
                    surface_pool.release(flash_overlay)
                else:
                    # Slight horizontal displacement
                    jitter_x = int(random.uniform(-1, 1) * self._glitch_intensity * 3)
                    surface.blit(enemy_sprite, (sprite_x + jitter_x, sprite_y))

        elif self._victory_state == "reality_break":
            # More intense distortion, sprite warps
            enemy_sprite = self.assets.get_sprite(e.name)
            if enemy_sprite:
                sw, sh = enemy_sprite.get_size()
                if sw != sprite_w:
                    enemy_sprite = pygame.transform.scale(enemy_sprite, (sprite_w, int(sh * sprite_w / sw)))
                # Draw sprite with horizontal shear/slice distortion
                src_w, src_h = enemy_sprite.get_size()
                dest_surface = surface_pool.acquire(src_w + 20, src_h)
                # Slice sprite into horizontal strips with random offsets
                strip_h = 4
                for sy in range(0, src_h, strip_h):
                    strip = enemy_sprite.subsurface((0, sy, src_w, min(strip_h, src_h - sy)))
                    # Random horizontal offset per strip — increases with glitch intensity
                    offset_x = int(random.uniform(-8, 8) * self._glitch_intensity)
                    dest_surface.blit(strip, (10 + offset_x, sy))
                # Color overlay — pulsing between purple and crimson
                color_flash = surface_pool.acquire(dest_surface.get_width(), dest_surface.get_height())
                pulse_color = C.ELDRITCH_PURPLE if random.random() < 0.5 else C.CRIMSON
                color_flash.fill((*pulse_color, int(40 * self._glitch_intensity)))
                dest_surface.blit(color_flash, (0, 0), special_flags=pygame.BLEND_RGBA_ADD)
                surface.blit(dest_surface, (sprite_x - 10, sprite_y))
                surface_pool.release(color_flash)
                surface_pool.release(dest_surface)

        elif self._victory_state == "glitch_vanish":
            # Sprite glitches harder and harder, fading out — no implosion, just decay
            if self._vanish_opacity > 0:
                enemy_sprite = self.assets.get_sprite(e.name)
                if enemy_sprite:
                    sw, sh = enemy_sprite.get_size()
                    if sw != sprite_w:
                        enemy_sprite = pygame.transform.scale(enemy_sprite, (sprite_w, int(sh * sprite_w / sw)))
                    src_w, src_h = enemy_sprite.get_size()
                    progress = self._vanish_progress

                    # Build the glitched sprite: horizontal strips with severe offsets
                    dest_surface = surface_pool.acquire(src_w + 40, src_h + 20)
                    strip_h = 3 if progress > 0.5 else 4
                    for sy in range(0, src_h, strip_h):
                        strip = enemy_sprite.subsurface((0, sy, src_w, min(strip_h, src_h - sy)))
                        # Increasingly extreme horizontal offsets as progress climbs
                        max_offset = 6 + progress * 18
                        offset_x = int(random.uniform(-max_offset, max_offset))
                        # Occasional vertical displacement for advanced glitch
                        offset_y = 0
                        if progress > 0.5 and random.random() < 0.2:
                            offset_y = int(random.uniform(-4, 4) * progress)
                        dest_surface.blit(strip, (20 + offset_x, sy + offset_y))

                    # Apply per-column distortion from the wobble table
                    if len(self._vanish_distortion) > 0 and src_w > 10:
                        # Create a copy to apply column distortion
                        distorted = surface_pool.acquire(dest_surface.get_width(), dest_surface.get_height())
                        col_w = max(1, src_w // len(self._vanish_distortion))
                        for i, offset in enumerate(self._vanish_distortion):
                            col_x = 20 + i * col_w
                            actual_w = min(col_w, src_w - i * col_w)
                            if actual_w <= 0 or col_x >= dest_surface.get_width() - 20:
                                continue
                            # Clamp subsurface bounds
                            sub_x = min(col_x, dest_surface.get_width() - actual_w)
                            sub_h = min(src_h, dest_surface.get_height())
                            if sub_x >= 0 and actual_w > 0 and sub_h > 0:
                                strip = dest_surface.subsurface((sub_x, 0, actual_w, sub_h))
                                distorted.blit(strip, (col_x, int(offset * progress * 4)))
                        surface_pool.release(dest_surface)  # Release original before reassign
                        dest_surface = distorted

                    # Color corruption — patches of wrong colors
                    if progress > 0.3:
                        num_patches = int(3 + progress * 8)
                        for _ in range(num_patches):
                            patch_w = random.randint(8, 40)
                            patch_h = random.randint(4, 20)
                            patch_x = random.randint(0, src_w - patch_w)
                            patch_y = random.randint(0, src_h - patch_h)
                            patch_color = random.choice(
                                [
                                    (140, 60, 180),
                                    (90, 30, 110),
                                    (50, 15, 80),
                                    (200, 80, 150),
                                    (30, 5, 50),
                                    C.CRIMSON,
                                    C.YELLOW,
                                ]
                            )
                            patch_alpha = int(random.uniform(30, 100) * progress)
                            patch_surf = surface_pool.acquire(patch_w, patch_h)
                            patch_surf.fill((*patch_color, patch_alpha))
                            dest_surface.blit(patch_surf, (20 + patch_x, patch_y))
                            surface_pool.release(patch_surf)

                    # Occasional complete row deletion (sprite data dropping out)
                    if progress > 0.4:
                        num_drops = int(progress * 5)
                        for _ in range(num_drops):
                            drop_y = random.randint(0, src_h - 3)
                            drop_h = random.randint(2, 8)
                            # Erase a horizontal strip (make it transparent)
                            erase_rect = pygame.Rect(20, drop_y, src_w, drop_h)
                            erase_surf = surface_pool.acquire(src_w, drop_h)
                            dest_surface.blit(erase_surf, (20, drop_y))
                            surface_pool.release(erase_surf)

                    # Apply the vanishing opacity
                    dest_surface.set_alpha(int(self._vanish_opacity))
                    surface.blit(dest_surface, (sprite_x - 20, sprite_y))
                    surface_pool.release(dest_surface)

            # Glitch noise particles around the sprite area
            if self._vanish_progress > 0.3 and random.random() < self._vanish_progress * 0.4:
                noise_x = sprite_x + random.randint(-10, sprite_w + 10)
                noise_y = sprite_y + random.randint(-5, int(sprite_y * 0.5))
                noise_w = random.randint(4, 30)
                noise_h = random.randint(2, 6)
                noise_surf = surface_pool.acquire(noise_w, noise_h)
                noise_color = random.choice(
                    [
                        C.ELDRITCH_PURPLE,
                        (30, 5, 50),
                        C.CRIMSON,
                        (50, 15, 80),
                    ]
                )
                noise_alpha = int(random.uniform(40, 120) * self._vanish_progress)
                noise_surf.fill((*noise_color, noise_alpha))
                surface.blit(noise_surf, (noise_x + ox, noise_y + oy))
                surface_pool.release(noise_surf)

        elif self._victory_state == "afterimage":
            # Burned-in silhouette fading — NO sprite
            if self._afterimage_surface and self._afterimage_alpha > 0:
                afterimage = self._afterimage_surface.copy()
                afterimage.set_alpha(self._afterimage_alpha)
                surface.blit(afterimage, (sprite_x + ox, sprite_y + oy))

        elif self._victory_state == "fade":
            # Final fade — NO sprite, NO afterimage, just darkness
            pass

        else:
            # Normal combat sprite (only when _victory_state is None)
            enemy_sprite = self.assets.get_sprite(e.name)
            if enemy_sprite:
                # Flash overlay when enemy acts
                if self._enemy_flash_timer > 0:
                    flash = enemy_sprite.copy()
                    flash_overlay = surface_pool.acquire(flash.get_width(), flash.get_height())
                    flash_overlay.fill((255, 60, 60, int(80 * (self._enemy_flash_timer / 0.25))))
                    flash.blit(flash_overlay, (0, 0))
                    surface.blit(flash, (sprite_x, sprite_y))
                    surface_pool.release(flash_overlay)
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

        # --- Character sprite (left side) — hidden during glitch_vanish and after ---
        if not self._victory_state or self._victory_state in ("glitch_onset", "reality_break"):
            class_sprite = self.assets.get_class_combat(s.class_id)
            if class_sprite:
                # Player hit flash effect - red flash when taking damage
                if self._player_hit_flash > 0:
                    flash = class_sprite.copy()
                    flash_overlay = surface_pool.acquire(flash.get_width(), flash.get_height())
                    # Directional flash based on damage source (enemy is on the right)
                    if self._player_hit_direction == 1:  # Damage from right
                        flash_overlay.fill((255, 30, 30, int(100 * (self._player_hit_flash / 0.3))))
                    else:  # Damage from left
                        flash_overlay.fill((255, 50, 50, int(80 * (self._player_hit_flash / 0.3))))
                    flash.blit(flash_overlay, (0, 0))
                    surface.blit(flash, (30 + ox, 250 + oy))
                    surface_pool.release(flash_overlay)
                else:
                    surface.blit(class_sprite, (30 + ox, 250 + oy))

        # --- Combat log (center, parchment panel) ---
        log_x, log_y = 280, 250
        log_w, log_h = 560, 180
        draw_parchment_panel(surface, log_x, log_y, log_w, log_h)
        if self._victory_state in ("afterimage", "fade"):
            # Show horror victory text in the log panel
            alpha = min(255, int(self._victory_timer * 300)) if self._victory_state == "afterimage" else 255
            # The death message was already added to the combat log
            # Show it with typewriter-style reveal
            draw_text_with_glow(
                surface,
                "— VICTORY —",
                self.assets.fonts["body"],
                C.ELDRITCH_PURPLE,
                log_x + log_w // 2,
                log_y + 40,
                align="center",
            )
            # Show latest log entries (the death message was added)
            if c.log:
                for i, (text, log_type) in enumerate(c.log[-3:]):
                    colors = {
                        "damage": C.CRIMSON,
                        "crit": C.PARCHMENT_EDGE,
                        "heal": C.MIST,
                        "shield": C.FROST,
                        "effect": C.ELDRITCH,
                        "info": C.INK_LIGHT,
                    }
                    color = colors.get(log_type, C.INK)
                    line_alpha = min(255, max(0, alpha - i * 40))
                    text = fit_text(self.assets.fonts["tiny"], text, log_w - 30)
                    if line_alpha > 0:
                        text_surf = self.assets.fonts["tiny"].render(text, True, color)
                        text_surf.set_alpha(line_alpha)
                        surface.blit(text_surf, (log_x + 15, log_y + 70 + i * 24))
        else:
            draw_text_with_glow(
                surface, "Combat Log", self.assets.fonts["tiny"], C.PARCHMENT_EDGE, log_x + 15, log_y + 8
            )
            draw_gold_divider(surface, log_x + 15, log_y + 26, log_w - 30)
            if c.log:
                for i, (text, log_type) in enumerate(c.log[-5:]):
                    colors = {
                        "damage": C.CRIMSON,
                        "crit": C.PARCHMENT_EDGE,
                        "heal": C.MIST,
                        "shield": C.FROST,
                        "effect": C.ELDRITCH,
                        "info": C.INK_LIGHT,
                    }
                    color = colors.get(log_type, C.INK)
                    text = fit_text(self.assets.fonts["tiny"], text, log_w - 30)
                    draw_text_with_glow(
                        surface, text, self.assets.fonts["tiny"], color, log_x + 15, log_y + 32 + i * 26
                    )

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
                draw_ornate_button(
                    surface,
                    btn,
                    label,
                    self.assets.fonts["small"],
                    hover=(i == self.hover_idx and not on_cd),
                    color=C.CRIMSON if on_cd else C.PARCHMENT_EDGE,
                    disabled=on_cd,
                )

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
                draw_ornate_button(
                    surface,
                    btn,
                    labels[name],
                    self.assets.fonts["tiny"],
                    hover=((len(s.active_skills) + ci) == self.hover_idx),
                    color=C.CRIMSON if name == "run" else C.PARCHMENT_EDGE,
                    disabled=(name == "run" and not can_run),
                )

        # Turn message popup
        if self.turn_msg_timer > 0 and self.turn_message:
            draw_text_with_glow(
                surface, self.turn_message, self.assets.fonts["body"], C.CRIMSON, SCREEN_W // 2, 245, align="center"
            )

        # --- Victory vignette tightening (afterimage + fade phases) ---
        if self._victory_vignette_intensity > 0:
            vignette = surface_pool.acquire(SCREEN_W, SCREEN_H)
            # Draw tight dark vignette around edges
            max_alpha = int(180 * self._victory_vignette_intensity)
            for i in range(40):
                ratio = i / 40.0
                alpha = int(max_alpha * (1.0 - ratio) * (1.0 - ratio))
                if alpha < 3:
                    continue
                # Dark purple-black vignette
                color = (10, 5, 20, alpha)
                # Shrink the clear area as intensity increases
                margin = int((1.0 - self._victory_vignette_intensity * 0.6) * max(SCREEN_W, SCREEN_H) * ratio * 0.5)
                rx = SCREEN_W // 2 - margin
                ry = SCREEN_H // 2 - margin
                if rx > 0 and ry > 0:
                    pygame.draw.ellipse(vignette, color, (rx, ry, (SCREEN_W - 2 * rx), (SCREEN_H - 2 * ry)))
            surface.blit(vignette, (0, 0))
            surface_pool.release(vignette)

        # --- Victory fade-to-black overlay ---
        if self._victory_fade_alpha > 0:
            fade_surf = surface_pool.acquire(SCREEN_W, SCREEN_H)
            fade_surf.fill((0, 0, 0, self._victory_fade_alpha))
            surface.blit(fade_surf, (0, 0))
            surface_pool.release(fade_surf)

        # ═══════════════════════════════════════════════════════════════════════════════
        # ELDRITCH FLOATING DAMAGE NUMBERS — Victorian Writhe System
        # Restrained menace: purple, red, and yellow only.
        # Cinzel Decorative Bold — refined, elegant, wrong.
        # ═══════════════════════════════════════════════════════════════════════════════

        # Palette: dark menacing Victorian colors - deep purples, blood crimsons, tarnished golds
        _PURPLE = (90, 40, 110)  # Deep dark purple
        _PURPLE_DEEP = (50, 15, 80)  # Even darker purple shadow
        _PURPLE_VOID = (30, 5, 50)  # Near-black purple void
        _CRIMSON = (120, 20, 35)  # Dark blood red
        _CRIMSON_DARK = (70, 10, 20)  # Dried blood crimson
        _GOLD = (160, 120, 20)  # Dark tarnished gold
        _GOLD_BRIGHT = (190, 150, 30)  # Slightly brighter dark gold

        # Victorian decorative runes
        _ELDRITCH_RUNES = ["\u2020", "\u2726", "\u263d", "\u2694", "\u2736", "\u2625", "\u271d"]

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
            surface.blit(
                shadow_surface,
                (
                    base_draw_x - text_surface.get_width() // 2 + shadow_offset,
                    base_draw_y - text_surface.get_height() // 2 + shadow_offset,
                ),
            )

            # Draw main text
            surface.blit(
                text_surface,
                (base_draw_x - text_surface.get_width() // 2, base_draw_y - text_surface.get_height() // 2),
            )

            # For crits only: add a subtle crimson glow pulse
            if is_crit:
                glow_alpha = int(60 + 40 * math.sin(self._time * 6.0))
                glow_surface = scaled_font.render(text, True, (120, 20, 35))  # Dark blood red
                glow_surface.set_alpha(glow_alpha)
                surface.blit(
                    glow_surface,
                    (base_draw_x - text_surface.get_width() // 2, base_draw_y - text_surface.get_height() // 2),
                )

        # Status effect tooltips on hover
        self._draw_status_tooltips(surface)

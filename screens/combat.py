import pygame
from shared import C, SCREEN_W, SCREEN_H, Assets, draw_hud, draw_text, draw_text_wrapped, fit_text, draw_text_fitted, draw_bar, draw_panel, draw_ornate_panel, draw_ornate_button, draw_gold_divider, hp_color, mad_color, rarity_color, generate_parchment_texture, draw_parchment_panel, draw_text_with_glow, draw_text_wrapped_glow, draw_text_fitted_glow, draw_status_icons_row, draw_status_tooltip
import random
from screens.base import Screen
from engine import (player_use_skill, enemy_turn, check_boss_phase,
                    tick_player_buffs, process_status_effects,
                    process_player_status_effects, generate_item, advance_floor,
                    combat_run_attempt, _get_enemy_intent_message,
                    calc_preview_damage)

class CombatScreen(Screen):
    def __init__(self, game):
        super().__init__(game)
        self.skill_buttons = []
        self.cmd_buttons = {}
        self.damage_numbers = []  # [text, x, y, color, timer, vy]
        self.shake_timer = 0
        self.shake_intensity = 0
        self.turn_message = ""
        self.turn_msg_timer = 0
        self.particles = []  # [x, y, vx, vy, size, color, alpha, life]
        self._enemy_status_rects = []  # [(Rect, effect_type), ...] for hover tooltips
        self._player_status_rects = []  # [(Rect, effect_type), ...] for hover tooltips

    def enter(self):
        self.damage_numbers = []
        self.shake_timer = 0
        self._build_buttons()
        self.turn_message = ""
        self.turn_msg_timer = 0
        self.particles = []
        # Ambient eldritch particles
        for _ in range(25):
            self.particles.append(self._new_ambient_particle())
        # Pre-select enemy's first action and show intent
        s = self.game.state
        if s.combat:
            s.combat.next_enemy_skill = random.choice(s.combat.enemy.skills)
            intent_msg = _get_enemy_intent_message(s.combat.next_enemy_skill)
            s.combat.add_log(intent_msg, "info")

    def _new_ambient_particle(self):
        return {
            "x": random.uniform(0, SCREEN_W),
            "y": random.uniform(120, SCREEN_H),
            "vx": random.uniform(-0.3, 0.3),
            "vy": random.uniform(-1.0, -0.2),
            "size": random.randint(1, 3),
            "color": random.choice([(175, 130, 225), (140, 100, 200), (80, 50, 130)]),
            "alpha": random.randint(20, 60),
            "life": random.uniform(2, 6),
        }

    def _spawn_blood_particles(self, x, y, count=8):
        """Spawn blood splatter particles at (x, y)."""
        for _ in range(count):
            self.particles.append({
                "x": x + random.uniform(-15, 15),
                "y": y + random.uniform(-10, 10),
                "vx": random.uniform(-2, 2),
                "vy": random.uniform(-3, -0.5),
                "size": random.randint(2, 5),
                "color": random.choice([(196, 30, 58), (139, 0, 0), (220, 50, 50)]),
                "alpha": random.randint(120, 200),
                "life": random.uniform(0.5, 1.5),
            })

    def _build_buttons(self):
        s = self.game.state
        if not s.combat:
            return
        bw, bh = 280, 44
        start_x = 30
        start_y = 460
        cols = 2
        self.skill_buttons = []
        for i, sk in enumerate(s.active_skills):
            col = i % cols
            row = i // cols
            x = start_x + col * (bw + 20)
            y = start_y + row * (bh + 8)
            self.skill_buttons.append(pygame.Rect(x, y, bw, bh))

        # Command buttons below skills
        cmd_y = start_y + ((len(s.active_skills) + 1) // cols) * (bh + 8) + 15
        self.cmd_buttons = {
            "run": pygame.Rect(30, cmd_y, 135, 36),
            "inventory": pygame.Rect(175, cmd_y, 135, 36),
            "save": pygame.Rect(320, cmd_y, 135, 36),
        }

    def add_damage_number(self, text, x, y, color):
        self.damage_numbers.append([text, x, y, color, 1.5, -60])
        # Spawn blood particles on damage
        if color == C.CRIMSON:
            self._spawn_blood_particles(x, y, count=10)
        elif color == C.YELLOW:  # crit
            self._spawn_blood_particles(x, y, count=16)

    def trigger_shake(self, intensity=8, duration=0.3):
        self.shake_intensity = intensity
        self.shake_timer = duration

    def update(self, dt):
        for dn in self.damage_numbers:
            dn[2] += dn[5] * dt
            dn[4] -= dt
        self.damage_numbers = [dn for dn in self.damage_numbers if dn[4] > 0]
        if self.shake_timer > 0:
            self.shake_timer -= dt
        if self.turn_msg_timer > 0:
            self.turn_msg_timer -= dt
        # Update particles
        for p in self.particles:
            p["x"] += p["vx"]
            p["y"] += p["vy"]
            p["life"] -= dt
            p["alpha"] = max(0, p["alpha"] - dt * 40)
        self.particles = [p for p in self.particles if p["life"] > 0 and p["alpha"] > 0]
        # Respawn ambient particles to maintain count
        ambient_count = sum(1 for p in self.particles if p["size"] <= 3)
        while ambient_count < 25:
            self.particles.append(self._new_ambient_particle())
            ambient_count += 1

    def handle_event(self, event):
        s = self.game.state
        c = s.combat
        if not c:
            return

        # Track hover for all buttons
        all_btns = self.skill_buttons + list(self.cmd_buttons.values())
        self.update_hover(event, all_btns)

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for i, btn in enumerate(self.skill_buttons):
                if btn.collidepoint(event.pos):
                    if i < len(s.active_skills):
                        self._use_skill(i)
            for name, btn in self.cmd_buttons.items():
                if btn.collidepoint(event.pos):
                    if name == "run":
                        self._try_run()
                    elif name == "inventory":
                        self.game.switch_screen("inventory")
                    elif name == "save":
                        self.game.switch_screen("save")
        elif event.type == pygame.KEYDOWN:
            if pygame.K_1 <= event.key <= pygame.K_9:
                idx = event.key - pygame.K_1
                if idx < len(s.active_skills):
                    self._use_skill(idx)
            elif event.key == pygame.K_r:
                self._try_run()
            elif event.key == pygame.K_i:
                self.game.switch_screen("inventory")
            elif event.key == pygame.K_s:
                self.game.switch_screen("save")

    def _use_skill(self, idx):
        s = self.game.state
        c = s.combat
        if not c or c.turn != "player":
            return
        sk = s.active_skills[idx]
        if sk.current_cd > 0:
            self.turn_message = f"{sk.name} is on cooldown!"
            self.turn_msg_timer = 1.5
            return

        logs = player_use_skill(s, idx)
        for text, log_type in logs:
            c.add_log(text, log_type)
            if log_type in ("damage", "crit"):
                color = C.YELLOW if log_type == "crit" else C.BONE
                dmg_val = text.split()[-1] if any(ch.isdigit() for ch in text) else ""
                # Damage number floats above enemy sprite (right side)
                self.add_damage_number(dmg_val, 1120, 200, color)

        phase_logs = check_boss_phase(s)
        for text, log_type in phase_logs:
            c.add_log(text, log_type)

        buff_logs = tick_player_buffs(s)
        for text, log_type in buff_logs:
            c.add_log(text, log_type)

        se_logs = process_status_effects(c.enemy, False, s)
        for text, log_type in se_logs:
            c.add_log(text, log_type)

        if c.enemy.hp <= 0:
            self._end_combat(victory=True)
            return

        c.turn = "enemy"
        self._do_enemy_turn()

    def _do_enemy_turn(self):
        s = self.game.state
        c = s.combat
        if not c:
            return

        logs = enemy_turn(s)
        for text, log_type in logs:
            c.add_log(text, log_type)
            if log_type == "damage":
                self.trigger_shake()
                dmg_val = text.split()[-1] if any(ch.isdigit() for ch in text) else ""
                # Damage number floats above player sprite (left side)
                self.add_damage_number(dmg_val, 140, 250, C.CRIMSON)

        if s.hp <= 0:
            self._end_combat(victory=False)
            return

        se_logs = process_player_status_effects(s)
        for text, log_type in se_logs:
            c.add_log(text, log_type)

        if s.hp <= 0:
            self._end_combat(victory=False)
            return

        for sk in s.active_skills:
            if sk.current_cd > 0:
                sk.current_cd -= 1

        buff_logs = tick_player_buffs(s)
        for text, log_type in buff_logs:
            c.add_log(text, log_type)

        c.turn = "player"
        c.turn_count += 1

        # Pre-select enemy's next action and show intent
        c.next_enemy_skill = random.choice(c.enemy.skills)
        intent_msg = _get_enemy_intent_message(c.next_enemy_skill)
        c.add_log(intent_msg, "info")

        self._build_buttons()

    def _try_run(self):
        s = self.game.state
        c = s.combat
        if not c or c.is_boss:
            self.turn_message = "Cannot flee from the Spiral!"
            self.turn_msg_timer = 1.5
            return
        if combat_run_attempt(s):
            s.combat = None
            advance_floor(s)
            self.game.switch_screen("explore")
        else:
            self.turn_message = "Failed to escape!"
            self.turn_msg_timer = 1.5
            c.turn = "enemy"
            self._do_enemy_turn()

    def _end_combat(self, victory):
        s = self.game.state
        c = s.combat
        if not c:
            return

        if victory:
            s.kills += 1
            xp_g = 12 + s.floor * 4 + (80 if c.is_boss else 0)
            gold_g = 6 + random.randint(0, 8) + s.floor * 2 + (50 if c.is_boss else 0)
            s.xp += xp_g
            s.gold += gold_g
            s.add_madness(-15 if c.is_boss else 3)
            loot = generate_item(s.floor, luck=s.luck, buffs=s.buffs)
            leveled = s.check_level_up()

            self.game.combat_result = {
                "victory": True, "xp": xp_g, "gold": gold_g,
                "loot": loot, "is_boss": c.is_boss, "leveled": leveled,
            }
            s.combat = None
            if leveled:
                self.game.switch_screen("levelup")
            else:
                self.game.switch_screen("combat_result")
        else:
            s.combat = None
            self.game.gameover_msg = "Your body crumples. The last thing you see is the Yellow Sign, burning brighter than ever."
            self.game.switch_screen("gameover")

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

    def draw(self, surface):
        s = self.game.state
        c = s.combat
        if not c:
            return
        e = c.enemy

        ox, oy = 0, 0
        if self.shake_timer > 0:
            ox = random.randint(-self.shake_intensity, self.shake_intensity)
            oy = random.randint(-self.shake_intensity, self.shake_intensity)

        draw_hud(surface, s, self.assets)

        # Particles (behind UI elements)
        for p in self.particles:
            ps = pygame.Surface((p["size"] * 2, p["size"] * 2), pygame.SRCALPHA)
            ps.fill((*p["color"], int(p["alpha"])))
            surface.blit(ps, (int(p["x"]) + ox, int(p["y"]) + oy))

        # --- Enemy info panel (compact nameplate above sprite) ---
        e_hp_pct = max(0, e.hp / e.max_hp * 100)
        panel_w = 495
        panel_h = 100  # Taller to fit status icons below HP bar
        sprite_w = 240
        sprite_x = SCREEN_W - sprite_w - 40 + ox
        sprite_y = 202 + oy
        # Panel right-aligned to sprite's right edge (panel wider than sprite)
        panel_x = sprite_x + sprite_w - panel_w
        panel_y = 120
        draw_parchment_panel(surface, panel_x, panel_y, panel_w, panel_h)

        if c.is_boss:
            draw_text_with_glow(surface, "BOSS", self.assets.fonts["tiny"], C.CRIMSON, panel_x + 12, panel_y + 5)
        draw_text_with_glow(surface, e.name, self.assets.fonts["small"], C.PARCHMENT_EDGE, panel_x + 12, panel_y + 22)

        # Enemy HP bar
        draw_bar(surface, panel_x + 12, panel_y + 44, 330, 14, e.hp, e.max_hp,
                 hp_color(e.hp, e.max_hp))
        draw_text_with_glow(surface, f"{e.hp}/{e.max_hp}", self.assets.fonts["tiny"],
                  C.INK, panel_x + 350, panel_y + 44)

        # Enemy status icons — below HP bar, left side
        enemy_statuses = list(e.statuses)
        if e.stunned:
            from engine.models import StatusEffect
            stun_se = StatusEffect("stunned", 1)
            enemy_statuses = [stun_se] + enemy_statuses
        self._enemy_status_rects = draw_status_icons_row(
            surface, panel_x + 12, panel_y + 65, enemy_statuses, {},
            size=26, gap=5
        )

        # --- Enemy sprite (right side, below panel, fully visible) ---
        enemy_sprite = self.assets.get_sprite(e.name)
        if enemy_sprite:
            surface.blit(enemy_sprite, (sprite_x, sprite_y))

        # --- Character sprite (left side) ---
        class_sprite = self.assets.get_class_combat(s.class_id)
        if class_sprite:
            surface.blit(class_sprite, (30 + ox, 250 + oy))

        # --- Combat log (center, parchment panel) ---
        log_x, log_y = 280, 250
        log_w, log_h = 560, 180
        draw_parchment_panel(surface, log_x, log_y, log_w, log_h)
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

        # --- Skills panel ---
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

        # Damage numbers
        for dn in self.damage_numbers:
            text, x, y, color, timer, vy = dn
            draw_text(surface, text, self.assets.fonts["heading"], color, int(x) + ox, int(y) + oy)

        # Status effect tooltips on hover
        self._draw_status_tooltips(surface)

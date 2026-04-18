import pygame
import math
import random
from shared import C, SCREEN_W, SCREEN_H, Assets, draw_hud, draw_text, draw_text_wrapped, fit_text, draw_text_fitted, draw_bar, draw_panel, draw_ornate_panel, draw_ornate_button, draw_gold_divider, hp_color, mad_color, rarity_color, generate_parchment_texture, draw_parchment_panel, draw_text_with_glow, draw_text_wrapped_glow, draw_text_fitted_glow, draw_status_icons_row, draw_status_tooltip
from screens.base import Screen
from screens.combat.particles import ParticleType, PARTICLE_TYPES, create_particle, create_burst
from screens.combat.renderer import CombatRendererMixin
from engine import (player_use_skill, enemy_turn, check_boss_phase,
                    tick_player_buffs, process_status_effects,
                    process_player_status_effects, generate_item, advance_floor,
                    combat_run_attempt, _get_enemy_intent_message,
                    calc_preview_damage)
from data import (XP_BASE, XP_PER_FLOOR, XP_BOSS_BONUS,
                  GOLD_BASE, GOLD_PER_FLOOR, GOLD_BOSS_BONUS, GOLD_BASE_RANDOM_MAX,
                  MADNESS_BOSS_KILL, MADNESS_NORMAL_KILL)


class CombatScreen(CombatRendererMixin, Screen):
    def __init__(self, game):
        super().__init__(game)
        self.skill_buttons = []
        self.cmd_buttons = {}
        self.damage_numbers = []  # [text, x, y, color, timer, vy]
        self.shake_timer = 0
        self.shake_intensity = 0
        self.shake_offset_x = 0  # For directional shake
        self.shake_offset_y = 0
        self.shake_direction = 0  # 0=random, 1=horizontal, 2=vertical
        self.turn_message = ""
        self.turn_msg_timer = 0
        self.particles = []  # [x, y, vx, vy, size, color, alpha, life]
        self._enemy_status_rects = []  # [(Rect, effect_type), ...] for hover tooltips
        self._player_status_rects = []  # [(Rect, effect_type), ...] for hover tooltips
        self._enemy_action_text = None  # (text, x, y, color, timer, vy) floating text
        self._enemy_flash_timer = 0  # brief flash when enemy acts
        self._time = 0.0  # Accumulated time for eldritch wave animations

        # ─────────────────────────────────────────────────────────────────────────────
        # ENEMY INTENT DISPLAY SYSTEM
        # Shows what the enemy will do on their next turn
        # ─────────────────────────────────────────────────────────────────────────────
        self._intent_panel_visible = True
        self._intent_hover = False
        self._intent_pulse = 0  # For pulsing animation
        self._intent_particles = []  # Particles around intent indicator

        # Player hit feedback
        self._player_hit_flash = 0  # Flash timer for player damage
        self._player_hit_direction = 0  # 0=left, 1=right (where damage came from)

        # Victory animation state machine
        # States: None (normal) → "hp_drain" → "disintegrate" → "dramatic_pause" → "fade_out" → done
        self._victory_state = None
        self._victory_timer = 0.0
        self._victory_hp_target = 0  # HP we're draining toward
        self._victory_hp_display = 0.0  # Smooth float for HP bar display
        self._victory_is_boss = False
        self._fragments = []  # Disintegration fragments: [x, y, vx, vy, w, h, color, alpha, rot, rot_v]
        self._victory_text_alpha = 0  # For "DEFEATED" text fade-in
        self._victory_fade_alpha = 0  # For final fade-to-black

    def enter(self):
        self.damage_numbers = []
        self.shake_timer = 0
        self.shake_intensity = 0
        self.shake_offset_x = 0
        self.shake_offset_y = 0
        self._player_hit_flash = 0
        self._time = 0.0
        self._intent_pulse = 0
        self._intent_particles = []
        self._build_buttons()
        self.turn_message = ""
        self.turn_msg_timer = 0
        self.particles = []
        self._victory_state = None
        self._victory_timer = 0.0
        self._fragments = []
        self._victory_text_alpha = 0
        self._victory_fade_alpha = 0
        # Ambient eldritch particles using new particle system
        for _ in range(25):
            self.particles.extend(create_particle("eldritch",
                random.uniform(0, SCREEN_W),
                random.uniform(120, SCREEN_H),
                count=1, spread=5))
        # Pre-select enemy's first action and show intent
        s = self.game.state
        if s.combat:
            s.combat.next_enemy_skill = random.choice(s.combat.enemy.skills)
            intent_msg = _get_enemy_intent_message(s.combat.next_enemy_skill)
            s.combat.add_log(intent_msg, "info")
            # Spawn intent particles to draw attention
            self._spawn_intent_particles()

    def _spawn_intent_particles(self):
        """Spawn atmospheric particles around the enemy intent indicator."""
        if not self._intent_panel_visible:
            return
        sprite_w = 240
        sprite_x = SCREEN_W - sprite_w - 40
        sprite_y = 202
        # Spawn particles near the enemy sprite to hint at their intent
        for _ in range(8):
            self.particles.extend(create_particle(
                self._get_intent_particle_type(),
                sprite_x + sprite_w // 2,
                sprite_y - 20,
                count=1, spread=30))

    def _get_intent_particle_type(self):
        """Get the appropriate particle type based on enemy intent."""
        s = self.game.state
        if not s or not s.combat or not s.combat.next_enemy_skill:
            return "eldritch"
        skill = s.combat.next_enemy_skill
        skill_type = skill.get("type", "")
        if "magic" in skill_type or "spell" in skill_type:
            return "intent_spell"
        elif "buff" in skill_type or "heal" in skill_type:
            return "intent_buff"
        else:
            return "intent_attack"

    def _spawn_blood_particles(self, x, y, count=8, is_crit=False):
        """Spawn blood splatter particles at (x, y) using new particle system."""
        particle_type = "crit_blood" if is_crit else "blood"
        self.particles.extend(create_particle(particle_type, x, y, count=count, spread=15))

    def _spawn_magic_particles(self, x, y, count=5):
        """Spawn magic effect particles."""
        self.particles.extend(create_particle("magic", x, y, count=count, spread=10))

    def _spawn_heal_particles(self, x, y, count=8):
        """Spawn healing particles that float upward."""
        self.particles.extend(create_particle("heal", x, y, count=count, spread=12, base_vy=-20))

    def _spawn_shield_particles(self, x, y, count=6):
        """Spawn shield/barrier effect particles."""
        self.particles.extend(create_particle("shield", x, y, count=count, spread=15, base_vy=-10))

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

    def add_damage_number(self, text, x, y, color, is_player_damage=False, is_crit=False, is_heal=False):
        """Add a floating damage/healing number with appropriate particle effects.
        Uses minimalist eldritch glyph style - no bouncy animations, just stark menacing numbers.

        Args:
            text: Damage/heal value string
            x, y: Position for the damage number
            color: Text color
            is_player_damage: If True, this is damage dealt to the player
            is_crit: If True, this was a critical hit
            is_heal: If True, this is healing (green float text)
        """
        # Adjust particle counts based on damage type
        if is_player_damage:
            # Damage to player - spawn on their sprite
            player_x, player_y = 100, 300
            self._spawn_blood_particles(player_x, player_y, count=10 if is_crit else 6)
            # Add directional hit flash
            self._player_hit_flash = 0.3
            self._player_hit_direction = 1 if x > SCREEN_W // 2 else 0  # Damage came from enemy side
        elif is_heal:
            # Healing - spawn heal particles
            self._spawn_heal_particles(x, y, count=12 if is_crit else 8)
        else:
            # Damage to enemy
            if is_crit:
                self._spawn_blood_particles(x, y, count=16, is_crit=True)
                self._spawn_magic_particles(x, y, count=8)
            else:
                self._spawn_blood_particles(x, y, count=10)
                self._spawn_magic_particles(x, y, count=4)

        # [text, x, y, color, timer, vy, scale, is_crit, base_y]
        # Minimalist: no scale pop, slower rise, longer duration for gravitas
        self.damage_numbers.append([text, x, y, color, 2.0, -40 if is_crit else -30, 1.0, is_crit, y])

    def trigger_shake(self, intensity=8, duration=0.3, direction=0, is_enemy_damage=False):
        """Trigger screen shake with enhanced options.

        Args:
            intensity: How strong the shake is (pixels offset)
            duration: How long the shake lasts (seconds)
            direction: 0=random, 1=horizontal only, 2=vertical only
            is_enemy_damage: If True, shake is from dealing damage to enemy
        """
        self.shake_intensity = intensity
        self.shake_timer = duration
        self.shake_direction = direction

        # Spawn impact particles based on what caused the shake
        if is_enemy_damage:
            # Dealing damage to enemy - spawn at enemy position
            sprite_w = 240
            sprite_x = SCREEN_W - sprite_w - 40
            self.particles.extend(create_burst(sprite_x + sprite_w // 2, 280, "damage_burst", count=15))
        else:
            # Taking damage - spawn at player position
            self.particles.extend(create_burst(100, 300, "blood", count=12))

    def update(self, dt):
        # --- Victory animation state machine ---
        if self._victory_state:
            self._victory_timer += dt

            if self._victory_state == "hp_drain":
                # Accelerating drain: starts slow, ends fast
                max_hp = max(1, int(self._victory_hp_display) + 1)  # avoid /0
                # fraction goes from 1.0 (full) to 0.0 (empty) as display drops
                fraction = max(0.0, self._victory_hp_display / max(1, self._victory_hp_display + 1))
                # Speed ramps from ~150 at start to ~700 at end
                drain_speed = 150.0 + (1.0 - fraction) * 550.0
                # Apply a power curve for smoother acceleration
                drain_amount = drain_speed * dt
                self._victory_hp_display -= drain_amount

                if self._victory_hp_display <= 0:
                    self._victory_hp_display = 0
                    # Final big damage number
                    self.add_damage_number(str(random.randint(30, 99)),
                        random.uniform(880, 1020), random.uniform(200, 260),
                        random.choice([C.YELLOW, C.CRIMSON]))
                    # HP drained — transition to disintegration
                    self.trigger_shake(intensity=18, duration=0.5)
                    self._build_disintegration_fragments()
                    if self._victory_state != "dramatic_pause":  # fragments may have skipped
                        self._victory_state = "disintegrate"
                        self._victory_timer = 0.0
                else:
                    # Continuously spawn floating damage numbers while draining
                    if random.random() < 0.25:
                        dmg_val = str(random.randint(5, 35))
                        self.add_damage_number(dmg_val,
                            random.uniform(860, 1050), random.uniform(180, 280),
                            random.choice([C.BONE, C.YELLOW, C.CRIMSON]))

            elif self._victory_state == "disintegrate":
                # Update fragment physics
                for f in self._fragments:
                    f["x"] += f["vx"] * dt
                    f["vy"] += f["gravity"] * dt  # Gravity pulls down
                    f["y"] += f["vy"] * dt
                    f["rot"] += f["rot_v"]
                    f["alpha"] -= 120 * dt  # Fade out
                self._fragments = [f for f in self._fragments if f["alpha"] > 0]

                # Spawn occasional eldritch wisps from disintegration area
                if self._victory_timer < 1.2 and random.random() < 0.2:
                    self.particles.append({
                        "x": random.uniform(860, 1050), "y": random.uniform(200, 350),
                        "vx": random.uniform(-0.5, 0.5), "vy": random.uniform(-1.5, -0.5),
                        "size": random.randint(2, 5),
                        "color": random.choice([(255, 215, 0), (175, 130, 225), (220, 180, 50)]),
                        "alpha": random.randint(80, 180),
                        "life": random.uniform(0.5, 1.5),
                    })

                # Once fragments are mostly gone or time elapsed
                if len(self._fragments) == 0 or self._victory_timer > 2.0:
                    self._fragments = []
                    self._victory_state = "dramatic_pause"
                    self._victory_timer = 0.0

            elif self._victory_state == "dramatic_pause":
                # Fade in "DEFEATED" text
                self._victory_text_alpha = min(255, int(self._victory_timer * 400))
                # Continue spawning a few final particles
                if random.random() < 0.1:
                    self.particles.append({
                        "x": random.uniform(400, 900), "y": random.uniform(200, 400),
                        "vx": random.uniform(-0.3, 0.3), "vy": random.uniform(-1.0, -0.3),
                        "size": random.randint(1, 3),
                        "color": (255, 215, 0),
                        "alpha": random.randint(40, 100),
                        "life": random.uniform(1.0, 2.0),
                    })
                # After pause, transition to fade-out
                if self._victory_timer > 1.8:
                    self._victory_state = "fade_out"
                    self._victory_timer = 0.0

            elif self._victory_state == "fade_out":
                # Smooth fade to black over 1.0s, then switch screen
                fade_dur = 1.0
                self._victory_fade_alpha = min(255, int(255 * (self._victory_timer / fade_dur)))
                if self._victory_timer >= fade_dur:
                    self._finish_victory()
                    return

            # During victory animation, update particles but skip normal logic
            self._update_particles(dt)
            # Update damage numbers with scale animation
            for dn in self.damage_numbers:
                dn[2] += dn[5] * dt  # y position
                dn[4] -= dt  # timer
                # Animate scale from pop (1.5) down to normal (1.0)
                if dn[6] > 1.0:
                    dn[6] -= 2.0 * dt  # Scale decay rate
            self.damage_numbers = [dn for dn in self.damage_numbers if dn[4] > 0]
            if self.shake_timer > 0:
                self.shake_timer -= dt
            return

        # --- Normal update (non-victory) ---
        self._time += dt  # Accumulate time for eldritch animations
        # Update damage numbers with scale animation
        for dn in self.damage_numbers:
            dn[2] += dn[5] * dt  # y position
            dn[4] -= dt  # timer
            # Animate scale from pop (1.5) down to normal (1.0)
            if dn[6] > 1.0:
                dn[6] -= 2.0 * dt  # Scale decay rate
        self.damage_numbers = [dn for dn in self.damage_numbers if dn[4] > 0]
        if self.shake_timer > 0:
            self.shake_timer -= dt
        if self.turn_msg_timer > 0:
            self.turn_msg_timer -= dt
        # Enemy action floating text
        if self._enemy_action_text:
            self._enemy_action_text[2] += self._enemy_action_text[5] * dt
            self._enemy_action_text[4] -= dt
            if self._enemy_action_text[4] <= 0:
                self._enemy_action_text = None
        # Enemy flash
        if self._enemy_flash_timer > 0:
            self._enemy_flash_timer -= dt
        # Player hit flash
        if self._player_hit_flash > 0:
            self._player_hit_flash -= dt
        # Intent pulse animation
        self._intent_pulse += dt
        # Update particles with physics
        self._update_particles(dt)
        # Respawn ambient particles to maintain count
        ambient_count = sum(1 for p in self.particles if p.get("size", 0) <= 3 and p.get("life", 0) > 0)
        while ambient_count < 25:
            self.particles.extend(create_particle("eldritch",
                random.uniform(0, SCREEN_W),
                random.uniform(120, SCREEN_H),
                count=1, spread=5))
            ambient_count += 1

    def _update_particles(self, dt):
        """Update all particles with physics including gravity."""
        for p in self.particles:
            p["x"] += p["vx"] * dt * 50  # Scale velocity by dt
            p["y"] += p["vy"] * dt * 50
            # Apply gravity if defined
            if "gravity" in p:
                p["vy"] += p["gravity"] * dt
            p["life"] -= dt
            p["alpha"] = max(0, p["alpha"] - dt * 40)
        self.particles = [p for p in self.particles if p["life"] > 0 and p["alpha"] > 0]

    def handle_event(self, event):
        s = self.game.state
        c = s.combat
        if not c:
            # During victory animation, s.combat is cleared only at the very end
            # Block all input during any victory phase
            return

        # Block input during victory animation
        if self._victory_state:
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
                is_crit = log_type == "crit"
                color = C.YELLOW if is_crit else C.BONE
                dmg_val = text.split()[-1] if any(ch.isdigit() for ch in text) else ""
                # Damage number floats above enemy sprite (right side) with enhanced effects
                self.add_damage_number(dmg_val, 1120, 200, color, is_crit=is_crit)
                # Screen shake when dealing damage
                self.trigger_shake(intensity=6, duration=0.15, direction=1, is_enemy_damage=True)

        phase_logs = check_boss_phase(s)
        for text, log_type in phase_logs:
            c.add_log(text, log_type)

        buff_logs = tick_player_buffs(s)
        for text, log_type in buff_logs:
            c.add_log(text, log_type)
            # Healing particles
            if log_type == "heal":
                self._spawn_heal_particles(100, 300, count=12)

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

        # Store the skill name for floating text before executing
        enemy_skill_name = ""
        if c.next_enemy_skill:
            enemy_skill_name = c.next_enemy_skill.get("name", "")

        logs = enemy_turn(s)
        for text, log_type in logs:
            c.add_log(text, log_type)
            if log_type == "damage":
                # Enhanced screen shake for player damage
                self.trigger_shake(intensity=10, duration=0.25, direction=0, is_enemy_damage=False)
                dmg_val = text.split()[-1] if any(ch.isdigit() for ch in text) else ""
                # Damage number floats above player sprite (left side) with player damage flag
                self.add_damage_number(dmg_val, 140, 250, C.CRIMSON, is_player_damage=True)

        # Enemy action floating text (shows what the enemy did)
        if enemy_skill_name:
            # Position near enemy sprite (right side)
            sprite_w = 240
            sprite_x = SCREEN_W - sprite_w - 40
            self._enemy_action_text = [enemy_skill_name, sprite_x + 120, 195, C.CRIMSON, 2.0, -30]
            self._enemy_flash_timer = 0.25

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
        # Spawn particles to indicate new intent
        self._spawn_intent_particles()

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
        """End combat. On victory, start animation sequence. On defeat, go to game over."""
        s = self.game.state
        c = s.combat
        if not c:
            return

        if victory:
            self._start_victory_animation()
        else:
            s.combat = None
            self.game.gameover_msg = "Your body crumples. The last thing you see is the Yellow Sign, burning brighter than ever."
            self.game.switch_screen("gameover")

    def _start_victory_animation(self):
        """Begin the multi-phase victory animation."""
        s = self.game.state
        c = s.combat
        self._victory_is_boss = c.is_boss
        # Start from max HP so the drain animation is always visible
        self._victory_hp_display = float(c.enemy.max_hp)
        self._victory_hp_target = 0
        self._victory_timer = 0.0
        self._victory_text_alpha = 0
        self._victory_fade_alpha = 0
        self._victory_state = "hp_drain"
        # Big screen shake on victory start
        self.trigger_shake(intensity=12, duration=0.5)

    def _build_disintegration_fragments(self):
        """Split the enemy sprite into vertical strips that will scatter."""
        s = self.game.state
        c = s.combat
        if not c:
            return
        e = c.enemy
        enemy_sprite = self.assets.get_sprite(e.name)
        if not enemy_sprite:
            # No sprite — just skip to dramatic pause
            self._victory_state = "dramatic_pause"
            self._victory_timer = 0.0
            return

        sprite_w = 240
        sprite_x = SCREEN_W - sprite_w - 40
        sprite_y = 202

        # Scale sprite to match combat size
        sw, sh = enemy_sprite.get_size()
        if sw != sprite_w:
            scale_h = int(sh * sprite_w / sw)
            enemy_sprite = pygame.transform.scale(enemy_sprite, (sprite_w, scale_h))
            sw, sh = enemy_sprite.get_size()

        # Create vertical strip fragments
        strip_w = 8  # Each strip is 8px wide
        self._fragments = []
        for fx in range(0, sw, strip_w):
            for fy in range(0, sh, 6):  # Also split vertically into chunks
                fw = min(strip_w, sw - fx)
                fh = min(6, sh - fy)
                if fw <= 0 or fh <= 0:
                    continue
                # Get average color of this strip chunk
                try:
                    pixel = enemy_sprite.get_at((min(fx + fw // 2, sw - 1), min(fy + fh // 2, sh - 1)))
                    if pixel.a < 20:  # Skip nearly transparent pixels
                        continue
                except Exception:
                    continue
                # Velocity: outward from center + upward bias + randomness
                cx, cy = sprite_x + sw / 2, sprite_y + sh / 2
                px, py = sprite_x + fx + fw / 2, sprite_y + fy + fh / 2
                dx, dy = px - cx, py - cy
                dist = max(1.0, (dx * dx + dy * dy) ** 0.5)
                speed = random.uniform(60, 180)
                self._fragments.append({
                    "x": float(px), "y": float(py),
                    "vx": (dx / dist) * speed + random.uniform(-20, 20),
                    "vy": (dy / dist) * speed - random.uniform(30, 80),  # Upward bias
                    "w": fw, "h": fh,
                    "color": (pixel.r, pixel.g, pixel.b),
                    "alpha": 255.0,
                    "rot": 0.0,
                    "rot_v": random.uniform(-5, 5),
                    "gravity": random.uniform(80, 150),  # Gravity to bring them down
                })
        # Also spawn a burst of eldritch particles from center
        self._spawn_victory_particle_burst(sprite_x + sw // 2, sprite_y + sh // 2)

    def _spawn_victory_particle_burst(self, cx, cy):
        """Eldritch energy burst + yellow sign particles at combat end."""
        for _ in range(60):
            angle = random.uniform(0, 6.283)
            speed = random.uniform(40, 200)
            self.particles.append({
                "x": cx + random.uniform(-20, 20),
                "y": cy + random.uniform(-20, 20),
                "vx": math.cos(angle) * speed * 0.3,
                "vy": math.sin(angle) * speed * 0.3 - random.uniform(20, 60),
                "size": random.randint(2, 6),
                "color": random.choice([
                    (255, 215, 0),   # Gold (Yellow Sign)
                    (175, 130, 225),  # Purple
                    (220, 180, 50),   # Amber
                    (140, 100, 200),  # Eldritch purple
                ]),
                "alpha": random.randint(150, 255),
                "life": random.uniform(1.0, 2.5),
            })
        for _ in range(30):
            angle = random.uniform(0, 6.283)
            speed = random.uniform(80, 300)
            self.particles.append({
                "x": cx, "y": cy,
                "vx": math.cos(angle) * speed * 0.4,
                "vy": math.sin(angle) * speed * 0.4,
                "size": 1,
                "color": (255, 240, 200),
                "alpha": 255,
                "life": random.uniform(0.3, 0.8),
            })

    def _finish_victory(self):
        """Actually compute rewards and switch to result screen."""
        s = self.game.state
        c = s.combat
        if not c:
            return
        # Safety guard: only finish once
        if not self._victory_state:
            return
        self._victory_state = None

        s.kills += 1
        xp_g = XP_BASE + s.floor * XP_PER_FLOOR + (XP_BOSS_BONUS if c.is_boss else 0)
        gold_g = GOLD_BASE + random.randint(0, GOLD_BASE_RANDOM_MAX) + s.floor * GOLD_PER_FLOOR + (GOLD_BOSS_BONUS if c.is_boss else 0)
        s.xp += xp_g
        s.gold += gold_g
        s.add_madness(MADNESS_BOSS_KILL if c.is_boss else MADNESS_NORMAL_KILL)
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

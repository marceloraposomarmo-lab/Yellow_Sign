import pygame
import math
import random
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
    draw_status_icons_row,
    draw_status_tooltip,
)
from shared.game_context import GameContext
from shared.rendering import ease_out_cubic, ease_in_cubic, ease_in_quad
from screens.base import Screen
from screens.screen_enum import ScreenName
from screens.combat.particles import ParticleType, PARTICLE_TYPES, create_particle, create_burst
from screens.combat.renderer import CombatRendererMixin
from engine import (
    player_use_skill,
    enemy_turn,
    check_boss_phase,
    tick_player_buffs,
    process_status_effects,
    process_player_status_effects,
    generate_item,
    advance_floor,
    combat_run_attempt,
    _get_enemy_intent_message,
    calc_preview_damage,
)
from data import (
    XP_BASE,
    XP_PER_FLOOR,
    XP_BOSS_BONUS,
    GOLD_BASE,
    GOLD_PER_FLOOR,
    GOLD_BOSS_BONUS,
    GOLD_BASE_RANDOM_MAX,
    MADNESS_BOSS_KILL,
    MADNESS_NORMAL_KILL,
)


class CombatScreen(CombatRendererMixin, Screen):
    def __init__(self, ctx):
        super().__init__(ctx)
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

        # ─────────────────────────────────────────────────────────────────────────────
        # HORROR DEATH ANIMATION STATE MACHINE
        # States: None → "glitch_onset" → "reality_break" → "glitch_vanish" →
        #         "afterimage" → "fade" → done
        # ─────────────────────────────────────────────────────────────────────────────
        self._victory_state = None
        self._victory_timer = 0.0
        self._victory_is_boss = False

        # Glitch phase data
        self._glitch_intensity = 0.0  # 0-1+, ramps up over glitch phases
        self._glitch_name_corrupted = ""  # Corrupted enemy name string
        self._glitch_name_timer = 0.0  # Timer for name scramble refresh
        self._glitch_bar_snap = False  # True when HP bar snaps to 0
        self._glitch_bar_flicker = 0.0  # HP bar flicker offset (random per frame)

        # Glitch vanish phase data
        self._vanish_progress = 0.0  # 0-1, how far into vanish we are
        self._vanish_opacity = 255.0  # Sprite opacity, drops to 0 during vanish
        self._vanish_distortion = []  # Per-column distortion offsets

        # Afterimage data
        self._afterimage_alpha = 0  # Fading silhouette alpha
        self._afterimage_surface = None  # Cached silhouette surface

        # Shared victory state
        self._victory_fade_alpha = 0  # Final fade-to-black
        self._victory_vignette_intensity = 0.0  # Tightening vignette

        # Eldritch symbols for name corruption
        self._eldritch_symbols = list(
            "\u2726\u263d\u2694\u2736\u2625\u271d\u2020\u2720\u263c\u2735\u2606\u2605\u263e\u2628\u2629\u262a"
        )

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
        self._victory_fade_alpha = 0
        self._glitch_intensity = 0.0
        self._glitch_name_corrupted = ""
        self._glitch_name_timer = 0.0
        self._glitch_bar_snap = False
        self._glitch_bar_flicker = 0.0
        self._implosion_progress = 0.0
        self._implosion_distortion = []
        self._void_flash_radius = 0.0
        self._void_flash_alpha = 0
        self._afterimage_alpha = 0
        self._afterimage_surface = None
        self._victory_vignette_intensity = 0.0
        # Ambient eldritch particles using new particle system
        for _ in range(25):
            self.particles.extend(
                create_particle(
                    "eldritch", random.uniform(0, SCREEN_W), random.uniform(120, SCREEN_H), count=1, spread=5
                )
            )
        # Pre-select enemy's first action and show intent
        s = self.ctx.state
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
            self.particles.extend(
                create_particle(
                    self._get_intent_particle_type(), sprite_x + sprite_w // 2, sprite_y - 20, count=1, spread=30
                )
            )

    def _get_intent_particle_type(self):
        """Get the appropriate particle type based on enemy intent."""
        s = self.ctx.state
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
        s = self.ctx.state
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
        # --- Horror death animation state machine ---
        if self._victory_state:
            self._victory_timer += dt

            if self._victory_state == "glitch_onset":
                # Phase 1: HP bar + name start glitching (0.8s)
                # Glitch intensity ramps from 0 to 0.5
                self._glitch_intensity = min(0.5, self._victory_timer / 0.8 * 0.5)
                self._glitch_bar_flicker = random.uniform(-8, 8) * self._glitch_intensity
                # Corrupt the name progressively
                self._glitch_name_timer += dt
                if self._glitch_name_timer > 0.08:
                    self._glitch_name_timer = 0.0
                    self._corrupt_enemy_name()
                # Occasional flicker-damage numbers
                if random.random() < 0.08:
                    self.add_damage_number(
                        str(random.randint(1, 9)),
                        random.uniform(880, 1050),
                        random.uniform(180, 280),
                        C.ELDRITCH_PURPLE,
                    )
                # Screen micro-shake at random intervals
                if random.random() < 0.05:
                    self.trigger_shake(intensity=2, duration=0.05)

                if self._victory_timer >= 0.8:
                    self._victory_state = "reality_break"
                    self._victory_timer = 0.0

            elif self._victory_state == "reality_break":
                # Phase 2: Glitch intensifies, bar shatters, name becomes symbols (0.5s)
                # Intensity ramps from 0.5 to 1.0
                self._glitch_intensity = 0.5 + min(0.5, self._victory_timer / 0.5 * 0.5)
                self._glitch_bar_flicker = random.uniform(-20, 20) * self._glitch_intensity
                # Name scrambles faster
                self._glitch_name_timer += dt
                if self._glitch_name_timer > 0.04:
                    self._glitch_name_timer = 0.0
                    self._corrupt_enemy_name()
                # More intense screen jitter
                if random.random() < 0.1:
                    self.trigger_shake(intensity=4, duration=0.05)
                # Spawn glitch particles (digital noise fragments)
                if random.random() < 0.15:
                    self.particles.append(
                        {
                            "x": random.uniform(820, 1100),
                            "y": random.uniform(120, 240),
                            "vx": random.uniform(-2, 2),
                            "vy": random.uniform(-1, 1),
                            "size": random.randint(1, 4),
                            "color": random.choice([C.ELDRITCH_PURPLE, C.CRIMSON, C.YELLOW]),
                            "alpha": random.randint(100, 200),
                            "life": random.uniform(0.2, 0.6),
                        }
                    )
                # At end: snap HP bar to 0
                if self._victory_timer >= 0.5:
                    self._glitch_bar_snap = True
                    # Big screen crack shake
                    self.trigger_shake(intensity=14, duration=0.3)
                    self._victory_state = "glitch_vanish"
                    self._victory_timer = 0.0
                    # Build distortion table for per-column offsets
                    sprite_w = 240
                    self._vanish_distortion = [random.uniform(-3, 3) for _ in range(sprite_w // 4)]
                    self._vanish_opacity = 255.0

            elif self._victory_state == "glitch_vanish":
                # Phase 3: Sprite glitches harder and harder, then vanishes (1.3s)
                vanish_dur = 1.3
                self._vanish_progress = min(1.0, self._victory_timer / vanish_dur)
                # Glitch intensity keeps climbing past 1.0 for extreme effects
                self._glitch_intensity = 1.0 + self._vanish_progress * 0.8
                self._glitch_bar_flicker = random.uniform(-30, 30) * self._glitch_intensity
                # Opacity drops: stays high for first 40%, then plummets
                if self._vanish_progress < 0.4:
                    # Still mostly visible, just heavy glitch
                    self._vanish_opacity = 255.0
                else:
                    # Rapid opacity drop — sprite is dying
                    fade_t = (self._vanish_progress - 0.4) / 0.6  # 0→1
                    self._vanish_opacity = max(0, 255.0 * (1.0 - ease_in_cubic(fade_t)))
                # Update distortion table — gets more extreme
                for i in range(len(self._vanish_distortion)):
                    self._vanish_distortion[i] += random.uniform(-4, 4) * self._vanish_progress
                    self._vanish_distortion[i] *= 0.85  # damping
                # Intense screen jitter
                if random.random() < 0.12 * self._vanish_progress:
                    self.trigger_shake(intensity=int(4 + 10 * self._vanish_progress), duration=0.05)
                # Glitch particles — more and more as vanish progresses
                if random.random() < 0.2 + self._vanish_progress * 0.3:
                    self.particles.append(
                        {
                            "x": random.uniform(820, 1100),
                            "y": random.uniform(160, 320),
                            "vx": random.uniform(-3, 3),
                            "vy": random.uniform(-2, 2),
                            "size": random.randint(1, 5),
                            "color": random.choice(
                                [
                                    C.ELDRITCH_PURPLE,
                                    C.CRIMSON,
                                    C.YELLOW,
                                    (90, 30, 110),
                                    (50, 15, 80),
                                    (30, 5, 50),
                                ]
                            ),
                            "alpha": random.randint(100, 220),
                            "life": random.uniform(0.2, 0.8),
                        }
                    )

                if self._victory_timer >= vanish_dur:
                    # Cache the afterimage silhouette before sprite is gone
                    self._build_afterimage()
                    self._vanish_opacity = 0
                    self._victory_state = "afterimage"
                    self._victory_timer = 0.0
                    self._afterimage_alpha = 180

            elif self._victory_state == "afterimage":
                # Phase 4: Burned-in silhouette fades, wisps drift (1.2s)
                # Fade the afterimage
                fade_dur = 1.2
                t = min(1.0, self._victory_timer / fade_dur)
                self._afterimage_alpha = int(180 * (1.0 - ease_in_quad(t)))
                # Start tightening vignette
                self._victory_vignette_intensity = min(0.7, t * 0.7)
                # Drift wisps upward from where the enemy was
                if random.random() < 0.2:
                    # Use the enemy sprite area center for wisps
                    sprite_w = 240
                    cx = SCREEN_W - sprite_w - 40 + sprite_w // 2
                    cy = 202 + 120  # Approximate center of sprite area
                    self.particles.append(
                        {
                            "x": cx + random.uniform(-40, 40),
                            "y": cy + random.uniform(-20, 20),
                            "vx": random.uniform(-0.3, 0.3),
                            "vy": random.uniform(-1.2, -0.4),
                            "size": random.randint(2, 5),
                            "color": random.choice(
                                [
                                    (140, 100, 200),
                                    (80, 50, 130),
                                    (50, 15, 80),
                                    (200, 160, 40),
                                    (30, 5, 50),
                                ]
                            ),
                            "alpha": random.randint(40, 120),
                            "life": random.uniform(0.8, 2.0),
                        }
                    )
                # Add combat log horror message
                if self._victory_timer > 0.3 and not hasattr(self, "_afterimage_logged"):
                    self._afterimage_logged = True
                    s = self.ctx.state
                    c = s.combat
                    if c:
                        msg = self._get_death_message(c.is_boss, c.enemy.name)
                        c.add_log(msg, "info")

                if self._victory_timer >= fade_dur:
                    self._victory_state = "fade"
                    self._victory_timer = 0.0

            elif self._victory_state == "fade":
                # Phase 5: Vignette tightens, screen darkens, transition (0.8s)
                fade_dur = 0.8
                t = min(1.0, self._victory_timer / fade_dur)
                self._victory_fade_alpha = min(255, int(255 * ease_in_cubic(t)))
                self._victory_vignette_intensity = min(1.0, 0.7 + t * 0.3)

                if self._victory_timer >= fade_dur:
                    self._finish_victory()
                    return

            # During victory animation, update particles but skip normal logic
            self._update_particles(dt)
            # Update damage numbers
            for dn in self.damage_numbers:
                dn[2] += dn[5] * dt  # y position
                dn[4] -= dt  # timer
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
            self.particles.extend(
                create_particle(
                    "eldritch", random.uniform(0, SCREEN_W), random.uniform(120, SCREEN_H), count=1, spread=5
                )
            )
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
        s = self.ctx.state
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
                        self.play_click()
                        self._use_skill(i)
            for name, btn in self.cmd_buttons.items():
                if btn.collidepoint(event.pos):
                    self.play_click()
                    if name == "run":
                        self._try_run()
                    elif name == "inventory":
                        self.ctx.navigate(ScreenName.INVENTORY)
                    elif name == "save":
                        self.ctx.navigate(ScreenName.SAVE)
        elif event.type == pygame.KEYDOWN:
            if pygame.K_1 <= event.key <= pygame.K_9:
                idx = event.key - pygame.K_1
                if idx < len(s.active_skills):
                    self.play_click()
                    self._use_skill(idx)
            elif event.key == pygame.K_r:
                self.play_click()
                self._try_run()
            elif event.key == pygame.K_i:
                self.play_click()
                self.ctx.navigate(ScreenName.INVENTORY)
            elif event.key == pygame.K_s:
                self.play_click()
                self.ctx.navigate(ScreenName.SAVE)

    def _use_skill(self, idx):
        s = self.ctx.state
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
        s = self.ctx.state
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
        s = self.ctx.state
        c = s.combat
        if not c or c.is_boss:
            self.turn_message = "Cannot flee from the Spiral!"
            self.turn_msg_timer = 1.5
            return
        if combat_run_attempt(s):
            s.combat = None
            advance_floor(s)
            self.ctx.navigate(ScreenName.EXPLORE)
        else:
            self.turn_message = "Failed to escape!"
            self.turn_msg_timer = 1.5
            c.turn = "enemy"
            self._do_enemy_turn()

    def _end_combat(self, victory):
        """End combat. On victory, start animation sequence. On defeat, go to game over."""
        s = self.ctx.state
        c = s.combat
        if not c:
            return

        if victory:
            self._start_victory_animation()
        else:
            s.combat = None
            self.ctx.screen_data["gameover_msg"] = (
                "Your body crumples. The last thing you see is the Yellow Sign, burning brighter than ever."
            )
            self.ctx.navigate(ScreenName.GAMEOVER)

    def _start_victory_animation(self):
        """Begin the multi-phase horror death animation."""
        s = self.ctx.state
        c = s.combat
        self._victory_is_boss = c.is_boss
        self._victory_timer = 0.0
        self._victory_fade_alpha = 0
        self._victory_vignette_intensity = 0.0
        self._glitch_intensity = 0.0
        self._glitch_name_corrupted = c.enemy.name
        self._glitch_name_timer = 0.0
        self._glitch_bar_snap = False
        self._glitch_bar_flicker = 0.0
        self._vanish_progress = 0.0
        self._vanish_opacity = 255.0
        self._vanish_distortion = []
        self._afterimage_alpha = 0
        self._afterimage_surface = None
        # Clear any stale logged flag
        if hasattr(self, "_afterimage_logged"):
            del self._afterimage_logged
        self._victory_state = "glitch_onset"
        # Initial screen crack
        self.trigger_shake(intensity=8, duration=0.2)

    def _corrupt_enemy_name(self):
        """Progressively replace characters in the enemy name with eldritch symbols."""
        s = self.ctx.state
        c = s.combat
        if not c:
            return
        original = c.enemy.name
        # How many characters to corrupt based on glitch intensity
        num_to_corrupt = int(len(original) * self._glitch_intensity * 1.5)
        name_chars = list(original)
        indices = list(range(len(name_chars)))
        random.shuffle(indices)
        for i in indices[:num_to_corrupt]:
            if name_chars[i] != " ":
                name_chars[i] = random.choice(self._eldritch_symbols)
        self._glitch_name_corrupted = "".join(name_chars)

    def _build_afterimage(self):
        """Create a dark silhouette surface from the enemy sprite for the afterimage phase."""
        s = self.ctx.state
        c = s.combat
        if not c:
            return
        enemy_sprite = self.assets.get_sprite(c.enemy.name)
        if not enemy_sprite:
            self._afterimage_surface = None
            return
        # Scale to combat size
        sprite_w = 240
        sw, sh = enemy_sprite.get_size()
        if sw != sprite_w:
            scale_h = int(sh * sprite_w / sw)
            enemy_sprite = pygame.transform.scale(enemy_sprite, (sprite_w, scale_h))
        # Create a dark silhouette using pygame surface operations (fast, no per-pixel loop)
        # Step 1: Create a dark purple-black overlay
        dark_overlay = pygame.Surface(enemy_sprite.get_size(), pygame.SRCALPHA)
        dark_overlay.fill((30, 5, 50, 220))  # Dark purple-black
        # Step 2: Copy sprite alpha mask, apply dark color where sprite is opaque
        silhouette = enemy_sprite.copy()
        silhouette.blit(dark_overlay, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
        # Step 3: Add subtle edge glow by blitting a purple-tinted version underneath
        glow_version = enemy_sprite.copy()
        purple_overlay = pygame.Surface(enemy_sprite.get_size(), pygame.SRCALPHA)
        purple_overlay.fill((140, 60, 180, 60))
        glow_version.blit(purple_overlay, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
        # Combine: glow behind, dark silhouette on top
        combined = pygame.Surface(enemy_sprite.get_size(), pygame.SRCALPHA)
        combined.blit(glow_version, (0, 0))
        combined.blit(silhouette, (0, 0))
        self._afterimage_surface = combined

    def _get_death_message(self, is_boss, enemy_name):
        """Return a thematic horror death message for the combat log."""
        boss_messages = [
            "The Spiral collapses. Reality shudders.",
            "The form unravels. Something vast recedes.",
            "It does not die. It... leaves. For now.",
            "The Yellow Sign flickers. The gate closes.",
            "Hastur's echo fades, but the memory lingers.",
        ]
        normal_messages = [
            f"The {enemy_name} dissolves into shadow.",
            f"Reality reasserts itself. The {enemy_name} is unmade.",
            f"The {enemy_name} collapses inward. Nothing remains.",
            f"The form of the {enemy_name} peels away like wet parchment.",
            f"The {enemy_name} implodes. Silence follows.",
            f"Something pulls the {enemy_name} apart from within.",
            f"The {enemy_name} flickers once more, then is gone.",
        ]
        if is_boss:
            return random.choice(boss_messages)
        return random.choice(normal_messages)

    def _finish_victory(self):
        """Actually compute rewards and switch to result screen."""
        s = self.ctx.state
        c = s.combat
        if not c:
            return
        # Safety guard: only finish once — keep _victory_state set until AFTER
        # the screen switch to prevent the enemy sprite from flashing back
        if not self._victory_state:
            return

        s.kills += 1
        xp_g = XP_BASE + s.floor * XP_PER_FLOOR + (XP_BOSS_BONUS if c.is_boss else 0)
        gold_g = (
            GOLD_BASE
            + random.randint(0, GOLD_BASE_RANDOM_MAX)
            + s.floor * GOLD_PER_FLOOR
            + (GOLD_BOSS_BONUS if c.is_boss else 0)
        )
        s.xp += xp_g
        s.gold += gold_g
        s.add_madness(MADNESS_BOSS_KILL if c.is_boss else MADNESS_NORMAL_KILL)
        loot = generate_item(s.floor, luck=s.luck, buffs=s.buffs)
        leveled = s.check_level_up()

        self.ctx.screen_data["combat_result"] = {
            "victory": True,
            "xp": xp_g,
            "gold": gold_g,
            "loot": loot,
            "is_boss": c.is_boss,
            "leveled": leveled,
        }
        # Clear combat FIRST (so draw() early-returns), then victory state
        s.combat = None
        self._victory_state = None
        if leveled:
            self.ctx.navigate(ScreenName.LEVELUP)
        else:
            self.ctx.navigate(ScreenName.COMBAT_RESULT)

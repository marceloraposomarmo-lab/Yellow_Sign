import pygame
import math
from shared import C, SCREEN_W, SCREEN_H, Assets, draw_hud, draw_text, draw_text_wrapped, fit_text, draw_text_fitted, draw_bar, draw_panel, draw_ornate_panel, draw_ornate_button, draw_gold_divider, hp_color, mad_color, rarity_color, generate_parchment_texture, draw_parchment_panel, draw_text_with_glow, draw_text_wrapped_glow, draw_text_fitted_glow, draw_status_icons_row, draw_status_tooltip
import random
from screens.base import Screen
from engine import (player_use_skill, enemy_turn, check_boss_phase,
                    tick_player_buffs, process_status_effects,
                    process_player_status_effects, generate_item, advance_floor,
                    combat_run_attempt, _get_enemy_intent_message,
                    calc_preview_damage)
from data import (XP_BASE, XP_PER_FLOOR, XP_BOSS_BONUS,
                  GOLD_BASE, GOLD_PER_FLOOR, GOLD_BOSS_BONUS, GOLD_BASE_RANDOM_MAX,
                  MADNESS_BOSS_KILL, MADNESS_NORMAL_KILL)


# ═══════════════════════════════════════════════════════════════════════════════
# PARTICLE TYPE DEFINITIONS
# Centralized particle configurations for consistent visual effects
# ═══════════════════════════════════════════════════════════════════════════════

class ParticleType:
    """Defines a particle effect type with color palette, size range, speed, and behavior."""

    def __init__(self, colors, size_range, speed_range, alpha_range, life_range,
                 gravity=0, rotation=False, special=None):
        self.colors = colors
        self.size_range = size_range  # (min, max)
        self.speed_range = speed_range  # velocity multiplier
        self.alpha_range = alpha_range
        self.life_range = life_range
        self.gravity = gravity
        self.rotation = rotation
        self.special = special  # Optional special behavior


# Pre-defined particle types for easy reuse
PARTICLE_TYPES = {
    # Combat particles
    "blood": ParticleType(
        colors=[(196, 30, 58), (139, 0, 0), (220, 50, 50), (180, 20, 40)],
        size_range=(2, 5), speed_range=(0.5, 1.5), alpha_range=(120, 220),
        life_range=(0.5, 1.5), gravity=150
    ),
    "crit_blood": ParticleType(
        colors=[(255, 215, 0), (255, 180, 0), (220, 50, 50), (196, 30, 58)],
        size_range=(3, 7), speed_range=(1.0, 2.5), alpha_range=(150, 255),
        life_range=(0.8, 2.0), gravity=120
    ),

    # Magic/skill particles
    "magic": ParticleType(
        colors=[(175, 130, 225), (140, 100, 200), (80, 50, 130), (200, 160, 255)],
        size_range=(2, 5), speed_range=(0.3, 0.8), alpha_range=(80, 160),
        life_range=(1.0, 2.5)
    ),
    "magic_burst": ParticleType(
        colors=[(200, 160, 255), (175, 130, 225), (255, 200, 100)],
        size_range=(3, 8), speed_range=(1.5, 3.0), alpha_range=(100, 200),
        life_range=(0.5, 1.5), gravity=-30  # Floats upward
    ),

    # Healing particles
    "heal": ParticleType(
        colors=[(143, 188, 143), (46, 204, 113), (152, 251, 152), (100, 255, 100)],
        size_range=(2, 4), speed_range=(0.2, 0.6), alpha_range=(100, 180),
        life_range=(1.0, 2.0), gravity=-50  # Floats upward
    ),

    # Shield/barrier particles
    "shield": ParticleType(
        colors=[(100, 180, 255), (70, 130, 200), (150, 200, 255)],
        size_range=(1, 3), speed_range=(0.1, 0.4), alpha_range=(60, 120),
        life_range=(1.5, 3.0), gravity=-20
    ),

    # Eldritch/cosmic particles (ambient)
    "eldritch": ParticleType(
        colors=[(175, 130, 225), (140, 100, 200), (80, 50, 130), (200, 160, 40)],
        size_range=(1, 3), speed_range=(0.1, 0.3), alpha_range=(20, 60),
        life_range=(2.0, 6.0)
    ),

    # Victory particles
    "victory_gold": ParticleType(
        colors=[(255, 215, 0), (175, 130, 225), (220, 180, 50), (140, 100, 200)],
        size_range=(2, 6), speed_range=(2.0, 5.0), alpha_range=(150, 255),
        life_range=(1.0, 2.5), gravity=80
    ),
    "victory_spark": ParticleType(
        colors=[(255, 240, 200), (255, 220, 100), (255, 200, 50)],
        size_range=(1, 2), speed_range=(3.0, 8.0), alpha_range=(200, 255),
        life_range=(0.3, 0.8)
    ),

    # Damage numbers burst
    "damage_burst": ParticleType(
        colors=[(255, 255, 255), (255, 200, 100), (255, 150, 50)],
        size_range=(1, 2), speed_range=(2.0, 4.0), alpha_range=(100, 180),
        life_range=(0.3, 0.8), gravity=-40
    ),

    # Debuff particles
    "poison": ParticleType(
        colors=[(50, 200, 50), (30, 150, 30), (100, 200, 100)],
        size_range=(2, 4), speed_range=(0.15, 0.4), alpha_range=(60, 120),
        life_range=(1.0, 2.0), gravity=30
    ),
    "burn": ParticleType(
        colors=[(255, 100, 0), (255, 50, 0), (255, 200, 50)],
        size_range=(2, 5), speed_range=(0.3, 0.7), alpha_range=(80, 150),
        life_range=(0.5, 1.5), gravity=-60
    ),

    # Madness particles
    "madness": ParticleType(
        colors=[(255, 99, 71), (255, 215, 0), (139, 0, 0), (200, 100, 50)],
        size_range=(2, 5), speed_range=(0.3, 0.8), alpha_range=(80, 150),
        life_range=(1.0, 2.5), gravity=20
    ),

    # Enemy action intent particles
    "intent_attack": ParticleType(
        colors=[(196, 30, 58), (255, 80, 80), (180, 40, 40)],
        size_range=(2, 4), speed_range=(0.2, 0.5), alpha_range=(60, 100),
        life_range=(1.0, 2.0)
    ),
    "intent_spell": ParticleType(
        colors=[(175, 130, 225), (200, 160, 255), (120, 80, 180)],
        size_range=(2, 4), speed_range=(0.15, 0.4), alpha_range=(60, 100),
        life_range=(1.0, 2.0)
    ),
    "intent_buff": ParticleType(
        colors=[(100, 200, 255), (150, 220, 255), (80, 180, 220)],
        size_range=(2, 4), speed_range=(0.1, 0.3), alpha_range=(50, 90),
        life_range=(1.0, 2.0), gravity=-30
    ),
}


def create_particle(particle_type_name, x, y, count=1, spread=15, base_vx=0, base_vy=0):
    """
    Factory function to create particles of a given type.

    Args:
        particle_type_name: Key from PARTICLE_TYPES dict
        x, y: Center position for particle spawn
        count: Number of particles to create
        spread: Random position offset from center
        base_vx, base_vy: Base velocity to add to random velocity

    Returns:
        List of particle dictionaries ready to be added to the particle system
    """
    ptype = PARTICLE_TYPES.get(particle_type_name, PARTICLE_TYPES["eldritch"])
    particles = []

    for _ in range(count):
        particle = {
            "x": x + random.uniform(-spread, spread),
            "y": y + random.uniform(-spread, spread),
            "vx": base_vx + random.uniform(-ptype.speed_range[0], ptype.speed_range[1]) * 50,
            "vy": base_vy + random.uniform(-ptype.speed_range[0], ptype.speed_range[1]) * 50,
            "size": random.randint(ptype.size_range[0], ptype.size_range[1]),
            "color": random.choice(ptype.colors),
            "alpha": random.randint(ptype.alpha_range[0], ptype.alpha_range[1]),
            "life": random.uniform(ptype.life_range[0], ptype.life_range[1]),
        }

        if ptype.gravity != 0:
            particle["gravity"] = ptype.gravity
        if ptype.rotation:
            particle["rot"] = random.uniform(0, 360)
            particle["rot_v"] = random.uniform(-180, 180)

        particles.append(particle)

    return particles


def create_burst(x, y, particle_type_name, count=30, outward=True, upward_bias=0):
    """
    Create an outward burst of particles from a center point.

    Args:
        x, y: Center of burst
        particle_type_name: Type of particles
        count: Number of particles
        outward: If True, particles move away from center; if False, random directions
        upward_bias: Add upward velocity component (negative = more upward)
    """
    ptype = PARTICLE_TYPES.get(particle_type_name, PARTICLE_TYPES["victory_gold"])
    particles = []

    for _ in range(count):
        if outward:
            angle = random.uniform(0, math.pi * 2)
            speed = random.uniform(ptype.speed_range[0], ptype.speed_range[1]) * 100
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed + upward_bias
        else:
            vx = random.uniform(-100, 100)
            vy = random.uniform(-150, 50) + upward_bias

        particle = {
            "x": x + random.uniform(-10, 10),
            "y": y + random.uniform(-10, 10),
            "vx": vx * ptype.speed_range[1] * 0.3,
            "vy": vy * ptype.speed_range[1] * 0.3,
            "size": random.randint(ptype.size_range[0], ptype.size_range[1]),
            "color": random.choice(ptype.colors),
            "alpha": random.randint(ptype.alpha_range[0], ptype.alpha_range[1]),
            "life": random.uniform(ptype.life_range[0], ptype.life_range[1]),
        }

        if ptype.gravity != 0:
            particle["gravity"] = ptype.gravity

        particles.append(particle)

    return particles

class CombatScreen(Screen):
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
        self.damage_numbers.append([text, x, y, color, 1.5, -60, 1.5 if is_crit else 1.2, is_crit, y])

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

        # Palette: strictly purple / crimson / gold
        _PURPLE = (175, 130, 225)
        _PURPLE_DEEP = (120, 60, 180)
        _PURPLE_VOID = (74, 14, 78)
        _CRIMSON = (196, 30, 58)
        _CRIMSON_DARK = (120, 15, 30)
        _GOLD = (212, 160, 23)
        _GOLD_BRIGHT = (232, 185, 45)

        # Victorian decorative runes
        _ELDRITCH_RUNES = ["\u2020", "\u2726", "\u263D", "\u2694", "\u2736", "\u2625", "\u271D"]

        for dn in self.damage_numbers:
            text, x, y, color, timer, vy, scale, is_crit = dn[:8]

            # ── Font selection ──
            if is_crit:
                base_font = self.assets.fonts.get("eldritch_crit") or self.assets.fonts["heading"]
                rune_font = self.assets.fonts.get("eldritch_rune") or self.assets.fonts["small"]
            else:
                base_font = self.assets.fonts.get("eldritch") or self.assets.fonts["heading"]
                rune_font = self.assets.fonts.get("eldritch_rune") or self.assets.fonts["small"]

            # ── Proper themed font scaling for pop effect ──
            if scale != 1.0 and self.assets._font_paths.get("eldritch"):
                try:
                    font_size = int(base_font.get_height() * scale)
                    scaled_font = pygame.font.Font(self.assets._font_paths["eldritch"],
                                                   max(14, font_size))
                except Exception:
                    scaled_font = base_font
            else:
                scaled_font = base_font

            # ── Subtle wave distortion ──
            if is_crit:
                wave_x = math.sin(self._time * 5.0 + y * 0.04) * 3
                wave_y = math.cos(self._time * 4.0 + x * 0.02) * 1.5
            else:
                wave_x = math.sin(self._time * 2.0 + y * 0.03) * 1.5
                wave_y = 0

            base_draw_x = int(x + wave_x) + ox
            base_draw_y = int(y + wave_y) + oy

            # ── Flickering alpha ──
            if is_crit:
                flicker = 0.75 + 0.25 * math.sin(self._time * 8.0)
            else:
                flicker = 0.9 + 0.1 * math.sin(self._time * 4.0 + x)
            alpha_mod = int(255 * flicker)

            # ── PER-CHARACTER RENDERING ──
            chars = list(text)
            char_surfaces = []
            total_w = 0

            for ci, ch in enumerate(chars):
                seed = ci * 7.3 + hash(ch) * 0.13

                if is_crit:
                    # Refined writhe — Victorian menace, not a carnival
                    char_rot = math.sin(self._time * 5.0 + seed) * 4     # ±4 degrees
                    char_dy = math.sin(self._time * 3.5 + seed * 1.3) * 2  # ±2px
                    char_scale = 1.0 + math.sin(self._time * 3.0 + seed * 0.9) * 0.06  # 0.94-1.06
                    corrupted = random.random() < 0.05  # Rare corruption
                    if corrupted:
                        char_rot += random.choice([-12, 12])
                        char_scale *= 1.15
                else:
                    # Nearly still — elegant drift
                    char_rot = math.sin(self._time * 2.5 + seed) * 1.5  # ±1.5 degrees
                    char_dy = math.sin(self._time * 2.0 + seed) * 1.0  # ±1px
                    char_scale = 1.0 + math.sin(self._time * 1.5 + seed) * 0.03
                    corrupted = False

                # Render character
                if abs(char_scale - 1.0) > 0.01 and self.assets._font_paths.get("eldritch"):
                    try:
                        ch_size = max(12, int(scaled_font.get_height() * char_scale))
                        ch_font = pygame.font.Font(self.assets._font_paths["eldritch"], ch_size)
                        ch_surf = ch_font.render(ch, True, (255, 255, 255))
                    except Exception:
                        ch_surf = scaled_font.render(ch, True, (255, 255, 255))
                else:
                    ch_surf = scaled_font.render(ch, True, (255, 255, 255))

                if abs(char_rot) > 0.3:
                    ch_surf = pygame.transform.rotate(ch_surf, char_rot)

                char_surfaces.append((ch_surf, char_dy, corrupted, ci))
                total_w += ch_surf.get_width()

            cursor_x = base_draw_x - total_w // 2

            # ── PASS 1: Ghost shadow (purple only) ──
            shadow_colors = [_PURPLE_DEEP, _PURPLE_VOID, _PURPLE]
            num_trails = 2 if is_crit else 1
            for trail_i in range(num_trails):
                trail_alpha = max(0, int(alpha_mod * (0.30 - trail_i * 0.12)))
                trail_color = shadow_colors[trail_i % len(shadow_colors)]
                trail_ox = (trail_i + 1) * (3 if is_crit else 2)
                trail_oy = (trail_i + 1) * 2
                tcx = cursor_x
                for ch_surf, char_dy, _, _ in char_surfaces:
                    shadow = ch_surf.copy()
                    shadow.fill(trail_color, special_flags=pygame.BLEND_RGBA_MULT)
                    shadow.set_alpha(trail_alpha)
                    surface.blit(shadow, (tcx + trail_ox,
                                          base_draw_y - ch_surf.get_height() // 2
                                          + char_dy + trail_oy))
                    tcx += ch_surf.get_width()

            # ── PASS 2: Glow aura ──
            if is_crit:
                glow_colors = [_GOLD_BRIGHT, _PURPLE, _GOLD, _CRIMSON]
                for gi, glow_col in enumerate(glow_colors):
                    glow_alpha = max(0, int(alpha_mod * (0.22 - gi * 0.05)))
                    spread = 2 + gi
                    gcx = cursor_x
                    for ch_surf, char_dy, _, ci in char_surfaces:
                        glow = ch_surf.copy()
                        glow.fill(glow_col, special_flags=pygame.BLEND_RGBA_MULT)
                        glow.set_alpha(glow_alpha)
                        gx = gcx + math.sin(self._time * 3.0 + gi + ci) * spread
                        gy = (base_draw_y - ch_surf.get_height() // 2 + char_dy
                              + math.cos(self._time * 2.5 + gi * 0.7 + ci) * spread)
                        surface.blit(glow, (gx, gy))
                        gcx += ch_surf.get_width()
            else:
                gcx = cursor_x
                for ch_surf, char_dy, _, _ in char_surfaces:
                    glow = ch_surf.copy()
                    glow.fill(_PURPLE_DEEP, special_flags=pygame.BLEND_RGBA_MULT)
                    glow.set_alpha(int(alpha_mod * 0.15))
                    surface.blit(glow, (gcx + 2,
                                        base_draw_y - ch_surf.get_height() // 2
                                        + char_dy + 2))
                    gcx += ch_surf.get_width()

            # ── PASS 3: Main characters ──
            for ch_surf, char_dy, corrupted, ci in char_surfaces:
                # Crits: oscillate between gold and purple. Normal: muted purple tint.
                if is_crit:
                    t = self._time * 2.5 + ci * 0.4
                    blend = (math.sin(t) + 1.0) * 0.5  # 0..1
                    eld_color = (
                        int(_GOLD[0] * blend + _PURPLE[0] * (1 - blend)),
                        int(_GOLD[1] * blend + _PURPLE[1] * (1 - blend)),
                        int(_GOLD[2] * blend + _PURPLE[2] * (1 - blend)),
                    )
                else:
                    eld_color = _PURPLE

                colored = ch_surf.copy()
                colored.fill(eld_color, special_flags=pygame.BLEND_RGBA_MULT)
                colored.set_alpha(alpha_mod)

                # Corrupted chars pulse crimson instead of white
                if corrupted:
                    flash_overlay = colored.copy()
                    flash_overlay.fill(_CRIMSON, special_flags=pygame.BLEND_RGBA_MULT)
                    flash_overlay.set_alpha(int(alpha_mod * 0.5))
                    surface.blit(flash_overlay,
                                 (cursor_x, base_draw_y - ch_surf.get_height() // 2 + char_dy))

                draw_y_char = base_draw_y - ch_surf.get_height() // 2 + char_dy
                surface.blit(colored, (cursor_x, draw_y_char))
                cursor_x += ch_surf.get_width()

            # ── PASS 4: Victorian rune particles (crits only) ──
            if is_crit and random.random() < 0.20:
                rune_char = random.choice(_ELDRITCH_RUNES)
                rune_color = random.choice([_PURPLE, _GOLD, _CRIMSON])
                rune_alpha = random.randint(40, 110)
                rune_rot = random.uniform(-15, 15)
                try:
                    rune_surf = rune_font.render(rune_char, True, rune_color)
                except Exception:
                    rune_surf = scaled_font.render("*", True, rune_color)
                if abs(rune_rot) > 1:
                    rune_surf = pygame.transform.rotate(rune_surf, rune_rot)
                rune_surf.set_alpha(rune_alpha)
                rune_x = base_draw_x + random.randint(-25, 25) - rune_surf.get_width() // 2
                rune_y = base_draw_y + random.randint(-18, 10) - rune_surf.get_height() // 2
                surface.blit(rune_surf, (rune_x, rune_y))

        # Status effect tooltips on hover
        self._draw_status_tooltips(surface)

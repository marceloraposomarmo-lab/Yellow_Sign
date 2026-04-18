import math
import random


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

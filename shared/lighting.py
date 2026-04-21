"""
THE KING IN YELLOW — Dynamic Lighting System

Provides atmospheric lighting effects for the Lovecraftian horror aesthetic.
The design philosophy is restraint: light is scarce, sickly, and dying. What
lurks in the darkness is left to the player's imagination.

  - HP-based vignette: screen edges close in with oppressive blackness as HP drops
  - Torch flicker: dying gaslight with faint, sputtering warmth
  - Status whispers: barely perceptible color tints at screen edges —
    not glowing auras, but unsettling suggestions that something is wrong
  - Depth darkness: progressive engulfment as the player descends into the Spiral
  - Ambient breathing: imperceptible light/dark cycle for creeping unease
  - Boss eldritch pulse: a faint wrongness in the air, not a neon light show

Architecture:
  - LightingSystem class holds state and cached surfaces
  - Called from pygame_game.py after screen.draw() but before transition overlay
  - Screens can register light sources via add_light() / remove_light()
  - Uses SRCALPHA surfaces composited with BLEND_RGBA_ADD for subtle glow
  - Full-screen darkness overlay with radial-gradient "light holes" punched in
"""

import math
import random

import pygame

from shared.constants import SCREEN_W, SCREEN_H
from shared.surface_pool import surface_pool

# ═══════════════════════════════════════════
# LIGHT SOURCE DEFINITIONS
# ═══════════════════════════════════════════

# Colors for status whispers — desaturated, dark, barely-there tints.
# Lovecraftian horror suggests wrongness; it does not announce it with neon.
_STATUS_GLOW_COLORS = {
    "burning": (80, 35, 10),  # Dying embers, barely smouldering
    "poisoned": (25, 50, 15),  # Putrid undergrowth rot
    "bleeding": (55, 10, 10),  # Old bloodstain, dried and dark
    "weakened": (45, 40, 22),  # Jaundiced, sickly pallor
    "freezing": (25, 40, 60),  # Cold tombstone, not ice blue
    "petrified": (40, 35, 30),  # Dead stone, grey and lifeless
    "doom": (30, 5, 20),  # The void whispering at the edge
}

# Torch light color: dying gaslight — sickly warm, not cheerful amber.
# Imagine a candle in a forgotten asylum corridor.
_TORCH_COLOR = (150, 125, 75)
_TORCH_FLICKER_COLOR = (120, 95, 55)

# HP-based vignette colors: oppressive blackness closing in, not a red flash.
_HP_VIGNETTE_HIGH = (0, 0, 0, 0)  # No vignette at full HP
_HP_VIGNETTE_LOW = (15, 2, 5, 200)  # Near-black with a faint dried-blood tint

# Depth darkness: the Spiral devours light. Deeper = darker, more claustrophobic.
_DEPTH_DARKNESS = {
    # floor_range: (ambient_alpha, torch_radius_mult, vignette_intensity)
    (1, 4): (15, 0.85, 0.05),  # The Asylum: dimly lit, not safe
    (5, 8): (35, 0.72, 0.15),  # The Depths Below: corridors narrow
    (9, 12): (55, 0.58, 0.30),  # The Descent: light is dying
    (13, 16): (80, 0.42, 0.50),  # Approaching the Threshold: suffocating
    (17, 20): (110, 0.25, 0.70),  # The Spiral: nearly pitch black
}

# Cache settings
_LIGHT_TEXTURE_CACHE_SIZE = 6
_LIGHT_TEXTURE_MAX_RADIUS = 512


# ═══════════════════════════════════════════
# RADIAL GRADIENT LIGHT TEXTURE GENERATOR
# ═══════════════════════════════════════════

_light_texture_cache: dict = {}


def _get_light_texture(radius: int, color: tuple, intensity: float = 1.0) -> pygame.Surface:
    """Get or generate a cached radial gradient light texture.

    Creates a pre-rendered circular gradient that goes from the given color
    at the center to fully transparent at the edges. Used as a "stamp" for
    light sources, blitted with BLEND_RGBA_ADD for additive glow.

    Args:
        radius: Radius of the light in pixels
        color: RGB color tuple for the light
        intensity: Brightness multiplier (0.0 to 1.0)

    Returns:
        A pygame Surface with the radial gradient, sized (radius*2, radius*2)
    """
    # Clamp radius to prevent excessive memory use
    radius = min(radius, _LIGHT_TEXTURE_MAX_RADIUS)
    # Quantize for caching (step of 4px for radius, 10 for intensity)
    cache_key = (radius // 4, color, int(intensity * 10))
    if cache_key in _light_texture_cache:
        return _light_texture_cache[cache_key]

    size = radius * 2
    surf = pygame.Surface((size, size), pygame.SRCALPHA)

    # Draw concentric circles from outside in — inner circles overwrite outer
    num_rings = min(radius, 60)  # Cap rings for performance
    for i in range(num_rings, 0, -1):
        ratio = i / num_rings
        # Alpha falls off with a quadratic curve — intentionally dim.
        # Real torches in dungeons are dim; we keep intensity low.
        alpha = int(255 * intensity * (1 - ratio * ratio) * 0.12)
        if alpha < 1:
            continue
        ring_radius = int(radius * ratio)
        r = min(255, int(color[0] * (1 - ratio * 0.2)))
        g = min(255, int(color[1] * (1 - ratio * 0.3)))
        b = min(255, int(color[2] * (1 - ratio * 0.4)))
        pygame.draw.circle(surf, (r, g, b, alpha), (radius, radius), ring_radius)

    # Manage cache size
    if len(_light_texture_cache) >= _LIGHT_TEXTURE_CACHE_SIZE:
        # Remove oldest entry
        oldest_key = next(iter(_light_texture_cache))
        del _light_texture_cache[oldest_key]
    _light_texture_cache[cache_key] = surf
    return surf


# ═══════════════════════════════════════════
# TORCH FLICKER ENGINE
# ═══════════════════════════════════════════


class TorchFlicker:
    """Simulates realistic torch-like light flicker using multiple sine waves.

    Combines several oscillators at different frequencies and amplitudes
    to create an organic, non-repeating flicker pattern. The result is
    a smooth variation in light intensity and slight color temperature
    shifts between warm amber and hot orange.
    """

    def __init__(self):
        # Multiple frequency components for organic flicker
        self._phases = [random.uniform(0, math.tau) for _ in range(5)]
        self._freqs = [1.7, 3.1, 5.3, 0.7, 8.9]  # Hz
        self._amps = [0.08, 0.05, 0.04, 0.12, 0.02]  # Subtle, restrained flicker

    def get_intensity(self, time_seconds: float) -> float:
        """Get current flicker intensity.

        Combines multiple sine waves with different frequencies and
        random phase offsets. The result is a subdued, non-repeating
        flicker pattern that mimics a dying gaslight — sometimes
        brighter, sometimes nearly extinguished.

        Args:
            time_seconds: Total elapsed game time

        Returns:
            Intensity multiplier (typically 0.35 to 0.85)
        """
        val = 0.55  # Dim base — this is a dying torch, not a campfire
        for i, (phase, freq, amp) in enumerate(zip(self._phases, self._freqs, self._amps)):
            # Slow phase drift for non-repeating pattern
            drift = time_seconds * 0.13 * (i + 1)
            val += amp * math.sin(time_seconds * freq + phase + drift)
        return max(0.25, min(0.85, val))

    def get_color(self, time_seconds: float) -> tuple:
        """Get current torch color with subtle temperature shift.

        The torch shifts between sickly warm and cooler tones as the
        flame gutters — never bright, always on the edge of going out.

        Args:
            time_seconds: Total elapsed game time

        Returns:
            RGB tuple (dim warm range)
        """
        temp_shift = 0.5 + 0.5 * math.sin(time_seconds * 1.7)
        r = int(_TORCH_COLOR[0] * (0.85 + 0.15 * temp_shift))
        g = int(_TORCH_FLICKER_COLOR[1] * (0.75 + 0.25 * (1 - temp_shift)))
        b = int(_TORCH_COLOR[2] * (0.4 + 0.6 * temp_shift))
        return (min(255, r), min(255, g), min(255, b))


# ═══════════════════════════════════════════
# LIGHT SOURCE
# ═══════════════════════════════════════════


class LightSource:
    """A single point light source in the scene.

    Each light source has a position, color, radius, and intensity.
    Lights can optionally flicker (like dying torches) or be static (like
    the faint pallor of an unnatural presence). Intensities should be
    kept low to maintain the oppressive darkness of the setting.

    Args:
        x: X position on screen
        y: Y position on screen
        radius: Light radius in pixels
        color: RGB color tuple
        intensity: Base brightness (0.0 to 1.0)
        flicker: If True, apply torch-like flicker animation
        pulse_speed: Speed of gentle pulsing (0 = no pulse)
    """

    def __init__(
        self,
        x: int,
        y: int,
        radius: int = 200,
        color: tuple = _TORCH_COLOR,
        intensity: float = 0.7,
        flicker: bool = False,
        pulse_speed: float = 0.0,
    ):
        self.x = x
        self.y = y
        self.radius = radius
        self.color = color
        self.base_intensity = intensity
        self.flicker = flicker
        self.pulse_speed = pulse_speed
        self._flicker = TorchFlicker() if flicker else None

    def get_current_intensity(self, time_seconds: float) -> float:
        """Get current intensity including flicker and pulse."""
        intensity = self.base_intensity
        if self._flicker:
            intensity *= self._flicker.get_intensity(time_seconds)
        if self.pulse_speed > 0:
            pulse = 0.5 + 0.5 * math.sin(time_seconds * self.pulse_speed)
            intensity *= 0.85 + 0.15 * pulse
        return max(0.0, min(1.0, intensity))

    def get_current_color(self, time_seconds: float) -> tuple:
        """Get current color including flicker temperature shift."""
        if self._flicker:
            return self._flicker.get_color(time_seconds)
        return self.color


# ═══════════════════════════════════════════
# MAIN LIGHTING SYSTEM
# ═══════════════════════════════════════════


class LightingSystem:
    """Central lighting system for the entire game.

    Manages all dynamic light sources and renders a combined lighting
    overlay each frame. The overlay is composited on top of the game
    scene to create atmospheric lighting effects.

    The system renders in layers:
    1. Depth-based ambient darkness overlay
    2. HP-based vignette (red tint at low HP)
    3. Light sources (torch flicker, status glows)
    4. Subtle ambient breathing effect

    Usage:
        lighting = LightingSystem()
        lighting.add_torch(640, 360, radius=250)
        lighting.set_status_effects(["burning", "poisoned"])
        # In game loop:
        lighting.update(dt, time_seconds, game_state)
        lighting.draw(surface)
    """

    def __init__(self):
        self.lights: list = []
        self._status_effects: list = []
        self._hp_ratio: float = 1.0
        self._madness: float = 0.0
        self._floor: int = 1
        self._max_floor: int = 20
        self._in_combat: bool = False
        self._enemy_hp_ratio: float = 1.0
        self._boss: bool = False
        self._enabled: bool = True

        # Cached overlay surface (reused each frame)
        self._overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)

        # Ambient torches for non-combat screens
        self._ambient_torches: list = []
        self._setup_ambient_torches()

    def _setup_ambient_torches(self):
        """Create ambient torch positions — dying wall sconces in a forgotten corridor."""
        # Two dim torches flanking the screen edges, barely holding on
        self._ambient_torches = [
            LightSource(80, SCREEN_H // 2 - 40, radius=220, color=_TORCH_COLOR, intensity=0.14, flicker=True),
            LightSource(
                SCREEN_W - 80, SCREEN_H // 2 - 40, radius=220, color=_TORCH_COLOR, intensity=0.14, flicker=True
            ),
            # Faint ceiling glow — like light filtering through a cracked dome
            LightSource(SCREEN_W // 2, 60, radius=280, color=(110, 100, 80), intensity=0.06, flicker=True),
        ]

    def enable(self):
        """Enable the lighting system."""
        self._enabled = True

    def disable(self):
        """Disable the lighting system (no overlay rendered)."""
        self._enabled = False

    def clear_lights(self):
        """Remove all dynamic light sources (keep ambient torches)."""
        self.lights.clear()

    def add_light(
        self,
        x: int,
        y: int,
        radius: int = 200,
        color: tuple = _TORCH_COLOR,
        intensity: float = 0.7,
        flicker: bool = False,
        pulse_speed: float = 0.0,
    ) -> LightSource:
        """Add a new light source to the scene.

        Args:
            x: X position on screen
            y: Y position on screen
            radius: Light radius in pixels
            color: RGB color tuple
            intensity: Base brightness (0.0 to 1.0)
            flicker: If True, apply torch-like flicker
            pulse_speed: Speed of gentle pulsing (0 = no pulse)

        Returns:
            The created LightSource (can be removed later)
        """
        light = LightSource(x, y, radius, color, intensity, flicker, pulse_speed)
        self.lights.append(light)
        return light

    def remove_light(self, light: LightSource):
        """Remove a previously added light source."""
        if light in self.lights:
            self.lights.remove(light)

    def set_status_effects(self, statuses: list):
        """Update the active status effects for status glow rendering.

        Args:
            statuses: List of status effect type strings (e.g., ["burning", "poisoned"])
        """
        self._status_effects = statuses

    def update_state(
        self,
        hp_ratio: float,
        madness: float,
        floor: int,
        max_floor: int,
        in_combat: bool = False,
        enemy_hp_ratio: float = 1.0,
        is_boss: bool = False,
    ):
        """Update the lighting system with current game state.

        Args:
            hp_ratio: Player HP ratio (0.0 to 1.0)
            madness: Current madness value (0 to 100)
            floor: Current floor number
            max_floor: Maximum floor count
            in_combat: Whether the player is in combat
            enemy_hp_ratio: Enemy HP ratio for combat aura (0.0 to 1.0)
            is_boss: Whether the current enemy is a boss
        """
        self._hp_ratio = hp_ratio
        self._madness = madness
        self._floor = floor
        self._max_floor = max_floor
        self._in_combat = in_combat
        self._enemy_hp_ratio = enemy_hp_ratio
        self._boss = is_boss

    def _get_depth_params(self) -> dict:
        """Get lighting parameters based on current floor depth.

        Returns:
            Dict with ambient_alpha, torch_radius_mult, vignette_intensity
        """
        for (lo, hi), params in _DEPTH_DARKNESS.items():
            if lo <= self._floor <= hi:
                return {"ambient_alpha": params[0], "torch_mult": params[1], "vig_int": params[2]}
        # Fallback for floors beyond defined ranges
        return {"ambient_alpha": 80, "torch_mult": 0.6, "vig_int": 0.55}

    def draw(self, surface: pygame.Surface, time_seconds: float):
        """Render the full lighting overlay onto the given surface.

        Composites all lighting layers onto the screen:
        1. Depth-based ambient darkness
        2. HP-based vignette
        3. Ambient torch light
        4. Status effect glows
        5. Dynamic light sources
        6. Boss eldritch pulsation

        Args:
            surface: The main display surface to render onto
            time_seconds: Total game time for animations
        """
        if not self._enabled:
            return

        self._overlay.fill((0, 0, 0, 0))

        depth = self._get_depth_params()

        # ── Layer 1: Depth-based ambient darkness ──
        if depth["ambient_alpha"] > 0:
            self._draw_ambient_darkness(depth["ambient_alpha"])

        # ── Layer 2: HP-based vignette ──
        self._draw_hp_vignette(time_seconds)

        # ── Layer 3: Ambient torch light sources ──
        for torch in self._ambient_torches:
            radius = int(torch.radius * depth["torch_mult"])
            intensity = torch.get_current_intensity(time_seconds)
            color = torch.get_current_color(time_seconds)
            self._draw_light_source(torch.x, torch.y, radius, color, intensity)

        # ── Layer 4: Status effect glows on screen edges ──
        self._draw_status_edge_glow(time_seconds)

        # ── Layer 5: Dynamic scene light sources ──
        for light in self.lights:
            intensity = light.get_current_intensity(time_seconds)
            color = light.get_current_color(time_seconds)
            self._draw_light_source(light.x, light.y, light.radius, color, intensity)

        # ── Layer 6: Boss eldritch pulsation ──
        if self._in_combat and self._boss:
            self._draw_boss_ambient_pulse(time_seconds)

        # ── Layer 7: Subtle ambient breathing ──
        self._draw_ambient_breathing(time_seconds, depth["ambient_alpha"])

        # Composite the overlay onto the screen
        surface.blit(self._overlay, (0, 0))

    def _draw_ambient_darkness(self, alpha: int):
        """Draw overall ambient darkness based on depth.

        Uses a large elliptical gradient to darken screen edges more than
        the center. The darkness is tinted with a faint sickly purple-black,
        like the air itself is rotting in the depths of the Spiral.
        """
        darkness = surface_pool.acquire(SCREEN_W, SCREEN_H)
        num_rings = 30
        max_rx = SCREEN_W // 2 + 100
        max_ry = SCREEN_H // 2 + 60
        for i in range(num_rings):
            ratio = i / num_rings
            # Quadratic falloff — edges much darker than center
            ring_alpha = int(alpha * ratio * ratio)
            if ring_alpha < 2:
                continue
            rx = int(max_rx * ratio)
            ry = int(max_ry * ratio)
            pygame.draw.ellipse(
                darkness,
                (6, 2, 12, ring_alpha),
                (SCREEN_W // 2 - rx, SCREEN_H // 2 - ry, rx * 2, ry * 2),
            )
        self._overlay.blit(darkness, (0, 0))
        surface_pool.release(darkness)

    def _draw_hp_vignette(self, time_seconds: float):
        """Draw an oppressive vignette that closes in as HP drops.

        This is not a red flash — it is darkness encroaching from the edges,
        narrowing the player's field of vision. A faint pulse of dried-blood
        crimson appears only near death, like the last throb of a failing heart.

        At high HP: no effect.
        At ~50% HP: edges subtly darken, tunnel vision begins.
        At ~25% HP: significant darkness closing in, faint pulse.
        Near death: screen is a narrow slit of vision, slow throbbing.
        """
        if self._hp_ratio >= 0.95:
            return

        # Base vignette intensity: darkness closing in
        # Stronger effect — 0% at full HP, up to 0.85 at 0 HP
        base_intensity = (1.0 - self._hp_ratio) * 0.85

        # Slow, heavy pulse — like a failing heartbeat, not an alarm
        pulse_speed = 0.6 + (1.0 - self._hp_ratio) * 1.5
        pulse = 0.5 + 0.5 * math.sin(time_seconds * pulse_speed)

        # Pulsed intensity: subtle throb
        pulsed = base_intensity * (0.88 + 0.12 * pulse)

        # Faint crimson only near death (below 30% HP) — like dried blood
        crimson_factor = max(0, (0.3 - self._hp_ratio) / 0.3) if self._hp_ratio < 0.3 else 0.0
        r = int(18 * crimson_factor)
        g = 0
        b = int(5 * crimson_factor)

        vignette = surface_pool.acquire(SCREEN_W, SCREEN_H)
        num_rings = 40
        max_rx = SCREEN_W // 2 + 60
        max_ry = SCREEN_H // 2 + 40
        for i in range(num_rings):
            ratio = i / num_rings
            alpha = int(255 * pulsed * ratio * ratio)
            if alpha < 3:
                continue
            rx = int(max_rx * ratio)
            ry = int(max_ry * ratio)
            pygame.draw.ellipse(
                vignette,
                (r, g, b, min(255, alpha)),
                (SCREEN_W // 2 - rx, SCREEN_H // 2 - ry, rx * 2, ry * 2),
            )
        self._overlay.blit(vignette, (0, 0))
        surface_pool.release(vignette)

    def _draw_status_edge_glow(self, time_seconds: float):
        """Draw barely perceptible color whispers at screen edges.

        Lovecraftian horror does not shout — it whispers. These are not
        glowing auras; they are unsettling tints that seep in from the
        periphery, suggesting something is wrong without spelling it out.

        Each status type uses a different edge emphasis — some creep from
        below (poison), some drip from above (blood), some are felt as
        a faint oppressive presence (doom). All are extremely subtle.
        """
        if not self._status_effects:
            return

        for status in self._status_effects:
            color = _STATUS_GLOW_COLORS.get(status)
            if color is None:
                continue

            # Very slow, barely perceptible pulse
            pulse = 0.5 + 0.5 * math.sin(time_seconds * 0.8 + hash(status) % 100)
            alpha = int(4 + 8 * pulse)  # Range: 4-12 (was 25-60)

            glow = surface_pool.acquire(SCREEN_W, SCREEN_H)

            # Different edge emphasis per status type
            if status == "burning":
                # Faint warmth licking at the edges — like distant embers
                for i in range(15):
                    a = int(alpha * (1 - i / 15))
                    pygame.draw.rect(glow, (*color, a), (i, i, SCREEN_W - i * 2, SCREEN_H - i * 2), 1)
            elif status == "poisoned":
                # Putrid green seeping up from the bottom
                for i in range(20):
                    a = int(alpha * (1 - i / 20))
                    pygame.draw.line(glow, (*color, a), (0, SCREEN_H - 1 - i), (SCREEN_W, SCREEN_H - 1 - i))
            elif status == "bleeding":
                # Dried-blood drip from above, barely visible
                for i in range(18):
                    a = int(alpha * (1 - i / 18))
                    pygame.draw.line(glow, (*color, a), (0, i), (SCREEN_W, i))
            elif status == "freezing":
                # Cold tombstone frost at bottom
                for i in range(15):
                    a = int(alpha * (1 - i / 15))
                    pygame.draw.line(glow, (*color, a), (0, SCREEN_H - 1 - i), (SCREEN_W, SCREEN_H - 1 - i))
            elif status == "doom":
                # The void pressing in from all sides — faint and oppressive
                for i in range(20):
                    ratio = i / 20
                    a = int(alpha * 0.8 * ratio * ratio)
                    pygame.draw.rect(glow, (*color, min(255, a)), (i * 3, i * 3, SCREEN_W - i * 6, SCREEN_H - i * 6), 1)
            else:
                # Generic: faint edge whisper
                for i in range(12):
                    a = int(alpha * 0.5 * (1 - i / 12))
                    pygame.draw.rect(glow, (*color, a), (i, i, SCREEN_W - i * 2, SCREEN_H - i * 2), 1)

            self._overlay.blit(glow, (0, 0), special_flags=pygame.BLEND_RGBA_ADD)
            surface_pool.release(glow)

    def _draw_light_source(self, x: int, y: int, radius: int, color: tuple, intensity: float):
        """Draw a single light source as an additive glow.

        Uses a cached radial gradient texture centered at the given position.
        The texture is blitted with additive blending (BLEND_RGBA_ADD) so
        overlapping lights naturally combine to create brighter areas.

        Args:
            x: Center X position
            y: Center Y position
            radius: Light radius in pixels
            color: RGB color of the light
            intensity: Current brightness (0.0 to 1.0)
        """
        if intensity < 0.05 or radius < 10:
            return
        texture = _get_light_texture(radius, color, intensity)
        self._overlay.blit(texture, (x - radius, y - radius), special_flags=pygame.BLEND_RGBA_ADD)

    def _draw_boss_ambient_pulse(self, time_seconds: float):
        """Draw a faint eldritch wrongness during boss fights.

        Not a glowing aura — a subtle distortion of light, as if reality
        itself is sick. The air feels heavy, colours seem slightly off.
        As the boss loses HP, this wrongness intensifies, but it never
        becomes a light show. It is always felt, not seen.

        Uses two overlapping sine waves at different frequencies to create
        an irregular rhythm that mimics something vast breathing.
        """
        # Intensity increases as boss HP drops
        boss_intensity = 0.15 + (1.0 - self._enemy_hp_ratio) * 0.35

        # Slow, irregular rhythm — like a heartbeat that isn't yours
        pulse1 = 0.5 + 0.5 * math.sin(time_seconds * 0.5)
        pulse2 = 0.5 + 0.5 * math.sin(time_seconds * 0.9 + 1.0)
        combined_pulse = (pulse1 * 0.6 + pulse2 * 0.4) * boss_intensity

        if combined_pulse < 0.05:
            return

        # Faint wrongness colour — not purple neon, just slightly off
        r = int(22 * combined_pulse)
        g = int(6 * combined_pulse)
        b = int(30 * combined_pulse)

        pulse_surf = surface_pool.acquire(SCREEN_W, SCREEN_H)
        num_rings = 20
        for i in range(num_rings):
            ratio = i / num_rings
            alpha = int(15 * combined_pulse * ratio * ratio)
            if alpha < 1:
                continue
            rx = int((SCREEN_W // 2 + 100) * ratio)
            ry = int((SCREEN_H // 2 + 60) * ratio)
            pygame.draw.ellipse(
                pulse_surf,
                (r, g, b, alpha),
                (SCREEN_W // 2 - rx, SCREEN_H // 2 - ry, rx * 2, ry * 2),
            )
        self._overlay.blit(pulse_surf, (0, 0), special_flags=pygame.BLEND_RGBA_ADD)
        surface_pool.release(pulse_surf)

    def _draw_ambient_breathing(self, time_seconds: float, depth_alpha: int):
        """Draw an imperceptible light/dark breathing cycle.

        A glacially slow oscillation that the player won't consciously
        register, but will feel as a crawling unease. The darkness
        seems to breathe — and the deeper you go, the faster it breathes.

        Args:
            time_seconds: Total game time for animation
            depth_alpha: Base ambient darkness alpha from depth params
        """
        if depth_alpha < 8:
            return

        # Very slow breathing (14-second cycle at floor 1, 7-second at floor 20)
        breath_period = max(7.0, 14.0 - self._floor * 0.35)
        breath = 0.5 + 0.5 * math.sin(time_seconds * (math.tau / breath_period))

        # Subtle alpha modulation: +/- 12% of depth darkness
        mod = int(depth_alpha * 0.12 * (breath - 0.5))
        if abs(mod) < 2:
            return

        breath_surf = surface_pool.acquire(SCREEN_W, SCREEN_H)
        if mod > 0:
            # Darkness inhales — grows slightly darker
            breath_surf.fill((3, 1, 6, mod))
            self._overlay.blit(breath_surf, (0, 0))
        surface_pool.release(breath_surf)


# ═══════════════════════════════════════════
# CONVENIENCE FUNCTIONS FOR SCREEN INTEGRATION
# ═══════════════════════════════════════════


def create_combat_lighting(
    player_x: int, player_y: int, enemy_x: int, enemy_y: int, player_statuses: list = None
) -> list:
    """Create combat light sources — dim, atmospheric, not a stadium.

    Combat is fought in near-darkness, lit only by the player's fading
    torch and the unsettling presence of whatever lurks opposite.

    Args:
        player_x: Player sprite center X
        player_y: Player sprite center Y
        enemy_x: Enemy sprite center X
        enemy_y: Enemy sprite center Y
        player_statuses: List of active status effect strings (used for edge whispers, not lights)

    Returns:
        List of LightSource objects (kept minimal for atmosphere)
    """
    lights = []

    # Player torch — a single dying flame, barely holding back the dark
    lights.append(LightSource(player_x, player_y + 40, radius=180, color=_TORCH_COLOR, intensity=0.22, flicker=True))

    # Enemy presence — not a light source, but a faint sickly pallor
    # suggesting something unnatural is standing in the darkness
    enemy_color = (75, 65, 85)  # Not purple. Wrong. Just... wrong.
    lights.append(LightSource(enemy_x, enemy_y + 30, radius=140, color=enemy_color, intensity=0.10, pulse_speed=0.8))

    # Center combat area — faintest hint of visibility
    center_x = (player_x + enemy_x) // 2
    center_y = (player_y + enemy_y) // 2
    lights.append(LightSource(center_x, center_y, radius=240, color=(90, 80, 65), intensity=0.05))

    # No status glow LightSources — status effects are conveyed through
    # edge whispers only (drawn by _draw_status_edge_glow).
    # Pulsing coloured circles around the player are too gamey for
    # a Lovecraftian horror atmosphere.

    return lights

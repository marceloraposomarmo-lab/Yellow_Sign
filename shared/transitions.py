"""
THE KING IN YELLOW — Context-Aware Screen Transitions

Pure overlay transitions drawn on top of the live-rendered screen.
Each effect is visually unmistakable and thematically appropriate.

Transition Types:
  FADE_BLACK   — Smooth fade through black (general navigation)
  MENU_REVEAL  — Gold frame expands like a scroll unrolling (menus/overlays)
  COMBAT_DIVE  — Bright flash → white burst → reveal (entering combat)
"""

from enum import Enum
import math
import pygame

from shared.constants import C, SCREEN_W, SCREEN_H


class TransitionType(str, Enum):
    FADE_BLACK = "fade_black"
    MENU_REVEAL = "menu_reveal"
    COMBAT_DIVE = "combat_dive"


def get_transition_for(source, target) -> TransitionType:
    """Determine the appropriate transition type for a screen change."""
    from screens.screen_enum import ScreenName
    tgt = getattr(target, "value", target)

    if tgt == ScreenName.COMBAT.value:
        return TransitionType.COMBAT_DIVE
    if tgt in (ScreenName.INVENTORY.value, ScreenName.SHOP.value,
               ScreenName.SAVE.value, ScreenName.LOAD.value,
               ScreenName.STATS.value):
        return TransitionType.MENU_REVEAL
    return TransitionType.FADE_BLACK


def get_transition_durations(transition_type: TransitionType):
    """Return (out_duration, in_duration) in seconds."""
    return {
        TransitionType.FADE_BLACK: (0.25, 0.25),
        TransitionType.MENU_REVEAL: (0.15, 0.35),
        TransitionType.COMBAT_DIVE: (0.3, 0.3),
    }.get(transition_type, (0.25, 0.25))


def render_transition(surface, transition_type, phase, progress, time_seconds=0.0):
    """Render a transition overlay on the live screen."""
    dispatch = {
        TransitionType.FADE_BLACK: _render_fade_black,
        TransitionType.MENU_REVEAL: _render_menu_reveal,
        TransitionType.COMBAT_DIVE: _render_combat_dive,
    }
    renderer = dispatch.get(transition_type, _render_fade_black)
    renderer(surface, phase, progress, time_seconds)


# ═══════════════════════════════════════════
# FADE BLACK
# ═══════════════════════════════════════════

def _render_fade_black(surface, phase, progress, t):
    sw, sh = surface.get_size()
    overlay = pygame.Surface((sw, sh), pygame.SRCALPHA)
    if phase == "out":
        alpha = int(255 * _ease_in_out_quad(progress))
    else:
        alpha = int(255 * (1.0 - _ease_in_out_quad(progress)))
    overlay.fill((0, 0, 0, alpha))
    surface.blit(overlay, (0, 0))


# ═══════════════════════════════════════════
# MENU REVEAL — Gold frame expands like a scroll
# ═══════════════════════════════════════════

def _render_menu_reveal(surface, phase, progress, t):
    sw, sh = surface.get_size()
    overlay = pygame.Surface((sw, sh), pygame.SRCALPHA)

    if phase == "out":
        # Screen fades to dark while a gold frame expands from center
        eased = _ease_in_quad(progress)

        # Dark overlay
        overlay.fill((8, 4, 16, int(220 * eased)))
        surface.blit(overlay, (0, 0))

        # Expanding gold frame — grows from center
        frame_progress = _ease_out_quad(progress)
        margin = int(sw * 0.45 * (1.0 - frame_progress))
        bx, by = margin, margin
        bw, bh = sw - margin * 2, sh - margin * 2

        if bw > 30 and bh > 30:
            gold_alpha = int(255 * min(1.0, eased * 2))
            gold = (218, 165, 32, gold_alpha)
            dim = (139, 101, 20, int(gold_alpha * 0.6))

            pygame.draw.rect(surface, gold, (bx, by, bw, bh), 3, border_radius=4)
            pygame.draw.rect(surface, dim, (bx + 5, by + 5, bw - 10, bh - 10), 1, border_radius=3)

            for cx, cy in [(bx + 12, by + 12), (bx + bw - 12, by + 12),
                           (bx + 12, by + bh - 12), (bx + bw - 12, by + bh - 12)]:
                pygame.draw.polygon(surface, gold, [
                    (cx, cy - 5), (cx + 5, cy), (cx, cy + 5), (cx - 5, cy)
                ])

    else:
        # New screen is live. Frame is at full size, then fades away
        eased = _ease_out_cubic(progress)

        # Full-screen gold frame that fades out
        frame_alpha = int(255 * (1.0 - eased))
        if frame_alpha > 5:
            gold = (218, 165, 32, frame_alpha)
            dim = (139, 101, 20, int(frame_alpha * 0.5))

            pygame.draw.rect(surface, gold, (6, 6, sw - 12, sh - 12), 3, border_radius=4)
            pygame.draw.rect(surface, dim, (12, 12, sw - 24, sh - 24), 1, border_radius=3)

            for cx, cy in [(18, 18), (sw - 18, 18), (18, sh - 18), (sw - 18, sh - 18)]:
                pygame.draw.polygon(surface, gold, [
                    (cx, cy - 5), (cx + 5, cy), (cx, cy + 5), (cx - 5, cy)
                ])

        # Dark edges that fade away
        edge_alpha = int(160 * (1.0 - eased))
        if edge_alpha > 3:
            edge_overlay = pygame.Surface((sw, sh), pygame.SRCALPHA)
            for i in range(25):
                a = int(edge_alpha * (1.0 - i / 25))
                if a > 2:
                    pygame.draw.line(edge_overlay, (0, 0, 0, a), (0, i), (sw, i))
                    pygame.draw.line(edge_overlay, (0, 0, 0, a), (0, sh - 1 - i), (sw, sh - 1 - i))
            for i in range(15):
                a = int(edge_alpha * 0.7 * (1.0 - i / 15))
                if a > 2:
                    pygame.draw.line(edge_overlay, (0, 0, 0, a), (i, 0), (i, sh))
                    pygame.draw.line(edge_overlay, (0, 0, 0, a), (sw - 1 - i, 0), (sw - 1 - i, sh))
            surface.blit(edge_overlay, (0, 0))


# ═══════════════════════════════════════════
# COMBAT DIVE — Immersive flash-and-reveal
# ═══════════════════════════════════════════

def _render_combat_dive(surface, phase, progress, t):
    sw, sh = surface.get_size()
    cx, cy = sw // 2, sh // 2

    if phase == "out":
        eased = _ease_in_quad(progress)
        overlay = pygame.Surface((sw, sh), pygame.SRCALPHA)

        # Pulsing dark vignette from edges — creates tension
        pulse = 0.7 + 0.3 * math.sin(t * 12.0)
        vig_max = int(255 * eased * pulse)
        for i in range(40):
            a = int(vig_max * (i / 40) * 0.9)
            if a > 2:
                c = (12, 6, 20, a)
                pygame.draw.line(overlay, c, (0, i), (sw, i))
                pygame.draw.line(overlay, c, (0, sh - 1 - i), (sw, sh - 1 - i))
                pygame.draw.line(overlay, c, (i, 0), (i, sh))
                pygame.draw.line(overlay, c, (sw - 1 - i, 0), (sw - 1 - i, sh))
        surface.blit(overlay, (0, 0))

        # Closing dark circle — screen gets consumed from outside in
        max_dim = max(sw, sh)
        radius = int(max_dim * (1.1 - eased * 1.15))
        if radius > 5:
            circle = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
            inner_a = int(250 * eased)
            pygame.draw.circle(circle, (10, 5, 18, inner_a), (radius, radius), radius)
            surface.blit(circle, (cx - radius, cy - radius))

        # Gold ring at the closing edge — pulses bright at peak
        ring_a = int(160 * math.sin(eased * math.pi))
        if ring_a > 8 and radius > 15:
            ring_overlay = pygame.Surface((sw, sh), pygame.SRCALPHA)
            pygame.draw.circle(ring_overlay, (218, 165, 32, ring_a), (cx, cy), max(1, radius), 3)
            surface.blit(ring_overlay, (0, 0))

    else:
        # IN: Bright flash from center that expands and fades — the "dive" landing
        eased = _ease_in_quad(progress)  # starts fast, slows down

        # White flash burst — strongest at start, fading as screen appears
        flash_alpha = int(220 * (1.0 - eased))
        if flash_alpha > 3:
            flash = pygame.Surface((sw, sh), pygame.SRCALPHA)
            flash.fill((220, 200, 255, flash_alpha))

            # Cut a growing transparent hole in the center
            hole_radius = int(max(sw, sh) * 0.6 * eased)
            if hole_radius > 10:
                pygame.draw.circle(flash, (0, 0, 0, 0), (cx, cy), hole_radius)
                # Feathered edge — concentric rings of decreasing alpha
                for r in range(hole_radius + 30, hole_radius, -3):
                    edge_a = int(flash_alpha * (1.0 - (r - hole_radius) / 30))
                    if edge_a > 2:
                        pygame.draw.circle(flash, (220, 200, 255, edge_a), (cx, cy), r)

            surface.blit(flash, (0, 0))

        # Fading dark vignette at edges — screen settles
        vig_alpha = int(120 * (1.0 - eased))
        if vig_alpha > 3:
            vig = pygame.Surface((sw, sh), pygame.SRCALPHA)
            for i in range(20):
                a = int(vig_alpha * (1.0 - i / 20))
                if a > 2:
                    pygame.draw.line(vig, (10, 5, 18, a), (0, i), (sw, i))
                    pygame.draw.line(vig, (10, 5, 18, a), (0, sh - 1 - i), (sw, sh - 1 - i))
            surface.blit(vig, (0, 0))


# ═══════════════════════════════════════════
# EASING
# ═══════════════════════════════════════════

def _ease_in_out_quad(t):
    if t < 0.5:
        return 2 * t * t
    return 1 - pow(-2 * t + 2, 2) / 2


def _ease_out_quad(t):
    return 1 - (1 - t) * (1 - t)


def _ease_in_quad(t):
    return t * t


def _ease_out_cubic(t):
    return 1 - pow(1 - t, 3)

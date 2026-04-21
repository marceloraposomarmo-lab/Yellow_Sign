"""
THE KING IN YELLOW — Rendering Functions
Drawing helpers, obsidian texture generation, glow text, HUD.
"""

import math
import random
import pygame
from shared.constants import C, SCREEN_W, SCREEN_H, CLASS_COLORS
from shared.surface_pool import surface_pool, render_cache
from data import CLASS_ICONS
from data.buff_debuff_data import get_effect_info

# ═══════════════════════════════════════════
# EASING FUNCTIONS FOR SMOOTH ANIMATIONS
# ═══════════════════════════════════════════


def ease_out_quad(t):
    """Quadratic easing out - starts fast, slows down smoothly."""
    return 1 - (1 - t) * (1 - t)


def ease_in_quad(t):
    """Quadratic easing in - starts slow, accelerates."""
    return t * t


def ease_in_out_quad(t):
    """Quadratic easing in and out - smooth acceleration and deceleration."""
    if t < 0.5:
        return 2 * t * t
    return 1 - pow(-2 * t + 2, 2) / 2


def ease_out_cubic(t):
    """Cubic easing out - natural deceleration, good for UI settling."""
    return 1 - pow(1 - t, 3)


def ease_in_cubic(t):
    """Cubic easing in - smooth acceleration."""
    return t * t * t


def ease_in_out_cubic(t):
    """Cubic easing in and out - very smooth motion."""
    if t < 0.5:
        return 4 * t * t * t
    return 1 - pow(-2 * t + 2, 3) / 2


def ease_out_bounce(t):
    """Bounce easing out - playful bounce effect."""
    n1 = 7.5625
    d1 = 2.75
    if t < 1 / d1:
        return n1 * t * t
    elif t < 2 / d1:
        return n1 * (t - 1.5 / d1) * (t - 1.5 / d1) + 0.75
    elif t < 2.5 / d1:
        return n1 * (t - 2.25 / d1) * (t - 2.25 / d1) + 0.9375
    return n1 * (t - 2.625 / d1) * (t - 2.625 / d1) + 0.984375


def lerp(start, end, t):
    """Linear interpolation between two values."""
    return start + (end - start) * t


def animate_value(current, target, dt, speed=5.0):
    """Smoothly interpolate a value toward a target using cubic easing.

    Args:
        current: Current value
        target: Target value
        dt: Delta time in seconds
        speed: Animation speed (higher = faster)

    Returns:
        New interpolated value
    """
    diff = abs(target - current)
    if diff < 0.1:
        return target

    # Calculate interpolation factor based on dt and speed
    t = min(1.0, speed * dt)
    # Use ease_out_cubic for natural deceleration as we approach target
    eased_t = ease_out_cubic(t)
    return lerp(current, target, eased_t)


# ═══════════════════════════════════════════
# DRAWING HELPERS
# ═══════════════════════════════════════════


def draw_text(surface, text, font, color, x, y, align="left"):
    """Draw text with alignment options."""
    rendered = font.render(text, True, color)
    rect = rendered.get_rect()
    if align == "center":
        rect.centerx = x
        rect.top = y
    elif align == "right":
        rect.right = x
        rect.top = y
    else:
        rect.topleft = (x, y)
    surface.blit(rendered, rect)
    return rect


def draw_text_wrapped(surface, text, font, color, x, y, max_width, line_height=None):
    """Draw text with word wrapping. Returns total height drawn."""
    if line_height is None:
        line_height = font.get_linesize()
    words = text.split(" ")
    lines = []
    current_line = ""
    for word in words:
        test = current_line + (" " if current_line else "") + word
        if font.size(test)[0] > max_width:
            if current_line:
                lines.append(current_line)
            current_line = word
        else:
            current_line = test
    if current_line:
        lines.append(current_line)

    for i, line_text in enumerate(lines):
        draw_text(surface, line_text, font, color, x, y + i * line_height)
    return len(lines) * line_height


def fit_text(font, text, max_pixel_width, suffix="…"):
    """Truncate text to fit within max_pixel_width pixels."""
    if font.size(text)[0] <= max_pixel_width:
        return text
    while len(text) > 0 and font.size(text + suffix)[0] > max_pixel_width:
        text = text[:-1]
    return text + suffix if text else suffix


def draw_text_fitted(surface, text, font, color, x, y, max_width, align="left"):
    """Draw text, auto-truncating to fit max_width pixels."""
    fitted = fit_text(font, text, max_width)
    draw_text(surface, fitted, font, color, x, y, align)


def draw_bar(
    surface,
    x,
    y,
    w,
    h,
    current,
    maximum,
    fg_color,
    bg_color=C.SHADOW,
    border_color=C.ASH,
    animate=False,
    prev_value=None,
    dt=0.0,
    animation_speed=8.0,
):
    """Draw a horizontal bar (HP, XP, etc.).

    Args:
        surface: Target pygame surface
        x, y: Position of the bar
        w, h: Width and height of the bar
        current: Current value
        maximum: Maximum value
        fg_color: Fill color
        bg_color: Background color (default: C.SHADOW)
        border_color: Border color (default: C.ASH)
        animate: If True, smoothly animate from prev_value to current
        prev_value: Previous value for animation (used when animate=True)
        dt: Delta time in seconds (used for animation)
        animation_speed: Speed of the bar animation (higher = faster)

    Returns:
        If animate=True, returns tuple (display_value, new_prev_value) for next frame
    """
    pygame.draw.rect(surface, border_color, (x - 1, y - 1, w + 2, h + 2), border_radius=3)
    pygame.draw.rect(surface, bg_color, (x, y, w, h), border_radius=2)

    if maximum > 0:
        if animate and prev_value is not None and dt > 0:
            # Smoothly interpolate toward target value using easing
            display_value = animate_value(prev_value, current, dt, animation_speed)
            fill_w = max(0, int(w * min(1, display_value / maximum)))
            if fill_w > 0:
                pygame.draw.rect(surface, fg_color, (x, y, fill_w, h), border_radius=2)
            # Return display value and current as the new prev_value for next frame
            return display_value, current
        else:
            fill_w = max(0, int(w * min(1, current / maximum)))
            if fill_w > 0:
                pygame.draw.rect(surface, fg_color, (x, y, fill_w, h), border_radius=2)

    return current, current  # Return unchanged for non-animated case


def draw_panel(surface, x, y, w, h, bg_color=None, border_color=C.GOLD_DIM, border_width=2):
    """Draw an obsidian panel with border."""
    texture = generate_parchment_texture(w, h)
    texture.set_alpha(235)
    surface.blit(texture, (x, y))
    pygame.draw.rect(surface, border_color, (x, y, w, h), border_width, border_radius=4)


def draw_ornate_panel(surface, x, y, w, h, title=None, title_color=None, title_font=None):
    """Draw an obsidian-textured panel with ornate gold frame."""
    draw_parchment_panel(surface, x, y, w, h, title=title, title_font=title_font)


def draw_ornate_button(
    surface, rect, text, font, hover=False, color=C.INK, disabled=False, pulse_speed=4.0, shimmer_speed=1.5
):
    """Draw a button styled with obsidian and gold trim borders.

    Args:
        surface: Target pygame surface
        rect: Button rectangle (pygame.Rect)
        text: Button label text
        font: Font to render text
        hover: Whether mouse is hovering over button
        color: Border/text color
        disabled: If True, use muted colors
        pulse_speed: Speed of the pulsing glow effect (higher = faster)
        shimmer_speed: Speed of the shimmer animation (higher = faster)
    """
    btn_tex = generate_parchment_texture(rect.w, rect.h)
    btn_tex.set_alpha(240 if not hover else 255)
    surface.blit(btn_tex, (rect.x, rect.y))

    border_color = color if not disabled else C.ASH
    text_color = color if not disabled else C.ASH

    pygame.draw.rect(surface, border_color, rect, 2, border_radius=4)
    inner_rect = pygame.Rect(rect.x + 3, rect.y + 3, rect.w - 6, rect.h - 6)
    dim_border = tuple(max(0, c - 60) for c in border_color)
    pygame.draw.rect(surface, dim_border, inner_rect, 1, border_radius=3)
    draw_text_with_glow(
        surface, text, font, text_color, rect.centerx, rect.centery - font.get_height() // 2, align="center"
    )
    # Animated hover effect with eased transitions
    if hover:
        t = pygame.time.get_ticks() / 1000.0
        # Use sine wave for smooth pulsing
        pulse_factor = 0.5 + 0.5 * math.sin(t * pulse_speed)
        # Apply easing for smoother alpha transitions
        eased_pulse = ease_in_out_quad(pulse_factor)
        pulse_alpha = int(20 + 50 * eased_pulse)

        # Use pooled surface instead of allocating each frame
        glow = surface_pool.acquire(rect.w + 12, rect.h + 12)
        glow.fill((120, 80, 200, pulse_alpha))
        surface.blit(glow, (rect.x - 6, rect.y - 6))

        border_pulse = int(eased_pulse)
        if border_pulse:
            gold_glow = surface_pool.acquire(rect.w + 6, rect.h + 6)
            gold_glow.fill((212, 160, 23, 35))
            surface.blit(gold_glow, (rect.x - 3, rect.y - 3))
            surface_pool.release(gold_glow)

        # Shimmer effect with smooth phase calculation
        shimmer_phase = (t * shimmer_speed) % 3.0
        if shimmer_phase < 1.0:
            # Use cubic easing for smoother shimmer movement
            shimmer_t = ease_out_cubic(shimmer_phase)
            shimmer_x = rect.x - 20 + int((rect.w + 40) * shimmer_t)
            shimmer = surface_pool.acquire(20, rect.h + 4)
            shimmer.fill((255, 220, 100, 25))
            surface.blit(shimmer, (shimmer_x, rect.y - 2))
            surface_pool.release(shimmer)

        surface_pool.release(glow)


def draw_gold_divider(surface, x, y, width):
    """Draw a decorative gold divider line with end caps."""
    mid = width // 2
    pygame.draw.line(surface, C.GOLD_DIM, (x, y), (x + mid - 15, y), 1)
    pygame.draw.line(surface, C.GOLD_DIM, (x + mid + 15, y), (x + width, y), 1)
    pygame.draw.polygon(surface, C.GOLD_TRIM, [(x + mid, y - 4), (x + mid + 4, y), (x + mid, y + 4), (x + mid - 4, y)])
    for ex in [x, x + width]:
        pygame.draw.circle(surface, C.GOLD_DIM, (ex, y), 2)


def hp_color(current, maximum):
    if maximum <= 0:
        return C.HP_RED
    pct = current / maximum
    if pct > 0.6:
        return C.HP_GREEN
    elif pct > 0.3:
        return C.HP_YELLOW
    else:
        return C.HP_RED


def mad_color(madness):
    if madness < 30:
        return C.MIST
    elif madness < 60:
        return C.HP_YELLOW
    else:
        return C.HP_RED


def rarity_color(rarity):
    return {1: C.ASH, 2: C.MIST, 3: C.FROST, 4: C.CRIMSON}.get(rarity, C.ASH)


# ═══════════════════════════════════════
# BUFF / DEBUFF ICON SYSTEM
# ═══════════════════════════════════════

_ICON_FONT_CACHE = {}  # size → font


def _get_icon_font(size):
    """Get a small font for icon letters, cached."""
    if size not in _ICON_FONT_CACHE:
        _ICON_FONT_CACHE[size] = pygame.font.Font(None, size)
    return _ICON_FONT_CACHE[size]


def draw_status_icon(surface, x, y, effect_type, duration=0, size=22):
    """Draw a single status effect icon as a colored circle with letter abbreviation.
    Returns the pygame.Rect of the icon (for hover detection)."""
    info = get_effect_info(effect_type)
    letter = info["letter"]
    color = info["color"]
    radius = size // 2
    cx, cy = x + radius, y + radius

    # Background circle — darker version of the effect color
    bg_color = tuple(max(0, c - 120) for c in color)
    pygame.draw.circle(surface, bg_color, (cx, cy), radius)
    pygame.draw.circle(surface, color, (cx, cy), radius, 2)

    # Cached highlight circle — same (size, color) always produces identical output
    highlight_key = ("status_hl", size, color)
    highlight = render_cache.get(highlight_key)
    if highlight is None:
        highlight = pygame.Surface((size, size), pygame.SRCALPHA)
        for r in range(radius - 1, 0, -1):
            alpha = int(20 * (1 - r / radius))
            pygame.draw.circle(highlight, (*color, alpha), (radius, radius), r)
        render_cache.put(highlight_key, highlight)
    surface.blit(highlight, (x, y))

    # Letter text
    font_size = max(11, int(size * 0.6))
    font = _get_icon_font(font_size)
    text_surf = font.render(letter, True, color)
    text_rect = text_surf.get_rect(center=(cx, cy - 1))
    surface.blit(text_surf, text_rect)

    # Duration number (bottom-right corner)
    if duration > 0:
        dur_font = _get_icon_font(max(9, int(size * 0.45)))
        dur_text = str(duration)
        dur_surf = dur_font.render(dur_text, True, (255, 255, 200))
        dur_rect = dur_surf.get_rect(bottomright=(x + size - 1, y + size))
        # Dark background for readability — use pooled surface
        bg_dur = surface_pool.acquire(dur_rect.w + 2, dur_rect.h + 1)
        bg_dur.fill((0, 0, 0, 160))
        surface.blit(bg_dur, (dur_rect.x - 1, dur_rect.y - 1))
        surface_pool.release(bg_dur)
        surface.blit(dur_surf, dur_rect)

    return pygame.Rect(x, y, size, size)


def draw_status_icons_row(surface, x, y, statuses, buffs, barrier=0, size=22, gap=5):
    """Draw a row of status effect icons. Returns list of (Rect, effect_type) for hover detection.

    Args:
        statuses: list of StatusEffect objects (debuffs on enemy/player)
        buffs: dict of {buff_type: duration} (player buffs)
        barrier: barrier stack count
        size: icon diameter in pixels
        gap: pixels between icons
    """
    icon_rects = []
    cx = x

    # Draw debuffs first (from statuses list)
    for st in statuses:
        rect = draw_status_icon(surface, cx, y, st.type, st.duration, size)
        icon_rects.append((rect, st.type))
        cx += size + gap

    # Draw stun if applicable (passed as a special case — check caller)
    # Player buffs (from buffs dict)
    for buff_type, duration in sorted(buffs.items()):
        if duration <= 0:
            continue
        # Skip internal/hidden buffs that shouldn't show icons
        if buff_type in ("darkRegenBuff",):
            continue
        rect = draw_status_icon(surface, cx, y, buff_type, duration, size)
        icon_rects.append((rect, buff_type))
        cx += size + gap

    # Barrier stacks
    if barrier > 0:
        rect = draw_status_icon(surface, cx, y, "barrier", barrier, size)
        icon_rects.append((rect, "barrier"))
        cx += size + gap

    return icon_rects


def draw_status_tooltip(surface, effect_type, icon_rect, font=None):
    """Draw a tooltip above/below a status icon showing the effect description.

    Args:
        surface: target surface
        effect_type: the buff/debuff type string
        icon_rect: pygame.Rect of the hovered icon
        font: font to use (defaults to tiny)
    """
    from shared.rendering import draw_text_with_glow, draw_parchment_panel

    info = get_effect_info(effect_type)

    if font is None:
        font = _get_icon_font(14)

    padding = 8
    max_w = 320
    name_font = _get_icon_font(15)

    # Build tooltip lines
    lines = []

    # Name line
    name_text = info["name"]
    if info.get("category") == "debuff":
        name_text += " (Debuff)"
    lines.append(("name", name_text))

    # Description (word-wrap)
    desc = info["desc"]
    desc_words = desc.split()
    line = ""
    for w in desc_words:
        test = f"{line} {w}".strip()
        if font.size(test)[0] > max_w - padding * 2:
            lines.append(("desc", line))
            line = w
        else:
            line = test
    if line:
        lines.append(("desc", line))

    line_h = font.get_height() + 2
    name_line_h = name_font.get_height() + 4
    tip_w = max_w
    tip_h = padding * 2 + name_line_h + (len(lines) - 1) * line_h

    # Position: centered above icon
    tip_x = icon_rect.centerx - tip_w // 2
    tip_y = icon_rect.y - tip_h - 6

    # Clamp to screen
    if tip_y < 5:
        tip_y = icon_rect.bottom + 6
    if tip_x < 5:
        tip_x = 5
    if tip_x + tip_w > SCREEN_W - 5:
        tip_x = SCREEN_W - tip_w - 5

    # Background — use pooled surface instead of allocating each frame
    bg = surface_pool.acquire(tip_w, tip_h)
    bg.fill((10, 8, 20, 235))
    surface.blit(bg, (tip_x, tip_y))
    surface_pool.release(bg)
    pygame.draw.rect(surface, info["color"], (tip_x, tip_y, tip_w, tip_h), 1, border_radius=3)
    pygame.draw.rect(surface, C.PARCHMENT_EDGE, (tip_x + 1, tip_y + 1, tip_w - 2, tip_h - 2), 1, border_radius=2)

    # Draw lines
    y_off = padding
    for kind, text in lines:
        if kind == "name":
            draw_text_with_glow(surface, text, name_font, info["color"], tip_x + padding, tip_y + y_off)
            y_off += name_line_h
        else:
            draw_text_with_glow(surface, text, font, C.INK, tip_x + padding, tip_y + y_off)
            y_off += line_h


# ═══════════════════════════════════════════
# OBSIDIAN TEXTURE — TILE-BASED CACHING
# ═══════════════════════════════════════════

_OBSIDIAN_TILE_SIZE = 256
_obsidian_master_tile = None


def _draw_yellow_sign(surf, cx, cy, size, alpha=18):
    s = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
    color = (200, 160, 40, alpha)
    points = []
    for a in range(0, 360 * 3, 5):
        rad = math.radians(a)
        r = (a / (360 * 3)) * size * 0.8
        px = size + int(r * math.cos(rad))
        py = size + int(r * math.sin(rad))
        points.append((px, py))
    if len(points) > 1:
        pygame.draw.lines(s, color, False, points, 1)
    bar = size // 3
    pygame.draw.line(s, color, (size - bar, size), (size + bar, size), 1)
    pygame.draw.line(s, color, (size, size - bar), (size, size + bar), 1)
    surf.blit(s, (cx - size, cy - size))


def _draw_elder_sign(surf, cx, cy, size, alpha=15):
    s = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
    color = (140, 100, 200, alpha)
    pygame.draw.circle(s, color, (size, size), size - 2, 1)
    pts = []
    for i in range(10):
        rad = math.radians(i * 36 - 90)
        r = (size * 0.8) if i % 2 == 0 else (size * 0.35)
        pts.append((size + int(r * math.cos(rad)), size + int(r * math.sin(rad))))
    pygame.draw.polygon(s, color, pts, 1)
    surf.blit(s, (cx - size, cy - size))


def _draw_alchemical_circle(surf, cx, cy, size, alpha=12):
    s = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
    color = (160, 120, 220, alpha)
    pygame.draw.circle(s, color, (size, size), size - 2, 1)
    pygame.draw.circle(s, color, (size, size), size - 6, 1)
    pts = []
    for i in range(3):
        rad = math.radians(i * 120 - 90)
        pts.append((size + int((size - 4) * math.cos(rad)), size + int((size - 4) * math.sin(rad))))
    pygame.draw.polygon(s, color, pts, 1)
    for angle in [0, 90, 180, 270]:
        rad = math.radians(angle)
        dx = size + int((size - 2) * math.cos(rad))
        dy = size + int((size - 2) * math.sin(rad))
        pygame.draw.circle(s, color, (dx, dy), 2)
    surf.blit(s, (cx - size, cy - size))


def _draw_crack(surf, x, y, length, alpha=25):
    color = (60, 40, 90, alpha)
    points = [(x, y)]
    cx, cy = x, y
    angle = random.uniform(0, 360)
    for _ in range(random.randint(3, 7)):
        angle += random.uniform(-40, 40)
        dist = random.randint(length // 3, length)
        rad = math.radians(angle)
        cx += int(dist * math.cos(rad))
        cy += int(dist * math.sin(rad))
        points.append((cx, cy))
    if len(points) > 1:
        pygame.draw.lines(surf, color, False, points, 1)


def _generate_obsidian_tile():
    global _obsidian_master_tile
    if _obsidian_master_tile is not None:
        return _obsidian_master_tile

    size = _OBSIDIAN_TILE_SIZE
    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    base = C.OBSIDIAN

    surf.fill((*base, 250))

    # Fine crystalline grain noise
    for _ in range(size * size // 3):
        px = random.randint(0, size - 1)
        py = random.randint(0, size - 1)
        v = random.randint(-12, 12)
        r = max(0, min(255, base[0] + v))
        g = max(0, min(255, base[1] + v))
        b = max(0, min(255, base[2] + v))
        surf.set_at((px, py), (r, g, b, 255))

    # Purple/indigo color variation patches
    for _ in range(max(4, size * size // 3000)):
        cx = random.randint(0, size)
        cy = random.randint(0, size)
        radius = random.randint(15, 40)
        spot = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
        for ring in range(radius, 0, -1):
            alpha = int(12 * (1 - ring / radius))
            purple_tint = (random.randint(20, 45), random.randint(10, 30), random.randint(40, 70))
            pygame.draw.circle(spot, (*purple_tint, alpha), (radius, radius), ring)
        surf.blit(spot, (cx - radius, cy - radius))

    # Bright crystalline sparkle points
    for _ in range(max(5, size * size // 2000)):
        sx = random.randint(0, size - 1)
        sy = random.randint(0, size - 1)
        sparkle = random.choice(
            [
                (200, 160, 50, random.randint(15, 35)),
                (140, 100, 190, random.randint(10, 25)),
                (180, 170, 160, random.randint(8, 18)),
            ]
        )
        sz = random.randint(1, 3)
        pygame.draw.circle(surf, sparkle, (sx, sy), sz)

    # Cracks
    for _ in range(random.randint(2, 4)):
        edge = random.choice(["top", "bottom", "left", "right"])
        if edge == "top":
            _draw_crack(surf, random.randint(0, size), 0, random.randint(30, 80))
        elif edge == "bottom":
            _draw_crack(surf, random.randint(0, size), size - 1, random.randint(30, 80))
        elif edge == "left":
            _draw_crack(surf, 0, random.randint(0, size), random.randint(30, 80))
        else:
            _draw_crack(surf, size - 1, random.randint(0, size), random.randint(30, 80))

    # Watermarks baked into tile
    if size > 200:
        _draw_yellow_sign(surf, size // 3, size // 3, 20, alpha=14)
        _draw_elder_sign(surf, 2 * size // 3, 2 * size // 3, 15, alpha=10)

    _obsidian_master_tile = surf
    return surf


# Pre-rendered HUD background — created once, reused every frame
_HUD_BG_KEY = ("hud_bg", SCREEN_W, 120)


def generate_parchment_texture(width, height):
    """Generate a panel texture by tiling the master obsidian tile, then adding per-panel effects.

    The expensive base (tiled obsidian + edge glow + vignette) is cached by
    (width, height).  Per-frame eldritch symbols are drawn on a copy so
    they shimmer naturally instead of being frozen in place.

    Callers that modify the returned surface with ``set_alpha()`` are safe:
    the base cache is never mutated, and the returned copy is a fresh surface.
    """
    # ── Base texture (cached): tile + glow + vignette ──
    base_key = ("parchment_base", width, height)
    base = render_cache.get(base_key)
    if base is None:
        tile = _generate_obsidian_tile()
        tile_w, tile_h = tile.get_size()

        base = pygame.Surface((width, height), pygame.SRCALPHA)

        for ty in range(0, height, tile_h):
            for tx in range(0, width, tile_w):
                base.blit(tile, (tx, ty))

        # Edge glow
        glow = pygame.Surface((width, height), pygame.SRCALPHA)
        for i in range(25):
            alpha = int(35 * (1 - i / 25))
            edge_c = C.OBSIDIAN_GLOW
            pygame.draw.line(glow, (*edge_c, alpha), (0, i), (width, i))
            pygame.draw.line(glow, (*edge_c, alpha), (0, height - 1 - i), (width, height - 1 - i))
        for i in range(15):
            alpha = int(25 * (1 - i / 15))
            edge_c = C.OBSIDIAN_GLOW
            pygame.draw.line(glow, (*edge_c, alpha), (i, 0), (i, height))
            pygame.draw.line(glow, (*edge_c, alpha), (width - 1 - i, 0), (width - 1 - i, height))
        base.blit(glow, (0, 0))

        # Dark vignette
        vig = pygame.Surface((width, height), pygame.SRCALPHA)
        for i in range(15):
            alpha = int(50 * (1 - i / 15))
            pygame.draw.line(vig, (0, 0, 0, alpha), (0, i), (width, i))
            pygame.draw.line(vig, (0, 0, 0, alpha), (0, height - 1 - i), (width, height - 1 - i))
        base.blit(vig, (0, 0))

        render_cache.put(base_key, base)

    # ── Per-frame copy with fresh random symbols ──
    surf = base.copy()

    # Per-panel eldritch symbols (random positions each frame for subtle shimmer)
    if width > 200 and height > 150:
        _draw_yellow_sign(
            surf,
            random.randint(width // 4, 3 * width // 4),
            random.randint(height // 4, 3 * height // 4),
            random.randint(25, 45),
            alpha=20,
        )
        _draw_elder_sign(
            surf, random.randint(30, width - 30), random.randint(30, height - 30), random.randint(18, 30), alpha=16
        )
        if width > 400:
            _draw_alchemical_circle(
                surf, random.randint(50, width - 50), random.randint(50, height - 50), random.randint(20, 35), alpha=14
            )
        for _ in range(random.randint(2, 4)):
            sx = random.randint(15, width - 15)
            sy = random.randint(15, height - 15)
            if random.random() < 0.5:
                _draw_elder_sign(surf, sx, sy, random.randint(8, 14), alpha=10)
            else:
                _draw_alchemical_circle(surf, sx, sy, random.randint(10, 16), alpha=8)

    return surf


def draw_parchment_panel(surface, x, y, w, h, title=None, title_font=None, animated_border=False, pulse_speed=1.0):
    """Draw an obsidian-textured panel with ornate gold frame borders.

    Args:
        surface: Target pygame surface
        x, y: Position of the panel
        w, h: Width and height of the panel
        title: Optional title text for the panel
        title_font: Font for the title
        animated_border: If True, animate the border glow with a subtle pulse
        pulse_speed: Speed of the border pulse animation (higher = faster)
    """
    texture = generate_parchment_texture(w, h)
    surface.blit(texture, (x, y))

    # Frame with optional animated glow
    if animated_border:
        t = pygame.time.get_ticks() / 1000.0
        pulse = 0.5 + 0.5 * math.sin(t * pulse_speed)
        eased_pulse = ease_in_out_quad(pulse)
        glow_alpha = int(40 + 30 * eased_pulse)

        # Subtle outer glow — use pooled surface
        glow_surf = surface_pool.acquire(w + 10, h + 10)
        for i in range(5):
            alpha = int((5 - i) * glow_alpha * 0.3)
            pygame.draw.rect(glow_surf, (*C.GOLD_TRIM[:3], alpha), (5 - i, 5 - i, w + i * 2, h + i * 2), 1)
        surface.blit(glow_surf, (x - 5, y - 5))
        surface_pool.release(glow_surf)

    pygame.draw.rect(surface, C.OBSIDIAN_EDGE, (x, y, w, h), 3, border_radius=4)
    pygame.draw.rect(surface, C.GOLD_TRIM, (x + 4, y + 4, w - 8, h - 8), 2, border_radius=3)
    pygame.draw.rect(surface, C.GOLD_DIM, (x + 7, y + 7, w - 14, h - 14), 1, border_radius=2)

    # Corner ornaments
    corners = [(x + 11, y + 11), (x + w - 11, y + 11), (x + 11, y + h - 11), (x + w - 11, y + h - 11)]
    for cx, cy in corners:
        pygame.draw.polygon(surface, C.GOLD_TRIM, [(cx, cy - 3), (cx + 3, cy), (cx, cy + 3), (cx - 3, cy)])

    # Title bar
    if title and title_font:
        title_w = title_font.size(title)[0] + 30
        tx = x + w // 2 - title_w // 2
        strip = generate_parchment_texture(title_w, 24)
        strip.set_alpha(200)
        surface.blit(strip, (tx, y - 2))
        pygame.draw.rect(surface, C.GOLD_DIM, (tx, y - 2, title_w, 24), 1, border_radius=2)
        draw_text_with_glow(surface, title, title_font, C.INK, x + w // 2, y + 3, align="center")


# ═══════════════════════════════════════════
# GLOW TEXT — CACHED RENDERING
# ═══════════════════════════════════════════

_glow_text_cache = {}
_GLOW_CACHE_MAX = 4096


def _make_glow_cache_key(text, font, color, glow_color, glow_radius):
    return (text, id(font), color, glow_color, glow_radius)


def _render_glow_surface(text, font, glow_color, glow_radius):
    main_surf = font.render(text, True, (255, 255, 255))
    tw, th = main_surf.get_size()
    pad = glow_radius * 2 + 2
    gw, gh = tw + pad * 2, th + pad * 2
    glow_combined = pygame.Surface((gw, gh), pygame.SRCALPHA)
    for dx in range(-glow_radius, glow_radius + 1):
        for dy in range(-glow_radius, glow_radius + 1):
            if dx == 0 and dy == 0:
                continue
            dist = (dx * dx + dy * dy) ** 0.5
            if dist > glow_radius:
                continue
            alpha = max(1, int(60 / (dist + 1)))
            glow_layer = font.render(text, True, glow_color)
            glow_layer.set_alpha(alpha)
            glow_combined.blit(glow_layer, (pad + dx, pad + dy))
    return glow_combined, pad


def draw_text_with_glow(surface, text, font, color, x, y, align="left", glow_color=None, glow_radius=2):
    """Draw text with an ethereal purple glow/shadow for readability on obsidian.
    Uses a cache to pre-compute the glow surface once per unique combination."""
    if glow_color is None:
        glow_color = (100, 60, 160)

    cache_key = _make_glow_cache_key(text, font, color, glow_color, glow_radius)
    cached = _glow_text_cache.get(cache_key)

    if cached is None:
        glow_surf, pad = _render_glow_surface(text, font, glow_color, glow_radius)
        main_surf = font.render(text, True, color)
        tw, th = main_surf.get_size()
        cached = (glow_surf, main_surf, tw, th, pad)
        if len(_glow_text_cache) >= _GLOW_CACHE_MAX:
            keys_to_remove = list(_glow_text_cache.keys())[: _GLOW_CACHE_MAX // 4]
            for k in keys_to_remove:
                del _glow_text_cache[k]
        _glow_text_cache[cache_key] = cached

    glow_surf, main_surf, tw, th, pad = cached

    if align == "center":
        glow_x = x - tw // 2 - pad
        glow_y = y - pad
        main_x = x - tw // 2
        main_y = y
    elif align == "right":
        glow_x = x - tw - pad
        glow_y = y - pad
        main_x = x - tw
        main_y = y
    else:
        glow_x = x - pad
        glow_y = y - pad
        main_x = x
        main_y = y

    surface.blit(glow_surf, (glow_x, glow_y))
    surface.blit(main_surf, (main_x, main_y))
    return pygame.Rect(main_x, main_y, tw, th)


def draw_text_wrapped_glow(surface, text, font, color, x, y, max_width, line_height=None, glow_color=None):
    """Word-wrapped text with glow effect."""
    if line_height is None:
        line_height = font.get_linesize()
    words = text.split(" ")
    lines = []
    current_line = ""
    for word in words:
        test = current_line + (" " if current_line else "") + word
        if font.size(test)[0] > max_width:
            if current_line:
                lines.append(current_line)
            current_line = word
        else:
            current_line = test
    if current_line:
        lines.append(current_line)
    for i, line_text in enumerate(lines):
        draw_text_with_glow(surface, line_text, font, color, x, y + i * line_height, glow_color=glow_color)
    return len(lines) * line_height


def draw_text_fitted_glow(surface, text, font, color, x, y, max_width, align="left", glow_color=None):
    """Fitted (truncated) text with glow effect."""
    fitted = fit_text(font, text, max_width)
    draw_text_with_glow(surface, fitted, font, color, x, y, align, glow_color=glow_color)


# ═══════════════════════════════════════════
# TYPEWRITER TEXT EFFECT SYSTEM
# ═══════════════════════════════════════════


class TypewriterText:
    """Manages typewriter-style text reveal effect."""

    def __init__(self, full_text, reveal_speed=36.0):
        """
        Args:
            full_text: The complete text to display
            reveal_speed: Characters revealed per second
        """
        self.full_text = full_text
        self.reveal_speed = reveal_speed
        self.current_index = 0
        self.timer = 0.0
        self.complete = False
        self.skip_requested = False

    def update(self, dt):
        """Update the typewriter effect. Call every frame with delta time."""
        if self.complete or self.skip_requested:
            self.current_index = len(self.full_text)
            self.complete = True
            return

        self.timer += dt
        # Calculate how many characters should be revealed
        chars_to_reveal = int(self.timer * self.reveal_speed)
        if chars_to_reveal > 0:
            self.current_index = min(len(self.full_text), self.current_index + chars_to_reveal)
            self.timer = 0.0  # Reset timer after revealing

        if self.current_index >= len(self.full_text):
            self.complete = True

    def skip(self):
        """Instantly complete the typewriter effect."""
        self.skip_requested = True
        self.update(0)

    def get_visible_text(self):
        """Get the currently visible portion of text."""
        return self.full_text[: self.current_index]

    def reset(self):
        """Reset the typewriter effect to start."""
        self.current_index = 0
        self.timer = 0.0
        self.complete = False
        self.skip_requested = False


# ═══════════════════════════════════════════
# MADNESS VIGNETTE EFFECT
# ═══════════════════════════════════════════

_madness_vignette_cache = {}
_VIGNETTE_CACHE_MAX = 8


def _make_vignette_cache_key(intensity, pulse_phase):
    """Create a cache key for vignette surfaces."""
    return f"{intensity}_{pulse_phase:.2f}"


def draw_madness_vignette(surface, madness_level, dt, time_seconds):
    """Draw a darkness vignette around screen edges based on madness level.

    As madness increases beyond 50%, the screen edges darken with a subtle
    pulsing effect to create visual tension without obscuring UI elements.

    Args:
        surface: Target pygame surface
        madness_level: Current madness value (0-100)
        dt: Delta time in seconds
        time_seconds: Total game time for pulse calculation
    """
    # Only activate when madness is above 50%
    if madness_level <= 50:
        return

    # Calculate intensity: 0 at 50% madness, up to 0.7 at 100% madness
    intensity = ((madness_level - 50) / 50) * 0.7

    # Add subtle pulsing using sine wave
    pulse_speed = 0.8  # Slow, eerie pulse
    pulse = 0.5 + 0.5 * math.sin(time_seconds * pulse_speed)
    pulsed_intensity = intensity * (0.85 + 0.15 * pulse)

    cache_key = _make_vignette_cache_key(int(pulsed_intensity * 100), pulse)

    if cache_key not in _madness_vignette_cache:
        # Create vignette surface with radial gradient
        vignette = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)

        # Draw multiple concentric ellipses for smooth gradient
        max_radius = max(SCREEN_W, SCREEN_H) // 2
        num_rings = 50

        for i in range(num_rings):
            ratio = i / num_rings
            # Alpha increases toward edges
            alpha = int(255 * pulsed_intensity * ratio * ratio)
            if alpha < 5:
                continue

            # Ellipse that fills the screen, growing outward
            rx = int(SCREEN_W // 2 + (max_radius * ratio))
            ry = int(SCREEN_H // 2 + (max_radius * 0.6 * ratio))

            # Dark purple-black color for eldritch feel
            color = (20, 10, 30, alpha)
            pygame.draw.ellipse(vignette, color, (SCREEN_W // 2 - rx, SCREEN_H // 2 - ry, rx * 2, ry * 2))

        if len(_madness_vignette_cache) >= _VIGNETTE_CACHE_MAX:
            keys_to_remove = list(_madness_vignette_cache.keys())[: _VIGNETTE_CACHE_MAX // 4]
            for k in keys_to_remove:
                del _madness_vignette_cache[k]

        _madness_vignette_cache[cache_key] = vignette

    vignette = _madness_vignette_cache[cache_key]
    surface.blit(vignette, (0, 0))


# ═══════════════════════════════════════════
# ELDRITCH PULSING AURA
# ═══════════════════════════════════════════


def draw_eldritch_aura(surface, rect, time_seconds, intensity=1.0, color=None):
    """Draw a pulsing eldritch aura around an enemy or area.

    Creates a threatening purple/pink glowing effect that pulses,
    used for bosses or dangerous enemies to highlight threat level.

    Args:
        surface: Target pygame surface
        rect: pygame.Rect defining the area to surround
        time_seconds: Total game time for pulse calculation
        intensity: Aura intensity multiplier (default 1.0)
        color: Custom color tuple (default: purple/pink eldritch colors)
    """
    if color is None:
        # Default eldritch purple-pink gradient colors
        base_color = (140, 60, 180)  # Purple
        accent_color = (200, 80, 150)  # Pink
    else:
        base_color = color
        accent_color = tuple(min(255, c + 40) for c in color)

    # Pulsing animation using sine wave
    pulse_speed = 2.0  # Moderate pulse speed
    pulse = 0.5 + 0.5 * math.sin(time_seconds * pulse_speed)
    eased_pulse = ease_in_out_quad(pulse)  # Smooth easing

    # Expand rect for aura layers
    max_expand = int(20 * intensity)

    # Draw multiple expanding layers for gradient effect — use pooled surfaces
    for i in range(5, 0, -1):
        layer_ratio = i / 5.0
        expand = int(max_expand * layer_ratio * eased_pulse)
        alpha = int(40 * intensity * layer_ratio * (1.0 - layer_ratio * 0.3))

        if alpha < 5:
            continue

        aura_rect = pygame.Rect(rect.x - expand, rect.y - expand, rect.w + expand * 2, rect.h + expand * 2)

        # Interpolate between base and accent color
        r = int(base_color[0] * layer_ratio + accent_color[0] * (1 - layer_ratio))
        g = int(base_color[1] * layer_ratio + accent_color[1] * (1 - layer_ratio))
        b = int(base_color[2] * layer_ratio + accent_color[2] * (1 - layer_ratio))

        aura_surf = surface_pool.acquire(aura_rect.w, aura_rect.h)
        pygame.draw.rect(aura_surf, (r, g, b, alpha), (0, 0, aura_rect.w, aura_rect.h), border_radius=8)
        surface.blit(aura_surf, (aura_rect.x, aura_rect.y))
        surface_pool.release(aura_surf)

    # Occasional spark particles for extra eldritch feel — use pooled surface
    if random.random() < 0.02 * intensity:
        spark_x = rect.x + random.randint(-max_expand, rect.w + max_expand)
        spark_y = rect.y + random.randint(-max_expand, rect.h + max_expand)
        spark_size = random.randint(2, 4)
        spark_surf = surface_pool.acquire(spark_size * 2, spark_size * 2)
        spark_color = (200, 160, 255, random.randint(100, 200))
        pygame.draw.circle(spark_surf, spark_color, (spark_size, spark_size), spark_size)
        surface.blit(spark_surf, (spark_x - spark_size, spark_y - spark_size))
        surface_pool.release(spark_surf)


# ═══════════════════════════════════════════
# HUD DRAWING
# ═══════════════════════════════════════════


def draw_hud(surface, s, assets):
    """Draw the persistent HUD bar at the top with ornate styling."""
    hud_h = 120
    # Cache the HUD background surface — it never changes
    hud_bg = render_cache.get(_HUD_BG_KEY)
    if hud_bg is None:
        hud_bg = pygame.Surface((SCREEN_W, hud_h), pygame.SRCALPHA)
        hud_bg.fill((12, 6, 24, 220))
        render_cache.put(_HUD_BG_KEY, hud_bg)
    surface.blit(hud_bg, (0, 0))
    pygame.draw.line(surface, C.GOLD_TRIM, (10, hud_h - 2), (SCREEN_W - 10, hud_h - 2), 2)
    pygame.draw.line(surface, C.GOLD_DIM, (10, hud_h - 5), (SCREEN_W - 10, hud_h - 5), 1)

    icon = CLASS_ICONS.get(s.class_id, "?")
    class_color = CLASS_COLORS.get(s.class_id, C.YELLOW)
    draw_text(surface, f"{icon} {s.class_name}", assets.fonts["body"], class_color, 15, 8)
    depth_names = ["The Asylum", "The Depths Below", "The Descent", "Approaching the Threshold", "The Spiral"]
    depth_idx = min(s.floor * len(depth_names) // s.max_floor, len(depth_names) - 1)
    draw_text(surface, depth_names[depth_idx], assets.fonts["body"], C.YELLOW, 420, 8)
    draw_text(surface, f"Lv.{s.level}", assets.fonts["body"], C.BONE, 680, 8)

    draw_text(surface, "HP", assets.fonts["small"], C.BONE, 15, 42)
    draw_bar(surface, 55, 42, 250, 20, s.hp, s.max_hp, hp_color(s.hp, s.max_hp))
    draw_text(surface, f"{s.hp}/{s.max_hp}", assets.fonts["tiny"], hp_color(s.hp, s.max_hp), 315, 44)
    if s.shield > 0:
        draw_text(surface, f"Shield:{int(s.shield)}", assets.fonts["tiny"], C.SHIELD_BLUE, 410, 44)

    draw_text(surface, "XP", assets.fonts["small"], C.BONE, 15, 68)
    draw_bar(surface, 55, 68, 250, 14, s.xp, s.xp_next, C.XP_PURPLE)
    draw_text(surface, f"{s.xp}/{s.xp_next}", assets.fonts["tiny"], C.XP_PURPLE, 315, 68)

    stats_display = [
        ("INT", s.stats.get("int", 0), C.ELDRITCH),
        ("STR", s.stats.get("str", 0), C.CRIMSON),
        ("AGI", s.stats.get("agi", 0), C.MIST),
        ("WIS", s.stats.get("wis", 0), C.FROST),
        ("LUK", s.luck, C.YELLOW),
    ]
    x = 480
    for name, val, color in stats_display:
        draw_text(surface, f"{name}:{val}", assets.fonts["tiny"], color, x, 42)
        x += 60
    draw_text(surface, f"ATK:{s.atk} DEF:{s.defense}", assets.fonts["tiny"], C.ASH, x, 42)

    draw_text(surface, f"Gold: {s.gold}g", assets.fonts["small"], C.GOLD, 480, 68)
    draw_text(surface, f"Madness: {int(s.madness)}%", assets.fonts["small"], mad_color(s.madness), 620, 68)

    # Buff/debuff icons row (replaces raw text statuses)
    draw_status_icons_row(surface, 480, 90, s.statuses, s.buffs, barrier=s.barrier, size=20, gap=4)

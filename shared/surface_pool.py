"""
THE KING IN YELLOW — Surface Pool & Render Cache

Performance optimization for the combat renderer and shared drawing functions.
Reduces garbage collection pressure by reusing pygame.Surface objects instead
of creating new ones every frame.

Two complementary systems:
1. SurfacePool — reuses per-frame temporary surfaces (particles, overlays)
2. RenderCache — caches expensive static render outputs (textures, panels)

Allocation hotspots addressed:
- Particles: one pygame.Surface per particle per frame → pooled
- Parchment textures: ~9 surface allocations per call → cached by (w, h)
- Button hover effects: 2-3 surfaces per hovered button per frame → pooled
- Combat overlays: glitch, flash, tooltip, intent panel → pooled
- Lighting system: full-screen scratch surfaces (~3.5 MB each) → pooled
- HUD background, status icon highlights, eldritch aura layers → cached/pooled
"""

from __future__ import annotations

import pygame
from collections import OrderedDict
from typing import Any, Optional, Tuple


class SurfacePool:
    """Pool of reusable pygame.Surface objects.

    Instead of creating a new ``pygame.Surface`` every frame (memory allocation
    + eventual GC), surfaces are *acquired* from the pool, used, and *released*
    for future reuse.

    The pool is keyed by ``(width, height, flags)`` so that only surfaces
    matching the exact specification are returned.

    Usage::

        pool = SurfacePool()
        surf = pool.acquire(100, 50)
        surf.fill((255, 0, 0, 128))
        screen.blit(surf, pos)
        pool.release(surf)
    """

    def __init__(self) -> None:
        self._pool: dict[Tuple[int, int, int], list[pygame.Surface]] = {}
        self._hits = 0
        self._misses = 0

    def acquire(self, width: int, height: int, srcalpha: bool = True) -> pygame.Surface:
        """Acquire a clean surface from the pool, or create a new one.

        The returned surface is cleared to transparent black (SRCALPHA) or
        solid black (non-alpha).

        Args:
            width: Desired width in pixels.
            height: Desired height in pixels.
            srcalpha: If True, surface supports per-pixel alpha (default).

        Returns:
            A ``pygame.Surface`` ready for use.
        """
        flags = pygame.SRCALPHA if srcalpha else 0
        key = (width, height, flags)
        bucket = self._pool.get(key)

        if bucket:
            surf = bucket.pop()
            if not bucket:
                del self._pool[key]
            self._hits += 1
        else:
            surf = pygame.Surface((width, height), flags)
            self._misses += 1

        # Always clean the surface before returning
        if srcalpha:
            surf.fill((0, 0, 0, 0))
        else:
            surf.fill((0, 0, 0))

        return surf

    def release(self, surface: pygame.Surface) -> None:
        """Return a surface to the pool for reuse.

        The surface **must not** be used after calling ``release()``.
        """
        key = (surface.get_width(), surface.get_height(), surface.get_flags())
        self._pool.setdefault(key, []).append(surface)

    def clear(self) -> None:
        """Discard all pooled surfaces. Call on game shutdown or screen transition."""
        self._pool.clear()

    @property
    def stats(self) -> dict[str, Any]:
        """Return pool statistics for debugging."""
        total = sum(len(v) for v in self._pool.values())
        return {
            "hits": self._hits,
            "misses": self._misses,
            "pooled_surfaces": total,
            "hit_rate": f"{self._hits / max(1, self._hits + self._misses):.1%}",
        }


class RenderCache:
    """LRU cache for expensive render outputs.

    Stores pre-rendered surfaces by key. When the cache exceeds *max_size*,
    the oldest (least-recently-used) entry is evicted.

    Usage::

        cache = RenderCache(max_size=128)
        surf = cache.get(("parchment", 400, 300))
        if surf is None:
            surf = generate_expensive_texture(400, 300)
            cache.put(("parchment", 400, 300), surf)
        screen.blit(surf, pos)
    """

    def __init__(self, max_size: int = 256) -> None:
        self._cache: OrderedDict[Any, pygame.Surface] = OrderedDict()
        self._max_size = max_size
        self._hits = 0
        self._misses = 0

    def get(self, key: Any) -> Optional[pygame.Surface]:
        """Retrieve a cached surface, promoting it to most-recently-used."""
        if key in self._cache:
            self._cache.move_to_end(key)
            self._hits += 1
            return self._cache[key]
        self._misses += 1
        return None

    def put(self, key: Any, surface: pygame.Surface) -> None:
        """Store a surface, evicting the oldest entry if at capacity."""
        if key in self._cache:
            self._cache.move_to_end(key)
            self._cache[key] = surface
        else:
            while len(self._cache) >= self._max_size:
                self._cache.popitem(last=False)
            self._cache[key] = surface

    def invalidate(self, key: Any) -> bool:
        """Remove one entry. Returns True if it existed."""
        if key in self._cache:
            del self._cache[key]
            return True
        return False

    def clear(self) -> None:
        """Discard all cached surfaces."""
        self._cache.clear()

    @property
    def stats(self) -> dict[str, Any]:
        """Return cache statistics for debugging."""
        return {
            "size": len(self._cache),
            "max_size": self._max_size,
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": f"{self._hits / max(1, self._hits + self._misses):.1%}",
        }


# ── Module-level singletons ──────────────────────────────────────────────

#: Global surface pool for per-frame temporary surfaces.
surface_pool = SurfacePool()

#: Global render cache for static/semi-static render outputs.
render_cache = RenderCache(max_size=256)

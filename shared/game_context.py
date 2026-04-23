"""
THE KING IN YELLOW — Game Context (Service Locator / Dependency Injection)

This module provides the :class:`GameContext` class, a lightweight service locator
that decouples screen classes from the concrete :class:`Game` class.  Screens
depend on ``GameContext`` (a well-defined interface) instead of ``Game`` (a
monolithic god-object), dramatically improving testability, modularity, and
extensibility.

Architecture
------------
The ``GameContext`` exposes four categories of services:

1. **State access** — read/write ``game.state`` through a property.
2. **Asset access** — read-only reference to the shared ``Assets`` instance.
3. **Navigation** — ``navigate()`` / ``toggle_fullscreen()`` / ``quit_game()``.
4. **Screen-to-screen data bus** — a generic ``screen_data`` dictionary that
   replaces the ad-hoc shared attributes that were previously scattered across
   the ``Game`` class (``shop_items``, ``trap_msg``, ``combat_result``, etc.).

Testing
-------
Because screens only depend on ``GameContext``, they can be unit-tested without
instantiating the full ``Game`` class (or even Pygame).  A test simply creates
a ``GameContext`` with mock callbacks and passes it to the screen constructor::

    ctx = GameContext(
        get_state=lambda: mock_state,
        set_state=lambda s: None,
        assets=mock_assets,
        navigate_callback=lambda name: None,
        toggle_fullscreen_callback=lambda: None,
        quit_callback=lambda: None,
    )
    screen = ExploreScreen(ctx)

Design notes
------------
* ``GameContext`` does **not** subclass ``Game``.  It is a *composition* wrapper,
  not an inheritance hierarchy — keeping the dependency one-directional.
* The ``screen_data`` dictionary is intentionally *generic* (``dict[str, Any]``)
  rather than typed fields, preserving the flexibility of the previous pattern
  while centralising it in one place.
* All callbacks are optional with sensible defaults, making partial mocks easy.
"""

from __future__ import annotations

from typing import Any, Callable, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from screens.screen_enum import ScreenName


class GameContext:
    """Service locator that provides decoupled access to game services.

    Screens receive a ``GameContext`` instead of a ``Game`` reference.
    This enables unit testing without instantiating the full game, and makes
    the dependency graph explicit and one-directional.

    Parameters
    ----------
    get_state:
        Callable that returns the current :class:`~engine.models.GameState`,
        or ``None`` if no game is in progress.
    set_state:
        Callable that accepts a new :class:`~engine.models.GameState` to
        replace the current one (used by class select and save/load).
    assets:
        The shared :class:`~shared.assets.Assets` instance for fonts, images,
        and sprites.
    navigate_callback:
        Callable accepting a :class:`ScreenName` to request a screen
        transition.  Mirrors ``Game.switch_screen()``.
    toggle_fullscreen_callback:
        Callable that toggles between fullscreen and windowed mode.
    quit_callback:
        Callable that signals the game loop to stop.
    get_prev_screen:
        Optional callable returning the previous screen's ``ScreenName``
        (or ``None``).  Used by screens that need to navigate "back".
    get_time_seconds:
        Optional callable returning the total elapsed game time in seconds.
        Used for animation timing.
    get_fullscreen:
        Optional callable returning whether the display is currently fullscreen.
    """

    def __init__(
        self,
        get_state: Callable[[], Any],
        set_state: Callable[[Any], None],
        assets: Any,
        navigate_callback: Callable[[ScreenName], None],
        toggle_fullscreen_callback: Callable[[], None],
        quit_callback: Callable[[], None],
        get_prev_screen: Optional[Callable[[], Optional[ScreenName]]] = None,
        get_time_seconds: Optional[Callable[[], float]] = None,
        get_fullscreen: Optional[Callable[[], bool]] = None,
        audio: Optional[Any] = None,
    ) -> None:
        self._get_state = get_state
        self._set_state = set_state
        self._assets = assets
        self._navigate = navigate_callback
        self._toggle_fullscreen = toggle_fullscreen_callback
        self._quit = quit_callback
        self._get_prev_screen = get_prev_screen
        self._get_time_seconds = get_time_seconds
        self._get_fullscreen = get_fullscreen
        self._audio = audio

        # Generic screen-to-screen data bus.
        # Replaces the former individual Game attributes:
        #   shop_items, shop_prices, shop_sold, shop_message, shop_msg_ok, shop_msg_timer,
        #   trap_msg, trap_name, trap_desc,
        #   combat_result, pending_event, gameover_msg
        self.screen_data: dict[str, Any] = {}

    # ── State access ──────────────────────────────────────────────────────────

    @property
    def state(self):
        """The current game state (read/write).

        Returns ``None`` when no game is in progress (e.g. on the title screen).
        """
        return self._get_state()

    @state.setter
    def state(self, value) -> None:
        self._set_state(value)

    # ── Asset access ──────────────────────────────────────────────────────────

    @property
    def assets(self):
        """The shared asset loader (fonts, images, sprites, cursor)."""
        return self._assets

    # ── Audio ─────────────────────────────────────────────────────────────────

    @property
    def audio(self):
        """The audio manager for playing UI sound effects (may be ``None``)."""
        return self._audio

    # ── Navigation ────────────────────────────────────────────────────────────

    def navigate(self, name: ScreenName) -> None:
        """Request a screen transition to *name*.

        This is the screen-layer replacement for ``Game.switch_screen()``.
        """
        self._navigate(name)

    def toggle_fullscreen(self) -> None:
        """Toggle between fullscreen and windowed display mode."""
        self._toggle_fullscreen()

    def quit_game(self) -> None:
        """Signal the game loop to stop (used by the Quit button)."""
        self._quit()

    # ── Contextual queries ────────────────────────────────────────────────────

    @property
    def prev_screen_name(self) -> Optional[ScreenName]:
        """The ``ScreenName`` of the previous screen, or ``None``."""
        if self._get_prev_screen:
            return self._get_prev_screen()
        return None

    @property
    def time_seconds(self) -> float:
        """Total elapsed game time in seconds (for animation)."""
        if self._get_time_seconds:
            return self._get_time_seconds()
        return 0.0

    @property
    def fullscreen(self) -> bool:
        """Whether the display is currently in fullscreen mode."""
        if self._get_fullscreen:
            return self._get_fullscreen()
        return False

    # ── Screen data bus helpers ───────────────────────────────────────────────

    def set_data(self, key: str, value: Any) -> None:
        """Store a value in the screen-to-screen data bus.

        Example::

            ctx.set_data("shop_items", items)
            ctx.set_data("trap_msg", "You triggered a spike trap!")
        """
        self.screen_data[key] = value

    def get_data(self, key: str, default: Any = None) -> Any:
        """Retrieve a value from the screen-to-screen data bus.

        Example::

            items = ctx.get_data("shop_items", [])
            msg = ctx.get_data("trap_msg", "")
        """
        return self.screen_data.get(key, default)

"""
Screen name enum for type-safe screen transitions.

All screen identifiers are defined here as members of ``ScreenName``.
Every call to ``Game.switch_screen()`` should use these enum values instead
of raw strings, which prevents typos and enables IDE autocompletion.

Usage::

    from screens import ScreenName

    self.game.switch_screen(ScreenName.EXPLORE)
"""

from enum import Enum


class ScreenName(str, Enum):
    """Unique identifier for every screen in the game.

    Inherits from ``str`` so that enum values can still be used as dictionary
    keys and compared to strings if needed (e.g. in ``get_background()``),
    while gaining full type-safety and IDE support.
    """

    TITLE = "title"
    CLASS_SELECT = "class_select"
    EXPLORE = "explore"
    COMBAT = "combat"
    INVENTORY = "inventory"
    SHOP = "shop"
    REST = "rest"
    LOOT = "loot"
    EVENT = "event"
    TRAP_RESULT = "trap_result"
    COMBAT_RESULT = "combat_result"
    LEVELUP = "levelup"
    GAMEOVER = "gameover"
    VICTORY = "victory"
    SAVE = "save"
    LOAD = "load"
    STATS = "stats"

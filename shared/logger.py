"""
THE KING IN YELLOW — Logging System

Provides a centralized, configurable logging setup for the entire project.
All modules should use this logger instead of raw print() statements.

Usage:
    from shared.logger import get_logger
    logger = get_logger(__name__)
    logger.info("Game started")
    logger.warning("Asset not found: %s", path)
    logger.error("Failed to save game: %s", err)

Log levels:
    DEBUG    — Verbose diagnostics (asset loading details, internal state)
    INFO     — Noteworthy events (game start, screen transitions, saves)
    WARNING  — Non-critical issues (asset fallbacks, missing optional files)
    ERROR    — Failures that affect functionality (save errors, load failures)
    CRITICAL — Fatal errors that crash the game

Configuration:
    Controlled via settings.json [logging] section:
    - level: minimum log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    - log_to_file: whether to write logs to a file
    - log_file: path to log file (relative to game root)
    - console_format: format string for console output
    - file_format: format string for file output
"""

import logging
import os
import sys
from typing import Optional

# ═══════════════════════════════════════════
# GAME-SPECIFIC LOG LEVELS
# ═══════════════════════════════════════════

# We use standard Python log levels — no custom levels needed.
# Modules use semantic log levels:
#   logger.debug()    → Verbose internal diagnostics
#   logger.info()     → Noteworthy game events
#   logger.warning()  → Non-critical issues, fallbacks
#   logger.error()    → Functional failures
#   logger.critical() → Fatal crashes


# ═══════════════════════════════════════════
# FORMAT STRINGS
# ═══════════════════════════════════════════

# Console format: colored level + short message
# Uses Unicode box-drawing characters for a clean, game-appropriate look
CONSOLE_FORMAT = "%(levelname)-8s │ %(name)-28s │ %(message)s"

# File format: timestamp + level + module + message (more detailed for debugging)
FILE_FORMAT = "%(asctime)s │ %(levelname)-8s │ %(name)-28s │ %(message)s"

# Date format for file logs
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


# ═══════════════════════════════════════════
# LOG LEVEL COLOR CODES (ANSI)
# ═══════════════════════════════════════════


class _LogColors:
    """ANSI color codes for log levels."""

    RESET = "\033[0m"
    DEBUG = "\033[36m"  # Cyan
    INFO = "\033[32m"  # Green
    WARNING = "\033[33m"  # Yellow
    ERROR = "\033[31m"  # Red
    CRITICAL = "\033[1;31m"  # Bold Red


_LEVEL_COLORS = {
    "DEBUG": _LogColors.DEBUG,
    "INFO": _LogColors.INFO,
    "WARNING": _LogColors.WARNING,
    "ERROR": _LogColors.ERROR,
    "CRITICAL": _LogColors.CRITICAL,
}


class _ColorFormatter(logging.Formatter):
    """Custom formatter that adds ANSI color codes to log levels."""

    def __init__(self, fmt=None, datefmt=None, use_color=True):
        super().__init__(fmt, datefmt)
        self.use_color = use_color

    def format(self, record):
        if self.use_color and record.levelname in _LEVEL_COLORS:
            # Store original and apply color
            record.levelname_colored = f"{_LEVEL_COLORS[record.levelname]}{record.levelname:<8}{_LogColors.RESET}"
            # Use the colored version in format string
            record.levelname = record.levelname_colored
        return super().format(record)


# ═══════════════════════════════════════════
# GLOBAL LOGGER REGISTRY
# ═══════════════════════════════════════════

_loggers = {}
_root_configured = False
_file_handler = None


def _get_game_root() -> str:
    """Get the root directory of the game project."""
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _detect_color_support() -> bool:
    """Detect if the terminal supports ANSI color codes."""
    if sys.platform == "win32":
        try:
            import ctypes

            kernel32 = ctypes.windll.kernel32
            # Enable ANSI escape sequences on Windows 10+
            kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
            return True
        except Exception:
            return False
    # Unix-like systems generally support ANSI colors
    # But check if we're not piped to a file
    return hasattr(sys.stderr, "isatty") and sys.stderr.isatty()


def configure_logging(
    level: str = "INFO",
    log_to_file: bool = False,
    log_file: Optional[str] = None,
    console_format: Optional[str] = None,
    file_format: Optional[str] = None,
) -> None:
    """Configure the root game logger.

    This should be called once at startup, before any other logging.
    Can be called again to reconfigure (e.g., when loading settings.json).

    Args:
        level: Minimum log level as string (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_to_file: Whether to write logs to a file
        log_file: Path to log file (relative to game root or absolute)
        console_format: Custom format string for console output
        file_format: Custom format string for file output
    """
    global _root_configured, _file_handler

    use_color = _detect_color_support()

    # Get the root game logger
    root_logger = logging.getLogger("yellow_sign")
    root_logger.setLevel(getattr(logging, level.upper(), logging.INFO))

    # Remove existing handlers to allow reconfiguration
    root_logger.handlers.clear()

    # ── Console Handler ──
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)  # Show everything; level filtering on logger

    fmt = console_format or CONSOLE_FORMAT
    console_formatter = _ColorFormatter(fmt, use_color=use_color)
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)

    # ── File Handler ──
    if _file_handler is not None:
        try:
            _file_handler.close()
        except Exception:
            pass
        _file_handler = None

    if log_to_file:
        game_root = _get_game_root()
        if log_file is None:
            log_file = "logs/game.log"

        # Resolve relative paths against game root
        if not os.path.isabs(log_file):
            log_file = os.path.join(game_root, log_file)

        # Ensure log directory exists
        log_dir = os.path.dirname(log_file)
        if log_dir:
            os.makedirs(log_dir, exist_ok=True)

        file_handler = logging.FileHandler(log_file, encoding="utf-8", mode="a")
        file_handler.setLevel(logging.DEBUG)  # Show everything; level filtering on logger
        file_formatter = logging.Formatter(
            file_format or FILE_FORMAT,
            datefmt=DATE_FORMAT,
        )
        file_handler.setFormatter(file_formatter)
        root_logger.addHandler(file_handler)
        _file_handler = file_handler

    _root_configured = True


def get_logger(name: str) -> logging.Logger:
    """Get a named logger under the game's logger hierarchy.

    All loggers created through this function are children of the
    'yellow_sign' root logger and inherit its configuration.

    Usage:
        logger = get_logger("assets")
        logger = get_logger("combat")
        logger = get_logger("screens.title")

    The logger name will be prefixed: "yellow_sign.assets", etc.

    Args:
        name: Logger name (typically module or subsystem name)

    Returns:
        A configured logging.Logger instance
    """
    if name in _loggers:
        return _loggers[name]

    # Create logger under the game hierarchy
    if name.startswith("yellow_sign"):
        logger = logging.getLogger(name)
    else:
        logger = logging.getLogger(f"yellow_sign.{name}")

    _loggers[name] = logger
    return logger


def set_level(level: str) -> None:
    """Change the minimum log level at runtime.

    Args:
        level: Log level string (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    root_logger = logging.getLogger("yellow_sign")
    root_logger.setLevel(getattr(logging, level.upper(), logging.INFO))


def shutdown() -> None:
    """Cleanly shut down the logging system (flush file handlers)."""
    global _file_handler
    root_logger = logging.getLogger("yellow_sign")
    for handler in root_logger.handlers:
        try:
            handler.flush()
            handler.close()
        except Exception:
            pass
    root_logger.handlers.clear()
    _file_handler = None

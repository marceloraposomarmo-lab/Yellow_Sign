"""
THE KING IN YELLOW — Settings Manager

Loads, validates, and provides access to game settings from settings.json.
Designed so that future player-customizable settings can be added easily
without changing the loading architecture.

Architecture:
  - Default settings are defined in DEFAULT_SETTINGS (this file)
  - config/settings.json provides project-wide overrides
  - Future: user_settings.json provides per-player overrides (highest priority)

Usage:
    from config import get_settings
    settings = get_settings()

    # Access display settings
    width = settings.get("display.screen_width", 1280)
    fps = settings.get("display.fps", 60)

    # Nested access
    log_level = settings.get("logging.level", "INFO")

    # Check if a key exists
    if settings.has("display.fullscreen"):
        ...
"""

import json
import os
from typing import Any, Optional, Dict


# ═══════════════════════════════════════════
# DEFAULT SETTINGS (fallback when files are missing)
# ═══════════════════════════════════════════

DEFAULT_SETTINGS: Dict[str, Any] = {
    "display": {
        "screen_width": 1280,
        "screen_height": 720,
        "fps": 60,
        "fullscreen": False,
        "vsync": True,
    },
    "audio": {
        "master_volume": 0.5,
        "muted": False,
    },
    "gameplay": {
        "max_floor": 20,
        "save_slots": 5,
    },
    "logging": {
        "level": "INFO",
        "log_to_file": False,
        "log_file": "logs/game.log",
        "console_format": "%(levelname)-8s │ %(name)-28s │ %(message)s",
        "file_format": "%(asctime)s │ %(levelname)-8s │ %(name)-28s │ %(message)s",
    },
}


class SettingsManager:
    """Manages game settings with layered configuration.

    Settings are loaded in priority order (later overrides earlier):
    1. DEFAULT_SETTINGS (built-in defaults)
    2. config/settings.json (project defaults)
    3. Future: user_settings.json (player preferences)

    Supports dot-notation access: settings.get("display.screen_width")
    """

    def __init__(self, config_dir: Optional[str] = None):
        """Initialize settings manager.

        Args:
            config_dir: Path to config directory. If None, auto-detects
                        as config/ relative to the game root.
        """
        self._data: Dict[str, Any] = {}
        self._config_dir = config_dir

        # Deep copy defaults
        self._data = self._deep_copy(DEFAULT_SETTINGS)

        # Load project settings file
        self._load_settings_file()

    @property
    def config_dir(self) -> str:
        """Get the config directory path."""
        if self._config_dir is None:
            self._config_dir = os.path.join(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                "config",
            )
        return self._config_dir

    @property
    def game_root(self) -> str:
        """Get the game root directory."""
        return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    def _deep_copy(self, d: Dict[str, Any]) -> Dict[str, Any]:
        """Deep copy a dictionary (no import needed for simple dicts)."""
        result = {}
        for k, v in d.items():
            if isinstance(v, dict):
                result[k] = self._deep_copy(v)
            else:
                result[k] = v
        return result

    def _deep_merge(self, base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        """Deep merge override dict into base dict. Returns merged result."""
        result = self._deep_copy(base)
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value
        return result

    def _load_settings_file(self) -> bool:
        """Load settings from config/settings.json.

        Returns:
            True if the file was loaded successfully, False otherwise.
        """
        settings_path = os.path.join(self.config_dir, "settings.json")
        if not os.path.exists(settings_path):
            return False

        try:
            with open(settings_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            # Filter out meta keys (starting with _)
            user_data = {k: v for k, v in data.items() if not k.startswith("_")}

            # Deep merge into current settings
            self._data = self._deep_merge(self._data, user_data)
            return True

        except (json.JSONDecodeError, IOError) as e:
            # If settings file is corrupt, keep defaults
            print(f"[Settings] Warning: Failed to load {settings_path}: {e}")
            return False

    def get(self, key: str, default: Any = None) -> Any:
        """Get a setting value using dot notation.

        Args:
            key: Setting key, supports dot notation (e.g., "display.screen_width")
            default: Default value if key is not found

        Returns:
            The setting value, or default if not found
        """
        parts = key.split(".")
        current = self._data
        for part in parts:
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                return default
        return current

    def set(self, key: str, value: Any) -> None:
        """Set a setting value using dot notation.

        This only changes the in-memory value. To persist, call save().

        Args:
            key: Setting key, supports dot notation (e.g., "display.screen_width")
            value: The value to set
        """
        parts = key.split(".")
        current = self._data
        for part in parts[:-1]:
            if part not in current or not isinstance(current[part], dict):
                current[part] = {}
            current = current[part]
        current[parts[-1]] = value

    def has(self, key: str) -> bool:
        """Check if a setting key exists.

        Args:
            key: Setting key, supports dot notation

        Returns:
            True if the key exists in settings
        """
        parts = key.split(".")
        current = self._data
        for part in parts:
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                return False
        return True

    def get_section(self, section: str) -> Dict[str, Any]:
        """Get an entire settings section as a dictionary.

        Args:
            section: Top-level section name (e.g., "display", "logging")

        Returns:
            Dictionary of settings in that section, or empty dict if not found
        """
        value = self._data.get(section)
        if isinstance(value, dict):
            return dict(value)
        return {}

    def save(self, filepath: Optional[str] = None) -> bool:
        """Save current settings to a JSON file.

        Args:
            filepath: Path to save to. If None, saves to config/settings.json

        Returns:
            True if saved successfully, False otherwise
        """
        if filepath is None:
            filepath = os.path.join(self.config_dir, "settings.json")

        try:
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(self._data, f, indent=2)
            return True
        except (IOError, OSError) as e:
            print(f"[Settings] Warning: Failed to save settings: {e}")
            return False

    def to_dict(self) -> Dict[str, Any]:
        """Return a deep copy of all settings as a dictionary."""
        return self._deep_copy(self._data)

    def __repr__(self) -> str:
        return f"SettingsManager(sections={list(self._data.keys())})"


# ═══════════════════════════════════════════
# GLOBAL SETTINGS INSTANCE (lazy singleton)
# ═══════════════════════════════════════════

_settings_instance: Optional[SettingsManager] = None


def get_settings() -> SettingsManager:
    """Get the global settings manager instance.

    Creates the instance on first call. Subsequent calls return
    the same instance.

    Returns:
        The global SettingsManager instance
    """
    global _settings_instance
    if _settings_instance is None:
        _settings_instance = SettingsManager()
    return _settings_instance


def init_settings(config_dir: Optional[str] = None) -> SettingsManager:
    """Initialize the settings manager with an optional custom config directory.

    This can be called before get_settings() to override the default
    config directory. Useful for testing or portable installations.

    Args:
        config_dir: Path to config directory

    Returns:
        The initialized SettingsManager instance
    """
    global _settings_instance
    _settings_instance = SettingsManager(config_dir=config_dir)
    return _settings_instance

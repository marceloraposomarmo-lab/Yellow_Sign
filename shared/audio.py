"""
THE KING IN YELLOW — Audio Manager

Plays UI sound effects from WAV assets in assets/audio/ui/.
Falls back to procedural synthesis when audio files are missing.

Sound palette (BNA horror UI pack):
  hover       — BNA_UI16  |  Soft bloop, subtle navigation feedback
  click       — BNA_UI19  |  Crisp digital click, instant button feedback
  confirm     — BNA_UI4   |  Playful blip/pop, positive accept actions
  cancel      — BNA_UI2   |  Descending blip, back/dismiss
  error       — BNA_UI18  |  Sharp electronic blip, invalid action
  game_over   — BNA_UI8   |  Heavy cinematic thud, dramatic end
  level_up    — BNA_UI1   |  Ascending chime, achievement sparkle
  transition  — BNA_UI7   |  Whoosh, screen-to-screen movement
  boss_start  — BNA_UI3   |  Heavy impact, boss encounter opener

Architecture:
  - AudioManager is created once in Game and passed via GameContext
  - Screens call ``ctx.audio.play("click")`` or use base Screen helpers
  - Sounds are loaded lazily on first use
  - Master volume and mute are configurable
  - Graceful fallback when pygame.mixer is unavailable
"""

from __future__ import annotations

import array
import math
import os
from typing import Dict, Optional

from shared.logger import get_logger

logger = get_logger("audio")

# Try to import pygame.mixer — may not be available in test environments
try:
    import pygame.mixer as _mixer
    _MIXER_AVAILABLE = True
except ImportError:
    _mixer = None
    _MIXER_AVAILABLE = False

# Directory containing UI sound WAV files
_UI_AUDIO_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "assets", "audio", "ui",
)

# Sound file mapping: sound_name -> filename
_SOUND_FILES: Dict[str, str] = {
    "hover":      "BNA_UI16.wav",
    "click":      "BNA_UI19.wav",
    "confirm":    "BNA_UI4.wav",
    "cancel":     "BNA_UI2.wav",
    "error":      "BNA_UI18.wav",
    "game_over":  "BNA_UI8.wav",
    "level_up":   "BNA_UI1.wav",
    "transition": "BNA_UI7.wav",
    "boss_start": "BNA_UI3.wav",
}

# Procedural fallback parameters: (frequency_hz, duration_sec, sweep_factor)
_FALLBACK_PARAMS: Dict[str, tuple] = {
    "hover":      (900, 0.04, 1.3),
    "click":      (600, 0.06, 1.0),
    "confirm":    (1000, 0.12, 1.5),
    "cancel":     (400, 0.10, 0.6),
    "error":      (150, 0.15, 0.7),
    "game_over":  (100, 0.40, 0.5),
    "level_up":   (800, 0.30, 2.0),
    "transition": (500, 0.20, 1.8),
    "boss_start": (80, 0.50, 0.4),
}


class AudioManager:
    """UI sound effect manager with WAV asset loading and procedural fallback.

    Parameters
    ----------
    sample_rate : int
        Audio sample rate in Hz (default 22050).
    master_volume : float
        Global volume multiplier (0.0 to 1.0).
    muted : bool
        If True, all play calls are silently skipped.
    """

    def __init__(
        self,
        sample_rate: int = 22050,
        master_volume: float = 0.5,
        muted: bool = False,
    ) -> None:
        self._sample_rate = sample_rate
        self._master_volume = master_volume
        self._muted = muted
        self._sounds: Dict[str, object] = {}
        self._mixer_ready = False

        if not _MIXER_AVAILABLE:
            logger.warning("pygame.mixer not available — audio disabled")
            return

        try:
            if not _mixer.get_init():
                _mixer.init(frequency=sample_rate, size=-16, channels=1, buffer=512)
            self._mixer_ready = _mixer.get_init() is not None
            if self._mixer_ready:
                logger.info("AudioManager initialized (rate=%d, vol=%.1f)", sample_rate, master_volume)
            else:
                logger.warning("pygame.mixer init returned None — audio disabled")
        except Exception as e:
            logger.warning("pygame.mixer init failed: %s — audio disabled", e)
            self._mixer_ready = False

    # ── Public API ────────────────────────────────────────────────────────────

    def play(self, name: str) -> None:
        """Play a named sound effect.

        Parameters
        ----------
        name : str
            Sound name: ``"hover"``, ``"click"``, ``"confirm"``,
            ``"cancel"``, ``"error"``, ``"game_over"``, ``"level_up"``,
            ``"transition"``, or ``"boss_start"``.
        """
        if self._muted or not self._mixer_ready:
            return

        snd = self._sounds.get(name)
        if snd is None:
            snd = self._load_or_generate(name)
            if snd is None:
                return
            self._sounds[name] = snd

        try:
            channel = _mixer.find_channel()
            if channel:
                channel.set_volume(self._master_volume)
                channel.play(snd)
        except Exception as e:
            logger.debug("play(%s) failed: %s", name, e)

    def set_volume(self, volume: float) -> None:
        """Set master volume (0.0 to 1.0)."""
        self._master_volume = max(0.0, min(1.0, volume))

    def get_volume(self) -> float:
        """Get current master volume."""
        return self._master_volume

    def mute(self) -> None:
        """Mute all sounds."""
        self._muted = True

    def unmute(self) -> None:
        """Unmute all sounds."""
        self._muted = False

    def toggle_mute(self) -> bool:
        """Toggle mute state. Returns new muted state."""
        self._muted = not self._muted
        return self._muted

    @property
    def muted(self) -> bool:
        """Whether audio is currently muted."""
        return self._muted

    @property
    def available(self) -> bool:
        """Whether the audio system is operational."""
        return self._mixer_ready

    # ── Sound Loading ─────────────────────────────────────────────────────────

    def _load_or_generate(self, name: str):
        """Try to load WAV file, fall back to procedural generation."""
        # Try WAV file first
        filename = _SOUND_FILES.get(name)
        if filename:
            filepath = os.path.join(_UI_AUDIO_DIR, filename)
            if os.path.exists(filepath):
                try:
                    snd = _mixer.Sound(filepath)
                    self._sounds[name] = snd
                    logger.debug("Loaded audio: %s (%s)", name, filename)
                    return snd
                except Exception as e:
                    logger.warning("Failed to load %s: %s — using fallback", filepath, e)

        # Fall back to procedural generation
        return self._generate_fallback(name)

    # ── Procedural Fallback ───────────────────────────────────────────────────

    def _generate_fallback(self, name: str):
        """Generate a fallback sound effect procedurally."""
        if name not in _FALLBACK_PARAMS:
            logger.debug("Unknown sound: %s", name)
            return None

        freq, dur, sweep = _FALLBACK_PARAMS[name]
        sr = self._sample_rate
        n = int(sr * dur)

        # Choose generator based on sound type
        if name == "confirm":
            samples = self._gen_confirm(n, sr)
        elif name == "error":
            samples = self._gen_error(n, sr)
        elif name in ("game_over", "boss_start"):
            samples = self._gen_heavy(n, sr, freq, sweep)
        elif name == "level_up":
            samples = self._gen_sparkle(n, sr)
        elif name == "transition":
            samples = self._gen_whoosh(n, sr)
        else:
            samples = self._gen_tone(n, sr, freq, sweep)

        # Convert to 16-bit PCM bytes
        buf = array.array("h", [max(-32768, min(32767, int(s))) for s in samples])

        try:
            snd = _mixer.Sound(buffer=buf)
            self._sounds[name] = snd
            logger.debug("Generated fallback: %s", name)
            return snd
        except Exception as e:
            logger.debug("Fallback generation failed for %s: %s", name, e)
            return None

    @staticmethod
    def _gen_tone(n: int, sr: int, freq: float, sweep: float) -> list:
        """Generate a single tone with exponential decay and optional frequency sweep."""
        samples = []
        for i in range(n):
            t = i / sr
            progress = i / n
            envelope = (1.0 - progress) ** 2
            f = freq * (1.0 + (sweep - 1.0) * progress)
            val = 12000 * envelope * math.sin(2 * math.pi * f * t)
            samples.append(val)
        return samples

    @staticmethod
    def _gen_confirm(n: int, sr: int) -> list:
        """Generate confirm sound: ascending double-tone."""
        samples = []
        half = n // 2
        for i in range(n):
            t = i / sr
            progress = i / n
            envelope = (1.0 - progress) ** 2
            f = 1000 if i < half else 1300
            val = 10000 * envelope * math.sin(2 * math.pi * f * t)
            val += 3000 * envelope * math.sin(2 * math.pi * f * 1.5 * t)
            samples.append(val)
        return samples

    @staticmethod
    def _gen_error(n: int, sr: int) -> list:
        """Generate error sound: low descending buzz."""
        samples = []
        for i in range(n):
            t = i / sr
            progress = i / n
            envelope = (1.0 - progress) ** 2
            f = 150 * (1.0 - 0.3 * progress)
            val = 10000 * envelope * math.sin(2 * math.pi * f * t)
            val += 5000 * envelope * math.sin(2 * math.pi * f * 2 * t)
            samples.append(val)
        return samples

    @staticmethod
    def _gen_heavy(n: int, sr: int, freq: float, sweep: float) -> list:
        """Generate heavy impact sound with sub-bass rumble."""
        samples = []
        for i in range(n):
            t = i / sr
            progress = i / n
            envelope = (1.0 - progress) ** 1.5
            f = freq * (1.0 + (sweep - 1.0) * progress)
            val = 15000 * envelope * math.sin(2 * math.pi * f * t)
            val += 8000 * envelope * math.sin(2 * math.pi * f * 0.5 * t)
            val += 4000 * envelope * math.sin(2 * math.pi * f * 2 * t)
            samples.append(val)
        return samples

    @staticmethod
    def _gen_sparkle(n: int, sr: int) -> list:
        """Generate ascending sparkle/chime for level up."""
        samples = []
        for i in range(n):
            t = i / sr
            progress = i / n
            envelope = (1.0 - progress) ** 2
            f = 600 + 800 * progress
            val = 10000 * envelope * math.sin(2 * math.pi * f * t)
            val += 5000 * envelope * math.sin(2 * math.pi * f * 1.5 * t)
            val += 2000 * envelope * math.sin(2 * math.pi * f * 2 * t)
            samples.append(val)
        return samples

    @staticmethod
    def _gen_whoosh(n: int, sr: int) -> list:
        """Generate whoosh/transition sound."""
        samples = []
        for i in range(n):
            t = i / sr
            progress = i / n
            # Bell-curve envelope for smooth in/out
            envelope = math.sin(math.pi * progress)
            # Frequency sweep from low to high
            f = 200 + 600 * progress
            # Mix sine + noise-like component
            import random
            noise = random.uniform(-0.3, 0.3) * 8000 * envelope
            val = 8000 * envelope * math.sin(2 * math.pi * f * t) + noise
            samples.append(val)
        return samples

    def __repr__(self) -> str:
        status = "muted" if self._muted else ("ready" if self._mixer_ready else "unavailable")
        return f"AudioManager({status}, vol={self._master_volume:.1f})"

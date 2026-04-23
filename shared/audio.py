"""
THE KING IN YELLOW — Audio Manager

Generates and plays synthetic UI sound effects procedurally.
No external audio files required — all sounds are synthesized at runtime
using sine waves with envelope shaping.

Sound palette:
  hover   — soft high-pitched blip on button hover
  click   — crisp mid-tone tap on button click
  confirm — ascending double-tone for accept/confirm actions
  cancel  — descending tone for back/cancel actions
  error   — low buzz for invalid/disabled actions

Architecture:
  - AudioManager is created once in Game and passed via GameContext
  - Screens call ``ctx.audio.play("click")`` or use base Screen helpers
  - Sounds are generated lazily on first use
  - Master volume and mute are configurable
  - Graceful fallback when pygame.mixer is unavailable
"""

from __future__ import annotations

import array
import math
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


class AudioManager:
    """Procedural UI sound effect manager.

    Generates short sound effects at runtime using sine wave synthesis.
    No external audio assets required.

    Parameters
    ----------
    sample_rate : int
        Audio sample rate in Hz (default 22050 — good quality, low overhead).
    master_volume : float
        Global volume multiplier (0.0 to 1.0).
    muted : int
        If True, all play calls are silently skipped.
    """

    # Sound generation parameters: (frequency_hz, duration_sec, sweep_factor)
    _SOUND_PARAMS: Dict[str, tuple] = {
        "hover":  (900, 0.04, 1.3),
        "click":  (600, 0.06, 1.0),
        "confirm": (1000, 0.12, 1.5),
        "cancel": (400, 0.10, 0.6),
        "error":  (150, 0.15, 0.7),
    }

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
            ``"cancel"``, or ``"error"``.
        """
        if self._muted or not self._mixer_ready:
            return

        snd = self._sounds.get(name)
        if snd is None:
            snd = self._generate(name)
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

    # ── Sound Generation ──────────────────────────────────────────────────────

    def _generate(self, name: str):
        """Generate a sound effect by name. Returns a pygame.mixer.Sound or None."""
        if name not in self._SOUND_PARAMS:
            logger.debug("Unknown sound: %s", name)
            return None

        freq, dur, sweep = self._SOUND_PARAMS[name]
        sr = self._sample_rate
        n = int(sr * dur)

        # Choose generator based on sound type
        if name == "confirm":
            samples = self._gen_confirm(n, sr)
        elif name == "error":
            samples = self._gen_error(n, sr)
        else:
            samples = self._gen_tone(n, sr, freq, sweep)

        # Convert to 16-bit PCM bytes
        buf = array.array("h", [max(-32768, min(32767, int(s))) for s in samples])

        try:
            snd = _mixer.Sound(buffer=buf)
            self._sounds[name] = snd
            return snd
        except Exception as e:
            logger.debug("Sound generation failed for %s: %s", name, e)
            return None

    @staticmethod
    def _gen_tone(n: int, sr: int, freq: float, sweep: float) -> list:
        """Generate a single tone with exponential decay and optional frequency sweep."""
        samples = []
        for i in range(n):
            t = i / sr
            progress = i / n
            # Exponential decay envelope
            envelope = 1.0 - progress
            envelope = envelope * envelope
            # Frequency sweep
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
            envelope = 1.0 - progress
            envelope = envelope * envelope
            if i < half:
                f = 1000
            else:
                f = 1300
            val = 10000 * envelope * math.sin(2 * math.pi * f * t)
            # Add soft harmonic
            val += 3000 * envelope * math.sin(2 * math.pi * f * 1.5 * t)
            samples.append(val)
        return samples

    @staticmethod
    def _gen_error(n: int, sr: int) -> list:
        """Generate error sound: low descending buzz with two tones."""
        samples = []
        for i in range(n):
            t = i / sr
            progress = i / n
            envelope = 1.0 - progress
            envelope = envelope * envelope
            f = 150 * (1.0 - 0.3 * progress)
            val = 10000 * envelope * math.sin(2 * math.pi * f * t)
            val += 5000 * envelope * math.sin(2 * math.pi * f * 2 * t)
            samples.append(val)
        return samples

    def __repr__(self) -> str:
        status = "muted" if self._muted else ("ready" if self._mixer_ready else "unavailable")
        return f"AudioManager({status}, vol={self._master_volume:.1f})"

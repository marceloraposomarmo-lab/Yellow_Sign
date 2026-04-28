"""
THE KING IN YELLOW — Audio Manager

Plays UI sound effects from WAV assets in assets/audio/ui/.
Falls back to procedural synthesis when audio files are missing.

Sound palette (BNA horror UI + Unholy Souls — Lovecraftian selection):
  click       — BNA_UI28  |  Quick digital tick, clean button press
  confirm     — BNA_UI40  |  Crisp metallic chime, positive confirmation
  cancel      — BNA_UI44  |  Descending bloop, back/dismiss
  error       — BNA_UI9   |  Deep metallic thud, ominous invalid action
  game_over   — BNA_UI29  |  Heavy cinematic slam, final dread
  level_up    — BNA_UI25  |  Ethereal shimmering sweep, dark reward
  transition  — BNA_UI13_Long3  |  Stone door whoosh, atmospheric passage
  boss_start  — BNA_UI13_Long4  |  Cinematic drone → metallic reveal
  loot        — BNA_UI11  |  Dice & coin clatter, loot chest opening
  equip       — Unholy_Souls_13  |  Metallic blade shing, weapon equipping
  purchase    — BNA_UI12  |  Bubbly rising chime, shop transaction
  combat_start — mixkit-horror-swish-1495  |  Horror swish, eerie pre-combat dread
  event_mystery — Creepy_ambience_3  |  Eerie ascending shimmer, unsettling discovery
  trap_trigger — Stinger  |  Heavy stone slam, ominous trap activation

Music contexts (MP3 assets in assets/audio/music/):
  intro        — Game_Intro_Song.mp3           | Title + Class Select
  explore_low  — Exploration_Low_Madness_1/2   | Exploration (madness < 50)
  explore_high — Exploration_High_Madness_1    | Exploration (madness ≥ 50)
  combat       — Combat_1/2/3                  | Normal enemy combat
  boss         — Combat_4                      | Boss encounters

Architecture:
  - AudioManager is created once in Game and passed via GameContext
  - Screens call ``ctx.audio.play("click")`` or use base Screen helpers
  - Sounds are loaded lazily on first use
  - Master volume and mute are configurable
  - Music playback via pygame.mixer.music with crossfade support
  - Graceful fallback when pygame.mixer is unavailable
  - No hover sounds — only action-based audio (clicks, confirms, etc.)
"""

from __future__ import annotations

import array
import math
import os
import random
from typing import Dict, List, Optional

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
    "assets",
    "audio",
    "ui",
)

# Directory containing background music MP3 files
_MUSIC_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "assets",
    "audio",
    "music",
)

# Music track registry: context -> list of MP3 filenames
# When multiple tracks are listed, one is picked at random (shuffled).
_MUSIC_TRACKS: Dict[str, List[str]] = {
    "intro": ["Game_Intro_Song.mp3"],
    "explore_low": ["Exploration_Low_Madness_1.mp3", "Exploration_Low_Madness_2.mp3"],
    "explore_high": ["Exploration_High_Madness_1.mp3"],
    "combat": ["Combat_1.mp3", "Combat_2.mp3", "Combat_3.mp3"],
    "boss": ["Combat_4.mp3"],
}

# Default volumes per music context (0.0–1.0)
_MUSIC_VOLUMES: Dict[str, float] = {
    "intro": 0.12,
    "explore_low": 0.09,
    "explore_high": 0.12,
    "combat": 0.14,
    "boss": 0.16,
}

# Fade durations in milliseconds
_FADE_MS = {
    "intro_to_explore": 2000,
    "explore_to_combat": 1500,
    "explore_madness": 2000,
    "combat_to_end": 2000,
    "boss_dramatic": 2500,
    "quick": 800,
}

# Sound file mapping: sound_name -> filename
_SOUND_FILES: Dict[str, str] = {
    "click": "BNA_UI28.wav",
    "confirm": "BNA_UI40.wav",
    "cancel": "BNA_UI44.wav",
    "error": "BNA_UI9.wav",
    "game_over": "BNA_UI29.wav",
    "level_up": "BNA_UI25.wav",
    "transition": "BNA_UI13_Long3.wav",
    "boss_start": "BNA_UI13_Long4.wav",
    "loot": "BNA_UI11.wav",
    "equip": "Unholy_Souls_13.wav",
    "purchase": "BNA_UI12.wav",
    "combat_start": "mixkit-horror-swish-1495.wav",
    "event_mystery": "Creepy_ambience_3.wav",
    "trap_trigger": "Stinger.wav",
}

# Procedural fallback parameters: (frequency_hz, duration_sec, sweep_factor)
_FALLBACK_PARAMS: Dict[str, tuple] = {
    "click": (800, 0.05, 1.0),
    "confirm": (400, 0.10, 0.9),
    "cancel": (300, 0.08, 0.6),
    "error": (120, 0.20, 0.5),
    "game_over": (80, 0.50, 0.4),
    "level_up": (600, 0.35, 1.8),
    "transition": (200, 0.30, 1.5),
    "boss_start": (60, 0.60, 0.3),
    "loot": (800, 0.10, 1.2),
    "equip": (1200, 0.15, 0.9),
    "purchase": (700, 0.12, 1.4),
    "combat_start": (80, 0.25, 0.4),
    "event_mystery": (150, 0.30, 0.7),
    "trap_trigger": (100, 0.25, 0.3),
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

        # ── Music state ───────────────────────────────────────────────────────
        self._music_volume = 0.5  # Current music volume (context-dependent)
        self._music_muted = False  # Music-specific mute
        self._current_music_ctx = None  # Currently playing music context
        self._shuffle_history: Dict[str, List[str]] = {}  # ctx -> last played track

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

    # ── Music API ──────────────────────────────────────────────────────────────

    def play_music(self, context: str, fade_ms: int = 1000) -> None:
        """Start background music for the given context.

        Parameters
        ----------
        context : str
            Music context: ``"intro"``, ``"explore_low"``, ``"explore_high"``,
            ``"combat"``, or ``"boss"``.
        fade_ms : int
            Fade-in duration in milliseconds (default 1000).
        """
        if self._muted or self._music_muted or not self._mixer_ready:
            return

        # Don't restart the same context if already playing
        if self._current_music_ctx == context and _mixer.music.get_busy():
            return

        tracks = _MUSIC_TRACKS.get(context)
        if not tracks:
            logger.debug("Unknown music context: %s", context)
            return

        # Fade out current track if switching contexts
        if self._current_music_ctx and self._current_music_ctx != context:
            try:
                if _mixer.music.get_busy():
                    _mixer.music.fadeout(min(fade_ms, 500))
            except Exception:
                pass

        # Pick a track (avoid repeating the last one if multiple tracks)
        if len(tracks) > 1:
            last = self._shuffle_history.get(context)
            candidates = [t for t in tracks if t != last] or tracks
            track = random.choice(candidates)
        else:
            track = tracks[0]
        self._shuffle_history[context] = track

        filepath = os.path.join(_MUSIC_DIR, track)
        if not os.path.exists(filepath):
            logger.debug("Music file not found: %s", filepath)
            return

        try:
            _mixer.music.load(filepath)
            vol = _MUSIC_VOLUMES.get(context, 0.5)
            self._music_volume = vol
            _mixer.music.set_volume(vol)
            _mixer.music.play(-1, fade_ms=fade_ms)  # -1 = loop forever
            self._current_music_ctx = context
            logger.info("Music: %s [%s] (vol=%.2f, fade=%dms)", context, track, vol, fade_ms)
        except Exception as e:
            logger.warning("play_music(%s) failed: %s", context, e)

    def stop_music(self, fade_ms: int = 1000) -> None:
        """Fade out and stop the current background music.

        Parameters
        ----------
        fade_ms : int
            Fade-out duration in milliseconds (default 1000).
        """
        if not self._mixer_ready:
            return
        try:
            if _mixer.music.get_busy():
                if fade_ms > 0:
                    _mixer.music.fadeout(fade_ms)
                    # Don't clear context during fadeout — play_music needs it
                    # to detect same-context restarts (e.g. flee combat → explore)
                else:
                    _mixer.music.stop()
                    self._current_music_ctx = None
                logger.debug("Music stopping (fade=%dms)", fade_ms)
            else:
                self._current_music_ctx = None
        except Exception as e:
            logger.debug("stop_music failed: %s", e)
            self._current_music_ctx = None

    def crossfade_music(self, context: str, fade_ms: int = 2000) -> None:
        """Crossfade from the current music to a new context.

        Stops the current track (fade-out) then starts the new one (fade-in).
        If nothing is playing, behaves like ``play_music()``.

        Parameters
        ----------
        context : str
            Target music context.
        fade_ms : int
            Total crossfade duration in milliseconds (split between out/in).
        """
        if self._current_music_ctx == context and _mixer.music.get_busy():
            return  # Already playing this context

        half_fade = max(fade_ms // 2, 100)
        self.stop_music(fade_ms=half_fade)
        # Small gap to let the fade complete before starting new track
        self.play_music(context, fade_ms=half_fade)

    def set_music_volume(self, volume: float) -> None:
        """Set the music volume (0.0 to 1.0)."""
        self._music_volume = max(0.0, min(1.0, volume))
        if _mixer.music:
            try:
                _mixer.music.set_volume(self._music_volume)
            except Exception:
                pass

    def get_music_volume(self) -> float:
        """Get current music volume."""
        return self._music_volume

    def mute_music(self) -> None:
        """Mute background music only (SFX still play)."""
        self._music_muted = True
        if _mixer.music:
            try:
                _mixer.music.set_volume(0)
            except Exception:
                pass

    def unmute_music(self) -> None:
        """Unmute background music."""
        self._music_muted = False
        if _mixer.music:
            try:
                _mixer.music.set_volume(self._music_volume)
            except Exception:
                pass

    @property
    def music_context(self) -> Optional[str]:
        """The currently active music context, or ``None``."""
        return self._current_music_ctx

    # ── Public API ────────────────────────────────────────────────────────────

    def play(self, name: str, volume: Optional[float] = None) -> None:
        """Play a named sound effect.

        Parameters
        ----------
        name : str
            Sound name: ``"click"``, ``"confirm"``, ``"cancel"``,
            ``"error"``, ``"game_over"``, ``"level_up"``,
            ``"transition"``, ``"boss_start"``, ``"loot"``, ``"equip"``,
            ``"purchase"``, ``"combat_start"``, ``"event_mystery"``,
            or ``"trap_trigger"``.
        volume : float, optional
            Per-play volume override (0.0 to 1.0). If None, uses master volume.
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
                vol = volume if volume is not None else self._master_volume
                channel.set_volume(max(0.0, min(1.0, vol)))
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
        """Mute all sounds (SFX + music)."""
        self._muted = True
        self.mute_music()

    def unmute(self) -> None:
        """Unmute all sounds (SFX + music)."""
        self._muted = False
        self.unmute_music()

    def toggle_mute(self) -> bool:
        """Toggle mute state. Returns new muted state."""
        self._muted = not self._muted
        if self._muted:
            self.mute_music()
        else:
            self.unmute_music()
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
        elif name == "loot":
            samples = self._gen_loot(n, sr)
        elif name == "equip":
            samples = self._gen_equip(n, sr)
        elif name == "purchase":
            samples = self._gen_purchase(n, sr)
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
            noise = random.uniform(-0.3, 0.3) * 8000 * envelope
            val = 8000 * envelope * math.sin(2 * math.pi * f * t) + noise
            samples.append(val)
        return samples

    @staticmethod
    def _gen_loot(n: int, sr: int) -> list:
        """Generate loot/coin clatter sound."""
        samples = []
        for i in range(n):
            t = i / sr
            progress = i / n
            envelope = (1.0 - progress) ** 3
            # Multiple short metallic taps at random pitches
            f = random.choice([1200, 1500, 1800, 2200])
            val = 8000 * envelope * math.sin(2 * math.pi * f * t)
            val += 4000 * envelope * math.sin(2 * math.pi * f * 1.7 * t)
            samples.append(val)
        return samples

    @staticmethod
    def _gen_equip(n: int, sr: int) -> list:
        """Generate metallic blade/equip sound."""
        samples = []
        for i in range(n):
            t = i / sr
            progress = i / n
            # Sharp attack, quick decay
            envelope = (1.0 - progress) ** 1.5
            # High metallic frequency with slight downward sweep
            f = 1800 - 400 * progress
            val = 12000 * envelope * math.sin(2 * math.pi * f * t)
            val += 6000 * envelope * math.sin(2 * math.pi * f * 2.3 * t)
            samples.append(val)
        return samples

    @staticmethod
    def _gen_purchase(n: int, sr: int) -> list:
        """Generate bubbly purchase/transaction chime."""
        samples = []
        for i in range(n):
            t = i / sr
            progress = i / n
            envelope = (1.0 - progress) ** 2
            # Rising bubbly pitch
            f = 600 + 600 * progress
            val = 8000 * envelope * math.sin(2 * math.pi * f * t)
            val += 4000 * envelope * math.sin(2 * math.pi * f * 1.5 * t)
            samples.append(val)
        return samples

    def __repr__(self) -> str:
        status = "muted" if self._muted else ("ready" if self._mixer_ready else "unavailable")
        music = f", music={self._current_music_ctx}" if self._current_music_ctx else ""
        return f"AudioManager({status}{music}, vol={self._master_volume:.1f})"

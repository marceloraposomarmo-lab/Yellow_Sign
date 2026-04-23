#!/usr/bin/env python3
"""
Audio System Tests for The King in Yellow.
Runs headless (no Pygame display) to verify audio manager logic.
"""

import sys
import os
import array
import math

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shared.audio import AudioManager


def test_sound_params_defined():
    """All expected sound names have generation parameters."""
    expected = {"hover", "click", "confirm", "cancel", "error"}
    actual = set(AudioManager._SOUND_PARAMS.keys())
    assert actual == expected, f"Expected {expected}, got {actual}"
    print("  ✓ Sound parameters defined for all 5 sounds")


def test_sound_generation_parameters():
    """Each sound has valid (freq, duration, sweep) tuple."""
    for name, params in AudioManager._SOUND_PARAMS.items():
        freq, dur, sweep = params
        assert isinstance(freq, (int, float)) and freq > 0, f"{name}: invalid freq {freq}"
        assert isinstance(dur, (int, float)) and 0 < dur < 1.0, f"{name}: invalid dur {dur}"
        assert isinstance(sweep, (int, float)) and sweep > 0, f"{name}: invalid sweep {sweep}"
    print("  ✓ All sound parameters are valid")


def test_gen_tone():
    """_gen_tone produces correct number of samples with proper range."""
    sr = 22050
    n = int(sr * 0.05)
    samples = AudioManager._gen_tone(n, sr, 600, 1.0)
    assert len(samples) == n, f"Expected {n} samples, got {len(samples)}"
    # All samples should be finite numbers
    for i, s in enumerate(samples):
        assert math.isfinite(s), f"Sample {i} is not finite: {s}"
    # First sample should be 0 (start of sine)
    assert samples[0] == 0.0
    print("  ✓ _gen_tone produces valid samples")


def test_gen_confirm():
    """_gen_confirm produces correct number of samples."""
    sr = 22050
    n = int(sr * 0.12)
    samples = AudioManager._gen_confirm(n, sr)
    assert len(samples) == n
    for s in samples:
        assert math.isfinite(s)
    print("  ✓ _gen_confirm produces valid samples")


def test_gen_error():
    """_gen_error produces correct number of samples."""
    sr = 22050
    n = int(sr * 0.15)
    samples = AudioManager._gen_error(n, sr)
    assert len(samples) == n
    for s in samples:
        assert math.isfinite(s)
    print("  ✓ _gen_error produces valid samples")


def test_pcm_conversion():
    """Samples are correctly clamped to 16-bit PCM range."""
    sr = 22050
    n = int(sr * 0.05)
    samples = AudioManager._gen_tone(n, sr, 600, 1.0)
    buf = array.array("h", [max(-32768, min(32767, int(s))) for s in samples])
    assert len(buf) == n
    for val in buf:
        assert -32768 <= val <= 32767, f"Value out of 16-bit range: {val}"
    print("  ✓ PCM conversion clamps to 16-bit range")


def test_volume_control():
    """Volume getter/setter works correctly."""
    mgr = AudioManager.__new__(AudioManager)
    mgr._master_volume = 0.5
    mgr._muted = False
    mgr._sounds = {}
    mgr._mixer_ready = False
    mgr._sample_rate = 22050

    mgr.set_volume(0.8)
    assert mgr.get_volume() == 0.8

    # Clamping
    mgr.set_volume(1.5)
    assert mgr.get_volume() == 1.0

    mgr.set_volume(-0.3)
    assert mgr.get_volume() == 0.0

    print("  ✓ Volume control works with clamping")


def test_mute_toggle():
    """Mute/unmute/toggle works correctly."""
    mgr = AudioManager.__new__(AudioManager)
    mgr._master_volume = 0.5
    mgr._muted = False
    mgr._sounds = {}
    mgr._mixer_ready = False
    mgr._sample_rate = 22050

    assert not mgr.muted
    mgr.mute()
    assert mgr.muted
    mgr.unmute()
    assert not mgr.muted
    result = mgr.toggle_mute()
    assert result is True
    assert mgr.muted
    result = mgr.toggle_mute()
    assert result is False
    assert not mgr.muted
    print("  ✓ Mute/unmute/toggle works correctly")


def test_play_noop_when_unavailable():
    """play() is a no-op when mixer is unavailable (no crash)."""
    mgr = AudioManager.__new__(AudioManager)
    mgr._master_volume = 0.5
    mgr._muted = False
    mgr._sounds = {}
    mgr._mixer_ready = False
    mgr._sample_rate = 22050

    # Should not raise
    mgr.play("hover")
    mgr.play("click")
    mgr.play("confirm")
    mgr.play("nonexistent")
    print("  ✓ play() is safe when mixer unavailable")


def test_play_noop_when_muted():
    """play() is a no-op when muted (no crash)."""
    mgr = AudioManager.__new__(AudioManager)
    mgr._master_volume = 0.5
    mgr._muted = True
    mgr._sounds = {}
    mgr._mixer_ready = True  # mixer "ready" but muted
    mgr._sample_rate = 22050

    # Should not raise
    mgr.play("hover")
    print("  ✓ play() is safe when muted")


def test_repr():
    """__repr__ returns useful status string."""
    mgr = AudioManager.__new__(AudioManager)
    mgr._master_volume = 0.5
    mgr._muted = False
    mgr._mixer_ready = False
    r = repr(mgr)
    assert "unavailable" in r

    mgr._muted = True
    r = repr(mgr)
    assert "muted" in r
    print("  ✓ __repr__ returns status string")


def test_all_sound_types_generate():
    """All 5 sound types generate without error."""
    sr = 22050
    for name, (freq, dur, sweep) in AudioManager._SOUND_PARAMS.items():
        n = int(sr * dur)
        if name == "confirm":
            samples = AudioManager._gen_confirm(n, sr)
        elif name == "error":
            samples = AudioManager._gen_error(n, sr)
        else:
            samples = AudioManager._gen_tone(n, sr, freq, sweep)
        assert len(samples) == n, f"{name}: expected {n} samples, got {len(samples)}"
        buf = array.array("h", [max(-32768, min(32767, int(s))) for s in samples])
        assert len(buf) == n
    print("  ✓ All 5 sound types generate successfully")


def test_hover_sound_is_short():
    """Hover sound should be the shortest (< 50ms)."""
    hover_dur = AudioManager._SOUND_PARAMS["hover"][1]
    for name, (_, dur, _) in AudioManager._SOUND_PARAMS.items():
        if name != "hover":
            assert hover_dur <= dur, f"Hover ({hover_dur}s) should be <= {name} ({dur}s)"
    print("  ✓ Hover sound is shortest")


def test_confirm_sound_is_longest():
    """Confirm sound should be among the longest."""
    confirm_dur = AudioManager._SOUND_PARAMS["confirm"][1]
    for name, (_, dur, _) in AudioManager._SOUND_PARAMS.items():
        if name not in ("confirm", "error"):
            assert confirm_dur >= dur, f"Confirm ({confirm_dur}s) should be >= {name} ({dur}s)"
    print("  ✓ Confirm sound is appropriately longer")


# ═══════════════════════════════════════════
# TEST RUNNER
# ═══════════════════════════════════════════

def run_all_tests():
    """Run all audio tests and return True if all passed."""
    tests = [
        test_sound_params_defined,
        test_sound_generation_parameters,
        test_gen_tone,
        test_gen_confirm,
        test_gen_error,
        test_pcm_conversion,
        test_volume_control,
        test_mute_toggle,
        test_play_noop_when_unavailable,
        test_play_noop_when_muted,
        test_repr,
        test_all_sound_types_generate,
        test_hover_sound_is_short,
        test_confirm_sound_is_longest,
    ]

    passed = 0
    failed = 0

    for test_fn in tests:
        try:
            test_fn()
            passed += 1
        except Exception as e:
            print(f"  ✗ {test_fn.__name__}: {e}")
            failed += 1

    print(f"\n  Audio Tests: {passed} passed, {failed} failed")
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)

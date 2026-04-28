# 🎵 Soundtrack Integration Plan — The King in Yellow

## Audio File Analysis

All tracks: **MP3, 48kbps, 44.1kHz, Mono** — consistent format, lightweight.

| # | File | Duration | RMS Level | Peak dB | Dynamic Range | Character |
|---|------|----------|-----------|---------|---------------|-----------|
| 1 | `Game_Intro_Song.mp3` | **2:58** | -15.5 dB | -0.4 dB | 292 | **Cinematic opener** — sets the Lovecraftian tone, grand and atmospheric |
| 2 | `Exploration_Low_Madness_1.mp3` | **2:55** | -15.1 dB | -0.4 dB | 294 | **Calm dread** — eerie but controlled, wandering through unknown halls |
| 3 | `Exploration_Low_Madness_2.mp3` | **2:57** | -15.1 dB | +0.6 dB | 386 | **Uneasy calm** — slightly more dynamic, still restrained |
| 4 | `Exploration_High_Madness_1.mp3` | **2:29** | -15.1 dB | +0.2 dB | 302 | **Fractured psyche** — shorter, more intense, distorted reality |
| 5 | `Combat_1.mp3` | **2:36** | -15.1 dB | -0.6 dB | 284 | **Standard combat** — driving, tense, reliable loop |
| 6 | `Combat_2.mp3` | **2:32** | -15.2 dB | -0.1 dB | 300 | **Escalated combat** — higher dynamic range, more variance |
| 7 | `Combat_3.mp3` | **1:56** | -15.5 dB | -0.2 dB | 280 | **Intense burst** — shortest combat track, fast-paced |
| 8 | `Combat_4.mp3` | **2:29** | -15.4 dB | +0.2 dB | 272 | **Boss-tier combat** — loudest peak, most compressed, relentless |

---

## 🎯 Track → Game Context Mapping

### 1. `Game_Intro_Song.mp3` → **Title Screen + Class Select**
- **Screens**: `TitleScreen`, `ClassSelectScreen`
- **Behavior**: Loop continuously across both screens. Stop when gameplay begins (explore screen enter).
- **Volume**: 0.5 (moderate — don't overwhelm on first launch)
- **User-confirmed**: ✅

### 2-3. `Exploration_Low_Madness_1/2.mp3` → **Explore Screen (Madness < 50)**
- **Screen**: `ExploreScreen`
- **Behavior**: Shuffle between the two tracks. Loop the current track, pick the other one next time.
- **Trigger**: Player madness < 50
- **Volume**: 0.35 (ambient, lower than SFX)
- **Crossfade**: When switching from high→low madness, crossfade over ~2s

### 4. `Exploration_High_Madness_1.mp3` → **Explore Screen (Madness ≥ 50)**
- **Screen**: `ExploreScreen`
- **Behavior**: Loop. Interrupts low-madness track when threshold crossed.
- **Trigger**: Player madness ≥ 50
- **Volume**: 0.45 (slightly louder — the madness is palpable)
- **Crossfade**: When crossing 50 threshold, crossfade from low→high over ~2s

### 5-7. `Combat_1/2/3.mp3` → **Combat Screen (Normal Enemies)**
- **Screen**: `CombatScreen`
- **Behavior**: Random selection per combat encounter. Loop for the duration of the fight.
- **Trigger**: Entering combat against non-boss enemies
- **Volume**: 0.5 (combat needs energy)
- **Transition**: Fade out exploration music (1s) → fade in combat music (0.5s)

### 8. `Combat_4.mp3` → **Boss Combat**
- **Screen**: `CombatScreen`
- **Behavior**: Always plays for boss encounters. Loop.
- **Trigger**: `is_boss == True` in combat state
- **Volume**: 0.6 (boss fights are the climax)
- **Transition**: Fade out exploration (0.5s) → dramatic pause (0.3s) → boss_start SFX → fade in Combat_4 (1s)

### Screen Transitions (No Music)
- **Shop, Rest, Loot, Event, Trap, Inventory, Level Up, Save/Load, Stats**: No background music — use existing UI SFX only. These are brief tactical screens.
- **Game Over**: Fade out combat music (2s) → silence → game_over SFX
- **Victory**: Fade out combat music (1.5s) → brief silence → victory SFX

---

## 🔧 Technical Implementation Plan

### New in `shared/audio.py`:
1. **Music track registry** — maps context → list of MP3 files
2. **`play_music(context, loop=True)`** — starts background music for a context
3. **`stop_music(fade_ms=1000)`** — fades out current music
4. **`crossfade_music(context, fade_ms=2000)`** — smooth transition between tracks
5. **`set_music_volume(vol)`** — separate volume control for music vs SFX
6. **Music state tracking** — current context, current track, shuffle history

### New in `screens/base.py`:
1. **`play_music_for(context)`** — helper that screens call
2. **`stop_music()`** — helper for fadeout

### Screen integration points:
- `TitleScreen.enter()` → `play_music("intro")`
- `ClassSelectScreen.enter()` → music continues (same context)
- `ExploreScreen.enter()` → `play_music("explore_low" or "explore_high")` based on madness
- `ExploreScreen.update()` → check madness threshold, crossfade if crossed
- `CombatScreen.enter()` → `play_music("combat" or "boss")` based on enemy type
- `CombatScreen` victory/gameover → `stop_music(fade_ms=2000)`

### Madness Threshold Logic:
```python
# In ExploreScreen.update():
if self._prev_madness_zone != self._current_madness_zone:
    if madness >= 50:
        self.ctx.audio.crossfade_music("explore_high", fade_ms=2000)
    else:
        self.ctx.audio.crossfade_music("explore_low", fade_ms=2000)
```

---

## 📊 Summary

| Context | Track(s) | Volume | Loop | Crossfade |
|---------|----------|--------|------|-----------|
| Title + Class Select | Game_Intro_Song | 0.5 | ✅ | — |
| Explore (MAD < 50) | Low_Madness_1, Low_Madness_2 | 0.35 | ✅ | 2s on swap |
| Explore (MAD ≥ 50) | High_Madness_1 | 0.45 | ✅ | 2s from low |
| Combat (normal) | Combat_1, Combat_2, Combat_3 | 0.5 | ✅ | 1.5s from explore |
| Combat (boss) | Combat_4 | 0.6 | ✅ | 2s dramatic |
| Game Over | (fade to silence) | — | — | 2s fadeout |
| Victory | (fade to silence) | — | — | 1.5s fadeout |

---

*~~Ready for implementation in next prompt.~~* **IMPLEMENTED** — commit `902f47e`

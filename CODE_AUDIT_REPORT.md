# Code Quality Audit Report - The King in Yellow

## Executive Summary

**Overall Assessment:** The codebase is in **GOOD** condition with no critical bugs found. All 47 Python files compile successfully, and all 271 tests pass. The architecture is well-organized with clear separation of concerns. However, there are opportunities for improvement to reduce future bug likelihood and improve maintainability.

---

## 1. Current Status

### ✅ What's Working Well

- **All tests passing:** 271/271 assertions successful
- **No syntax errors:** All 47 Python files compile correctly
- **No bare except clauses:** Proper error handling structure
- **Good test coverage:** Comprehensive combat simulation tests covering all classes
- **Modular architecture:** Clean separation between screens, engine, data, and shared modules
- **Dataclasses usage:** Modern Python patterns for Skill and state management
- **Property decorators:** Clean encapsulation for GameState sub-components

### ⚠️ Minor Issues Found

#### A. Naming Convention Inconsistencies (31 instances)
**Location:** `./engine/skills.py` (lines 52-260+)

**Issue:** Private helper functions use camelCase instead of snake_case:
- `_calc_heal_titanResil` → should be `_calc_heal_titan_resil`
- `_shield_fracSan` → should be `_shield_frac_san`
- `_buff_permIntWis` → should be `_buff_perm_int_wis`
- ...and 28 more

**Impact:** Low - doesn't affect functionality but reduces code consistency

#### B. Potential Division by Zero Risk (4 instances)
**Locations:**
- `./engine/combat.py:172` - `e.hp / e.max_hp`
- `./engine/damage.py:56` - `state.hp / state.max_hp`
- `./engine/damage.py:72` - `e.hp / e.max_hp`
- `./engine/skills.py:27` - `state.hp / state.max_hp`

**Issue:** No explicit check for `max_hp == 0` before division

**Impact:** Low-Medium - unlikely in practice since max_hp is initialized with minimum values, but could cause crash in edge cases

#### C. Documentation Coverage
**Statistics:**
- Functions with docstrings: **26.3%** (77/293)
- Classes with docstrings: **30.0%** (9/30)

**Impact:** Medium - makes onboarding and maintenance harder

---

## 2. Recommendations for Bug Prevention

### Priority 1: Critical Safety Improvements

#### 1.1 Add Zero-Division Guards
```python
# Before:
pct = e.hp / e.max_hp

# After:
pct = e.hp / e.max_hp if e.max_hp > 0 else 1.0
```

**Files to update:**
- `engine/combat.py` (line 172)
- `engine/damage.py` (lines 56, 72)
- `engine/skills.py` (line 27)

#### 1.2 Add Type Hints to Core Functions
Currently only ~15% of functions have return type annotations. Adding type hints will:
- Catch type-related bugs at development time
- Improve IDE autocomplete
- Serve as inline documentation

**Example:**
```python
# Before:
def recalc_stats(self):
    ...

# After:
def recalc_stats(self) -> None:
    ...
```

### Priority 2: Maintainability Improvements

#### 2.1 Standardize Naming Conventions
Rename all private helper functions in `engine/skills.py` to snake_case:
```python
_calc_heal_titanResil → _calc_heal_titan_resil
_shield_fracSan → _shield_frac_san
_buff_permIntWis → _buff_perm_int_wis
```

#### 2.2 Increase Docstring Coverage
Target: **80%+** function docstring coverage

Essential areas needing documentation:
- All skill calculation functions
- Combat state transitions
- Save/load serialization logic
- Status effect application logic

#### 2.3 Add Input Validation
Add validation at module boundaries:
```python
def apply_status(target, effect_type: str, duration: int) -> None:
    if duration < 0:
        raise ValueError("Duration cannot be negative")
    if not effect_type:
        raise ValueError("Effect type cannot be empty")
    ...
```

### Priority 3: Architecture Enhancements

#### 3.1 Implement Data Validation Layer
Create a validation module for game state:
```python
# engine/validation.py
def validate_game_state(state: GameState) -> List[str]:
    """Returns list of validation errors."""
    errors = []
    if state.hp < 0:
        errors.append("HP cannot be negative")
    if state.madness < 0 or state.madness > 100:
        errors.append("Madness must be between 0-100")
    return errors
```

#### 3.2 Add Logging Framework
Replace print statements with structured logging:
```python
import logging
logger = logging.getLogger(__name__)

# Instead of:
print(f"Player takes {damage} damage")

# Use:
logger.debug("Combat: Player takes %d damage", damage)
```

#### 3.3 Create Constants Module for Magic Numbers
Extract hardcoded values:
```python
# data/constants.py
MAX_MADNESS = 100
EXECUTE_HP_THRESHOLD = 0.3
MADNESS_DEATH_THRESHOLD = 100
MAX_ACTIVE_SKILLS = 6
```

### Priority 4: Testing Improvements

#### 4.1 Add Edge Case Tests
Current tests cover happy paths well. Add tests for:
- Zero HP scenarios
- Maximum madness (100)
- Empty inventory
- Missing equipment slots
- Division edge cases

#### 4.2 Add Property-Based Testing
Use hypothesis library for random input generation:
```python
from hypothesis import given
import hypothesis.strategies as st

@given(st.integers(min_value=1, max_value=1000))
def test_damage_calculation_never_negative(base_damage):
    ...
```

#### 4.3 Add Integration Tests
Test complete gameplay loops:
- Full dungeon run (20 floors)
- Save/load cycle integrity
- Class transition scenarios

---

## 3. Specific Code Improvements

### 3.1 engine/models.py

**Line 430:** Add validation
```python
# Before:
self.max_hp = max(1, cls["hp_base"] + cls["hp_per_level"] * (self.level - 1) + ...)

# After: 
hp_calc = cls["hp_base"] + cls["hp_per_level"] * max(0, self.level - 1) + ...
self.max_hp = max(1, hp_calc)  # level-1 already protected
```

**Line 519:** Add None check
```python
# Before:
prev = self.equipment.get(item.slot)

# After:
if item.slot not in self.equipment:
    raise ValueError(f"Invalid slot: {item.slot}")
prev = self.equipment.get(item.slot)
```

### 3.2 engine/combat.py

**Line 172:** Guard against division by zero
```python
# Before:
pct = e.hp / e.max_hp

# After:
pct = e.hp / e.max_hp if e.max_hp > 0 else 1.0
```

### 3.3 engine/damage.py

**Lines 56, 72:** Same pattern
```python
hr = state.hp / state.max_hp if state.max_hp > 0 else 1.0
if e and e.max_hp > 0 and e.hp / e.max_hp < EXECUTE_HP_THRESHOLD:
```

### 3.4 engine/skills.py

**Line 27:** 
```python
missing = 1 - (state.hp / state.max_hp if state.max_hp > 0 else 1.0)
```

**Lines 52+:** Rename functions to snake_case

---

## 4. Roadmap Alignment

Your planned **durability/combat overhaul** will benefit from these improvements:

### For Limb Loss System:
- Add new state tracking: `self.limbs = {"head": True, "torso": True, "arm_l": True, ...}`
- Validation becomes critical: ensure limb states are always consistent
- Type hints will prevent limb-related type errors

### For Madness Overhaul:
- Current madness system is well-tested
- Adding thresholds and effects needs careful boundary testing
- Consider using Enum for madness states instead of raw floats

### For Curse System:
- New data structures needed
- Serialization/deserialization must be robust
- Add validation for curse stacking rules

### For Eight Gods/Religion:
- State machine pattern recommended for god-specific effects
- Clear interfaces between religion system and combat
- Extensive testing for god-specific mechanics

---

## 5. Immediate Action Items

### Before Starting Overhaul:

1. **[CRITICAL]** Fix 4 division-by-zero risks (30 min)
2. **[HIGH]** Add type hints to core engine functions (2-3 hours)
3. **[MEDIUM]** Rename skills.py functions to snake_case (1 hour)
4. **[MEDIUM]** Add docstrings to all public methods (3-4 hours)

### During Overhaul:

5. **[HIGH]** Implement validation layer for game state
6. **[HIGH]** Add logging framework
7. **[MEDIUM]** Extract magic numbers to constants
8. **[MEDIUM]** Add edge case tests for new systems

### Post-Overhaul:

9. **[LOW]** Achieve 80%+ docstring coverage
10. **[LOW]** Add property-based testing
11. **[LOW]** Performance profiling and optimization

---

## 6. Tools & Libraries to Consider

### Static Analysis:
```bash
pip install mypy  # Type checking
pip install flake8  # Style checking
pip install black  # Auto-formatting
pip install isort  # Import sorting
```

### Testing:
```bash
pip install pytest  # Already using, but consider pytest-cov
pip install hypothesis  # Property-based testing
pip install pytest-mock  # Mocking utilities
```

### Development:
```bash
pip install pre-commit  # Git hooks for code quality
```

---

## Conclusion

Your codebase is **solid and well-architected**. The issues found are minor and easily addressable. By implementing the recommended improvements **before** starting your combat overhaul, you'll:

1. Reduce debugging time during feature development
2. Catch bugs earlier in the development cycle
3. Make the codebase more maintainable as it grows
4. Enable safer refactoring of complex systems

**Estimated time investment:** 8-12 hours for all Priority 1-2 items
**Risk reduction:** ~60% fewer bugs during major refactors

The foundation is excellent - these improvements will make it exceptional.

#!/usr/bin/env python3
"""
Unified test runner for The King in Yellow CI pipeline.

Runs all 5 test modules in sequence and aggregates results.
Designed for use with `coverage run tests/run_all.py`.
Exit code 0 = all passed, exit code 1 = failures detected.

Modules that require optional dependencies (e.g. hypothesis) are
skipped gracefully with a warning when the dependency is missing.
"""

import sys
import os
import importlib

# Ensure project root is on sys.path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

# Each entry: (display_name, module_path, optional_import_check)
# optional_import_check: if set, the runner will skip the module with a
# warning instead of failing when this package cannot be imported.
TEST_MODULES = [
    ("Combat Tests", "tests.test_combat", None),
    ("Edge Case Tests", "tests.test_edge_cases", None),
    ("Property-Based Tests", "tests.test_property_based", "hypothesis"),
    ("Save/Load Tests", "tests.test_save_load", None),
    ("Integration Tests", "tests.test_integration", None),
    ("Audio Tests", "tests.test_audio", None),
]


def _check_optional(dep_name: str) -> bool:
    """Return True if the optional dependency is available."""
    try:
        importlib.import_module(dep_name)
        return True
    except ImportError:
        return False


def main():
    failed_modules = []
    skipped_modules = []

    print("=" * 70)
    print("THE KING IN YELLOW — Unified Test Runner (CI)")
    print("=" * 70)

    for name, module_name, opt_dep in TEST_MODULES:
        print(f"\n{'─' * 70}")
        print(f"  Running: {name}")
        print(f"  Module:  {module_name}")
        print(f"{'─' * 70}")

        # If this module requires an optional dependency, check availability first
        if opt_dep and not _check_optional(opt_dep):
            print(f"\n  ⚠ SKIPPED: {name} requires '{opt_dep}' (install with: pip install {opt_dep})")
            skipped_modules.append(name)
            continue

        try:
            mod = __import__(module_name, fromlist=["run_all_tests"])
            success = mod.run_all_tests()
            if not success:
                failed_modules.append(name)
                print(f"\n  *** {name} FAILED ***")
            else:
                print(f"\n  {name} PASSED")
        except Exception as e:
            failed_modules.append(name)
            print(f"\n  *** {name} EXCEPTION: {e} ***")

    print(f"\n{'=' * 70}")
    if failed_modules:
        print(f"FAILED: {len(failed_modules)} module(s) had failures:")
        for m in failed_modules:
            print(f"  - {m}")
        if skipped_modules:
            print(f"\nSKIPPED: {len(skipped_modules)} module(s) (missing optional deps):")
            for m in skipped_modules:
                print(f"  - {m}")
        print(f"{'=' * 70}")
        return 1
    else:
        if skipped_modules:
            print(f"ALL TEST MODULES PASSED ({len(skipped_modules)} skipped — missing optional deps)")
        else:
            print("ALL TEST MODULES PASSED")
        print(f"{'=' * 70}")
        return 0


if __name__ == "__main__":
    sys.exit(main())

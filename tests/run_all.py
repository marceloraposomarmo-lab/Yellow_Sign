#!/usr/bin/env python3
"""
Unified test runner for The King in Yellow CI pipeline.

Runs all 5 test modules in sequence and aggregates results.
Designed for use with `coverage run tests/run_all.py`.
Exit code 0 = all passed, exit code 1 = failures detected.
"""

import sys
import os

# Ensure project root is on sys.path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

TEST_MODULES = [
    ("Combat Tests", "tests.test_combat"),
    ("Edge Case Tests", "tests.test_edge_cases"),
    ("Property-Based Tests", "tests.test_property_based"),
    ("Save/Load Tests", "tests.test_save_load"),
    ("Integration Tests", "tests.test_integration"),
]


def main():
    failed_modules = []

    print("=" * 70)
    print("THE KING IN YELLOW — Unified Test Runner (CI)")
    print("=" * 70)

    for name, module_name in TEST_MODULES:
        print(f"\n{'─' * 70}")
        print(f"  Running: {name}")
        print(f"  Module:  {module_name}")
        print(f"{'─' * 70}")

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
        print(f"{'=' * 70}")
        return 1
    else:
        print("ALL TEST MODULES PASSED")
        print(f"{'=' * 70}")
        return 0


if __name__ == "__main__":
    sys.exit(main())

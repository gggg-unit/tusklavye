"""Standalone test runner for the typing tutor test suite (no pytest required)."""
from __future__ import annotations

import inspect
import os
import sys
import tempfile
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from src.core.keyboard_layout import KeyboardLayout
from src.core.typing_engine import TypingEngine
from src.database.db import Database
from src.database.models import (
    StatsRepository,
    LessonRepository,
    AchievementRepository,
    SettingsRepository,
)


def make_fixtures():
    tmpdir = Path(tempfile.mkdtemp(prefix="tt_test_"))
    db_path = tmpdir / "test.db"
    db = Database.reset(db_path)
    return {
        "layout": KeyboardLayout(),
        "engine": TypingEngine(),
        "db": db,
        "stats_repo": StatsRepository(db),
        "lesson_repo": LessonRepository(db),
        "achievement_repo": AchievementRepository(db),
        "settings_repo": SettingsRepository(db),
    }


def teardown_fixtures(fixtures):
    try:
        fixtures["db"].close()
    except Exception:
        pass
    Database._instance = None


def run_module(module_name):
    mod = __import__(module_name, fromlist=["*"])
    passed = 0
    failed = 0
    errors = []
    for name, obj in sorted(vars(mod).items()):
        if not name.startswith("test_"):
            continue
        if not callable(obj):
            continue
        sig = inspect.signature(obj)
        fixtures = make_fixtures()
        kwargs = {}
        ok = True
        for pname in sig.parameters:
            if pname in fixtures:
                kwargs[pname] = fixtures[pname]
            else:
                ok = False
                errors.append(f"  {name}: unknown fixture '{pname}'")
                failed += 1
                break
        if not ok:
            teardown_fixtures(fixtures)
            continue
        try:
            obj(**kwargs)
            passed += 1
        except Exception:
            failed += 1
            errors.append(f"  {name} FAILED:\n{traceback.format_exc()}")
        finally:
            teardown_fixtures(fixtures)
    return passed, failed, errors


def main():
    test_modules = [
        "tests.test_keyboard_layout",
        "tests.test_typing_engine",
        "tests.test_lessons",
        "tests.test_db",
        "tests.test_streak",
        "tests.test_achievements",
        "tests.test_settings",
        "tests.test_combine_result",
        "tests.test_migrations",
        "tests.test_texts",
    ]

    total_passed = 0
    total_failed = 0
    all_errors = []

    for mod_name in test_modules:
        p, f, errs = run_module(mod_name)
        total_passed += p
        total_failed += f
        all_errors.extend(errs)
        status = "OK" if f == 0 else "FAIL"
        print(f"[{status}] {mod_name}: {p} passed, {f} failed")

    print(f"\nTotal: {total_passed} passed, {total_failed} failed")
    if all_errors:
        print("\n--- Failures ---")
        for e in all_errors:
            print(e)
    return 0 if total_failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
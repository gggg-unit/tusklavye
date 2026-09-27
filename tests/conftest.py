"""Pytest fixtures for the typing tutor test suite."""
from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

import pytest

# Ensure src is importable
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


@pytest.fixture
def tmp_db_path(tmp_path):
    """Return a path for a temporary SQLite database file."""
    return tmp_path / "test.db"


@pytest.fixture
def db(tmp_db_path):
    """Yield a fresh Database singleton backed by a temp file."""
    from src.database.db import Database
    database = Database.reset(tmp_db_path)
    yield database
    try:
        database.close()
    except Exception:
        pass
    Database._instance = None


@pytest.fixture
def stats_repo(db):
    from src.database.models import StatsRepository
    return StatsRepository(db)


@pytest.fixture
def lesson_repo(db):
    from src.database.models import LessonRepository
    return LessonRepository(db)


@pytest.fixture
def achievement_repo(db):
    from src.database.models import AchievementRepository
    return AchievementRepository(db)


@pytest.fixture
def settings_repo(db):
    from src.database.models import SettingsRepository
    return SettingsRepository(db)


@pytest.fixture
def engine():
    from src.core.typing_engine import TypingEngine
    return TypingEngine()


@pytest.fixture
def layout():
    from src.core.keyboard_layout import KeyboardLayout
    return KeyboardLayout()
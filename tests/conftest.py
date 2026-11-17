"""Pytest fixtures for the typing tutor test suite."""
from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("PYTEST_QT_API", "pyside6")

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

@pytest.fixture
def app_window(qtbot, db, monkeypatch):
    """Use a temp SQLite singleton and real Qt widgets, with sound output disabled."""
    from src.core.sound import SoundManager
    from src.ui.main_window import MainWindow

    monkeypatch.setattr(SoundManager, "_init_sounds", lambda self: None)
    window = MainWindow()
    qtbot.addWidget(window)
    window.show()
    yield window
    # Avoid creating pending-session records or modal dialogs during fixture cleanup.
    for page in window.pages.values():
        engine = getattr(page, "engine", None)
        if engine is not None:
            engine.reset("")
        if hasattr(page, "pause_page"):
            page.pause_page()
    window.close()

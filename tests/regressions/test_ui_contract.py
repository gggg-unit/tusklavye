"""Exercise production Qt pages, never a copied FakeTestsPage implementation."""
import json
import sqlite3
from copy import deepcopy

from PySide6.QtWidgets import QFileDialog, QLabel, QMessageBox

from src.core.typing_engine import TypingResult
from src.database.models import SessionRecord
from src.ui.widgets.results_dialog import ResultsDialog


def record():
    return SessionRecord(
        mode="test", mode_detail="60s", text_content="abc",
        total_chars=3, correct_chars=3, incorrect_chars=0,
        wpm=42, raw_wpm=42, accuracy=100, max_wpm=42,
        key_counts={"a": {"correct": 1, "incorrect": 0}},
        started_at="2026-01-01T00:00:00",
    )


def test_combine_does_not_mutate_accumulator(app_window):
    page = app_window.pages["tests"]
    page._start_test_with_text("abc")
    page._acc_key_counts = {"a": {"correct": 1, "incorrect": 0}}
    before = deepcopy(page._acc_key_counts)
    current = TypingResult(key_counts={"a": {"correct": 1, "incorrect": 0}})
    page._combine_result(current)
    assert page._acc_key_counts == before


def test_timeout_then_close_persists_once(app_window, monkeypatch, tmp_db_path):
    monkeypatch.setattr(ResultsDialog, "exec", lambda self: 0)
    page = app_window.pages["tests"]
    page._start_test_with_text("abcdef")
    page.on_key_press("a")
    page._remaining_seconds = 0
    page._force_finish()
    assert app_window.ctx.stats_repo.get_session_count() == 1
    app_window.close()
    with sqlite3.connect(tmp_db_path) as conn:
        assert conn.execute("SELECT COUNT(*) FROM sessions").fetchone()[0] == 1


def test_save_error_shows_warning(app_window, monkeypatch):
    shown = []
    monkeypatch.setattr(QMessageBox, "warning", lambda *args: shown.append(args))
    app_window.pages["training"]._show_save_error(RuntimeError("test-only failure"))
    assert len(shown) == 1


def test_backup_restores_progress_and_key_stats(app_window, monkeypatch, tmp_path):
    ctx = app_window.ctx
    ctx.stats_repo.save_session(record())
    ctx.lesson_repo.mark_completed("L01", 42, 100)
    ctx.achievement_repo.unlock("first_session")
    backup = tmp_path / "backup.json"
    monkeypatch.setattr(QFileDialog, "getSaveFileName", lambda *a: (str(backup), "JSON"))
    monkeypatch.setattr(QFileDialog, "getOpenFileName", lambda *a: (str(backup), "JSON"))
    warnings = []
    monkeypatch.setattr(QMessageBox, "warning", lambda *a: warnings.append(a))
    page = app_window.pages["settings"]
    page._export_data()
    assert backup.is_file()
    expected = {
        table: [dict(row) for row in ctx.stats_repo.db.query("SELECT * FROM " + table)]
        for table in ("lesson_progress", "achievements", "key_stats", "streak")
    }
    for table in ("key_stats", "sessions", "lesson_progress", "achievements", "streak"):
        ctx.stats_repo.db.execute("DELETE FROM " + table)
    page._import_data()
    actual = {
        table: [dict(row) for row in ctx.stats_repo.db.query("SELECT * FROM " + table)]
        for table in expected
    }
    # IDs are implementation details; compare the user-facing per-key aggregates.
    for rows in (expected["key_stats"], actual["key_stats"]):
        for row in rows:
            row.pop("id", None)
            row.pop("session_id", None)
    assert not warnings
    assert actual == expected


def test_import_preserves_dates_and_duration(app_window, monkeypatch, tmp_path):
    row = vars(record()) | {
        "finished_at": "2026-01-01T00:01:00", "duration_seconds": 60,
    }
    backup = tmp_path / "historical.json"
    backup.write_text(json.dumps({"sessions": [row]}), encoding="utf-8")
    monkeypatch.setattr(QFileDialog, "getOpenFileName", lambda *a: (str(backup), "JSON"))
    app_window.pages["settings"]._import_data()
    restored = app_window.ctx.stats_repo.get_recent_sessions()[0]
    assert (restored["finished_at"], restored["duration_seconds"]) == (
        row["finished_at"], 60,
    )


def test_statistics_summary_refreshes(app_window):
    app_window.ctx.stats_repo.save_session(record())
    page = app_window.pages["stats"]
    page.refresh()
    values = [label.text() for label in page.findChildren(QLabel, "statValue")]
    assert "42.0" in values

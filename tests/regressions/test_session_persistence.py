"""Atomic persistence and explicit active-time contract."""
import sqlite3
from copy import deepcopy

import pytest
from PySide6.QtWidgets import QMessageBox

from src.database.models import SessionRecord, SettingsRepository


def record(**changes):
    values = dict(
        mode="test", mode_detail="60s", text_content="ab", total_chars=2,
        correct_chars=2, incorrect_chars=0, wpm=1, raw_wpm=1,
        accuracy=100, max_wpm=1,
        key_counts={"a": {"correct": 1}, "b": {"correct": 1}},
        started_at="2026-01-01T00:00:00",
        finished_at="2026-01-01T01:00:00", duration_seconds=60.5,
    )
    return SessionRecord(**(values | changes))


@pytest.mark.parametrize("table,condition", [
    ("sessions", "1"), ("key_stats", "NEW.key_char = 'b'"), ("streak", "1"),
])
def test_each_write_failure_rolls_back_every_table(stats_repo, table, condition):
    db = stats_repo.db
    db.execute(f"""CREATE TEMP TRIGGER fail_write BEFORE INSERT ON {table}
        WHEN {condition} BEGIN SELECT RAISE(ABORT, 'injected failure'); END""")
    with pytest.raises(sqlite3.IntegrityError, match="injected failure"):
        stats_repo.save_session(record())
    assert not db.conn.in_transaction
    SettingsRepository(db).set("theme", "dark")
    for name in ("sessions", "key_stats", "streak"):
        assert db.query_one(f"SELECT COUNT(*) FROM {name}")[0] == 0
    db.execute("DROP TRIGGER fail_write")
    stats_repo.save_session(record())
    assert stats_repo.get_session_count() == 1


def test_active_time_and_historical_dates_are_preserved(stats_repo):
    value = record()
    before = deepcopy(value)
    stats_repo.save_session(value)
    saved = stats_repo.get_recent_sessions()[0]
    assert saved["duration_seconds"] == 60.5
    assert saved["started_at"] == value.started_at
    assert saved["finished_at"] == value.finished_at
    assert stats_repo.db.query_one("SELECT date FROM streak")[0] == "2026-01-01"
    assert stats_repo.get_total_practice_minutes() == 60.5 / 60
    assert value == before


def test_legacy_missing_time_is_zero_without_mutating_input(stats_repo):
    value = record(started_at="", finished_at="", duration_seconds=0)
    stats_repo.save_session(value)
    saved = stats_repo.get_recent_sessions()[0]
    assert saved["started_at"] == saved["finished_at"]
    assert saved["duration_seconds"] == 0
    assert value.started_at == value.finished_at == ""


@pytest.mark.parametrize("duration", [-1, float("nan"), float("inf"), -float("inf")])
def test_invalid_duration_rejected_before_write(stats_repo, duration):
    with pytest.raises(ValueError):
        stats_repo.save_session(record(duration_seconds=duration))
    assert stats_repo.get_session_count() == 0
    assert not stats_repo.db.conn.in_transaction


@pytest.mark.parametrize("field", ["started_at", "finished_at"])
def test_invalid_timestamp_rejected_before_write(stats_repo, field):
    with pytest.raises(ValueError):
        stats_repo.save_session(record(**{field: "invalid"}))
    assert stats_repo.get_session_count() == 0


def test_nested_transaction_and_execute_do_not_commit_early(db):
    with sqlite3.connect(db.path) as reader:
        with db.transaction():
            db.execute("INSERT INTO settings VALUES ('outer', '1')")
            with pytest.raises(ValueError):
                with db.transaction():
                    db.execute("INSERT INTO settings VALUES ('inner', '1')")
                    raise ValueError("abort inner")
            assert reader.execute("SELECT COUNT(*) FROM settings").fetchone()[0] == 0
        assert reader.execute("SELECT key FROM settings").fetchall() == [("outer",)]


def test_outer_failure_rolls_back_successful_nested_scope(db):
    with pytest.raises(ValueError):
        with db.transaction():
            with db.transaction():
                db.execute("INSERT INTO settings VALUES ('nested', '1')")
            raise ValueError("abort outer")
    assert db.query("SELECT * FROM settings") == []


def test_commit_failure_rolls_back_and_can_retry(stats_repo, monkeypatch):
    connection = stats_repo.db.conn

    class FailingCommit:
        def __getattr__(self, name):
            return getattr(connection, name)

        def commit(self):
            raise sqlite3.OperationalError("database or disk is full")

    monkeypatch.setattr(stats_repo.db, "conn", FailingCommit())
    with pytest.raises(sqlite3.OperationalError, match="disk is full"):
        stats_repo.save_session(record())
    assert not connection.in_transaction
    monkeypatch.setattr(stats_repo.db, "conn", connection)
    SettingsRepository(stats_repo.db).set("theme", "dark")
    assert stats_repo.get_session_count() == 0
    stats_repo.save_session(record())
    assert stats_repo.get_session_count() == 1


def test_locked_database_shows_warning_and_retry_succeeds(app_window, db, monkeypatch):
    warnings = []
    monkeypatch.setattr(QMessageBox, "warning", lambda *args: warnings.append(args))
    db.conn.execute("PRAGMA busy_timeout = 0")
    page = app_window.pages["training"]
    with sqlite3.connect(db.path) as writer:
        writer.execute("BEGIN IMMEDIATE")
        assert page._save_session(record()) is False
        assert len(warnings) == 1
        assert "locked" in str(warnings[0])
        writer.rollback()
    assert page._save_session(record()) is True
    assert app_window.ctx.stats_repo.get_session_count() == 1


@pytest.mark.parametrize("action", ["commit", "rollback"])
def test_manual_transaction_completion_is_rejected(db, action):
    with pytest.raises(RuntimeError):
        with db.transaction():
            db.execute("INSERT INTO settings VALUES ('pending', '1')")
            getattr(db, action)()
    assert db.query("SELECT * FROM settings") == []


@pytest.mark.parametrize("page_name", ["training", "tests", "custom"])
def test_completion_pages_persist_engine_duration(app_window, monkeypatch, page_name):
    from src.core.typing_engine import TypingResult
    from src.ui.widgets.results_dialog import ResultsDialog

    monkeypatch.setattr(ResultsDialog, "exec", lambda self: 0)
    page = app_window.pages[page_name]
    result = TypingResult(total_chars=2, correct_chars=2, accuracy=100,
                          duration_seconds=12.75, started_at="2026-01-01T00:00:00")
    if page_name == "training":
        page.current_lesson = {"id": "L01", "text": "ab"}
    page.engine.reset("ab")
    if page_name == "tests":
        page._start_test_with_text("ab")
        page._save_and_show(result)
    else:
        page._on_finished(result)
    saved = app_window.ctx.stats_repo.get_recent_sessions()[0]
    assert saved["duration_seconds"] == 12.75


def test_close_persists_engine_duration(app_window, monkeypatch, tmp_db_path):
    from src.core.typing_engine import TypingResult

    page = app_window.pages["custom"]
    page.engine.reset("abcdef")
    page.engine.process_key("a")
    monkeypatch.setattr(page.engine, "get_result", lambda: TypingResult(
        total_chars=1, correct_chars=1, duration_seconds=8.25))
    app_window.close()
    with sqlite3.connect(tmp_db_path) as conn:
        assert conn.execute("SELECT duration_seconds FROM sessions").fetchall() == [(8.25,)]

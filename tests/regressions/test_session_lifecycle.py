"""Real Qt lifecycle, atomic retry and monotonic multi-text tests."""
from copy import deepcopy

import pytest
from PySide6.QtWidgets import QMessageBox

from src.ui.widgets.results_dialog import ResultsDialog


@pytest.fixture
def timed(app_window, monkeypatch):
    ticks = [0.0]
    monkeypatch.setattr("src.core.typing_engine.monotonic", lambda: ticks[0])
    page = app_window.pages["tests"]
    page.engine._clock = lambda: ticks[0]
    monkeypatch.setattr(ResultsDialog, "exec", lambda self: 0)
    monkeypatch.setattr(QMessageBox, "warning", lambda *args: None)
    page._start_test_with_text("ab")
    return page, ticks


def test_countdown_uses_elapsed_not_number_of_callbacks(timed):
    page, ticks = timed
    ticks[0] = 12.2
    page._on_countdown_tick()
    assert page._remaining_seconds == 48
    for _ in range(10):
        page._on_countdown_tick()
    assert page._remaining_seconds == 48
    assert page._combine_result(page.engine.get_result()).duration_seconds == 12.2


def test_timed_pause_excludes_wait_and_blocks_input(timed):
    page, ticks = timed
    ticks[0] = 10
    page.pause_page()
    ticks[0] = 110
    page.on_key_press("a")
    page._on_countdown_tick()
    assert page.engine.position == 0
    page.resume_page()
    assert page._remaining_seconds == 50
    ticks[0] = 115
    page._on_countdown_tick()
    assert page._remaining_seconds == 45


def test_multi_text_retains_start_counts_and_full_text(timed, monkeypatch):
    page, ticks = timed
    identity = page.session.identity
    started = page._test_started_at
    ticks[0] = 5
    page.on_key_press("a")
    ticks[0] = 10
    page.on_key_press("b")
    result = page.engine.get_result()
    monkeypatch.setattr("src.ui.pages.tests.get_texts", lambda _: ["cd"])
    page._on_finished(result)
    # A duplicate signal from the previous text must not add it twice.
    page._on_finished(result)
    ticks[0] = 20
    page.on_key_press("c")
    before = deepcopy(page._acc_key_counts)
    one = page._combine_result(page.engine.get_result())
    two = page._combine_result(page.engine.get_result())
    assert one == two
    assert before == page._acc_key_counts
    assert one.total_chars == 3
    assert one.duration_seconds == 20
    assert one.started_at == started
    assert page.session.identity == identity
    assert page.save_for_close()
    saved = page.ctx.stats_repo.get_recent_sessions()[0]
    assert saved["text_content"] == "abcd"
    assert saved["total_chars"] == 3


def test_close_between_texts_keeps_completed_text(timed, monkeypatch):
    page, ticks = timed
    monkeypatch.setattr("src.ui.pages.tests.get_texts", lambda _: ["cd"])
    page.on_key_press("a")
    ticks[0] = 5
    page.on_key_press("b")
    page._on_finished(page.engine.get_result())
    assert page.engine.position == 0
    assert page.save_for_close()
    assert page.ctx.stats_repo.get_recent_sessions()[0]["total_chars"] == 2


def test_late_input_finishes_at_deadline_without_accepting_key(timed):
    page, ticks = timed
    ticks[0] = 1
    page.on_key_press("a")
    ticks[0] = 65
    page.on_key_press("b")
    saved = page.ctx.stats_repo.get_recent_sessions()[0]
    assert saved["duration_seconds"] == 60
    assert saved["total_chars"] == 1
    page._force_finish()
    page._on_finished(page.engine.get_result())
    assert page.save_for_close()
    assert page.ctx.stats_repo.get_session_count() == 1


def test_empty_timeout_has_no_record_achievement_or_success(timed, monkeypatch):
    page, ticks = timed
    sounds = []
    monkeypatch.setattr(page.ctx.sound, "play_success", lambda: sounds.append(1))
    ticks[0] = 60
    page._on_countdown_tick()
    assert page.session.saved
    assert page.ctx.stats_repo.get_session_count() == 0
    assert page.ctx.stats_repo.db.query("SELECT * FROM achievements") == []
    assert not sounds


def test_retry_keeps_frozen_record_and_does_not_show_success_on_failure(timed, monkeypatch):
    page, ticks = timed
    db = page.ctx.stats_repo.db
    sounds = []
    dialogs = []
    monkeypatch.setattr(page.ctx.sound, "play_success", lambda: sounds.append(1))
    monkeypatch.setattr(ResultsDialog, "exec", lambda self: dialogs.append(1))
    page.on_key_press("a")
    db.execute("""CREATE TEMP TRIGGER fail_save BEFORE INSERT ON sessions
        BEGIN SELECT RAISE(ABORT, 'test failure'); END""")
    ticks[0] = 60
    page._on_countdown_tick()
    pending = deepcopy(page.session.pending)
    assert not page.session.saved
    assert not page.retry_save_btn.isHidden()
    assert not sounds and not dialogs
    ticks[0] = 200
    page._start_test_with_text("new")
    assert page.engine.target_text == "ab"
    assert page.session.pending == pending
    db.execute("DROP TRIGGER fail_save")
    assert page._retry_pending_save()
    assert page._retry_pending_save()
    saved = page.ctx.stats_repo.get_recent_sessions()[0]
    assert saved["duration_seconds"] == pending.duration_seconds
    assert saved["finished_at"] == pending.finished_at
    assert page.ctx.stats_repo.get_session_count() == 1


def test_close_failure_keeps_window_and_connection_open(timed, app_window):
    page, ticks = timed
    page.on_key_press("a")
    db = page.ctx.stats_repo.db
    db.execute("""CREATE TEMP TRIGGER fail_close BEFORE INSERT ON sessions
        BEGIN SELECT RAISE(ABORT, 'close failure'); END""")
    assert app_window.close() is False
    assert app_window.isVisible()
    assert db.query_one("SELECT 1")[0] == 1
    assert page.session.pending is not None
    db.execute("DROP TRIGGER fail_close")
    assert page._retry_pending_save()


@pytest.mark.parametrize("table", ["lesson_progress", "achievements"])
def test_completed_lesson_is_atomic_with_progress_and_awards(app_window, monkeypatch, table):
    monkeypatch.setattr(QMessageBox, "warning", lambda *args: None)
    monkeypatch.setattr(ResultsDialog, "exec", lambda self: 0)
    page = app_window.pages["training"]
    page.current_lesson = {"id": "L01", "text": "ab"}
    page.engine.reset("ab")
    page.engine.process_key("a")
    page.engine.process_key("b")
    db = page.ctx.stats_repo.db
    db.execute(f"""CREATE TEMP TRIGGER fail_related BEFORE INSERT ON {table}
        BEGIN SELECT RAISE(ABORT, 'related failure'); END""")
    page._on_finished(page.engine.get_result())
    for name in ("sessions", "key_stats", "streak", "lesson_progress", "achievements"):
        assert db.query_one(f"SELECT COUNT(*) FROM {name}")[0] == 0
    db.execute("DROP TRIGGER fail_related")
    assert page._retry_pending_save()
    assert page._retry_pending_save()
    assert db.query_one("SELECT attempts FROM lesson_progress")[0] == 1
    assert page.ctx.stats_repo.get_session_count() == 1


def test_restart_creates_new_identity_and_preserves_partial_session(timed):
    page, ticks = timed
    old_identity = page.session.identity
    page.on_key_press("a")
    ticks[0] = 5
    page._start_test_with_text("cd")
    assert page.session.identity != old_identity
    assert page.ctx.stats_repo.get_session_count() == 1
    page.on_key_press("c")
    ticks[0] = 8
    assert page.save_for_close()
    assert page.ctx.stats_repo.get_session_count() == 2


def test_resume_after_text_finished_before_signal_continues_test(timed, monkeypatch):
    page, ticks = timed
    monkeypatch.setattr("src.ui.pages.tests.get_texts", lambda _: ["cd"])
    page.on_key_press("a")
    ticks[0] = 5
    page.on_key_press("b")
    page.pause_page()
    ticks[0] = 100
    page.resume_page()
    assert page.engine.target_text == "cd"
    assert page._test_active
    assert page._remaining_seconds == 55


@pytest.mark.parametrize("page_name", ["training", "custom"])
def test_repeated_completion_and_close_save_once(app_window, monkeypatch, page_name):
    monkeypatch.setattr(ResultsDialog, "exec", lambda self: 0)
    page = app_window.pages[page_name]
    if page_name == "training":
        page.current_lesson = {"id": "L01", "text": "ab"}
    page.engine.reset("ab")
    page.engine.process_key("a")
    page.engine.process_key("b")
    result = page.engine.get_result()
    page._on_finished(result)
    page._on_finished(result)
    assert page.save_for_close()
    assert page.ctx.stats_repo.get_session_count() == 1
    if page_name == "training":
        assert page.ctx.stats_repo.db.query_one("SELECT attempts FROM lesson_progress")[0] == 1


def test_one_page_failure_does_not_duplicate_other_page_on_close_retry(timed, app_window):
    page, ticks = timed
    page.on_key_press("a")
    custom = app_window.pages["custom"]
    custom.engine.reset("xyz")
    custom.engine.process_key("x")
    db = page.ctx.stats_repo.db
    db.execute("""CREATE TEMP TRIGGER fail_custom BEFORE INSERT ON sessions
        WHEN NEW.mode = 'custom'
        BEGIN SELECT RAISE(ABORT, 'custom failure'); END""")
    assert app_window.close() is False
    assert page.session.saved
    assert not custom.session.saved
    assert page.ctx.stats_repo.get_session_count() == 1
    db.execute("DROP TRIGGER fail_custom")
    assert page.save_for_close()
    assert custom.save_for_close()
    assert page.ctx.stats_repo.get_session_count() == 2


def test_outer_commit_failure_can_retry_without_duplicate(timed, monkeypatch):
    import sqlite3

    page, ticks = timed
    db = page.ctx.stats_repo.db
    connection = db.conn

    class FailCommit:
        def __getattr__(self, name):
            return getattr(connection, name)

        def commit(self):
            raise sqlite3.OperationalError("disk is full")

    page.on_key_press("a")
    monkeypatch.setattr(db, "conn", FailCommit())
    ticks[0] = 60
    page._on_countdown_tick()
    assert not page.session.saved
    assert page.ctx.stats_repo.get_session_count() == 0
    assert db.query("SELECT * FROM achievements") == []
    monkeypatch.setattr(db, "conn", connection)
    assert page._retry_pending_save()
    assert page.ctx.stats_repo.get_session_count() == 1


def test_failed_lesson_switch_preserves_selection_and_session(app_window, monkeypatch):
    monkeypatch.setattr(QMessageBox, "warning", lambda *args: None)
    page = app_window.pages["training"]
    page.lesson_list.setCurrentRow(0)
    lesson = page.current_lesson
    page.on_key_press(lesson["text"][0])
    identity = page.session.identity
    db = page.ctx.stats_repo.db
    db.execute("""CREATE TEMP TRIGGER fail_switch BEFORE INSERT ON sessions
        BEGIN SELECT RAISE(ABORT, 'switch failure'); END""")
    page.lesson_list.setCurrentRow(1)
    assert page.lesson_list.currentRow() == 0
    assert page.current_lesson == lesson
    assert page.session.identity == identity
    db.execute("DROP TRIGGER fail_switch")
    page.lesson_list.setCurrentRow(1)
    assert page.session.identity != identity
    assert page.ctx.stats_repo.get_session_count() == 1
    # An interrupted lesson is recorded as practice, not completed.
    assert db.query("SELECT * FROM lesson_progress") == []

"""Backup round trips, validation, migration and real UI data safety."""
import json
import sqlite3
from copy import deepcopy
from uuid import uuid4

import pytest
from PySide6.QtWidgets import QFileDialog, QMessageBox

from src.database.backup import TABLES, BackupService
from src.database.db import _SCHEMA, Database
from src.database.models import AchievementRepository, LessonRepository, SessionRecord


@pytest.fixture
def service(stats_repo):
    stats_repo.save_session(SessionRecord(
        mode="lesson", mode_detail="L01", text_content="aş", total_chars=2,
        correct_chars=1, incorrect_chars=1, wpm=2, raw_wpm=4, accuracy=50, max_wpm=5,
        key_counts={"a": {"correct": 1}, "ş": {"incorrect": 1}},
        started_at="2026-01-01T10:00:00", finished_at="2026-01-01T10:01:00",
        duration_seconds=30,
    ))
    LessonRepository(stats_repo.db).mark_completed("L01", 2, 50)
    AchievementRepository(stats_repo.db).unlock("first_session")
    stats_repo.db.execute("INSERT INTO settings VALUES ('theme', 'light')")
    return BackupService(stats_repo.db)


def state(db):
    return {table: [dict(row) for row in db.query(f"SELECT * FROM {table} ORDER BY 1")]
            for table in TABLES}


def semantic_snapshot(service):
    result = service.snapshot()
    result.pop("created_at")
    ids = {row["id"]: row["session_uid"] for row in result["sessions"]}
    for row in result["sessions"]:
        row.pop("id")
    for row in result["key_stats"]:
        row.pop("id")
        row["session_id"] = ids[row["session_id"]]
    return result


def test_full_round_trip_and_repeated_restore(service):
    backup = service.snapshot()
    expected = semantic_snapshot(service)
    service.reset()
    assert service.restore(backup) == 1
    assert semantic_snapshot(service) == expected
    assert service.restore(backup) == 0
    assert semantic_snapshot(service) == expected
    assert service.db.query("PRAGMA foreign_key_check") == []


def test_id_collisions_are_remapped_and_local_data_preserved(service):
    backup = service.snapshot()
    backup["sessions"][0]["session_uid"] = uuid4().hex
    backup["sessions"][0]["text_content"] = "xy"
    original_id = backup["sessions"][0]["id"]
    assert service.restore(backup) == 1
    assert len(service.db.query("SELECT * FROM sessions")) == 2
    imported = service.db.query_one("SELECT id FROM sessions WHERE text_content = 'xy'")[0]
    assert imported != original_id
    assert len(service._keys(imported)) == 2
    assert service.restore(backup) == 0


def test_identity_conflict_rolls_back_earlier_new_session(service):
    backup = service.snapshot()
    new = deepcopy(backup["sessions"][0])
    new["id"] = 999
    new["session_uid"] = uuid4().hex
    backup["sessions"].insert(0, new)
    backup["sessions"][1]["wpm"] = 99
    before = state(service.db)
    with pytest.raises(ValueError, match="conflicts"):
        service.restore(backup)
    assert state(service.db) == before


@pytest.mark.parametrize("mutation", [
    lambda b: b.update(backup_version=99),
    lambda b: b.update(schema_version=99),
    lambda b: b.pop("key_stats"),
    lambda b: b.update(sessions={}),
    lambda b: b["sessions"].append(deepcopy(b["sessions"][0])),
    lambda b: b["sessions"][0].update(duration_seconds=-1),
    lambda b: b["sessions"][0].update(wpm=float("nan")),
    lambda b: b["sessions"][0].update(accuracy=101),
    lambda b: b["sessions"][0].update(total_chars=True),
    lambda b: b["sessions"][0].update(total_chars=100),
    lambda b: b["sessions"][0].update(started_at="bad"),
    lambda b: b["sessions"][0].update(session_uid="bad"),
    lambda b: b["key_stats"][0].update(session_id=999),
    lambda b: b["key_stats"].append(deepcopy(b["key_stats"][0])),
    lambda b: b["key_stats"][0].update(correct_count=-1),
    lambda b: b["lesson_progress"][0].update(attempts=0),
    lambda b: b["achievements"][0].update(unlocked_at="bad"),
    lambda b: b["streak"][0].update(date="2026-99-01"),
    lambda b: b["settings"].update(volume="900"),
    lambda b: b["settings"].update(theme=None),
])
def test_invalid_backup_leaves_every_table_unchanged(service, mutation):
    backup = service.snapshot()
    mutation(backup)
    before = state(service.db)
    with pytest.raises((ValueError, TypeError)):
        service.restore(backup)
    assert state(service.db) == before


@pytest.mark.parametrize("table", ["key_stats", "lesson_progress", "achievements", "streak", "settings"])
def test_restore_write_failure_is_atomic(service, table):
    backup = service.snapshot()
    service.reset()
    service.db.execute("INSERT INTO settings VALUES ('local', 'keep')")
    before = state(service.db)
    service.db.execute(f"""CREATE TEMP TRIGGER reject_restore BEFORE INSERT ON {table}
        BEGIN SELECT RAISE(ABORT, 'restore failure'); END""")
    with pytest.raises(sqlite3.IntegrityError):
        service.restore(backup)
    assert state(service.db) == before
    assert not service.db.conn.in_transaction
    service.db.execute("DROP TRIGGER reject_restore")
    assert service.restore(backup) == 1


def test_commit_failure_rolls_back_restore(service, monkeypatch):
    backup = service.snapshot()
    service.reset()
    connection = service.db.conn

    class FailCommit:
        def __getattr__(self, key):
            return getattr(connection, key)

        def commit(self):
            raise sqlite3.OperationalError("disk full")

    monkeypatch.setattr(service.db, "conn", FailCommit())
    with pytest.raises(sqlite3.OperationalError):
        service.restore(backup)
    assert all(not rows for rows in state(service.db).values())
    monkeypatch.setattr(service.db, "conn", connection)
    assert service.restore(backup) == 1


def test_reset_failure_restores_all_deleted_rows(service):
    before = state(service.db)
    service.db.execute("""CREATE TEMP TRIGGER reject_reset BEFORE DELETE ON settings
        BEGIN SELECT RAISE(ABORT, 'reset failure'); END""")
    with pytest.raises(sqlite3.IntegrityError):
        service.reset()
    assert state(service.db) == before


def test_legacy_import_preserves_present_data_and_does_not_duplicate(service):
    legacy = service.snapshot()
    for key in ("format", "backup_version", "schema_version", "created_at", "key_stats", "streak"):
        legacy.pop(key)
    for row in legacy["sessions"]:
        row.pop("session_uid")
    assert service.restore(legacy) == 0  # Exact legacy match against migrated current data.
    service.reset()
    assert service.restore(legacy) == 1
    assert service.restore(legacy) == 0
    assert service.db.query_one("SELECT duration_seconds FROM sessions")[0] == 30
    assert service.db.query_one("SELECT date FROM streak")[0] == "2026-01-01"
    assert service.db.query("SELECT * FROM key_stats") == []  # Never invent missing counters.
    assert service.db.query_one("SELECT COUNT(*) FROM lesson_progress")[0] == 1


def test_legacy_list_identical_rows_keep_multiplicity(service):
    rows = service.snapshot()["sessions"]
    rows[0].pop("session_uid")
    rows.append(deepcopy(rows[0]))
    rows[1]["id"] = 2
    service.reset()
    assert service.restore(rows) == 2
    assert service.restore(rows) == 0


def test_legacy_missing_duration_is_zero_and_missing_dates_rejected(service):
    row = service.snapshot()["sessions"][0]
    row.pop("session_uid")
    row.pop("duration_seconds")
    row.pop("finished_at")
    service.reset()
    assert service.restore([row]) == 1
    saved = service.db.query_one("SELECT * FROM sessions")
    assert saved["duration_seconds"] == 0
    assert saved["finished_at"] == row["started_at"]
    row.pop("started_at")
    before = state(service.db)
    with pytest.raises(ValueError):
        service.restore([row])
    assert state(service.db) == before


def test_export_failure_keeps_existing_file(service, tmp_path, monkeypatch):
    destination = tmp_path / "backup.json"
    destination.write_text("previous backup", encoding="utf-8")

    def fail(*args):
        raise OSError("replace failed")

    monkeypatch.setattr("src.database.backup.os.replace", fail)
    with pytest.raises(OSError):
        service.export_file(destination)
    assert destination.read_text(encoding="utf-8") == "previous backup"
    assert list(tmp_path.glob("*.tmp")) == []


def test_export_has_no_ten_thousand_row_limit(service, tmp_path):
    with service.db.transaction():
        service.db.conn.executemany("""
            INSERT INTO sessions (started_at, finished_at, duration_seconds, mode,
            text_content, total_chars, correct_chars, incorrect_chars,
            wpm, raw_wpm, accuracy, session_uid)
            VALUES ('2026-01-01', '2026-01-01', 1, 'test', 'a', 1, 1, 0, 1, 1, 100, ?)
        """, [(uuid4().hex,) for _ in range(10000)])
    path = tmp_path / "large.json"
    service.export_file(path)
    assert len(json.loads(path.read_text(encoding="utf-8"))["sessions"]) == 10001


def old_database(path):
    with sqlite3.connect(path) as connection:
        connection.executescript(_SCHEMA)
        connection.execute("INSERT INTO schema_version VALUES (2)")
        connection.execute("""INSERT INTO sessions (
            started_at, finished_at, duration_seconds, mode, text_content,
            total_chars, correct_chars, incorrect_chars, wpm, raw_wpm, accuracy)
            VALUES ('2026-01-01', '2026-01-01', 12, 'test', 'a', 1, 1, 0, 1, 1, 100)""")
        connection.execute("INSERT INTO key_stats (session_id, key_char, correct_count) VALUES (1, 'a', 1)")


def test_v2_migration_keeps_ids_metrics_keys_and_uid_across_reopen(tmp_path):
    path = tmp_path / "old.db"
    old_database(path)
    db = Database(path)
    row = dict(db.query_one("SELECT * FROM sessions"))
    assert len(row["session_uid"]) == 32
    assert row["id"] == 1 and row["duration_seconds"] == 12
    assert db.query_one("SELECT session_id FROM key_stats")[0] == 1
    db.close()
    reopened = Database(path)
    assert dict(reopened.query_one("SELECT * FROM sessions")) == row
    assert reopened.query_one("SELECT MAX(version) FROM schema_version")[0] == 3
    reopened.close()


def test_migration_failure_rolls_back_added_column(tmp_path, monkeypatch):
    from src.database import db as module

    path = tmp_path / "old.db"
    old_database(path)

    def fail(conn):
        raise RuntimeError("migration interrupted")

    monkeypatch.setattr(module, "_MIGRATIONS", [*module._MIGRATIONS, (3, fail)])
    with pytest.raises(RuntimeError):
        Database(path)
    with sqlite3.connect(path) as conn:
        assert "session_uid" not in {row[1] for row in conn.execute("PRAGMA table_info(sessions)")}
        assert conn.execute("SELECT MAX(version) FROM schema_version").fetchone()[0] == 2
        assert conn.execute("SELECT COUNT(*) FROM sessions").fetchone()[0] == 1


def test_future_database_schema_rejected(tmp_path):
    path = tmp_path / "future.db"
    old_database(path)
    with sqlite3.connect(path) as conn:
        conn.execute("INSERT INTO schema_version VALUES (99)")
    with pytest.raises(ValueError, match="newer"):
        Database(path)


@pytest.mark.parametrize("action", ["_import_data", "_reset_data", "_export_data"])
def test_data_operations_block_unsaved_work(app_window, monkeypatch, action):
    page = app_window.pages["custom"]
    page.engine.reset("abc")
    page.engine.process_key("a")
    warnings = []
    monkeypatch.setattr(QMessageBox, "warning", lambda *args: warnings.append(args))
    before = state(app_window.ctx.stats_repo.db)
    getattr(app_window.pages["settings"], action)()
    assert warnings
    assert page.engine.position == 1
    assert state(app_window.ctx.stats_repo.db) == before


def test_successful_restore_reload_settings_without_reinserting_saved_session(
        app_window, monkeypatch, tmp_path):
    page = app_window.pages["custom"]
    page.engine.reset("abc")
    page.engine.process_key("a")
    assert page.save_for_close()
    service = BackupService(app_window.ctx.stats_repo.db)
    backup = service.snapshot()
    backup["settings"].update(theme="light", font_size="30", volume="15")
    path = tmp_path / "backup.json"
    path.write_text(json.dumps(backup), encoding="utf-8")
    monkeypatch.setattr(QFileDialog, "getOpenFileName", lambda *a: (str(path), "JSON"))
    app_window.pages["settings"]._import_data()
    assert app_window.ctx.theme == "light"
    assert app_window.ctx.font_size == 30
    assert page.engine.position == 0
    assert page.session.pending is None
    assert page.save_for_close()
    assert app_window.ctx.stats_repo.get_session_count() == 1


def test_reset_clears_runtime_and_does_not_resurrect_saved_session(app_window, monkeypatch):
    page = app_window.pages["custom"]
    page.engine.reset("abc")
    page.engine.process_key("a")
    assert page.save_for_close()
    monkeypatch.setattr(QMessageBox, "question", lambda *args: QMessageBox.Yes)
    app_window.pages["settings"]._reset_data()
    assert page.engine.target_text == ""
    assert page.session.pending is None
    assert page.save_for_close()
    assert all(not rows for rows in state(app_window.ctx.stats_repo.db).values())


def test_merge_keeps_best_progress_and_imported_settings_win(service):
    backup = service.snapshot()
    backup["lesson_progress"][0].update(best_wpm=1, best_accuracy=30, attempts=1)
    backup["settings"]["theme"] = "dark"
    service.db.execute("UPDATE lesson_progress SET best_wpm=80, best_accuracy=100, attempts=9")
    service.restore(backup)
    service.restore(backup)
    progress = service.db.query_one("SELECT * FROM lesson_progress")
    assert (progress["best_wpm"], progress["best_accuracy"], progress["attempts"]) == (80, 100, 9)
    assert service.db.query_one("SELECT value FROM settings WHERE key='theme'")[0] == "dark"


def test_v1_migration_adds_both_metrics_and_uid(tmp_path):
    path = tmp_path / "v1.db"
    old_database(path)
    with sqlite3.connect(path) as conn:
        conn.execute("ALTER TABLE sessions DROP COLUMN max_wpm")
        conn.execute("UPDATE schema_version SET version=1")
    db = Database(path)
    saved = db.query_one("SELECT * FROM sessions")
    assert saved["max_wpm"] == 0
    assert len(saved["session_uid"]) == 32
    assert saved["duration_seconds"] == 12
    assert db.query_one("SELECT MAX(version) FROM schema_version")[0] == 3
    db.close()


def test_pending_failed_record_blocks_reset_even_after_engine_reset(app_window, monkeypatch):
    page = app_window.pages["custom"]
    page.engine.reset("abc")
    page.engine.process_key("a")
    monkeypatch.setattr(QMessageBox, "warning", lambda *args: None)
    db = page.ctx.stats_repo.db
    db.execute("""CREATE TEMP TRIGGER fail_pending BEFORE INSERT ON sessions
        BEGIN SELECT RAISE(ABORT, 'pending failure'); END""")
    assert not page.save_for_close()
    pending = deepcopy(page.session.pending)
    page.engine.reset("")
    app_window.pages["settings"]._reset_data()
    assert page.session.pending == pending
    db.execute("DROP TRIGGER fail_pending")
    assert page._retry_pending_save()
    assert db.query_one("SELECT session_uid FROM sessions")[0] == page.session.identity


def test_invalid_import_does_not_clear_saved_runtime(app_window, monkeypatch, tmp_path):
    page = app_window.pages["custom"]
    page.engine.reset("abc")
    page.engine.process_key("a")
    assert page.save_for_close()
    before = state(app_window.ctx.stats_repo.db)
    pending = deepcopy(page.session.pending)
    path = tmp_path / "invalid.json"
    path.write_text('{"sessions": [', encoding="utf-8")
    warnings = []
    monkeypatch.setattr(QFileDialog, "getOpenFileName", lambda *args: (str(path), "JSON"))
    monkeypatch.setattr(QMessageBox, "warning", lambda *args: warnings.append(args))
    app_window.pages["settings"]._import_data()
    assert warnings
    assert page.session.pending == pending
    assert state(app_window.ctx.stats_repo.db) == before


def test_uid_and_repeat_import_survive_reopening_database(service, tmp_path):
    path = tmp_path / "restored.db"
    backup = service.snapshot()
    target = Database(path)
    assert BackupService(target).restore(backup) == 1
    target.close()
    target = Database(path)
    assert BackupService(target).restore(backup) == 0
    assert target.query_one("SELECT session_uid FROM sessions")[0] == backup["sessions"][0]["session_uid"]
    target.close()


def test_new_record_uid_is_validated_and_normalized(stats_repo):
    uid = uuid4()
    record = SessionRecord(
        mode="test", mode_detail="", text_content="a", total_chars=1,
        correct_chars=1, incorrect_chars=0, wpm=1, raw_wpm=1, accuracy=100,
        max_wpm=1, session_uid=str(uid).upper())
    stats_repo.save_session(record)
    assert stats_repo.get_recent_sessions()[0]["session_uid"] == uid.hex
    record.session_uid = "invalid"
    with pytest.raises(ValueError):
        stats_repo.save_session(record)
    assert stats_repo.get_session_count() == 1

"""Tests for the database migration framework."""
from src.database.db import Database, _SCHEMA_VERSION, _MIGRATIONS


def test_schema_version_is_set(db):
    row = db.query_one("SELECT version FROM schema_version ORDER BY version DESC LIMIT 1")
    assert row["version"] == _SCHEMA_VERSION


def test_migrations_registered():
    assert len(_MIGRATIONS) >= 1
    versions = [v for v, _ in _MIGRATIONS]
    assert 2 in versions


def test_schema_tables_exist(db):
    tables = {row[0] for row in db.conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table'"
    ).fetchall()}
    expected = {"sessions", "key_stats", "lesson_progress", "achievements",
                "settings", "streak", "schema_version"}
    assert expected.issubset(tables)


def test_indexes_exist(db):
    indexes = {row[0] for row in db.conn.execute(
        "SELECT name FROM sqlite_master WHERE type='index'"
    ).fetchall()}
    expected = {"idx_sessions_finished_at", "idx_sessions_mode",
                "idx_key_stats_session_id", "idx_key_stats_key_char"}
    assert expected.issubset(indexes)
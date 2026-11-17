"""Reproduce partial writes using the real repository and SQLite."""
import sqlite3

import pytest

from src.database.models import SessionRecord, SettingsRepository


def test_failed_session_does_not_leak_into_next_commit(stats_repo):
    record = SessionRecord(
        mode="test", mode_detail="60s", text_content="a",
        total_chars=1, correct_chars=1, incorrect_chars=0,
        wpm=1, raw_wpm=1, accuracy=100, max_wpm=1,
        key_counts={"a": {"correct": None, "incorrect": 0}},
    )
    with pytest.raises((sqlite3.IntegrityError, ValueError, TypeError)):
        stats_repo.save_session(record)
    SettingsRepository(stats_repo.db).set("theme", "dark")
    assert stats_repo.get_session_count() == 0
    assert stats_repo.get_key_error_stats() == {}

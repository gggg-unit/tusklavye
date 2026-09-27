"""Tests for database operations and the SessionRecord dataclass."""
from src.database.models import SessionRecord


def _make_record(**overrides):
    defaults = dict(
        mode="test", mode_detail="60s", text_content="hello",
        total_chars=5, correct_chars=4, incorrect_chars=1,
        wpm=30.0, raw_wpm=35.0, accuracy=80.0, max_wpm=32.0,
        key_counts={"h": {"correct": 1, "incorrect": 0}},
        started_at="2026-01-01T00:00:00",
    )
    defaults.update(overrides)
    return SessionRecord(**defaults)


def test_save_and_query(stats_repo):
    sid = stats_repo.save_session(_make_record())
    assert sid > 0
    assert stats_repo.get_session_count() == 1
    assert stats_repo.get_best_wpm() == 30.0
    assert stats_repo.get_best_accuracy() == 80.0
    assert stats_repo.get_avg_accuracy() == 80.0
    recent = stats_repo.get_recent_sessions(5)
    assert len(recent) == 1
    assert recent[0]["mode"] == "test"


def test_multiple_sessions(stats_repo):
    stats_repo.save_session(_make_record(wpm=30.0, accuracy=80.0))
    stats_repo.save_session(_make_record(wpm=50.0, accuracy=95.0))
    assert stats_repo.get_session_count() == 2
    assert stats_repo.get_best_wpm() == 50.0
    assert stats_repo.get_best_accuracy() == 95.0


def test_text_truncation(stats_repo):
    long_text = "x" * 20000
    sid = stats_repo.save_session(_make_record(text_content=long_text))
    rows = stats_repo.db.query("SELECT text_content FROM sessions WHERE id = ?", (sid,))
    assert len(rows[0]["text_content"]) == 10000


def test_key_stats_persisted(stats_repo):
    stats_repo.save_session(_make_record(
        key_counts={"a": {"correct": 3, "incorrect": 1}, "b": {"correct": 2, "incorrect": 0}},
    ))
    stats = stats_repo.get_key_error_stats()
    assert stats["a"]["correct"] == 3
    assert stats["a"]["incorrect"] == 1
    assert stats["b"]["correct"] == 2


def test_finger_stats(stats_repo, layout):
    stats_repo.save_session(_make_record(
        key_counts={"a": {"correct": 5, "incorrect": 1}, "j": {"correct": 3, "incorrect": 0}},
    ))
    finger_map = {c: f for c, f in layout.char_to_finger.items()}
    fs = stats_repo.get_finger_stats(finger_map)
    assert fs.get("LP", {}).get("total") == 6
    assert fs.get("RI", {}).get("total") == 3


def test_wpm_history(stats_repo):
    for wpm in (20.0, 30.0, 40.0):
        stats_repo.save_session(_make_record(wpm=wpm))
    history = stats_repo.get_wpm_history(10)
    assert len(history) == 3


def test_today_stats(stats_repo):
    stats_repo.save_session(_make_record(wpm=25.0))
    assert stats_repo.get_today_session_count() == 1
    assert stats_repo.get_today_best_wpm() == 25.0
    assert stats_repo.get_today_practice_minutes() >= 0
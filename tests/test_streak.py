"""Tests for streak calculation."""
from datetime import date


def test_empty_streak(stats_repo):
    assert stats_repo.get_streak() == 0


def test_today_only(stats_repo):
    today = date.today().isoformat()
    stats_repo.db.execute("INSERT INTO streak (date, practiced) VALUES (?, 1)", (today,))
    assert stats_repo.get_streak() == 1


def test_today_and_yesterday(stats_repo):
    today = date.today().isoformat()
    yesterday = date.fromordinal(date.today().toordinal() - 1).isoformat()
    stats_repo.db.execute("INSERT INTO streak (date, practiced) VALUES (?, 1)", (today,))
    stats_repo.db.execute("INSERT INTO streak (date, practiced) VALUES (?, 1)", (yesterday,))
    assert stats_repo.get_streak() == 2


def test_gap_breaks_streak(stats_repo):
    today = date.today().isoformat()
    three_days_ago = date.fromordinal(date.today().toordinal() - 3).isoformat()
    stats_repo.db.execute("INSERT INTO streak (date, practiced) VALUES (?, 1)", (today,))
    stats_repo.db.execute("INSERT INTO streak (date, practiced) VALUES (?, 1)", (three_days_ago,))
    assert stats_repo.get_streak() == 1


def test_save_session_touches_streak(stats_repo):
    from src.database.models import SessionRecord
    record = SessionRecord(
        mode="test", mode_detail="", text_content="hi",
        total_chars=2, correct_chars=2, incorrect_chars=0,
        wpm=20.0, raw_wpm=22.0, accuracy=100.0, max_wpm=21.0,
        key_counts={}, started_at="",
    )
    stats_repo.save_session(record)
    assert stats_repo.get_streak() == 1
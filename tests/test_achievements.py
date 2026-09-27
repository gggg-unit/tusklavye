"""Tests for achievement unlock logic."""
from src.core.achievements import check_and_unlock, get_definitions, THRESHOLDS
from src.database.models import SessionRecord


def _record(**ov):
    defaults = dict(
        mode="test", mode_detail="60s", text_content="hello",
        total_chars=5, correct_chars=5, incorrect_chars=0,
        wpm=25.0, raw_wpm=30.0, accuracy=100.0, max_wpm=26.0,
        key_counts={"h": {"correct": 1, "incorrect": 0}},
        started_at="2026-01-01T00:00:00",
    )
    defaults.update(ov)
    return SessionRecord(**defaults)


def test_no_unlock_initially(stats_repo, achievement_repo):
    unlocked = check_and_unlock(stats_repo, achievement_repo, lesson_count=0, streak=0)
    assert "first_session" not in unlocked


def test_first_session_unlock(stats_repo, achievement_repo):
    stats_repo.save_session(_record())
    unlocked = check_and_unlock(stats_repo, achievement_repo, lesson_count=0, streak=1)
    assert "first_session" in unlocked
    assert "speed_20" in unlocked
    assert "accuracy_95" in unlocked
    assert "accuracy_100" in unlocked


def test_no_re_unlock(stats_repo, achievement_repo):
    stats_repo.save_session(_record())
    check_and_unlock(stats_repo, achievement_repo, lesson_count=0, streak=1)
    unlocked2 = check_and_unlock(stats_repo, achievement_repo, lesson_count=0, streak=1)
    assert len(unlocked2) == 0


def test_accuracy_100_threshold(stats_repo, achievement_repo):
    stats_repo.save_session(_record(accuracy=99.5))
    unlocked = check_and_unlock(stats_repo, achievement_repo, lesson_count=0, streak=0)
    assert "accuracy_100" not in unlocked
    stats_repo.save_session(_record(wpm=30.0, accuracy=100.0))
    unlocked = check_and_unlock(stats_repo, achievement_repo, lesson_count=0, streak=0)
    assert "accuracy_100" in unlocked


def test_speed_thresholds(stats_repo, achievement_repo):
    stats_repo.save_session(_record(wpm=40.0))
    unlocked = check_and_unlock(stats_repo, achievement_repo, lesson_count=0, streak=0)
    assert "speed_20" in unlocked
    assert "speed_40" in unlocked
    assert "speed_60" not in unlocked


def test_streak_achievements(stats_repo, achievement_repo):
    unlocked = check_and_unlock(stats_repo, achievement_repo, lesson_count=0, streak=7)
    assert "streak_3" in unlocked
    assert "streak_7" in unlocked


def test_lesson_achievements(stats_repo, achievement_repo):
    unlocked = check_and_unlock(stats_repo, achievement_repo, lesson_count=5, streak=0)
    assert "lessons_5" in unlocked
    assert "lessons_all" not in unlocked


def test_all_lessons_achievement(stats_repo, achievement_repo):
    from src.core.lessons import LESSONS
    unlocked = check_and_unlock(stats_repo, achievement_repo, lesson_count=len(LESSONS), streak=0)
    assert "lessons_all" in unlocked


def test_thresholds_constant():
    assert THRESHOLDS["speed_20"] == 20
    assert THRESHOLDS["accuracy_100"] == 100.0
    assert THRESHOLDS["lessons_all"] >= 15
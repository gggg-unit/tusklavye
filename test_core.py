"""Standalone tests for core logic (no Qt required). Run: python test_core.py

Kept for backwards compatibility — the pytest suite in tests/ is the primary
test runner. These tests use the new SessionRecord dataclass and Database.reset()
factory instead of the old positional-arg / __new__ hack.
"""
import sys
import os
import tempfile
from pathlib import Path

sys.path.insert(0, os.path.dirname(__file__))

from src.core.keyboard_layout import KeyboardLayout, _tr_upper, _tr_lower
from src.core.typing_engine import TypingEngine
from src.core.lessons import LESSONS, get_lesson
from src.database.models import SessionRecord


def _record(**ov):
    defaults = dict(
        mode="test", mode_detail="60s", text_content="hello",
        total_chars=5, correct_chars=4, incorrect_chars=1,
        wpm=30.0, raw_wpm=35.0, accuracy=80.0, max_wpm=32.0,
        key_counts={"h": {"correct": 1, "incorrect": 0}},
        started_at="2026-01-01T00:00:00",
    )
    defaults.update(ov)
    return SessionRecord(**defaults)


def _fresh_db():
    from src.database.db import Database
    tmp = tempfile.mkdtemp()
    db_path = Path(tmp) / "test.db"
    return Database.reset(db_path)


def test_keyboard_layout():
    layout = KeyboardLayout()
    assert layout.finger_for_char("a") == "LP"
    assert layout.finger_for_char("j") == "RI"
    assert layout.finger_for_char("ş") == "RR"
    assert layout.finger_for_char(" ") == "RT"
    assert len(layout.rows) == 4
    print("✅ test_keyboard_layout passed")


def test_typing_engine():
    engine = TypingEngine()
    engine.reset("merhaba")
    for ch in "merhaba":
        engine.process_key(ch)
    assert engine.is_finished
    result = engine.get_result()
    assert result.correct_chars == 7
    assert result.incorrect_chars == 0
    assert result.accuracy == 100.0
    print("✅ test_typing_engine passed")


def test_typing_engine_errors():
    engine = TypingEngine()
    engine.reset("asdf")
    engine.process_key("a")
    engine.process_key("x")
    engine.process_key("d")
    engine.process_key("f")
    result = engine.get_result()
    assert result.correct_chars == 3
    assert result.incorrect_chars == 1
    assert result.accuracy == 75.0
    print("✅ test_typing_engine_errors passed")


def test_backspace():
    engine = TypingEngine()
    engine.reset("asdf")
    engine.process_key("a")
    engine.process_key("x")
    engine.backspace()
    assert engine.position == 1
    engine.process_key("s")
    engine.process_key("d")
    engine.process_key("f")
    assert engine.is_finished
    assert engine.get_result().accuracy == 100.0
    print("✅ test_backspace passed")


def test_lessons():
    assert len(LESSONS) == 15
    for lesson in LESSONS:
        assert lesson["text"]
        assert lesson["target_wpm"] > 0
    l1 = get_lesson("L01")
    assert l1 is not None
    assert "asdf" in l1["text"]
    print("✅ test_lessons passed")


def test_char_status():
    engine = TypingEngine()
    engine.reset("abc")
    assert engine.char_status(0) == "current"
    engine.process_key("a")
    assert engine.char_status(0) == "correct"
    assert engine.char_status(1) == "current"
    assert engine.char_status(2) == "pending"
    print("✅ test_char_status passed")


def test_newline_autoskip():
    engine = TypingEngine()
    engine.reset("ab\ncd")
    assert engine.position == 0
    engine.process_key("a")
    engine.process_key("b")
    assert engine.position == 3
    engine.process_key("c")
    engine.process_key("d")
    assert engine.is_finished
    assert engine.get_result().accuracy == 100.0
    print("✅ test_newline_autoskip passed")


def test_backspace_past_newline():
    engine = TypingEngine()
    engine.reset("ab\ncd")
    engine.process_key("a")
    engine.process_key("b")
    engine.process_key("c")
    engine.backspace()
    assert engine.target_text[engine.position] == "c"
    engine.process_key("c")
    engine.process_key("d")
    assert engine.is_finished
    assert engine.get_result().accuracy == 100.0
    print("✅ test_backspace_past_newline passed")


def test_empty_text():
    engine = TypingEngine()
    engine.reset("")
    assert engine.is_finished
    assert engine.position == 0
    result = engine.get_result()
    assert result.total_chars == 0
    assert result.accuracy == 100.0
    print("✅ test_empty_text passed")


def test_backspace_after_finish():
    engine = TypingEngine()
    engine.reset("ab")
    engine.process_key("a")
    engine.process_key("b")
    assert engine.is_finished
    engine.backspace()
    assert not engine.is_finished
    assert engine.position == 1
    engine.process_key("b")
    assert engine.is_finished
    print("✅ test_backspace_after_finish passed")


def test_turkish_uppercase():
    assert _tr_upper("i") == "İ"
    assert _tr_upper("ı") == "I"
    assert _tr_lower("İ") == "i"
    assert _tr_lower("I") == "ı"
    layout = KeyboardLayout()
    assert layout.finger_for_char("İ") == layout.finger_for_char("i")
    assert layout.finger_for_char("I") == layout.finger_for_char("ı")
    assert layout.finger_for_char("A") == layout.finger_for_char("a")
    k = layout.find_key("Ş")
    assert k is not None and k.char == "ş"
    print("✅ test_turkish_uppercase passed")


def test_db_operations():
    from src.database.models import StatsRepository
    db = _fresh_db()
    stats = StatsRepository(db)
    sid = stats.save_session(_record())
    assert sid > 0
    assert stats.get_session_count() == 1
    assert stats.get_best_wpm() == 30.0
    assert stats.get_best_accuracy() == 80.0
    assert stats.get_avg_accuracy() == 80.0
    recent = stats.get_recent_sessions(5)
    assert len(recent) == 1
    assert recent[0]["mode"] == "test"
    db.close()
    print("✅ test_db_operations passed")


def test_achievement_logic():
    from src.database.models import StatsRepository, AchievementRepository
    from src.core.achievements import check_and_unlock
    db = _fresh_db()
    stats = StatsRepository(db)
    ach = AchievementRepository(db)
    unlocked = check_and_unlock(stats, ach, lesson_count=0, streak=0)
    assert "first_session" not in unlocked
    stats.save_session(_record(wpm=25.0, accuracy=100.0, correct_chars=5, incorrect_chars=0))
    unlocked = check_and_unlock(stats, ach, lesson_count=0, streak=1)
    assert "first_session" in unlocked
    assert "speed_20" in unlocked
    assert "accuracy_95" in unlocked
    assert "accuracy_100" in unlocked
    unlocked2 = check_and_unlock(stats, ach, lesson_count=0, streak=1)
    assert len(unlocked2) == 0
    db.close()
    print("✅ test_achievement_logic passed")


def test_streak_edge_cases():
    from src.database.models import StatsRepository
    from datetime import date
    db = _fresh_db()
    stats = StatsRepository(db)
    assert stats.get_streak() == 0
    today = date.today().isoformat()
    db.execute("INSERT INTO streak (date, practiced) VALUES (?, 1)", (today,))
    assert stats.get_streak() == 1
    yesterday = date.fromordinal(date.today().toordinal() - 1).isoformat()
    db.execute("INSERT INTO streak (date, practiced) VALUES (?, 1)", (yesterday,))
    assert stats.get_streak() == 2
    db.close()
    print("✅ test_streak_edge_cases passed")


def test_newline_not_inflating_wpm():
    engine = TypingEngine()
    engine.reset("ab\ncd")
    engine.process_key("a")
    engine.process_key("b")
    engine.process_key("c")
    engine.process_key("d")
    assert engine.is_finished
    result = engine.get_result()
    assert result.total_chars == 4
    assert result.correct_chars == 4
    assert result.accuracy == 100.0
    print("✅ test_newline_not_inflating_wpm passed")


def test_backspace_decrements_key_counts():
    engine = TypingEngine()
    engine.reset("abc")
    engine.process_key("a")
    engine.process_key("b")
    assert engine.key_counts.get("a", {}).get("correct", 0) == 1
    assert engine.key_counts.get("b", {}).get("correct", 0) == 1
    engine.backspace()
    assert engine.key_counts.get("b") is None
    assert engine.key_counts.get("a", {}).get("correct", 0) == 1
    print("✅ test_backspace_decrements_key_counts passed")


def test_process_key_returns_true_when_finished():
    engine = TypingEngine()
    engine.reset("ab")
    engine.process_key("a")
    engine.process_key("b")
    assert engine.is_finished
    assert engine.process_key("x") is True
    print("✅ test_process_key_returns_true_when_finished passed")


def test_multi_char_input_guard():
    engine = TypingEngine()
    engine.reset("abc")
    assert engine.process_key("ab") is True
    assert engine.position == 0
    print("✅ test_multi_char_input_guard passed")


def test_elapsed_clamped_to_zero():
    engine = TypingEngine()
    engine.reset("abc")
    engine.process_key("a")
    engine._paused_duration = 999999.0
    assert engine.elapsed_seconds == 0.0
    print("✅ test_elapsed_clamped_to_zero passed")


def test_tr_upper_complete():
    assert _tr_upper("ş") == "Ş"
    assert _tr_upper("ğ") == "Ğ"
    assert _tr_upper("ü") == "Ü"
    assert _tr_upper("ö") == "Ö"
    assert _tr_upper("ç") == "Ç"
    print("✅ test_tr_upper_complete passed")


def test_achievement_100_accuracy_threshold():
    from src.database.models import StatsRepository, AchievementRepository
    from src.core.achievements import check_and_unlock
    db = _fresh_db()
    stats = StatsRepository(db)
    ach = AchievementRepository(db)
    stats.save_session(_record(accuracy=99.5))
    unlocked = check_and_unlock(stats, ach, lesson_count=0, streak=0)
    assert "accuracy_100" not in unlocked
    stats.save_session(_record(wpm=30.0, accuracy=100.0))
    unlocked = check_and_unlock(stats, ach, lesson_count=0, streak=0)
    assert "accuracy_100" in unlocked
    db.close()
    print("✅ test_achievement_100_accuracy_threshold passed")


def test_last_expected_property():
    engine = TypingEngine()
    engine.reset("abc")
    assert engine.last_expected == ""
    engine.process_key("a")
    assert engine.last_expected == "a"
    print("✅ test_last_expected_property passed")


if __name__ == "__main__":
    test_keyboard_layout()
    test_typing_engine()
    test_typing_engine_errors()
    test_backspace()
    test_lessons()
    test_char_status()
    test_newline_autoskip()
    test_backspace_past_newline()
    test_empty_text()
    test_backspace_after_finish()
    test_turkish_uppercase()
    test_db_operations()
    test_achievement_logic()
    test_streak_edge_cases()
    test_newline_not_inflating_wpm()
    test_backspace_decrements_key_counts()
    test_process_key_returns_true_when_finished()
    test_multi_char_input_guard()
    test_elapsed_clamped_to_zero()
    test_tr_upper_complete()
    test_achievement_100_accuracy_threshold()
    test_last_expected_property()
    print("\n✅ All tests passed!")

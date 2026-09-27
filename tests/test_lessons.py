"""Tests for the lesson curriculum."""
from src.core.lessons import LESSONS, get_lesson, get_lesson_index


def test_lesson_count():
    assert len(LESSONS) == 15


def test_lesson_content():
    for lesson in LESSONS:
        assert lesson["text"], f"lesson {lesson['id']} has no text"
        assert lesson["target_wpm"] > 0, f"lesson {lesson['id']} has no target wpm"
        assert "id" in lesson
        assert "title" in lesson
        assert "description" in lesson


def test_get_lesson():
    l1 = get_lesson("L01")
    assert l1 is not None
    assert "asdf" in l1["text"]
    assert get_lesson("ZZZ") is None


def test_get_lesson_index():
    assert get_lesson_index("L01") == 0
    assert get_lesson_index("L15") == 14
    assert get_lesson_index("ZZZ") == -1
"""Tests for test_texts and sound generation (no Qt required)."""
from src.core.test_texts import get_texts, get_random_text, LEVEL_NAMES, EASY_TEXTS, MEDIUM_TEXTS, HARD_TEXTS


def test_text_counts():
    assert len(EASY_TEXTS) == 20
    assert len(MEDIUM_TEXTS) == 20
    assert len(HARD_TEXTS) == 20


def test_get_texts():
    assert get_texts("easy") == EASY_TEXTS
    assert get_texts("medium") == MEDIUM_TEXTS
    assert get_texts("hard") == HARD_TEXTS
    assert get_texts("unknown") == MEDIUM_TEXTS


def test_get_random_text():
    text = get_random_text("easy")
    assert text in EASY_TEXTS


def test_level_names():
    assert LEVEL_NAMES[0] == "easy"
    assert LEVEL_NAMES[1] == "medium"
    assert LEVEL_NAMES[2] == "hard"


def test_all_texts_have_content():
    for text in EASY_TEXTS + MEDIUM_TEXTS + HARD_TEXTS:
        assert len(text) > 10
        assert not text.startswith(" ")
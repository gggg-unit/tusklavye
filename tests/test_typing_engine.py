"""Tests for the TypingEngine state machine."""
from src.core.typing_engine import TypingEngine


def test_basic_completion(engine):
    engine.reset("merhaba")
    for ch in "merhaba":
        engine.process_key(ch)
    assert engine.is_finished
    result = engine.get_result()
    assert result.correct_chars == 7
    assert result.incorrect_chars == 0
    assert result.accuracy == 100.0


def test_errors_tracked(engine):
    engine.reset("asdf")
    engine.process_key("a")
    engine.process_key("x")
    engine.process_key("d")
    engine.process_key("f")
    result = engine.get_result()
    assert result.correct_chars == 3
    assert result.incorrect_chars == 1
    assert result.accuracy == 75.0


def test_backspace_correction(engine):
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


def test_char_status(engine):
    engine.reset("abc")
    assert engine.char_status(0) == "current"
    engine.process_key("a")
    assert engine.char_status(0) == "correct"
    assert engine.char_status(1) == "current"
    assert engine.char_status(2) == "pending"


def test_newline_autoskip(engine):
    engine.reset("ab\ncd")
    assert engine.position == 0
    engine.process_key("a")
    engine.process_key("b")
    assert engine.position == 3
    assert engine.target_text[engine.position] == "c"
    engine.process_key("c")
    engine.process_key("d")
    assert engine.is_finished
    assert engine.get_result().accuracy == 100.0


def test_backspace_past_newline(engine):
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


def test_empty_text(engine):
    engine.reset("")
    assert engine.is_finished
    assert engine.position == 0
    result = engine.get_result()
    assert result.total_chars == 0
    assert result.accuracy == 100.0


def test_backspace_after_finish(engine):
    engine.reset("ab")
    engine.process_key("a")
    engine.process_key("b")
    assert engine.is_finished
    engine.backspace()
    assert not engine.is_finished
    assert engine.position == 1
    engine.process_key("b")
    assert engine.is_finished


def test_newline_not_inflating_wpm(engine):
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


def test_backspace_decrements_key_counts(engine):
    engine.reset("abc")
    engine.process_key("a")
    engine.process_key("b")
    assert engine.key_counts.get("a", {}).get("correct", 0) == 1
    assert engine.key_counts.get("b", {}).get("correct", 0) == 1
    engine.backspace()
    assert engine.key_counts.get("b") is None
    assert engine.key_counts.get("a", {}).get("correct", 0) == 1


def test_process_key_returns_true_when_finished(engine):
    engine.reset("ab")
    engine.process_key("a")
    engine.process_key("b")
    assert engine.is_finished
    assert engine.process_key("x") is True


def test_multi_char_input_guard(engine):
    engine.reset("abc")
    assert engine.process_key("ab") is True
    assert engine.position == 0


def test_elapsed_clamped_to_zero(engine):
    engine.reset("abc")
    engine.process_key("a")
    engine._paused_duration = 999999.0
    assert engine.elapsed_seconds == 0.0


def test_last_expected_property(engine):
    engine.reset("abc")
    assert engine.last_expected == ""
    engine.process_key("a")
    assert engine.last_expected == "a"
    engine.process_key("b")
    assert engine.last_expected == "b"


def test_pause_resume(engine):
    engine.reset("abc")
    engine.process_key("a")
    engine.pause()
    paused_elapsed = engine.elapsed_seconds
    engine.resume()
    assert engine.elapsed_seconds >= paused_elapsed
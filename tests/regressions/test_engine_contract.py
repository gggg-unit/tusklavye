"""Deterministic engine timing and independent result contracts."""
from datetime import datetime, timedelta

import pytest

from src.core.typing_engine import TypingEngine


@pytest.fixture
def clock(monkeypatch):
    class Clock:
        value = datetime(2026, 1, 1)
        tick = 0.0

        @classmethod
        def monotonic(cls):
            return cls.tick

        @classmethod
        def now(cls):
            return cls.value

        @classmethod
        def advance(cls, seconds):
            cls.value += timedelta(seconds=seconds)
            cls.tick += seconds

    monkeypatch.setattr("src.core.typing_engine.datetime", Clock)
    monkeypatch.setattr("src.core.typing_engine.monotonic", Clock.monotonic)
    return Clock


def test_pause_freezes_elapsed(clock):
    engine = TypingEngine()
    engine.reset("abc")
    engine.process_key("a")
    clock.advance(10)
    engine.pause()
    before = engine.elapsed_seconds
    clock.advance(20)
    assert engine.elapsed_seconds == before


def test_pause_rejects_input(clock):
    engine = TypingEngine()
    engine.reset("abc")
    engine.process_key("a")
    engine.pause()
    engine.process_key("b")
    assert engine.position == 1


def test_finish_freezes_result_duration(clock):
    engine = TypingEngine()
    engine.reset("ab")
    engine.process_key("a")
    clock.advance(10)
    engine.process_key("b")
    before = engine.get_result().duration_seconds
    clock.advance(20)
    assert engine.get_result().duration_seconds == before


def test_result_survives_later_edits(clock):
    engine = TypingEngine()
    engine.reset("abc")
    engine.process_key("a")
    engine.process_key("b")
    result = engine.get_result()
    engine.backspace()
    assert result.key_counts["b"]["correct"] == 1


def test_repeated_pause_resume_excludes_all_idle_time(clock):
    engine = TypingEngine()
    engine.reset("abc")
    engine.start()
    clock.advance(5)
    engine.pause()
    clock.advance(10)
    engine.pause()
    clock.advance(10)
    engine.resume()
    engine.resume()
    clock.advance(3)
    engine.pause()
    clock.advance(50)
    engine.resume()
    assert engine.elapsed_seconds == 8


def test_pause_before_first_input_blocks_start_and_backspace(clock):
    engine = TypingEngine()
    engine.reset("abc")
    engine.pause()
    clock.advance(20)
    engine.start()
    engine.process_key("a")
    engine.backspace()
    assert engine.position == 0
    assert engine.get_result().started_at == ""
    engine.resume()
    engine.process_key("a")
    clock.advance(2)
    assert engine.elapsed_seconds == 2


def test_paused_backspace_preserves_result(clock):
    engine = TypingEngine()
    engine.reset("abc")
    engine.process_key("a")
    clock.advance(3)
    engine.pause()
    before = engine.get_result()
    clock.advance(10)
    engine.backspace()
    assert engine.get_result() == before


def test_wall_clock_jump_does_not_change_duration_or_start_date(clock):
    engine = TypingEngine()
    engine.reset("abc")
    engine.process_key("a")
    started = engine.get_result().started_at
    clock.value -= timedelta(days=3)
    clock.tick += 7
    assert engine.elapsed_seconds == 7
    clock.value += timedelta(days=10)
    clock.tick += 2
    assert engine.elapsed_seconds == 9
    assert engine.get_result().started_at == started


@pytest.mark.parametrize("text", ["ab", "ab\n\n"])
def test_finished_result_stays_equal_until_explicit_edit(clock, text):
    engine = TypingEngine()
    engine.reset(text)
    engine.process_key("a")
    clock.advance(10)
    engine.process_key("b")
    before = engine.get_result()
    assert before.duration_seconds == 10
    assert before.wpm == before.raw_wpm == 2.4
    clock.advance(60)
    engine.pause()
    engine.resume()
    engine.start()
    engine.finish()
    engine.process_key("x")
    assert engine.get_result() == before


def test_explicit_finish_during_pause_uses_active_duration(clock):
    engine = TypingEngine()
    engine.reset("abc")
    engine.process_key("a")
    clock.advance(5)
    engine.pause()
    clock.advance(20)
    engine.finish()
    engine.resume()
    clock.advance(20)
    assert engine.is_finished
    assert engine.elapsed_seconds == 5


def test_edit_after_finish_excludes_waiting_time(clock):
    engine = TypingEngine()
    engine.reset("ab")
    engine.process_key("a")
    clock.advance(5)
    engine.process_key("b")
    snapshot = engine.get_result()
    clock.advance(100)
    engine.backspace()
    assert not engine.is_finished
    assert engine.elapsed_seconds == 5
    clock.advance(2)
    engine.process_key("b")
    assert engine.get_result().duration_seconds == 7
    assert snapshot.duration_seconds == 5
    assert snapshot.key_counts["b"]["correct"] == 1


def test_result_mutation_cannot_change_engine_or_another_result(clock):
    engine = TypingEngine()
    engine.reset("abc")
    engine.process_key("a")
    first = engine.get_result()
    second = engine.get_result()
    first.key_counts["a"]["correct"] = 100
    first.key_counts["x"] = {"correct": 5}
    assert engine.key_counts == second.key_counts == {"a": {"correct": 1, "incorrect": 0}}
    engine.reset("xyz")
    assert second.key_counts["a"]["correct"] == 1


def test_reset_clears_paused_and_finished_clock_state(clock):
    engine = TypingEngine()
    engine.reset("a")
    engine.process_key("a")
    clock.advance(20)
    engine.reset("ab")
    engine.pause()
    engine.reset("xy")
    assert not engine.is_paused
    assert not engine.is_finished
    assert engine.elapsed_seconds == 0
    assert engine.get_result().started_at == ""
    engine.process_key("x")
    clock.advance(4)
    assert engine.elapsed_seconds == 4


@pytest.mark.parametrize("text", ["", "\n", "\n\n"])
def test_no_real_characters_never_start_clock(clock, text):
    engine = TypingEngine()
    engine.reset(text)
    engine.start()
    engine.backspace()
    clock.advance(20)
    assert engine.is_finished
    assert engine.elapsed_seconds == 0
    assert engine.get_result().started_at == ""


def test_clock_can_be_injected_and_result_reads_it_once():
    ticks = iter([0, 0, 60])
    engine = TypingEngine(clock=lambda: next(ticks))
    engine.reset("ab")
    engine.process_key("a")
    result = engine.get_result()
    assert result.duration_seconds == 60
    assert result.wpm == result.raw_wpm == 0.2


def test_invalid_input_does_not_start_clock(clock):
    engine = TypingEngine()
    engine.reset("ab")
    engine.process_key("")
    engine.process_key("ab")
    clock.advance(10)
    assert engine.get_result().started_at == ""
    assert engine.elapsed_seconds == 0


def test_active_duration_reaches_database_without_pause_time(clock, stats_repo):
    from src.database.models import SessionRecord

    engine = TypingEngine()
    engine.reset("ab")
    engine.process_key("a")
    clock.advance(5)
    engine.pause()
    clock.advance(100)
    engine.resume()
    clock.advance(7)
    engine.process_key("b")
    clock.advance(200)
    result = engine.get_result()
    stats_repo.save_session(SessionRecord(
        mode="custom", mode_detail="test", text_content="ab", **vars(result)))
    saved = stats_repo.get_recent_sessions()[0]
    assert saved["duration_seconds"] == 12
    assert saved["wpm"] == 2.0


def test_real_qt_typing_area_pause_resume_freezes_engine(clock, app_window):
    page = app_window.pages["custom"]
    page.typing_area.set_text("abc")
    page.engine.process_key("a")
    clock.advance(4)
    page.pause_page()
    clock.advance(50)
    page.engine.process_key("b")
    page.engine.backspace()
    assert page.engine.position == 1
    assert page.engine.elapsed_seconds == 4
    page.resume_page()
    clock.advance(3)
    page.engine.process_key("b")
    assert page.engine.position == 2
    assert page.engine.elapsed_seconds == 7

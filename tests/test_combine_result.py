"""Tests for the multi-text result aggregation in TestsPage._combine_result."""
from src.core.typing_engine import TypingResult


def _make_result(**ov):
    defaults = dict(
        total_chars=100, correct_chars=90, incorrect_chars=10,
        duration_seconds=60.0, wpm=18.0, raw_wpm=20.0,
        accuracy=90.0, max_wpm=22.0,
        key_counts={"a": {"correct": 50, "incorrect": 5}},
        started_at="2026-01-01T00:00:00",
    )
    defaults.update(ov)
    return TypingResult(**defaults)


class FakeTestsPage:
    """Minimal stand-in for TestsPage to test _combine_result in isolation."""
    _time_limit = 60
    _remaining_seconds = 0
    _acc_total = 0
    _acc_correct = 0
    _acc_incorrect = 0
    _acc_key_counts: dict = {}
    _acc_max_wpm = 0.0
    _test_started_at = ""

    def _combine_result(self, current: TypingResult) -> TypingResult:
        from src.core.typing_engine import TypingResult as TR
        total_chars = self._acc_total + current.total_chars
        correct_chars = self._acc_correct + current.correct_chars
        incorrect_chars = self._acc_incorrect + current.incorrect_chars
        duration = float(self._time_limit - self._remaining_seconds)
        minutes = duration / 60.0
        wpm = round((correct_chars / 5.0) / minutes, 1) if minutes > 0 else 0.0
        raw_wpm = round((total_chars / 5.0) / minutes, 1) if minutes > 0 else 0.0
        accuracy = round(correct_chars / total_chars * 100.0, 1) if total_chars > 0 else 100.0
        key_counts = dict(self._acc_key_counts)
        for k, v in current.key_counts.items():
            entry = key_counts.setdefault(k, {"correct": 0, "incorrect": 0})
            entry["correct"] += v.get("correct", 0)
            entry["incorrect"] += v.get("incorrect", 0)
        max_wpm = max(self._acc_max_wpm, current.max_wpm, wpm)
        started_at = self._test_started_at or current.started_at
        return TR(
            total_chars=total_chars, correct_chars=correct_chars,
            incorrect_chars=incorrect_chars, duration_seconds=round(duration, 1),
            wpm=wpm, raw_wpm=raw_wpm, accuracy=accuracy, max_wpm=max_wpm,
            key_counts=key_counts, started_at=started_at,
        )


def test_combine_single_result():
    page = FakeTestsPage()
    result = _make_result()
    combined = page._combine_result(result)
    assert combined.total_chars == 100
    assert combined.correct_chars == 90
    assert combined.accuracy == 90.0


def test_combine_multiple_results():
    page = FakeTestsPage()
    page._acc_total = 100
    page._acc_correct = 80
    page._acc_incorrect = 20
    page._acc_max_wpm = 25.0
    page._acc_key_counts = {"a": {"correct": 40, "incorrect": 10}}
    page._test_started_at = "2026-01-01T00:00:00"

    current = _make_result(total_chars=50, correct_chars=45, incorrect_chars=5, max_wpm=30.0)
    combined = page._combine_result(current)
    assert combined.total_chars == 150
    assert combined.correct_chars == 125
    assert combined.incorrect_chars == 25
    assert combined.max_wpm == 30.0
    assert combined.key_counts["a"]["correct"] == 90
    assert combined.key_counts["a"]["incorrect"] == 15


def test_combine_accuracy_calculation():
    page = FakeTestsPage()
    page._acc_total = 50
    page._acc_correct = 50
    page._acc_incorrect = 0
    current = _make_result(total_chars=50, correct_chars=40, incorrect_chars=10)
    combined = page._combine_result(current)
    assert combined.accuracy == 90.0


def test_combine_empty_accumulators():
    page = FakeTestsPage()
    result = _make_result()
    combined = page._combine_result(result)
    assert combined.total_chars == result.total_chars
    assert combined.wpm >= 0
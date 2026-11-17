"""Core typing engine: tracks keystrokes, computes WPM and accuracy in real time.

The engine is a small state machine: it holds the target text, the typed
characters, per-position error flags, and per-key correct/incorrect counts.
Newlines in the target text are auto-skipped (the user never types Enter).
"""
from __future__ import annotations

import logging
import unicodedata
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from time import monotonic

from .keyboard_layout import KeyboardLayout

logger = logging.getLogger(__name__)

WPM_WORD_CHARS = 5.0


def normalize_text(text: str) -> str:
    """NFC text; CR/LF are layout breaks, tabs expand to four typeable spaces."""
    text = unicodedata.normalize("NFC", text.replace("\r\n", "\n").replace("\r", "\n").replace("\t", "    "))
    if any(not char.isprintable() and char != "\n" for char in text):
        raise ValueError("Metin desteklenmeyen görünmez kontrol karakteri içeriyor.")
    return text


@dataclass
class TypingResult:
    """Snapshot of a completed (or in-progress) typing session."""
    total_chars: int = 0
    correct_chars: int = 0
    incorrect_chars: int = 0
    duration_seconds: float = 0.0
    wpm: float = 0.0
    raw_wpm: float = 0.0
    accuracy: float = 0.0
    max_wpm: float = 0.0
    key_counts: dict = field(default_factory=dict)
    started_at: str = ""


class TypingEngine:
    """Stateful typing tracker — processes keystrokes and computes live stats."""

    def __init__(self, layout: KeyboardLayout | None = None, *,
                 clock: Callable[[], float] | None = None):
        self._clock = clock or monotonic
        self.layout = layout or KeyboardLayout()
        self.reset("")

    def reset(self, text: str) -> None:
        """Reset the engine for a new target text."""
        self.target_text = normalize_text(text)
        self.typed_chars: list = []
        self.errors_at: list = []
        self._expected_chars: list = []
        self.key_counts: dict = {}
        self._start_time: datetime | None = None
        self._max_wpm = 0.0
        self._finished = False
        self._paused_duration: float = 0.0
        self._pause_time: float | None = None
        self._start_tick: float | None = None
        self._finish_tick: float | None = None
        self._newline_count = 0
        self._last_expected = ""
        self._skip_newlines()

    @property
    def position(self) -> int:
        return len(self.typed_chars)

    @property
    def is_finished(self) -> bool:
        return self._finished or (
            len(self.target_text) > 0 and self.position >= len(self.target_text)
        )

    @property
    def elapsed_seconds(self) -> float:
        if self._start_tick is None:
            return 0.0
        end = self._finish_tick
        if end is None:
            end = self._pause_time if self._pause_time is not None else self._clock()
        return max(0.0, end - self._start_tick - self._paused_duration)

    @property
    def is_paused(self) -> bool:
        return self._pause_time is not None

    @property
    def typed_char_count(self) -> int:
        """Number of real (non-newline) typed characters."""
        return sum(1 for c in self.typed_chars if c != "\n")

    @property
    def last_expected(self) -> str:
        """The most recently expected character (public; avoids private access from pages)."""
        return self._last_expected

    def pause(self) -> None:
        if not self.is_finished and not self.is_paused:
            self._pause_time = self._clock()

    def resume(self) -> None:
        if self.is_paused:
            if self._start_tick is not None and not self.is_finished:
                self._paused_duration += self._clock() - self._pause_time
            self._pause_time = None

    def start(self) -> None:
        if self._start_tick is None and not self.is_paused and not self.is_finished:
            self._start_tick = self._clock()
            self._start_time = datetime.now()

    def finish(self) -> None:
        """Freeze active time; repeated completion is harmless."""
        if self._finish_tick is None and self._start_tick is not None:
            self._finish_tick = (
                self._pause_time if self.is_paused else self._clock()
            )
        self._finished = True

    def process_key(self, char: str) -> bool:
        """Process a typed character. Returns True if correct, False if incorrect.

        Returns True (no-op) if paused, already finished, or input is invalid.
        """
        if self.is_paused or self.is_finished or self.position >= len(self.target_text):
            return True
        char = unicodedata.normalize("NFC", char)
        if not char or len(char) != 1 or not char.isprintable():
            return True
        if self.target_text[self.position] == "\n":
            self._skip_newlines()
        if self.is_finished or self.position >= len(self.target_text):
            return True
        self.start()
        expected = self.target_text[self.position]
        correct = char == expected
        self.typed_chars.append(char)
        self.errors_at.append(0 if correct else 1)
        self._expected_chars.append(expected)
        self._last_expected = expected
        self._record_key(expected, correct)
        self._skip_newlines()
        self._update_max_wpm()
        return correct

    def _skip_newlines(self):
        """Auto-advance past newline characters — user never types Enter."""
        while (self.position < len(self.target_text)
               and self.target_text[self.position] == "\n"):
            self.typed_chars.append("\n")
            self.errors_at.append(0)
            self._expected_chars.append("\n")
            self._newline_count += 1
        if self.position >= len(self.target_text):
            self.finish()

    def _record_key(self, expected_char: str, correct: bool):
        entry = self.key_counts.setdefault(
            expected_char, {"correct": 0, "incorrect": 0}
        )
        if correct:
            entry["correct"] += 1
        else:
            entry["incorrect"] += 1

    def backspace(self):
        """Remove the last typed character (skipping auto-inserted newlines)."""
        if self.is_paused or self.typed_char_count == 0:
            return
        # Preserve explicit post-completion editing, excluding the idle interval.
        if self._finish_tick is not None:
            self._paused_duration += self._clock() - self._finish_tick
            self._finish_tick = None
        while self.typed_chars and self.typed_chars[-1] == "\n":
            self.typed_chars.pop()
            self.errors_at.pop()
            self._expected_chars.pop()
        if self.typed_chars:
            self.typed_chars.pop()
            was_correct = self.errors_at.pop()
            expected = self._expected_chars.pop()
            entry = self.key_counts.get(expected)
            if entry:
                if was_correct == 0:
                    entry["correct"] = max(0, entry["correct"] - 1)
                else:
                    entry["incorrect"] = max(0, entry["incorrect"] - 1)
                if entry["correct"] == 0 and entry["incorrect"] == 0:
                    del self.key_counts[expected]
        self._finished = False

    def _update_max_wpm(self):
        current = self.current_wpm()
        if current > self._max_wpm:
            self._max_wpm = current

    def correct_count(self) -> int:
        return sum(
            1 for i, e in enumerate(self.errors_at)
            if e == 0 and self.typed_chars[i] != "\n"
        )

    def incorrect_count(self) -> int:
        return sum(self.errors_at)

    def current_wpm(self) -> float:
        minutes = self.elapsed_seconds / 60.0
        if minutes <= 0:
            return 0.0
        words = self.correct_count() / WPM_WORD_CHARS
        return round(words / minutes, 1)

    def raw_wpm(self) -> float:
        minutes = self.elapsed_seconds / 60.0
        if minutes <= 0:
            return 0.0
        return round((self.typed_char_count / WPM_WORD_CHARS) / minutes, 1)

    def current_accuracy(self) -> float:
        real_typed = self.typed_char_count
        if real_typed == 0:
            return 100.0
        return round(self.correct_count() / real_typed * 100.0, 1)

    def max_wpm(self) -> float:
        return round(self._max_wpm, 1)

    def get_result(self) -> TypingResult:
        duration = self.elapsed_seconds
        minutes = duration / 60.0
        return TypingResult(
            total_chars=self.typed_char_count,
            correct_chars=self.correct_count(),
            incorrect_chars=self.incorrect_count(),
            duration_seconds=round(duration, 1),
            wpm=round(self.correct_count() / WPM_WORD_CHARS / minutes, 1) if minutes > 0 else 0.0,
            raw_wpm=round(self.typed_char_count / WPM_WORD_CHARS / minutes, 1) if minutes > 0 else 0.0,
            accuracy=self.current_accuracy(),
            max_wpm=self.max_wpm(),
            key_counts={key: counts.copy() for key, counts in self.key_counts.items()},
            started_at=self._start_time.isoformat(timespec="seconds") if self._start_time else "",
        )

    def remaining_text(self) -> str:
        return self.target_text[self.position:]

    def char_status(self, index: int) -> str:
        """Return 'correct', 'incorrect', 'current', or 'pending' for display."""
        if index < self.position:
            return "incorrect" if self.errors_at[index] else "correct"
        if index == self.position:
            return "current"
        return "pending"

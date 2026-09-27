"""Tests page: timed tests (1/3/5 min) with difficulty levels and custom duration."""
from __future__ import annotations

import random

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QFrame, QPushButton, QComboBox, QSpinBox,
)

from ...core.typing_engine import TypingEngine, TypingResult
from ...core.test_texts import get_texts, LEVEL_NAMES
from ...database.models import SessionRecord
from ..widgets.typing_area import TypingArea
from ..widgets.finger_guide import FingerGuide
from ..widgets.results_dialog import ResultsDialog
from .base import BasePage, TypingPageMixin

DURATION_PRESETS = [60, 180, 300]
TICK_MS = 1000
WPM_WORD_CHARS = 5.0


class TestsPage(BasePage, TypingPageMixin):
    """Timed typing tests with difficulty selection and multi-text aggregation."""

    def __init__(self, ctx, parent=None):
        super().__init__(ctx, parent)
        self.engine = TypingEngine(self.ctx.layout)
        self.add_header_with_stats(
            "Testler", "Zamana karşı yarış ve hız testleri",
            self.ctx.show_timer, self.ctx.show_wpm,
        )
        self._test_active = False
        self._saved = False
        self._time_limit = DURATION_PRESETS[0]
        self._last_test_text = ""
        self._init_typing_mixin()
        self._build_ui()
        self._load_random_text()

    def _load_random_text(self) -> None:
        level_idx = random.randint(0, 2)
        self.level_combo.setCurrentIndex(level_idx)
        level = LEVEL_NAMES.get(level_idx, "medium")
        texts = get_texts(level)
        if texts:
            text = random.choice(texts)
            self.typing_area.set_text(text)
            self._highlight_next_key()

    def _build_ui(self) -> None:
        controls = QFrame()
        controls.setObjectName("card")
        ctrl_layout = QHBoxLayout(controls)
        ctrl_layout.setContentsMargins(16, 12, 16, 12)

        ctrl_layout.addWidget(QLabel("Seviye:"))
        self.level_combo = QComboBox()
        self.level_combo.addItems(["Kolay", "Orta", "Zor"])
        self.level_combo.setCurrentIndex(1)
        ctrl_layout.addWidget(self.level_combo)

        ctrl_layout.addWidget(QLabel("Süre:"))
        self.duration_combo = QComboBox()
        self.duration_combo.addItems(["1 dakika", "3 dakika", "5 dakika", "Özel"])
        self.duration_combo.currentIndexChanged.connect(self._on_duration_changed)
        ctrl_layout.addWidget(self.duration_combo)

        self.custom_spin = QSpinBox()
        self.custom_spin.setRange(1, 30)
        self.custom_spin.setValue(2)
        self.custom_spin.setSuffix(" dk")
        self.custom_spin.setVisible(False)
        ctrl_layout.addWidget(self.custom_spin)

        ctrl_layout.addStretch()

        self.start_btn = QPushButton("Testi Başlat")
        self.start_btn.setObjectName("primary")
        self.start_btn.clicked.connect(self._start_test)
        ctrl_layout.addWidget(self.start_btn)

        self._root.addWidget(controls)

        self.typing_area = TypingArea(self.engine, self.ctx.font_size, self.ctx.show_timer, self.ctx.theme)
        self._root.addWidget(self.typing_area)
        self.typing_area.finished.connect(self._on_finished)
        self.typing_area.statsUpdated.connect(self.update_header_stats)

        self.finger_guide = FingerGuide(self.ctx.layout)
        self._root.addWidget(self.finger_guide)

        self._countdown_timer = QTimer(self)
        self._countdown_timer.timeout.connect(self._on_countdown_tick)
        self._remaining_seconds = 0

        self.time_left_lbl = QLabel(self._format_time(self._get_duration()))
        self.time_left_lbl.setObjectName("statValue")
        self.time_left_lbl.setAlignment(Qt.AlignCenter)
        self._root.addWidget(self.time_left_lbl)
        self.custom_spin.valueChanged.connect(self._on_custom_spin_changed)

    def _format_time(self, seconds: int) -> str:
        m, s = divmod(seconds, 60)
        return f"Kalan: {m}:{s:02d}"

    def _on_duration_changed(self, idx: int) -> None:
        self.custom_spin.setVisible(idx == 3)
        if not self._test_active:
            self.time_left_lbl.setText(self._format_time(self._get_duration()))

    def _on_custom_spin_changed(self) -> None:
        if not self._test_active and self.duration_combo.currentIndex() == 3:
            self.time_left_lbl.setText(self._format_time(self._get_duration()))

    def _get_duration(self) -> int:
        idx = self.duration_combo.currentIndex()
        if idx < len(DURATION_PRESETS):
            return DURATION_PRESETS[idx]
        return self.custom_spin.value() * 60

    def _start_test(self) -> None:
        level = LEVEL_NAMES.get(self.level_combo.currentIndex(), "medium")
        text = random.choice(get_texts(level))
        self._last_test_text = text
        self._start_test_with_text(text)

    def _retry_test(self) -> None:
        if self._last_test_text:
            self._start_test_with_text(self._last_test_text)
        else:
            self._start_test()

    def _start_test_with_text(self, text: str) -> None:
        self._time_limit = self._get_duration()
        self._remaining_seconds = self._time_limit
        self._test_active = True
        self._saved = False
        self._acc_total = 0
        self._acc_correct = 0
        self._acc_incorrect = 0
        self._acc_key_counts: dict = {}
        self._acc_text_parts: list = []
        self._acc_max_wpm = 0.0
        self._test_started_at = ""
        self.typing_area.set_text(text)

        self.time_left_lbl.setText(self._format_time(self._remaining_seconds))
        self._countdown_timer.start(TICK_MS)
        self.start_btn.setText("Testi Yeniden Başlat")
        self._highlight_next_key()
        self.window().setFocus()

    def _on_countdown_tick(self) -> None:
        self._remaining_seconds -= 1
        self.time_left_lbl.setText(self._format_time(self._remaining_seconds))
        if self._remaining_seconds <= 0:
            self._countdown_timer.stop()
            self._force_finish()

    def _force_finish(self) -> None:
        if self._saved or self.engine.is_finished:
            return
        self._saved = True
        self._test_active = False
        self.typing_area.stop()
        result = self.engine.get_result()
        combined = self._combine_result(result)
        self._save_and_show(combined)

    def _is_active(self) -> bool:
        return self._test_active

    def _on_finished(self, result) -> None:
        if self._saved:
            return
        if self._test_active and self._remaining_seconds > 0:
            self._acc_total += result.total_chars
            self._acc_correct += result.correct_chars
            self._acc_incorrect += result.incorrect_chars
            self._acc_max_wpm = max(self._acc_max_wpm, result.max_wpm)
            for k, v in result.key_counts.items():
                entry = self._acc_key_counts.setdefault(k, {"correct": 0, "incorrect": 0})
                entry["correct"] += v.get("correct", 0)
                entry["incorrect"] += v.get("incorrect", 0)
            self._acc_text_parts.append(self.engine.target_text)
            if not self._test_started_at:
                self._test_started_at = result.started_at

            level = LEVEL_NAMES.get(self.level_combo.currentIndex(), "medium")
            text = random.choice(get_texts(level))
            self.typing_area.set_text(text)
            self._highlight_next_key()
            return
        self._saved = True
        self._countdown_timer.stop()
        self._test_active = False
        self.time_left_lbl.setText(self._format_time(self._get_duration()))
        combined = self._combine_result(result)
        self._save_and_show(combined)

    def _combine_result(self, current: TypingResult) -> TypingResult:
        total_chars = self._acc_total + current.total_chars
        correct_chars = self._acc_correct + current.correct_chars
        incorrect_chars = self._acc_incorrect + current.incorrect_chars
        duration = float(self._time_limit - self._remaining_seconds)
        minutes = duration / 60.0
        wpm = round((correct_chars / WPM_WORD_CHARS) / minutes, 1) if minutes > 0 else 0.0
        raw_wpm = round((total_chars / WPM_WORD_CHARS) / minutes, 1) if minutes > 0 else 0.0
        accuracy = round(correct_chars / total_chars * 100.0, 1) if total_chars > 0 else 100.0
        key_counts = dict(self._acc_key_counts)
        for k, v in current.key_counts.items():
            entry = key_counts.setdefault(k, {"correct": 0, "incorrect": 0})
            entry["correct"] += v.get("correct", 0)
            entry["incorrect"] += v.get("incorrect", 0)
        max_wpm = max(self._acc_max_wpm, current.max_wpm, wpm)
        started_at = self._test_started_at or current.started_at
        return TypingResult(
            total_chars=total_chars,
            correct_chars=correct_chars,
            incorrect_chars=incorrect_chars,
            duration_seconds=round(duration, 1),
            wpm=wpm,
            raw_wpm=raw_wpm,
            accuracy=accuracy,
            max_wpm=max_wpm,
            key_counts=key_counts,
            started_at=started_at,
        )

    def _save_and_show(self, result) -> None:
        self.ctx.sound.play_success()
        self.finger_guide.clear()
        full_text = "".join(self._acc_text_parts) + self.engine.target_text
        record = SessionRecord(
            mode="test",
            mode_detail=f"{self._time_limit}s",
            text_content=full_text,
            total_chars=result.total_chars,
            correct_chars=result.correct_chars,
            incorrect_chars=result.incorrect_chars,
            wpm=result.wpm,
            raw_wpm=result.raw_wpm,
            accuracy=result.accuracy,
            max_wpm=result.max_wpm,
            key_counts=result.key_counts,
            started_at=result.started_at,
        )
        self._save_session(record)
        self._check_achievements()
        dialog = ResultsDialog(result, "Test Tamamlandı", self, show_retry=True, show_next=True)
        dialog.retry_requested.connect(self._retry_test)
        dialog.next_requested.connect(self._start_test)
        dialog.exec()
        self.start_btn.setText("Testi Başlat")

    def pause_page(self) -> None:
        self.typing_area.pause()
        self._countdown_timer.stop()
        if self._test_active and not self.engine.is_finished:
            self.time_left_lbl.setText("⏸️ Duraklatıldı")

    def resume_page(self) -> None:
        if self._test_active and not self.engine.is_finished:
            self.typing_area.resume()
            self._countdown_timer.start(TICK_MS)
            self.time_left_lbl.setText(self._format_time(self._remaining_seconds))

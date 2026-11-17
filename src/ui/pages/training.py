"""Training page: lesson list + typing practice with virtual keyboard and finger guide."""
from __future__ import annotations

from typing import Optional

from PySide6.QtCore import Qt, QSignalBlocker
from PySide6.QtWidgets import (
    QVBoxLayout, QLabel, QFrame, QListWidget, QListWidgetItem, QSplitter, QScrollArea, QWidget,
)

from ...core.lessons import LESSONS, meets_lesson_target
from ...core.typing_engine import TypingEngine
from ...database.models import SessionRecord
from ..widgets.typing_area import TypingArea
from ..widgets.virtual_keyboard import VirtualKeyboard
from ..widgets.finger_guide import FingerGuide
from ..widgets.results_dialog import ResultsDialog
from .base import BasePage, TypingPageMixin


class TrainingPage(BasePage, TypingPageMixin):
    """Lesson-based training with progressive difficulty and a virtual keyboard."""

    def __init__(self, ctx, parent=None):
        super().__init__(ctx, parent)
        self.engine = TypingEngine(self.ctx.layout)
        self.current_lesson: Optional[dict] = None
        self.add_header_with_stats(
            "Eğitim", "Adım adım derslerle 10 parmak yazmayı öğren",
            self.ctx.show_timer, self.ctx.show_wpm,
        )
        self._init_typing_mixin()
        self._build_ui()
        self._load_lessons()

    def _build_ui(self) -> None:
        splitter = QSplitter(Qt.Horizontal)

        left = QFrame()
        left.setObjectName("card")
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(12, 12, 12, 12)
        left_layout.addWidget(QLabel("Dersler"))
        self.lesson_list = QListWidget()
        self.lesson_list.currentRowChanged.connect(self._on_lesson_selected)
        left_layout.addWidget(self.lesson_list)
        splitter.addWidget(left)

        right = QWidget()
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(10)

        info_card = QFrame()
        info_card.setObjectName("card")
        info_layout = QVBoxLayout(info_card)
        info_layout.setContentsMargins(16, 12, 16, 12)
        self.lesson_title_lbl = QLabel("Bir ders seç")
        self.lesson_title_lbl.setWordWrap(True)
        self.lesson_title_lbl.setObjectName("pageTitle")
        self.lesson_desc_lbl = QLabel("")
        self.lesson_desc_lbl.setWordWrap(True)
        self.lesson_desc_lbl.setObjectName("pageSubtitle")
        info_layout.addWidget(self.lesson_title_lbl)
        info_layout.addWidget(self.lesson_desc_lbl)
        right_layout.addWidget(info_card)

        self.finger_guide = FingerGuide(self.ctx.layout)
        right_layout.addWidget(self.finger_guide)

        self.typing_area = TypingArea(self.engine, self.ctx.font_size, self.ctx.show_timer, self.ctx.theme)
        right_layout.addWidget(self.typing_area)
        self.typing_area.finished.connect(self._on_finished)
        self.typing_area.statsUpdated.connect(self.update_header_stats)

        self.keyboard = VirtualKeyboard(self.ctx.layout)
        self.keyboard.keyPressed.connect(self.on_key_press)
        right_layout.addWidget(self.keyboard)
        right_layout.addStretch(1)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(right)
        splitter.addWidget(scroll)
        splitter.setSizes([260, 700])
        self._root.addWidget(splitter, 1)
        self._root.addWidget(QLabel("✓ Metin bitirildi   ★ Hız ve doğruluk hedefine ulaşıldı"))

    def _load_lessons(self) -> None:
        completed = self.ctx.lesson_repo.get_completed()
        mastered = self.ctx.lesson_repo.get_mastered()
        selected_id = self.current_lesson["id"] if self.current_lesson else None
        with QSignalBlocker(self.lesson_list):
            self.lesson_list.clear()
            for index, lesson in enumerate(LESSONS):
                status = "★ " if lesson["id"] in mastered else ("✓ " if lesson["id"] in completed else "○ ")
                item = QListWidgetItem(f"{status}{lesson['id']} - {lesson['title']}")
                item.setData(Qt.UserRole, lesson)
                self.lesson_list.addItem(item)
                if lesson["id"] == selected_id:
                    self.lesson_list.setCurrentRow(index)

    def _on_lesson_selected(self, row: int) -> None:
        if row < 0:
            return
        if not self._prepare_session():
            self.lesson_list.blockSignals(True)
            for index in range(self.lesson_list.count()):
                item = self.lesson_list.item(index)
                if self.current_lesson and item.data(Qt.UserRole)["id"] == self.current_lesson["id"]:
                    self.lesson_list.setCurrentRow(index)
                    break
            self.lesson_list.blockSignals(False)
            return
        item = self.lesson_list.item(row)
        lesson = item.data(Qt.UserRole)
        self.current_lesson = lesson
        self.lesson_title_lbl.setText(lesson["title"])
        self.lesson_desc_lbl.setText(
            f"{lesson['description']}  •  Hedef: {lesson['target_wpm']} WPM + %{lesson['target_accuracy']:.0f} doğruluk"
        )
        self.typing_area.set_text(lesson["text"])
        self.keyboard.clear_highlights()
        self._highlight_next_key()
        self.typing_area.setFocus()

    def _is_active(self) -> bool:
        return self.current_lesson is not None

    def _on_finished(self, result) -> None:
        if self.session.pending is not None:
            return
        self.typing_area.stop()
        self.keyboard.clear_highlights()
        self.finger_guide.clear()
        record = SessionRecord(
            mode="lesson",
            mode_detail=self.current_lesson["id"],
            text_content=self.current_lesson["text"],
            total_chars=result.total_chars,
            correct_chars=result.correct_chars,
            incorrect_chars=result.incorrect_chars,
            wpm=result.wpm,
            raw_wpm=result.raw_wpm,
            accuracy=result.accuracy,
            max_wpm=result.max_wpm,
            key_counts=result.key_counts,
            started_at=result.started_at,
            duration_seconds=result.duration_seconds,
        )
        if not self._save_session(record, completed=True):
            return
        if result.total_chars == 0:
            return
        self.ctx.sound.play_success()
        self._load_lessons()
        is_last = self.current_lesson["id"] == LESSONS[-1]["id"]
        mastered_now = meets_lesson_target(self.current_lesson, result) if "target_wpm" in self.current_lesson else False
        title = "Hedefe Ulaşıldı" if mastered_now else "Metin Bitti — Hedef İçin Tekrar Çalış"
        dialog = ResultsDialog(result, title, self, show_retry=True,
                               show_next=not is_last and mastered_now)
        dialog.retry_requested.connect(self.retry_lesson)
        dialog.next_requested.connect(self.next_lesson)
        dialog.exec()

    def retry_lesson(self) -> None:
        if self.current_lesson and self._prepare_session():
            self.typing_area.set_text(self.current_lesson["text"])
            self.keyboard.clear_highlights()
            self._highlight_next_key()
            self.typing_area.setFocus()

    def next_lesson(self) -> None:
        if self.current_lesson:
            idx = next((i for i, l in enumerate(LESSONS) if l["id"] == self.current_lesson["id"]), 0)
            next_idx = min(idx + 1, len(LESSONS) - 1)
            self.lesson_list.setCurrentRow(next_idx)

    def refresh(self) -> None:
        self._load_lessons()

    def pause_page(self) -> None:
        self.typing_area.pause()

    def resume_page(self) -> None:
        self.typing_area.resume()

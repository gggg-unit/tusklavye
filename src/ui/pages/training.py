"""Training page: lesson list + typing practice with virtual keyboard and finger guide."""
from __future__ import annotations

from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QVBoxLayout, QLabel, QFrame, QListWidget, QListWidgetItem, QSplitter, QWidget,
)

from ...core.lessons import LESSONS
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
        self.lesson_title_lbl.setObjectName("pageTitle")
        self.lesson_desc_lbl = QLabel("")
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

        splitter.addWidget(right)
        splitter.setSizes([260, 700])
        self._root.addWidget(splitter)

    def _load_lessons(self) -> None:
        completed = self.ctx.lesson_repo.get_completed()
        self.lesson_list.clear()
        for lesson in LESSONS:
            status = "✅ " if lesson["id"] in completed else "○ "
            item = QListWidgetItem(f"{status}{lesson['id']} - {lesson['title']}")
            item.setData(Qt.UserRole, lesson)
            self.lesson_list.addItem(item)

    def _on_lesson_selected(self, row: int) -> None:
        if row < 0:
            return
        item = self.lesson_list.item(row)
        lesson = item.data(Qt.UserRole)
        self.current_lesson = lesson
        self.lesson_title_lbl.setText(lesson["title"])
        self.lesson_desc_lbl.setText(
            f"{lesson['description']}  •  Hedef: {lesson['target_wpm']} WPM"
        )
        self.typing_area.set_text(lesson["text"])
        self.keyboard.clear_highlights()
        self._highlight_next_key()
        self.window().setFocus()

    def _is_active(self) -> bool:
        return self.current_lesson is not None

    def _on_finished(self, result) -> None:
        self.ctx.sound.play_success()
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
        )
        if self._save_session(record):
            self.ctx.lesson_repo.mark_completed(
                self.current_lesson["id"], result.wpm, result.accuracy
            )
        self._check_achievements()
        self._load_lessons()
        is_last = self.current_lesson["id"] == LESSONS[-1]["id"]
        dialog = ResultsDialog(result, "Ders Tamamlandı", self, show_retry=True, show_next=not is_last)
        dialog.retry_requested.connect(self.retry_lesson)
        dialog.next_requested.connect(self.next_lesson)
        dialog.exec()

    def retry_lesson(self) -> None:
        if self.current_lesson:
            self.typing_area.set_text(self.current_lesson["text"])
            self.keyboard.clear_highlights()
            self._highlight_next_key()
            self.window().setFocus()

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

"""Base page and typing-page mixin with common header and key-press helpers."""
from __future__ import annotations

from typing import Optional

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QSizePolicy

from ...core.achievements import check_and_unlock
from ...database.models import SessionRecord


class BasePage(QWidget):
    """Base class for all pages — provides header and stat-card helpers."""

    def __init__(self, ctx, parent=None):
        super().__init__(parent)
        self.ctx = ctx
        self._root = QVBoxLayout(self)
        self._root.setContentsMargins(24, 20, 24, 20)
        self._root.setSpacing(16)

    def _clear_layout(self, layout) -> None:
        while layout.count():
            item = layout.takeAt(0)
            child = item.widget()
            if child:
                child.setParent(None)
                child.deleteLater()
            else:
                sub = item.layout()
                if sub:
                    self._clear_layout(sub)
                    sub.deleteLater()

    def add_header(self, title: str, subtitle: str = "") -> None:
        title_lbl = QLabel(title)
        title_lbl.setObjectName("pageTitle")
        sub_lbl = QLabel(subtitle)
        sub_lbl.setObjectName("pageSubtitle")
        self._root.addWidget(title_lbl)
        if subtitle:
            self._root.addWidget(sub_lbl)

    def add_header_with_stats(
        self, title: str, subtitle: str = "", show_timer: bool = False, show_wpm: bool = False
    ) -> None:
        header_row = QHBoxLayout()
        header_row.setContentsMargins(0, 0, 0, 0)

        left = QVBoxLayout()
        left.setContentsMargins(0, 0, 0, 0)
        title_lbl = QLabel(title)
        title_lbl.setObjectName("pageTitle")
        left.addWidget(title_lbl)
        if subtitle:
            sub_lbl = QLabel(subtitle)
            sub_lbl.setObjectName("pageSubtitle")
            left.addWidget(sub_lbl)
        header_row.addLayout(left)
        header_row.addStretch()

        self.header_wpm = QLabel("0.0")
        self.header_wpm.setObjectName("statValue")
        self.header_acc = QLabel("100%")
        self.header_acc.setObjectName("statValue")
        self.header_time = QLabel("0s")
        self.header_time.setObjectName("statValue")

        for lbl in (self.header_wpm, self.header_acc, self.header_time):
            header_row.addWidget(lbl)
        self.header_wpm.setVisible(show_wpm)
        self.header_time.setVisible(show_timer)
        self._root.addLayout(header_row)

    def update_header_stats(self, wpm: float, acc: float, elapsed: float) -> None:
        self.header_wpm.setText(f"{wpm:.1f}")
        self.header_acc.setText(f"{acc:.0f}%")
        self.header_time.setText(f"{elapsed:.0f}s")

    def set_header_timer_visible(self, show: bool) -> None:
        if hasattr(self, "header_time"):
            self.header_time.setVisible(show)

    def set_header_wpm_visible(self, show: bool) -> None:
        if hasattr(self, "header_wpm"):
            self.header_wpm.setVisible(show)

    def make_card(self) -> QFrame:
        card = QFrame()
        card.setObjectName("card")
        return card

    def make_stat_card(self, value: str, label: str) -> QFrame:
        card = QFrame()
        card.setObjectName("card")
        card.setFixedHeight(90)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(16, 12, 16, 12)
        val_lbl = QLabel(value)
        val_lbl.setObjectName("statValue")
        val_lbl.setAlignment(Qt.AlignCenter)
        cap_lbl = QLabel(label)
        cap_lbl.setObjectName("statLabel")
        cap_lbl.setAlignment(Qt.AlignCenter)
        layout.addWidget(val_lbl)
        layout.addWidget(cap_lbl)
        return card


class TypingPageMixin:
    """Mixin for pages with a typing engine, typing_area, and finger_guide.

    Extracts the common ``on_key_press``, ``_highlight_next_key``, session-save,
    and achievement-check logic that was duplicated across TrainingPage,
    TestsPage, and CustomTextPage.

    The host page must set:
        self.engine        — a TypingEngine
        self.finger_guide  — a FingerGuide widget
        self.ctx           — the AppContext
    and may optionally set:
        self.keyboard      — a VirtualKeyboard widget (training page only)
    The host must implement ``_is_active() -> bool``.
    """

    ERROR_FLASH_MS = 700

    def _init_typing_mixin(self) -> None:
        self._error_timer = QTimer(self)
        self._error_timer.setSingleShot(True)
        self._error_timer.timeout.connect(self._highlight_next_key)

    def _is_active(self) -> bool:
        raise NotImplementedError

    def on_key_press(self, char: str, key_text: str = "") -> None:
        if not self._is_active() or self.engine.is_finished:
            return
        if char == "\b":
            self.engine.backspace()
            self._highlight_next_key()
            return
        if not char:
            return
        correct = self.engine.process_key(char)
        if correct:
            self.ctx.sound.play_key()
            keyboard = getattr(self, "keyboard", None)
            if keyboard is not None:
                keyboard.flash_correct(char)
            self._highlight_next_key()
        else:
            self.ctx.sound.play_error()
            keyboard = getattr(self, "keyboard", None)
            if keyboard is not None:
                keyboard.flash_error(char)
            expected = self.engine.last_expected or self._fallback_expected()
            self.finger_guide.show_error(expected)
            self._error_timer.start(self.ERROR_FLASH_MS)

    def _fallback_expected(self) -> str:
        if self.engine.position > 0:
            return self.engine.target_text[self.engine.position - 1]
        return ""

    def _highlight_next_key(self) -> None:
        remaining = self.engine.remaining_text()
        keyboard = getattr(self, "keyboard", None)
        if remaining:
            next_char = remaining[0]
            if keyboard is not None:
                keyboard.highlight_next(next_char)
            self.finger_guide.update_for_next_key(next_char)
        else:
            if keyboard is not None:
                keyboard.clear_highlights()
            self.finger_guide.clear()

    def _save_session(self, record: SessionRecord) -> bool:
        """Persist a session; returns True on success, False on error."""
        try:
            self.ctx.stats_repo.save_session(record)
            return True
        except Exception as e:
            self._show_save_error(e)
            return False

    def _check_achievements(self) -> None:
        completed = len(self.ctx.lesson_repo.get_completed())
        streak = self.ctx.stats_repo.get_streak()
        check_and_unlock(
            self.ctx.stats_repo, self.ctx.achievement_repo,
            lesson_count=completed, streak=streak,
        )

    def _show_save_error(self, error: Exception) -> None:
        from PySide6.QtWidgets import QMessageBox
        from ..i18n import tr
        QMessageBox.warning(
            self,
            tr("error.save_failed", error=error),
            tr("error.save_failed_detail"),
        )

"""Achievements page: badges and gamification."""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QFrame, QGridLayout, QScrollArea, QWidget,
    QGraphicsOpacityEffect,
)

from ...core.achievements import get_definitions, check_and_unlock
from .base import BasePage

GRID_COLS = 3
CARD_MIN_HEIGHT = 110
LOCKED_OPACITY = 0.5


class AchievementsPage(BasePage):
    """Grid of achievement badges — locked ones are dimmed."""

    def __init__(self, ctx, parent=None):
        super().__init__(ctx, parent)
        self.add_header("Başarılar", "Kazandığın rozetler ve hedefler")
        self._build_ui()

    def _build_ui(self) -> None:
        streak = self.ctx.stats_repo.get_streak()
        completed_lessons = len(self.ctx.lesson_repo.get_completed())
        check_and_unlock(self.ctx.stats_repo, self.ctx.achievement_repo,
                         lesson_count=completed_lessons, streak=streak)

        unlocked = {a["code"] for a in self.ctx.achievement_repo.get_all()}

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        inner = QWidget()
        grid = QGridLayout(inner)
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setSpacing(12)

        definitions = get_definitions()
        for i, (code, title, desc, emoji) in enumerate(definitions):
            card = QFrame()
            card.setObjectName("card")
            card.setMinimumHeight(CARD_MIN_HEIGHT)
            cl = QVBoxLayout(card)
            cl.setContentsMargins(16, 12, 16, 12)

            header_row = QHBoxLayout()
            icon = QLabel(emoji)
            icon.setStyleSheet("font-size: 28px;")
            header_row.addWidget(icon)
            name = QLabel(title)
            name.setStyleSheet("font-size: 14px; font-weight: 600;")
            header_row.addWidget(name)
            header_row.addStretch()
            status = QLabel("✅" if code in unlocked else "🔒")
            status.setStyleSheet("font-size: 18px;")
            header_row.addWidget(status)
            cl.addLayout(header_row)

            desc_lbl = QLabel(desc)
            desc_lbl.setObjectName("pageSubtitle")
            cl.addWidget(desc_lbl)

            if code not in unlocked:
                effect = QGraphicsOpacityEffect(card)
                effect.setOpacity(LOCKED_OPACITY)
                card.setGraphicsEffect(effect)

            grid.addWidget(card, i // GRID_COLS, i % GRID_COLS)

        scroll.setWidget(inner)
        self._root.addWidget(scroll)

        unlocked_count = len(unlocked)
        total = len(definitions)
        progress_lbl = QLabel(f"{unlocked_count} / {total} başarının kilidi açıldı")
        progress_lbl.setObjectName("pageSubtitle")
        progress_lbl.setAlignment(Qt.AlignCenter)
        self._root.addWidget(progress_lbl)

    def refresh(self) -> None:
        self._clear_layout(self._root)
        self.add_header("Başarılar", "Kazandığın rozetler ve hedefler")
        self._build_ui()

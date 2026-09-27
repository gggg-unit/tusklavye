"""Results dialog shown after completing a lesson or test."""
from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
)

CARD_HEIGHT = 80


class ResultsDialog(QDialog):
    """Modal dialog showing WPM, accuracy, duration, and error counts."""
    retry_requested = Signal()
    next_requested = Signal()

    def __init__(self, result, title: str = "Sonuçlar", parent=None, show_retry: bool = False, show_next: bool = False):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setModal(True)
        self.setMinimumWidth(420)
        self._build(result, show_retry, show_next)

    def _build(self, result, show_retry: bool, show_next: bool) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(16)

        header = QLabel("✅ Tamamlandı!")
        header.setObjectName("pageTitle")
        header.setAlignment(Qt.AlignCenter)
        layout.addWidget(header)

        row = QHBoxLayout()
        row.setSpacing(12)
        for value, label in [
            (f"{result.wpm:.1f}", "WPM"),
            (f"{result.accuracy:.0f}%", "Doğruluk"),
            (f"{result.duration_seconds:.0f}s", "Süre"),
            (f"{result.correct_chars}", "Doğru"),
            (f"{result.incorrect_chars}", "Hata"),
        ]:
            card = QFrame()
            card.setObjectName("card")
            card.setFixedHeight(CARD_HEIGHT)
            cl = QVBoxLayout(card)
            cl.setContentsMargins(12, 8, 12, 8)
            v = QLabel(value)
            v.setObjectName("statValue")
            v.setAlignment(Qt.AlignCenter)
            c = QLabel(label)
            c.setObjectName("statLabel")
            c.setAlignment(Qt.AlignCenter)
            cl.addWidget(v)
            cl.addWidget(c)
            row.addWidget(card)
        layout.addLayout(row)

        if result.max_wpm > 0:
            max_lbl = QLabel(f"En yüksek anlık hız: {result.max_wpm:.1f} WPM")
            max_lbl.setAlignment(Qt.AlignCenter)
            max_lbl.setObjectName("pageSubtitle")
            layout.addWidget(max_lbl)

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        if show_retry:
            retry_btn = QPushButton("🔄 Tekrar Dene")
            retry_btn.setObjectName("secondary")
            retry_btn.clicked.connect(lambda: (self.accept(), self.retry_requested.emit()))
            btn_row.addWidget(retry_btn)
        if show_next:
            next_btn = QPushButton("➡️ Sonraki")
            next_btn.setObjectName("secondary")
            next_btn.clicked.connect(lambda: (self.accept(), self.next_requested.emit()))
            btn_row.addWidget(next_btn)
        close_btn = QPushButton("Kapat")
        close_btn.setObjectName("primary")
        close_btn.clicked.connect(self.accept)
        btn_row.addWidget(close_btn)
        btn_row.addStretch()
        layout.addLayout(btn_row)

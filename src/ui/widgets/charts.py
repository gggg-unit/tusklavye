"""Simple chart widgets drawn with QPainter (no external chart dependency)."""
from __future__ import annotations

from typing import List

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QPainter, QColor, QPaintEvent, QPen
from PySide6.QtWidgets import QFrame, QSizePolicy

from ...core.fonts import ui_font
from ..theme import palette

MARGIN_LEFT = 40
MARGIN_TOP = 30
MARGIN_RIGHT = 16
MARGIN_BOTTOM = 30
GRID_LINES = 5
EMPTY_MSG = "Henüz veri yok"


class LineChart(QFrame):
    """Line chart with optional theme-aware grid and axis labels."""

    def __init__(self, title: str = "", parent=None):
        super().__init__(parent)
        self.setObjectName("card")
        self.title = title
        self.data: List[float] = []
        self.color = QColor("#0067c0")
        self._theme = "dark"
        self.setMinimumHeight(200)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

    def set_theme(self, theme: str) -> None:
        self._theme = theme
        self.update()

    def set_data(self, values: list) -> None:
        self.data = [float(v) for v in values]
        self.update()

    def paintEvent(self, event: QPaintEvent) -> None:
        p = palette(self._theme)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        rect = self.rect().adjusted(MARGIN_LEFT, MARGIN_TOP, -MARGIN_RIGHT, -MARGIN_BOTTOM)

        text_color = QColor(p["text_secondary"])
        grid_color = QColor(p["grid"])
        empty_color = QColor(p["empty"])

        painter.setFont(QFont(ui_font(), 11, QFont.Bold))
        painter.setPen(text_color)
        painter.drawText(16, 20, self.title)

        if not self.data:
            painter.setFont(QFont(ui_font(), 11))
            painter.setPen(empty_color)
            painter.drawText(rect, Qt.AlignCenter, EMPTY_MSG)
            painter.end()
            return

        max_val = max(self.data) if self.data else 1
        min_val = min(self.data) if self.data else 0
        val_range = max(max_val - min_val, 1)

        painter.setPen(QPen(grid_color, 1))
        for i in range(GRID_LINES):
            y = rect.top() + rect.height() * i / (GRID_LINES - 1)
            painter.drawLine(rect.left(), int(y), rect.right(), int(y))
            label_val = max_val - val_range * i / (GRID_LINES - 1)
            painter.setFont(QFont(ui_font(), 8))
            painter.setPen(text_color)
            painter.drawText(4, int(y + 4), f"{label_val:.0f}")
            painter.setPen(QPen(grid_color, 1))

        pen = QPen(self.color, 2)
        painter.setPen(pen)
        n = len(self.data)
        points = []
        for i, val in enumerate(self.data):
            x = rect.left() + (rect.width() * i / (n - 1) if n > 1 else rect.width() / 2)
            y = rect.top() + rect.height() * (1 - (val - min_val) / val_range)
            points.append((x, y))
        for i in range(1, len(points)):
            painter.drawLine(int(points[i - 1][0]), int(points[i - 1][1]),
                             int(points[i][0]), int(points[i][1]))
        painter.setBrush(self.color)
        for x, y in points:
            painter.drawEllipse(int(x) - 3, int(y) - 3, 6, 6)
        painter.end()


class BarChart(QFrame):
    """Bar chart with theme-aware colors and value labels."""

    def __init__(self, title: str = "", parent=None):
        super().__init__(parent)
        self.setObjectName("card")
        self.title = title
        self.labels: List[str] = []
        self.values: List[float] = []
        self._theme = "dark"
        self.setMinimumHeight(200)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

    def set_theme(self, theme: str) -> None:
        self._theme = theme
        self.update()

    def set_data(self, labels: list, values: list) -> None:
        self.labels = labels
        self.values = [float(v) for v in values]
        self.update()

    def paintEvent(self, event: QPaintEvent) -> None:
        p = palette(self._theme)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        rect = self.rect().adjusted(MARGIN_LEFT, MARGIN_TOP, -MARGIN_RIGHT, -MARGIN_BOTTOM)

        text_color = QColor(p["text_secondary"])
        label_color = QColor(p["text_muted"])
        empty_color = QColor(p["empty"])

        painter.setFont(QFont(ui_font(), 11, QFont.Bold))
        painter.setPen(text_color)
        painter.drawText(16, 20, self.title)

        if not self.values:
            painter.setFont(QFont(ui_font(), 11))
            painter.setPen(empty_color)
            painter.drawText(rect, Qt.AlignCenter, EMPTY_MSG)
            painter.end()
            return

        max_val = max(self.values) if self.values else 1
        n = len(self.values)
        bar_w = rect.width() / n * 0.7
        gap = rect.width() / n * 0.3

        painter.setFont(QFont(ui_font(), 8))
        for i, val in enumerate(self.values):
            x = rect.left() + i * (bar_w + gap) + gap / 2
            h = rect.height() * (val / max_val) if max_val > 0 else 0
            y = rect.bottom() - h
            color = QColor(p["primary"])
            color.setHsv(color.hue(), color.saturation(), max(120, 255 - int(80 * i / max(n, 1))))
            painter.setBrush(color)
            painter.setPen(Qt.NoPen)
            painter.drawRoundedRect(int(x), int(y), int(bar_w), int(h), 4, 4)
            painter.setPen(label_color)
            label = self.labels[i] if i < len(self.labels) else ""
            painter.drawText(int(x), rect.bottom() + 14, label)
            painter.drawText(int(x), int(y - 4), f"{val:.0f}")
        painter.end()

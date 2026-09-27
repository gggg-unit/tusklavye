"""Error heatmap widget showing which keys are most frequently missed."""
from __future__ import annotations

from PySide6.QtCore import Qt, QEvent
from PySide6.QtGui import QFont, QPainter, QColor, QPaintEvent
from PySide6.QtWidgets import QWidget, QFrame, QSizePolicy, QToolTip

from ...core.keyboard_layout import KeyboardLayout
from ...core.fonts import ui_font
from ..theme import palette

KEY_W = 44
KEY_H = 44
KEY_GAP = 4
MARGIN = 20


class HeatmapWidget(QFrame):
    """Paints the keyboard layout with error-count heat coloring and tooltips."""

    def __init__(self, layout: KeyboardLayout = None, parent=None):
        super().__init__(parent)
        self.setObjectName("card")
        self.layout_def = layout or KeyboardLayout()
        self.error_data: dict = {}
        self._theme = "dark"
        self._key_rects: dict = {}
        self.setMinimumHeight(230)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setMouseTracking(True)

    def set_theme(self, theme: str) -> None:
        self._theme = theme
        self.update()

    def set_data(self, key_stats: dict) -> None:
        self.error_data = key_stats
        self.update()

    def paintEvent(self, event: QPaintEvent) -> None:
        p = palette(self._theme)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        font = QFont(ui_font(), 10, QFont.Bold)
        painter.setFont(font)
        metrics = painter.fontMetrics()

        max_errors = 1
        for stats in self.error_data.values():
            if isinstance(stats, dict):
                max_errors = max(max_errors, stats.get("incorrect", 0))

        self._key_rects = {}
        y = MARGIN
        for row in self.layout_def.rows:
            x = MARGIN
            for key in row:
                stats = self.error_data.get(key.char, {})
                errors = stats.get("incorrect", 0) if isinstance(stats, dict) else 0
                intensity = errors / max_errors if max_errors > 0 else 0
                if errors == 0:
                    bg = QColor(p["heatmap_empty_bg"])
                    text_color = QColor(p["heatmap_empty_text"])
                else:
                    r = int(255 - (255 - 231) * intensity)
                    g = int(243 - (243 - 76) * intensity)
                    b = int(205 - (205 - 60) * intensity)
                    bg = QColor(r, g, b)
                    text_color = QColor("white")
                painter.setBrush(bg)
                painter.setPen(QColor(p["heatmap_border"]))
                painter.drawRoundedRect(int(x), int(y), KEY_W, KEY_H, 6, 6)
                painter.setPen(text_color)
                painter.drawText(
                    int(x + KEY_W / 2 - metrics.horizontalAdvance(key.display) / 2),
                    int(y + KEY_H / 2 + metrics.ascent() / 2 - 2),
                    key.display,
                )
                if errors > 0:
                    painter.setFont(QFont(ui_font(), 7))
                    painter.drawText(int(x + 2), int(y + 10), str(errors))
                    painter.setFont(font)
                self._key_rects[key.char] = (int(x), int(y), KEY_W, KEY_H, errors)
                x += KEY_W + KEY_GAP
            y += KEY_H + KEY_GAP

        painter.end()

    def event(self, event: QEvent) -> bool:
        if event.type() == QEvent.ToolTip:
            pos = event.pos()
            for char, (rx, ry, rw, rh, errors) in self._key_rects.items():
                if rx <= pos.x() <= rx + rw and ry <= pos.y() <= ry + rh:
                    if errors > 0:
                        QToolTip.showText(event.globalPos(), f"'{char}': {errors} hata", self)
                    else:
                        QToolTip.showText(event.globalPos(), f"'{char}': hata yok", self)
                    return True
            QToolTip.hideText()
        return super().event(event)

"""Typing text display with 2-line windowed view — shows 2 lines at a time, advances when done."""
from __future__ import annotations

from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QFont, QFontMetrics, QPainter, QColor, QPaintEvent, QPen
from PySide6.QtWidgets import QWidget, QVBoxLayout, QFrame, QSizePolicy

from ...core.typing_engine import TypingEngine
from ...core.fonts import mono_font
from ..theme import palette

TICK_MS = 100
LINE_PADDING = 8
VERTICAL_PADDING = 20


class _TextDisplay(QFrame):
    """Paints the target text with correct/incorrect/current/pending coloring."""

    def __init__(self, engine: TypingEngine, font_size: int, theme: str = "dark", parent=None):
        super().__init__(parent)
        self.setObjectName("card")
        self.engine = engine
        self.font_size = font_size
        self._theme = theme
        self._vl_cache_key = None
        self._vl_cache = None
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self._update_height()

    def set_theme(self, theme: str) -> None:
        self._theme = theme
        self.update()

    def _update_height(self) -> None:
        font = QFont(mono_font(), self.font_size)
        metrics = QFontMetrics(font)
        line_height = metrics.height() + LINE_PADDING
        self.setFixedHeight(line_height * 2 + VERTICAL_PADDING * 2)

    def set_font_size(self, size: int) -> None:
        self.font_size = size
        self._update_height()
        self.update()

    def _calc_visual_lines(self, rect, char_width) -> list:
        lines = []
        max_chars = max(1, rect.width() // char_width)
        text = self.engine.target_text
        i = 0
        start = 0
        count = 0
        last_space = -1
        while i < len(text):
            ch = text[i]
            if ch == "\n":
                lines.append((start, i))
                i += 1
                start = i
                count = 0
                last_space = -1
            elif count >= max_chars:
                if last_space >= start:
                    lines.append((start, last_space + 1))
                    i = last_space + 1
                    start = i
                    count = 0
                    last_space = -1
                else:
                    lines.append((start, i))
                    start = i
                    count = 0
                    last_space = -1
            else:
                if ch == " ":
                    last_space = i
                i += 1
                count += 1
        if start < len(text):
            lines.append((start, len(text)))
        return lines

    def _find_current_vline(self, visual_lines, pos: int) -> int:
        for idx, (start, end) in enumerate(visual_lines):
            if start <= pos < end:
                return idx
        return len(visual_lines) - 1 if visual_lines else 0

    def paintEvent(self, event: QPaintEvent) -> None:
        super().paintEvent(event)
        p = palette(self._theme)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        rect = self.rect().adjusted(VERTICAL_PADDING, VERTICAL_PADDING, -VERTICAL_PADDING, -VERTICAL_PADDING)

        font = QFont(mono_font(), self.font_size)
        painter.setFont(font)
        metrics = painter.fontMetrics()
        line_height = metrics.height() + LINE_PADDING
        char_width = metrics.horizontalAdvance("M")

        text = self.engine.target_text
        if not text:
            painter.end()
            return

        vl_key = (len(text), rect.width(), char_width)
        if vl_key == self._vl_cache_key:
            visual_lines = self._vl_cache
        else:
            visual_lines = self._calc_visual_lines(rect, char_width)
            self._vl_cache_key = vl_key
            self._vl_cache = visual_lines
        if not visual_lines:
            painter.end()
            return

        pos = self.engine.position
        current_vline = self._find_current_vline(visual_lines, pos)
        window_start = (current_vline // 2) * 2
        window_end = min(window_start + 2, len(visual_lines))

        color_correct = QColor(p["success"])
        color_error = QColor(p["error"])
        color_error_bg = QColor(p["error_bg"])
        color_current_bg = QColor(p["warning_bg"])
        color_current = QColor(p["text"])
        color_pending = QColor(p["text_secondary"])

        y = rect.y() + metrics.ascent()
        for vline_idx in range(window_start, window_end):
            start, end = visual_lines[vline_idx]
            line_text = text[start:end].rstrip()
            visible_end = start + len(line_text)
            visible_width = len(line_text) * char_width
            x = rect.x() + (rect.width() - visible_width) / 2
            for i in range(start, visible_end):
                ch = text[i]
                status = self.engine.char_status(i)
                if status == "correct":
                    painter.setPen(color_correct)
                elif status == "incorrect":
                    painter.fillRect(
                        int(x - 2), int(y - metrics.ascent() - 2),
                        char_width + 4, line_height - 4, color_error_bg
                    )
                    painter.setPen(color_error)
                    painter.drawText(int(x), int(y), ch)
                    painter.setPen(QPen(color_error, 2))
                    painter.drawLine(int(x), int(y + 3), int(x + char_width), int(y + 3))
                    x += char_width
                    continue
                elif status == "current":
                    painter.fillRect(
                        int(x - 2), int(y - metrics.ascent() - 2),
                        char_width + 4, line_height - 4, color_current_bg
                    )
                    painter.setPen(color_current)
                else:
                    painter.setPen(color_pending)
                painter.drawText(int(x), int(y), ch)
                x += char_width
            y += line_height

        painter.end()


class TypingArea(QWidget):
    """Wrapper around _TextDisplay that emits stats and finished signals."""
    finished = Signal(object)
    statsUpdated = Signal(float, float, float)

    def __init__(self, engine: TypingEngine, font_size: int = 26, show_timer: bool = False, theme: str = "dark", parent=None):
        super().__init__(parent)
        self.engine = engine
        self.font_size = font_size
        self._show_timer = show_timer
        self._theme = theme
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        self.text_display = _TextDisplay(self.engine, self.font_size, self._theme)
        layout.addWidget(self.text_display)

    def set_text(self, text: str) -> None:
        self.engine.reset(text)
        self._timer.start(TICK_MS)
        self.text_display.update()

    def _tick(self) -> None:
        wpm = self.engine.current_wpm()
        acc = self.engine.current_accuracy()
        elapsed = self.engine.elapsed_seconds
        self.statsUpdated.emit(wpm, acc, elapsed)
        if self.engine.is_finished and self.engine.target_text:
            self._timer.stop()
            self.finished.emit(self.engine.get_result())
        self.text_display.update()

    def set_font_size(self, size: int) -> None:
        self.font_size = size
        self.text_display.set_font_size(size)

    def set_theme(self, theme: str) -> None:
        self._theme = theme
        self.text_display.set_theme(theme)

    def stop(self) -> None:
        self._timer.stop()

    def pause(self) -> None:
        self._timer.stop()
        self.engine.pause()

    def resume(self) -> None:
        if self.engine.target_text and not self.engine.is_finished:
            self.engine.resume()
            self._timer.start(TICK_MS)

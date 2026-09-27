"""Finger placement guide widget with visual hands and real-time guidance.

Shows two stylized hands with 10 fingers, each labeled with its home-row key
and finger name. The active finger glows. A hint line below tells the user
exactly which finger to use and whether to reach up/down from the home row.
"""
from __future__ import annotations

import math

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont, QPainter, QColor, QPaintEvent, QPen, QBrush
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QFrame, QSizePolicy

from ...config import FINGER_COLORS, FINGER_NAMES
from ...core.keyboard_layout import KeyboardLayout
from ...core.fonts import ui_font, mono_font
from ..theme import palette

FINGER_LAYOUT = [
    ("LP", "Serçe", "a", "left"),
    ("LR", "Yüzük", "s", "left"),
    ("LM", "Orta", "d", "left"),
    ("LI", "İşaret", "f", "left"),
    ("LT", "Başparmak", "␣", "left"),
    ("RT", "Başparmak", "␣", "right"),
    ("RI", "İşaret", "j", "right"),
    ("RM", "Orta", "k", "right"),
    ("RR", "Yüzük", "l", "right"),
    ("RP", "Serçe", "ş", "right"),
]

HOME_ROW = set("asdfghjklşi,")
UPPER_ROW = set("qwertyuıopğü")
LOWER_ROW = set("zxcvbnmöç.")

PULSE_MS = 50
PULSE_STEP = 0.15
CIRCLE_R = 26
CIRCLE_GAP = 8
THUMB_OFFSET = 18


def _row_label(char: str) -> str:
    if char in HOME_ROW:
        return ""
    if char in UPPER_ROW:
        return "yukarı uzan"
    if char in LOWER_ROW:
        return "aşağı uzan"
    return ""


class _HandsCanvas(QFrame):
    """Paints two stylized hands with 10 finger circles and active/error glow."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("card")
        self.setMinimumHeight(150)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.active_finger: str = ""
        self.error_finger: str = ""
        self._theme = "dark"
        self._pulse_phase = 0.0
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(PULSE_MS)

    def set_theme(self, theme: str) -> None:
        self._theme = theme
        self.update()

    def _tick(self) -> None:
        if self.active_finger or self.error_finger:
            self._pulse_phase = (self._pulse_phase + PULSE_STEP) % (2 * math.pi)
            self.update()
        else:
            self._timer.stop()

    def set_active(self, finger: str) -> None:
        self.active_finger = finger
        self.error_finger = ""
        if finger:
            self._timer.start(PULSE_MS)
        self.update()

    def set_error(self, finger: str) -> None:
        self.error_finger = finger
        if finger:
            self._timer.start(PULSE_MS)
        self.update()

    def clear(self) -> None:
        self.active_finger = ""
        self.error_finger = ""
        self.update()

    def paintEvent(self, event: QPaintEvent) -> None:
        super().paintEvent(event)
        p = palette(self._theme)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        w = self.width()
        h = self.height()

        title_font = QFont(ui_font(), 10, QFont.Bold)
        painter.setFont(title_font)
        painter.setPen(QColor(p["finger_title"]))
        painter.drawText(16, 18, "PARMAK YERLEŞİMİ")

        hand_font = QFont(ui_font(), 9, QFont.Bold)
        key_font = QFont(mono_font(), 14, QFont.Bold)
        name_font = QFont(ui_font(), 7)

        finger_count = len(FINGER_LAYOUT)
        total_width = finger_count * (CIRCLE_R * 2) + (finger_count - 1) * CIRCLE_GAP
        start_x = (w - total_width) // 2
        center_y = h // 2 + 6

        for i, (code, short_name, home_key, hand) in enumerate(FINGER_LAYOUT):
            cx = start_x + i * (CIRCLE_R * 2 + CIRCLE_GAP) + CIRCLE_R
            cy = center_y

            if hand == "left" and code == "LT":
                cy += THUMB_OFFSET
            if hand == "right" and code == "RT":
                cy += THUMB_OFFSET

            color = QColor(FINGER_COLORS.get(code, "#888888"))
            is_active = code == self.active_finger
            is_error = code == self.error_finger

            if is_error:
                r = CIRCLE_R + 6
                painter.setBrush(QBrush(QColor(231, 76, 60, 60)))
                painter.setPen(Qt.NoPen)
                painter.drawEllipse(int(cx - r), int(cy - r), int(r * 2), int(r * 2))
            elif is_active:
                pulse = 0.5 + 0.5 * (0.5 + 0.5 * math.sin(self._pulse_phase))
                glow = QColor(color)
                glow.setAlpha(int(40 + 60 * pulse))
                r = CIRCLE_R + 5
                painter.setBrush(QBrush(glow))
                painter.setPen(Qt.NoPen)
                painter.drawEllipse(int(cx - r), int(cy - r), int(r * 2), int(r * 2))

            if is_error:
                painter.setBrush(QBrush(QColor(p["error"])))
                painter.setPen(QPen(QColor(p["error_dark"]), 3))
            elif is_active:
                painter.setBrush(QBrush(color))
                painter.setPen(QPen(color.darker(150), 3))
            else:
                painter.setBrush(QBrush(QColor(color.red(), color.green(), color.blue(), 50)))
                painter.setPen(QPen(color, 2))

            painter.drawEllipse(int(cx - CIRCLE_R), int(cy - CIRCLE_R), int(CIRCLE_R * 2), int(CIRCLE_R * 2))

            painter.setFont(key_font)
            painter.setPen(QColor(p["text"]) if (is_active or is_error) else QColor(p["finger_idle_text"]))
            text = home_key
            tw = painter.fontMetrics().horizontalAdvance(text)
            painter.drawText(int(cx - tw / 2), int(cy + 5), text)

            painter.setFont(name_font)
            painter.setPen(QColor(p["finger_label"]))
            tw = painter.fontMetrics().horizontalAdvance(short_name)
            painter.drawText(int(cx - tw / 2), int(cy + CIRCLE_R + 14), short_name)

        painter.setFont(QFont(ui_font(), 8))
        painter.setPen(QColor(p["finger_hand_label"]))
        painter.drawText(start_x - 50, center_y + 5, "SOL EL")
        painter.drawText(int(start_x + total_width + 10), center_y + 5, "SAĞ EL")

        painter.end()


class FingerGuide(QWidget):
    """Wrapper around _HandsCanvas with a hint label below."""

    def __init__(self, layout: KeyboardLayout = None, parent=None):
        super().__init__(parent)
        self.layout_def = layout or KeyboardLayout()
        self._theme = "dark"
        self._build_ui()

    def _build_ui(self) -> None:
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(6)

        self.canvas = _HandsCanvas()
        outer.addWidget(self.canvas)

        self.hint_label = QLabel("Bir ders seçerek başla — parmak yerleşimini burada göstereceğiz.")
        self.hint_label.setAlignment(Qt.AlignCenter)
        self.hint_label.setObjectName("pageSubtitle")
        self.hint_label.setStyleSheet("font-size: 13px; padding: 4px;")
        outer.addWidget(self.hint_label)

    def set_theme(self, theme: str) -> None:
        self._theme = theme
        self.canvas.set_theme(theme)

    def update_for_next_key(self, char: str) -> None:
        if not char:
            self.clear()
            return
        finger = self.layout_def.finger_for_char(char)
        self.canvas.set_active(finger)
        finger_name = FINGER_NAMES.get(finger, finger)
        reach = _row_label(char.lower())
        display = char if char != " " else "boşluk"
        if reach:
            self.hint_label.setText(
                f"👉 Sıradaki: '{display}'  →  {finger_name} parmağı  ({reach})"
            )
        else:
            self.hint_label.setText(
                f"👉 Sıradaki: '{display}'  →  {finger_name} parmağı  (ana satır)"
            )
        self.hint_label.setStyleSheet("font-size: 13px; padding: 4px; color: #f39c12; font-weight: 600;")

    def show_error(self, expected_char: str) -> None:
        finger = self.layout_def.finger_for_char(expected_char)
        self.canvas.set_error(finger)
        finger_name = FINGER_NAMES.get(finger, finger)
        display = expected_char if expected_char != " " else "boşluk"
        self.hint_label.setText(
            f"❌ Hata! '{display}' tuşunu {finger_name} parmağınla basmalısın"
        )
        self.hint_label.setStyleSheet("font-size: 13px; padding: 4px; color: #e74c3c; font-weight: 600;")

    def clear(self) -> None:
        self.canvas.clear()
        self.hint_label.setText("Bir ders seçerek başla — parmak yerleşimini burada göstereceğiz.")
        self.hint_label.setStyleSheet("font-size: 13px; padding: 4px;")
        self.hint_label.setObjectName("pageSubtitle")

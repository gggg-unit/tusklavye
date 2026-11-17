"""Virtual on-screen keyboard widget with finger color coding and live highlighting."""
from __future__ import annotations

from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QSizePolicy

from ...config import FINGER_COLORS, FINGER_NAMES
from ...core.keyboard_layout import KeyboardLayout
from ...core.fonts import ui_font
from ..theme import palette

LEGEND_ORDER = ["LP", "LR", "LM", "LI", "RI", "RM", "RR", "RP"]
LEGEND_SHORT = {
    "LP": "S.Serçe", "LR": "S.Yüzük", "LM": "S.Orta", "LI": "S.İşaret",
    "RI": "Sa.İşaret", "RM": "Sa.Orta", "RR": "Sa.Yüzük", "RP": "Sa.Serçe",
}

CORRECT_STYLE = (
    "QPushButton { background-color: #2ecc71; border: 2px solid #27ae60; "
    "border-radius: 6px; color: white; }"
)
ERROR_STYLE = (
    "QPushButton { background-color: #e74c3c; border: 2px solid #c0392b; "
    "border-radius: 6px; color: white; }"
)
NEXT_STYLE = (
    "QPushButton { background-color: #f39c12; border: 2px solid #e67e22; "
    "border-radius: 6px; color: white; }"
)

KEY_HEIGHT = 44
FLASH_MS = 150
LEGEND_FONT_PX = 9


def _hex_to_rgba(hex_color: str, alpha: int) -> str:
    h = hex_color.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f"rgba({r}, {g}, {b}, {alpha})"


class VirtualKeyboard(QWidget):
    """On-screen keyboard with finger-color coding and live key highlighting."""
    keyPressed = Signal(str)

    def __init__(self, layout: KeyboardLayout = None, parent=None):
        super().__init__(parent)
        self.layout_def = layout or KeyboardLayout()
        self._theme = "dark"
        self._modifier = ""
        self._key_buttons: dict = {}
        self._base_styles: dict = {}
        self._prev_active: set = set()
        self._next_key_char: str = ""
        self._error_key_char: str = ""
        self._flash_key_char: str = ""
        self._flash_timer = QTimer(self)
        self._flash_timer.setSingleShot(True)
        self._flash_timer.timeout.connect(self._clear_flash)
        self._build_ui()

    def set_theme(self, theme: str) -> None:
        self._theme = theme
        self._rebuild_base_styles()
        self._refresh_styles()

    def _rebuild_base_styles(self) -> None:
        for row in self.layout_def.rows:
            for key in row:
                self._base_styles[key.char] = self._key_style(key.char, key.finger)
        self._base_styles[" "] = self._key_style(" ", "RT")

    def _build_ui(self) -> None:
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(4)

        for row in self.layout_def.rows:
            row_widget = self._build_row(row)
            outer.addWidget(row_widget)

        space_row = QHBoxLayout()
        space_row.setSpacing(4)
        space_row.addStretch()
        for modifier in ("Shift", "AltGr"):
            button = QPushButton(modifier)
            button.setCheckable(True)
            button.clicked.connect(lambda checked, name=modifier: self._set_modifier(name, checked))
            setattr(self, "_" + modifier.lower() + "_button", button)
            space_row.addWidget(button)
        space_btn = QPushButton("Boşluk")
        space_btn.setFixedHeight(KEY_HEIGHT)
        space_btn.setMinimumWidth(280)
        space_btn.setFont(QFont(ui_font(), 10))
        space_btn.setStyleSheet(self._key_style(" ", "RT"))
        space_btn.clicked.connect(lambda: self.keyPressed.emit(" "))
        self._key_buttons[" "] = space_btn
        self._base_styles[" "] = self._key_style(" ", "RT")
        space_row.addWidget(space_btn)
        space_row.addStretch()
        outer.addLayout(space_row)

        p = palette(self._theme)
        legend_row = QHBoxLayout()
        legend_row.setContentsMargins(0, 2, 0, 0)
        legend_row.setSpacing(8)
        legend_title = QLabel("Parmak renkleri:")
        legend_title.setStyleSheet(f"font-size: {LEGEND_FONT_PX}px; color: {p['text_muted']};")
        legend_row.addWidget(legend_title)
        for code in LEGEND_ORDER:
            color = FINGER_COLORS.get(code, "#888")
            dot = QLabel(f"● {LEGEND_SHORT[code]}")
            dot.setStyleSheet(f"font-size: {LEGEND_FONT_PX}px; color: {color}; font-weight: 600;")
            legend_row.addWidget(dot)
        legend_row.addStretch()
        outer.addLayout(legend_row)
        self.setMinimumHeight(5 * KEY_HEIGHT + 48)

    def _build_row(self, row) -> QWidget:
        container = QHBoxLayout()
        container.setContentsMargins(0, 0, 0, 0)
        container.setSpacing(4)
        container.addStretch(1)
        for key in row:
            btn = QPushButton(key.display)
            btn.setFixedHeight(KEY_HEIGHT)
            btn.setMinimumWidth(int(24 * key.width))
            btn.setMaximumWidth(int(KEY_HEIGHT * key.width))
            btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            btn.setFont(QFont(ui_font(), 11, QFont.Bold))
            btn.setStyleSheet(self._key_style(key.char, key.finger))
            btn.clicked.connect(lambda checked, c=key.char: self._emit_key(c))
            self._key_buttons[key.char] = btn
            self._base_styles[key.char] = self._key_style(key.char, key.finger)
            container.addWidget(btn, 1)
        container.addStretch(1)
        wrapper = QWidget()
        wrapper.setLayout(container)
        wrapper.setMinimumHeight(KEY_HEIGHT)
        wrapper.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        return wrapper

    def _set_modifier(self, name, checked):
        self._modifier = name if checked else ""
        self._shift_button.setChecked(self._modifier == "Shift")
        self._altgr_button.setChecked(self._modifier == "AltGr")
        for row in self.layout_def.rows:
            for key in row:
                output = self.layout_def.output_for_key(key.char, self._modifier)
                self._key_buttons[key.char].setText(output or "—")

    def _emit_key(self, base):
        output = self.layout_def.output_for_key(base, self._modifier)
        if output:
            self.keyPressed.emit(output)

    def _key_style(self, char: str, finger: str) -> str:
        color = FINGER_COLORS.get(finger, "#888888")
        bg = _hex_to_rgba(color, 34)
        border = _hex_to_rgba(color, 102)
        hover = _hex_to_rgba(color, 68)
        p = palette(self._theme)
        return (
            f"QPushButton {{ background-color: {bg}; border: 1px solid {border}; "
            f"border-radius: 6px; color: {p['key_text']}; }}"
            f"QPushButton:hover {{ background-color: {hover}; }}"
        )

    def highlight_next(self, char: str) -> None:
        self._next_key_char, modifier = self.layout_def.stroke_for_char(char)
        self._shift_button.setStyleSheet(NEXT_STYLE if modifier == "Shift" else "")
        self._altgr_button.setStyleSheet(NEXT_STYLE if modifier == "AltGr" else "")
        self._error_key_char = ""
        self._refresh_styles()

    def flash_error(self, char: str) -> None:
        self._error_key_char = self.layout_def.stroke_for_char(char)[0]
        self._refresh_styles()

    def flash_correct(self, char: str) -> None:
        self._flash_key_char = self.layout_def.stroke_for_char(char)[0]
        self._refresh_styles()
        self._flash_timer.start(FLASH_MS)

    def _clear_flash(self) -> None:
        self._flash_key_char = ""
        self._refresh_styles()

    def clear_highlights(self) -> None:
        self._shift_button.setStyleSheet("")
        self._altgr_button.setStyleSheet("")
        self._next_key_char = ""
        self._error_key_char = ""
        self._flash_key_char = ""
        self._refresh_styles()

    def _refresh_styles(self) -> None:
        active = {self._flash_key_char, self._error_key_char, self._next_key_char} - {""}
        chars_to_update = active | self._prev_active
        self._prev_active = active
        for char in chars_to_update:
            btn = self._key_buttons.get(char)
            if not btn:
                continue
            if char == self._flash_key_char:
                btn.setStyleSheet(CORRECT_STYLE)
            elif char == self._error_key_char:
                btn.setStyleSheet(ERROR_STYLE)
            elif char == self._next_key_char:
                btn.setStyleSheet(NEXT_STYLE)
            else:
                btn.setStyleSheet(self._base_styles.get(char, ""))

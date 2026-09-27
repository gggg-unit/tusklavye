"""Dark/light theme manager with cross-platform styling and centralized color palette."""
from __future__ import annotations

from typing import Dict

from ..core.fonts import qss_font_chain

_FONT_CHAIN = qss_font_chain()


COLORS: Dict[str, str] = {
    "primary": "#0078d4",
    "primary_hover": "#1a86e0",
    "primary_dark": "#00549b",
    "accent": "#4cc2ff",
    "success": "#27ae60",
    "success_bg": "#27ae6022",
    "success_border": "#27ae6066",
    "error": "#e74c3c",
    "error_dark": "#c0392b",
    "error_bg": "#e74c3c44",
    "warning": "#f39c12",
    "warning_bg": "#f39c1244",
    "info": "#0067c0",
}


def palette(theme: str = "dark") -> Dict[str, str]:
    """Return a semantic color palette for the given theme.

    Keys include: bg, bg_card, bg_input, border, text, text_secondary, text_muted,
    text_on_primary, grid, empty, success/error/warning/info + their _bg/_border variants.
    """
    if theme == "dark":
        return {
            "bg": "#202020",
            "bg_card": "#2b2b2b",
            "bg_input": "#333333",
            "border": "#3a3a3a",
            "border_input": "#555555",
            "text": "#ffffff",
            "text_secondary": "#a0a0a0",
            "text_muted": "#999999",
            "text_dim": "#666666",
            "text_on_primary": "#ffffff",
            "grid": "#444444",
            "empty": "#888888",
            "key_text": "#e0e0e0",
            "key_dim": "#aaaaaa",
            "key_idle": "#888888",
            "key_border": "#bbbbbb",
            "heatmap_empty_bg": "#3a3a3a",
            "heatmap_empty_text": "#888888",
            "heatmap_border": "#555555",
            "finger_idle_text": "#cccccc",
            "finger_dim_text": "#888888",
            "finger_label": "#aaaaaa",
            "finger_hand_label": "#666666",
            "finger_title": "#888888",
            **COLORS,
        }
    return {
        "bg": "#f3f3f3",
        "bg_card": "#ffffff",
        "bg_input": "#ffffff",
        "border": "#e0e0e0",
        "border_input": "#c0c0c0",
        "text": "#1f1f1f",
        "text_secondary": "#616161",
        "text_muted": "#999999",
        "text_dim": "#666666",
        "text_on_primary": "#ffffff",
        "grid": "#cccccc",
        "empty": "#888888",
        "key_text": "#1f1f1f",
        "key_dim": "#555555",
        "key_idle": "#888888",
        "key_border": "#bbbbbb",
        "heatmap_empty_bg": "#dddddd",
        "heatmap_empty_text": "#777777",
        "heatmap_border": "#bbbbbb",
        "finger_idle_text": "#333333",
        "finger_dim_text": "#555555",
        "finger_label": "#666666",
        "finger_hand_label": "#666666",
        "finger_title": "#555555",
        **COLORS,
    }


LIGHT_QSS = """
* { font-family: %FONT_CHAIN%; }
QMainWindow, QWidget#central { background-color: #f3f3f3; }
QFrame#sidebar { background-color: #ffffff; border-right: 1px solid #e0e0e0; }
QPushButton#navBtn {
    text-align: left; padding: 10px 16px; border: none; border-radius: 6px;
    font-size: 14px; color: #1f1f1f; background: transparent;
}
QPushButton#navBtn:hover { background-color: #e9e9e9; }
QPushButton#navBtn:checked { background-color: #e6f0fd; color: #005fb8; font-weight: 600; }
QLabel#pageTitle { font-size: 22px; font-weight: 700; color: #1f1f1f; }
QLabel#pageSubtitle { font-size: 13px; color: #616161; }
QLabel#statValue { font-size: 28px; font-weight: 700; color: #005fb8; }
QLabel#statLabel { font-size: 12px; color: #616161; }
QFrame#card { background-color: #ffffff; border: 1px solid #e0e0e0; border-radius: 8px; }
QPushButton#primary {
    background-color: #0067c0; color: white; border: none; border-radius: 6px;
    padding: 8px 20px; font-size: 14px; font-weight: 600;
}
QPushButton#primary:hover { background-color: #0078d4; }
QPushButton#secondary {
    background-color: transparent; color: #0067c0; border: 1px solid #0067c0;
    border-radius: 6px; padding: 8px 20px; font-size: 14px;
}
QPushButton#secondary:hover { background-color: #f0f7ff; }
QProgressBar { border: 1px solid #e0e0e0; border-radius: 4px; text-align: center; background: #f0f0f0; }
QProgressBar::chunk { background-color: #0067c0; border-radius: 3px; }
QListWidget { border: 1px solid #e0e0e0; border-radius: 6px; background: #ffffff; }
QListWidget::item { padding: 8px 12px; border-bottom: 1px solid #f0f0f0; color: #1f1f1f; }
QListWidget::item:selected { background-color: #e6f0fd; color: #005fb8; }
QComboBox, QSpinBox, QLineEdit {
    border: 1px solid #c0c0c0; border-radius: 4px; padding: 6px 10px;
    background: #ffffff; color: #1f1f1f; font-size: 14px;
}
QComboBox:focus, QSpinBox:focus, QLineEdit:focus { border-color: #0067c0; }
QComboBox QAbstractItemView { background: #ffffff; color: #1f1f1f; selection-background-color: #e6f0fd; selection-color: #005fb8; outline: none; }
QCheckBox { font-size: 14px; color: #1f1f1f; spacing: 8px; }
QCheckBox::indicator { width: 18px; height: 18px; border: 2px solid #c0c0c0; border-radius: 4px; background: #ffffff; }
QCheckBox::indicator:unchecked { background: #ffffff; border: 2px solid #c0c0c0; }
QCheckBox::indicator:checked { background: #0067c0; border: 2px solid #0067c0; image: none; }
QCheckBox::indicator:hover { border-color: #0067c0; }
QGroupBox {
    border: 1px solid #e0e0e0; border-radius: 8px; margin-top: 12px;
    font-size: 14px; font-weight: 600; color: #1f1f1f; padding-top: 8px;
}
QGroupBox::title { subcontrol-origin: margin; left: 12px; padding: 0 6px; }
QScrollBar:vertical { border: none; background: #f3f3f3; width: 10px; border-radius: 5px; }
QScrollBar::handle:vertical { background: #c0c0c0; min-height: 30px; border-radius: 5px; }
QScrollBar::handle:vertical:hover { background: #a0a0a0; }
QLabel { color: #1f1f1f; }
QLabel#lessonTitle { color: #1f1f1f; font-weight: 600; }
QLabel#lessonDesc { color: #616161; }
QScrollArea { background: transparent; border: none; }
QScrollArea > QWidget > QWidget { background: transparent; }
QTextEdit { border: 1px solid #c0c0c0; border-radius: 4px; background: #ffffff; color: #1f1f1f; font-size: 14px; }
QMenu { background-color: #ffffff; border: 1px solid #c0c0c0; border-radius: 6px; padding: 4px; }
QMenu::item { padding: 6px 24px; border-radius: 4px; }
QMenu::item:selected { background-color: #e6f0fd; color: #005fb8; }
QMenu::separator { height: 1px; background: #e0e0e0; margin: 4px 8px; }
QToolTip { background-color: #1f1f1f; color: #ffffff; border: none; border-radius: 4px; padding: 4px 8px; font-size: 12px; }
QMessageBox { background-color: #f3f3f3; }
QMessageBox QLabel { color: #1f1f1f; font-size: 14px; }
QSlider::groove:horizontal { height: 6px; background: #e0e0e0; border-radius: 3px; }
QSlider::handle:horizontal { width: 16px; height: 16px; margin: -5px 0; background: #0067c0; border-radius: 8px; }
QSlider::handle:horizontal:hover { background: #0078d4; }
QSlider::sub-page:horizontal { background: #0067c0; border-radius: 3px; }
QDialog { background-color: #f3f3f3; }
"""

DARK_QSS = """
* { font-family: %FONT_CHAIN%; }
QMainWindow, QWidget#central { background-color: #202020; }
QFrame#sidebar { background-color: #2b2b2b; border-right: 1px solid #3a3a3a; }
QPushButton#navBtn {
    text-align: left; padding: 10px 16px; border: none; border-radius: 6px;
    font-size: 14px; color: #ffffff; background: transparent;
}
QPushButton#navBtn:hover { background-color: #3a3a3a; }
QPushButton#navBtn:checked { background-color: #00345e; color: #4cc2ff; font-weight: 600; }
QLabel#pageTitle { font-size: 22px; font-weight: 700; color: #ffffff; }
QLabel#pageSubtitle { font-size: 13px; color: #a0a0a0; }
QLabel#statValue { font-size: 28px; font-weight: 700; color: #4cc2ff; }
QLabel#statLabel { font-size: 12px; color: #a0a0a0; }
QFrame#card { background-color: #2b2b2b; border: 1px solid #3a3a3a; border-radius: 8px; }
QPushButton#primary {
    background-color: #0078d4; color: white; border: none; border-radius: 6px;
    padding: 8px 20px; font-size: 14px; font-weight: 600;
}
QPushButton#primary:hover { background-color: #1a86e0; }
QPushButton#secondary {
    background-color: transparent; color: #4cc2ff; border: 1px solid #4cc2ff;
    border-radius: 6px; padding: 8px 20px; font-size: 14px;
}
QPushButton#secondary:hover { background-color: #1c3a52; }
QProgressBar { border: 1px solid #3a3a3a; border-radius: 4px; text-align: center; background: #333; color: #fff; }
QProgressBar::chunk { background-color: #0078d4; border-radius: 3px; }
QListWidget { border: 1px solid #3a3a3a; border-radius: 6px; background: #2b2b2b; color: #fff; }
QListWidget::item { padding: 8px 12px; border-bottom: 1px solid #333; }
QListWidget::item:selected { background-color: #00345e; color: #4cc2ff; }
QComboBox, QSpinBox, QLineEdit {
    border: 1px solid #555; border-radius: 4px; padding: 6px 10px;
    background: #333; color: #fff; font-size: 14px;
}
QComboBox:focus, QSpinBox:focus, QLineEdit:focus { border-color: #0078d4; }
QComboBox QAbstractItemView { background: #2b2b2b; color: #fff; selection-background-color: #00345e; }
QCheckBox { font-size: 14px; color: #fff; spacing: 8px; }
QCheckBox::indicator { width: 18px; height: 18px; border: 2px solid #555; border-radius: 4px; background: #333; }
QCheckBox::indicator:unchecked { background: #333; border: 2px solid #555; }
QCheckBox::indicator:checked { background: #0078d4; border: 2px solid #0078d4; image: none; }
QCheckBox::indicator:hover { border-color: #4cc2ff; }
QGroupBox {
    border: 1px solid #3a3a3a; border-radius: 8px; margin-top: 12px;
    font-size: 14px; font-weight: 600; color: #fff; padding-top: 8px;
}
QGroupBox::title { subcontrol-origin: margin; left: 12px; padding: 0 6px; }
QScrollBar:vertical { border: none; background: #202020; width: 10px; border-radius: 5px; }
QScrollBar::handle:vertical { background: #555; min-height: 30px; border-radius: 5px; }
QScrollBar::handle:vertical:hover { background: #777; }
QLabel { color: #e0e0e0; }
QLabel#lessonTitle { color: #ffffff; font-weight: 600; }
QLabel#lessonDesc { color: #a0a0a0; }
QScrollArea { background: transparent; border: none; }
QScrollArea > QWidget > QWidget { background: transparent; }
QTextEdit { border: 1px solid #555; border-radius: 4px; background: #333; color: #fff; font-size: 14px; }
QMenu { background-color: #2b2b2b; border: 1px solid #555; border-radius: 6px; padding: 4px; }
QMenu::item { padding: 6px 24px; border-radius: 4px; color: #e0e0e0; }
QMenu::item:selected { background-color: #00345e; color: #4cc2ff; }
QMenu::separator { height: 1px; background: #3a3a3a; margin: 4px 8px; }
QToolTip { background-color: #1f1f1f; color: #ffffff; border: none; border-radius: 4px; padding: 4px 8px; font-size: 12px; }
QMessageBox { background-color: #202020; }
QMessageBox QLabel { color: #e0e0e0; font-size: 14px; }
QSlider::groove:horizontal { height: 6px; background: #3a3a3a; border-radius: 3px; }
QSlider::handle:horizontal { width: 16px; height: 16px; margin: -5px 0; background: #0078d4; border-radius: 8px; }
QSlider::handle:horizontal:hover { background: #1a86e0; }
QSlider::sub-page:horizontal { background: #0078d4; border-radius: 3px; }
QDialog { background-color: #202020; }
"""


def get_qss(theme: str) -> str:
    """Return the QSS stylesheet for the given theme."""
    base = DARK_QSS if theme == "dark" else LIGHT_QSS
    return base.replace("%FONT_CHAIN%", _FONT_CHAIN)

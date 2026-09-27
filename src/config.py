"""Application configuration constants."""
import os
import sys
from pathlib import Path

APP_NAME = "TuşKlavye - 10 Parmak Yazma Eğitmeni"
APP_VERSION = "1.0.0"

BASE_DIR = Path(__file__).resolve().parent.parent
ASSETS_DIR = BASE_DIR / "assets"
SOUNDS_DIR = ASSETS_DIR / "sounds"


def _get_data_dir() -> Path:
    """Return platform-appropriate data directory.

    - Windows: %APPDATA%/TuşKlavye
    - macOS: ~/Library/Application Support/TuşKlavye
    - Linux: ~/.local/share/TuşKlavye
    Falls back to project-local data/ if detection fails.
    """
    try:
        if sys.platform == "win32":
            base = os.environ.get("APPDATA")
            if base:
                return Path(base) / "TuşKlavye"
        elif sys.platform == "darwin":
            return Path.home() / "Library" / "Application Support" / "TuşKlavye"
        else:
            xdg = os.environ.get("XDG_DATA_HOME")
            if xdg:
                return Path(xdg) / "tusklavye"
            return Path.home() / ".local" / "share" / "tusklavye"
    except Exception:
        pass
    return BASE_DIR / "data"


DATA_DIR = _get_data_dir()
DB_PATH = DATA_DIR / "typing_tutor.db"

DEFAULT_SETTINGS = {
    "theme": "dark",
    "sound_enabled": "True",
    "key_sound_enabled": "True",
    "error_sound_enabled": "True",
    "font_size": "26",
    "daily_goal_wpm": "40",
    "daily_goal_minutes": "15",
    "keyboard_layout": "tr_q",
    "show_timer": "False",
    "show_wpm": "False",
    "volume": "50",
}

FINGER_NAMES = {
    "LP": "Sol Serçe",
    "LR": "Sol Yüzük",
    "LM": "Sol Orta",
    "LI": "Sol İşaret",
    "RI": "Sağ İşaret",
    "RM": "Sağ Orta",
    "RR": "Sağ Yüzük",
    "RP": "Sağ Serçe",
    "LT": "Sol Başparmak",
    "RT": "Sağ Başparmak",
}

FINGER_COLORS = {
    "LP": "#E74C3C",
    "LR": "#E67E22",
    "LM": "#F1C40F",
    "LI": "#2ECC71",
    "RI": "#1ABC9C",
    "RM": "#3498DB",
    "RR": "#9B59B6",
    "RP": "#E91E63",
    "LT": "#95A5A6",
    "RT": "#7F8C8D",
}

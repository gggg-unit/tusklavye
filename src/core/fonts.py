"""Cross-platform font resolution — picks the best available font per OS."""
from __future__ import annotations

import sys


def _platform() -> str:
    """Return a normalized platform name: 'windows', 'macos', or 'linux'."""
    if sys.platform == "win32":
        return "windows"
    elif sys.platform == "darwin":
        return "macos"
    else:
        return "linux"


_PLATFORM = _platform()

UI_FONTS = {
    "windows": "Segoe UI Variable",
    "macos": "SF Pro Text",
    "linux": "Ubuntu",
}

UI_FALLBACK = {
    "windows": "Segoe UI",
    "macos": "Helvetica Neue",
    "linux": "DejaVu Sans",
}

MONO_FONTS = {
    "windows": "Consolas",
    "macos": "Menlo",
    "linux": "DejaVu Sans Mono",
}

MONO_FALLBACK = {
    "windows": "Courier New",
    "macos": "Monaco",
    "linux": "Liberation Mono",
}


def ui_font() -> str:
    """Return the preferred UI font for the current platform."""
    return UI_FONTS.get(_PLATFORM, "sans-serif")


def ui_fallback() -> str:
    """Return the fallback UI font for the current platform."""
    return UI_FALLBACK.get(_PLATFORM, "sans-serif")


def mono_font() -> str:
    """Return the preferred monospace font for the current platform."""
    return MONO_FONTS.get(_PLATFORM, "monospace")


def mono_fallback() -> str:
    """Return the fallback monospace font for the current platform."""
    return MONO_FALLBACK.get(_PLATFORM, "monospace")


def qss_font_chain() -> str:
    """Return a CSS font-family chain covering all supported platforms."""
    return (
        f"'Segoe UI Variable', 'Segoe UI', 'SF Pro Text', 'Helvetica Neue', "
        f"'Ubuntu', 'DejaVu Sans', sans-serif"
    )

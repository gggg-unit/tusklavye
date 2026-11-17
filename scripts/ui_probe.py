"""Render isolated Qt pages; run in a fresh process for each DPI scale."""
import json
import os
import sys
import tempfile
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def main():
    from PySide6.QtWidgets import QApplication

    from src.core.sound import SoundManager
    from src.database.db import Database
    from src.ui.main_window import MainWindow
    app = QApplication([])
    from PySide6.QtGui import QFont, QFontDatabase
    for font in ("segoeui.ttf", "consola.ttf"):
        path = Path("C:/Windows/Fonts") / font
        if path.exists():
            QFontDatabase.addApplicationFont(str(path))
    app.setFont(QFont("Segoe UI", 10))
    SoundManager._init_sounds = lambda self: None
    output = ROOT / ".dev-data" / "ui" / os.environ.get("QT_SCALE_FACTOR", "1")
    output.mkdir(parents=True, exist_ok=True)
    results = []
    with tempfile.TemporaryDirectory() as folder:
        Database.reset(Path(folder) / "probe.db")
        window = MainWindow()
        window.show()
        window.pages["training"].lesson_list.setCurrentRow(0)
        for theme in ("dark", "light"):
            window.ctx.theme = theme
            window.apply_settings()
            for width, height in ((1100, 720), (1280, 900)):
                window.resize(width, height)
                for key in window.pages:
                    window._switch_page(key)
                    app.processEvents()
                    picture = window.grab()
                    picture.save(str(output / f"{theme}-{width}-{key}.png"))
                    results.append({"theme": theme, "page": key, "requested": [width, height],
                                    "actual": [window.width(), window.height()],
                                    "dpr": picture.devicePixelRatio()})
        window.close()
    (output / "results.json").write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(json.dumps(results))


if __name__ == "__main__":
    main()

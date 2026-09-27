"""Application entry point with CLI argument support."""
from __future__ import annotations

import argparse
import logging
import sys


def main() -> None:
    parser = argparse.ArgumentParser(description="TuşKlavye — 10 parmak yazma eğitmeni")
    parser.add_argument("--version", action="version", version="TuşKlavye 1.0.0")
    parser.add_argument("--text", type=str, default=None, help="Start typing this text directly")
    parser.add_argument("--lesson", type=str, default=None, help="Start a specific lesson by ID (e.g. L01)")
    args = parser.parse_args()

    try:
        from PySide6.QtWidgets import QApplication
        from PySide6.QtGui import QFont
    except ImportError:
        print("PySide6 is required. Install with: pip install PySide6", file=sys.stderr)
        sys.exit(1)

    from src.core.fonts import ui_font
    from src.core.lessons import get_lesson
    from src.ui.main_window import MainWindow

    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    app = QApplication(sys.argv)
    app.setApplicationName("TuşKlavye")
    font = QFont(ui_font(), 10)
    font.setPixelSize(13)
    app.setFont(font)
    window = MainWindow()

    if args.lesson:
        lesson = get_lesson(args.lesson)
        if lesson:
            window._switch_page("training")
            page = window.pages.get("training")
            if page:
                from PySide6.QtCore import Qt
                for i in range(page.lesson_list.count()):
                    item = page.lesson_list.item(i)
                    data = item.data(Qt.UserRole)
                    if data and data["id"] == args.lesson:
                        page.lesson_list.setCurrentRow(i)
                        break
        else:
            print(f"Lesson {args.lesson} not found.", file=sys.stderr)

    if args.text:
        window._switch_page("custom")
        page = window.pages.get("custom")
        if page:
            page.text_edit.setPlainText(args.text)
            page._start_practice()

    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()

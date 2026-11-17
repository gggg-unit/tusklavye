"""Real Qt construction, navigation and input; isolated from user data."""
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel


def test_all_pages_open(app_window, qtbot):
    window = app_window
    assert set(window.pages) == {
        "home", "training", "tests", "custom", "stats", "achievements", "settings",
    }
    for key, page in window.pages.items():
        qtbot.mouseClick(window.nav_buttons[key], Qt.LeftButton)
        assert window.stack.currentWidget() is page
        assert window.nav_buttons[key].isChecked()
    assert window.ctx.stats_repo.get_session_count() == 0


def test_lesson_accepts_keyboard_input(app_window, qtbot):
    window = app_window
    window._switch_page("training")
    page = window.pages["training"]
    page.lesson_list.setCurrentRow(0)
    qtbot.keyClicks(window, "asdf")
    assert page.engine.position == 4
    assert page.engine.correct_count() == 4
    assert not page.engine.is_finished


def test_custom_text_starts_from_editor(app_window, qtbot):
    window = app_window
    window._switch_page("custom")
    page = window.pages["custom"]
    page.text_edit.setPlainText("merhaba dünya")
    qtbot.mouseClick(page.start_btn, Qt.LeftButton)
    qtbot.keyClicks(window, "mer")
    assert page.engine.position == 3
    assert page.engine.correct_count() == 3


def test_main_window_uses_test_database(app_window, tmp_db_path):
    assert app_window.ctx.stats_repo.db.path == tmp_db_path
    assert app_window.findChildren(QLabel)

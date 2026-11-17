"""Regressions reported during real beta usage."""
import pytest
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication


def test_training_refresh_preserves_session(app_window):
    window = app_window
    window._switch_page("training")
    page = window.pages["training"]
    page.lesson_list.setCurrentRow(2)
    page.on_key_press(page.engine.target_text[0])
    page.on_key_press(page.engine.target_text[1])
    lesson = page.current_lesson["id"]
    position = page.engine.position
    elapsed = page.engine.elapsed_seconds
    window._switch_page("stats")
    paused_elapsed = page.engine.elapsed_seconds
    window._switch_page("training")
    assert page.current_lesson["id"] == lesson
    assert page.lesson_list.currentItem().data(Qt.UserRole)["id"] == lesson
    assert page.engine.position == position == 2
    assert page.engine.elapsed_seconds >= paused_elapsed >= elapsed
    assert not page.engine.is_finished
    assert len(window.ctx.stats_repo.get_all_sessions()) == 0


def test_training_manual_pause_survives_refresh(app_window):
    window = app_window
    window._switch_page("training")
    page = window.pages["training"]
    page.lesson_list.setCurrentRow(0)
    page.on_key_press(page.engine.target_text[0])
    window._toggle_pause()
    elapsed = page.engine.elapsed_seconds
    window._switch_page("custom")
    window._switch_page("training")
    assert page.engine.is_paused
    assert page.typing_area.manual_pause
    assert page.engine.position == 1
    assert page.engine.elapsed_seconds == elapsed


def test_application_and_window_icons_match(app_window):
    application = QApplication.instance().windowIcon()
    window = app_window.windowIcon()
    assert not application.pixmap(32, 32).isNull()
    assert application.cacheKey() == window.cacheKey()


@pytest.mark.parametrize("theme", ["light", "dark"])
def test_settings_numbers_have_room(app_window, qtbot, theme):
    window = app_window
    window.ctx.theme = theme
    window.apply_settings()
    window.resize(1100, 720)
    window._switch_page("settings")
    page = window.pages["settings"]
    for spin in (page.font_spin, page.goal_wpm_spin, page.goal_min_spin):
        for value in (spin.minimum(), spin.maximum()):
            spin.setValue(value)
            window.grab()
            edit = spin.lineEdit()
            margins = edit.textMargins()
            available = edit.contentsRect().width() - margins.left() - margins.right()
            assert available >= edit.fontMetrics().horizontalAdvance(str(value)) + 8
        spin.setFocus()
        qtbot.keyClick(spin, Qt.Key_Down)
        assert spin.value() == spin.maximum() - 1
    page._save()
    assert page.ctx.settings_repo.get_int("daily_goal_wpm") == page.goal_wpm_spin.value()

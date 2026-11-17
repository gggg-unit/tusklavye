"""Rendering, pause and focus regressions."""
from PySide6.QtCore import QRect, Qt

from src.ui.widgets.typing_area import TypingArea


def test_equal_length_text_rebuilds_wrap(qtbot, engine):
    area = TypingArea(engine)
    qtbot.addWidget(area)
    area.resize(260, 180)
    area.show()
    area.set_text("aaaa bbbbb ccccc ddddd")
    area.grab()
    previous = area.text_display._vl_cache_key
    area.set_text("aaaaaaaaa b ccccc dddd")
    area.grab()
    assert area.text_display._vl_cache_key != previous
    display = area.text_display
    rect = display.rect().adjusted(20, 20, -20, -20)
    assert display._vl_cache == display._calc_visual_lines(rect, display._vl_cache_key[2])


def test_newline_has_visible_position(qtbot, engine):
    area = TypingArea(engine)
    qtbot.addWidget(area)
    area.set_text("a  \nb")
    lines = area.text_display._calc_visual_lines(QRect(0, 0, 200, 100), 10)
    assert lines == [(0, 4), (4, 5)]
    assert area.text_display._find_current_vline(lines, 3) == 0


def test_pause_navigation_and_focus(app_window, qtbot):
    window = app_window
    window._switch_page("custom")
    page = window.pages["custom"]
    page.text_edit.setPlainText("asdf asdf")
    assert page._start_practice()
    qtbot.keyClick(page.typing_area.text_display, Qt.Key_A)
    assert page.engine.position == 1
    qtbot.mouseClick(page.typing_area.pause_btn, Qt.LeftButton)
    assert page.engine.is_paused
    page.on_key_press("s", "s")
    assert page.engine.position == 1
    window._switch_page("home")
    window._switch_page("custom")
    assert page.engine.is_paused
    qtbot.mouseClick(page.typing_area.pause_btn, Qt.LeftButton)
    assert not page.engine.is_paused
    assert page.typing_area.text_display.hasFocus()
    qtbot.keyClick(page.typing_area.text_display, Qt.Key_Tab)
    assert not page.typing_area.text_display.hasFocus()
    qtbot.keyClick(window.focusWidget(), Qt.Key_F6)
    assert page.typing_area.text_display.hasFocus()
    qtbot.keyClick(page.typing_area.text_display, Qt.Key_Escape)
    assert page.engine.is_paused


def test_automatic_pause_resumes(app_window):
    window = app_window
    window._switch_page("custom")
    page = window.pages["custom"]
    page.text_edit.setPlainText("asdf asdf")
    page._start_practice()
    window._switch_page("home")
    assert page.engine.is_paused
    window._switch_page("custom")
    assert not page.engine.is_paused


def test_timed_pause_controls_both_clocks(app_window, qtbot, monkeypatch):
    app_window._switch_page("tests")
    page = app_window.pages["tests"]
    page._start_test_with_text("asdf asdf")
    qtbot.mouseClick(page.typing_area.pause_btn, Qt.LeftButton)
    assert page.engine.is_paused
    assert page.session.clock.is_paused
    assert not page._countdown_timer.isActive()
    qtbot.mouseClick(page.typing_area.pause_btn, Qt.LeftButton)
    assert not page.session.clock.is_paused
    assert page._countdown_timer.isActive()
    monkeypatch.setattr(page, "_save_and_show", lambda result: None)
    page._force_finish()
    assert not page.typing_area.pause_btn.isEnabled()


def test_editor_input_does_not_reach_practice(app_window, qtbot):
    app_window._switch_page("custom")
    page = app_window.pages["custom"]
    page.text_edit.setPlainText("asdf asdf")
    page._start_practice()
    page.text_edit.setFocus()
    qtbot.keyClicks(page.text_edit, "abc")
    assert page.engine.position == 0

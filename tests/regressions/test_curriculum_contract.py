"""Shared layout, curriculum progression, mastery and character contracts."""
from copy import deepcopy

import pytest
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QMessageBox

from src.core.keyboard_layout import HOME_FINGER_KEYS, KeyboardLayout
from src.core.lessons import LESSONS, meets_lesson_target
from src.core.typing_engine import TypingEngine, TypingResult, normalize_text
from src.database.backup import BackupService
from src.database.models import SessionRecord
from src.ui.widgets.finger_guide import FINGER_LAYOUT
from src.ui.widgets.results_dialog import ResultsDialog


@pytest.mark.parametrize("char,base,modifier,finger", [
    ("ş", "ş", "", "RP"), ("Ş", "ş", "Shift", "RP"),
    ("i", "i", "", "RP"), ("İ", "i", "Shift", "RP"),
    ("ı", "ı", "", "RM"), ("I", "ı", "Shift", "RM"),
    ("0", "0", "", "RP"), ("!", "1", "Shift", "LP"),
    ("?", "*", "Shift", "RP"), (";", ",", "Shift", "RP"),
    (":", ".", "Shift", "RP"), ("@", "q", "AltGr", "LP"),
    ("€", "e", "AltGr", "LM"), ("[", "8", "AltGr", "RM"),
    (">", "<", "Shift", "LP"),
])
def test_shared_character_strokes(char, base, modifier, finger):
    layout = KeyboardLayout()
    assert layout.stroke_for_char(char) == (base, modifier)
    assert layout.find_key(char).char == base
    assert layout.finger_for_char(char) == finger
    assert layout.output_for_key(base, modifier) == char


def test_all_home_fingers_match_drawn_hands_and_layout():
    layout = KeyboardLayout()
    drawn = {code: key for code, _, key, _ in FINGER_LAYOUT}
    for finger, key in HOME_FINGER_KEYS.items():
        assert drawn[finger] == key
        assert layout.finger_for_char(key) == finger


def test_every_lesson_uses_only_introduced_keys():
    layout = KeyboardLayout()
    introduced = {" "}
    for lesson in LESSONS:
        introduced.update(lesson["keys"])
        for char in lesson["text"]:
            if char != "\n":
                base, _ = layout.stroke_for_char(char)
                assert base and base in introduced, (lesson["id"], char)
        assert lesson["content_version"] == 2
        assert lesson["target_accuracy"] == 95


def test_guide_uses_turkish_case_rows_and_does_not_guess_unknown(app_window):
    guide = app_window.pages["training"].finger_guide
    guide.update_for_next_key("I")
    assert guide.canvas.active_finger == "RM"
    assert "yukarı" in guide.hint_label.text()
    guide.update_for_next_key("Ş")
    assert guide.canvas.active_finger == "RP"
    assert "Shift" in guide.hint_label.text()
    guide.update_for_next_key("😀")
    assert guide.canvas.active_finger == ""
    assert "tanımlı değil" in guide.hint_label.text()
    guide.show_error("😀")
    assert guide.canvas.error_finger == ""


def test_virtual_keyboard_emits_selected_modifier_and_highlights_base(app_window, qtbot):
    keyboard = app_window.pages["training"].keyboard
    captured = []
    keyboard.keyPressed.connect(captured.append)
    keyboard.highlight_next("?")
    assert keyboard._next_key_char == "*"
    qtbot.mouseClick(keyboard._shift_button, Qt.LeftButton)
    qtbot.mouseClick(keyboard._key_buttons["*"], Qt.LeftButton)
    assert captured[-1] == "?"
    qtbot.mouseClick(keyboard._altgr_button, Qt.LeftButton)
    qtbot.mouseClick(keyboard._key_buttons["q"], Qt.LeftButton)
    assert captured[-1] == "@"
    assert not keyboard._shift_button.isChecked()


@pytest.mark.parametrize("char", ["\n", "\r", "\t", "\x00", "\x1b"])
def test_control_input_does_not_advance_or_start_engine(char):
    engine = TypingEngine()
    engine.reset("ab")
    engine.process_key(char)
    assert engine.position == 0
    assert engine.get_result().started_at == ""


def test_normalization_preserves_turkish_case_and_expands_tabs():
    assert normalize_text("I İ ı i\r\na\tb") == "I İ ı i\na    b"
    engine = TypingEngine()
    engine.reset("Iİıi")
    for char in "Iİıi":
        engine.process_key(char)
    assert engine.get_result().accuracy == 100
    engine.reset("İ")
    engine.process_key("I")
    assert engine.get_result().accuracy == 0


def test_unicode_printable_without_mapping_remains_typeable():
    engine = TypingEngine()
    engine.reset("😀")
    engine.process_key("😀")
    assert engine.is_finished
    assert engine.get_result().accuracy == 100
    assert engine.layout.finger_for_char("😀") == ""


def test_invalid_target_is_rejected_without_erasing_current_engine():
    engine = TypingEngine()
    engine.reset("abc")
    engine.process_key("a")
    with pytest.raises(ValueError):
        engine.reset("a\x00b")
    assert engine.target_text == "abc"
    assert engine.position == 1


def test_custom_invalid_target_warns_and_keeps_existing_work(app_window, monkeypatch):
    page = app_window.pages["custom"]
    page.engine.reset("abc")
    page.engine.process_key("a")
    warnings = []
    monkeypatch.setattr(QMessageBox, "warning", lambda *args: warnings.append(args))
    page.text_edit.setPlainText("a\x01b")
    page._start_practice()
    assert warnings
    assert page.engine.target_text == "abc"


def lesson_record(lesson, wpm, accuracy):
    count = len(lesson["text"].replace("\n", ""))
    incorrect = round(count * (100 - accuracy) / 100)
    return SessionRecord(
        mode="lesson", mode_detail=lesson["id"], text_content=lesson["text"],
        total_chars=count, correct_chars=count - incorrect, incorrect_chars=incorrect,
        wpm=wpm, raw_wpm=wpm, accuracy=accuracy, max_wpm=wpm, duration_seconds=60,
    )


def test_mastery_requires_both_thresholds_in_same_full_attempt(stats_repo, lesson_repo):
    lesson = LESSONS[0]
    stats_repo.save_session(lesson_record(lesson, 100, 80))
    stats_repo.save_session(lesson_record(lesson, 10, 100))
    lesson_repo.mark_completed(lesson["id"], 100, 100)
    assert lesson_repo.is_completed(lesson["id"])
    assert lesson["id"] not in lesson_repo.get_mastered()
    stats_repo.save_session(lesson_record(lesson, lesson["target_wpm"], 95))
    assert lesson["id"] in lesson_repo.get_mastered()


@pytest.mark.parametrize("change", [
    {"total_chars": 1}, {"text_content": "different curriculum"}, {"duration_seconds": 0},
])
def test_partial_old_or_unknown_duration_is_not_mastery(stats_repo, lesson_repo, change):
    record = lesson_record(LESSONS[0], 100, 100)
    for field, value in change.items():
        setattr(record, field, value)
    stats_repo.save_session(record)
    assert lesson_repo.get_mastered() == set()


def test_legacy_completion_not_promoted_to_mastery(lesson_repo):
    lesson_repo.mark_completed("L01", 100, 100)
    assert lesson_repo.is_completed("L01")
    assert not lesson_repo.get_mastered()


def test_mastery_survives_full_backup_round_trip(stats_repo, lesson_repo):
    stats_repo.save_session(lesson_record(LESSONS[0], 20, 100))
    lesson_repo.mark_completed("L01", 20, 100)
    service = BackupService(stats_repo.db)
    backup = service.snapshot()
    service.reset()
    service.restore(backup)
    assert lesson_repo.get_mastered() == {"L01"}
    assert service.restore(backup) == 0


@pytest.mark.parametrize("wpm,accuracy,achieved", [(15, 95, True), (14.9, 100, False), (99, 94.9, False)])
def test_ui_mastery_message_and_badge(app_window, monkeypatch, wpm, accuracy, achieved):
    page = app_window.pages["training"]
    page.current_lesson = deepcopy(LESSONS[0])
    record = lesson_record(LESSONS[0], wpm, accuracy)
    result = TypingResult(**{key: value for key, value in vars(record).items()
                             if key in TypingResult.__dataclass_fields__})
    page.engine.reset(LESSONS[0]["text"])
    captured = []
    monkeypatch.setattr(ResultsDialog, "exec", lambda self: captured.append(self.windowTitle()))
    page._on_finished(result)
    assert meets_lesson_target(LESSONS[0], result) is achieved
    assert ("Hedefe Ulaşıldı" in captured[0]) is achieved
    assert page.lesson_list.item(0).text().startswith("★" if achieved else "✓")


def test_result_heading_uses_actual_outcome(qtbot):
    dialog = ResultsDialog(TypingResult(), "Metin Bitti — Hedef İçin Tekrar Çalış")
    qtbot.addWidget(dialog)
    assert dialog.findChild(QLabel, "pageTitle").text() == dialog.windowTitle()


def test_lesson_awards_use_mastery_not_legacy_completion(app_window):
    ctx = app_window.ctx
    for lesson in LESSONS[:5]:
        ctx.lesson_repo.mark_completed(lesson["id"], 100, 100)
    page = app_window.pages["custom"]
    page.engine.reset("ab")
    page.engine.process_key("a")
    assert page.save_for_close()
    assert ctx.stats_repo.db.query_one("SELECT 1 FROM achievements WHERE code='lessons_5'") is None


def test_all_bundled_test_texts_and_presets_have_supported_characters():
    from src.core.test_texts import get_texts
    from src.ui.pages.custom_text import PRESETS

    layout = KeyboardLayout()
    texts = [text for level in ("easy", "medium", "hard") for text in get_texts(level)]
    presets = [text for _, group in PRESETS for text in group]
    assert len(texts) == len(presets) == 72
    for text in texts + presets:
        assert normalize_text(text) == text
        assert all(char == "\n" or layout.finger_for_char(char) for char in text)


def test_altgr_does_not_trigger_ctrl_navigation(app_window):
    from PySide6.QtCore import QEvent
    from PySide6.QtGui import QKeyEvent

    app_window._switch_page("custom")
    page = app_window.pages["custom"]
    page.text_edit.setPlainText("#ab")
    page._start_practice()
    event = QKeyEvent(QEvent.KeyPress, Qt.Key_3,
                      Qt.ControlModifier | Qt.AltModifier, "#")
    app_window.keyPressEvent(event)
    assert app_window._current_page_key == "custom"
    assert page.engine.position == 1
    assert page.engine.get_result().correct_chars == 1


def test_tab_expansion_and_newlines_count_only_typeable_characters():
    engine = TypingEngine()
    engine.reset("a\r\n\tb")
    for char in "a    b":
        engine.process_key(char)
    assert engine.is_finished
    assert engine.get_result().total_chars == 6
    assert engine.get_result().accuracy == 100

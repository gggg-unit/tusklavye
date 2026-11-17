"""Filtered metric, recommendation, CSV and real Qt regression contracts."""
import csv
from copy import deepcopy
from datetime import date

import pytest
from PySide6.QtWidgets import QFileDialog, QMessageBox

from src.core.analytics import AnalyticsService, aggregate_keys, recommend_practice
from src.core.keyboard_layout import KeyboardLayout
from src.database.models import SessionRecord


def save(repo, **changes):
    values = dict(
        mode="custom", mode_detail="sample", text_content="a" * 10,
        total_chars=10, correct_chars=8, incorrect_chars=2,
        wpm=16, raw_wpm=20, accuracy=80, max_wpm=20, duration_seconds=6,
        started_at="2026-11-17T10:00:00", finished_at="2026-11-17T10:00:06",
        key_counts={"a": {"correct": 8, "incorrect": 2}},
    )
    return repo.save_session(SessionRecord(**(values | changes)))


def test_character_weighted_accuracy_and_time_weighted_speed(stats_repo):
    save(stats_repo, total_chars=100, correct_chars=90, incorrect_chars=10,
         duration_seconds=60, accuracy=90, wpm=18)
    save(stats_repo, total_chars=10, correct_chars=0, incorrect_chars=10,
         duration_seconds=60, accuracy=0, wpm=0)
    report = AnalyticsService(stats_repo.db).report()
    assert report["accuracy"] == pytest.approx(90 / 110 * 100)
    assert report["average_wpm"] == 9
    assert report["minutes"] == 2
    assert stats_repo.get_avg_accuracy() == report["accuracy"]


def test_unknown_duration_and_empty_sessions_are_explicit(stats_repo):
    save(stats_repo, duration_seconds=0, wpm=400)
    save(stats_repo, total_chars=0, correct_chars=0, incorrect_chars=0,
         duration_seconds=100, wpm=999, key_counts={})
    report = AnalyticsService(stats_repo.db).report()
    assert report["count"] == 2
    assert report["unknown_duration_count"] == report["empty_count"] == 1
    assert report["best_wpm"] == 400
    assert report["average_wpm"] is None
    assert report["speed_history"] == []
    assert report["minutes"] == stats_repo.get_total_practice_minutes() == 0
    assert stats_repo.get_best_wpm() == 400


def test_empty_report_has_no_nan_and_has_safe_fallback(db):
    report = AnalyticsService(db).report()
    assert report["accuracy"] is None
    assert report["average_wpm"] is None
    assert report["count"] == 0
    assert report["recommendation"]["keys"] == []
    assert "ana sıra" in report["recommendation"]["explanation"]


@pytest.mark.parametrize("day,included", [
    ("2026-11-10", False), ("2026-11-11", True), ("2026-11-17", True), ("2026-11-18", False),
])
def test_seven_day_filter_is_inclusive_and_excludes_future(stats_repo, day, included):
    save(stats_repo, finished_at=day + "T23:59:59")
    report = AnalyticsService(stats_repo.db).report(days=7, today=date(2026, 11, 17))
    assert report["count"] == int(included)
    assert bool(report["key_stats"]) is included


def test_filter_uses_recorded_calendar_day_without_utc_shift(stats_repo):
    save(stats_repo, finished_at="2026-11-17T00:05:00+03:00")
    report = AnalyticsService(stats_repo.db).report(days=1, today=date(2026, 11, 17))
    assert report["count"] == 1


def test_mode_filter_applies_to_sessions_keys_and_recommendation(stats_repo):
    save(stats_repo, mode="lesson", key_counts={"ş": {"correct": 3, "incorrect": 4}})
    save(stats_repo, mode="test", key_counts={"a": {"correct": 3, "incorrect": 8}})
    report = AnalyticsService(stats_repo.db).report(mode="lesson")
    assert report["count"] == 1
    assert set(report["key_stats"]) == {"ş"}
    assert report["recommendation"]["keys"] == ["ş"]


@pytest.mark.parametrize("days,mode", [(0, None), (-1, None), (True, None), (None, "invalid")])
def test_invalid_filters_are_rejected(db, days, mode):
    with pytest.raises(ValueError):
        AnalyticsService(db).report(days=days, mode=mode)


def test_heatmap_and_fingers_use_physical_keys_without_mutating_input():
    stats = {"Ş": {"correct": 1, "incorrect": 2}, "ş": {"correct": 3, "incorrect": 1},
             "?": {"correct": 1, "incorrect": 2}, "I": {"correct": 2, "incorrect": 1},
             "İ": {"correct": 1, "incorrect": 0}, "😀": {"correct": 2, "incorrect": 3}}
    original = deepcopy(stats)
    physical, fingers, unknown = aggregate_keys(stats, KeyboardLayout())
    assert physical["ş"] == {"correct": 4, "incorrect": 3}
    assert physical["*"] == {"correct": 1, "incorrect": 2}
    assert physical["ı"]["correct"] == 2
    assert physical["i"]["correct"] == 1
    assert fingers["RP"] == 11
    assert fingers["RM"] == 3
    assert unknown == 5
    assert stats == original


def test_recommendations_use_minimum_evidence_and_deterministic_order():
    stats = {"a": {"correct": 0, "incorrect": 2}, "s": {"correct": 4, "incorrect": 1},
             "Ş": {"correct": 3, "incorrect": 3}, "k": {"correct": 6, "incorrect": 6},
             "😀": {"correct": 0, "incorrect": 50}, " ": {"correct": 0, "incorrect": 50}}
    first = recommend_practice(stats, KeyboardLayout())
    second = recommend_practice(dict(reversed(list(stats.items()))), KeyboardLayout())
    assert first == second
    assert first["keys"] == ["k", "Ş"]
    assert "6/12" in first["explanation"]
    assert len(first["text"]) < 200


def test_csv_exports_full_filter_and_neutralizes_formulas(stats_repo, tmp_path):
    save(stats_repo, mode="lesson", mode_detail="=1+1")
    save(stats_repo, mode="test")
    service = AnalyticsService(stats_repo.db)
    path = tmp_path / "stats.csv"
    service.export_csv(path, service.report(mode="lesson"))
    with path.open(encoding="utf-8-sig", newline="") as stream:
        rows = list(csv.DictReader(stream))
    assert len(rows) == 1
    assert rows[0]["mode"] == "lesson"
    assert rows[0]["mode_detail"] == "'=1+1"
    assert rows[0]["duration_seconds"] == "6.0"


def test_csv_is_not_limited_by_ui_history(stats_repo, tmp_path):
    for _ in range(35):
        save(stats_repo)
    service = AnalyticsService(stats_repo.db)
    report = service.report()
    assert len(report["sessions"]) == 35
    assert len(report["speed_history"]) == 30
    path = tmp_path / "all.csv"
    service.export_csv(path, report)
    with path.open(encoding="utf-8-sig") as stream:
        assert len(list(csv.DictReader(stream))) == 35


def test_csv_replace_failure_preserves_old_file(db, tmp_path, monkeypatch):
    path = tmp_path / "stats.csv"
    path.write_text("old", encoding="utf-8")

    def fail(*args):
        raise OSError("disk error")

    monkeypatch.setattr("src.core.analytics.os.replace", fail)
    with pytest.raises(OSError):
        AnalyticsService.export_csv(path, AnalyticsService(db).report())
    assert path.read_text(encoding="utf-8") == "old"
    assert list(tmp_path.glob("*.tmp")) == []


def test_ui_refresh_updates_existing_cards_and_clears_after_reset(app_window):
    page = app_window.pages["stats"]
    label = page.summary_values["best_wpm"]
    save(app_window.ctx.stats_repo, wpm=42)
    page.refresh()
    assert page.summary_values["best_wpm"] is label
    assert label.text() == "42.0"
    assert page.history_list.count() == 1
    app_window.ctx.stats_repo.db.execute("DELETE FROM sessions")
    page.refresh()
    assert label.text() == "0.0"
    assert page.history_list.count() == 0
    assert page.heatmap.error_data == {}


def test_ui_mode_filter_updates_all_outputs_and_csv(app_window, tmp_path, monkeypatch):
    repo = app_window.ctx.stats_repo
    save(repo, mode="lesson", wpm=42, key_counts={"Ş": {"correct": 3, "incorrect": 4}})
    save(repo, mode="custom", wpm=10, key_counts={"a": {"correct": 3, "incorrect": 5}})
    page = app_window.pages["stats"]
    page.mode_combo.setCurrentIndex(page.mode_combo.findData("lesson"))
    assert page.summary_values["count"].text() == "1"
    assert page.summary_values["best_wpm"].text() == "42.0"
    assert set(page.heatmap.error_data) == {"ş"}
    assert page.current_report["recommendation"]["keys"] == ["Ş"]
    path = tmp_path / "filtered.csv"
    monkeypatch.setattr(QFileDialog, "getSaveFileName", lambda *args: (str(path), "CSV"))
    page._export_csv()
    with path.open(encoding="utf-8-sig") as stream:
        assert [row["mode"] for row in csv.DictReader(stream)] == ["lesson"]


def test_practice_button_starts_suggested_text(app_window):
    save(app_window.ctx.stats_repo, key_counts={"ş": {"correct": 5, "incorrect": 5}})
    page = app_window.pages["stats"]
    page.refresh()
    text = page.current_report["recommendation"]["text"]
    page._start_recommended_practice()
    custom = app_window.pages["custom"]
    assert app_window._current_page_key == "custom"
    assert custom.engine.target_text == text
    assert custom._active


def test_suggestion_preserves_pending_session_and_editor_on_save_failure(app_window, monkeypatch):
    custom = app_window.pages["custom"]
    custom.text_edit.setPlainText("original text")
    custom._start_practice()
    custom.on_key_press("o")
    app_window._switch_page("stats")
    db = app_window.ctx.stats_repo.db
    db.execute("""CREATE TEMP TRIGGER fail_suggestion BEFORE INSERT ON sessions
        BEGIN SELECT RAISE(ABORT, 'save failure'); END""")
    monkeypatch.setattr(QMessageBox, "warning", lambda *args: None)
    app_window.pages["stats"]._start_recommended_practice()
    assert custom.text_edit.toPlainText() == "original text"
    assert custom.engine.target_text == "original text"
    assert app_window._current_page_key == "stats"
    assert custom.session.pending is not None
    db.execute("DROP TRIGGER fail_suggestion")
    assert custom._retry_pending_save()


def test_report_does_not_write_data(stats_repo):
    save(stats_repo)
    before = stats_repo.db.conn.total_changes
    AnalyticsService(stats_repo.db).report()
    assert stats_repo.db.conn.total_changes == before


def test_inactive_and_future_streak_dates_do_not_break_current_streak(db, stats_repo):
    today = date.today()
    db.execute("INSERT INTO streak VALUES (?, 1)", (today.isoformat(),))
    db.execute("INSERT INTO streak VALUES ('2999-01-01', 1)")
    db.execute("INSERT INTO streak VALUES ('2000-01-01', 0)")
    assert stats_repo.get_streak() == 1


def test_heatmap_distinguishes_missing_data_from_error_free_samples(app_window):
    heatmap = app_window.pages["stats"].heatmap
    heatmap.set_data({"a": {"correct": 10, "incorrect": 0}})
    assert "veri yok" in heatmap.tooltip_for_key("ş")
    assert "0/10" in heatmap.tooltip_for_key("a")

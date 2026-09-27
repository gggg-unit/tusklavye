"""Home / dashboard page."""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QFrame, QWidget, QProgressBar,
)

from ...core.achievements import get_definitions, check_and_unlock
from .base import BasePage
from ..theme import palette


class HomePage(BasePage):
    """Dashboard with stats summary, daily goals, and achievement progress."""

    def __init__(self, ctx, parent=None):
        super().__init__(ctx, parent)
        self.add_header("Hoş Geldin", "10 parmak yazma eğitimine genel bakış")
        self._build_stats()
        self._build_achievements()
        self._build_quick_actions()

    def _build_stats(self) -> None:
        row = QHBoxLayout()
        row.setSpacing(12)
        best = self.ctx.stats_repo.get_best_wpm()
        avg_acc = self.ctx.stats_repo.get_avg_accuracy()
        total_min = self.ctx.stats_repo.get_total_practice_minutes()
        streak = self.ctx.stats_repo.get_streak()

        row.addWidget(self.make_stat_card(f"{best:.1f}", "En İyi (Kelime/Dakika)"))
        row.addWidget(self.make_stat_card(f"{avg_acc:.0f}%", "Ort. Doğruluk"))
        row.addWidget(self.make_stat_card(f"{total_min:.0f}dk", "Toplam Pratik"))
        row.addWidget(self.make_stat_card(f"{streak}", "Gün Serisi"))
        self._root.addLayout(row)
        self._build_daily_goals()

    def _build_daily_goals(self) -> None:
        p = palette(self.ctx.theme)
        goal_wpm = self.ctx.settings_repo.get_int("daily_goal_wpm", 40)
        goal_min = self.ctx.settings_repo.get_int("daily_goal_minutes", 15)
        today_wpm = self.ctx.stats_repo.get_today_best_wpm()
        today_min = self.ctx.stats_repo.get_today_practice_minutes()

        card = self.make_card()
        cl = QVBoxLayout(card)
        cl.setContentsMargins(20, 16, 20, 16)
        cl.setSpacing(10)

        top_row = QHBoxLayout()
        top_row.setSpacing(16)

        title = QLabel("🎯 Günlük Hedefler")
        title.setObjectName("pageTitle")
        top_row.addWidget(title)
        top_row.addStretch()

        goals_widget = QWidget()
        goals_col = QVBoxLayout(goals_widget)
        goals_col.setContentsMargins(0, 0, 0, 0)
        goals_col.setSpacing(6)
        for label, current, target, unit in [
            ("WPM", today_wpm, goal_wpm, ""),
            ("Pratik", today_min, goal_min, "dk"),
        ]:
            row = QHBoxLayout()
            row.setSpacing(8)
            name_lbl = QLabel(label)
            name_lbl.setStyleSheet("font-size: 13px; font-weight: 600;")
            row.addWidget(name_lbl)
            bar = QProgressBar()
            pct = min(100, int(current / target * 100)) if target > 0 else 0
            bar.setValue(pct)
            bar.setFixedHeight(10)
            bar.setTextVisible(False)
            row.addWidget(bar, 1)
            status = "✅" if current >= target else "⏳"
            val_lbl = QLabel(f"{status} {current:.0f}{unit} / {target}{unit}")
            val_lbl.setStyleSheet(f"font-size: 12px; color: {p['text_muted']};")
            val_lbl.setFixedWidth(120)
            row.addWidget(val_lbl)
            goals_col.addLayout(row)

        goals_widget.setFixedWidth(360)
        top_row.addWidget(goals_widget)
        cl.addLayout(top_row)

        self._root.addWidget(card)

    def _build_achievements(self) -> None:
        p = palette(self.ctx.theme)
        best_wpm = self.ctx.stats_repo.get_best_wpm()
        best_acc = self.ctx.stats_repo.get_best_accuracy()
        session_count = self.ctx.stats_repo.get_session_count()
        streak = self.ctx.stats_repo.get_streak()
        completed_lessons = len(self.ctx.lesson_repo.get_completed())
        check_and_unlock(self.ctx.stats_repo, self.ctx.achievement_repo,
                         lesson_count=completed_lessons, streak=streak)
        unlocked = {a["code"] for a in self.ctx.achievement_repo.get_all()}

        from ...core.achievements import THRESHOLDS
        targets = {
            "first_session": (session_count, THRESHOLDS["first_session"]),
            "speed_20": (best_wpm, THRESHOLDS["speed_20"]),
            "speed_40": (best_wpm, THRESHOLDS["speed_40"]),
            "speed_60": (best_wpm, THRESHOLDS["speed_60"]),
            "accuracy_95": (best_acc, THRESHOLDS["accuracy_95"]),
            "accuracy_100": (best_acc, THRESHOLDS["accuracy_100"]),
            "streak_3": (streak, THRESHOLDS["streak_3"]),
            "streak_7": (streak, THRESHOLDS["streak_7"]),
            "sessions_10": (session_count, THRESHOLDS["sessions_10"]),
            "sessions_50": (session_count, THRESHOLDS["sessions_50"]),
            "lessons_5": (completed_lessons, THRESHOLDS["lessons_5"]),
            "lessons_all": (completed_lessons, THRESHOLDS["lessons_all"]),
        }

        earned_list = []
        progress_list = []
        for code, title, desc, emoji in get_definitions():
            if code in unlocked:
                earned_list.append((emoji, title))
            else:
                current, target = targets.get(code, (0, 1))
                pct = min(100, int(current / target * 100)) if target > 0 else 0
                progress_list.append((emoji, title, desc, pct))

        card = self.make_card()
        cl = QVBoxLayout(card)
        cl.setContentsMargins(20, 16, 20, 16)
        cl.setSpacing(10)

        header_row = QHBoxLayout()
        header_row.setSpacing(12)
        title = QLabel("🏆 Başarıların")
        title.setObjectName("pageTitle")
        header_row.addWidget(title)

        if earned_list:
            earned_lbl = QLabel(f"✅ Kazanılan ({len(earned_list)})")
            earned_lbl.setStyleSheet(f"font-size: 13px; font-weight: 600; color: {p['success']};")
            header_row.addWidget(earned_lbl)
        header_row.addStretch()
        cl.addLayout(header_row)

        if earned_list:
            earned_row = QHBoxLayout()
            earned_row.setSpacing(8)
            for emoji, name in earned_list:
                chip = QLabel(f" {emoji} {name} ")
                chip.setStyleSheet(
                    f"background-color: {p['success_bg']}; border: 1px solid {p['success_border']}; "
                    "border-radius: 12px; padding: 4px 10px; font-size: 12px; font-weight: 600;"
                )
                earned_row.addWidget(chip)
            earned_row.addStretch()
            cl.addLayout(earned_row)

        if progress_list:
            prog_lbl = QLabel(f"🎯 Hedefler ({len(progress_list)})")
            prog_lbl.setStyleSheet(f"font-size: 13px; font-weight: 600; color: {p['warning']};")
            cl.addWidget(prog_lbl)
            for emoji, name, desc, pct in progress_list[:6]:
                row = QHBoxLayout()
                row.setSpacing(8)
                icon_lbl = QLabel(f"{emoji}")
                icon_lbl.setStyleSheet("font-size: 18px;")
                row.addWidget(icon_lbl)
                name_lbl = QLabel(name)
                name_lbl.setStyleSheet("font-size: 12px; font-weight: 600;")
                row.addWidget(name_lbl)
                bar = QProgressBar()
                bar.setValue(pct)
                bar.setFixedHeight(8)
                bar.setTextVisible(False)
                row.addWidget(bar, 1)
                pct_lbl = QLabel(f"{pct}%")
                pct_lbl.setStyleSheet(f"font-size: 11px; color: {p['text_muted']};")
                pct_lbl.setFixedWidth(36)
                row.addWidget(pct_lbl)
                cl.addLayout(row)
            if len(progress_list) > 6:
                more = QLabel(f"…ve {len(progress_list) - 6} hedef daha")
                more.setStyleSheet(f"font-size: 11px; color: {p['text_muted']}; padding: 2px 0;")
                cl.addWidget(more)

        self._root.addWidget(card)

    def _build_quick_actions(self) -> None:
        card = self.make_card()
        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(8)
        title = QLabel("Hızlı Başla")
        title.setObjectName("pageTitle")
        layout.addWidget(title)

        info = QLabel(
            "Sol menüden Eğitim bölümüne giderek adım adım dersleri takip edebilir,\n"
            "Testler bölümünde zamana karşı yarışabilir, İstatistikler'de gelişimini izleyebilirsin."
        )
        info.setObjectName("pageSubtitle")
        layout.addWidget(info)
        self._root.addWidget(card)

    def refresh(self) -> None:
        self._clear_layout(self._root)
        self.add_header("Hoş Geldin", "10 parmak yazma eğitimine genel bakış")
        self._build_stats()
        self._build_achievements()
        self._build_quick_actions()

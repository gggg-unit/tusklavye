"""Statistics page: WPM/accuracy charts, error heatmap, finger performance."""
from __future__ import annotations

import csv

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QFrame, QScrollArea, QWidget,
    QListWidget, QListWidgetItem, QPushButton, QFileDialog,
)

from ...config import FINGER_NAMES
from ..widgets.charts import LineChart, BarChart
from ..widgets.heatmap import HeatmapWidget
from .base import BasePage

FINGER_ORDER = ["LP", "LR", "LM", "LI", "LT", "RT", "RI", "RM", "RR", "RP"]
MODE_NAMES = {"lesson": "Ders", "test": "Test", "custom": "Özel"}
HISTORY_LIMIT = 20
CHART_LIMIT = 30


class StatisticsPage(BasePage):
    """Stats page with WPM/accuracy charts, error heatmap, and session history."""

    def __init__(self, ctx, parent=None):
        super().__init__(ctx, parent)
        self.add_header("İstatistikler", "Gelişimini grafikler ve ısı haritasıyla izle")
        self._build_ui()

    def _build_ui(self) -> None:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        inner = QWidget()
        self.inner_layout = QVBoxLayout(inner)
        self.inner_layout.setContentsMargins(0, 0, 0, 0)
        self.inner_layout.setSpacing(16)

        summary = QHBoxLayout()
        summary.setSpacing(12)
        best = self.ctx.stats_repo.get_best_wpm()
        avg_acc = self.ctx.stats_repo.get_avg_accuracy()
        total = self.ctx.stats_repo.get_session_count()
        minutes = self.ctx.stats_repo.get_total_practice_minutes()
        summary.addWidget(self.make_stat_card(f"{best:.1f}", "En İyi WPM"))
        summary.addWidget(self.make_stat_card(f"{avg_acc:.0f}%", "Ort. Doğruluk"))
        summary.addWidget(self.make_stat_card(f"{total}", "Toplam Seans"))
        summary.addWidget(self.make_stat_card(f"{minutes:.0f}dk", "Toplam Süre"))
        self.inner_layout.addLayout(summary)

        export_row = QHBoxLayout()
        export_row.addStretch()
        export_btn = QPushButton("📤 CSV Aktar")
        export_btn.setObjectName("secondary")
        export_btn.clicked.connect(self._export_csv)
        export_row.addWidget(export_btn)
        self.inner_layout.addLayout(export_row)

        self.wpm_chart = LineChart("WPM Gelişimi (son seanslar)")
        self.wpm_chart.set_theme(self.ctx.theme)
        self.inner_layout.addWidget(self.wpm_chart)

        self.acc_chart = LineChart("Doğruluk Gelişimi (son seanslar)")
        self.acc_chart.color = QColor("#27ae60")
        self.acc_chart.set_theme(self.ctx.theme)
        self.inner_layout.addWidget(self.acc_chart)

        self.heatmap = HeatmapWidget(self.ctx.layout)
        self.heatmap.set_theme(self.ctx.theme)
        heat_label = QLabel("Hata Isı Haritası (en çok hata yapılan tuşlar)")
        heat_label.setObjectName("pageSubtitle")
        self.inner_layout.addWidget(heat_label)
        self.inner_layout.addWidget(self.heatmap)

        self.finger_chart = BarChart("Parmak Bazında Toplam Tuş Basışı")
        self.finger_chart.set_theme(self.ctx.theme)
        self.inner_layout.addWidget(self.finger_chart)

        history_label = QLabel("Seans Geçmişi")
        history_label.setObjectName("pageTitle")
        self.inner_layout.addWidget(history_label)
        self.history_list = QListWidget()
        self.history_list.setMaximumHeight(200)
        self.inner_layout.addWidget(self.history_list)

        scroll.setWidget(inner)
        self._root.addWidget(scroll)
        self.refresh()

    def refresh(self) -> None:
        sessions = self.ctx.stats_repo.get_wpm_history(CHART_LIMIT)
        sessions.reverse()
        wpm_values = [s["wpm"] for s in sessions]
        acc_values = [s["accuracy"] for s in sessions]
        self.wpm_chart.set_data(wpm_values)
        self.acc_chart.set_data(acc_values)

        key_stats = self.ctx.stats_repo.get_key_error_stats()
        self.heatmap.set_data(key_stats)

        finger_map = {c: f for c, f in self.ctx.layout.char_to_finger.items()}
        finger_stats = self.ctx.stats_repo.get_finger_stats(finger_map)
        labels = []
        values = []
        for code in FINGER_ORDER:
            name = FINGER_NAMES.get(code, code)
            hand = "L" if code.startswith("L") else "R"
            short = f"{hand}-{name.split()[-1]}"
            labels.append(short)
            values.append(finger_stats.get(code, {}).get("total", 0))
        self.finger_chart.set_data(labels, values)
        recent = self.ctx.stats_repo.get_recent_sessions(HISTORY_LIMIT)
        self.history_list.clear()
        for s in recent:
            mode = MODE_NAMES.get(s["mode"], s["mode"])
            detail = f" ({s['mode_detail']})" if s["mode_detail"] else ""
            date_str = s["finished_at"][:16].replace("T", " ")
            item = QListWidgetItem(
                f"{date_str}  •  {mode}{detail}  •  {s['wpm']:.1f} WPM  •  {s['accuracy']:.0f}%"
            )
            self.history_list.addItem(item)

    def _export_csv(self) -> None:
        path, _ = QFileDialog.getSaveFileName(
            self, "CSV Aktar", "typing_stats.csv", "CSV (*.csv)"
        )
        if not path:
            return
        try:
            sessions = self.ctx.stats_repo.get_all_sessions(10000)
            with open(path, "w", encoding="utf-8", newline="") as f:
                writer = csv.writer(f)
                writer.writerow([
                    "finished_at", "mode", "mode_detail", "wpm", "raw_wpm",
                    "accuracy", "duration_seconds", "total_chars",
                    "correct_chars", "incorrect_chars", "max_wpm",
                ])
                for s in sessions:
                    writer.writerow([
                        s["finished_at"], s["mode"], s["mode_detail"] or "",
                        f"{s['wpm']:.1f}", f"{s['raw_wpm']:.1f}",
                        f"{s['accuracy']:.1f}", f"{s['duration_seconds']:.1f}",
                        s["total_chars"], s["correct_chars"], s["incorrect_chars"],
                        f"{s['max_wpm']:.1f}",
                    ])
        except Exception as e:
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "Hata", f"CSV aktarılamadı: {e}")

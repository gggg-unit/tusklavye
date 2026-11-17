"""Filtered statistics, physical-key distribution and personal practice."""
from __future__ import annotations

from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from ...config import FINGER_NAMES
from ...core.analytics import AnalyticsService
from ..widgets.charts import BarChart, LineChart
from ..widgets.heatmap import HeatmapWidget
from .base import BasePage

FINGER_ORDER = ["LP", "LR", "LM", "LI", "LT", "RT", "RI", "RM", "RR", "RP"]
MODE_NAMES = {"lesson": "Ders", "test": "Test", "custom": "Özel"}
HISTORY_LIMIT = 20


class StatisticsPage(BasePage):
    def __init__(self, ctx, parent=None):
        super().__init__(ctx, parent)
        self.analytics = AnalyticsService(ctx.stats_repo.db, ctx.layout)
        self.add_header("İstatistikler", "Seçili dönemdeki gelişim ve çalışma önerileri")
        self._build_ui()

    def _build_ui(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        inner = QWidget()
        self.inner_layout = QVBoxLayout(inner)
        filters = QHBoxLayout()
        filters.addWidget(QLabel("Dönem:"))
        self.period_combo = QComboBox()
        for title, days in (("Tüm zamanlar", None), ("Son 7 gün", 7), ("Son 30 gün", 30),
                            ("Son 90 gün", 90), ("Son 365 gün", 365)):
            self.period_combo.addItem(title, days)
        filters.addWidget(self.period_combo)
        filters.addWidget(QLabel("Çalışma:"))
        self.mode_combo = QComboBox()
        self.mode_combo.addItem("Tümü", None)
        for code, name in MODE_NAMES.items():
            self.mode_combo.addItem(name, code)
        filters.addWidget(self.mode_combo)
        export = QPushButton("Seçili verileri CSV aktar")
        export.clicked.connect(self._export_csv)
        filters.addWidget(export)
        self.inner_layout.addLayout(filters)

        summary = QHBoxLayout()
        self.summary_values = {}
        for key, title in (("best_wpm", "En iyi kayıtlı WPM"), ("average_wpm", "Ort. aktif WPM"),
                           ("accuracy", "Karakter doğruluğu"), ("count", "Seans"),
                           ("minutes", "Aktif süre")):
            card = self.make_stat_card("—", title)
            self.summary_values[key] = card.findChild(QLabel, "statValue")
            summary.addWidget(card)
        self.inner_layout.addLayout(summary)
        self.data_note = QLabel()
        self.data_note.setWordWrap(True)
        self.inner_layout.addWidget(self.data_note)

        self.wpm_chart = LineChart("Aktif süresi bilinen son 30 seans: kayıtlı WPM")
        self.acc_chart = LineChart("Son 30 dolu seans: karakter doğruluğu")
        self.acc_chart.color = QColor("#27ae60")
        for chart in (self.wpm_chart, self.acc_chart):
            chart.set_theme(self.ctx.theme)
            self.inner_layout.addWidget(chart)

        self.inner_layout.addWidget(QLabel("Beklenen tuşa göre kalan hatalar — büyük harf ve semboller temel tuşa katılır"))
        self.heatmap = HeatmapWidget(self.ctx.layout)
        self.heatmap.set_theme(self.ctx.theme)
        self.inner_layout.addWidget(self.heatmap)
        self.finger_chart = BarChart("Önerilen parmağa göre tuş dağılımı")
        self.finger_chart.set_theme(self.ctx.theme)
        self.inner_layout.addWidget(self.finger_chart)
        self.finger_note = QLabel()
        self.finger_note.setWordWrap(True)
        self.inner_layout.addWidget(self.finger_note)

        self.recommendation_label = QLabel()
        self.recommendation_label.setWordWrap(True)
        self.inner_layout.addWidget(self.recommendation_label)
        self.practice_btn = QPushButton("Önerilen alıştırmayı başlat")
        self.practice_btn.clicked.connect(self._start_recommended_practice)
        self.inner_layout.addWidget(self.practice_btn)
        self.inner_layout.addWidget(QLabel("Son 20 seans — CSV seçili dönemin tamamını içerir"))
        self.history_list = QListWidget()
        self.history_list.setMaximumHeight(200)
        self.inner_layout.addWidget(self.history_list)
        scroll.setWidget(inner)
        self._root.addWidget(scroll)
        self.period_combo.currentIndexChanged.connect(self.refresh)
        self.mode_combo.currentIndexChanged.connect(self.refresh)
        self.refresh()

    def _report(self):
        return self.analytics.report(self.period_combo.currentData(), self.mode_combo.currentData())

    def refresh(self, *_):
        report = self._report()
        self.current_report = report
        values = {
            "best_wpm": f"{report['best_wpm']:.1f}",
            "average_wpm": f"{report['average_wpm']:.1f}" if report["average_wpm"] is not None else "—",
            "accuracy": f"{report['accuracy']:.1f}%" if report["accuracy"] is not None else "—",
            "count": str(report["count"]), "minutes": f"{report['minutes']:.1f} dk",
        }
        for key, value in values.items():
            self.summary_values[key].setText(value)
        self.data_note.setText(
            f"{report['unknown_duration_count']} dolu seansın aktif süresi bilinmiyor; hız ortalamasına ve "
            f"hız grafiğine katılmadı. {report['empty_count']} boş seans hız/doğruluk hesabına katılmadı. "
            "En iyi kayıtlı WPM eski kayıtları da içerir. Ortalama hız: doğru karakter / 5 / aktif dakika. "
            "Doğruluk, Backspace düzeltmelerinden sonra kalan metne dayanır.")
        self.wpm_chart.set_data([row["wpm"] for row in report["speed_history"]])
        self.acc_chart.set_data([
            row["correct_chars"] / row["total_chars"] * 100 for row in report["accuracy_history"]])
        self.heatmap.set_data(report["physical_keys"])
        self.finger_chart.set_data(
            [FINGER_NAMES[code] for code in FINGER_ORDER],
            [report["fingers"].get(code, 0) for code in FINGER_ORDER])
        self.finger_note.setText(
            "Gerçekte kullanılan parmak ölçülmez; güncel Türkçe Q eşleştirmesi kullanılır "
            "(Ş/ş sağ serçe). "
            f"{report['unmapped']} karakter için parmak eşleştirmesi yok.")
        self.recommendation_label.setText(report["recommendation"]["explanation"])
        self.history_list.clear()
        for row in report["sessions"][:HISTORY_LIMIT]:
            mode = MODE_NAMES.get(row["mode"], row["mode"])
            detail = f" ({row['mode_detail']})" if row["mode_detail"] else ""
            duration = f"{row['duration_seconds']:.1f}s" if row["duration_seconds"] > 0 else "süre bilinmiyor"
            accuracy = f"{row['correct_chars'] / row['total_chars'] * 100:.1f}%" if row["total_chars"] else "—"
            self.history_list.addItem(QListWidgetItem(
                f"{row['finished_at'][:16]} — {mode}{detail} — {row['wpm']:.1f} WPM — {accuracy} — {duration}"))

    def _start_recommended_practice(self):
        page = getattr(self.window(), "pages", {}).get("custom")
        if page is None:
            return
        previous = page.text_edit.toPlainText()
        page.text_edit.setPlainText(self.current_report["recommendation"]["text"])
        if page._start_practice():
            self.window()._switch_page("custom")
        else:
            page.text_edit.setPlainText(previous)

    def _export_csv(self):
        path, _ = QFileDialog.getSaveFileName(self, "CSV Aktar", "typing_stats.csv", "CSV (*.csv)")
        if not path:
            return
        try:
            self.analytics.export_csv(path, self._report())
        except Exception as error:
            QMessageBox.warning(self, "Hata", f"CSV aktarılamadı: {error}")

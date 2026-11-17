"""Settings page: theme, sound, font size, daily goals, data export/import/reset."""
from __future__ import annotations

from ...database.backup import BackupService

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QSpinBox, QCheckBox, QGroupBox,
    QSlider, QFileDialog, QPushButton, QMessageBox,
)

from .base import BasePage
from ..theme import palette

FONT_MIN = 14
FONT_MAX = 36
WPM_MIN = 10
WPM_MAX = 120
MIN_MIN = 1
MIN_MAX = 120
FLASH_MS = 1500


class SettingsPage(BasePage):
    """Settings page — appearance, sound, goals, display, and data management."""

    def __init__(self, ctx, parent=None):
        super().__init__(ctx, parent)
        self.add_header("Ayarlar", "Uygulama tercihlerini düzenle")
        self._flash_timer = QTimer(self)
        self._flash_timer.timeout.connect(self._on_flash_tick)
        self._build_ui()

    def _build_ui(self) -> None:
        appearance = QGroupBox("Görünüm")
        ap_layout = QVBoxLayout(appearance)
        theme_row = QHBoxLayout()
        theme_row.addWidget(QLabel("Tema:"))
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Açık", "Koyu"])
        self.theme_combo.setCurrentIndex(0 if self.ctx.theme == "light" else 1)
        theme_row.addWidget(self.theme_combo)
        theme_row.addStretch()
        ap_layout.addLayout(theme_row)

        font_row = QHBoxLayout()
        font_row.addWidget(QLabel("Yazı boyutu:"))
        self.font_spin = QSpinBox()
        self.font_spin.setRange(FONT_MIN, FONT_MAX)
        self.font_spin.setValue(self.ctx.font_size)
        font_row.addWidget(self.font_spin)
        font_row.addStretch()
        ap_layout.addLayout(font_row)
        self._root.addWidget(appearance)

        sound_group = QGroupBox("Ses")
        sound_layout = QVBoxLayout(sound_group)
        self.sound_check = QCheckBox("Sesleri etkinleştir")
        self.sound_check.setChecked(self.ctx.sound.enabled)
        sound_layout.addWidget(self.sound_check)

        self.key_sound_check = QCheckBox("Tuş sesi")
        self.key_sound_check.setChecked(self.ctx.sound.key_enabled)
        sound_layout.addWidget(self.key_sound_check)

        self.error_sound_check = QCheckBox("Hata sesi")
        self.error_sound_check.setChecked(self.ctx.sound.error_enabled)
        sound_layout.addWidget(self.error_sound_check)

        vol_row = QHBoxLayout()
        vol_row.addWidget(QLabel("Ses seviyesi:"))
        self.volume_slider = QSlider(Qt.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(self.ctx.settings_repo.get_int("volume", 50))
        self.volume_slider.setFixedWidth(160)
        vol_row.addWidget(self.volume_slider)
        self._vol_label = QLabel(f"{self.volume_slider.value()}%")
        self._vol_label.setFixedWidth(36)
        self.volume_slider.valueChanged.connect(lambda v: self._vol_label.setText(f"{v}%"))
        vol_row.addWidget(self._vol_label)
        vol_row.addStretch()
        sound_layout.addLayout(vol_row)
        self._root.addWidget(sound_group)

        goals_group = QGroupBox("Günlük Hedefler")
        goals_layout = QVBoxLayout(goals_group)
        wpm_row = QHBoxLayout()
        wpm_row.addWidget(QLabel("Hedef WPM:"))
        self.goal_wpm_spin = QSpinBox()
        self.goal_wpm_spin.setRange(WPM_MIN, WPM_MAX)
        self.goal_wpm_spin.setValue(self.ctx.settings_repo.get_int("daily_goal_wpm", 40))
        wpm_row.addWidget(self.goal_wpm_spin)
        wpm_row.addStretch()
        goals_layout.addLayout(wpm_row)

        min_row = QHBoxLayout()
        min_row.addWidget(QLabel("Günlük pratik (dk):"))
        self.goal_min_spin = QSpinBox()
        self.goal_min_spin.setRange(MIN_MIN, MIN_MAX)
        self.goal_min_spin.setValue(self.ctx.settings_repo.get_int("daily_goal_minutes", 15))
        min_row.addWidget(self.goal_min_spin)
        min_row.addStretch()
        goals_layout.addLayout(min_row)
        self._root.addWidget(goals_group)

        for spin in (self.font_spin, self.goal_wpm_spin, self.goal_min_spin):
            spin.setMinimumWidth(120)
            spin.setAlignment(Qt.AlignCenter)

        display_group = QGroupBox("Görüntü Seçenekleri")
        display_layout = QVBoxLayout(display_group)
        self.timer_check = QCheckBox("Süre göstergesini göster")
        self.timer_check.setChecked(self.ctx.show_timer)
        display_layout.addWidget(self.timer_check)
        self.wpm_check = QCheckBox("WPM göstergesini göster")
        self.wpm_check.setChecked(self.ctx.show_wpm)
        display_layout.addWidget(self.wpm_check)
        self._root.addWidget(display_group)

        data_group = QGroupBox("Veri Yönetimi")
        data_layout = QVBoxLayout(data_group)
        data_row = QHBoxLayout()
        export_btn = QPushButton("📤 Dışa Aktar (JSON)")
        export_btn.setObjectName("secondary")
        export_btn.clicked.connect(self._export_data)
        data_row.addWidget(export_btn)
        import_btn = QPushButton("📥 İçe Aktar (JSON)")
        import_btn.setObjectName("secondary")
        import_btn.clicked.connect(self._import_data)
        data_row.addWidget(import_btn)
        reset_btn = QPushButton("🗑️ Verileri Sıfırla")
        reset_btn.setObjectName("secondary")
        reset_btn.clicked.connect(self._reset_data)
        data_row.addWidget(reset_btn)
        data_row.addStretch()
        data_layout.addLayout(data_row)
        self._root.addWidget(data_group)

        self.save_btn = QPushButton("💾 Ayarları Kaydet")
        self.save_btn.setObjectName("primary")
        self.save_btn.clicked.connect(self._save)
        self._root.addWidget(self.save_btn, 0, Qt.AlignLeft)
        self._root.addStretch(1)

    def _data_operation_allowed(self):
        for page in getattr(self.window(), "pages", {}).values():
            session = getattr(page, "session", None)
            if session is None or session.saved:
                continue
            if (session.pending is not None or page.engine.typed_char_count > 0
                    or getattr(page, "_test_active", False)
                    or getattr(page, "_acc_total", 0) > 0):
                QMessageBox.warning(
                    self, "Kaydedilmemiş çalışma",
                    "Önce mevcut çalışmayı tamamlayın veya Kaydı yeniden dene düğmesini kullanın.")
                return False
        return True

    def _export_data(self) -> None:
        if not self._data_operation_allowed():
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "Verileri Dışa Aktar", "typing_data.json", "JSON (*.json)")
        if not path:
            return
        try:
            BackupService(self.ctx.stats_repo.db).export_file(path)
            self.save_btn.setText("Veriler aktarıldı")
        except Exception as e:
            QMessageBox.warning(self, "Hata", f"Dışa aktarma başarısız: {e}")

    def _import_data(self) -> None:
        if not self._data_operation_allowed():
            return
        path, _ = QFileDialog.getOpenFileName(
            self, "Verileri İçe Aktar", "", "JSON (*.json)")
        if not path:
            return
        try:
            count = BackupService(self.ctx.stats_repo.db).import_file(path)
        except Exception as e:
            QMessageBox.warning(self, "Hata", f"İçe aktarma başarısız: {e}")
            return
        self._reload_after_data_change()
        self.save_btn.setText(f"{count} yeni seans içe aktarıldı")

    def _reset_data(self) -> None:
        if not self._data_operation_allowed():
            return
        reply = QMessageBox.question(
            self, "Verileri Sıfırla",
            "Tüm seanslar, ders ilerlemesi, başarılar ve ayarlar silinecek. Emin misin?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply != QMessageBox.Yes:
            return
        try:
            BackupService(self.ctx.stats_repo.db).reset()
        except Exception as e:
            QMessageBox.warning(self, "Hata", f"Sıfırlama başarısız: {e}")
            return
        self._reload_after_data_change()
        self.save_btn.setText("Veriler sıfırlandı")

    def _reload_after_data_change(self):
        from ...config import DEFAULT_SETTINGS
        repo = self.ctx.settings_repo
        values = DEFAULT_SETTINGS | repo.get_all()
        self.ctx.theme = values["theme"]
        self.ctx.font_size = int(values["font_size"])
        self.ctx.show_timer = values["show_timer"] == "True"
        self.ctx.show_wpm = values["show_wpm"] == "True"
        self.ctx.sound.enabled = values["sound_enabled"] == "True"
        self.ctx.sound.key_enabled = values["key_sound_enabled"] == "True"
        self.ctx.sound.error_enabled = values["error_sound_enabled"] == "True"
        self.ctx.sound.set_volume(int(values["volume"]) / 100)
        self.theme_combo.setCurrentIndex(0 if self.ctx.theme == "light" else 1)
        self.font_spin.setValue(self.ctx.font_size)
        self.sound_check.setChecked(self.ctx.sound.enabled)
        self.key_sound_check.setChecked(self.ctx.sound.key_enabled)
        self.error_sound_check.setChecked(self.ctx.sound.error_enabled)
        self.timer_check.setChecked(self.ctx.show_timer)
        self.wpm_check.setChecked(self.ctx.show_wpm)
        self.volume_slider.setValue(int(values["volume"]))
        self.goal_wpm_spin.setValue(int(values["daily_goal_wpm"]))
        self.goal_min_spin.setValue(int(values["daily_goal_minutes"]))
        for page in getattr(self.window(), "pages", {}).values():
            if hasattr(page, "session"):
                page.pause_page()
                page.engine.reset("")
                page.session.reset()
                page.retry_save_btn.hide()
                if hasattr(page, "current_lesson"):
                    page.current_lesson = None
                if hasattr(page, "_active"):
                    page._active = False
                if hasattr(page, "_test_active"):
                    page._test_active = False
                    page._saved = False
                    page._acc_total = page._acc_correct = page._acc_incorrect = 0
                    page._acc_key_counts = {}
                    page._acc_text_parts = []
                    page._acc_max_wpm = 0
                    page._test_started_at = ""
                    page._remaining_seconds = 0
                    page.start_btn.setText("Testi Başlat")
                page.typing_area.text_display.update()
            if hasattr(page, "refresh"):
                page.refresh()
        if hasattr(self.window(), "apply_settings"):
            self.window().apply_settings()

    def _save(self) -> None:
        self.ctx.settings_repo.set("theme", "dark" if self.theme_combo.currentIndex() == 1 else "light")
        self.ctx.settings_repo.set("font_size", str(self.font_spin.value()))
        self.ctx.settings_repo.set("sound_enabled", str(self.sound_check.isChecked()))
        self.ctx.settings_repo.set("key_sound_enabled", str(self.key_sound_check.isChecked()))
        self.ctx.settings_repo.set("error_sound_enabled", str(self.error_sound_check.isChecked()))
        self.ctx.settings_repo.set("volume", str(self.volume_slider.value()))
        self.ctx.settings_repo.set("daily_goal_wpm", str(self.goal_wpm_spin.value()))
        self.ctx.settings_repo.set("daily_goal_minutes", str(self.goal_min_spin.value()))
        self.ctx.settings_repo.set("show_timer", str(self.timer_check.isChecked()))
        self.ctx.settings_repo.set("show_wpm", str(self.wpm_check.isChecked()))

        self.ctx.sound.enabled = self.sound_check.isChecked()
        self.ctx.sound.key_enabled = self.key_sound_check.isChecked()
        self.ctx.sound.error_enabled = self.error_sound_check.isChecked()
        self.ctx.sound.set_volume(self.volume_slider.value() / 100.0)
        self.ctx.font_size = self.font_spin.value()
        self.ctx.theme = "dark" if self.theme_combo.currentIndex() == 1 else "light"
        self.ctx.show_timer = self.timer_check.isChecked()
        self.ctx.show_wpm = self.wpm_check.isChecked()

        self._flash_button()
        main_win = self.window()
        if hasattr(main_win, "apply_settings"):
            main_win.apply_settings()

    def _flash_button(self) -> None:
        p = palette(self.ctx.theme)
        self.save_btn.setText("✅ Ayarlar Onaylandı")
        self.save_btn.setStyleSheet(
            f"QPushButton {{ background-color: {p['success']}; color: white; border: none; "
            "border-radius: 6px; padding: 8px 20px; font-size: 14px; font-weight: 600; }"
        )
        self._flash_timer.start(FLASH_MS)

    def _on_flash_tick(self) -> None:
        self._flash_timer.stop()
        self.save_btn.setText("💾 Ayarları Kaydet")
        self.save_btn.setStyleSheet("")
        self.save_btn.setObjectName("primary")

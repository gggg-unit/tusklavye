"""Main window with sidebar navigation and global key event routing."""
from __future__ import annotations

import logging
import sys

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QKeyEvent, QIcon, QPixmap, QPainter, QColor, QLinearGradient, QBrush
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QFrame, QPushButton,
    QStackedWidget, QLabel, QButtonGroup, QMessageBox,
)

from ..config import APP_NAME, APP_VERSION, DEFAULT_SETTINGS
from ..core.typing_engine import TypingEngine
from ..core.sound import SoundManager
from ..core.keyboard_layout import KeyboardLayout
from ..core.fonts import ui_font
from ..database.models import (
    StatsRepository, LessonRepository, AchievementRepository, SettingsRepository, SessionRecord,
)
from .theme import get_qss, palette
from .app_context import AppContext
from .pages.home import HomePage
from .pages.training import TrainingPage
from .pages.tests import TestsPage
from .pages.statistics import StatisticsPage
from .pages.achievements import AchievementsPage
from .pages.custom_text import CustomTextPage
from .pages.settings import SettingsPage

logger = logging.getLogger(__name__)

NAV_ITEMS = [
    ("🏠", "Ana Sayfa", "home"),
    ("📖", "Eğitim", "training"),
    ("⏱️", "Testler", "tests"),
    ("📝", "Özel Metin", "custom"),
    ("📊", "İstatistikler", "stats"),
    ("🏆", "Başarılar", "achievements"),
    ("⚙️", "Ayarlar", "settings"),
]

WINDOW_MIN_W = 1100
WINDOW_MIN_H = 720
WINDOW_W = 1200
WINDOW_H = 800
SIDEBAR_W = 220
BRAND_FONT_PX = 16
VERSION_FONT_PX = 11


class MainWindow(QMainWindow):
    """Main application window with sidebar navigation and key routing."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle(APP_NAME)
        self.setMinimumSize(WINDOW_MIN_W, WINDOW_MIN_H)
        self.resize(WINDOW_W, WINDOW_H)
        self.setFocusPolicy(Qt.StrongFocus)
        self._set_app_icon()

        self._init_context()
        self._build_ui()
        self.apply_settings()

    def _set_app_icon(self) -> None:
        if sys.platform == "win32":
            try:
                import ctypes
                ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("TuşKlavye.10Parmak.1")
            except Exception:
                pass

        px = QPixmap(64, 64)
        px.fill(Qt.transparent)
        p = QPainter(px)
        p.setRenderHint(QPainter.Antialiasing)

        grad = QLinearGradient(0, 0, 0, 64)
        grad.setColorAt(0, QColor("#0078d4"))
        grad.setColorAt(1, QColor("#00549b"))
        p.setBrush(QBrush(grad))
        p.setPen(QColor("#00345e"))
        p.drawRoundedRect(2, 2, 60, 60, 12, 12)

        p.setPen(QColor("#ffffff"))
        font = QFont(ui_font(), 26, QFont.Bold)
        p.setFont(font)
        p.drawText(px.rect().adjusted(0, -6, 0, 0), Qt.AlignCenter, "10")

        p.setPen(QColor("#ffffff"))
        p.setBrush(QColor("#ffffff"))
        key_w, key_h, gap = 6, 4, 2
        total_w = 5 * key_w + 4 * gap
        start_x = (64 - total_w) // 2
        y = 44
        for i in range(5):
            p.drawRoundedRect(start_x + i * (key_w + gap), y, key_w, key_h, 1, 1)

        p.end()
        self.setWindowIcon(QIcon(px))

    def _init_context(self) -> None:
        self.layout_def = KeyboardLayout()
        self.engine = TypingEngine(self.layout_def)
        self.sound = SoundManager(self)
        self.stats_repo = StatsRepository()
        self.lesson_repo = LessonRepository()
        self.achievement_repo = AchievementRepository()
        self.settings_repo = SettingsRepository()

        settings = self.settings_repo.get_all()
        for key, default in DEFAULT_SETTINGS.items():
            if key not in settings:
                settings[key] = default
        theme = settings.get("theme", "dark")
        font_size = int(settings.get("font_size", "26"))
        show_timer = settings.get("show_timer", "False") == "True"
        show_wpm = settings.get("show_wpm", "False") == "True"
        self.sound.enabled = settings.get("sound_enabled", "True") == "True"
        self.sound.key_enabled = settings.get("key_sound_enabled", "True") == "True"
        self.sound.error_enabled = settings.get("error_sound_enabled", "True") == "True"
        self.sound.set_volume(float(settings.get("volume", "50")) / 100.0)

        self.ctx = AppContext(
            engine=self.engine,
            sound=self.sound,
            layout=self.layout_def,
            stats_repo=self.stats_repo,
            lesson_repo=self.lesson_repo,
            achievement_repo=self.achievement_repo,
            settings_repo=self.settings_repo,
            font_size=font_size,
            theme=theme,
            show_timer=show_timer,
            show_wpm=show_wpm,
        )

    def _build_ui(self) -> None:
        pal = palette(self.ctx.theme)
        central = QWidget()
        central.setObjectName("central")
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(SIDEBAR_W)
        sb_layout = QVBoxLayout(sidebar)
        sb_layout.setContentsMargins(12, 16, 12, 16)
        sb_layout.setSpacing(4)

        brand = QLabel(APP_NAME.split(" - ")[0])
        brand.setStyleSheet(f"font-size: {BRAND_FONT_PX}px; font-weight: 700; padding: 8px 8px 16px 8px;")
        sb_layout.addWidget(brand)

        self.nav_group = QButtonGroup(self)
        self.nav_group.setExclusive(True)
        self.nav_buttons: dict = {}
        for emoji, label, key in NAV_ITEMS:
            btn = QPushButton(f"  {emoji}  {label}")
            btn.setObjectName("navBtn")
            btn.setCheckable(True)
            btn.clicked.connect(lambda checked, k=key: self._switch_page(k))
            self.nav_group.addButton(btn)
            sb_layout.addWidget(btn)
            self.nav_buttons[key] = btn

        sb_layout.addStretch()
        ver = QLabel(f"v{APP_VERSION}")
        ver.setStyleSheet(f"color: {pal['text_muted']}; font-size: {VERSION_FONT_PX}px; padding: 8px;")
        sb_layout.addWidget(ver)

        main_layout.addWidget(sidebar)

        self.stack = QStackedWidget()
        self.pages: dict = {}
        self.pages["home"] = HomePage(self.ctx)
        self.pages["training"] = TrainingPage(self.ctx)
        self.pages["tests"] = TestsPage(self.ctx)
        self.pages["custom"] = CustomTextPage(self.ctx)
        self.pages["stats"] = StatisticsPage(self.ctx)
        self.pages["achievements"] = AchievementsPage(self.ctx)
        self.pages["settings"] = SettingsPage(self.ctx)
        for key in [k for _, _, k in NAV_ITEMS]:
            self.stack.addWidget(self.pages[key])
        main_layout.addWidget(self.stack)

        self.setCentralWidget(central)
        self.nav_buttons["home"].setChecked(True)
        self._current_page_key = "home"

    def _switch_page(self, key: str) -> None:
        old_page = self.pages.get(self._current_page_key)
        if old_page and hasattr(old_page, "pause_page"):
            old_page.pause_page()

        self._current_page_key = key
        page = self.pages.get(key)
        if page and hasattr(page, "refresh"):
            page.refresh()
        self.stack.setCurrentWidget(page)

        if page and hasattr(page, "resume_page"):
            page.resume_page()

        btn = self.nav_buttons.get(key)
        if btn:
            btn.setChecked(True)

    def apply_settings(self) -> None:
        self.setStyleSheet(get_qss(self.ctx.theme))
        self.engine.layout = self.layout_def
        for page in self.pages.values():
            ta = getattr(page, "typing_area", None)
            if ta is not None:
                ta.set_font_size(self.ctx.font_size)
                ta.set_theme(self.ctx.theme)
            finger_guide = getattr(page, "finger_guide", None)
            if finger_guide is not None and hasattr(finger_guide, "set_theme"):
                finger_guide.set_theme(self.ctx.theme)
            keyboard = getattr(page, "keyboard", None)
            if keyboard is not None and hasattr(keyboard, "set_theme"):
                keyboard.set_theme(self.ctx.theme)
            heatmap = getattr(page, "heatmap", None)
            if heatmap is not None and hasattr(heatmap, "set_theme"):
                heatmap.set_theme(self.ctx.theme)
            for chart_name in ("wpm_chart", "acc_chart", "finger_chart"):
                chart = getattr(page, chart_name, None)
                if chart is not None and hasattr(chart, "set_theme"):
                    chart.set_theme(self.ctx.theme)
            if hasattr(page, "set_header_timer_visible"):
                page.set_header_timer_visible(self.ctx.show_timer)
            if hasattr(page, "set_header_wpm_visible"):
                page.set_header_wpm_visible(self.ctx.show_wpm)

    def keyPressEvent(self, event: QKeyEvent) -> None:
        key = event.key()
        text = event.text()

        if event.modifiers() & Qt.ControlModifier:
            nav_keys = {
                Qt.Key_1: "home", Qt.Key_2: "training", Qt.Key_3: "tests",
                Qt.Key_4: "custom", Qt.Key_5: "stats", Qt.Key_6: "achievements",
                Qt.Key_7: "settings",
            }
            if key in nav_keys:
                self._switch_page(nav_keys[key])
                return
            if key == Qt.Key_R:
                page = self.pages.get(self._current_page_key)
                if page and hasattr(page, "retry_lesson"):
                    page.retry_lesson()
                elif page and hasattr(page, "_retry_test"):
                    page._retry_test()
                return
        if key == Qt.Key_Escape:
            page = self.pages.get(self._current_page_key)
            if page and hasattr(page, "pause_page"):
                page.pause_page()
                return
        if key == Qt.Key_Tab:
            if self._current_page_key in ("training", "tests", "custom"):
                return
            super().keyPressEvent(event)
            return
        if key == Qt.Key_Backspace:
            page = self.pages.get(self._current_page_key)
            if page and hasattr(page, "on_key_press"):
                page.on_key_press("\b", "")
            return
        if key in (Qt.Key_Return, Qt.Key_Enter):
            text = "\n"
        if key == Qt.Key_Space:
            text = " "
        if not text:
            super().keyPressEvent(event)
            return

        page = self.pages.get(self._current_page_key)
        if page and hasattr(page, "on_key_press"):
            page.on_key_press(text, event.text())
        else:
            super().keyPressEvent(event)

    def closeEvent(self, event) -> None:
        """Save any in-progress sessions before closing, with error reporting."""
        mode_map = {"training": "lesson", "tests": "test", "custom": "custom"}
        save_errors = []
        for key, page in self.pages.items():
            engine = getattr(page, "engine", None)
            if not engine or not engine.target_text or engine.is_finished or engine.position == 0:
                continue
            result = engine.get_result()
            if key == "tests" and hasattr(page, "_acc_total") and hasattr(page, "_combine_result"):
                result = page._combine_result(result)
            mode = mode_map.get(key, "unknown")
            mode_detail = ""
            if key == "training" and getattr(page, "current_lesson", None):
                mode_detail = page.current_lesson["id"]
            elif key == "tests":
                mode_detail = f"{getattr(page, '_time_limit', 0)}s"
            elif key == "custom":
                mode_detail = "custom_text"
            try:
                record = SessionRecord(
                    mode=mode, mode_detail=mode_detail,
                    text_content=engine.target_text,
                    total_chars=result.total_chars,
                    correct_chars=result.correct_chars,
                    incorrect_chars=result.incorrect_chars,
                    wpm=result.wpm, raw_wpm=result.raw_wpm,
                    accuracy=result.accuracy, max_wpm=result.max_wpm,
                    key_counts=result.key_counts, started_at=result.started_at,
                )
                self.ctx.stats_repo.save_session(record)
            except Exception as e:
                logger.error(f"Failed to save pending session on close: {e}", exc_info=True)
                save_errors.append(str(e))

        if save_errors:
            QMessageBox.warning(
                self,
                "Uyarı",
                f"{len(save_errors)} oturum kaydedilemedi. Veriler kaybolmuş olabilir.\n"
                f"İlk hata: {save_errors[0]}",
            )

        try:
            from ..database.db import Database
            Database.get().close()
        except Exception as e:
            logger.error(f"Failed to close database on close: {e}", exc_info=True)

        super().closeEvent(event)

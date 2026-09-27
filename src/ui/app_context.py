"""Shared application context passed to all pages."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from ..core.typing_engine import TypingEngine
from ..core.sound import SoundManager
from ..core.keyboard_layout import KeyboardLayout
from ..database.models import (
    StatsRepository, LessonRepository, AchievementRepository, SettingsRepository,
)


@dataclass
class AppContext:
    """Dependency-injection container shared between MainWindow and all pages."""
    engine: TypingEngine
    sound: SoundManager
    layout: KeyboardLayout
    stats_repo: StatsRepository
    lesson_repo: LessonRepository
    achievement_repo: AchievementRepository
    settings_repo: SettingsRepository
    font_size: int = 26
    theme: str = "dark"
    show_timer: bool = False
    show_wpm: bool = False

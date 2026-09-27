"""Achievement definitions and unlock logic.

Each achievement is a ``(code, title, description, emoji)`` tuple. The
``check_and_unlock`` function queries the stats/lesson/streak state and unlocks
any newly-satisfied achievements.
"""
from __future__ import annotations

from typing import List, Tuple

from ..database.models import AchievementRepository, StatsRepository
from .lessons import LESSONS

ACHIEVEMENTS: List[Tuple[str, str, str, str]] = [
    ("first_session", "İlk Adım", "İlk pratiğini tamamla", "🎯"),
    ("speed_20", "Hızlı Başlangıç", "20 WPM hızına ulaş", "⚡"),
    ("speed_40", "Hızlı Yazıcı", "40 WPM hızına ulaş", "🚀"),
    ("speed_60", "Usta Yazıcı", "60 WPM hızına ulaş", "🏆"),
    ("accuracy_95", "Hassas", "%95 doğruluk yakala", "💎"),
    ("accuracy_100", "Kusursuz", "%100 doğruluk yakala", "✨"),
    ("streak_3", "Seride 3", "3 gün üst üste pratik yap", "🔥"),
    ("streak_7", "Haftalık Seri", "7 gün üst üste pratik yap", "📅"),
    ("sessions_10", "Azimli", "10 pratik seansı tamamla", "💪"),
    ("sessions_50", "Düşkün", "50 pratik seansı tamamla", "📚"),
    ("lessons_5", "Öğrenci", "5 dersi tamamla", "🎓"),
    ("lessons_all", "Usta", "Tüm dersleri tamamla", "👑"),
]

THRESHOLDS = {
    "first_session": 1,
    "speed_20": 20,
    "speed_40": 40,
    "speed_60": 60,
    "accuracy_95": 95,
    "accuracy_100": 100.0,
    "streak_3": 3,
    "streak_7": 7,
    "sessions_10": 10,
    "sessions_50": 50,
    "lessons_5": 5,
    "lessons_all": len(LESSONS),
}


def check_and_unlock(
    stats: StatsRepository,
    achievements: AchievementRepository,
    lesson_count: int = 0,
    streak: int = 0,
) -> list:
    """Check all achievements and unlock any newly-satisfied ones.

    Returns a list of newly-unlocked achievement codes.
    """
    newly_unlocked = []
    best_wpm = stats.get_best_wpm()
    best_acc = stats.get_best_accuracy()
    session_count = stats.get_session_count()

    checks = {
        "first_session": session_count >= THRESHOLDS["first_session"],
        "speed_20": best_wpm >= THRESHOLDS["speed_20"],
        "speed_40": best_wpm >= THRESHOLDS["speed_40"],
        "speed_60": best_wpm >= THRESHOLDS["speed_60"],
        "accuracy_95": best_acc >= THRESHOLDS["accuracy_95"],
        "accuracy_100": best_acc >= THRESHOLDS["accuracy_100"],
        "streak_3": streak >= THRESHOLDS["streak_3"],
        "streak_7": streak >= THRESHOLDS["streak_7"],
        "sessions_10": session_count >= THRESHOLDS["sessions_10"],
        "sessions_50": session_count >= THRESHOLDS["sessions_50"],
        "lessons_5": lesson_count >= THRESHOLDS["lessons_5"],
        "lessons_all": lesson_count >= THRESHOLDS["lessons_all"],
    }

    for code, _, _, _ in ACHIEVEMENTS:
        if checks.get(code) and achievements.unlock(code):
            newly_unlocked.append(code)
    return newly_unlocked


def get_definitions() -> list:
    """Return the full list of achievement definition tuples."""
    return ACHIEVEMENTS

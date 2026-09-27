"""High-level database operations for sessions, stats, achievements, settings.

Uses a ``SessionRecord`` dataclass instead of a long positional-arg list, and
``SettingsRepository`` exposes typed ``get_bool``/``get_int``/``get_float``
accessors so callers do not need to compare against the string ``"True"``.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, date
from typing import Optional, Dict

from .db import Database
from ..core.keyboard_layout import _tr_lower

MAX_TEXT_LENGTH = 10000


def _now() -> str:
    return datetime.now().isoformat(timespec="seconds")


def _today() -> str:
    return date.today().isoformat()


@dataclass
class SessionRecord:
    """A completed typing session ready to be persisted."""
    mode: str
    mode_detail: str
    text_content: str
    total_chars: int
    correct_chars: int
    incorrect_chars: int
    wpm: float
    raw_wpm: float
    accuracy: float
    max_wpm: float
    key_counts: Dict[str, Dict[str, int]] = field(default_factory=dict)
    started_at: str = ""


class StatsRepository:
    """Repository for typing sessions and aggregate statistics."""

    def __init__(self, db: Optional[Database] = None):
        self.db = db or Database.get()

    def save_session(self, record: SessionRecord) -> int:
        """Persist a session and its per-key stats. Returns the new session id."""
        text = record.text_content or ""
        finished = _now()
        if record.started_at:
            try:
                duration = (
                    datetime.fromisoformat(finished)
                    - datetime.fromisoformat(record.started_at)
                ).total_seconds()
            except (ValueError, TypeError):
                duration = 0.0
        else:
            duration = 0.0
            record.started_at = finished

        cur = self.db.execute_no_commit(
            """INSERT INTO sessions
               (started_at, finished_at, duration_seconds, mode, mode_detail,
                text_content, total_chars, correct_chars, incorrect_chars,
                wpm, raw_wpm, accuracy, max_wpm)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                record.started_at,
                finished,
                duration,
                record.mode,
                record.mode_detail,
                text[:MAX_TEXT_LENGTH],
                record.total_chars,
                record.correct_chars,
                record.incorrect_chars,
                record.wpm,
                record.raw_wpm,
                record.accuracy,
                record.max_wpm,
            ),
        )
        session_id = cur.lastrowid
        if record.key_counts:
            rows = [
                (session_id, k, v.get("correct", 0), v.get("incorrect", 0))
                for k, v in record.key_counts.items()
            ]
            self.db.executemany_no_commit(
                """INSERT INTO key_stats (session_id, key_char, correct_count, incorrect_count)
                   VALUES (?, ?, ?, ?)""",
                rows,
            )
        self._touch_streak_no_commit()
        self.db.commit()
        return session_id

    def _touch_streak_no_commit(self):
        """Mark today as practiced, without committing (caller commits)."""
        today = _today()
        row = self.db.query_one("SELECT 1 FROM streak WHERE date = ?", (today,))
        if row is None:
            self.db.execute_no_commit(
                "INSERT INTO streak (date, practiced) VALUES (?, 1)", (today,)
            )

    def get_recent_sessions(self, limit: int = 20) -> list:
        return self.db.query(
            "SELECT * FROM sessions ORDER BY finished_at DESC LIMIT ?", (limit,)
        )

    def get_session_count(self) -> int:
        row = self.db.query_one("SELECT COUNT(*) AS c FROM sessions")
        return row["c"] if row else 0

    def get_best_wpm(self) -> float:
        row = self.db.query_one("SELECT MAX(wpm) AS m FROM sessions")
        return row["m"] if row and row["m"] is not None else 0.0

    def get_avg_accuracy(self) -> float:
        row = self.db.query_one("SELECT AVG(accuracy) AS a FROM sessions")
        return row["a"] if row and row["a"] is not None else 0.0

    def get_best_accuracy(self) -> float:
        row = self.db.query_one("SELECT MAX(accuracy) AS a FROM sessions")
        return row["a"] if row and row["a"] is not None else 0.0

    def get_total_practice_minutes(self) -> float:
        row = self.db.query_one("SELECT SUM(duration_seconds) AS s FROM sessions")
        return (row["s"] / 60.0) if row and row["s"] is not None else 0.0

    def get_wpm_history(self, limit: int = 30) -> list:
        return self.db.query(
            "SELECT wpm, accuracy, finished_at FROM sessions ORDER BY finished_at DESC LIMIT ?",
            (limit,),
        )

    def get_key_error_stats(self) -> dict:
        rows = self.db.query(
            """SELECT key_char,
                      SUM(correct_count) AS correct,
                      SUM(incorrect_count) AS incorrect
               FROM key_stats GROUP BY key_char"""
        )
        return {r["key_char"]: {"correct": r["correct"], "incorrect": r["incorrect"]} for r in rows}

    def get_finger_stats(self, finger_map: dict) -> dict:
        key_stats = self.get_key_error_stats()
        finger_stats: dict = {}
        for key_char, counts in key_stats.items():
            finger = finger_map.get(key_char) or finger_map.get(_tr_lower(key_char))
            if not finger:
                continue
            agg = finger_stats.setdefault(
                finger, {"correct": 0, "incorrect": 0, "total": 0}
            )
            agg["correct"] += counts["correct"]
            agg["incorrect"] += counts["incorrect"]
            agg["total"] += counts["correct"] + counts["incorrect"]
        return finger_stats

    def get_streak(self) -> int:
        rows = self.db.query("SELECT date FROM streak ORDER BY date DESC")
        if not rows:
            return 0
        dates = [date.fromisoformat(row["date"]) for row in rows]
        today = date.today()
        yesterday = date.fromordinal(today.toordinal() - 1)

        if dates[0] == today:
            expected = today
        elif dates[0] == yesterday:
            expected = yesterday
        else:
            return 0

        streak = 0
        for d in dates:
            if d == expected:
                streak += 1
                expected = date.fromordinal(expected.toordinal() - 1)
            elif d == date.fromordinal(expected.toordinal() + 1):
                continue
            else:
                break
        return streak

    def get_today_session_count(self) -> int:
        row = self.db.query_one(
            "SELECT COUNT(*) AS c FROM sessions WHERE date(finished_at) = ?", (_today(),)
        )
        return row["c"] if row else 0

    def get_today_practice_minutes(self) -> float:
        row = self.db.query_one(
            "SELECT SUM(duration_seconds) AS s FROM sessions WHERE date(finished_at) = ?",
            (_today(),),
        )
        return (row["s"] / 60.0) if row and row["s"] is not None else 0.0

    def get_today_best_wpm(self) -> float:
        row = self.db.query_one(
            "SELECT MAX(wpm) AS m FROM sessions WHERE date(finished_at) = ?", (_today(),)
        )
        return row["m"] if row and row["m"] is not None else 0.0

    def get_all_sessions(self, limit: int = 100) -> list:
        return self.db.query(
            "SELECT * FROM sessions ORDER BY finished_at DESC LIMIT ?", (limit,)
        )


class LessonRepository:
    """Repository for lesson completion progress."""

    def __init__(self, db: Optional[Database] = None):
        self.db = db or Database.get()

    def mark_completed(self, lesson_id: str, wpm: float, accuracy: float) -> None:
        row = self.db.query_one(
            "SELECT * FROM lesson_progress WHERE lesson_id = ?", (lesson_id,)
        )
        if row is None:
            self.db.execute(
                """INSERT INTO lesson_progress (lesson_id, completed_at, best_wpm, best_accuracy)
                   VALUES (?, ?, ?, ?)""",
                (lesson_id, _now(), wpm, accuracy),
            )
        else:
            self.db.execute(
                """UPDATE lesson_progress
                   SET completed_at = ?, best_wpm = MAX(best_wpm, ?),
                       best_accuracy = MAX(best_accuracy, ?), attempts = attempts + 1
                   WHERE lesson_id = ?""",
                (_now(), wpm, accuracy, lesson_id),
            )

    def get_completed(self) -> dict:
        rows = self.db.query("SELECT * FROM lesson_progress")
        return {r["lesson_id"]: dict(r) for r in rows}

    def is_completed(self, lesson_id: str) -> bool:
        row = self.db.query_one(
            "SELECT 1 FROM lesson_progress WHERE lesson_id = ?", (lesson_id,)
        )
        return row is not None


class AchievementRepository:
    """Repository for unlocked achievements."""

    def __init__(self, db: Optional[Database] = None):
        self.db = db or Database.get()

    def unlock(self, code: str) -> bool:
        row = self.db.query_one("SELECT 1 FROM achievements WHERE code = ?", (code,))
        if row is not None:
            return False
        self.db.execute(
            "INSERT INTO achievements (code, unlocked_at) VALUES (?, ?)", (code, _now())
        )
        return True

    def get_all(self) -> list:
        return self.db.query("SELECT * FROM achievements ORDER BY unlocked_at")


class SettingsRepository:
    """Repository for application settings with typed accessors."""

    def __init__(self, db: Optional[Database] = None):
        self.db = db or Database.get()

    def get_all(self) -> dict:
        rows = self.db.query("SELECT key, value FROM settings")
        return {r["key"]: r["value"] for r in rows}

    def get(self, key: str, default=None):
        row = self.db.query_one("SELECT value FROM settings WHERE key = ?", (key,))
        return row["value"] if row else default

    def get_bool(self, key: str, default: bool = False) -> bool:
        raw = self.get(key)
        if raw is None:
            return default
        return raw == "True"

    def get_int(self, key: str, default: int = 0) -> int:
        raw = self.get(key)
        if raw is None:
            return default
        try:
            return int(raw)
        except (ValueError, TypeError):
            return default

    def get_float(self, key: str, default: float = 0.0) -> float:
        raw = self.get(key)
        if raw is None:
            return default
        try:
            return float(raw)
        except (ValueError, TypeError):
            return default

    def set(self, key: str, value) -> None:
        self.db.execute(
            "INSERT INTO settings (key, value) VALUES (?, ?) "
            "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
            (key, str(value)),
        )

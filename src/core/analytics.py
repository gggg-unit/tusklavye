"""Read-only filtered statistics and deterministic practice recommendations."""
import csv
import os
import tempfile
from datetime import date, timedelta
from pathlib import Path

from .keyboard_layout import KeyboardLayout


def aggregate_keys(key_stats, layout):
    physical, fingers = {}, {}
    unknown = 0
    for char, counts in key_stats.items():
        total = counts["correct"] + counts["incorrect"]
        base, _ = layout.stroke_for_char(char)
        finger = layout.finger_for_char(char)
        if not base or not finger:
            unknown += total
            continue
        entry = physical.setdefault(base, {"correct": 0, "incorrect": 0})
        entry["correct"] += counts["correct"]
        entry["incorrect"] += counts["incorrect"]
        fingers[finger] = fingers.get(finger, 0) + total
    return physical, fingers, unknown


def recommend_practice(key_stats, layout):
    """Minimum five samples and two errors; prioritize error rate, then count."""
    candidates = []
    for char, counts in key_stats.items():
        total = counts["correct"] + counts["incorrect"]
        if (total >= 5 and counts["incorrect"] >= 2 and char.isprintable()
                and not char.isspace() and layout.finger_for_char(char)):
            candidates.append((char, counts["incorrect"], total))
    candidates.sort(key=lambda item: (-item[1] / item[2], -item[1], item[0]))
    selected = candidates[:5]
    if not selected:
        return {
            "text": "asdf jklş asdf jklş\naş sk dl fj aş sk dl fj",
            "keys": [],
            "explanation": ("Bu seçimde kişisel öneri için yeterli hata örneği yok. "
                            "Başlangıç: ana sıra çalışması. Eşik: tuş başına en az 5 örnek ve 2 hata."),
        }
    keys = [item[0] for item in selected]
    chunks = [key * 3 for key in keys]
    pairs = [key + keys[(index + 1) % len(keys)] for index, key in enumerate(keys)]
    text = " ".join(chunks + pairs) + "\n" + " ".join(reversed(chunks + pairs))
    description = ", ".join(f"{char}: {errors}/{total} hata" for char, errors, total in selected)
    return {"text": text, "keys": keys,
            "explanation": "Seçili dönemde öncelikli tuşlar — " + description}


class AnalyticsService:
    def __init__(self, db, layout=None):
        self.db = db
        self.layout = layout or KeyboardLayout()

    def report(self, days=None, mode=None, today=None):
        if days is not None and (type(days) is not int or days < 1):
            raise ValueError("days must be a positive integer")
        if mode not in (None, "lesson", "test", "custom"):
            raise ValueError("Invalid mode")
        clauses, params = [], []
        if days is not None:
            end = today or date.today()
            start = end - timedelta(days=days - 1)
            clauses.append("substr(s.finished_at, 1, 10) BETWEEN ? AND ?")
            params.extend((start.isoformat(), end.isoformat()))
        if mode is not None:
            clauses.append("s.mode = ?")
            params.append(mode)
        where = " WHERE " + " AND ".join(clauses) if clauses else ""
        with self.db.transaction():
            sessions = [dict(row) for row in self.db.query(
                "SELECT s.* FROM sessions s" + where + " ORDER BY s.finished_at DESC, s.id DESC",
                tuple(params))]
            rows = self.db.query(
                "SELECT k.key_char, SUM(k.correct_count) AS correct, "
                "SUM(k.incorrect_count) AS incorrect FROM key_stats k "
                "JOIN sessions s ON s.id = k.session_id" + where + " GROUP BY k.key_char",
                tuple(params))
        key_stats = {row["key_char"]: {"correct": row["correct"], "incorrect": row["incorrect"]}
                     for row in rows}
        nonempty = [row for row in sessions if row["total_chars"] > 0]
        timed = [row for row in nonempty if row["duration_seconds"] > 0]
        chars = sum(row["total_chars"] for row in nonempty)
        correct = sum(row["correct_chars"] for row in nonempty)
        seconds = sum(row["duration_seconds"] for row in timed)
        physical, fingers, unknown = aggregate_keys(key_stats, self.layout)
        return {
            "sessions": sessions, "key_stats": key_stats, "physical_keys": physical,
            "fingers": fingers, "unmapped": unknown,
            "count": len(sessions), "empty_count": len(sessions) - len(nonempty),
            "unknown_duration_count": len(nonempty) - len(timed),
            "best_wpm": max((row["wpm"] for row in nonempty), default=0),
            "average_wpm": (sum(row["correct_chars"] for row in timed) * 12 / seconds
                            if seconds else None),
            "accuracy": correct * 100 / chars if chars else None,
            "minutes": seconds / 60,
            "speed_history": list(reversed(timed[:30])),
            "accuracy_history": list(reversed(nonempty[:30])),
            "recommendation": recommend_practice(key_stats, self.layout),
        }

    @staticmethod
    def export_csv(path, report):
        """Export all filtered rows, preserving an old file on write failure."""
        fields = ("finished_at", "mode", "mode_detail", "wpm", "raw_wpm", "accuracy",
                  "duration_seconds", "total_chars", "correct_chars", "incorrect_chars", "max_wpm")
        path = Path(path)
        temporary = None
        try:
            with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8-sig", newline="",
                                             dir=path.parent, prefix=path.name + ".",
                                             suffix=".tmp", delete=False) as stream:
                temporary = Path(stream.name)
                writer = csv.writer(stream)
                writer.writerow(fields)
                for session in report["sessions"]:
                    values = []
                    for field in fields:
                        value = session[field]
                        if isinstance(value, str) and value.lstrip().startswith(("=", "+", "-", "@")):
                            value = "'" + value
                        values.append(value)
                    writer.writerow(values)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, path)
        finally:
            if temporary is not None:
                temporary.unlink(missing_ok=True)

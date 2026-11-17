"""Versioned, validated, atomic backup merge. No UI or singleton dependencies."""
import json
import math
import os
import tempfile
from collections import Counter
from copy import deepcopy
from datetime import date, datetime
from hashlib import sha256
from pathlib import Path
from uuid import UUID

from .db import _SCHEMA_VERSION

FORMAT = "tusklavye"
VERSION = 1
TABLES = ("sessions", "key_stats", "lesson_progress", "achievements", "streak", "settings")
SESSION_FIELDS = (
    "started_at", "finished_at", "duration_seconds", "mode", "mode_detail",
    "text_content", "total_chars", "correct_chars", "incorrect_chars",
    "wpm", "raw_wpm", "accuracy", "max_wpm", "session_uid",
)
COUNTERS = ("total_chars", "correct_chars", "incorrect_chars")
METRICS = ("duration_seconds", "wpm", "raw_wpm", "accuracy", "max_wpm")
RELATED = {
    "lesson_progress": ("lesson_id", "completed_at", "best_wpm", "best_accuracy", "attempts"),
    "achievements": ("code", "unlocked_at"),
    "streak": ("date", "practiced"),
}


def _require(condition, message):
    if not condition:
        raise ValueError(message)


def _integer(value, minimum=0):
    _require(type(value) is int and minimum <= value <= 2**63 - 1, "Invalid integer")
    return value


def _number(value, maximum=None):
    _require(type(value) in (int, float) and math.isfinite(value) and value >= 0,
             "Invalid non-negative number")
    if maximum is not None:
        _require(value <= maximum, "Number outside allowed range")
    return float(value)


def _text(value, empty=True):
    _require(isinstance(value, str) and (empty or bool(value)), "Invalid text")
    return value


def _timestamp(value):
    _text(value, empty=False)
    datetime.fromisoformat(value)
    return value


def _unique(rows, key):
    values = [row[key] for row in rows]
    _require(len(values) == len(set(values)), f"Duplicate {key}")


def _settings(settings, legacy):
    _require(isinstance(settings, dict), "settings must be an object")
    result = {}
    for key, value in settings.items():
        _text(key, empty=False)
        if legacy and type(value) in (bool, int, float):
            if type(value) is float:
                _require(math.isfinite(value), "Invalid setting")
            value = str(value)
        _require(value is None or isinstance(value, str), "Invalid setting value")
        result[key] = value
    for key in ("sound_enabled", "key_sound_enabled", "error_sound_enabled", "show_timer", "show_wpm"):
        if key in result:
            _require(result[key] in ("True", "False"), f"Invalid {key}")
    for key, bounds in {
        "font_size": (14, 36), "volume": (0, 100), "daily_goal_wpm": (10, 120),
        "daily_goal_minutes": (1, 120),
    }.items():
        if key in result:
            _require(result[key] is not None, f"Invalid {key}")
            number = int(result[key])
            _require(bounds[0] <= number <= bounds[1], f"Invalid {key}")
    if "theme" in result:
        _require(result["theme"] in ("light", "dark"), "Invalid theme")
    if "keyboard_layout" in result:
        _require(result["keyboard_layout"] == "tr_q", "Unsupported keyboard layout")
    return result


def validate_backup(payload):
    """Return an independent normalized payload before any database writes."""
    data = deepcopy(payload)
    if isinstance(data, list):
        data = {"sessions": data}
    _require(isinstance(data, dict), "Backup must be an object or legacy session list")
    legacy = "format" not in data and "backup_version" not in data
    if not legacy:
        _require(data.get("format") == FORMAT and type(data.get("backup_version")) is int
                 and data["backup_version"] == VERSION, "Unsupported backup format/version")
        _require(type(data.get("schema_version")) is int
                 and data["schema_version"] == _SCHEMA_VERSION, "Unsupported backup schema")
        _timestamp(data.get("created_at"))
        _require(all(table in data for table in TABLES), "Incomplete backup")
    _require("sessions" in data, "Missing sessions")
    for table in TABLES[:-1]:
        _require(isinstance(data.get(table, []), list), f"{table} must be a list")
    settings = _settings(data.get("settings", {}), legacy)
    sessions = []
    occurrences = Counter()
    for index, row in enumerate(data["sessions"], 1):
        _require(isinstance(row, dict), "Invalid session row")
        if legacy:
            _require(all(key in row for key in ("mode", *COUNTERS, "wpm", "accuracy")),
                     "Incomplete legacy session")
            row.setdefault("id", index)
            row.setdefault("text_content", "")
            row.setdefault("mode_detail", "")
            row.setdefault("duration_seconds", 0)
            row.setdefault("raw_wpm", row["wpm"])
            row.setdefault("max_wpm", 0)
            row["started_at"] = row.get("started_at") or row.get("finished_at")
            row["finished_at"] = row.get("finished_at") or row["started_at"]
            row.setdefault("session_uid", "")
        _require(all(key in row for key in (*SESSION_FIELDS, "id")), "Incomplete session")
        item = {key: row[key] for key in SESSION_FIELDS}
        item["id"] = _integer(row["id"], 1)
        for key in ("started_at", "finished_at"):
            _timestamp(item[key])
        for key in ("mode", "text_content"):
            _text(item[key], empty=key != "mode")
        _require(item["mode_detail"] is None or isinstance(item["mode_detail"], str),
                 "Invalid mode detail")
        for key in COUNTERS:
            _integer(item[key])
        _require(item["correct_chars"] + item["incorrect_chars"] == item["total_chars"],
                 "Character totals disagree")
        for key in METRICS:
            item[key] = _number(item[key], 100 if key == "accuracy" else None)
        if legacy and not item["session_uid"]:
            canonical = json.dumps({k: item[k] for k in SESSION_FIELDS if k != "session_uid"},
                                   sort_keys=True, ensure_ascii=False)
            occurrences[canonical] += 1
            item["session_uid"] = sha256(
                (canonical + ":" + str(occurrences[canonical])).encode("utf-8")
            ).hexdigest()[:32]
        else:
            item["session_uid"] = UUID(_text(item["session_uid"], empty=False)).hex
        item["keys"] = []
        sessions.append(item)
    _unique(sessions, "id")
    _unique(sessions, "session_uid")
    by_id = {row["id"]: row for row in sessions}
    keys = data.get("key_stats", [])
    if legacy and not keys:
        for source, target in zip(data["sessions"], sessions, strict=True):
            counts = source.get("key_counts", {})
            _require(isinstance(counts, dict), "Invalid legacy key counts")
            for char, values in counts.items():
                _require(isinstance(values, dict), "Invalid legacy key counts")
                keys.append(dict(session_id=target["id"], key_char=char,
                                 correct_count=values.get("correct", 0),
                                 incorrect_count=values.get("incorrect", 0)))
    for key in keys:
        _require(isinstance(key, dict), "Invalid key statistics")
        sid = _integer(key.get("session_id"), 1)
        _require(sid in by_id, "Orphan key statistics")
        char = _text(key.get("key_char"), empty=False)
        _require(len(char) == 1, "Key must be a single character")
        by_id[sid]["keys"].append(dict(
            key_char=char, correct_count=_integer(key.get("correct_count")),
            incorrect_count=_integer(key.get("incorrect_count")),
        ))
    for session in sessions:
        _unique(session["keys"], "key_char")
        session["keys"].sort(key=lambda row: row["key_char"])
    result = dict(sessions=sessions, settings=settings, legacy=legacy)
    for table, fields in RELATED.items():
        rows = []
        for source in data.get(table, []):
            _require(isinstance(source, dict) and all(k in source for k in fields),
                     f"Incomplete {table} row")
            row = {k: source[k] for k in fields}
            _text(row[fields[0]], empty=False)
            if table == "lesson_progress":
                _timestamp(row["completed_at"])
                _number(row["best_wpm"])
                _number(row["best_accuracy"], 100)
                _integer(row["attempts"], 1)
            elif table == "achievements":
                _timestamp(row["unlocked_at"])
            else:
                _require(date.fromisoformat(row["date"]).isoformat() == row["date"],
                         "Invalid streak date")
                _require(type(row["practiced"]) is int and row["practiced"] in (0, 1),
                         "Invalid practiced flag")
            rows.append(row)
        _unique(rows, fields[0])
        result[table] = rows
    if legacy and "streak" not in data:
        result["streak"] = [
            {"date": day, "practiced": 1}
            for day in sorted({datetime.fromisoformat(s["finished_at"]).date().isoformat()
                               for s in sessions if s["total_chars"] > 0})
        ]
    return result


class BackupService:
    def __init__(self, db):
        self.db = db

    def snapshot(self):
        with self.db.transaction():
            data = {table: [dict(row) for row in self.db.query(f"SELECT * FROM {table}")]
                    for table in TABLES}
        data["settings"] = {row["key"]: row["value"] for row in data["settings"]}
        data.update(format=FORMAT, backup_version=VERSION, schema_version=_SCHEMA_VERSION,
                    created_at=datetime.now().isoformat(timespec="seconds"))
        validate_backup(data)
        return data

    def export_file(self, path):
        """Replace destination only after a complete, flushed temporary file."""
        path = Path(path)
        data = self.snapshot()
        temporary = None
        try:
            with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=path.parent,
                                             prefix=path.name + ".", suffix=".tmp",
                                             delete=False) as stream:
                temporary = Path(stream.name)
                json.dump(data, stream, ensure_ascii=False, indent=2, allow_nan=False)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, path)
        finally:
            if temporary is not None:
                temporary.unlink(missing_ok=True)

    def import_file(self, path):
        with open(path, encoding="utf-8-sig") as stream:
            data = json.load(stream)
        return self.restore(data)

    def _keys(self, session_id):
        return [dict(row) for row in self.db.query(
            "SELECT key_char, correct_count, incorrect_count FROM key_stats "
            "WHERE session_id = ? ORDER BY key_char", (session_id,))]

    def restore(self, payload):
        data = validate_backup(payload)
        inserted = 0
        matched = set()
        with self.db.transaction():
            for row in data["sessions"]:
                existing = self.db.query_one(
                    "SELECT * FROM sessions WHERE session_uid = ?", (row["session_uid"],))
                if existing is not None:
                    _require(all(existing[k] == row[k] for k in SESSION_FIELDS)
                             and self._keys(existing["id"]) == row["keys"],
                             "Session identity conflicts with existing data")
                elif data["legacy"]:
                    # Old backups lack stable identity; match exact metrics once per row.
                    candidates = self.db.query(
                        "SELECT * FROM sessions WHERE started_at = ? AND finished_at = ?",
                        (row["started_at"], row["finished_at"]))
                    existing = next((candidate for candidate in candidates
                                     if candidate["id"] not in matched
                                     and all(candidate[k] == row[k] for k in SESSION_FIELDS
                                             if k != "session_uid")
                                     and (not row["keys"] or self._keys(candidate["id"]) == row["keys"])),
                                    None)
                if existing is None:
                    columns = ", ".join(SESSION_FIELDS)
                    marks = ", ".join("?" for _ in SESSION_FIELDS)
                    cursor = self.db.execute(
                        f"INSERT INTO sessions ({columns}) VALUES ({marks})",
                        tuple(row[k] for k in SESSION_FIELDS))
                    sid = cursor.lastrowid
                    for key in row["keys"]:
                        self.db.execute(
                            "INSERT INTO key_stats "
                            "(session_id, key_char, correct_count, incorrect_count) VALUES (?, ?, ?, ?)",
                            (sid, key["key_char"], key["correct_count"], key["incorrect_count"]))
                    inserted += 1
                else:
                    sid = existing["id"]
                matched.add(sid)
            for row in data["lesson_progress"]:
                self.db.execute("""
                    INSERT INTO lesson_progress VALUES (?, ?, ?, ?, ?)
                    ON CONFLICT(lesson_id) DO UPDATE SET
                    completed_at = MAX(completed_at, excluded.completed_at),
                    best_wpm = MAX(best_wpm, excluded.best_wpm),
                    best_accuracy = MAX(best_accuracy, excluded.best_accuracy),
                    attempts = MAX(attempts, excluded.attempts)
                """, tuple(row[k] for k in RELATED["lesson_progress"]))
            for row in data["achievements"]:
                self.db.execute("""
                    INSERT INTO achievements VALUES (?, ?)
                    ON CONFLICT(code) DO UPDATE SET unlocked_at = MIN(unlocked_at, excluded.unlocked_at)
                """, (row["code"], row["unlocked_at"]))
            for row in data["streak"]:
                self.db.execute("""
                    INSERT INTO streak VALUES (?, ?)
                    ON CONFLICT(date) DO UPDATE SET practiced = MAX(practiced, excluded.practiced)
                """, (row["date"], row["practiced"]))
            for key, value in data["settings"].items():
                self.db.execute("INSERT INTO settings VALUES (?, ?) "
                                "ON CONFLICT(key) DO UPDATE SET value = excluded.value", (key, value))
        return inserted

    def reset(self):
        with self.db.transaction():
            for table in ("key_stats", "sessions", "lesson_progress", "achievements", "streak", "settings"):
                self.db.execute(f"DELETE FROM {table}")

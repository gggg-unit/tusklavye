"""SQLite database connection and schema management.

Uses a simple singleton with a ``reset()`` classmethod so tests can swap in a
fresh temp-file database without the ``Database.__new__(Database)`` hack.
"""
from __future__ import annotations

import logging
import sqlite3
import threading
from pathlib import Path
from typing import Optional, Callable, List, Tuple

from ..config import DB_PATH

logger = logging.getLogger(__name__)

_SCHEMA = """
CREATE TABLE IF NOT EXISTS sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    started_at TEXT NOT NULL,
    finished_at TEXT NOT NULL,
    duration_seconds REAL NOT NULL,
    mode TEXT NOT NULL,
    mode_detail TEXT,
    text_content TEXT NOT NULL,
    total_chars INTEGER NOT NULL,
    correct_chars INTEGER NOT NULL,
    incorrect_chars INTEGER NOT NULL,
    wpm REAL NOT NULL,
    raw_wpm REAL NOT NULL,
    accuracy REAL NOT NULL,
    max_wpm REAL NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS key_stats (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER NOT NULL,
    key_char TEXT NOT NULL,
    correct_count INTEGER NOT NULL DEFAULT 0,
    incorrect_count INTEGER NOT NULL DEFAULT 0,
    FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS lesson_progress (
    lesson_id TEXT PRIMARY KEY,
    completed_at TEXT NOT NULL,
    best_wpm REAL NOT NULL,
    best_accuracy REAL NOT NULL,
    attempts INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS achievements (
    code TEXT PRIMARY KEY,
    unlocked_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    value TEXT
);

CREATE TABLE IF NOT EXISTS streak (
    date TEXT PRIMARY KEY,
    practiced INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS schema_version (
    version INTEGER PRIMARY KEY
);

CREATE INDEX IF NOT EXISTS idx_sessions_finished_at ON sessions(finished_at);
CREATE INDEX IF NOT EXISTS idx_sessions_mode ON sessions(mode);
CREATE INDEX IF NOT EXISTS idx_key_stats_session_id ON key_stats(session_id);
CREATE INDEX IF NOT EXISTS idx_key_stats_key_char ON key_stats(key_char);
"""

_SCHEMA_VERSION = 2

_MIGRATIONS: List[Tuple[int, Callable[[sqlite3.Connection], None]]] = []


def migration(version: int):
    """Decorator to register a migration for a given schema version."""
    def decorator(func: Callable[[sqlite3.Connection], None]):
        _MIGRATIONS.append((version, func))
        return func
    return decorator


@migration(2)
def _migrate_v2(conn: sqlite3.Connection):
    """v2: ensure max_wpm column exists (added in v1 schema but guards old DBs)."""
    cols = {row[1] for row in conn.execute("PRAGMA table_info(sessions)").fetchall()}
    if "max_wpm" not in cols:
        conn.execute("ALTER TABLE sessions ADD COLUMN max_wpm REAL NOT NULL DEFAULT 0")


class Database:
    """Singleton SQLite wrapper with thread-locked access."""

    _instance: Optional["Database"] = None

    def __init__(self, path: Path = DB_PATH):
        self.path = path
        self._lock = threading.Lock()
        path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(str(path), check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys = ON;")
        self.conn.execute("PRAGMA journal_mode = WAL;")
        self._init_schema()

    def _init_schema(self):
        self.conn.executescript(_SCHEMA)
        self._run_migrations()
        self.conn.commit()

    def _run_migrations(self):
        row = self.conn.execute(
            "SELECT version FROM schema_version ORDER BY version DESC LIMIT 1"
        ).fetchone()
        current = row["version"] if row else 0
        if current < _SCHEMA_VERSION:
            self._apply_migrations(current)
            self.conn.execute(
                "INSERT OR REPLACE INTO schema_version (version) VALUES (?)",
                (_SCHEMA_VERSION,),
            )
            logger.info(f"Database migrated from v{current} to v{_SCHEMA_VERSION}")

    def _apply_migrations(self, from_version: int):
        """Apply registered migrations from ``from_version`` up to ``_SCHEMA_VERSION``."""
        for version, func in sorted(_MIGRATIONS, key=lambda x: x[0]):
            if from_version < version <= _SCHEMA_VERSION:
                logger.debug(f"Applying migration v{version}")
                func(self.conn)

    @classmethod
    def get(cls) -> "Database":
        if cls._instance is None:
            cls._instance = Database()
        return cls._instance

    @classmethod
    def reset(cls, path: Optional[Path] = None) -> "Database":
        """Replace the singleton with a fresh database at ``path`` (for tests)."""
        if cls._instance is not None:
            try:
                cls._instance.close()
            except Exception:
                pass
        cls._instance = Database(path) if path else Database()
        return cls._instance

    def execute(self, sql: str, params: tuple = ()) -> sqlite3.Cursor:
        with self._lock:
            cur = self.conn.execute(sql, params)
            self.conn.commit()
            return cur

    def execute_no_commit(self, sql: str, params: tuple = ()) -> sqlite3.Cursor:
        with self._lock:
            return self.conn.execute(sql, params)

    def executemany_no_commit(self, sql: str, params: list) -> sqlite3.Cursor:
        with self._lock:
            return self.conn.executemany(sql, params)

    def commit(self):
        with self._lock:
            self.conn.commit()

    def query(self, sql: str, params: tuple = ()) -> list:
        with self._lock:
            return self.conn.execute(sql, params).fetchall()

    def query_one(self, sql: str, params: tuple = ()):
        with self._lock:
            return self.conn.execute(sql, params).fetchone()

    def close(self):
        with self._lock:
            if self.conn is not None:
                self.conn.close()
                self.conn = None
        Database._instance = None

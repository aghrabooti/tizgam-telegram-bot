"""لایه‌ی ذخیره‌سازی (SQLite)
============================

دو کاربرد:
- آمار ربات (کاربران + رویدادها)
- مقادیر ویرایش‌شده‌ی محتوا توسط مدیر (content overrides)

از sqlite3 استاندارد استفاده می‌شود (بدون وابستگی جدید). چون حجم نوشتن
کم است، یک اتصال با قفل thread-safe کفایت می‌کند.
"""

from __future__ import annotations

import sqlite3
import threading
from pathlib import Path
from typing import Any, Iterable, Optional

_SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    user_id    INTEGER PRIMARY KEY,
    first_name TEXT,
    username   TEXT,
    joined_at  TEXT,
    last_seen  TEXT
);

CREATE TABLE IF NOT EXISTS events (
    id      INTEGER PRIMARY KEY AUTOINCREMENT,
    ts      TEXT NOT NULL,
    user_id INTEGER,
    type    TEXT NOT NULL,
    name    TEXT NOT NULL DEFAULT ''
);

CREATE INDEX IF NOT EXISTS idx_events_type_name ON events (type, name);
CREATE INDEX IF NOT EXISTS idx_events_ts        ON events (ts);

CREATE TABLE IF NOT EXISTS content_overrides (
    key        TEXT PRIMARY KEY,
    value      TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
"""


class Database:
    """پوشش کوچک و thread-safe روی sqlite3."""

    def __init__(self, path: str) -> None:
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._lock = threading.Lock()
        with self._lock:
            self._conn.execute("PRAGMA journal_mode=WAL")
            self._conn.executescript(_SCHEMA)
            self._conn.commit()

    def execute(self, sql: str, params: Iterable[Any] = ()) -> None:
        """اجرای یک دستور نوشتنی (INSERT/UPDATE/DELETE) با commit."""
        with self._lock:
            self._conn.execute(sql, tuple(params))
            self._conn.commit()

    def query_all(self, sql: str, params: Iterable[Any] = ()) -> list[sqlite3.Row]:
        with self._lock:
            return self._conn.execute(sql, tuple(params)).fetchall()

    def query_one(
        self, sql: str, params: Iterable[Any] = ()
    ) -> Optional[sqlite3.Row]:
        with self._lock:
            return self._conn.execute(sql, tuple(params)).fetchone()

    def close(self) -> None:
        with self._lock:
            self._conn.close()


# ---------------------------------------------------------------------------
# نمونه‌ی سراسری (توسط init_db مقداردهی می‌شود)
# ---------------------------------------------------------------------------

_db: Optional[Database] = None


def init_db(path: str) -> Database:
    """باز کردن (یا تعویض) دیتابیس؛ در create_application صدا زده می‌شود."""
    global _db
    if _db is not None:
        _db.close()
    _db = Database(path)
    return _db


def get_db() -> Database:
    """دسترسی به دیتابیس جاری."""
    if _db is None:
        raise RuntimeError(
            "دیتابیس مقداردهی نشده است؛ ابتدا init_db() (در create_application)"
            " باید صدا زده شود."
        )
    return _db


def close_db() -> None:
    global _db
    if _db is not None:
        _db.close()
        _db = None

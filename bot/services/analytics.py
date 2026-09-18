"""آمارگیری ربات (Analytics)
============================

رویدادهای ثبت‌شده:
- ``start``  → هر بار اجرای /start
- ``screen`` → هر بار باز شدن یک صفحه با دکمه‌ی inline (نام = callback data)

نکته‌ی مهم: تلگرام «کلیک روی دکمه‌های URL» (لینک خارجی) را به ربات گزارش
نمی‌دهد؛ معنای عملی «باز شدن لینک ویدیو/سایت» همین تعداد نمایش صفحه‌ی
محتوی آن لینک است. برای شمارش دقیق کلیک باید لینک‌ها از طریق یک سرویس
ریدایرکت (مثلاً tizgam.ir/r/…) عبور داده شوند.

نکته‌ی معماری: همه‌ی «نوشتن‌ها» غیرمهلک هستند؛ یعنی اگر دیتابیس دچار
مشکل شود، هیچ‌وقت ناوبری و تجربه‌ی کاربر خراب نمی‌شود و فقط در لاگ
خطا ثبت می‌شود.
"""

from __future__ import annotations

import csv
import io
import logging
from datetime import datetime
from typing import Optional

from telegram import User

from bot.config import content
from bot.services.database import get_db

logger = logging.getLogger(__name__)


def _now() -> str:
    """زمان محلی سرور به‌صورت ISO (ثانیه‌دقیق)."""
    return datetime.now().isoformat(timespec="seconds")


def _today() -> str:
    return datetime.now().date().isoformat()


def _log_event(user_id: int, event_type: str, name: str = "") -> None:
    get_db().execute(
        "INSERT INTO events (ts, user_id, type, name) VALUES (?, ?, ?, ?)",
        (_now(), user_id, event_type, name),
    )


def upsert_user(user: User) -> None:
    """ثبت/به‌روزرسانی کاربر (نام و آخرین بازدید) — غیرمهلک."""
    try:
        get_db().execute(
            """
            INSERT INTO users (user_id, first_name, username, joined_at, last_seen)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                first_name = excluded.first_name,
                username   = excluded.username,
                last_seen  = excluded.last_seen
            """,
            (user.id, user.first_name, user.username, _now(), _now()),
        )
    except Exception:  # noqa: BLE001
        logger.exception("ثبت/به‌روزرسانی کاربر ناموفق بود")


def log_start(user_id: int) -> None:
    """ثبت رویداد /start — غیرمهلک."""
    try:
        _log_event(user_id, "start")
    except Exception:  # noqa: BLE001
        logger.exception("ثبت رویداد start ناموفق بود")


def log_screen(user_id: int, name: str) -> None:
    """ثبت نمایش یک صفحه (ناوبری با دکمه‌ی inline) — غیرمهلک."""
    try:
        _log_event(user_id, "screen", name)
        get_db().execute(
            "UPDATE users SET last_seen = ? WHERE user_id = ?", (_now(), user_id)
        )
    except Exception:  # noqa: BLE001
        logger.exception("ثبت رویداد نمایش صفحه ناموفق بود")


def summary() -> dict[str, int]:
    """خلاصه‌ی آمار برای پنل مدیریت."""
    db = get_db()

    def one(sql: str, params: tuple = ()) -> int:
        row = db.query_one(sql, params)
        return int(row[0]) if row and row[0] is not None else 0

    return {
        "users_total": one("SELECT COUNT(*) FROM users"),
        "users_today": one(
            "SELECT COUNT(*) FROM users WHERE joined_at >= ?", (_today(),)
        ),
        "starts_total": one("SELECT COUNT(*) FROM events WHERE type = 'start'"),
        "starts_today": one(
            "SELECT COUNT(*) FROM events WHERE type = 'start' AND ts >= ?",
            (_today(),),
        ),
        "views_total": one("SELECT COUNT(*) FROM events WHERE type = 'screen'"),
        "views_today": one(
            "SELECT COUNT(*) FROM events WHERE type = 'screen' AND ts >= ?",
            (_today(),),
        ),
    }


def top_screens(limit: int = 8) -> list[tuple[str, int]]:
    """پربازدیدترین صفحه‌ها به‌صورت (callback_name, تعداد)."""
    rows = get_db().query_all(
        """
        SELECT name, COUNT(*) AS c
        FROM events
        WHERE type = 'screen'
        GROUP BY name
        ORDER BY c DESC, name
        LIMIT ?
        """,
        (limit,),
    )
    return [(row["name"], int(row["c"])) for row in rows]


def reset_all() -> None:
    """پاک کردن کامل آمار (کاربران و رویدادها)."""
    get_db().execute("DELETE FROM events")
    get_db().execute("DELETE FROM users")


def screen_titles() -> dict[str, str]:
    """عنوان فارسی هر صفحه (بر اساس محتوای جاری؛ تغییرات مدیر را هم می‌گیرد)."""
    titles: dict[str, str] = {"main": "منوی اصلی"}
    for item in content.MAIN_MENU:
        titles.setdefault(item.callback, item.label)
    titles.update(
        {
            "sup": "پشتیبانی",
            "sup:call": "پشتیبانی — تماس",
            "sup:tg": "پشتیبانی — تلگرام",
        }
    )
    for grade in content.GRADES:
        titles[f"prod:g:{grade.id}"] = f"محصولات {grade.title}"
        titles[f"cls:g:{grade.id}"] = f"درس‌های {grade.title}"
        titles[f"exm:g:{grade.id}"] = f"آزمون‌های {grade.title}"
        for subject in grade.subjects:
            titles[f"cls:g:{grade.id}:{subject.id}"] = (
                f"نمونه کلاس {subject.title} ({grade.title})"
            )
    for grade_id, products in content.PRODUCTS_BY_GRADE.items():
        for product in products:
            titles[f"prod:g:{grade_id}:{product.id}"] = f"محصول «{product.title}»"
    for grade_id, exams in content.EXAMS_BY_GRADE.items():
        for exam in exams:
            titles[f"exm:g:{grade_id}:{exam.id}"] = f"آزمون «{exam.title}»"
    return titles


def user_count() -> int:
    row = get_db().query_one("SELECT COUNT(*) FROM users")
    return int(row[0]) if row else 0


def find_user(user_id: int) -> Optional[dict]:
    row = get_db().query_one("SELECT * FROM users WHERE user_id = ?", (user_id,))
    return dict(row) if row else None


# ---------------------------------------------------------------------------
# شماره‌ی تماس کاربران
# ---------------------------------------------------------------------------


def needs_phone(user_id: int) -> bool:
    """آیا این کاربر باید شماره‌ی تماس بدهد؟ (ثبت‌شده ولی بدون شماره و رد نکرده)"""
    row = get_db().query_one(
        "SELECT phone, phone_skipped_at FROM users WHERE user_id = ?", (user_id,)
    )
    return row is not None and row["phone"] is None and row["phone_skipped_at"] is None


def set_phone(user_id: int, phone: str, source: str) -> None:
    """ذخیره‌ی شماره‌ی تماس کاربر — غیرمهلک."""
    try:
        get_db().execute(
            "UPDATE users SET phone = ?, phone_source = ? WHERE user_id = ?",
            (phone, source, user_id),
        )
    except Exception:  # noqa: BLE001
        logger.exception("ثبت شماره تماس ناموفق بود")


def set_phone_skipped(user_id: int) -> None:
    """ثبت اینکه کاربر دادن شماره را رد کرد (دیگر پرسیده نمی‌شود)."""
    try:
        get_db().execute(
            "UPDATE users SET phone_skipped_at = ? WHERE user_id = ?",
            (_now(), user_id),
        )
    except Exception:  # noqa: BLE001
        logger.exception("ثبت رد کردن شماره ناموفق بود")


def users_with_phone_count() -> int:
    """تعداد کاربرانی که شماره تماس داده‌اند."""
    row = get_db().query_one("SELECT COUNT(*) FROM users WHERE phone IS NOT NULL")
    return int(row[0]) if row else 0


def recent_users(limit: int = 10) -> list[dict]:
    """آخرین کاربران (جدیدترین اول)."""
    rows = get_db().query_all(
        """
        SELECT user_id, first_name, username, phone, joined_at
        FROM users ORDER BY joined_at DESC, user_id DESC LIMIT ?
        """,
        (limit,),
    )
    return [dict(r) for r in rows]


def users_csv() -> str:
    """خروجی CSV کامل کاربران (سازگار با Excel فارسی)."""
    rows = get_db().query_all(
        """
        SELECT user_id, first_name, username, phone, phone_source,
               phone_skipped_at, joined_at, last_seen
        FROM users ORDER BY joined_at DESC, user_id DESC
        """
    )
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(
        ["user_id", "first_name", "username", "phone", "phone_source",
         "phone_skipped_at", "joined_at", "last_seen"]
    )
    for r in rows:
        writer.writerow([r[k] if r[k] is not None else "" for k in r.keys()])
    return buf.getvalue()

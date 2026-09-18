"""تست‌های جمع‌آوری شماره تماس + فایل لاگ + لیست کاربران ادمین."""

from __future__ import annotations

import logging
import sqlite3

from bot.config import content
from bot.services import analytics
from bot.services.database import Database
from bot.utils.logging_setup import setup_logging
from bot.utils.phone import normalize_phone
from tests.helpers import (
    USER,
    last_send,
    send_command,
    send_text,
    share_contact,
    tap,
)

# ---------------------------------------------------------------------------
# نرمال‌سازی شماره
# ---------------------------------------------------------------------------


def test_normalize_phone_variants():
    assert normalize_phone("09123456789") == "+989123456789"
    assert normalize_phone("+98 912 345 6789") == "+989123456789"
    assert normalize_phone("۰۹۱۲ ۳۴۵ ۶۷۸۹") == "+989123456789"  # ارقام فارسی
    assert normalize_phone("989123456789") == "+989123456789"
    assert normalize_phone("9123456789") == "+989123456789"
    assert normalize_phone("02112345678") is None  # شماره‌ی ثابت
    assert normalize_phone("سلام") is None
    assert normalize_phone("12345") is None


# ---------------------------------------------------------------------------
# جریان شماره تماس
# ---------------------------------------------------------------------------


async def test_phone_flow_contact(bot_app):
    """/start → درخواست شماره → اشتراک مخاطب → ذخیره + منو."""
    app, bot = bot_app
    await send_command(app, bot, "/start")
    await share_contact(app, bot)

    user = analytics.find_user(USER.id)
    assert user["phone"] == "+989121234567"
    assert user["phone_source"] == "contact"

    # /start بعدی → مستقیم منو (بدون درخواست شماره)
    await send_command(app, bot, "/start")
    assert last_send(bot)["text"] == content.WELCOME_TEXT


async def test_phone_flow_manual_persian_digits(bot_app):
    """/start → تایپ دستی شماره با ارقام فارسی → ذخیره."""
    app, bot = bot_app
    await send_command(app, bot, "/start")
    await send_text(app, bot, "۰۹۳۵ ۱۲۳ ۴۵۶۷")

    user = analytics.find_user(USER.id)
    assert user["phone"] == "+989351234567"
    assert user["phone_source"] == "manual"
    assert "ثبت شد" in last_send(bot)["text"] or "منوی" in last_send(bot)["text"]


async def test_phone_flow_later_is_remembered(bot_app):
    """/start → «بعداً» → منو؛ و دیگر پرسیده نمی‌شود."""
    app, bot = bot_app
    await send_command(app, bot, "/start")
    await send_text(app, bot, content.LBL_PHONE_LATER)

    assert "منوی اصلی" in last_send(bot)["text"] or content.WELCOME_TEXT in last_send(bot)["text"]

    await send_command(app, bot, "/start")
    assert last_send(bot)["text"] == content.WELCOME_TEXT  # بدون درخواست مجدد

    user = analytics.find_user(USER.id)
    assert user["phone"] is None
    assert user["phone_skipped_at"] is not None


async def test_unrelated_text_while_phone_pending_falls_back(bot_app):
    """متن نامرتبط در انتظار شماره → همان fallback منوی اصلی."""
    app, bot = bot_app
    await send_command(app, bot, "/start")
    await send_text(app, bot, "سلام این شماره نیست")

    assert content.FALLBACK_TEXT in last_send(bot)["text"]


async def test_needs_phone_false_for_unknown_user(bot_app):
    """کاربری که هرگز /start نزده، در جریان شماره نیست."""
    assert analytics.needs_phone(USER.id) is False


# ---------------------------------------------------------------------------
# لیست کاربران و CSV در پنل ادمین
# ---------------------------------------------------------------------------


async def test_admin_users_screen_and_csv(bot_app):
    app, bot = bot_app
    # یک کاربر با شماره و یک کاربر بدون شماره
    await send_command(app, bot, "/start")
    await share_contact(app, bot, phone="+989121112233")

    from tests.helpers import NON_ADMIN
    from tests.helpers import send_command as sc

    await sc(app, bot, "/start", user=NON_ADMIN)  # کاربر دوم (شماره نمی‌دهد)

    # منوی ادمین → دکمه‌ی کاربران
    await tap(app, bot, "adm")
    await tap(app, bot, "adm:users")

    screen = bot.edit_message_text.await_args.kwargs
    assert "کاربران و شماره‌های تماس" in screen["text"]
    assert "+989121112233" in screen["text"]
    assert "Tester" in screen["text"]

    # دریافت CSV
    await tap(app, bot, "adm:users:csv")
    assert bot.send_document.await_count == 1
    doc_kwargs = bot.send_document.await_args.kwargs
    assert doc_kwargs["filename"] == "tizgam-users.csv"

    # محتوای CSV: هدر + دو کاربر (با BOM برای Excel)
    csv_text = doc_kwargs["document"].getvalue().decode("utf-8-sig")
    assert csv_text.startswith("user_id,first_name,username,phone")
    assert "+989121112233" in csv_text
    assert "888" in csv_text  # کاربر دوم


# ---------------------------------------------------------------------------
# مهاجرت دیتابیس قدیمی و فایل لاگ
# ---------------------------------------------------------------------------


def test_migration_adds_phone_columns(tmp_path):
    """دیتابیس با اسکیمای قدیمی → ستون‌های شماره خودکار اضافه می‌شوند."""
    db_path = tmp_path / "old.db"
    conn = sqlite3.connect(db_path)
    conn.execute(
        """CREATE TABLE users (
            user_id INTEGER PRIMARY KEY, first_name TEXT, username TEXT,
            joined_at TEXT, last_seen TEXT
        )"""
    )
    conn.execute("INSERT INTO users (user_id, first_name) VALUES (1, 'قدیمی')")
    conn.commit()
    conn.close()

    db = Database(str(db_path))
    columns = {row["name"] for row in db.query_all("PRAGMA table_info(users)")}
    assert {"phone", "phone_source", "phone_skipped_at"} <= columns

    # داده‌ی قبلی سالم است و قابل به‌روزرسانی
    db.execute("UPDATE users SET phone = '+989120000000' WHERE user_id = 1")
    row = db.query_one("SELECT phone FROM users WHERE user_id = 1")
    assert row["phone"] == "+989120000000"
    db.close()


def test_setup_logging_writes_file(tmp_path):
    """لاگ روی فایل با محتوای فارسی نوشته می‌شود."""
    log_file = tmp_path / "logs" / "bot.log"
    setup_logging(level="INFO", log_file=str(log_file))

    logging.getLogger("tizgam-test").info("سلام، این یک لاگ آزمایشی است")
    for handler in logging.getLogger().handlers:
        handler.flush()

    assert log_file.exists()
    assert "سلام، این یک لاگ آزمایشی است" in log_file.read_text(encoding="utf-8")

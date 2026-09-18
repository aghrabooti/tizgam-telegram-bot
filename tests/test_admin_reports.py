"""تست‌های گزارش‌های پنل مدیریت: لاگ‌ها، دیتابیس و دسترسی‌ها.

پوشش:
- منوی ادمین شامل دکمه‌های کاربران/لاگ‌ها/دیتابیس است (رگرشن v8: دکمه‌ی
  کاربران جا افتاده بود).
- صفحه‌ی لاگ‌ها: دم‌کردن انتهای فایل + دانلود فایل کامل.
- صفحه‌ی دیتابیس: وضعیت + دریافت پشتیبان سالم SQLite.
- کاربر غیرمدیر به هیچ‌کدام از گزارش‌ها دسترسی ندارد.
"""

from __future__ import annotations

import sqlite3

from tests.helpers import NON_ADMIN, tap
from tests.helpers import send_command as send_cmd


async def test_admin_menu_has_report_buttons(bot_app):
    """منوی پنل باید به همه‌ی گزارش‌ها دکمه داشته باشد."""
    app, bot = bot_app
    await tap(app, bot, "adm")
    markup = bot.edit_message_text.await_args.kwargs["reply_markup"]
    labels = [b.text for row in markup.inline_keyboard for b in row]
    assert "📊 آمار و گزارش‌ها" in labels
    assert "👥 کاربران و شماره‌ها" in labels
    assert "📋 لاگ‌ها" in labels
    assert "💾 دیتابیس و پشتیبان" in labels


async def test_logs_screen_shows_tail(bot_app, monkeypatch, tmp_path):
    """صفحه‌ی لاگ‌ها: آخرین خطوط فایل + حجم، به‌روزرسانی هم کار می‌کند."""
    app, bot = bot_app
    log_file = tmp_path / "bot.log"
    log_file.write_text(
        "2026-09-19 10:12:03 | INFO | راه‌اندازی ربات\n"
        "2026-09-19 10:14:41 | INFO | ثبت شماره تماس جدید\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("LOG_FILE", str(log_file))

    await tap(app, bot, "adm:logs")
    screen = bot.edit_message_text.await_args.kwargs
    assert "گزارش لاگ ربات" in screen["text"]
    assert "ثبت شماره تماس جدید" in screen["text"]

    # دکمه‌ی به‌روزرسانی همان صفحه را دوباره می‌سازد
    await tap(app, bot, "adm:logs")
    assert bot.edit_message_text.await_count >= 2


async def test_log_file_download(bot_app, monkeypatch, tmp_path):
    """دریافت فایل کامل لاگ به‌صورت سند."""
    app, bot = bot_app
    log_file = tmp_path / "bot.log"
    log_file.write_text("خط تست دانلود لاگ\n", encoding="utf-8")
    monkeypatch.setenv("LOG_FILE", str(log_file))

    await tap(app, bot, "adm:logs:file")
    assert bot.send_document.await_count == 1
    kwargs = bot.send_document.await_args.kwargs
    assert kwargs["filename"] == "tizgam-bot.log"
    assert "خط تست دانلود لاگ".encode() in kwargs["document"].getvalue()


async def test_logs_screen_when_no_log_file(bot_app, monkeypatch, tmp_path):
    """فایل لاگ وجود ندارد → صفحه بدون کرش + هشدار به‌جای دانلود."""
    app, bot = bot_app
    monkeypatch.setenv("LOG_FILE", str(tmp_path / "missing.log"))

    await tap(app, bot, "adm:logs")
    text = bot.edit_message_text.await_args.kwargs["text"]
    assert "خالی است یا هنوز ساخته نشده" in text

    await tap(app, bot, "adm:logs:file")
    assert not bot.send_document.called


async def test_db_screen_and_backup(bot_app, monkeypatch, tmp_path):
    """صفحه‌ی دیتابیس + پشتیبان سالم SQLite با داده‌ی واقعی."""
    app, bot = bot_app
    await send_cmd(app, bot, "/start")  # حداقل یک کاربر واقعی

    await tap(app, bot, "adm:db")
    screen = bot.edit_message_text.await_args.kwargs
    assert "دیتابیس و پشتیبان" in screen["text"]

    await tap(app, bot, "adm:db:file")
    assert bot.send_document.await_count == 1
    kwargs = bot.send_document.await_args.kwargs
    assert kwargs["filename"].startswith("tizgam-backup-")
    assert kwargs["filename"].endswith(".db")

    data = kwargs["document"].getvalue()
    assert data.startswith(b"SQLite format 3\x00")

    # پشتیبان واقعاً قابل بازیابی است: جدول users با داده‌ی زنده
    backup_path = tmp_path / "restore.db"
    backup_path.write_bytes(data)
    conn = sqlite3.connect(backup_path)
    users = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    conn.close()
    assert users >= 1


async def test_reports_denied_for_non_admin(bot_app, monkeypatch, tmp_path):
    """کاربر غیرمدیر به گزارش‌ها دسترسی ندارد و فایلی نمی‌گیرد."""
    app, bot = bot_app
    monkeypatch.setenv("LOG_FILE", str(tmp_path / "bot.log"))
    (tmp_path / "bot.log").write_text("x\n", encoding="utf-8")

    for cb in ("adm:logs", "adm:logs:file", "adm:db", "adm:db:file"):
        await tap(app, bot, cb, user=NON_ADMIN)

    assert not bot.edit_message_text.called
    assert not bot.send_document.called


def test_read_log_tail_edge_cases(tmp_path):
    """فایل غایب → لیست خالی؛ فایل بزرگ → فقط آخرین خطوط."""
    from bot.handlers.admin import LOG_TAIL_LINES, _read_log_tail

    assert _read_log_tail(tmp_path / "nope.log") == []

    big = tmp_path / "big.log"
    big.write_text(
        "\n".join(f"line-{i}" for i in range(LOG_TAIL_LINES * 4)), encoding="utf-8"
    )
    tail = _read_log_tail(big)
    assert len(tail) == LOG_TAIL_LINES
    assert tail[-1] == f"line-{LOG_TAIL_LINES * 4 - 1}"

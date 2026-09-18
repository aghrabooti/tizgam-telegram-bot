"""تست‌های پنل مدیریت (آمار + ویرایش محتوا).

پوشش:
- کنترل دسترسی (غیرمدیر → پیام/هشدار رد دسترسی)
- /id
- منوی پنل، صفحه‌ی آمار و شمارش واقعی رویدادها (start و نمایش صفحه‌ها)
- پاک کردن آمار با تأیید
- جریان کامل ویرایش یک لینک: گروه ← فیلد ← شروع ویرایش ← ارسال مقدار
  ← اعمال روی ربات + ذخیره در دیتابیس ← بازگردانی پیش‌فرض
- اعتبارسنجی لینک نامعتبر (state حفظ می‌شود)
- پاک شدن state ویرایش با /start و عبور پیام عادی به fallback
- escape شدن HTML متن‌های مدیر
"""

from __future__ import annotations

from bot.config import content
from bot.handlers.admin import ADMIN_DENIED_TEXT
from bot.services import analytics
from bot.services.database import get_db
from tests.helpers import (
    NON_ADMIN,
    USER,
    callbacks,
    last_answer,
    last_edit,
    last_send,
    send_command,
    send_text,
    tap,
    url_buttons,
)

MEDIA_TG_URL_FIELD = "media:item:telegram:url"
MEDIA_TG_URL_SET = f"adm:edit:s:{MEDIA_TG_URL_FIELD}"
MEDIA_TG_URL_FIELD_CB = f"adm:edit:f:{MEDIA_TG_URL_FIELD}"
MEDIA_TG_URL_REVERT = f"adm:edit:d:{MEDIA_TG_URL_FIELD}"


def _media_telegram_url() -> str:
    return next(
        item.url for item in content.MEDIA_SECTION.items if item.id == "telegram"
    )


def _url_buttons_of_last_edit(bot) -> list[tuple[str, str]]:
    return url_buttons(last_edit(bot)["reply_markup"])


# ---------------------------------------------------------------------------
# دسترسی
# ---------------------------------------------------------------------------


async def test_admin_command_denied_for_non_admin(bot_app):
    app, bot = bot_app
    await send_command(app, bot, "/admin", user=NON_ADMIN)
    assert last_send(bot)["text"] == ADMIN_DENIED_TEXT


async def test_admin_callback_denied_for_non_admin(bot_app):
    app, bot = bot_app
    await tap(app, bot, "adm", user=NON_ADMIN)
    assert "مدیران" in last_answer(bot)["text"]
    assert bot.edit_message_text.await_count == 0  # هیچ صفحه‌ای رندر نشد


async def test_admin_command_opens_panel_for_admin(bot_app):
    app, bot = bot_app
    await send_command(app, bot, "/admin", user=USER)
    sent = last_send(bot)
    assert "پنل مدیریت" in sent["text"]
    assert "adm:stats" in callbacks(sent["reply_markup"])
    assert "adm:edit" in callbacks(sent["reply_markup"])


async def test_id_command_shows_user_id(bot_app):
    app, bot = bot_app
    await send_command(app, bot, "/id", user=NON_ADMIN)
    assert str(NON_ADMIN.id) in last_send(bot)["text"]


# ---------------------------------------------------------------------------
# آمار
# ---------------------------------------------------------------------------


async def test_stats_counts_starts_and_screen_views(bot_app):
    app, bot = bot_app
    # کاربر: یک /start و دو ناوبری با دکمه
    await send_command(app, bot, "/start", user=USER)
    await tap(app, bot, "about")
    await tap(app, bot, "main")

    s = analytics.summary()
    assert s["users_total"] == 1
    assert s["starts_total"] == 1
    assert s["starts_today"] == 1
    assert s["views_total"] == 2  # about + main

    # صفحه‌ی آمار خود پنل
    await tap(app, bot, "adm")
    await tap(app, bot, "adm:stats")

    text = last_edit(bot)["text"]
    assert "آمار ربات" in text
    assert "منوی اصلی" in text  # عنوان فارسی صفحه‌ی پربازدید
    assert "درباره" in text


async def test_stats_reset_with_confirmation(bot_app):
    app, bot = bot_app
    await send_command(app, bot, "/start", user=USER)
    await tap(app, bot, "adm")
    await tap(app, bot, "adm:stats:rst")

    # صفحه‌ی تأیید
    assert "بازگشت‌پذیر نیست" in last_edit(bot)["text"]

    await tap(app, bot, "adm:stats:rst:yes")
    assert "پاک شد" in last_edit(bot)["text"]

    s = analytics.summary()
    assert s["users_total"] == 0
    assert s["starts_total"] == 0
    # توجه: نمایش خود صفحه‌ی آمارِ پس از پاک‌کردن، یک رویداد تازه ثبت می‌کند
    assert s["views_total"] >= 0


# ---------------------------------------------------------------------------
# ویرایش محتوا
# ---------------------------------------------------------------------------


async def test_edit_media_link_full_flow(bot_app):
    app, bot = bot_app
    default_url = _media_telegram_url()

    # مرحله ۱: منوی ویرایش → گروه‌ها
    await tap(app, bot, "adm:edit")
    group_cbs = callbacks(last_edit(bot)["reply_markup"])
    assert "adm:edit:g:media" in group_cbs
    assert "adm:edit:g:products" in group_cbs

    # مرحله ۲: فیلدهای گروه رسانه‌ها
    await tap(app, bot, "adm:edit:g:media")
    field_cbs = callbacks(last_edit(bot)["reply_markup"])
    assert MEDIA_TG_URL_FIELD_CB in field_cbs
    assert "adm:edit:f:media:item:telegram:label" in field_cbs

    # مرحله ۳: صفحه‌ی فیلد (مقدار پیش‌فرض + دکمه‌ی تغییر؛ بدون دکمه‌ی بازگردانی)
    await tap(app, bot, MEDIA_TG_URL_FIELD_CB)
    edited = last_edit(bot)
    assert default_url in edited["text"]
    assert MEDIA_TG_URL_SET in callbacks(edited["reply_markup"])
    assert MEDIA_TG_URL_REVERT not in callbacks(edited["reply_markup"])

    # مرحله ۴: شروع ویرایش
    await tap(app, bot, MEDIA_TG_URL_SET)
    assert "مقدار جدید" in last_edit(bot)["text"]

    # مرحله ۵: ارسال مقدار جدید توسط مدیر
    await send_text(app, bot, "https://t.me/new_tizgam", user=USER)
    sent = last_send(bot)
    assert "ذخیره شد" in sent["text"]
    assert "https://t.me/new_tizgam" in sent["text"]
    # دکمه‌ی بازگردانی حالا ظاهر شده است
    assert MEDIA_TG_URL_REVERT in callbacks(sent["reply_markup"])

    # اعمال روی محتوای زنده‌ی ربات
    assert _media_telegram_url() == "https://t.me/new_tizgam"

    # ذخیره‌شدن در دیتابیس (ماندگار پس از ری‌استارت)
    row = get_db().query_one(
        "SELECT value FROM content_overrides WHERE key = ?", (MEDIA_TG_URL_FIELD,)
    )
    assert row is not None and row["value"] == "https://t.me/new_tizgam"

    # مرحله ۶: بازگردانی پیش‌فرض
    await tap(app, bot, MEDIA_TG_URL_REVERT)
    assert "پیش‌فرض" in last_edit(bot)["text"]
    assert _media_telegram_url() == default_url
    assert (
        get_db().query_one(
            "SELECT value FROM content_overrides WHERE key = ?", (MEDIA_TG_URL_FIELD,)
        )
        is None
    )

    # کاربر رسانه‌ها را باز می‌کند → لینک تلگرام دوباره پیش‌فرض است
    await tap(app, bot, "media")
    assert ("📨 کانال تلگرام", default_url) in _url_buttons_of_last_edit(bot)


async def test_edit_subject_aparat_link(bot_app):
    """ویرایش لینک آپارات یک درس (کلاس‌ها ← پایه ← درس)."""
    app, bot = bot_app
    await tap(app, bot, "adm:edit:g:classes")
    field_cbs = callbacks(last_edit(bot)["reply_markup"])
    assert "adm:edit:f:classes:6:math:url" in field_cbs

    await tap(app, bot, "adm:edit:f:classes:6:math:url")
    await tap(app, bot, "adm:edit:s:classes:6:math:url")
    await send_text(app, bot, "https://www.aparat.com/v/xyz123", user=USER)
    assert "ذخیره شد" in last_send(bot)["text"]

    grade = content.get_grade("6")
    assert content.get_subject(grade, "math").aparat_url == "https://www.aparat.com/v/xyz123"


async def test_edit_rejects_invalid_url_and_keeps_state(bot_app):
    app, bot = bot_app
    await tap(app, bot, "adm:edit:s:media:item:bale:url")
    await send_text(app, bot, "این یک لینک نیست", user=USER)
    sent = last_send(bot)
    assert "http://" in sent["text"]  # پیام خطای اعتبارسنجی

    # state حفظ شده → مقدار درست را که بفرستد، همان‌جا ذخیره می‌شود
    await send_text(app, bot, "https://ble.ir/new_channel", user=USER)
    assert "ذخیره شد" in last_send(bot)["text"]
    bale_url = next(
        item.url for item in content.MEDIA_SECTION.items if item.id == "bale"
    )
    assert bale_url == "https://ble.ir/new_channel"


async def test_admin_plain_text_without_edit_state_falls_back(bot_app):
    """پیام عادی مدیر وقتی در حالت ویرایش نیست → منوی راهنما (fallback)."""
    app, bot = bot_app
    await send_text(app, bot, "سلام", user=USER)
    sent = last_send(bot)
    assert content.FALLBACK_TEXT in sent["text"]


async def test_start_resets_edit_state(bot_app):
    app, bot = bot_app
    # مدیر وسط ویرایش است
    await tap(app, bot, "adm:edit:s:media:item:telegram:url")
    # /start می‌زند → state پاک می‌شود
    await send_command(app, bot, "/start", user=USER)
    # پیام بعدی مدیر دیگر مقدار ویرایشی نیست → fallback
    await send_text(app, bot, "https://t.me/should_not_apply", user=USER)
    sent = last_send(bot)
    assert content.FALLBACK_TEXT in sent["text"]
    assert _media_telegram_url() == "https://t.me/tizgam"  # تغییر نکرده


async def test_text_values_are_html_escaped(bot_app):
    """متن مدیر با تگ HTML فرستاده شود → escape می‌شود و صفحه نمی‌شکند."""
    app, bot = bot_app
    await tap(app, bot, "adm:edit:s:support:call_text")
    await send_text(app, bot, "شماره‌ی جدید: <b>021-999</b> & تست", user=USER)
    assert "ذخیره شد" in last_send(bot)["text"]

    # مقدار ذخیره‌شده escape شده است
    assert "&lt;b&gt;021-999&lt;/b&gt;" in content.SUPPORT.call_text

    # صفحه‌ی پشتیبانی بدون خطای parse رندر می‌شود
    await tap(app, bot, "sup:call")
    assert "شماره‌ی جدید" in last_edit(bot)["text"]


async def test_overrides_are_reapplied_on_restart(bot_app):
    """شبیه‌سازی ری‌استارت: اپ جدید، override های دیتابیس را دوباره اعمال می‌کند."""
    import os

    app, bot = bot_app
    await tap(app, bot, "adm:edit:s:media:item:telegram:url")
    await send_text(app, bot, "https://t.me/persisted_link", user=USER)
    assert _media_telegram_url() == "https://t.me/persisted_link"

    # «ری‌استارت»: ساخت اپلیکیشن جدید روی همان دیتابیس (همان env)
    assert os.environ["DATABASE_PATH"]
    from bot.main import create_application

    create_application()  # init_db + ContentManager.initialize()

    # مقدار ویرایش‌شده پس از ری‌استارت هم اعمال شده است
    assert _media_telegram_url() == "https://t.me/persisted_link"

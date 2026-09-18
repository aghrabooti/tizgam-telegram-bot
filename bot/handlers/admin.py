"""پنل مدیریت ربات
==================

دسترسی: فقط کاربران موجود در ``ADMIN_IDS`` (فایل .env).

امکانات:
- ``/admin`` → منوی پنل (آمار / کاربران / لاگ‌ها / دیتابیس / ویرایش محتوا)
- ``/id``    → نمایش شناسه‌ی کاربری (برای پیدا کردن ADMIN_IDS)
- 📊 آمار: تعداد کاربران، تعداد /start، تعداد نمایش هر صفحه (کل و امروز)
  + پربازدیدترین صفحه‌ها + پاک کردن آمار (با تأیید)
- 👥 کاربران: خلاصه + آخرین شماره‌های ثبت‌شده + خروجی CSV کامل
- 📋 لاگ‌ها: آخرین خطوط فایل لاگ + دریافت فایل کامل لاگ
- 💾 دیتابیس: وضعیت فایل + دریافت نسخه‌ی پشتیبان (SQLite snapshot)
- ✏️ ویرایش محتوا: همه‌ی متن‌ها و لینک‌های placeholder (رابط کاربری
  چندمرحله‌ای + دریافت مقدار جدید به‌صورت پیام)

نکته: ویرایش‌ها در دیتابیس ذخیره می‌شوند و پس از ری‌استارت هم اعمال
می‌شوند؛ ساختار (افزودن پایه/درس/محصول جدید) همچنان از طریق
``bot/config/content.py`` انجام می‌شود.
"""

from __future__ import annotations

import io
import logging
import os
import sqlite3
import tempfile
from datetime import datetime
from pathlib import Path

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import (
    Application,
    ApplicationHandlerStop,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from bot.config.settings import get_settings
from bot.constants import (
    CB_ADMIN_EDIT_CANCEL,
    CB_ADMIN_EDIT_FIELD,
    CB_ADMIN_EDIT_GROUP,
    CB_ADMIN_EDIT_REVERT,
    CB_ADMIN_EDIT_SET,
    EDIT_STATE_KEY,
    PATTERN_ADMIN,
    PATTERN_ADMIN_DB,
    PATTERN_ADMIN_DB_FILE,
    PATTERN_ADMIN_EDIT,
    PATTERN_ADMIN_EDIT_CANCEL,
    PATTERN_ADMIN_EDIT_FIELD,
    PATTERN_ADMIN_EDIT_GROUP,
    PATTERN_ADMIN_EDIT_REVERT,
    PATTERN_ADMIN_EDIT_SET,
    PATTERN_ADMIN_LOG_FILE,
    PATTERN_ADMIN_LOGS,
    PATTERN_ADMIN_STATS,
    PATTERN_ADMIN_STATS_RESET_ASK,
    PATTERN_ADMIN_STATS_RESET_YES,
    PATTERN_ADMIN_USERS,
    PATTERN_ADMIN_USERS_CSV,
)
from bot.keyboards import admin as keyboards
from bot.services import analytics, content_manager, navigation
from bot.services.content_manager import KIND_LABELS, ContentManager
from bot.utils.text import esc, fa_num, truncate

logger = logging.getLogger(__name__)

ADMIN_MENU_TEXT = (
    "🛠 <b>پنل مدیریت تیزگام</b>\n\n"
    "گزینه‌ی مورد نظر را انتخاب کنید:"
)

ADMIN_DENIED_TEXT = "⛔️ این بخش فقط برای مدیران ربات فعال است."

STATS_RESET_CONFIRM_TEXT = (
    "⚠️ <b>پاک کردن کامل آمار</b>\n\n"
    "همه‌ی کاربران و رویدادهای ثبت‌شده حذف می‌شوند.\n"
    "این عمل بازگشت‌پذیر نیست؛ مطمئن هستید؟"
)

EDIT_MENU_TEXT = (
    "✏️ <b>ویرایش محتوا</b>\n\n"
    "بخش مورد نظر را انتخاب کنید. مقدار جدید را به‌صورت پیام می‌گیریم و"
    " بلافاصله روی ربات اعمال می‌شود."
)


# ---------------------------------------------------------------------------
# ابزارهای مشترک
# ---------------------------------------------------------------------------


def is_admin(user_id: int | None) -> bool:
    return user_id is not None and user_id in get_settings().admin_ids


async def _require_admin(update: Update) -> bool:
    """گارد دسترسی برای callback ها؛ در صورت عدم دسترسی، پاسخ می‌دهد."""
    if is_admin(update.effective_user and update.effective_user.id):
        return True
    query = update.callback_query
    if query is not None:
        await query.answer(ADMIN_DENIED_TEXT, show_alert=True)
    return False


def _stats_text() -> str:
    s = analytics.summary()
    titles = analytics.screen_titles()
    lines = [
        "📊 <b>آمار ربات تیزگام</b>",
        "",
        f"👥 کاربران: <b>{fa_num(s['users_total'])}</b>"
        f" — امروز: {fa_num(s['users_today'])}",
        f"▶️ اجرای /start: <b>{fa_num(s['starts_total'])}</b>"
        f" — امروز: {fa_num(s['starts_today'])}",
        f"👁 نمایش صفحه‌ها: <b>{fa_num(s['views_total'])}</b>"
        f" — امروز: {fa_num(s['views_today'])}",
    ]
    top = analytics.top_screens(8)
    if top:
        lines += ["", "🏆 <b>پربازدیدترین صفحه‌ها:</b>"]
        lines += [
            f"• {titles.get(name, esc(name))} — {fa_num(count)} بار"
            for name, count in top
        ]
    lines += [
        "",
        "ℹ️ «نمایش صفحه» یعنی هر بار باز شدن صفحه توسط کاربر. باز شدن"
        " مستقیم لینک‌های خارجی (آپارات/سایت) توسط تلگرام گزارش نمی‌شود؛"
        " برای شمارش دقیق کلیک، لینک‌ها را از طریق ریدایرکت سایت خودتان"
        " عبور دهید.",
    ]
    return "\n".join(lines)


def _field_text(field, *, prefix: str = "") -> str:
    """متن صفحه‌ی جزئیات یک فیلد قابل‌ویرایش."""
    current = field.get_current()
    overridden = ContentManager.is_overridden(field.key)
    kind_label = KIND_LABELS.get(field.kind, field.kind)
    lines = []
    if prefix:
        lines += [prefix, ""]
    lines += [
        f"✏️ <b>{esc(field.title)}</b>",
        f"نوع: {kind_label}",
        "",
    ]
    if overridden:
        lines += [
            "مقدار فعلی (ویرایش‌شده توسط مدیر):",
            esc(truncate(current, 1500)),
            "",
            "مقدار پیش‌فرض:",
            esc(truncate(field.default, 300)),
        ]
    else:
        lines += ["مقدار فعلی (پیش‌فرض):", esc(truncate(current, 1500))]
    lines += ["", "با «✏️ تغییر مقدار» شروع کنید؛ مقدار جدید را پیام می‌دهید."]
    return "\n".join(lines)


def _field_markup(field) -> object:
    revert_cb = (
        CB_ADMIN_EDIT_REVERT.format(field_key=field.key)
        if ContentManager.is_overridden(field.key)
        else None
    )
    return keyboards.field_detail(
        set_callback=CB_ADMIN_EDIT_SET.format(field_key=field.key),
        revert_callback=revert_cb,
        back_to=CB_ADMIN_EDIT_GROUP.format(group_id=field.group),
    )


# ---------------------------------------------------------------------------
# فرمان‌ها
# ---------------------------------------------------------------------------


async def admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/admin → ورود به پنل مدیریت."""
    user = update.effective_user
    if not is_admin(user and user.id):
        await context.bot.send_message(
            chat_id=update.effective_chat.id, text=ADMIN_DENIED_TEXT
        )
        return
    await navigation.render_screen(
        update, context, text=ADMIN_MENU_TEXT, reply_markup=keyboards.menu()
    )


async def id_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/id → نمایش شناسه‌ی کاربری (برای تنظیم ADMIN_IDS)."""
    user = update.effective_user
    chat = update.effective_chat
    text = (
        "🆔 <b>شناسه‌ی شما</b>\n\n"
        f"👤 شناسه‌ی کاربری: <code>{user.id if user else '?'}</code>\n"
        f"💬 شناسه‌ی این گفت‌وگو: <code>{chat.id if chat else '?'}</code>\n\n"
        "برای دسترسی به پنل مدیریت (/admin)، شناسه‌ی کاربری خود را در"
        " متغیر ADMIN_IDS فایل .env قرار دهید."
    )
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=text,
        parse_mode=ParseMode.HTML,
    )


# ---------------------------------------------------------------------------
# منو و آمار
# ---------------------------------------------------------------------------


async def admin_menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await _require_admin(update):
        return
    await navigation.render_screen(
        update, context, text=ADMIN_MENU_TEXT, reply_markup=keyboards.menu()
    )


async def admin_stats(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await _require_admin(update):
        return
    await navigation.render_screen(
        update, context, text=_stats_text(), reply_markup=keyboards.stats()
    )


async def admin_stats_reset_ask(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    if not await _require_admin(update):
        return
    await navigation.render_screen(
        update,
        context,
        text=STATS_RESET_CONFIRM_TEXT,
        reply_markup=keyboards.stats_reset_confirm(),
    )


async def admin_stats_reset_yes(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    if not await _require_admin(update):
        return
    analytics.reset_all()
    logger.warning("آمار ربات توسط مدیر %s پاک شد.", update.effective_user.id)
    await navigation.render_screen(
        update,
        context,
        text="✅ آمار پاک شد.\n\n" + _stats_text(),
        reply_markup=keyboards.stats(),
    )


# ---------------------------------------------------------------------------
# ویرایش محتوا
# ---------------------------------------------------------------------------


async def admin_edit_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await _require_admin(update):
        return
    groups = [
        (title, CB_ADMIN_EDIT_GROUP.format(group_id=group_id))
        for group_id, title in ContentManager.edit_groups()
    ]
    await navigation.render_screen(
        update,
        context,
        text=EDIT_MENU_TEXT,
        reply_markup=keyboards.edit_groups(groups),
    )


async def admin_edit_group(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await _require_admin(update):
        return
    group_id = context.match.group("group_id")
    fields = ContentManager.fields_in_group(group_id)
    if not fields:
        await update.callback_query.answer(
            "این بخش یافت نشد؛ ممکن است تغییر کرده باشد.", show_alert=True
        )
        return await admin_edit_menu(update, context)

    buttons = [
        (truncate(field.title, 44), CB_ADMIN_EDIT_FIELD.format(field_key=field.key))
        for field in fields
    ]
    group_title = dict(ContentManager.edit_groups()).get(group_id, group_id)
    await navigation.render_screen(
        update,
        context,
        text=f"✏️ <b>ویرایش «{esc(group_title)}»</b>\n\n"
        "مورد دلخواه را انتخاب کنید تا مقدار فعلی و دکمه‌ی تغییر را ببینید:",
        reply_markup=keyboards.edit_fields(buttons),
    )


async def admin_edit_field(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await _require_admin(update):
        return
    field = ContentManager.get_field(context.match.group("field_key"))
    if field is None:
        await update.callback_query.answer("این مورد دیگر وجود ندارد.", show_alert=True)
        return await admin_edit_menu(update, context)

    await navigation.render_screen(
        update, context, text=_field_text(field), reply_markup=_field_markup(field)
    )


async def admin_edit_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """شروع ویرایش: state ذخیره می‌شود و کاربر مقدار جدید را پیام می‌دهد."""
    if not await _require_admin(update):
        return
    field = ContentManager.get_field(context.match.group("field_key"))
    if field is None:
        await update.callback_query.answer("این مورد دیگر وجود ندارد.", show_alert=True)
        return await admin_edit_menu(update, context)

    context.user_data[EDIT_STATE_KEY] = field.key
    kind_label = KIND_LABELS.get(field.kind, field.kind)
    text = (
        f"✏️ <b>ویرایش: {esc(field.title)}</b>\n\n"
        f"نوع: {kind_label}\n"
        f"مقدار فعلی: {esc(truncate(field.get_current(), 120))}\n\n"
        "📥 مقدار جدید را همین حالا به‌صورت یک پیام بفرستید."
    )
    markup = keyboards.edit_prompt(
        cancel_callback=CB_ADMIN_EDIT_CANCEL,
        back_to=CB_ADMIN_EDIT_GROUP.format(group_id=field.group),
    )
    await navigation.render_screen(update, context, text=text, reply_markup=markup)


async def admin_edit_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """انصراف از ویرایش → بازگشت به صفحه‌ی همان فیلد."""
    if not await _require_admin(update):
        return
    key = context.user_data.pop(EDIT_STATE_KEY, None)
    field = ContentManager.get_field(key) if key else None
    if field is None:
        return await admin_edit_menu(update, context)
    await navigation.render_screen(
        update,
        context,
        text=_field_text(field, prefix="❌ ویرایش لغو شد."),
        reply_markup=_field_markup(field),
    )


async def admin_edit_revert(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """بازگردانی مقدار پیش‌فرض برای یک فیلد."""
    if not await _require_admin(update):
        return
    field = ContentManager.get_field(context.match.group("field_key"))
    if field is None:
        await update.callback_query.answer("این مورد دیگر وجود ندارد.", show_alert=True)
        return await admin_edit_menu(update, context)

    ContentManager.revert(field.key)
    await navigation.render_screen(
        update,
        context,
        text=_field_text(field, prefix="↩️ به مقدار پیش‌فرض بازگشت."),
        reply_markup=_field_markup(field),
    )


async def admin_edit_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """دریافت مقدار جدید از مدیر (وقتی در حالت ویرایش است).

    این هندلر در گروه ۰ ثبت شده است؛ اگر مدیر در حالت ویرایش نباشد،
    بدون مصرف برمی‌گردد تا fallback (گروه ۱) پیام را بگیرد.
    """
    user = update.effective_user
    key = context.user_data.get(EDIT_STATE_KEY)
    if not key or not is_admin(user and user.id):
        return  # مصرف نمی‌کنیم

    field = ContentManager.get_field(key)
    if field is None:
        context.user_data.pop(EDIT_STATE_KEY, None)
        return

    value = (update.message.text or "").strip()
    error = content_manager.validate_value(field.kind, value)
    if error:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"⚠️ {error}\n\nدوباره بفرستید یا با دکمه‌ی «❌ انصراف» خارج شوید.",
        )
        raise ApplicationHandlerStop

    ContentManager.set_value(field.key, value)
    context.user_data.pop(EDIT_STATE_KEY, None)

    await navigation.render_screen(
        update,
        context,
        text=_field_text(field, prefix="✅ ذخیره شد و روی ربات اعمال شد."),
        reply_markup=_field_markup(field),
    )
    raise ApplicationHandlerStop


# ---------------------------------------------------------------------------
# کاربران و شماره‌های تماس
# ---------------------------------------------------------------------------


async def admin_users(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """خلاصه‌ی کاربران + آخرین شماره‌های ثبت‌شده."""
    if not await _require_admin(update):
        return
    await navigation.render_screen(
        update, context, text=_users_text(), reply_markup=keyboards.users()
    )


def _users_text() -> str:
    """متن صفحه‌ی کاربران (در ربات و پیش‌نمایش وب مشترک است)."""
    s = analytics.summary()
    lines = [
        "👥 <b>کاربران و شماره‌های تماس</b>",
        "",
        f"📊 ثبت‌شده: <b>{fa_num(s['users_total'])}</b>"
        f" — امروز: {fa_num(s['users_today'])}",
        f"📱 دارای شماره: <b>{fa_num(analytics.users_with_phone_count())}</b>",
        "",
        "<b>آخرین کاربران:</b>",
    ]
    recent = analytics.recent_users(10)
    if recent:
        for u in recent:
            name = esc(u["first_name"] or "—")
            phone = f"<code>{esc(u['phone'])}</code>" if u["phone"] else "بدون شماره"
            username = f" — @{esc(u['username'])}" if u["username"] else ""
            lines.append(f"• {name} — {phone}{username}")
    else:
        lines.append("• هنوز کاربری ثبت نشده است.")
    lines += ["", "برای لیست کامل با همه‌ی فیلدها، فایل CSV را دریافت کنید:"]
    return "\n".join(lines)


async def admin_users_csv(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """ارسال خروجی CSV کامل کاربران به‌صورت فایل."""
    if not await _require_admin(update):
        return
    csv_bytes = ("\ufeff" + analytics.users_csv()).encode("utf-8")  # BOM برای Excel
    await update.callback_query.answer("در حال ساخت فایل…")
    await context.bot.send_document(
        chat_id=update.effective_chat.id,
        document=io.BytesIO(csv_bytes),
        filename="tizgam-users.csv",
        caption="👥 لیست کامل کاربران و شماره‌های تماس",
    )


# ---------------------------------------------------------------------------
# لاگ‌ها و دیتابیس (گزارش و دریافت فایل)
# ---------------------------------------------------------------------------

# پارامترهای دم‌کردن انتهای فایل لاگ (همیشه محدود تا پیام طولانی نشود)
LOG_TAIL_LINES = 25
LOG_TAIL_BYTES = 8_000


def _read_log_tail(path: Path, max_bytes: int = LOG_TAIL_BYTES,
                   max_lines: int = LOG_TAIL_LINES) -> list[str]:
    """آخرین خطوط فایل لاگ؛ در نبود/خطای فایل، لیست خالی برمی‌گردد."""
    try:
        with path.open("rb") as fh:
            fh.seek(0, os.SEEK_END)
            size = fh.tell()
            fh.seek(max(0, size - max_bytes))
            data = fh.read()
    except OSError:
        return []
    return data.decode("utf-8", errors="replace").splitlines()[-max_lines:]


def _human_size(num_bytes: int) -> str:
    """حجم فایل به شکل خوانا (کیلوبایت/مگابایت)."""
    if num_bytes >= 1024 * 1024:
        return f"{fa_num(round(num_bytes / (1024 * 1024), 1))} مگابایت"
    return f"{fa_num(max(1, round(num_bytes / 1024)))} کیلوبایت"


def _logs_text() -> str:
    """متن صفحه‌ی لاگ‌ها (در ربات و پیش‌نمایش وب مشترک است)."""
    settings = get_settings()
    path = Path(settings.log_file)
    lines = _read_log_tail(path)
    size = path.stat().st_size if path.exists() else 0
    if lines:
        tail = [f"آخرین {fa_num(len(lines))} خط:", ""]
        tail += [f"<code>{esc(line)}</code>" for line in lines]
    else:
        tail = ["(فایل لاگ خالی است یا هنوز ساخته نشده است)"]
    return "\n".join([
        "📋 <b>گزارش لاگ ربات</b>",
        "",
        f"📁 مسیر: <code>{esc(path.name)}</code> — حجم: {_human_size(size)}",
        "",
        *tail,
        "",
        "برای دریافت کل فایل لاگ، دکمه‌ی زیر را بزنید.",
    ])


def _db_info_text() -> str:
    """متن صفحه‌ی وضعیت دیتابیس (در ربات و پیش‌نمایش وب مشترک است)."""
    settings = get_settings()
    path = Path(settings.database_path)
    size = path.stat().st_size if path.exists() else 0
    s = analytics.summary()
    return "\n".join([
        "💾 <b>دیتابیس و پشتیبان</b>",
        "",
        f"📁 فایل: <code>{esc(path.name)}</code> — حجم: {_human_size(size)}",
        f"👥 کاربران: <b>{fa_num(s['users_total'])}</b>"
        f" — دارای شماره: {fa_num(analytics.users_with_phone_count())}",
        f"👁 رویدادهای ثبت‌شده: <b>{fa_num(s['views_total'] + s['starts_total'])}</b>",
        "",
        "دکمه‌ی زیر یک نسخه‌ی پشتیبان سازگار با SQLite از دیتابیس می‌سازد"
        " و به‌صورت فایل می‌فرستد؛ با آن می‌توان دیتابیس را روی هر سرور"
        " دیگری بازیابی کرد.",
    ])


def _snapshot_db() -> bytes:
    """نسخه‌ی پشتیبان امن از دیتابیس (online backup رسمی SQLite).

    برخلاف کپی مستقیم فایل، حتی اگر هم‌زمان نوشتنی در جریان باشد
    خروجی سالم و بدون خرابی است.
    """
    settings = get_settings()
    fd, tmp_path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    try:
        src = sqlite3.connect(settings.database_path)
        try:
            dst = sqlite3.connect(tmp_path)
            try:
                src.backup(dst)
            finally:
                dst.close()
        finally:
            src.close()
        return Path(tmp_path).read_bytes()
    finally:
        os.unlink(tmp_path)


async def admin_logs(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """صفحه‌ی لاگ‌ها: آخرین خطوط + دکمه‌ی دریافت فایل کامل."""
    if not await _require_admin(update):
        return
    await navigation.render_screen(
        update, context, text=_logs_text(), reply_markup=keyboards.logs()
    )


async def admin_log_file(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """ارسال فایل کامل لاگ به مدیر."""
    if not await _require_admin(update):
        return
    path = Path(get_settings().log_file)
    if not path.exists():
        await update.callback_query.answer(
            "هنوز فایل لاگی ساخته نشده است.", show_alert=True
        )
        return
    await update.callback_query.answer("در حال ارسال فایل…")
    await context.bot.send_document(
        chat_id=update.effective_chat.id,
        document=io.BytesIO(path.read_bytes()),
        filename="tizgam-bot.log",
        caption=f"📋 فایل کامل لاگ ربات ({_human_size(path.stat().st_size)})",
    )


async def admin_db(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """صفحه‌ی وضعیت دیتابیس + دکمه‌ی دریافت پشتیبان."""
    if not await _require_admin(update):
        return
    await navigation.render_screen(
        update, context, text=_db_info_text(), reply_markup=keyboards.db()
    )


async def admin_db_file(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """ارسال نسخه‌ی پشتیبان دیتابیس به مدیر."""
    if not await _require_admin(update):
        return
    if not Path(get_settings().database_path).exists():
        await update.callback_query.answer(
            "فایل دیتابیس وجود ندارد.", show_alert=True
        )
        return
    await update.callback_query.answer("در حال ساخت پشتیبان…")
    stamp = datetime.now().strftime("%Y%m%d-%H%M")
    await context.bot.send_document(
        chat_id=update.effective_chat.id,
        document=io.BytesIO(_snapshot_db()),
        filename=f"tizgam-backup-{stamp}.db",
        caption="💾 نسخه‌ی پشتیبان دیتابیس (SQLite) — برای بازیابی، فایل را"
        " جایگزین data/tizgam.db کنید و ربات را ری‌استارت کنید.",
    )


# ---------------------------------------------------------------------------
# ثبت
# ---------------------------------------------------------------------------


def register(app: Application) -> None:
    app.add_handler(CommandHandler("admin", admin_command))
    app.add_handler(CommandHandler("id", id_command))

    app.add_handler(CallbackQueryHandler(admin_menu_callback, pattern=PATTERN_ADMIN))
    app.add_handler(CallbackQueryHandler(admin_stats, pattern=PATTERN_ADMIN_STATS))
    app.add_handler(
        CallbackQueryHandler(admin_stats_reset_ask, pattern=PATTERN_ADMIN_STATS_RESET_ASK)
    )
    app.add_handler(
        CallbackQueryHandler(admin_stats_reset_yes, pattern=PATTERN_ADMIN_STATS_RESET_YES)
    )
    app.add_handler(CallbackQueryHandler(admin_edit_menu, pattern=PATTERN_ADMIN_EDIT))
    app.add_handler(
        CallbackQueryHandler(admin_edit_group, pattern=PATTERN_ADMIN_EDIT_GROUP)
    )
    app.add_handler(
        CallbackQueryHandler(admin_edit_field, pattern=PATTERN_ADMIN_EDIT_FIELD)
    )
    app.add_handler(
        CallbackQueryHandler(admin_edit_start, pattern=PATTERN_ADMIN_EDIT_SET)
    )
    app.add_handler(
        CallbackQueryHandler(admin_edit_cancel, pattern=PATTERN_ADMIN_EDIT_CANCEL)
    )
    app.add_handler(
        CallbackQueryHandler(admin_edit_revert, pattern=PATTERN_ADMIN_EDIT_REVERT)
    )

    app.add_handler(CallbackQueryHandler(admin_users, pattern=PATTERN_ADMIN_USERS))
    app.add_handler(
        CallbackQueryHandler(admin_users_csv, pattern=PATTERN_ADMIN_USERS_CSV)
    )
    app.add_handler(CallbackQueryHandler(admin_logs, pattern=PATTERN_ADMIN_LOGS))
    app.add_handler(
        CallbackQueryHandler(admin_log_file, pattern=PATTERN_ADMIN_LOG_FILE)
    )
    app.add_handler(CallbackQueryHandler(admin_db, pattern=PATTERN_ADMIN_DB))
    app.add_handler(CallbackQueryHandler(admin_db_file, pattern=PATTERN_ADMIN_DB_FILE))

    # دریافت مقدار جدید مدیر (گروه ۰؛ فقط وقتی state ویرایش فعال است مصرف می‌کند)
    app.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, admin_edit_text), group=0
    )

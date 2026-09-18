"""ناوبری و رندر صفحه‌ها
========================

رفتار اصلی:
- صفحات همیشه روی «همان پیام» ویرایش می‌شوند (``editMessageText``) تا
  چت کاربر با پیام‌های تکراری شلوغ نشود.
- اگر پیام قابل ویرایش نباشد (حذف/قدیمی شده باشد)، همان صفحه به‌صورت
  پیام جدید ارسال می‌شود.
- اگر محتوای صفحه دقیقاً برابر پیام فعلی باشد، خطای
  ``message is not modified`` بی‌صدا نادیده گرفته می‌شود.
- ``/start`` و پیام‌های متنی، چون callback نیستند، به‌صورت پیام جدید
  رندر می‌شوند.

این ماژول state-less است؛ ناوبری یک درخت ثابت است و هر صفحه خودش
والدش را می‌شناسد، بنابراین «بازگشت» همیشه دقیقاً یک مرحله عقب است و
دکمه‌های منقضی (پس از تغییر کانفیگ) با یک هشدار کاربر را به منوی
اصلی برمی‌گردانند.
"""

from __future__ import annotations

import logging
from typing import Sequence

from telegram import InlineKeyboardButton, LinkPreviewOptions, Update
from telegram.constants import ParseMode
from telegram.error import BadRequest, TelegramError
from telegram.ext import ContextTypes

from bot.config import content
from bot.keyboards import menus
from bot.services import analytics

logger = logging.getLogger(__name__)

# پیش‌نمایش لینک در متن صفحه‌ها غیرفعال است (تمیزتر و سبک‌تر)
_NO_PREVIEW = LinkPreviewOptions(is_disabled=True)

# خطاهای قابل چشم‌پوشی هنگام ویرایش پیام
_NOT_MODIFIED = "message is not modified"
_NOT_FOUND = "message to edit not found"
_NOT_EDITABLE = "message can't be edited"


async def render_screen(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    *,
    text: str,
    reply_markup,
    answer_callback: bool = True,
) -> None:
    """یک صفحه را روی همان پیام رندر می‌کند (یا پیام جدید می‌فرستد).

    Args:
        text: متن صفحه (HTML).
        reply_markup: کیبورد صفحه.
        answer_callback: اگر ``False`` باشد، callback query قبلاً توسط
            فراخواننده پاسخ داده شده است.
    """
    query = update.callback_query

    if query is None:
        # فرمان/پیام جدید (مثل /start) → پیام جدید
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=text,
            reply_markup=reply_markup,
            parse_mode=ParseMode.HTML,
            link_preview_options=_NO_PREVIEW,
        )
        return

    if answer_callback:
        try:
            await query.answer()
        except TelegramError as exc:
            # مثلاً دوباره‌کلیک یا گذشته‌شدن مهلت پاسخ؛ نباید ناوبری را بشکند
            logger.debug("پاسخ به callback query ناموفق بود: %s", exc)

    # ثبت آمار: هر ناوبری با دکمه‌ی inline یک «نمایش صفحه» است
    # (خطای دیتابیس هرگز نباید ناوبری کاربر را متوقف کند)
    try:
        analytics.log_screen(query.from_user.id, query.data)
    except Exception:  # noqa: BLE001
        logger.exception("ثبت آمار نمایش صفحه ناموفق بود")

    try:
        await query.edit_message_text(
            text=text,
            reply_markup=reply_markup,
            parse_mode=ParseMode.HTML,
            link_preview_options=_NO_PREVIEW,
        )
    except BadRequest as exc:
        message = str(exc).lower()
        if _NOT_MODIFIED in message:
            # صفحه از قبل همین است → هیچ کاری لازم نیست
            return
        if _NOT_FOUND in message or _NOT_EDITABLE in message:
            # پیام قبلی حذف/غیرقابل ویرایش است → صفحه را جدید بفرست
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=text,
                reply_markup=reply_markup,
                parse_mode=ParseMode.HTML,
                link_preview_options=_NO_PREVIEW,
            )
            return
        raise


async def render_content_section(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    section: content.ContentSection,
    *,
    extra_rows: Sequence[Sequence[InlineKeyboardButton]] = (),
    answer_callback: bool = True,
) -> None:
    """یک بخش محتوایی (متن + دکمه‌های لینک + رسانه‌ی اختیاری) را رندر می‌کند."""
    await render_screen(
        update,
        context,
        text=section.text,
        reply_markup=menus.content_section(section, extra_rows=extra_rows),
        answer_callback=answer_callback,
    )
    await _send_section_media(update, context, section)


async def _send_section_media(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    section: content.ContentSection,
) -> None:
    """رسانه‌ی اختیاری بخش (عکس/ویدیو) را بعد از صفحه ارسال می‌کند.

    ارسال رسانه هرگز نباید ناوبری را بشکند؛ خطاها فقط لاگ می‌شوند.
    """
    chat_id = update.effective_chat.id
    try:
        if section.video_url:
            await context.bot.send_video(chat_id=chat_id, video=section.video_url)
        if section.photo_url:
            await context.bot.send_photo(chat_id=chat_id, photo=section.photo_url)
    except TelegramError as exc:
        logger.warning("ارسال رسانه‌ی بخش ناموفق بود: %s", exc)


async def show_main_menu(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    *,
    answer_callback: bool = True,
) -> None:
    """منوی اصلی را نمایش می‌دهد (و هر state قبلی را عملاً باطل می‌کند)."""
    await render_screen(
        update,
        context,
        text=content.WELCOME_TEXT,
        reply_markup=menus.main_menu(),
        answer_callback=answer_callback,
    )


async def show_stale_button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """دکمه‌ی منقضی/نامعتبر: هشدار + بازگشت به منوی اصلی."""
    query = update.callback_query
    if query is not None:
        await query.answer(content.STALE_BUTTON_TEXT, show_alert=True)
    await show_main_menu(update, context, answer_callback=False)

"""هندلرهای خطا و حالت‌های مرزی.

- ``on_error``: خطای غیرمنتظره → لاگ کامل + پیام کوتاه به کاربر.
- ``unknown_callback``: callback ناشناخته/منقضی (مثلاً پس از تغییر
  کانفیگ) → هشدار + بازگشت به منوی اصلی.
- ``fallback_text``: پیام متنی غیردستوری → نمایش مجدد منوی اصلی.

نکته: ``unknown_callback`` باید «آخرین» CallbackQueryHandler ثبت‌شده
باشد (بدون pattern) تا فقط callbackهایی که هیچ هندلر دیگری نپذیرفته
را بگیرد.
"""

from __future__ import annotations

import logging

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from bot.config import content
from bot.keyboards import menus
from bot.services import navigation
from bot.utils.text import esc

logger = logging.getLogger(__name__)


async def on_error(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """گرفتن و لاگ تمام خطاهای مدیریت‌نشده‌ی هندلرها."""
    logger.error(
        "خطا هنگام پردازش آپدیت %s",
        update,
        exc_info=context.error,
    )

    if isinstance(update, Update) and update.callback_query is not None:
        try:
            await update.callback_query.answer(
                "⚠️ خطایی رخ داد؛ لطفاً دوباره تلاش کنید.", show_alert=True
            )
        except Exception:  # noqa: BLE001 - پاسخ‌دادن به خطا نباید خودش خطا دهد
            logger.debug("پاسخ به callback query ناموفق بود", exc_info=True)


async def unknown_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """callback ناشناخته → هشدار و بازگشت به منوی اصلی."""
    logger.warning("callback ناشناخته دریافت شد: %r", update.callback_query.data)
    await navigation.show_stale_button(update, context)


async def fallback_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """پیام متنی غیردستوری → راهنما + منوی اصلی."""
    user_name = update.effective_user.first_name if update.effective_user else ""
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f"{esc(user_name)} عزیز، {content.FALLBACK_TEXT}",
        reply_markup=menus.main_menu(),
        parse_mode=ParseMode.HTML,
    )


def register_error_handlers(app: Application) -> None:
    # fallback در گروه ۱ ثبت می‌شود تا هندلرهای گروه ۰ (مانند دریافت مقدار
    # جدید از مدیر در حالت ویرایش) بتوانند پیام را ابتدا بررسی کنند.
    app.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, fallback_text), group=1
    )
    # آخرین هندلر callback (بدون pattern) → فقط callbackهای ناشناخته
    app.add_handler(CallbackQueryHandler(unknown_callback))
    app.add_error_handler(on_error)

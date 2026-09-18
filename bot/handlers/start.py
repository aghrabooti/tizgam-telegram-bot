"""/start و نمایش منوی اصلی.

هر بار /start:
- آمار کاربر و رویداد start ثبت می‌شود،
- state ویرایش نیمه‌تمام مدیر (در صورت وجود) پاک می‌شود،
- منوی اصلی به‌صورت یک پیام تازه نمایش داده می‌شود.

چون ناوبری ربات state-less است، این یعنی کاربر عملاً به منوی اصلی
بازگشته است.
"""

from __future__ import annotations

from telegram import Update
from telegram.ext import Application, CallbackQueryHandler, CommandHandler, ContextTypes

from bot.constants import EDIT_STATE_KEY, PATTERN_MAIN
from bot.services import analytics, navigation


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/start → منوی اصلی (reset کامل به منوی اصلی)."""
    # reset state های موقت (مثل ویرایش نیمه‌تمام محتوا)
    context.user_data.pop(EDIT_STATE_KEY, None)

    # ثبت آمار
    if update.effective_user is not None:
        analytics.upsert_user(update.effective_user)
        analytics.log_start(update.effective_user.id)

    await navigation.show_main_menu(update, context)


async def main_menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """دکمه‌ی «🏠 منوی اصلی» → ویرایش همان پیام به منوی اصلی."""
    await navigation.show_main_menu(update, context)


def register(app: Application) -> None:
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("menu", start_command))
    app.add_handler(CallbackQueryHandler(main_menu_callback, pattern=PATTERN_MAIN))

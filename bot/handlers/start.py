"""/start و نمایش منوی اصلی.

جریان شروع:
1. ثبت/به‌روزرسانی کاربر و رویداد start در آمار.
2. اگر کاربر هنوز شماره‌ی تماس نداده و رد هم نکرده → اول درخواست شماره.
3. در غیر این صورت → منوی اصلی.

هر بار /start، state ویرایش نیمه‌تمام مدیر پاک می‌شود؛ چون ناوبری ربات
state-less است، این یعنی کاربر عملاً به منوی اصلی بازگشته است.
"""

from __future__ import annotations

from telegram import Update
from telegram.ext import Application, CallbackQueryHandler, CommandHandler, ContextTypes

from bot.constants import EDIT_STATE_KEY, PATTERN_MAIN
from bot.handlers.phone import send_phone_request
from bot.services import analytics, navigation


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/start → درخواست شماره (اگر لازم) یا منوی اصلی."""
    # reset state های موقت (مثل ویرایش نیمه‌تمام محتوا)
    context.user_data.pop(EDIT_STATE_KEY, None)

    user = update.effective_user
    if user is not None:
        analytics.upsert_user(user)
        analytics.log_start(user.id)

        # اولین بار: قبل از منو، شماره‌ی تماس را می‌خواهیم
        if analytics.needs_phone(user.id):
            return await send_phone_request(update, context)

    await navigation.show_main_menu(update, context)


async def main_menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """دکمه‌ی «🏠 منوی اصلی» → ویرایش همان پیام به منوی اصلی."""
    await navigation.show_main_menu(update, context)


def register(app: Application) -> None:
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("menu", start_command))
    app.add_handler(CallbackQueryHandler(main_menu_callback, pattern=PATTERN_MAIN))

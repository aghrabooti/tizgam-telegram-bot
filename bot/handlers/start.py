"""/start و نمایش منوی اصلی.

هر بار /start، منوی اصلی به‌صورت یک پیام تازه نمایش داده می‌شود؛
چون ناوبری ربات state-less است، این یعنی state قبلی کاربر عملاً
باطل شده و ربات به منوی اصلی بازگشته است.
"""

from __future__ import annotations

from telegram import Update
from telegram.ext import Application, CallbackQueryHandler, CommandHandler, ContextTypes

from bot.constants import PATTERN_MAIN
from bot.services import navigation


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/start → منوی اصلی (reset کامل به منوی اصلی)."""
    await navigation.show_main_menu(update, context)


async def main_menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """دکمه‌ی «🏠 منوی اصلی» → ویرایش همان پیام به منوی اصلی."""
    await navigation.show_main_menu(update, context)


def register(app: Application) -> None:
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("menu", start_command))
    app.add_handler(CallbackQueryHandler(main_menu_callback, pattern=PATTERN_MAIN))

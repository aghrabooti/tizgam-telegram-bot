"""بخش «پشتیبانی»: تماس تلفنی یا گفت‌وگو در تلگرام."""

from __future__ import annotations

from telegram import Update
from telegram.ext import Application, CallbackQueryHandler, ContextTypes

from bot.config import content
from bot.constants import (
    BTN_STYLE_SUCCESS,
    CB_SUPPORT_CALL,
    CB_SUPPORT_TELEGRAM,
    PATTERN_SUPPORT,
    PATTERN_SUPPORT_CALL,
    PATTERN_SUPPORT_TELEGRAM,
)
from bot.keyboards.common import build, button
from bot.services import navigation


async def show_support_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """انتخاب روش پشتیبانی: تماس / تلگرام."""
    await navigation.render_screen(
        update,
        context,
        text=content.SUPPORT_MENU_TEXT,
        reply_markup=build(
            [
                [button(content.LBL_SUPPORT_CALL, callback_data=CB_SUPPORT_CALL)],
                [
                    button(
                        content.LBL_SUPPORT_TELEGRAM, callback_data=CB_SUPPORT_TELEGRAM
                    )
                ],
            ]
        ),
    )


async def show_call_support(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """نمایش شماره تماس و ساعات پاسخگویی (از کانفیگ)."""
    await navigation.render_screen(
        update,
        context,
        text=content.SUPPORT.call_text,
        reply_markup=build([]),
    )


async def show_telegram_support(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """اتصال به اکانت/گروه پشتیبانی تلگرام (لینک از کانفیگ)."""
    await navigation.render_screen(
        update,
        context,
        text=content.SUPPORT.telegram_text,
        reply_markup=build(
            [
                [
                    button(
                        content.LBL_SUPPORT_CHAT,
                        url=content.SUPPORT.telegram_url,
                        style=BTN_STYLE_SUCCESS,
                    )
                ]
            ]
        ),
    )


def register(app: Application) -> None:
    app.add_handler(CallbackQueryHandler(show_support_menu, pattern=PATTERN_SUPPORT))
    app.add_handler(CallbackQueryHandler(show_call_support, pattern=PATTERN_SUPPORT_CALL))
    app.add_handler(
        CallbackQueryHandler(show_telegram_support, pattern=PATTERN_SUPPORT_TELEGRAM)
    )

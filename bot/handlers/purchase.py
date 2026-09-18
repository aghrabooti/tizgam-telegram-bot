"""بخش «خرید تیزپک».

اطلاعات محصول و لینک/روش خرید کاملاً از ``bot/config/content.py``
خوانده می‌شود؛ تا زمان اتصال درگاه پرداخت آنلاین، دکمه‌ی خرید کاربر را
به لینک سفارش (سایت/تلگرام) هدایت می‌کند.
"""

from __future__ import annotations

from telegram import Update
from telegram.ext import Application, CallbackQueryHandler, ContextTypes

from bot.config import content
from bot.constants import PATTERN_PURCHASE
from bot.services import navigation


async def show_purchase(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """نمایش اطلاعات تیزپک + دکمه‌ی خرید (لینک از کانفیگ)."""
    await navigation.render_content_section(update, context, content.PURCHASE_SECTION)


def register(app: Application) -> None:
    app.add_handler(CallbackQueryHandler(show_purchase, pattern=PATTERN_PURCHASE))

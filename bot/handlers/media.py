"""بخش «لینک رسانه‌های تیزگام».

تمام لینک‌های شبکه‌های اجتماعی (تلگرام، اینستاگرام، بله، روبیکا،
ایتا، سایت) از کانفیگ خوانده می‌شوند و هر دکمه مستقیماً لینک مربوطه
را باز می‌کند.
"""

from __future__ import annotations

from telegram import Update
from telegram.ext import Application, CallbackQueryHandler, ContextTypes

from bot.config import content
from bot.constants import PATTERN_MEDIA
from bot.services import navigation


async def show_media(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """نمایش دکمه‌های لینک رسانه‌های اجتماعی."""
    await navigation.render_content_section(update, context, content.MEDIA_SECTION)


def register(app: Application) -> None:
    app.add_handler(CallbackQueryHandler(show_media, pattern=PATTERN_MEDIA))

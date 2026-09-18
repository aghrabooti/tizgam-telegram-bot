"""بخش‌های ویدیویی: «قبولی‌های تیزگام» و «رضایت‌های تیزپک»."""

from __future__ import annotations

from telegram import Update
from telegram.ext import Application, CallbackQueryHandler, ContextTypes

from bot.config import content
from bot.constants import PATTERN_VIDEO_ACCEPTANCE, PATTERN_VIDEO_SATISFACTION
from bot.services import navigation


async def show_acceptance_videos(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """ویدیوهای قبولی‌های تیزگام (لیست ویدیوها از کانفیگ خوانده می‌شود)."""
    await navigation.render_content_section(update, context, content.ACCEPTANCE_VIDEOS_SECTION)


async def show_satisfaction_videos(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """ویدیوهای رضایت مشتریان/دانش‌آموزان تیزپک."""
    await navigation.render_content_section(update, context, content.SATISFACTION_VIDEOS_SECTION)


def register(app: Application) -> None:
    app.add_handler(CallbackQueryHandler(show_acceptance_videos, pattern=PATTERN_VIDEO_ACCEPTANCE))
    app.add_handler(
        CallbackQueryHandler(show_satisfaction_videos, pattern=PATTERN_VIDEO_SATISFACTION)
    )

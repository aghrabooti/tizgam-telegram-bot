"""بخش «درباره موسسه تیزهوشان تیزگام»."""

from __future__ import annotations

from telegram import Update
from telegram.ext import Application, CallbackQueryHandler, ContextTypes

from bot.config import content
from bot.constants import PATTERN_ABOUT
from bot.services import navigation


async def show_about(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """نمایش محتوای معرفی موسسه (متن/لینک/رسانه؛ همه از کانفیگ)."""
    await navigation.render_content_section(update, context, content.ABOUT_SECTION)


def register(app: Application) -> None:
    app.add_handler(CallbackQueryHandler(show_about, pattern=PATTERN_ABOUT))

"""نقطه‌ی ورود ربات: ساخت اپلیکیشن و اجرای polling."""

from __future__ import annotations

import logging

from telegram import Update
from telegram.ext import Application, ApplicationBuilder

from bot import __version__
from bot.config.settings import get_settings
from bot.handlers import register_handlers

logger = logging.getLogger("bot")


def create_application() -> Application:
    """اپلیکیشن ربات را می‌سازد (برای استفاده در production و تست‌ها)."""
    settings = get_settings()

    application = ApplicationBuilder().token(settings.bot_token).build()
    register_handlers(application)
    return application


def main() -> None:
    """اجرای ربات با long-polling."""
    settings = get_settings()
    logging.basicConfig(
        level=getattr(logging, settings.log_level, logging.INFO),
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    )

    logger.info("راه‌اندازی ربات تیزگام (نسخه %s) ...", __version__)
    application = create_application()

    # فقط آپدیتهایی که لازم داریم را دریافت می‌کنیم
    application.run_polling(allowed_updates=Update.ALL_TYPES)

    logger.info("ربات تیزگام متوقف شد.")


if __name__ == "__main__":
    main()

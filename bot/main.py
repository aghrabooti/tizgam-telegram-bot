"""نقطه‌ی ورود ربات: ساخت اپلیکیشن و اجرای polling.

روش استاندارد اجرا از ریشه‌ی پروژه::

    python -m bot

اجرای مستقیم فایل هم پشتیبانی می‌شود::

    python bot/main.py
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

# برای اینکه «اجرای مستقیم فایل» هم کار کند (python bot/main.py)، ریشه‌ی
# پروژه را به sys.path اضافه می‌کنیم. در حالت استاندارد (python -m bot)
# این مسیر از قبل موجود است و این کار بی‌اثر و بی‌ضرر است.
_PROJECT_ROOT = str(Path(__file__).resolve().parent.parent)
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from telegram import Update  # noqa: E402
from telegram.ext import Application, ApplicationBuilder  # noqa: E402

from bot import __version__  # noqa: E402
from bot.config.settings import get_settings  # noqa: E402
from bot.handlers import register_handlers  # noqa: E402
from bot.services.content_manager import ContentManager  # noqa: E402
from bot.services.database import init_db  # noqa: E402
from bot.utils.logging_setup import setup_logging  # noqa: E402

logger = logging.getLogger("bot")


def create_application() -> Application:
    """اپلیکیشن ربات را می‌سازد (برای استفاده در production و تست‌ها)."""
    settings = get_settings()

    # دیتابیس (آمار + مقادیر ویرایش‌شده‌ی محتوا) و اعمال override ها
    init_db(settings.database_path)
    ContentManager.initialize()

    application = ApplicationBuilder().token(settings.bot_token).build()
    register_handlers(application)
    return application


def main() -> None:
    """اجرای ربات با long-polling."""
    settings = get_settings()
    # لاگ هم‌زمان روی کنسول و فایل چرخشی (data/bot.log)
    setup_logging(level=settings.log_level, log_file=settings.log_file)

    logger.info("راه‌اندازی ربات تیزگام (نسخه %s) ...", __version__)
    application = create_application()

    # فقط آپدیتهایی که لازم داریم را دریافت می‌کنیم
    application.run_polling(allowed_updates=Update.ALL_TYPES)

    logger.info("ربات تیزگام متوقف شد.")


if __name__ == "__main__":
    main()

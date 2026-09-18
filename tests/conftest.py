"""فیکسچرهای تست.

استراتژی: اپلیکیشن واقعی (با تمام هندلرهای ثبت‌شده) ساخته می‌شود اما
``bot`` آن با یک mock خودکار (autospec) جایگزین می‌شود؛ سپس آپدیت‌های
ساختنی از طریق ``app.process_update`` پردازش می‌شوند. به این ترتیب
مسیریابی کامل ربات (pattern ها، ترتیب هندلرها، متن‌ها و کیبوردها)
بدون هیچ تماس شبکه‌ای تست می‌شود.
"""

from __future__ import annotations

import os

# باید قبل از import بسته‌ی bot تنظیم شود
os.environ.setdefault("BOT_TOKEN", "123456:TEST-TOKEN")

from unittest.mock import create_autospec  # noqa: E402

import pytest  # noqa: E402
from telegram.ext._extbot import ExtBot  # noqa: E402

from bot.main import create_application  # noqa: E402


@pytest.fixture()
async def bot_app():
    """(application, mock_bot) آماده‌ی پردازش آپدیت."""
    application = create_application()
    mock_bot = create_autospec(ExtBot, instance=True)
    # جایگزینی bot با mock و حذف updater تا هیچ تماس شبکه‌ای صورت نگیرد
    application.bot = mock_bot
    application.updater = None
    await application.initialize()
    try:
        yield application, mock_bot
    finally:
        await application.shutdown()

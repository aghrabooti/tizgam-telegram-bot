"""ثبت متمرکز تمام هندلرها.

ترتیب ثبت مهم است:
1. هندلرهای بخش‌ها (هر کدام pattern اختصاصی خودش را دارد).
2. پنل مدیریت (فرمان‌ها + callback های adm:* + دریافت مقدار جدید مدیر).
3. در پایان ``errors.register_error_handlers`` که هندلرهای «گیرنده‌ی
   باقی‌مانده» (callback ناشناخته، متن نامفهوم و error handler) را اضافه
   می‌کند.
"""

from __future__ import annotations

from telegram.ext import Application

from bot.handlers import (
    about,
    admin,
    classes,
    errors,
    exams,
    media,
    products,
    purchase,
    start,
    support,
    videos,
)

_MODULES = (
    start,
    about,
    videos,
    products,
    support,
    purchase,
    classes,
    exams,
    media,
    admin,
)


def register_handlers(app: Application) -> None:
    """تمام هندلرهای ربات را روی اپلیکیشن ثبت می‌کند."""
    for module in _MODULES:
        module.register(app)
    errors.register_error_handlers(app)

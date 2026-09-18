"""
تنظیمات اجرایی ربات (environment-driven)
==========================================

این فایل «چگونگی اجرا» را کنترل می‌کند (توکن، سطح لاگ) و با
``bot/config/content.py`` (محتوای قابل‌تنظیم) متفاوت است.
"""

from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv


@dataclass(frozen=True)
class Settings:
    """تنظیمات اجرایی ربات."""

    bot_token: str
    log_level: str = "INFO"


def get_settings() -> Settings:
    """تنظیمات را از متغیرهای محیطی (یا فایل ``.env``) می‌خواند."""
    load_dotenv()

    bot_token = os.getenv("BOT_TOKEN", "").strip()
    if not bot_token:
        raise SystemExit(
            "❌ متغیر BOT_TOKEN تنظیم نشده است.\n"
            "   فایل .env.example را به .env کپی کرده و توکن ربات را"
            " از @BotFather در آن قرار دهید."
        )

    return Settings(
        bot_token=bot_token,
        log_level=os.getenv("LOG_LEVEL", "INFO").upper(),
    )

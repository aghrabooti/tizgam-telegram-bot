"""تنظیمات اجرایی ربات (environment-driven)
==========================================

این فایل «چگونگی اجرا» را کنترل می‌کند (توکن، مدیران، دیتابیس، سطح لاگ)
و با ``bot/config/content.py`` (محتوای قابل‌تنظیم) متفاوت است.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


@dataclass(frozen=True)
class Settings:
    """تنظیمات اجرایی ربات."""

    bot_token: str
    admin_ids: frozenset[int]
    database_path: str
    log_level: str = "INFO"


def _parse_admin_ids(raw: str) -> frozenset[int]:
    """پردازش ADMIN_IDS به‌صورت لیست شناسه‌های عددی (با , یا ; جدا شده)."""
    ids: set[int] = set()
    for part in raw.replace(";", ",").split(","):
        part = part.strip()
        if not part:
            continue
        try:
            ids.add(int(part))
        except ValueError:
            continue  # مقادیر نامعتبر بی‌صدا نادیده گرفته می‌شوند
    return frozenset(ids)


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

    project_root = Path(__file__).resolve().parent.parent.parent
    database_path = (
        os.getenv("DATABASE_PATH", "").strip()
        or str(project_root / "data" / "tizgam.db")
    )

    return Settings(
        bot_token=bot_token,
        admin_ids=_parse_admin_ids(os.getenv("ADMIN_IDS", "")),
        database_path=database_path,
        log_level=os.getenv("LOG_LEVEL", "INFO").upper(),
    )

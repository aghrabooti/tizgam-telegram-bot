"""راه‌اندازی لاگ: کنسول + فایل چرخشی (RotatingFileHandler).

فایل لاگ به‌صورت پیش‌فرض در ``data/bot.log`` ساخته می‌شود و پس از رسیدن به
حجم معین، به‌صورت خودکار بایگانی و چرخیده می‌شود (تا دیسک پر نشود).
"""

from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
_MAX_BYTES = 2 * 1024 * 1024  # ۲ مگابایت
_BACKUP_COUNT = 3  # + فایل جاری = حداکثر ۴ فایل


def setup_logging(level: str = "INFO", log_file: str | None = None) -> None:
    """پیکربندی لاگر ریشه: خروجی کنسول + فایل (اختیاری)."""
    root = logging.getLogger()
    root.setLevel(getattr(logging, level.upper(), logging.INFO))
    root.handlers.clear()

    formatter = logging.Formatter(_FORMAT)

    console = logging.StreamHandler()
    console.setFormatter(formatter)
    root.addHandler(console)

    if log_file:
        Path(log_file).parent.mkdir(parents=True, exist_ok=True)
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=_MAX_BYTES,
            backupCount=_BACKUP_COUNT,
            encoding="utf-8",
        )
        file_handler.setFormatter(formatter)
        root.addHandler(file_handler)

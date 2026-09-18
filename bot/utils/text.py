"""ابزارهای متنی (HTML rendering).

همه‌ی متن‌های ثابت در ``bot/config/content.py`` به‌صورت HTML-safe نوشته
شده‌اند؛ این ابزارها برای درج امن مقادیر «داینامیک» (عناوین درس، محصول و
...) درون قالب‌های HTML به کار می‌روند.
"""

from __future__ import annotations

from html import escape


def esc(value: object) -> str:
    """مقدار را برای درج امن در متن HTML فرار (escape) می‌دهد."""
    return escape(str(value), quote=False)


def bullet(items: list[str] | tuple[str, ...], marker: str = "•") -> str:
    """یک لیست نشانه‌دار می‌سازد."""
    return "\n".join(f"{marker} {item}" for item in items)

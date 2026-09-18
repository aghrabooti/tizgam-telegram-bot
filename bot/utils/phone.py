"""ابزار اعتبارسنجی و نرمال‌سازی شماره‌ی موبایل ایران.

ورودی می‌تواند شامل ارقام فارسی/عربی، فاصله، خط تیره و پرانتز باشد؛
خروجی همیشه به‌صورت ``+989XXXXXXXXX`` است یا ``None`` اگر معتبر نباشد.
"""

from __future__ import annotations

import re

# ارقام فارسی و عربی → لاتین
_FA_DIGITS = str.maketrans("۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩", "01234567890123456789")

# 09xxxxxxxxx / 9xxxxxxxxx / +989xxxxxxxxx / 00989xxxxxxxxx
_PHONE_RE = re.compile(r"^(?:\+98|0098|98|0)?(9\d{9})$")


def normalize_phone(raw: str) -> str | None:
    """شماره را نرمال می‌کند؛ در صورت نامعتبر بودن None برمی‌گرداند."""
    if not raw:
        return None

    digits = str(raw).translate(_FA_DIGITS)
    digits = re.sub(r"[\s\-\(\)\.]", "", digits)
    digits = digits.lstrip("+")

    match = _PHONE_RE.match(digits)
    if not match:
        return None
    return "+98" + match.group(1)

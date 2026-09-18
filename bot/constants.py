"""
قرارداد داده‌ی Callback ها (تنها منبع حقیقت)
=============================================

نام‌گذاری همه‌ی callback data ها در این فایل متمرکز شده است تا:

- callback ها کوتاه، استاندارد و بدون تکرار باشند،
- هندلرها و کیبوردها هرگز رشته‌ی جادویی hard-code نکنند،
- افزودن بخش جدید فقط با افزودن ثابت + pattern انجام شود.

طرح نام‌گذاری::

    <بخش>[:<عمل>][:<کلید>...]

مثال‌ها::

    main                  → منوی اصلی
    vid:acc               → ویدیو قبولی‌ها
    prod                  → ریشه‌ی بخش محصولات
    prod:g:6              → محصولات پایه ششم
    prod:g:6:tezpack      → جزئیات محصول «تیزپک» پایه ششم
    cls:g:9:math          → نمونه کلاس ریاضی پایه نهم
"""

from __future__ import annotations

import re

# ---------------------------------------------------------------------------
# ثابت‌های callback (مقادیری که در دکمه‌ها نوشته می‌شوند)
# ---------------------------------------------------------------------------

# صفحه‌های ایستا (یک سطحی)
CB_MAIN = "main"
CB_ABOUT = "about"
CB_VIDEO_ACCEPTANCE = "vid:acc"
CB_VIDEO_SATISFACTION = "vid:sat"
CB_SUPPORT = "sup"
CB_SUPPORT_CALL = "sup:call"
CB_SUPPORT_TELEGRAM = "sup:tg"
CB_PURCHASE = "buy"
CB_CLASSES = "cls"
CB_EXAMS = "exm"
CB_MEDIA = "media"

# ریشه‌ی بخش‌های چندمرحله‌ای
CB_PRODUCTS = "prod"

# الگوهای پویا (با .format(...) ساخته می‌شوند)
CB_PRODUCTS_GRADE = "prod:g:{grade_id}"
CB_PRODUCT_DETAIL = "prod:g:{grade_id}:{product_id}"
CB_CLASSES_GRADE = "cls:g:{grade_id}"
CB_CLASS_SUBJECT = "cls:g:{grade_id}:{subject_id}"
CB_EXAMS_GRADE = "exm:g:{grade_id}"
CB_EXAM_DETAIL = "exm:g:{grade_id}:{exam_id}"


# ---------------------------------------------------------------------------
# الگوهای Regex برای CallbackQueryHandler
# ---------------------------------------------------------------------------
# کلیدها از content خوانده می‌شوند؛ pattern فقط «شکل» داده را اعتبارسنجی
# می‌کند و اعتبار مقدار (وجود پایه/درس/محصول) در خود هندلر چک می‌شود.
# به این ترتیب افزودن پایه یا محصول «جدید» هیچ تغییری در کد هندلرها
# لازم ندارد و صرفاً در فایل محتوا انجام می‌شود.

PATTERN_MAIN = rf"^{re.escape(CB_MAIN)}$"
PATTERN_ABOUT = rf"^{re.escape(CB_ABOUT)}$"
PATTERN_VIDEO_ACCEPTANCE = rf"^{re.escape(CB_VIDEO_ACCEPTANCE)}$"
PATTERN_VIDEO_SATISFACTION = rf"^{re.escape(CB_VIDEO_SATISFACTION)}$"
PATTERN_PRODUCTS = rf"^{re.escape(CB_PRODUCTS)}$"
PATTERN_PRODUCTS_GRADE = r"^prod:g:(?P<grade_id>[^:]+)$"
PATTERN_PRODUCT_DETAIL = r"^prod:g:(?P<grade_id>[^:]+):(?P<product_id>[^:]+)$"
PATTERN_SUPPORT = rf"^{re.escape(CB_SUPPORT)}$"
PATTERN_SUPPORT_CALL = rf"^{re.escape(CB_SUPPORT_CALL)}$"
PATTERN_SUPPORT_TELEGRAM = rf"^{re.escape(CB_SUPPORT_TELEGRAM)}$"
PATTERN_PURCHASE = rf"^{re.escape(CB_PURCHASE)}$"
PATTERN_CLASSES = rf"^{re.escape(CB_CLASSES)}$"
PATTERN_CLASSES_GRADE = r"^cls:g:(?P<grade_id>[^:]+)$"
PATTERN_CLASS_SUBJECT = r"^cls:g:(?P<grade_id>[^:]+):(?P<subject_id>[^:]+)$"
PATTERN_EXAMS = rf"^{re.escape(CB_EXAMS)}$"
PATTERN_EXAMS_GRADE = r"^exm:g:(?P<grade_id>[^:]+)$"
PATTERN_EXAM_DETAIL = r"^exm:g:(?P<grade_id>[^:]+):(?P<exam_id>[^:]+)$"
PATTERN_MEDIA = rf"^{re.escape(CB_MEDIA)}$"

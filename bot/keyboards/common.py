"""قطعات مشترک ساخت کیبورد (دکمه‌های ناوبری و سازنده‌ی صفحه).

قرارداد ناوبری:
- صفحه‌های سطح ۱ (ریشه‌ی هر بخش): یک دکمه‌ی «🔙 بازگشت به منوی اصلی».
- صفحه‌های سطح ۲ به بعد: ردیف ``[🔙 بازگشت] [🏠 منوی اصلی]``.
"""

from __future__ import annotations

from typing import Callable, Optional, Sequence

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from bot.config import content
from bot.constants import CB_MAIN


def back_button(callback_data: str) -> InlineKeyboardButton:
    """دکمه‌ی بازگشت به مرحله‌ی قبل (callback صفحه‌ی والد)."""
    return InlineKeyboardButton(content.LBL_BACK, callback_data=callback_data)


def home_button() -> InlineKeyboardButton:
    """دکمه‌ی بازگشت به منوی اصلی."""
    return InlineKeyboardButton(content.LBL_HOME, callback_data=CB_MAIN)


def nav_row(back_to: Optional[str] = None) -> list[InlineKeyboardButton]:
    """ردیف ناوبری پایین هر صفحه.

    Args:
        back_to: callback صفحه‌ی والد؛ اگر ``None`` باشد صفحه سطح ۱ است و
            فقط دکمه‌ی «بازگشت به منوی اصلی» نمایش داده می‌شود.
    """
    if back_to is None:
        return [InlineKeyboardButton(content.LBL_BACK_TO_MAIN, callback_data=CB_MAIN)]
    return [back_button(back_to), home_button()]


def build(
    rows: Sequence[Sequence[InlineKeyboardButton]],
    back_to: Optional[str] = None,
) -> InlineKeyboardMarkup:
    """ردیف‌های محتوای صفحه را به‌همراه ردیف ناوبری کامل می‌کند."""
    return InlineKeyboardMarkup([*rows, nav_row(back_to=back_to)])


def grade_selection(
    callback_of_grade: Callable[[str], str],
    grades: Sequence = (),
) -> InlineKeyboardMarkup:
    """کیبورد انتخاب پایه؛ برای هر پایه یک دکمه.

    Args:
        callback_of_grade: تابعی که شناسه‌ی پایه را به callback_data تبدیل
            می‌کند (مثلاً ``"6" -> "prod:g:6"``).
        grades: لیست پایه‌ها (پیش‌فرض: همه‌ی پایه‌های تعریف‌شده).
    """
    grades = tuple(grades) or content.GRADES
    rows = [
        [InlineKeyboardButton(f"{g.emoji} {g.title}", callback_data=callback_of_grade(g.id))]
        for g in grades
    ]
    return build(rows)

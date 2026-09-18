"""کیبوردهای اختصاصی هر صفحه‌ی ربات.

هر تابع فقط یک ``InlineKeyboardMarkup`` می‌سازد و هیچ منطق ناوبری /
ارسال پیام در این لایه وجود ندارد.
"""

from __future__ import annotations

from typing import Optional, Sequence

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from bot.config import content
from bot.constants import (
    BTN_STYLE_SUCCESS,
    CB_CLASS_SUBJECT,
    CB_CLASSES_GRADE,
    CB_EXAM_DETAIL,
    CB_EXAMS_GRADE,
    CB_PRODUCT_DETAIL,
    CB_PRODUCTS_GRADE,
)
from bot.keyboards.common import build


def main_menu() -> InlineKeyboardMarkup:
    """منوی اصلی ربات (۹ گزینه‌ی تعریف‌شده در محتوا)."""
    rows = [
        [InlineKeyboardButton(item.label, callback_data=item.callback)]
        for item in content.MAIN_MENU
    ]
    return InlineKeyboardMarkup(rows)


def content_section(
    section: content.ContentSection,
    extra_rows: Sequence[Sequence[InlineKeyboardButton]] = (),
) -> InlineKeyboardMarkup:
    """کیبورد یک بخش محتوایی: دکمه‌های URL آیتم‌ها + ناوبری.

    دکمه‌های لینک به‌صورت سبز (success) نمایش داده می‌شوند تا «اقدام اصلی»
    بودن‌شان مشخص باشد (Bot API 9.4+).
    """
    rows = [
        [InlineKeyboardButton(item.label, url=item.url, style=BTN_STYLE_SUCCESS)]
        for item in section.items
    ]
    return build([*rows, *extra_rows])


def link_detail(url: str, label: str, back_to: Optional[str]) -> InlineKeyboardMarkup:
    """کیبورد صفحه‌ی جزئیات با یک دکمه‌ی URL سبز + ناوبری."""
    return build(
        [[InlineKeyboardButton(label, url=url, style=BTN_STYLE_SUCCESS)]],
        back_to=back_to,
    )


def class_subjects(grade: content.Grade) -> InlineKeyboardMarkup:
    """لیست درس‌های یک پایه برای تماشای نمونه کلاس."""
    rows = [
        [
            InlineKeyboardButton(
                f"{subject.emoji} {subject.title}",
                callback_data=CB_CLASS_SUBJECT.format(
                    grade_id=grade.id, subject_id=subject.id
                ),
            )
        ]
        for subject in grade.subjects
    ]
    return build(rows, back_to=CB_CLASSES_GRADE.format(grade_id=grade.id))


def products(grade_id: str, products: Sequence[content.Product]) -> InlineKeyboardMarkup:
    """لیست محصولات یک پایه."""
    rows = [
        [
            InlineKeyboardButton(
                f"📦 {product.title}",
                callback_data=CB_PRODUCT_DETAIL.format(
                    grade_id=grade_id, product_id=product.id
                ),
            )
        ]
        for product in products
    ]
    return build(rows, back_to=CB_PRODUCTS_GRADE.format(grade_id=grade_id))


def exams(grade_id: str, exams: Sequence[content.Exam]) -> InlineKeyboardMarkup:
    """لیست نمونه آزمون‌های یک پایه."""
    rows = [
        [
            InlineKeyboardButton(
                f"📝 {exam.title}",
                callback_data=CB_EXAM_DETAIL.format(grade_id=grade_id, exam_id=exam.id),
            )
        ]
        for exam in exams
    ]
    return build(rows, back_to=CB_EXAMS_GRADE.format(grade_id=grade_id))

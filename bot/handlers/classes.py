"""بخش «نمونه کلاس‌های تیزگام».

جریان: پایه (ششم/نهم) → درس → لینک جلسه‌ی نمونه در آپارات.

ساختار داده به‌صورت ``grade → subject → aparat_url`` در
``bot/config/content.py`` تعریف شده است و هیچ لینکی در این فایل
hard-code نشده است؛ افزودن پایه/درس جدید فقط با ویرایش همان فایل
انجام می‌شود.
"""

from __future__ import annotations

from telegram import Update
from telegram.ext import Application, CallbackQueryHandler, ContextTypes

from bot.config import content
from bot.constants import (
    CB_CLASSES_GRADE,
    PATTERN_CLASS_SUBJECT,
    PATTERN_CLASSES,
    PATTERN_CLASSES_GRADE,
)
from bot.keyboards import common, menus
from bot.services import navigation
from bot.utils.text import esc


async def show_classes_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """مرحله ۱: انتخاب پایه."""
    await navigation.render_screen(
        update,
        context,
        text=content.CLASSES_INTRO_TEXT,
        reply_markup=common.grade_selection(
            lambda grade_id: CB_CLASSES_GRADE.format(grade_id=grade_id)
        ),
    )


async def show_grade_subjects(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """مرحله ۲: لیست درس‌های پایه‌ی انتخاب‌شده."""
    grade_id = context.match.group("grade_id")
    grade = content.get_grade(grade_id)
    if grade is None:
        return await navigation.show_stale_button(update, context)

    await navigation.render_screen(
        update,
        context,
        text=content.CLASSES_GRADE_TEXT.format(grade_title=esc(grade.title)),
        reply_markup=menus.class_subjects(grade),
    )


async def show_subject_sample(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """مرحله ۳: نمایش لینک جلسه‌ی نمونه‌ی درس انتخاب‌شده در آپارات."""
    grade_id = context.match.group("grade_id")
    grade = content.get_grade(grade_id)
    subject = content.get_subject(grade, context.match.group("subject_id")) if grade else None
    if subject is None:
        return await navigation.show_stale_button(update, context)

    await navigation.render_screen(
        update,
        context,
        text=content.CLASS_SUBJECT_TEXT.format(
            subject=esc(subject.title),
            grade_title=esc(grade.title),
        ),
        reply_markup=menus.link_detail(
            subject.aparat_url,
            content.LBL_WATCH_ON_APARAT,
            back_to=CB_CLASSES_GRADE.format(grade_id=grade.id),
        ),
    )


def register(app: Application) -> None:
    app.add_handler(CallbackQueryHandler(show_classes_menu, pattern=PATTERN_CLASSES))
    app.add_handler(CallbackQueryHandler(show_grade_subjects, pattern=PATTERN_CLASSES_GRADE))
    app.add_handler(CallbackQueryHandler(show_subject_sample, pattern=PATTERN_CLASS_SUBJECT))

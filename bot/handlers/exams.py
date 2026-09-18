"""بخش «نمونه آزمون تیزگام».

جریان: پایه (ششم/نهم) → لیست نمونه آزمون‌ها → مشاهده/دانلود.
ساختار داده‌محور و قابل توسعه؛ افزودن آزمون جدید فقط در فایل محتوا.
"""

from __future__ import annotations

from telegram import Update
from telegram.ext import Application, CallbackQueryHandler, ContextTypes

from bot.config import content
from bot.constants import (
    CB_EXAMS_GRADE,
    PATTERN_EXAM_DETAIL,
    PATTERN_EXAMS,
    PATTERN_EXAMS_GRADE,
)
from bot.keyboards import common, menus
from bot.services import navigation
from bot.utils.text import esc


async def show_exams_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """مرحله ۱: انتخاب پایه."""
    await navigation.render_screen(
        update,
        context,
        text=content.EXAMS_INTRO_TEXT,
        reply_markup=common.grade_selection(
            lambda grade_id: CB_EXAMS_GRADE.format(grade_id=grade_id),
            grades=content.exam_grades(),
        ),
    )


async def show_grade_exams(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """مرحله ۲: لیست نمونه آزمون‌های پایه‌ی انتخاب‌شده."""
    grade_id = context.match.group("grade_id")
    grade = content.get_grade(grade_id)
    exams = content.get_exams(grade_id)
    if grade is None or not exams:
        return await navigation.show_stale_button(update, context)

    await navigation.render_screen(
        update,
        context,
        text=content.EXAMS_GRADE_TEXT.format(grade_title=esc(grade.title)),
        reply_markup=menus.exams(grade_id, exams),
    )


async def show_exam_detail(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """مرحله ۳: نمایش لینک مشاهده/دانلود نمونه آزمون."""
    grade_id = context.match.group("grade_id")
    grade = content.get_grade(grade_id)
    exam = content.get_exam(grade_id, context.match.group("exam_id"))
    if grade is None or exam is None:
        return await navigation.show_stale_button(update, context)

    await navigation.render_screen(
        update,
        context,
        text=content.EXAM_DETAIL_TEXT.format(
            title=esc(exam.title),
            grade_title=esc(grade.title),
        ),
        reply_markup=menus.link_detail(
            exam.url,
            content.LBL_OPEN_EXAM,
            back_to=CB_EXAMS_GRADE.format(grade_id=grade_id),
        ),
    )


def register(app: Application) -> None:
    app.add_handler(CallbackQueryHandler(show_exams_menu, pattern=PATTERN_EXAMS))
    app.add_handler(CallbackQueryHandler(show_grade_exams, pattern=PATTERN_EXAMS_GRADE))
    app.add_handler(CallbackQueryHandler(show_exam_detail, pattern=PATTERN_EXAM_DETAIL))

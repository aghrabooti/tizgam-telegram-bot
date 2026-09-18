"""بخش «محصولات پایه ششم و نهم».

جریان: انتخاب پایه → لیست محصولات → جزئیات محصول + لینک سفارش.
محصولات به‌صورت داده‌محور از ``bot/config/content.py`` خوانده می‌شوند؛
افزودن محصول یا پایه‌ی جدید هیچ تغییری در این فایل لازم ندارد.
"""

from __future__ import annotations

from telegram import Update
from telegram.ext import Application, CallbackQueryHandler, ContextTypes

from bot.config import content
from bot.constants import (
    CB_PRODUCTS_GRADE,
    PATTERN_PRODUCT_DETAIL,
    PATTERN_PRODUCTS,
    PATTERN_PRODUCTS_GRADE,
)
from bot.keyboards import menus
from bot.services import navigation
from bot.utils.text import esc


async def show_products_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """مرحله ۱: انتخاب پایه (فقط پایه‌هایی که محصول دارند)."""
    await navigation.render_screen(
        update,
        context,
        text=content.PRODUCTS_INTRO_TEXT,
        reply_markup=_grade_keyboard(),
    )


async def show_grade_products(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """مرحله ۲: لیست محصولات پایه‌ی انتخاب‌شده."""
    grade_id = context.match.group("grade_id")
    grade = content.get_grade(grade_id)
    products = content.get_products(grade_id)
    if grade is None or not products:
        return await navigation.show_stale_button(update, context)

    await navigation.render_screen(
        update,
        context,
        text=content.PRODUCTS_GRADE_TEXT.format(grade_title=esc(grade.title)),
        reply_markup=menus.products(grade_id, products),
    )


async def show_product_detail(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """مرحله ۳: جزئیات محصول + دکمه‌ی ثبت سفارش (لینک خرید از کانفیگ)."""
    grade_id = context.match.group("grade_id")
    product_id = context.match.group("product_id")
    grade = content.get_grade(grade_id)
    product = content.get_product(grade_id, product_id)
    if grade is None or product is None:
        return await navigation.show_stale_button(update, context)

    text = content.PRODUCT_DETAIL_TEXT.format(
        title=esc(product.title),
        grade_title=esc(grade.title),
        description=esc(product.description),
        price=esc(product.price),
    )
    await navigation.render_screen(
        update,
        context,
        text=text,
        reply_markup=menus.link_detail(
            product.order_url,
            content.LBL_ORDER_PRODUCT,
            back_to=CB_PRODUCTS_GRADE.format(grade_id=grade_id),
        ),
    )


def _grade_keyboard():
    """کیبورد انتخاب پایه برای بخش محصولات."""
    from bot.keyboards.common import grade_selection

    return grade_selection(
        lambda grade_id: CB_PRODUCTS_GRADE.format(grade_id=grade_id),
        grades=content.product_grades(),
    )


def register(app: Application) -> None:
    app.add_handler(CallbackQueryHandler(show_products_menu, pattern=PATTERN_PRODUCTS))
    app.add_handler(CallbackQueryHandler(show_grade_products, pattern=PATTERN_PRODUCTS_GRADE))
    app.add_handler(CallbackQueryHandler(show_product_detail, pattern=PATTERN_PRODUCT_DETAIL))

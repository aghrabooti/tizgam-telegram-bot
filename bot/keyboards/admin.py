"""کیبوردهای پنل مدیریت."""

from __future__ import annotations

from typing import Optional, Sequence

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from bot.constants import (
    BTN_STYLE_DANGER,
    CB_ADMIN,
    CB_ADMIN_EDIT,
    CB_ADMIN_STATS,
    CB_ADMIN_STATS_RESET_ASK,
    CB_ADMIN_STATS_RESET_YES,
)
from bot.keyboards.common import build


def menu() -> InlineKeyboardMarkup:
    """منوی اصلی پنل مدیریت."""
    rows = [
        [InlineKeyboardButton("📊 آمار و گزارش‌ها", callback_data=CB_ADMIN_STATS)],
        [InlineKeyboardButton("✏️ ویرایش محتوا", callback_data=CB_ADMIN_EDIT)],
    ]
    return build(rows)


def stats() -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton("🔄 به‌روزرسانی", callback_data=CB_ADMIN_STATS)],
        [InlineKeyboardButton("🗑 پاک کردن آمار", callback_data=CB_ADMIN_STATS_RESET_ASK)],
    ]
    return build(rows, back_to=CB_ADMIN)


def stats_reset_confirm() -> InlineKeyboardMarkup:
    """تأیید پاک‌کردن آمار؛ دکمه‌ی خطر به‌صورت قرمز (danger) است (Bot API 9.4+)."""
    rows = [
        [
            InlineKeyboardButton(
                "✅ بله، پاک شود",
                callback_data=CB_ADMIN_STATS_RESET_YES,
                style=BTN_STYLE_DANGER,
            )
        ],
        [InlineKeyboardButton("❌ انصراف", callback_data=CB_ADMIN_STATS)],
    ]
    return build(rows, back_to=CB_ADMIN)


def edit_groups(groups: Sequence[tuple[str, str]]) -> InlineKeyboardMarkup:
    """لیست گروه‌های محتوایی؛ هر عضو: (عنوان, callback)."""
    rows = [
        [InlineKeyboardButton(title, callback_data=callback)]
        for title, callback in groups
    ]
    return build(rows, back_to=CB_ADMIN)


def edit_fields(fields: Sequence[tuple[str, str]]) -> InlineKeyboardMarkup:
    """لیست فیلدهای یک گروه؛ هر عضو: (عنوان, callback)."""
    rows = [
        [InlineKeyboardButton(title, callback_data=callback)]
        for title, callback in fields
    ]
    return build(rows, back_to=CB_ADMIN_EDIT)


def field_detail(
    set_callback: str,
    revert_callback: Optional[str],
    back_to: str,
) -> InlineKeyboardMarkup:
    """صفحه‌ی جزئیات یک فیلد."""
    rows = [[InlineKeyboardButton("✏️ تغییر مقدار", callback_data=set_callback)]]
    if revert_callback is not None:
        rows.append(
            [InlineKeyboardButton("↩️ بازگردانی پیش‌فرض", callback_data=revert_callback)]
        )
    return build(rows, back_to=back_to)


def edit_prompt(cancel_callback: str, back_to: str) -> InlineKeyboardMarkup:
    """صفحه‌ی «مقدار جدید را بفرستید»."""
    rows = [[InlineKeyboardButton("❌ انصراف", callback_data=cancel_callback)]]
    return build(rows, back_to=back_to)

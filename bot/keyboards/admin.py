"""کیبوردهای پنل مدیریت."""

from __future__ import annotations

from typing import Optional, Sequence

from telegram import InlineKeyboardMarkup

from bot.constants import (
    BTN_STYLE_DANGER,
    BTN_STYLE_SUCCESS,
    CB_ADMIN,
    CB_ADMIN_DB,
    CB_ADMIN_DB_FILE,
    CB_ADMIN_EDIT,
    CB_ADMIN_LOG_FILE,
    CB_ADMIN_LOGS,
    CB_ADMIN_STATS,
    CB_ADMIN_STATS_RESET_ASK,
    CB_ADMIN_STATS_RESET_YES,
    CB_ADMIN_USERS,
    CB_ADMIN_USERS_CSV,
)
from bot.keyboards.common import build, button


def menu() -> InlineKeyboardMarkup:
    """منوی اصلی پنل مدیریت."""
    rows = [
        [button("📊 آمار و گزارش‌ها", callback_data=CB_ADMIN_STATS)],
        [button("👥 کاربران و شماره‌ها", callback_data=CB_ADMIN_USERS)],
        [button("📋 لاگ‌ها", callback_data=CB_ADMIN_LOGS)],
        [button("💾 دیتابیس و پشتیبان", callback_data=CB_ADMIN_DB)],
        [button("✏️ ویرایش محتوا", callback_data=CB_ADMIN_EDIT)],
    ]
    return build(rows)


def stats() -> InlineKeyboardMarkup:
    rows = [
        [button("🔄 به‌روزرسانی", callback_data=CB_ADMIN_STATS)],
        [button("🗑 پاک کردن آمار", callback_data=CB_ADMIN_STATS_RESET_ASK)],
    ]
    return build(rows, back_to=CB_ADMIN)


def stats_reset_confirm() -> InlineKeyboardMarkup:
    """تأیید پاک‌کردن آمار؛ دکمه‌ی خطر به‌صورت قرمز (danger) است (Bot API 9.4+)."""
    rows = [
        [
            button(
                "✅ بله، پاک شود",
                callback_data=CB_ADMIN_STATS_RESET_YES,
                style=BTN_STYLE_DANGER,
            )
        ],
        [button("❌ انصراف", callback_data=CB_ADMIN_STATS)],
    ]
    return build(rows, back_to=CB_ADMIN)


def edit_groups(groups: Sequence[tuple[str, str]]) -> InlineKeyboardMarkup:
    """لیست گروه‌های محتوایی؛ هر عضو: (عنوان, callback)."""
    rows = [
        [button(title, callback_data=callback)]
        for title, callback in groups
    ]
    return build(rows, back_to=CB_ADMIN)


def edit_fields(fields: Sequence[tuple[str, str]]) -> InlineKeyboardMarkup:
    """لیست فیلدهای یک گروه؛ هر عضو: (عنوان, callback)."""
    rows = [
        [button(title, callback_data=callback)]
        for title, callback in fields
    ]
    return build(rows, back_to=CB_ADMIN_EDIT)


def field_detail(
    set_callback: str,
    revert_callback: Optional[str],
    back_to: str,
) -> InlineKeyboardMarkup:
    """صفحه‌ی جزئیات یک فیلد."""
    rows = [[button("✏️ تغییر مقدار", callback_data=set_callback)]]
    if revert_callback is not None:
        rows.append(
            [button("↩️ بازگردانی پیش‌فرض", callback_data=revert_callback)]
        )
    return build(rows, back_to=back_to)


def edit_prompt(cancel_callback: str, back_to: str) -> InlineKeyboardMarkup:
    """صفحه‌ی «مقدار جدید را بفرستید»."""
    rows = [[button("❌ انصراف", callback_data=cancel_callback)]]
    return build(rows, back_to=back_to)


def users() -> InlineKeyboardMarkup:
    """صفحه‌ی کاربران: دریافت خروجی CSV + ناوبری."""
    rows = [
        [button("📥 دریافت فایل CSV کاربران", callback_data=CB_ADMIN_USERS_CSV)],
    ]
    return build(rows, back_to=CB_ADMIN)


def logs() -> InlineKeyboardMarkup:
    """صفحه‌ی لاگ‌ها: به‌روزرسانی + دریافت فایل کامل لاگ."""
    rows = [
        [button("🔄 به‌روزرسانی", callback_data=CB_ADMIN_LOGS)],
        [
            button(
                "📥 دریافت فایل کامل لاگ",
                callback_data=CB_ADMIN_LOG_FILE,
                style=BTN_STYLE_SUCCESS,
            )
        ],
    ]
    return build(rows, back_to=CB_ADMIN)


def db() -> InlineKeyboardMarkup:
    """صفحه‌ی دیتابیس: دریافت فایل پشتیبان + ناوبری."""
    rows = [
        [
            button(
                "📥 دریافت فایل پشتیبان دیتابیس",
                callback_data=CB_ADMIN_DB_FILE,
                style=BTN_STYLE_SUCCESS,
            )
        ],
    ]
    return build(rows, back_to=CB_ADMIN)

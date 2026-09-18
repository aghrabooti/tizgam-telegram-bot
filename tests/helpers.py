"""ابزارهای ساخت آپدیت و بررسی خروجی‌ها در تست‌ها."""

from __future__ import annotations

import itertools
from datetime import datetime, timezone
from typing import Optional

from telegram import (
    CallbackQuery,
    Chat,
    Contact,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
    MessageEntity,
    Update,
    User,
)
from telegram.constants import MessageEntityType

from bot.config import content

_IDS = itertools.count(1000)

CHAT = Chat(id=555, type="private")
USER = User(id=777, first_name="Tester", is_bot=False)
# کاربر غیرمدیر (در ADMIN_IDS نیست)
NON_ADMIN = User(id=888, first_name="Outsider", is_bot=False)


def _next_id() -> int:
    return next(_IDS)


def _message(bot, text: str, user: User, entities: Optional[list[MessageEntity]] = None) -> Message:
    message = Message(
        message_id=_next_id(),
        date=datetime.now(tz=timezone.utc),
        chat=CHAT,
        from_user=user,
        text=text,
        entities=entities or [],
    )
    message.set_bot(bot)
    return message


def _command_entities(text: str) -> list[MessageEntity]:
    """entities لازم برای تشخیص متن به‌عنوان دستور."""
    command = text.split("@")[0].split()[0]
    return [MessageEntity(type=MessageEntityType.BOT_COMMAND, offset=0, length=len(command))]


async def send_command(app, bot, text: str, user: User = USER) -> None:
    """ارسال یک دستور (مثل /start) به ربات."""
    update = Update(
        update_id=_next_id(),
        message=_message(bot, text, user, _command_entities(text)),
    )
    await app.process_update(update)


async def send_text(app, bot, text: str, user: User = USER) -> None:
    """ارسال یک پیام متنی معمولی به ربات."""
    update = Update(update_id=_next_id(), message=_message(bot, text, user))
    await app.process_update(update)


async def tap(app, bot, callback_data: str, user: User = USER) -> None:
    """شبیه‌سازی فشردن یک دکمه‌ی inline با callback_data داده‌شده."""
    message = _message(bot, "menu", user)
    query = CallbackQuery(
        id=str(_next_id()),
        from_user=user,
        chat_instance="test",
        data=callback_data,
        message=message,
    )
    query.set_bot(bot)
    await app.process_update(Update(update_id=_next_id(), callback_query=query))


# ---------------------------------------------------------------------------
# بررسی خروجی‌ها (روی mock bot)
# ---------------------------------------------------------------------------


def last_send(bot) -> dict:
    """kwargs آخرین send_message."""
    assert bot.send_message.await_count > 0, "send_message هرگز صدا زده نشد"
    return bot.send_message.await_args.kwargs


def last_edit(bot) -> dict:
    """kwargs آخرین edit_message_text."""
    assert bot.edit_message_text.await_count > 0, "edit_message_text هرگز صدا زده نشد"
    return bot.edit_message_text.await_args.kwargs


def last_answer(bot) -> dict:
    """kwargs آخرین answer_callback_query."""
    assert bot.answer_callback_query.await_count > 0, "answer_callback_query هرگز صدا زده نشد"
    return bot.answer_callback_query.await_args.kwargs


# ---------------------------------------------------------------------------
# بررسی کیبوردها
# ---------------------------------------------------------------------------


def buttons(markup: InlineKeyboardMarkup) -> list[InlineKeyboardButton]:
    """همه‌ی دکمه‌های کیبورد به‌صورت مسطح."""
    return [button for row in markup.inline_keyboard for button in row]


def callbacks(markup: InlineKeyboardMarkup) -> list[str]:
    """callback_data دکمه‌های callback‌دار به‌ترتیب نمایش (دکمه‌های URL حذف)."""
    return [button.callback_data for button in buttons(markup) if button.callback_data]


def url_buttons(markup: InlineKeyboardMarkup) -> list[tuple[str, str]]:
    """(label, url) همه‌ی دکمه‌های لینک‌دار به‌ترتیب نمایش."""
    return [(button.text, button.url) for button in buttons(markup) if button.url]


def main_menu_callbacks() -> list[str]:
    """callbackهای مورد انتظار منوی اصلی (بر اساس محتوا)."""
    return [item.callback for item in content.MAIN_MENU]


async def share_contact(
    app, bot, user=USER, phone: str = "+989121234567"
) -> None:
    """شبیه‌سازی فشردن دکمه‌ی «ارسال شماره تماس» (اشتراک مخاطب تلگرام)."""
    contact = Contact(
        phone_number=phone, first_name=user.first_name, user_id=user.id
    )
    message = Message(
        message_id=_next_id(),
        date=datetime.now(tz=timezone.utc),
        chat=CHAT,
        from_user=user,
        contact=contact,
    )
    message.set_bot(bot)
    await app.process_update(Update(update_id=_next_id(), message=message))

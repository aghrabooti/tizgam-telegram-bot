"""جمع‌آوری شماره‌ی تماس کاربران
================================

جریان:
1. اولین ``/start`` کاربر (وقتی هنوز شماره نداده و رد هم نکرده) →
   پیام درخواست شماره با دکمه‌ی «📱 ارسال شماره تماس» (اشتراک مخاطبِ
   بومی تلگرام با ``request_contact=True``) + دکمه‌ی «⏭ بعداً».
2. کاربر مخاطبش را می‌فرستد → شماره نرمال‌سازی و ذخیره می‌شود؛
   یا شماره را دستی تایپ می‌کند (ارقام فارسی هم پذیرفته است)؛
   یا «بعداً» را می‌زند و دیگر پرسیده نمی‌شود.
3. در هر سه حالت، کیبورد درخواست برداشته می‌شود و منوی اصلی می‌آید.

پیام‌های این بخش از ``bot/config/content.py`` خوانده می‌شوند.
"""

from __future__ import annotations

from telegram import KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove, Update
from telegram.constants import ParseMode
from telegram.ext import Application, ContextTypes, MessageHandler, filters

from bot.config import content
from bot.services import analytics, navigation
from bot.utils.phone import normalize_phone


async def send_phone_request(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """ارسال پیام درخواست شماره با کیبورد اشتراک مخاطب تلگرام."""
    keyboard = ReplyKeyboardMarkup(
        [
            [KeyboardButton(content.LBL_SHARE_CONTACT, request_contact=True)],
            [KeyboardButton(content.LBL_PHONE_LATER)],
        ],
        resize_keyboard=True,
        one_time_keyboard=True,
    )
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=content.PHONE_REQUEST_TEXT,
        parse_mode=ParseMode.HTML,
        reply_markup=keyboard,
    )


async def _finish(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str) -> None:
    """پایان جریان: برداشتن کیبورد درخواست + نمایش منوی اصلی."""
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=text,
        parse_mode=ParseMode.HTML,
        reply_markup=ReplyKeyboardRemove(),
    )
    await navigation.show_main_menu(update, context)


async def on_contact(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """دریافت مخاطب به‌اشتراک‌گذاشته‌شده توسط کاربر."""
    message = update.message
    user = message.from_user
    phone = normalize_phone(message.contact.phone_number)

    if phone is None:
        await context.bot.send_message(
            chat_id=update.effective_chat.id, text=content.PHONE_INVALID_TEXT
        )
        return await send_phone_request(update, context)

    analytics.set_phone(user.id, phone, source="contact")
    await _finish(update, context, content.PHONE_THANKS_TEXT)


class _PhoneFlowFilter(filters.MessageFilter):
    """فقط وقتی فعال است که کاربر در انتظار شماره است و متنش مرتبط است."""

    def filter(self, message) -> bool:
        user = message.from_user
        if user is None or message.text is None:
            return False
        if not analytics.needs_phone(user.id):
            return False
        text = message.text.strip()
        return text == content.LBL_PHONE_LATER or normalize_phone(text) is not None


async def on_phone_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """متن‌های مرتبط با جریان شماره: «بعداً» یا شماره‌ی تایپ‌شده."""
    message = update.message
    user = message.from_user
    text = message.text.strip()

    if text == content.LBL_PHONE_LATER:
        analytics.set_phone_skipped(user.id)
        return await _finish(update, context, content.PHONE_LATER_ACK_TEXT)

    phone = normalize_phone(text)
    if phone is not None:
        analytics.set_phone(user.id, phone, source="manual")
        return await _finish(update, context, content.PHONE_THANKS_TEXT)

    # متن غیرمرتبط بود (فیلتر نباید اجازه می‌داد؛ محض احتیاط)


def register(app: Application) -> None:
    # مخاطب به‌اشتراک‌گذاشته‌شده (گروه ۰)
    app.add_handler(MessageHandler(filters.CONTACT, on_contact))
    # متن «بعداً» یا شماره‌ی دستی (گروه ۱ — قبل از fallback عمومی)
    app.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND & _PhoneFlowFilter(), on_phone_text),
        group=1,
    )

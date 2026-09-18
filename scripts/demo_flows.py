"""دموی تعاملی ربات تیزگام (بدون نیاز به توکن و شبکه)
=====================================================

این اسکریپت همان «تست دستی» flowها است: کاربر ساختگی، /start می‌زند،
دکمه‌ها را می‌فشارد و متن/کیبورد هر صفحه همان‌طور که کاربر واقعی در
تلگرام می‌بیند چاپ می‌شود.

اجرا::

    python scripts/demo_flows.py
"""

from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ.setdefault("BOT_TOKEN", "123456:DEMO-TOKEN")
# کاربر تست (id=777) برای سناریوی پنل مدیریت، مدیر است
os.environ.setdefault("ADMIN_IDS", "777")
os.environ["DATABASE_PATH"] = "/tmp/demo_flows.db"
if os.path.exists(os.environ["DATABASE_PATH"]):
    os.remove(os.environ["DATABASE_PATH"])
# فایل لاگ نمونه برای صفحه‌ی «لاگ‌ها»ی پنل مدیریت
os.environ["LOG_FILE"] = "/tmp/demo_flows.log"
Path(os.environ["LOG_FILE"]).write_text(
    "2026-09-19 10:12:03 | INFO | راه‌اندازی ربات تیزگام (نسخه 1.1.0)\n"
    "2026-09-19 10:12:05 | INFO | شروع polling تلگرام\n"
    "2026-09-19 10:14:41 | INFO | ثبت شماره تماس جدید: +989121234567\n",
    encoding="utf-8",
)

from unittest.mock import AsyncMock, create_autospec  # noqa: E402

from telegram.ext._extbot import ExtBot  # noqa: E402

from bot.config import content  # noqa: E402
from bot.main import create_application  # noqa: E402
from tests.helpers import send_command, share_contact, tap  # noqa: E402

LINE = "─" * 62


def describe(markup) -> None:
    if markup is None:
        return
    if not hasattr(markup, "inline_keyboard"):
        # کیبورد پاسخ (مثل دکمه‌ی اشتراک مخاطب)
        for row in markup.keyboard:
            parts = []
            for b in row:
                tag = " 🔂(اشتراک مخاطب)" if getattr(b, "request_contact", False) else ""
                parts.append(f"[{b.text}{tag}]")
            print("   " + "  ".join(parts))
        return
    for row in markup.inline_keyboard:
        parts = []
        for button in row:
            if button.url:
                parts.append(f"[{button.text} → {button.url}]")
            else:
                parts.append(f"[{button.text} 〈{button.callback_data}〉]")
        print("   " + "  ".join(parts))


def screen(title: str, text: str, markup) -> None:
    print(f"\n{LINE}\n▶ {title}\n{LINE}")
    print(text)
    print()
    describe(markup)


async def run_scenario(app, bot, name: str, steps: list[str], command: str | None = None) -> None:
    print(f"\n\n{'═' * 62}\n  سناریو: {name}\n{'═' * 62}")
    if command:
        send_count = bot.send_message.await_count
        await send_command(app, bot, command)
        kwargs = bot.send_message.await_args_list[send_count].kwargs
        screen(f"دستور {command}", kwargs["text"], kwargs["reply_markup"])
        if kwargs["text"] == content.PHONE_REQUEST_TEXT:
            await share_contact(app, bot)
            thanks = bot.send_message.await_args_list[-2].kwargs
            menu = bot.send_message.await_args_list[-1].kwargs
            screen("📱 کاربر دکمه‌ی «ارسال شماره تماس» را زد", thanks["text"], None)
            screen("سپس منوی اصلی", menu["text"], menu["reply_markup"])
    for step in steps:
        bot.edit_message_text.reset_mock()
        await tap(app, bot, step)
        kwargs = bot.edit_message_text.await_args.kwargs
        screen(f"کلیک روی «{step}»", kwargs["text"], kwargs["reply_markup"])


async def main() -> None:
    app = create_application()
    bot = create_autospec(ExtBot, instance=True)
    bot.edit_message_text = AsyncMock()
    app.bot = bot
    app.updater = None
    await app.initialize()

    await run_scenario(
        app, bot, "/start → منوی اصلی", steps=[], command="/start"
    )
    await run_scenario(
        app,
        bot,
        "درباره موسسه",
        steps=["about"],
    )
    await run_scenario(
        app,
        bot,
        "ویدیو قبولی‌های تیزگام",
        steps=["vid:acc"],
    )
    await run_scenario(
        app,
        bot,
        "ویدیو رضایت‌های تیزپک",
        steps=["vid:sat"],
    )
    await run_scenario(
        app,
        bot,
        "محصولات: ششم/نهم → محصول",
        steps=["prod", "prod:g:6", "prod:g:6:tezpack", "main"],
    )
    await run_scenario(
        app,
        bot,
        "پشتیبانی: تماس / تلگرام",
        steps=["sup", "sup:call", "sup:tg", "main"],
    )
    await run_scenario(
        app,
        bot,
        "خرید تیزپک",
        steps=["buy"],
    )
    await run_scenario(
        app,
        bot,
        "نمونه کلاس: ششم → ریاضی → آپارات (+ بازگشت مرحله‌به‌مرحله)",
        steps=[
            "cls",
            "cls:g:6",
            "cls:g:6:math",
            "cls:g:6",   # 🔙 بازگشت به لیست درس‌ها
            "cls",       # 🔙 بازگشت به انتخاب پایه
            "main",      # 🏠 منوی اصلی
        ],
    )
    await run_scenario(
        app,
        bot,
        "نمونه کلاس: نهم → شیمی",
        steps=["cls", "cls:g:9", "cls:g:9:chemistry"],
    )
    await run_scenario(
        app,
        bot,
        "نمونه آزمون: نهم → آزمون (+ بازگشت)",
        steps=["exm", "exm:g:9", "exm:g:9:sample-1", "exm:g:9", "main"],
    )
    await run_scenario(
        app,
        bot,
        "رسانه‌های تیزگام",
        steps=["media"],
    )
    await run_scenario(
        app,
        bot,
        "حالت مرزی: دکمه‌ی منقضی و callback ناشناخته",
        steps=["cls:g:99", "totally:bogus"],
    )

    await run_scenario(
        app,
        bot,
        "پنل مدیریت: آمار / کاربران / لاگ‌ها / دیتابیس (فقط مدیران)",
        steps=[
            "adm",
            "adm:stats",
            "adm:users",
            "adm:logs",
            "adm:db",
            "adm",  # 🏠 بازگشت به منوی پنل
        ],
    )

    await app.shutdown()
    print(f"\n{'═' * 62}\n✅ دموی همه‌ی سناریوها با موفقیت اجرا شد.\n{'═' * 62}")


if __name__ == "__main__":
    asyncio.run(main())

"""تست یکپارچه‌ی تمام مسیرهای (flow) ربات تیزگام.

هر تست، کاربر را دقیقاً مثل تلگرام شبیه‌سازی می‌کند (ارسال دستور یا
فشردن دکمه‌ی inline) و متن/کیبورد صفحه‌ی نتیجه را بررسی می‌کند.

پوشش:
- /start → منوی اصلی
- همه‌ی ۹ بخش منوی اصلی
- نمونه کلاس: ششم/نهم → درس → لینک آپارات
- نمونه آزمون: ششم/نهم → آزمون → لینک
- محصولات: ششم/نهم → محصول → لینک سفارش
- پشتیبانی: تماس/تلگرام
- رسانه‌ها: تلگرام/اینستاگرام/بله/روبیکا/ایتا/سایت
- همه‌ی دکمه‌های بازگشت و منوی اصلی
- حالت‌های مرزی: دکمه‌ی منقضی، callback ناشناخته، متن نامفهوم
"""

from __future__ import annotations

from bot.config import content
from bot.constants import (
    CB_CLASSES_GRADE,
    CB_EXAMS_GRADE,
    CB_PRODUCTS_GRADE,
)
from tests.helpers import (
    callbacks,
    last_answer,
    last_edit,
    last_send,
    main_menu_callbacks,
    send_command,
    send_text,
    tap,
    url_buttons,
)

# ---------------------------------------------------------------------------
# /start و منوی اصلی
# ---------------------------------------------------------------------------


async def test_start_shows_main_menu(bot_app):
    app, bot = bot_app
    await send_command(app, bot, "/start")

    sent = last_send(bot)
    assert sent["text"] == content.WELCOME_TEXT
    assert sent["reply_markup"] is not None
    assert callbacks(sent["reply_markup"]) == main_menu_callbacks()
    assert len(main_menu_callbacks()) == 9


async def test_start_from_deep_state_resets_to_main_menu(bot_app):
    """/start در هر مرحله‌ای → reset کامل و بازگشت به منوی اصلی."""
    app, bot = bot_app
    # کاربر را تا عمیق‌ترین مرحله می‌بریم
    await tap(app, bot, "cls")
    await tap(app, bot, "cls:g:6")
    await tap(app, bot, "cls:g:6:math")
    assert "ریاضی" in last_edit(bot)["text"]

    # حالا /start
    await send_command(app, bot, "/start")
    sent = last_send(bot)
    assert sent["text"] == content.WELCOME_TEXT
    assert callbacks(sent["reply_markup"]) == main_menu_callbacks()


async def test_main_menu_button_edits_same_message(bot_app):
    """دکمه‌ی منوی اصلی، همان پیام را ویرایش می‌کند (پیام جدید نمی‌فرستد)."""
    app, bot = bot_app
    send_count_before = bot.send_message.await_count

    await tap(app, bot, "about")
    await tap(app, bot, "main")

    edited = last_edit(bot)
    assert edited["text"] == content.WELCOME_TEXT
    assert callbacks(edited["reply_markup"]) == main_menu_callbacks()
    assert bot.send_message.await_count == send_count_before  # بدون پیام جدید


async def test_every_callback_query_is_answered(bot_app):
    """هر کلیک باید callback query را answer کند (بدون loading بی‌پایان)."""
    app, bot = bot_app
    for data in ("about", "vid:acc", "vid:sat", "prod", "sup", "buy", "cls", "exm", "media"):
        await tap(app, bot, data)
    assert bot.answer_callback_query.await_count == 9


# ---------------------------------------------------------------------------
# ۱) درباره موسسه
# ---------------------------------------------------------------------------


async def test_about_flow(bot_app):
    app, bot = bot_app
    await tap(app, bot, "about")

    edited = last_edit(bot)
    assert edited["text"] == content.ABOUT_SECTION.text
    assert url_buttons(edited["reply_markup"]) == [
        (item.label, item.url) for item in content.ABOUT_SECTION.items
    ]
    # سطح ۱ → فقط «بازگشت به منوی اصلی»
    assert callbacks(edited["reply_markup"]) == ["main"]


# ---------------------------------------------------------------------------
# ۲) ویدیو قبولی‌ها و ۳) ویدیو رضایت‌های تیزپک
# ---------------------------------------------------------------------------


async def test_acceptance_videos_flow(bot_app):
    app, bot = bot_app
    await tap(app, bot, "vid:acc")

    edited = last_edit(bot)
    assert edited["text"] == content.ACCEPTANCE_VIDEOS_SECTION.text
    assert url_buttons(edited["reply_markup"]) == [
        (item.label, item.url) for item in content.ACCEPTANCE_VIDEOS_SECTION.items
    ]
    assert callbacks(edited["reply_markup"]) == ["main"]


async def test_satisfaction_videos_flow(bot_app):
    app, bot = bot_app
    await tap(app, bot, "vid:sat")

    edited = last_edit(bot)
    assert edited["text"] == content.SATISFACTION_VIDEOS_SECTION.text
    assert url_buttons(edited["reply_markup"]) == [
        (item.label, item.url) for item in content.SATISFACTION_VIDEOS_SECTION.items
    ]
    assert callbacks(edited["reply_markup"]) == ["main"]


# ---------------------------------------------------------------------------
# ۴) محصولات پایه ششم و نهم
# ---------------------------------------------------------------------------


async def test_products_flow(bot_app):
    app, bot = bot_app

    # مرحله ۱: انتخاب پایه
    await tap(app, bot, "prod")
    edited = last_edit(bot)
    assert edited["text"] == content.PRODUCTS_INTRO_TEXT
    assert callbacks(edited["reply_markup"]) == ["prod:g:6", "prod:g:9", "main"]

    # مرحله ۲: محصولات پایه نهم
    await tap(app, bot, "prod:g:9")
    edited = last_edit(bot)
    expected = [
        f"prod:g:9:{product.id}" for product in content.get_products("9")
    ] + ["prod:g:9", "main"]
    assert callbacks(edited["reply_markup"]) == expected

    # مرحله ۳: جزئیات محصول + لینک سفارش
    product = content.get_product("9", "tezpack")
    await tap(app, bot, "prod:g:9:tezpack")
    edited = last_edit(bot)
    assert product.title in edited["text"]
    assert product.price in edited["text"]
    assert url_buttons(edited["reply_markup"]) == [
        (content.LBL_ORDER_PRODUCT, product.order_url)
    ]
    assert callbacks(edited["reply_markup"]) == ["prod:g:9", "main"]


async def test_products_back_navigation(bot_app):
    app, bot = bot_app
    await tap(app, bot, "prod")
    await tap(app, bot, "prod:g:6")

    # بازگشت از جزئیات محصول → لیست محصولات همان پایه
    product = content.get_products("6")[0]
    await tap(app, bot, f"prod:g:6:{product.id}")
    await tap(app, bot, CB_PRODUCTS_GRADE.format(grade_id="6"))

    edited = last_edit(bot)
    assert edited["text"] == content.PRODUCTS_GRADE_TEXT.format(grade_title="پایه ششم")
    assert callbacks(edited["reply_markup"]) == [
        f"prod:g:6:{p.id}" for p in content.get_products("6")
    ] + ["prod:g:6", "main"]

    # بازگشت از لیست محصولات → انتخاب پایه
    await tap(app, bot, "prod")
    edited = last_edit(bot)
    assert edited["text"] == content.PRODUCTS_INTRO_TEXT


# ---------------------------------------------------------------------------
# ۵) پشتیبانی
# ---------------------------------------------------------------------------


async def test_support_flow(bot_app):
    app, bot = bot_app

    # انتخاب روش پشتیبانی
    await tap(app, bot, "sup")
    edited = last_edit(bot)
    assert edited["text"] == content.SUPPORT_MENU_TEXT
    assert callbacks(edited["reply_markup"]) == ["sup:call", "sup:tg", "main"]

    # پشتیبانی با تماس → نمایش شماره تماس
    await tap(app, bot, "sup:call")
    edited = last_edit(bot)
    assert edited["text"] == content.SUPPORT.call_text
    assert callbacks(edited["reply_markup"]) == ["main"]

    # پشتیبانی تلگرام → دکمه‌ی لینک اکانت پشتیبانی
    await tap(app, bot, "sup:tg")
    edited = last_edit(bot)
    assert edited["text"] == content.SUPPORT.telegram_text
    assert url_buttons(edited["reply_markup"]) == [
        (content.LBL_SUPPORT_CHAT, content.SUPPORT.telegram_url)
    ]
    assert callbacks(edited["reply_markup"]) == ["main"]


# ---------------------------------------------------------------------------
# ۶) خرید تیزپک
# ---------------------------------------------------------------------------


async def test_purchase_flow(bot_app):
    app, bot = bot_app
    await tap(app, bot, "buy")

    edited = last_edit(bot)
    assert edited["text"] == content.PURCHASE_SECTION.text
    assert url_buttons(edited["reply_markup"]) == [
        (item.label, item.url) for item in content.PURCHASE_SECTION.items
    ]
    assert callbacks(edited["reply_markup"]) == ["main"]


# ---------------------------------------------------------------------------
# ۷) نمونه کلاس‌ها: پایه → درس → لینک آپارات
# ---------------------------------------------------------------------------


async def test_sample_classes_flow_grade_6(bot_app):
    app, bot = bot_app

    # مرحله ۱: انتخاب پایه
    await tap(app, bot, "cls")
    edited = last_edit(bot)
    assert edited["text"] == content.CLASSES_INTRO_TEXT
    assert callbacks(edited["reply_markup"]) == ["cls:g:6", "cls:g:9", "main"]

    # مرحله ۲: درس‌های پایه ششم
    await tap(app, bot, "cls:g:6")
    edited = last_edit(bot)
    grade = content.get_grade("6")
    assert edited["text"] == content.CLASSES_GRADE_TEXT.format(grade_title=grade.title)
    assert callbacks(edited["reply_markup"]) == [
        f"cls:g:6:{subject.id}" for subject in grade.subjects
    ] + ["cls:g:6", "main"]

    # مرحله ۳: لینک آپارات جلسه‌ی نمونه‌ی ریاضی
    math_subject = content.get_subject(grade, "math")
    await tap(app, bot, "cls:g:6:math")
    edited = last_edit(bot)
    assert "ریاضی" in edited["text"]
    assert url_buttons(edited["reply_markup"]) == [
        (content.LBL_WATCH_ON_APARAT, math_subject.aparat_url)
    ]
    assert callbacks(edited["reply_markup"]) == ["cls:g:6", "main"]


async def test_sample_classes_flow_grade_9(bot_app):
    app, bot = bot_app
    await tap(app, bot, "cls")
    await tap(app, bot, "cls:g:9")
    edited = last_edit(bot)

    grade = content.get_grade("9")
    assert callbacks(edited["reply_markup"]) == [
        f"cls:g:9:{subject.id}" for subject in grade.subjects
    ] + ["cls:g:9", "main"]

    science = content.get_subject(grade, "science")
    await tap(app, bot, "cls:g:9:science")
    edited = last_edit(bot)
    assert "علوم" in edited["text"]
    assert url_buttons(edited["reply_markup"]) == [
        (content.LBL_WATCH_ON_APARAT, science.aparat_url)
    ]


async def test_sample_classes_back_navigation(bot_app):
    """بازگشت مرحله‌به‌مرحله: درس → لیست درس‌ها → انتخاب پایه → منوی اصلی."""
    app, bot = bot_app
    await tap(app, bot, "cls")
    await tap(app, bot, "cls:g:6")
    await tap(app, bot, "cls:g:6:farsi")

    # بازگشت از درس → لیست درس‌های پایه ششم
    await tap(app, bot, CB_CLASSES_GRADE.format(grade_id="6"))
    edited = last_edit(bot)
    assert edited["text"] == content.CLASSES_GRADE_TEXT.format(grade_title="پایه ششم")

    # بازگشت از لیست درس‌ها → صفحه‌ی انتخاب پایه
    await tap(app, bot, "cls")
    edited = last_edit(bot)
    assert edited["text"] == content.CLASSES_INTRO_TEXT

    # بازگشت از ریشه بخش → منوی اصلی
    await tap(app, bot, "main")
    edited = last_edit(bot)
    assert edited["text"] == content.WELCOME_TEXT
    assert callbacks(edited["reply_markup"]) == main_menu_callbacks()


async def test_home_button_from_deep_screen(bot_app):
    """دکمه‌ی «منوی اصلی» از عمیق‌ترین مرحله مستقیم به منوی اصلی می‌رود."""
    app, bot = bot_app
    await tap(app, bot, "cls")
    await tap(app, bot, "cls:g:9")
    await tap(app, bot, "cls:g:9:arabic")
    await tap(app, bot, "main")

    edited = last_edit(bot)
    assert edited["text"] == content.WELCOME_TEXT
    assert callbacks(edited["reply_markup"]) == main_menu_callbacks()


# ---------------------------------------------------------------------------
# ۸) نمونه آزمون‌ها: پایه → آزمون → لینک
# ---------------------------------------------------------------------------


async def test_sample_exams_flow(bot_app):
    app, bot = bot_app

    await tap(app, bot, "exm")
    edited = last_edit(bot)
    assert edited["text"] == content.EXAMS_INTRO_TEXT
    assert callbacks(edited["reply_markup"]) == ["exm:g:6", "exm:g:9", "main"]

    await tap(app, bot, "exm:g:6")
    edited = last_edit(bot)
    grade = content.get_grade("6")
    assert edited["text"] == content.EXAMS_GRADE_TEXT.format(grade_title=grade.title)
    assert callbacks(edited["reply_markup"]) == [
        f"exm:g:6:{exam.id}" for exam in content.get_exams("6")
    ] + ["exm:g:6", "main"]

    exam = content.get_exam("6", "sample-1")
    await tap(app, bot, "exm:g:6:sample-1")
    edited = last_edit(bot)
    assert exam.title in edited["text"]
    assert url_buttons(edited["reply_markup"]) == [(content.LBL_OPEN_EXAM, exam.url)]
    assert callbacks(edited["reply_markup"]) == ["exm:g:6", "main"]


async def test_sample_exams_back_navigation(bot_app):
    app, bot = bot_app
    await tap(app, bot, "exm")
    await tap(app, bot, "exm:g:9")
    await tap(app, bot, "exm:g:9:sample-2")

    # بازگشت → لیست آزمون‌های پایه نهم
    await tap(app, bot, CB_EXAMS_GRADE.format(grade_id="9"))
    edited = last_edit(bot)
    assert callbacks(edited["reply_markup"]) == [
        f"exm:g:9:{exam.id}" for exam in content.get_exams("9")
    ] + ["exm:g:9", "main"]

    # بازگشت → انتخاب پایه
    await tap(app, bot, "exm")
    edited = last_edit(bot)
    assert edited["text"] == content.EXAMS_INTRO_TEXT

    # بازگشت → منوی اصلی
    await tap(app, bot, "main")
    edited = last_edit(bot)
    assert edited["text"] == content.WELCOME_TEXT


# ---------------------------------------------------------------------------
# ۹) رسانه‌های تیزگام
# ---------------------------------------------------------------------------


async def test_media_flow(bot_app):
    app, bot = bot_app
    await tap(app, bot, "media")

    edited = last_edit(bot)
    assert edited["text"] == content.MEDIA_SECTION.text
    # شش رسانه: تلگرام/اینستاگرام/بله/روبیکا/ایتا/سایت — همه با لینک درست
    assert url_buttons(edited["reply_markup"]) == [
        (item.label, item.url) for item in content.MEDIA_SECTION.items
    ]
    labels = [label for label, _ in url_buttons(edited["reply_markup"])]
    assert len(labels) == 6
    for keyword in ("تلگرام", "اینستاگرام", "بله", "روبیکا", "ایتا", "سایت"):
        assert any(keyword in label for label in labels), f"رسانه «{keyword}» پیدا نشد"
    assert callbacks(edited["reply_markup"]) == ["main"]


# ---------------------------------------------------------------------------
# حالت‌های مرزی
# ---------------------------------------------------------------------------


async def test_stale_grade_shows_alert_and_returns_to_main_menu(bot_app):
    """پایه‌ی نامعتبر (مثلاً پس از تغییر کانفیگ) → هشدار + منوی اصلی."""
    app, bot = bot_app
    await tap(app, bot, "cls:g:99")

    answered = last_answer(bot)
    assert answered["show_alert"] is True
    assert answered["text"] == content.STALE_BUTTON_TEXT

    edited = last_edit(bot)
    assert edited["text"] == content.WELCOME_TEXT
    assert callbacks(edited["reply_markup"]) == main_menu_callbacks()
    # پاسخ دوباره به همان query نباید داده شود
    assert bot.answer_callback_query.await_count == 1


async def test_stale_subject_shows_alert(bot_app):
    app, bot = bot_app
    await tap(app, bot, "cls:g:6:nonexistent")
    assert last_answer(bot)["show_alert"] is True
    assert last_edit(bot)["text"] == content.WELCOME_TEXT


async def test_unknown_callback_shows_alert_and_main_menu(bot_app):
    """callback کاملاً ناشناخته → هشدار + منوی اصلی."""
    app, bot = bot_app
    await tap(app, bot, "totally:bogus:data")

    assert last_answer(bot)["show_alert"] is True
    assert last_edit(bot)["text"] == content.WELCOME_TEXT
    assert callbacks(last_edit(bot)["reply_markup"]) == main_menu_callbacks()


async def test_plain_text_shows_fallback_menu(bot_app):
    app, bot = bot_app
    await send_text(app, bot, "سلام")

    sent = last_send(bot)
    assert content.FALLBACK_TEXT in sent["text"]
    assert callbacks(sent["reply_markup"]) == main_menu_callbacks()


async def test_all_screens_have_navigation(bot_app):
    """همه‌ی صفحه‌های میانی باید دکمه‌ی بازگشت/منوی اصلی داشته باشند."""
    app, bot = bot_app
    level1 = ["about", "vid:acc", "vid:sat", "prod", "sup", "buy", "cls", "exm", "media"]
    for data in level1:
        await tap(app, bot, data)
        edited = last_edit(bot)
        assert "main" in callbacks(edited["reply_markup"]), f"بدون منوی اصلی: {data}"

    level2 = [
        "prod:g:6", "prod:g:9",
        "cls:g:6", "cls:g:9",
        "exm:g:6", "exm:g:9",
        "sup:call", "sup:tg",
    ]
    for data in level2:
        await tap(app, bot, data)
        edited = last_edit(bot)
        assert "main" in callbacks(edited["reply_markup"]), f"بدون منوی اصلی: {data}"

"""
محتوای قابل‌تنظیم ربات تیزگام
==============================

⚠️⚠️⚠️  هشدار مهم  ⚠️⚠️⚠️
این فایل تنها جایی است که مدیر پروژه برای تغییر «متن‌ها، لینک‌ها،
شماره‌ها، محصولات، درس‌ها و شبکه‌های اجتماعی» باید آن را ویرایش کند.

تمام مقادیر لینک/شماره‌ی موجود در این فایل در حال حاضر PLACEHOLDER هستند؛
پیش از استقرار، مقادیر واقعی را از موسسه دریافت و جایگزین کنید.

قواعد:
- هیچ لینک یا متن کاربرپسندی در هندلرها/کیبوردها hard-code نشده است.
- متن‌ها با فرمت HTML نوشته می‌شوند (parse_mode ربات HTML است).
- برای افزودن پایه/درس/محصول/آزمون جدید فقط همین فایل را ویرایش کنید؛
  منطق ربات به‌صورت خودکار دکمه‌های مربوطه را می‌سازد.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from bot.constants import (
    CB_ABOUT,
    CB_CLASSES,
    CB_EXAMS,
    CB_MEDIA,
    CB_PRODUCTS,
    CB_PURCHASE,
    CB_SUPPORT,
    CB_VIDEO_ACCEPTANCE,
    CB_VIDEO_SATISFACTION,
)

# ---------------------------------------------------------------------------
# مدل‌های داده‌ی محتوا
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class MenuItem:
    """یک دکمه‌ی منوی اصلی."""

    label: str
    callback: str


@dataclass(frozen=True)
class LinkItem:
    """یک آیتم لینک‌دار (ویدیو، فایل، صفحه وب و ...) درون یک بخش محتوایی."""

    label: str
    url: str


@dataclass(frozen=True)
class ContentSection:
    """بخش محتوایی قابل‌تنظیم.

    متن اصلی بخش همیشه نمایش داده می‌شود؛ ``items`` به‌صورت دکمه‌ی URL
    زیر متن رندر می‌شوند و ``photo_url`` / ``video_url`` (اختیاری) به‌صورت
    یک پیام رسانه‌ای جداگانه بعد از صفحه ارسال می‌شوند.
    """

    text: str
    items: tuple[LinkItem, ...] = ()
    photo_url: Optional[str] = None
    video_url: Optional[str] = None


@dataclass(frozen=True)
class Subject:
    """یک درس + لینک جلسه‌ی نمونه کلاس آن در آپارات."""

    id: str
    title: str
    emoji: str
    aparat_url: str


@dataclass(frozen=True)
class Grade:
    """یک پایه‌ی تحصیلی به‌همراه درس‌های آن."""

    id: str
    title: str
    emoji: str
    subjects: tuple[Subject, ...]


@dataclass(frozen=True)
class Product:
    """یک محصول قابل فروش."""

    id: str
    title: str
    description: str
    price: str
    order_url: str


@dataclass(frozen=True)
class Exam:
    """یک نمونه‌آزمون."""

    id: str
    title: str
    url: str


@dataclass(frozen=True)
class SupportConfig:
    """تنظیمات بخش پشتیبانی."""

    call_text: str
    telegram_text: str
    telegram_url: str


# ---------------------------------------------------------------------------
# برچسب‌های عمومی دکمه‌ها
# ---------------------------------------------------------------------------

LBL_BACK = "🔙 بازگشت"
LBL_HOME = "🏠 منوی اصلی"
LBL_BACK_TO_MAIN = "🔙 بازگشت به منوی اصلی"
LBL_WATCH_ON_APARAT = "▶️ تماشا در آپارات"
LBL_OPEN_EXAM = "📄 مشاهده / دانلود آزمون"
LBL_ORDER_PRODUCT = "🛒 ثبت سفارش"
LBL_SUPPORT_CALL = "📞 پشتیبانی با تماس"
LBL_SUPPORT_TELEGRAM = "💬 پشتیبانی تلگرام"
LBL_SUPPORT_CHAT = "💬 گفت‌وگو با پشتیبانی"

INSTITUTE_NAME = "موسسه تیزهوشان تیزگام"

# ---------------------------------------------------------------------------
# منوی اصلی
# ---------------------------------------------------------------------------

WELCOME_TEXT = (
    "🎓 <b>موسسه تیزهوشان تیزگام</b>\n\n"
    "به ربات رسمی موسسه تیزهوشان تیزگام خوش آمدید 👋\n\n"
    "🎯 هدف ما هموار کردن مسیر قبولی شما در آزمون ورودی مدارس تیزهوشان است.\n\n"
    "از منوی زیر گزینه‌ی مورد نظر خود را انتخاب کنید:"
)

MAIN_MENU: tuple[MenuItem, ...] = (
    MenuItem("🏛 درباره موسسه تیزهوشان تیزگام", CB_ABOUT),
    MenuItem("🎓 ویدیو قبولی‌های تیزگام", CB_VIDEO_ACCEPTANCE),
    MenuItem("💬 ویدیو رضایت‌های تیزپک", CB_VIDEO_SATISFACTION),
    MenuItem("📚 محصولات پایه ششم و نهم", CB_PRODUCTS),
    MenuItem("🛠 پشتیبانی", CB_SUPPORT),
    MenuItem("🛒 خرید تیزپک", CB_PURCHASE),
    MenuItem("🎬 مشاهده نمونه کلاس‌های تیزگام", CB_CLASSES),
    MenuItem("📝 مشاهده نمونه آزمون تیزگام", CB_EXAMS),
    MenuItem("🌐 لینک رسانه‌های تیزگام", CB_MEDIA),
)

# متن پاسخ به پیام‌های نامفهوم (غیر دستوری)
FALLBACK_TEXT = (
    "🙏 متوجه پیام شما نشدیم.\n\n"
    "از منوی زیر انتخاب کنید یا با زدن /start به منوی اصلی بازگردید:"
)

# هشدار دکمه‌ی منقضی (مثلاً پس از تغییر کانفیگ و کلیک روی دکمه‌ی قدیمی)
STALE_BUTTON_TEXT = "این دکمه دیگر فعال نیست؛ به منوی اصلی بازگردانده شدید."

# ---------------------------------------------------------------------------
# ۱) درباره موسسه
# ---------------------------------------------------------------------------

ABOUT_SECTION = ContentSection(
    text=(
        "🏛 <b>درباره موسسه تیزهوشان تیزگام</b>\n\n"
        "موسسه تیزهوشان تیزگام با گردهم‌آوردن بسته‌ی کامل آموزشی، آزمون‌های"
        " هدفمند و مشاوره‌ی تخصصی، مسیر آمادگی دانش‌آموزان پایه‌های ششم و نهم"
        " را برای قبولی در مدارس تیزهوشان و نمونه‌دولتی هموار می‌کند.\n\n"
        "✅ تدریس اساتید مجرب و برتر\n"
        "✅ پک آموزشی جامع «تیزپک»\n"
        "✅ آزمون‌های آزمایشی استاندارد با تحلیل دقیق\n"
        "✅ پشتیبانی و مشاوره‌ی اختصاصی تا روز آزمون\n\n"
        "برای اطلاعات بیشتر، وبسایت ما را ببینید:"
    ),
    items=(
        LinkItem("🌐 وبسایت رسمی تیزگام", "https://tizgam.ir"),
        # LinkItem("🎥 ویدیوی معرفی موسسه", "https://www.aparat.com/tizgam"),
    ),
)

# ---------------------------------------------------------------------------
# ۲) ویدیو قبولی‌های تیزگام  /  ۳) ویدیو رضایت‌های تیزپک
# ---------------------------------------------------------------------------

ACCEPTANCE_VIDEOS_SECTION = ContentSection(
    text=(
        "🎓 <b>ویدیو قبولی‌های تیزگام</b>\n\n"
        "لحظه‌های موفقیت رتبه‌های برتر تیزگام را ببینید؛ همین مسیر برای شما"
        " هم ممکن است! 🏆"
    ),
    items=(
        LinkItem("🏆 قبولی‌های تیزهوشان ۱۴۰۳", "https://www.aparat.com/tizgam"),
        LinkItem("🥇 رتبه‌های برتر پایه نهم", "https://www.aparat.com/tizgam"),
        LinkItem("🎖 ایشان هم قبول شدند!", "https://www.aparat.com/tizgam"),
    ),
)

SATISFACTION_VIDEOS_SECTION = ContentSection(
    text=(
        "💬 <b>ویدیو رضایت‌های تیزپک</b>\n\n"
        "دانش‌آموزان و خانواده‌های آن‌ها درباره‌ی پک آموزشی «تیزپک» چه"
        " می‌گویند؟ 👇"
    ),
    items=(
        LinkItem("👨‍👩‍👦 رضایت والدین", "https://www.aparat.com/tizgam"),
        LinkItem("🧑‍🎓 رضایت دانش‌آموزان", "https://www.aparat.com/tizgam"),
    ),
)

# ---------------------------------------------------------------------------
# ۴) محصولات پایه ششم و نهم
# ---------------------------------------------------------------------------

PRODUCTS_INTRO_TEXT = (
    "📚 <b>محصولات تیزگام</b>\n\n"
    "پایه‌ی مورد نظر را انتخاب کنید:"
)

PRODUCTS_GRADE_TEXT = (
    "📚 <b>محصولات {grade_title}</b>\n\n"
    "برای مشاهده‌ی جزئیات و ثبت سفارش، محصول را انتخاب کنید:"
)

PRODUCT_DETAIL_TEXT = (
    "📦 <b>{title}</b>\n"
    "🎓 {grade_title}\n\n"
    "{description}\n\n"
    "💰 قیمت: {price}"
)

# برای هر پایه هر تعداد محصول که لازم بود اضافه کنید؛
# دکمه‌ها به‌صورت خودکار ساخته می‌شوند.
GRADES: tuple[Grade, ...] = (
    Grade(
        id="6",
        title="پایه ششم",
        emoji="🎒",
        subjects=(
            Subject("math", "ریاضی", "➗", "https://www.aparat.com/tizgam"),
            Subject("geometry", "هندسه", "📐", "https://www.aparat.com/tizgam"),
            Subject("science", "علوم تجربی", "🔬", "https://www.aparat.com/tizgam"),
            Subject("farsi", "فارسی", "📖", "https://www.aparat.com/tizgam"),
            Subject("arabic", "عربی", "✍️", "https://www.aparat.com/tizgam"),
        ),
    ),
    Grade(
        id="9",
        title="پایه نهم",
        emoji="🧭",
        subjects=(
            Subject("math", "ریاضی", "➗", "https://www.aparat.com/tizgam"),
            Subject("geometry", "هندسه", "📐", "https://www.aparat.com/tizgam"),
            Subject("science", "علوم تجربی", "🔬", "https://www.aparat.com/tizgam"),
            Subject("chemistry", "شیمی", "⚗️", "https://www.aparat.com/tizgam"),
            Subject("farsi", "فارسی", "📖", "https://www.aparat.com/tizgam"),
            Subject("arabic", "عربی", "✍️", "https://www.aparat.com/tizgam"),
        ),
    ),
)

PRODUCTS_BY_GRADE: dict[str, tuple[Product, ...]] = {
    "6": (
        Product(
            id="tezpack",
            title="تیزپک پایه ششم",
            description=(
                "پک جامع آمادگی آزمون تیزهوشان پایه ششم شامل ویدیوهای آموزشی"
                " کامل، جزوات رنگی، بانک تست و آزمون‌های آزمایشی."
            ),
            price="۱٬۴۸۰٬۰۰۰ تومان",
            order_url="https://tizgam.ir/order/tezpack-6",
        ),
        Product(
            id="mock-exams",
            title="آزمون‌های آزمایشی تیزهوشان ششم",
            description=(
                "دوره‌ی آزمون‌های آزمایشی استاندارد با کاربرگ تحلیلی و رتبه‌بندی"
                " کشوری."
            ),
            price="۶۹۰٬۰۰۰ تومان",
            order_url="https://tizgam.ir/order/exams-6",
        ),
    ),
    "9": (
        Product(
            id="tezpack",
            title="تیزپک پایه نهم",
            description=(
                "پک جامع آمادگی آزمون تیزهوشان پایه نهم شامل ویدیوهای آموزشی"
                " کامل، جزوات رنگی، بانک تست و آزمون‌های آزمایشی."
            ),
            price="۱٬۶۸۰٬۰۰۰ تومان",
            order_url="https://tizgam.ir/order/tezpack-9",
        ),
        Product(
            id="mock-exams",
            title="آزمون‌های آزمایشی تیزهوشان نهم",
            description=(
                "دوره‌ی آزمون‌های آزمایشی استاندارد با کاربرگ تحلیلی و رتبه‌بندی"
                " کشوری."
            ),
            price="۷۹۰٬۰۰۰ تومان",
            order_url="https://tizgam.ir/order/exams-9",
        ),
    ),
}

# ---------------------------------------------------------------------------
# ۵) پشتیبانی
# ---------------------------------------------------------------------------

SUPPORT_MENU_TEXT = (
    "🛠 <b>پشتیبانی تیزگام</b>\n\n"
    "روش ارتباط مورد نظر را انتخاب کنید:"
)

SUPPORT = SupportConfig(
    call_text=(
        "📞 <b>پشتیبانی با تماس</b>\n\n"
        "برای ارتباط با بخش پشتیبانی موسسه تیزهوشان تیزگام با شماره‌ی زیر"
        " تماس بگیرید:\n\n"
        "☎️ <b>۰۲۱-۱۲۳۴۵۶۷۸</b>\n\n"
        "🕘 ساعت پاسخگویی: شنبه تا پنجشنبه، ۹ صبح تا ۶ عصر"
    ),
    telegram_text=(
        "💬 <b>پشتیبانی تلگرام</b>\n\n"
        "تیم پشتیبانی تیزگام در تلگرام آماده‌ی پاسخ‌گویی به سوالات شماست."
        " روی دکمه‌ی زیر بزنید تا به گفت‌وگو متصل شوید:"
    ),
    telegram_url="https://t.me/tizgam_support",
)

# ---------------------------------------------------------------------------
# ۶) خرید تیزپک
# ---------------------------------------------------------------------------

PURCHASE_SECTION = ContentSection(
    text=(
        "🛒 <b>خرید تیزپک</b>\n\n"
        "پک جامع آمادگی آزمون تیزهوشان؛ شامل ویدیوهای آموزشی کامل، جزوات"
        " رنگی، بانک تست تصحیح‌شده و آزمون‌های آزمایشی.\n\n"
        "💰 قیمت: <b>از ۱٬۴۸۰٬۰۰۰ تومان</b>\n\n"
        "برای خرید و ثبت سفارش، روی دکمه‌ی زیر بزنید. پس از ثبت سفارش،"
        " کارشناسان ما برای هماهنگی ارسال با شما تماس می‌گیرند. 🤝"
    ),
    items=(
        LinkItem("🛒 خرید / ثبت سفارش تیزپک", "https://tizgam.ir/order/tezpack"),
        LinkItem("💬 سوال قبل از خرید؟ پشتیبانی", "https://t.me/tizgam_support"),
    ),
)

# ---------------------------------------------------------------------------
# ۷) نمونه کلاس‌ها
# ---------------------------------------------------------------------------

CLASSES_INTRO_TEXT = (
    "🎬 <b>نمونه کلاس‌های تیزگام</b>\n\n"
    "پایه‌ی مورد نظر را انتخاب کنید:"
)

CLASSES_GRADE_TEXT = (
    "🎬 <b>نمونه کلاس‌های {grade_title}</b>\n\n"
    "درس مورد نظر را برای تماشای جلسه‌ی نمونه انتخاب کنید:"
)

CLASS_SUBJECT_TEXT = (
    "🎓 <b>نمونه کلاس {subject}</b>\n"
    "🎒 {grade_title}\n\n"
    "جلسه‌ی نمونه‌ی این درس را می‌توانید در آپارات تماشا کنید:"
)

# ---------------------------------------------------------------------------
# ۸) نمونه آزمون‌ها
# ---------------------------------------------------------------------------

EXAMS_INTRO_TEXT = (
    "📝 <b>نمونه آزمون تیزگام</b>\n\n"
    "پایه‌ی مورد نظر را انتخاب کنید:"
)

EXAMS_GRADE_TEXT = (
    "📝 <b>نمونه آزمون‌های {grade_title}</b>\n\n"
    "آزمون مورد نظر را برای مشاهده انتخاب کنید:"
)

EXAM_DETAIL_TEXT = (
    "📝 <b>{title}</b>\n"
    "🎓 {grade_title}\n\n"
    "این نمونه آزمون را می‌توانید به‌صورت آنلاین مشاهده یا دانلود کنید:"
)

EXAMS_BY_GRADE: dict[str, tuple[Exam, ...]] = {
    "6": (
        Exam(
            id="sample-1",
            title="نمونه آزمون ورودی تیزهوشان شماره ۱",
            url="https://tizgam.ir/exams/6/sample-1",
        ),
        Exam(
            id="sample-2",
            title="نمونه آزمون ورودی تیزهوشان شماره ۲",
            url="https://tizgam.ir/exams/6/sample-2",
        ),
    ),
    "9": (
        Exam(
            id="sample-1",
            title="نمونه آزمون ورودی تیزهوشان شماره ۱",
            url="https://tizgam.ir/exams/9/sample-1",
        ),
        Exam(
            id="sample-2",
            title="نمونه آزمون ورودی تیزهوشان شماره ۲",
            url="https://tizgam.ir/exams/9/sample-2",
        ),
    ),
}

# ---------------------------------------------------------------------------
# ۹) رسانه‌های تیزگام
# ---------------------------------------------------------------------------

MEDIA_SECTION = ContentSection(
    text=(
        "🌐 <b>رسانه‌های تیزگام</b>\n\n"
        "ما را در شبکه‌های اجتماعی دنبال کنید:"
    ),
    items=(
        LinkItem("📨 کانال تلگرام", "https://t.me/tizgam"),
        LinkItem("📸 پیج اینستاگرام", "https://instagram.com/tizgam"),
        LinkItem("🟣 کانال بله", "https://ble.ir/tizgam"),
        LinkItem("🔴 کانال روبیکا", "https://rubika.ir/tizgam"),
        LinkItem("🟢 کانال ایتا", "https://eitaa.com/tizgam"),
        LinkItem("🌍 سایت", "https://tizgam.ir"),
    ),
)


# ---------------------------------------------------------------------------
# توابع دسترسی (Accessor) — رابط یکنواخت برای بقیه‌ی کد
# ---------------------------------------------------------------------------

_GRADES_BY_ID = {grade.id: grade for grade in GRADES}


def get_grade(grade_id: str) -> Optional[Grade]:
    """پایه را بر اساس شناسه برمی‌گرداند (در صورت عدم وجود None)."""
    return _GRADES_BY_ID.get(grade_id)


def get_subject(grade: Grade, subject_id: str) -> Optional[Subject]:
    """درس را درون یک پایه بر اساس شناسه برمی‌گرداند."""
    return next((s for s in grade.subjects if s.id == subject_id), None)


def product_grades() -> tuple[Grade, ...]:
    """پایه‌هایی که برای آن‌ها محصول تعریف شده است (به‌ترتیب GRADES)."""
    return tuple(g for g in GRADES if g.id in PRODUCTS_BY_GRADE)


def get_products(grade_id: str) -> tuple[Product, ...]:
    """محصولات یک پایه (در صورت نبود، تاپل خالی)."""
    return PRODUCTS_BY_GRADE.get(grade_id, ())


def get_product(grade_id: str, product_id: str) -> Optional[Product]:
    """یک محصول مشخص را برمی‌گرداند."""
    return next((p for p in get_products(grade_id) if p.id == product_id), None)


def exam_grades() -> tuple[Grade, ...]:
    """پایه‌هایی که برای آن‌ها نمونه آزمون تعریف شده است."""
    return tuple(g for g in GRADES if g.id in EXAMS_BY_GRADE)


def get_exams(grade_id: str) -> tuple[Exam, ...]:
    """نمونه آزمون‌های یک پایه."""
    return EXAMS_BY_GRADE.get(grade_id, ())


def get_exam(grade_id: str, exam_id: str) -> Optional[Exam]:
    """یک نمونه آزمون مشخص را برمی‌گرداند."""
    return next((e for e in get_exams(grade_id) if e.id == exam_id), None)

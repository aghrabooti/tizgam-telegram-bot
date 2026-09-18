"""مدیریت محتوای قابل‌ویرایش از پنل مدیریت
==========================================

این ماژول پل بین «مقادیر پیش‌فرض» (``bot/config/content.py``) و «مقادیر
ویرایش‌شده‌ی مدیر» (جدول ``content_overrides`` در دیتابیس) است:

- در شروع برنامه، فهرست فیلدهای قابل‌ویرایش به‌صورت **پویا** از ساختارهای
  content ساخته می‌شود؛ در نتیجه افزودن محصول/درس/رسانه‌ی جدید در
  ``content.py`` به‌طور خودکار در پنل مدیریت هم ظاهر می‌شود.
- هر تغییر مدیر، هم در دیتابیس ذخیره می‌شود (ماندگار پس از ری‌استارت) و هم
  روی ماژول content اعمال می‌شود تا همه‌ی هندلرها مقدار جدید را ببینند.
- مقادیر متنی هنگام ذخیره HTML-escape می‌شوند تا صفحه‌ها هرگز نشکنند؛
  برای فرمت‌های خاص (بولد و ...) باید ``content.py`` ویرایش شود.
- «بازگردانی به پیش‌فرض» override را حذف و مقدار اصلی را برمی‌گرداند.
"""

from __future__ import annotations

import dataclasses
import html
import logging
import re
from dataclasses import dataclass
from datetime import datetime
from typing import Callable, Optional

from bot.config import content
from bot.services.database import get_db

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# مدل و گروه‌های ویرایش
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class EditableField:
    """یک فیلد قابل‌ویرایش (متن یا لینک) در محتوای ربات."""

    key: str
    group: str
    title: str
    kind: str  # "text" | "short" | "url"
    default: str
    get_current: Callable[[], str]
    apply: Callable[[str], None]


# عنوان گروه‌های ویرایش در پنل (به همین ترتیب نمایش داده می‌شوند)
EDIT_GROUP_TITLES: dict[str, str] = {
    "about": "🏛 درباره موسسه",
    "acceptance": "🎓 ویدیو قبولی‌ها",
    "satisfaction": "💬 ویدیو رضایت‌های تیزپک",
    "purchase": "🛒 خرید تیزپک",
    "media": "🌐 رسانه‌ها",
    "support": "🛠 پشتیبانی",
    "classes": "🎬 نمونه کلاس‌ها (آپارات)",
    "products": "📦 محصولات",
    "exams": "📝 نمونه آزمون‌ها",
}

KIND_LABELS = {"text": "متن", "short": "متن کوتاه", "url": "لینک"}

# بخش‌های محتوایی ایستا: (group_id, section_key, attr, عنوان)
_SECTIONS = (
    ("about", "about", "ABOUT_SECTION", "درباره موسسه"),
    ("acceptance", "acceptance", "ACCEPTANCE_VIDEOS_SECTION", "ویدیو قبولی‌ها"),
    ("satisfaction", "satisfaction", "SATISFACTION_VIDEOS_SECTION", "ویدیو رضایت‌های تیزپک"),
    ("purchase", "purchase", "PURCHASE_SECTION", "خرید تیزپک"),
    ("media", "media", "MEDIA_SECTION", "رسانه‌ها"),
)


# ---------------------------------------------------------------------------
# سازنده‌های اعمال تغییر روی ماژول content
# ---------------------------------------------------------------------------


def _section_item(section, item_id: str, part: str) -> str:
    return next(getattr(item, part) for item in section.items if item.id == item_id)


def _set_section_item(attr: str, item_id: str, part: str, value: str) -> None:
    section = getattr(content, attr)
    items = tuple(
        dataclasses.replace(item, **{part: value}) if item.id == item_id else item
        for item in section.items
    )
    setattr(content, attr, dataclasses.replace(section, items=items))


def _add_section_fields(
    fields: dict[str, EditableField], group: str, sec_key: str, attr: str, title: str
) -> None:
    section = getattr(content, attr)
    fields[f"{sec_key}:text"] = EditableField(
        key=f"{sec_key}:text",
        group=group,
        title=f"متن بخش «{title}»",
        kind="text",
        default=section.text,
        get_current=lambda a=attr: getattr(content, a).text,
        apply=lambda v, a=attr: setattr(
            content, a, dataclasses.replace(getattr(content, a), text=v)
        ),
    )
    for item in section.items:
        for part, part_title, kind in (
            ("label", "عنوان دکمه", "short"),
            ("url", "لینک دکمه", "url"),
        ):
            key = f"{sec_key}:item:{item.id}:{part}"
            fields[key] = EditableField(
                key=key,
                group=group,
                title=f"{part_title} «{item.label}» — {title}",
                kind=kind,
                default=getattr(item, part),
                get_current=lambda a=attr, iid=item.id, p=part: _section_item(
                    getattr(content, a), iid, p
                ),
                apply=lambda v, a=attr, iid=item.id, p=part: _set_section_item(
                    a, iid, p, v
                ),
            )


def _add_support_fields(fields: dict[str, EditableField]) -> None:
    for part, title, kind in (
        ("call_text", "متن پشتیبانی تلفنی", "text"),
        ("telegram_text", "متن پشتیبانی تلگرام", "text"),
        ("telegram_url", "لینک پشتیبانی تلگرام", "url"),
    ):
        fields[f"support:{part}"] = EditableField(
            key=f"support:{part}",
            group="support",
            title=title,
            kind=kind,
            default=getattr(content.SUPPORT, part),
            get_current=lambda p=part: getattr(content.SUPPORT, p),
            apply=lambda v, p=part: setattr(
                content, "SUPPORT", dataclasses.replace(content.SUPPORT, **{p: v})
            ),
        )


def _get_subject(grade_id: str, subject_id: str, part: str) -> str:
    grade = content.get_grade(grade_id)
    subject = content.get_subject(grade, subject_id) if grade else None
    return getattr(subject, part) if subject else ""


def _set_subject(grade_id: str, subject_id: str, part: str, value: str) -> None:
    grades = []
    for grade in content.GRADES:
        if grade.id == grade_id:
            subjects = tuple(
                dataclasses.replace(s, **{part: value}) if s.id == subject_id else s
                for s in grade.subjects
            )
            grades.append(dataclasses.replace(grade, subjects=subjects))
        else:
            grades.append(grade)
    content.GRADES = tuple(grades)
    # به‌روزرسانی ایندکس داخلی ماژول content
    content._GRADES_BY_ID = {g.id: g for g in content.GRADES}


def _add_subject_fields(fields: dict[str, EditableField]) -> None:
    for grade in content.GRADES:
        for subject in grade.subjects:
            specs = (
                ("title", f"عنوان درس «{subject.title}»", "short"),
                ("url", f"لینک آپارات «{subject.title}»", "url"),
            )
            for part, title, kind in specs:
                key = f"classes:{grade.id}:{subject.id}:{part}"
                fields[key] = EditableField(
                    key=key,
                    group="classes",
                    title=f"{title} — {grade.title}",
                    kind=kind,
                    default=getattr(subject, part if part != "url" else "aparat_url"),
                    get_current=lambda g=grade.id, s=subject.id, p=part: _get_subject(
                        g, s, "aparat_url" if p == "url" else p
                    ),
                    apply=lambda v, g=grade.id, s=subject.id, p=part: _set_subject(
                        g, s, "aparat_url" if p == "url" else p, v
                    ),
                )


def _get_product(grade_id: str, product_id: str, part: str) -> str:
    product = content.get_product(grade_id, product_id)
    return getattr(product, part) if product else ""


def _set_product(grade_id: str, product_id: str, part: str, value: str) -> None:
    products = tuple(
        dataclasses.replace(p, **{part: value}) if p.id == product_id else p
        for p in content.get_products(grade_id)
    )
    updated = dict(content.PRODUCTS_BY_GRADE)
    updated[grade_id] = products
    content.PRODUCTS_BY_GRADE = updated


def _add_product_fields(fields: dict[str, EditableField]) -> None:
    for grade_id, products in content.PRODUCTS_BY_GRADE.items():
        grade = content.get_grade(grade_id)
        grade_title = grade.title if grade else grade_id
        for product in products:
            for part, title, kind in (
                ("title", "عنوان", "short"),
                ("description", "توضیحات", "text"),
                ("price", "قیمت", "short"),
                ("order_url", "لینک سفارش", "url"),
            ):
                key = f"products:{grade_id}:{product.id}:{part}"
                fields[key] = EditableField(
                    key=key,
                    group="products",
                    title=f"{title} محصول «{product.title}» — {grade_title}",
                    kind=kind,
                    default=getattr(product, part),
                    get_current=lambda g=grade_id, pid=product.id, pt=part: _get_product(
                        g, pid, pt
                    ),
                    apply=lambda v, g=grade_id, pid=product.id, pt=part: _set_product(
                        g, pid, pt, v
                    ),
                )


def _get_exam(grade_id: str, exam_id: str, part: str) -> str:
    exam = content.get_exam(grade_id, exam_id)
    return getattr(exam, part) if exam else ""


def _set_exam(grade_id: str, exam_id: str, part: str, value: str) -> None:
    exams = tuple(
        dataclasses.replace(e, **{part: value}) if e.id == exam_id else e
        for e in content.get_exams(grade_id)
    )
    updated = dict(content.EXAMS_BY_GRADE)
    updated[grade_id] = exams
    content.EXAMS_BY_GRADE = updated


def _add_exam_fields(fields: dict[str, EditableField]) -> None:
    for grade_id, exams in content.EXAMS_BY_GRADE.items():
        grade = content.get_grade(grade_id)
        grade_title = grade.title if grade else grade_id
        for exam in exams:
            for part, title, kind in (
                ("title", "عنوان", "short"),
                ("url", "لینک آزمون", "url"),
            ):
                key = f"exams:{grade_id}:{exam.id}:{part}"
                fields[key] = EditableField(
                    key=key,
                    group="exams",
                    title=f"{title} آزمون «{exam.title}» — {grade_title}",
                    kind=kind,
                    default=getattr(exam, part),
                    get_current=lambda g=grade_id, eid=exam.id, pt=part: _get_exam(g, eid, pt),
                    apply=lambda v, g=grade_id, eid=exam.id, pt=part: _set_exam(g, eid, pt, v),
                )


def build_registry() -> dict[str, EditableField]:
    """فهرست کامل فیلدهای قابل‌ویرایش را از ساختارهای content می‌سازد."""
    fields: dict[str, EditableField] = {}
    for group, sec_key, attr, title in _SECTIONS:
        _add_section_fields(fields, group, sec_key, attr, title)
    _add_support_fields(fields)
    _add_subject_fields(fields)
    _add_product_fields(fields)
    _add_exam_fields(fields)
    return fields


# ---------------------------------------------------------------------------
# اعتبارسنجی
# ---------------------------------------------------------------------------

_URL_PATTERN = re.compile(r"^(https?://|tg://)", re.IGNORECASE)

ValidationMessage = Optional[str]


def validate_value(kind: str, value: str) -> ValidationMessage:
    """اعتبارسنجی مقدار جدید؛ در صورت خطا پیام فارسی برمی‌گرداند."""
    value = value.strip()
    if not value:
        return "مقدار خالی است؛ لطفاً یک مقدار بفرستید."
    if kind == "url":
        if not _URL_PATTERN.match(value):
            return "لینک باید با http:// یا https:// شروع شود (برای تلگرام: tg://)."
        if len(value) > 500:
            return "لینک بیش از حد طولانی است."
    elif kind == "short":
        if len(value) > 64:
            return "این مقدار باید حداکثر ۶۴ کاراکتر باشد."
    elif kind == "text":
        if len(value) > 3500:
            return "متن بیش از حد طولانی است (حداکثر ۳۵۰۰ کاراکتر)."
    return None


# ---------------------------------------------------------------------------
# مدیر محتوا
# ---------------------------------------------------------------------------


class ContentManager:
    """دسترسی یکنواخت به فیلدهای قابل‌ویرایش + ذخیره‌سازی override ها."""

    _fields: Optional[dict[str, EditableField]] = None

    @classmethod
    def initialize(cls) -> None:
        """ساخت رجیستری (یک بار)، بازگردانی پیش‌فرض‌ها و اعمال override ها.

        در ابتدای ``create_application`` صدا زده می‌شود؛ چون رجیستری فقط
        «یک بار» و پیش از هر تغییری ساخته می‌شود، مقادیر پیش‌فرض همیشه
        همان مقادیر اصلی ``content.py`` هستند.
        """
        if cls._fields is None:
            cls._fields = build_registry()
            logger.info("رجیستری محتوای قابل‌ویرایش ساخته شد (%d فیلد).", len(cls._fields))
        cls.reset_to_defaults()
        cls.apply_overrides()

    @classmethod
    def fields(cls) -> dict[str, EditableField]:
        if cls._fields is None:
            raise RuntimeError("ContentManager.initialize() هنوز صدا زده نشده است.")
        return cls._fields

    @classmethod
    def get_field(cls, key: str) -> Optional[EditableField]:
        return cls.fields().get(key)

    @classmethod
    def edit_groups(cls) -> list[tuple[str, str]]:
        """(group_id, عنوان) گروه‌هایی که فیلد دارند — به ترتیب تعریف."""
        present = {field.group for field in cls.fields().values()}
        return [
            (group_id, title)
            for group_id, title in EDIT_GROUP_TITLES.items()
            if group_id in present
        ]

    @classmethod
    def fields_in_group(cls, group_id: str) -> list[EditableField]:
        return [f for f in cls.fields().values() if f.group == group_id]

    @classmethod
    def reset_to_defaults(cls) -> None:
        """اعمال مجدد مقادیر پیش‌فرض روی ماژول content."""
        for field in cls.fields().values():
            field.apply(field.default)

    @classmethod
    def apply_overrides(cls) -> None:
        """اعمال همه‌ی override های ذخیره‌شده در دیتابیس."""
        for row in get_db().query_all("SELECT key, value FROM content_overrides"):
            field = cls.fields().get(row["key"])
            if field is not None:
                field.apply(row["value"])
            else:
                logger.warning("override ناشناخته در دیتابیس: %s", row["key"])

    @classmethod
    def set_value(cls, key: str, value: str) -> EditableField:
        """ذخیره‌ی مقدار جدید (دیتابیس + ماژول content)."""
        field = cls.get_field(key)
        if field is None:
            raise KeyError(f"فیلد ناشناخته: {key}")

        value = value.strip()
        if field.kind in ("text", "short"):
            # متن‌های مدیر HTML-escape می‌شوند تا صفحه‌ها هرگز نشکنند
            value = html.escape(value, quote=False)

        get_db().execute(
            """
            INSERT INTO content_overrides (key, value, updated_at)
            VALUES (?, ?, ?)
            ON CONFLICT(key) DO UPDATE SET
                value = excluded.value,
                updated_at = excluded.updated_at
            """,
            (key, value, datetime.now().isoformat(timespec="seconds")),
        )
        field.apply(value)
        logger.info("محتوای «%s» توسط مدیر به‌روزرسانی شد.", key)
        return field

    @classmethod
    def revert(cls, key: str) -> EditableField:
        """حذف override و بازگردانی مقدار پیش‌فرض."""
        field = cls.get_field(key)
        if field is None:
            raise KeyError(f"فیلد ناشناخته: {key}")
        get_db().execute("DELETE FROM content_overrides WHERE key = ?", (key,))
        field.apply(field.default)
        logger.info("محتوای «%s» به پیش‌فرض بازگشت.", key)
        return field

    @classmethod
    def is_overridden(cls, key: str) -> bool:
        """آیا این فیلد توسط مدیر تغییر داده شده است؟"""
        return (
            get_db().query_one(
                "SELECT 1 AS x FROM content_overrides WHERE key = ?", (key,)
            )
            is not None
        )

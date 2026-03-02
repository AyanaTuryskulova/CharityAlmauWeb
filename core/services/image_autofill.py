"""
Автоопределение предмета по фото на бэкенде.

- Модель: бесплатная предобученная HuggingFace (ViT, ImageNet).
- Стек: transformers + torch, без сторонних платных API.
- Вызов: после загрузки изображения (AJAX infer_product_image или при отправке формы add_product).
- Результат: автоматическое заполнение title и main_category; пользователь может изменить вручную.
"""
import logging
from dataclasses import dataclass
from functools import lru_cache
from typing import Optional, Sequence

from PIL import Image
from django.db.models import Q

from core.models import Category

logger = logging.getLogger(__name__)

# Бесплатная предобученная модель HuggingFace (ImageNet-1k)
MODEL_ID = "google/vit-base-patch16-224"


@dataclass
class ImageAutofillResult:
    title: Optional[str] = None
    main_category: Optional[Category] = None
    score: Optional[float] = None
    raw_label: Optional[str] = None


@lru_cache(maxsize=1)
def _classifier():
    from transformers import pipeline

    return pipeline("image-classification", model=MODEL_ID)


def _normalize(text: str) -> str:
    return " ".join((text or "").lower().replace("-", " ").replace("_", " ").split())


# Один русский заголовок по английской метке ImageNet (топ-1)
LABEL_TO_RUSSIAN = {
    "jersey": "Футболка",
    "t shirt": "Футболка",
    "tee shirt": "Футболка",
    "jean": "Джинсы",
    "jeans": "Джинсы",
    "sweater": "Свитер",
    "jacket": "Куртка",
    "coat": "Пальто",
    "dress": "Платье",
    "skirt": "Юбка",
    "blouse": "Блузка",
    "suit": "Костюм",
    "hoodie": "Толстовка",
    "sneaker": "Кроссовки",
    "sneakers": "Кроссовки",
    "boot": "Ботинки",
    "boots": "Ботинки",
    "sandal": "Сандалии",
    "slipper": "Тапочки",
    "backpack": "Рюкзак",
    "bag": "Сумка",
    "handbag": "Сумка",
    "book": "Книга",
    "notebook": "Тетрадь",
    "laptop": "Ноутбук",
    "computer": "Компьютер",
    "monitor": "Монитор",
    "keyboard": "Клавиатура",
    "mouse": "Компьютерная мышь",
    "cellular telephone": "Телефон",
    "mobile phone": "Телефон",
    "camera": "Фотоаппарат",
    "headphone": "Наушники",
    "speaker": "Колонка",
    "chair": "Стул",
    "table": "Стол",
    "sofa": "Диван",
    "bed": "Кровать",
    "lamp": "Лампа",
    "vase": "Ваза",
    "clock": "Часы",
    "bottle": "Бутылка",
    "cup": "Чашка",
    "mug": "Кружка",
    "pen": "Ручка",
    "pencil": "Карандаш",
    "shelf": "Полка",
    "wardrobe": "Шкаф",
    "cabinet": "Шкаф",
    "pillow": "Подушка",
    "blanket": "Плед",
    "curtain": "Шторы",
    "towel": "Полотенце",
}


def _label_to_russian_title(label: str) -> str:
    """Одно название на русском по английской метке (топ-1, без запятых)."""
    normalized = _normalize(label)
    # Если метка содержит запятые (jersey, t shirt, tee shirt), берём первый токен
    first_part = normalized.split(",")[0].strip() if "," in normalized else normalized
    first_part = " ".join(first_part.split())  # один пробел
    if not first_part:
        return "Предмет"
    # Точное совпадение
    if first_part in LABEL_TO_RUSSIAN:
        return LABEL_TO_RUSSIAN[first_part]
    # Совпадение по началу (одно слово)
    for en, ru in LABEL_TO_RUSSIAN.items():
        if first_part == en or first_part.startswith(en + " ") or first_part.endswith(" " + en):
            return ru
    # По подстроке для составных (e.g. "tee shirt" -> "Футболка")
    for en, ru in LABEL_TO_RUSSIAN.items():
        if en in first_part:
            return ru
    # Не нашли — капитализируем первое слово (оставляем по-английски только если нет перевода)
    return first_part.split()[0].capitalize() if first_part else "Предмет"


def _pick_category_name(label: str) -> Optional[str]:
    normalized = _normalize(label)
    keyword_map = {
        "Обувь": (
            "shoe", "sneaker", "boot", "sandal", "slipper", "loafer", "heel", "sock",
            "кроссов", "ботин", "туфл", "сапог", "босонож", "обув",
        ),
        "Одежда": (
            "shirt", "t shirt", "tshirt", "jean", "jacket", "coat", "dress", "skirt",
            "blouse", "suit", "sweater", "hoodie", "trousers", "pants", "garment",
            "одеж", "рубаш", "куртк", "пальто", "плать", "юбк", "джинс", "брюк",
        ),
        "Электроника": (
            "phone", "smartphone", "cellular", "mobile", "laptop", "notebook", "computer",
            "monitor", "screen", "tablet", "keyboard", "mouse", "camera", "headphone",
            "earphone", "speaker", "console", "printer", "router", "charger", "cable",
            "электрон", "смартфон", "ноутбук", "компьютер", "телефон", "камера", "наушник",
        ),
        "Книги": (
            "book", "comic", "magazine", "notebook", "textbook",
            "книга", "учебник", "комикс", "журнал",
        ),
        "Для дома": (
            "chair", "table", "sofa", "couch", "bed", "pillow", "blanket", "curtain",
            "cabinet", "wardrobe", "vase", "lamp", "kitchen", "pan", "pot", "mug",
            "дом", "мебел", "стол", "стул", "кровать", "шкаф", "декор", "плед", "подуш",
        ),
        "Для учебы": (
            "pen", "pencil", "backpack", "bag", "notepad", "marker", "ruler",
            "канцел", "рюкзак", "тетрад", "ручк", "карандаш",
        ),
    }
    for category_name, keywords in keyword_map.items():
        if any(keyword in normalized for keyword in keywords):
            return category_name
    return "Прочее"


def _find_main_category(candidate_names: Sequence[str]) -> Optional[Category]:
    names = [name for name in candidate_names if name]
    if not names:
        return None

    query = Q()
    for name in names:
        query |= Q(name__iexact=name)

    category = Category.objects.filter(parent__isnull=True).filter(query).first()
    if category:
        return category

    fallback_query = Q()
    for name in names:
        fallback_query |= Q(name__icontains=name)
    return Category.objects.filter(parent__isnull=True).filter(fallback_query).first()


def infer_product_from_image(uploaded_file) -> ImageAutofillResult:
    if not uploaded_file:
        return ImageAutofillResult()

    try:
        uploaded_file.seek(0)
        image = Image.open(uploaded_file).convert("RGB")
        predictions = _classifier()(image)
        uploaded_file.seek(0)
    except Exception:
        logger.exception("Image classification failed")
        try:
            uploaded_file.seek(0)
        except Exception:
            pass
        return ImageAutofillResult()

    if not predictions:
        return ImageAutofillResult()

    top_prediction = predictions[0]
    label = (top_prediction.get("label") or "").strip()
    score = float(top_prediction.get("score", 0.0))
    cleaned_label = label.replace("_", " ").replace("-", " ").strip()
    title = _label_to_russian_title(cleaned_label) if cleaned_label else None
    category_name = _pick_category_name(cleaned_label)
    main_category = _find_main_category((category_name,)) if category_name else None

    return ImageAutofillResult(
        title=title,
        main_category=main_category,
        score=score,
        raw_label=label,
    )


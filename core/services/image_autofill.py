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


# Полный словарь русских названий по меткам ImageNet (1k классов)
LABEL_TO_RUSSIAN = {
    # --- Одежда ---
    "jersey": "Футболка", "t shirt": "Футболка", "tee shirt": "Футболка",
    "sweatshirt": "Свитшот", "cardigan": "Кардиган", "pullover": "Пуловер",
    "sweater": "Свитер", "hoodie": "Худи", "jean": "Джинсы", "jeans": "Джинсы",
    "suit": "Костюм", "jacket": "Куртка", "coat": "Пальто", "overcoat": "Пальто",
    "trench coat": "Тренч", "raincoat": "Дождевик", "fur coat": "Шуба",
    "dress": "Платье", "skirt": "Юбка", "miniskirt": "Мини-юбка",
    "blouse": "Блузка", "shirt": "Рубашка", "polo shirt": "Поло",
    "pajama": "Пижама", "bikini": "Купальник", "brassiere": "Бюстгальтер",
    "shorts": "Шорты", "trousers": "Брюки", "pants": "Брюки",
    "stole": "Палантин", "apron": "Фартук", "lab coat": "Халат",
    "gown": "Халат", "swimming trunks": "Плавки",
    # --- Головные уборы и аксессуары ---
    "hat": "Шапка", "cap": "Кепка", "beanie": "Шапка",
    "helmet": "Шлем", "hard hat": "Каска", "bonnet": "Чепец",
    "cowboy hat": "Ковбойская шляпа", "beret": "Берет",
    "sunglasses": "Очки солнечные", "glasses": "Очки",
    "tie": "Галстук", "bow tie": "Бабочка", "scarf": "Шарф",
    "glove": "Перчатки", "mitten": "Варежки", "belt": "Ремень",
    "watch": "Часы", "bracelet": "Браслет", "necklace": "Ожерелье",
    "ring": "Кольцо", "earring": "Серьги",
    # --- Обувь ---
    "sneaker": "Кроссовки", "running shoe": "Кроссовки",
    "boot": "Ботинки", "ankle boot": "Ботильоны",
    "sandal": "Сандалии", "slipper": "Тапочки",
    "loafer": "Мокасины", "high heel": "Туфли на каблуке",
    "clog": "Сабо", "moccasin": "Мокасины", "sock": "Носки",
    # --- Сумки ---
    "backpack": "Рюкзак", "back pack": "Рюкзак", "knapsack": "Рюкзак",
    "handbag": "Сумка", "bag": "Сумка", "purse": "Кошелёк",
    "briefcase": "Портфель", "wallet": "Кошелёк",
    "suitcase": "Чемодан", "luggage": "Чемодан",
    "tote bag": "Шоппер", "shoulder bag": "Сумка через плечо",
    # --- Электроника ---
    "laptop": "Ноутбук", "notebook": "Ноутбук",
    "desktop computer": "Компьютер", "computer": "Компьютер",
    "monitor": "Монитор", "screen": "Монитор",
    "keyboard": "Клавиатура", "computer keyboard": "Клавиатура",
    "mouse": "Компьютерная мышь",
    "cellular telephone": "Телефон", "mobile phone": "Телефон",
    "smartphone": "Смартфон", "iphone": "Смартфон",
    "tablet": "Планшет", "ipad": "Планшет",
    "camera": "Фотоаппарат", "digital camera": "Фотоаппарат",
    "reflex camera": "Зеркальный фотоаппарат",
    "headphone": "Наушники", "earphone": "Наушники", "earbuds": "Наушники",
    "loudspeaker": "Колонка", "speaker": "Колонка",
    "microphone": "Микрофон", "radio": "Радио",
    "television": "Телевизор", "tv": "Телевизор",
    "remote control": "Пульт управления",
    "printer": "Принтер", "scanner": "Сканер",
    "projector": "Проектор",
    "hard disk": "Жёсткий диск", "flash drive": "Флешка",
    "router": "Роутер", "modem": "Модем",
    "charger": "Зарядное устройство", "battery": "Батарейка",
    "electric fan": "Вентилятор", "hair dryer": "Фен",
    "iron": "Утюг", "toaster": "Тостер",
    "microwave": "Микроволновка", "oven": "Духовка",
    "refrigerator": "Холодильник", "freezer": "Морозильник",
    "washing machine": "Стиральная машина",
    "vacuum cleaner": "Пылесос", "blender": "Блендер",
    "coffee maker": "Кофемашина", "kettle": "Чайник",
    "calculator": "Калькулятор", "alarm clock": "Будильник",
    # --- Книги и канцтовары ---
    "book": "Книга", "comic book": "Комикс",
    "pen": "Ручка", "ballpoint pen": "Ручка", "fountain pen": "Ручка перьевая",
    "pencil": "Карандаш", "marker": "Маркер", "crayon": "Восковой мелок",
    "ruler": "Линейка", "scissors": "Ножницы", "stapler": "Степлер",
    "tape": "Скотч", "glue": "Клей", "eraser": "Ластик",
    "notebook computer": "Тетрадь", "binder": "Папка",
    # --- Мебель ---
    "chair": "Стул", "folding chair": "Складной стул",
    "rocking chair": "Кресло-качалка", "armchair": "Кресло",
    "desk": "Стол", "table": "Стол", "coffee table": "Журнальный столик",
    "dining table": "Обеденный стол",
    "sofa": "Диван", "couch": "Диван", "studio couch": "Диван-кровать",
    "bed": "Кровать", "bunk bed": "Двухъярусная кровать",
    "wardrobe": "Шкаф", "cabinet": "Шкаф",
    "chest of drawers": "Комод", "bookcase": "Книжный шкаф",
    "shelf": "Полка", "nightstand": "Тумбочка",
    "lamp": "Лампа", "table lamp": "Настольная лампа",
    "chandelier": "Люстра", "lantern": "Фонарь",
    "pillow": "Подушка", "blanket": "Плед", "quilt": "Одеяло",
    "curtain": "Шторы", "window blind": "Жалюзи",
    "mirror": "Зеркало", "rug": "Ковёр", "doormat": "Коврик",
    "towel": "Полотенце",
    # --- Кухня ---
    "cup": "Чашка", "mug": "Кружка", "teapot": "Чайник заварной",
    "bottle": "Бутылка", "wine bottle": "Бутылка вина",
    "pitcher": "Кувшин", "carafe": "Графин",
    "bowl": "Миска", "plate": "Тарелка", "platter": "Блюдо",
    "knife": "Нож", "fork": "Вилка", "spoon": "Ложка",
    "pan": "Сковорода", "frying pan": "Сковорода",
    "pot": "Кастрюля", "wok": "Вок",
    "cutting board": "Разделочная доска", "colander": "Дуршлаг",
    "jar": "Банка", "can opener": "Консервный нож",
    # --- Спорт ---
    "dumbbell": "Гантель", "barbell": "Штанга",
    "tennis racket": "Теннисная ракетка", "racket": "Ракетка",
    "badminton": "Ракетка для бадминтона",
    "volleyball": "Волейбольный мяч", "basketball": "Баскетбольный мяч",
    "soccer ball": "Футбольный мяч", "football": "Футбольный мяч",
    "baseball bat": "Бейсбольная бита", "baseball": "Бейсбольный мяч",
    "bicycle": "Велосипед", "mountain bike": "Горный велосипед",
    "skateboard": "Скейтборд", "roller skate": "Ролики",
    "ski": "Лыжи", "snowboard": "Сноуборд",
    "swimming cap": "Шапочка для плавания",
    "yoga mat": "Коврик для йоги", "jump rope": "Скакалка",
    "treadmill": "Беговая дорожка",
    # --- Музыкальные инструменты ---
    "guitar": "Гитара", "electric guitar": "Электрогитара",
    "acoustic guitar": "Акустическая гитара", "banjo": "Банджо",
    "violin": "Скрипка", "cello": "Виолончель", "viola": "Альт",
    "piano": "Пианино", "keyboard instrument": "Синтезатор",
    "drum": "Барабан", "drumstick": "Барабанная палочка",
    "flute": "Флейта", "harmonica": "Губная гармошка",
    "saxophone": "Саксофон", "trumpet": "Труба",
    "accordion": "Аккордеон", "ukulele": "Укулеле",
    # --- Игрушки и игры ---
    "doll": "Кукла", "teddy bear": "Мягкая игрушка",
    "toy": "Игрушка", "stuffed animal": "Мягкая игрушка",
    "jigsaw puzzle": "Пазл", "chess": "Шахматы",
    "board game": "Настольная игра", "playing card": "Игральные карты",
    # --- Прочее ---
    "vase": "Ваза", "clock": "Часы",
    "umbrella": "Зонт", "candle": "Свеча",
    "hammer": "Молоток", "screwdriver": "Отвёртка",
    "wrench": "Гаечный ключ", "saw": "Пила",
    "paintbrush": "Кисть", "palette": "Палитра",
    "picture frame": "Рамка для фото",
    "plant": "Растение", "flower pot": "Горшок с цветком",
    "bicycle helmet": "Велосипедный шлем",
    "trophy": "Кубок", "medal": "Медаль",
    "map": "Карта", "globe": "Глобус",
    "canteen": "Фляжка", "thermos": "Термос",
    "sewing machine": "Швейная машина",
}


def _translate_via_api(text: str) -> Optional[str]:
    """Переводит слово через бесплатный MyMemory API (fallback)."""
    try:
        import urllib.request, urllib.parse, json as _json
        params = urllib.parse.urlencode({'q': text, 'langpair': 'en|ru'})
        url = f'https://api.mymemory.translated.net/get?{params}'
        with urllib.request.urlopen(url, timeout=3) as r:
            data = _json.loads(r.read())
        result = data.get('responseData', {}).get('translatedText', '')
        if result and result.lower() != text.lower() and not result.startswith('PLEASE SELECT'):
            return result.capitalize()
    except Exception:
        pass
    return None


def _label_to_russian_title(label: str) -> str:
    """Одно название на русском по английской метке (топ-1, без запятых)."""
    normalized = _normalize(label)
    # Берём часть до запятой (ImageNet метки вида "jersey, T-shirt, tee shirt")
    first_part = normalized.split(",")[0].strip() if "," in normalized else normalized
    first_part = " ".join(first_part.split())
    if not first_part:
        return "Предмет"

    # 1. Точное совпадение
    if first_part in LABEL_TO_RUSSIAN:
        return LABEL_TO_RUSSIAN[first_part]

    # 2. Совпадение по частям
    for en, ru in LABEL_TO_RUSSIAN.items():
        if first_part == en or first_part.startswith(en + " ") or first_part.endswith(" " + en):
            return ru

    # 3. По подстроке
    for en, ru in LABEL_TO_RUSSIAN.items():
        if en in first_part:
            return ru

    # 4. Попытка перевести через бесплатный API (если есть интернет)
    translated = _translate_via_api(first_part)
    if translated:
        return translated

    # 5. Если ничего не помогло — возвращаем "Предмет"
    return "Предмет"


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
            "remote control", "remote", "controller", "gamepad", "joystick", "tv",
            "электрон", "смартфон", "ноутбук", "компьютер", "телефон", "камера", "наушник",
            "пульт", "колонк", "клавиатур", "мыш", "телевиз", "роутер", "заряд",
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
            "folder", "binder", "file folder", "document folder", "stationery",
            "канцел", "рюкзак", "тетрад", "ручк", "карандаш", "папк", "папка", "скоросшив",
        ),
    }

    # Небольшой приоритет для устройств управления и аксессуаров электроники,
    # чтобы "remote control" не уходил в "Прочее".
    electronics_priority = ("remote control", "remote", "controller", "gamepad", "joystick", "пульт")
    if any(keyword in normalized for keyword in electronics_priority):
        return "Электроника"

    # Выбираем категорию с максимальным числом совпадений по ключам.
    # Это уменьшает случайные попадания в "Прочее" при составных метках.
    best_category = None
    best_score = 0
    for category_name, keywords in keyword_map.items():
        score = sum(1 for keyword in keywords if keyword in normalized)
        if score > best_score:
            best_score = score
            best_category = category_name

    if best_category and best_score > 0:
        return best_category
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


"""
Полная интернационализация всех шаблонов.
Добавляет {% trans %} и {% blocktrans %} ко всем пользовательским строкам,
обновляет .po файлы и компилирует .mo.
"""
import pathlib
import polib

BASE = pathlib.Path(__file__).resolve().parent

# ─────────────────────────────────────────────
# 1.  Словарь всех переводов
# ─────────────────────────────────────────────
TRANSLATIONS = {
    # ── Общие ──
    "Нет фото":                          {"en": "No photo",                "kk": "Фото жоқ"},
    "Нет подкатегорий":                  {"en": "No subcategories",        "kk": "Қосымша санат жоқ"},
    "Категории":                         {"en": "Categories",              "kk": "Санаттар"},
    "Категории пока не добавлены":       {"en": "No categories yet",       "kk": "Санаттар әлі қосылмаған"},
    "В избранном":                       {"en": "In favorites",            "kk": "Таңдаулыда"},
    "В избранное":                       {"en": "Add to favorites",        "kk": "Таңдаулыға"},
    "Отдать даром":                      {"en": "Give away",               "kk": "Тегін беру"},
    "Обмен":                             {"en": "Exchange",                "kk": "Айырбас"},
    # ── Уже есть в .po, но продублируем на случай отсутствия ──
    "Лента":                             {"en": "Feed",                    "kk": "Жиналғы"},
    "Заявки":                            {"en": "Requests",                "kk": "Өтінімдер"},
    "Чаты":                              {"en": "Chats",                   "kk": "Чаттар"},
    "Добавить":                          {"en": "Add",                     "kk": "Қосу"},
    "Выйти":                             {"en": "Log out",                 "kk": "Шығу"},
    "Войти":                             {"en": "Log in",                  "kk": "Кіру"},
    "Аренда":                            {"en": "Rental",                  "kk": "Жалдау"},
    "Главная":                           {"en": "Home",                    "kk": "Басты"},
    "Профиль":                           {"en": "Profile",                 "kk": "Профиль"},
    # ── Главная страница ──
    "Найти вещь":                        {"en": "Search items",            "kk": "Зат іздеу"},
    "Все":                               {"en": "All",                     "kk": "Барлығы"},
    "Добавлено недавно":                 {"en": "Recently added",          "kk": "Соңғы қосылған"},
    "Пока нет объявлений.":              {"en": "No listings yet.",        "kk": "Хабарландырулар жоқ."},
    # ── Отдать даром ──
    "Пока нет товаров в разделе «Отдать даром».":
                                         {"en": "No items in the 'Give away' section.",
                                          "kk": "«Тегін беру» бөліміндегі заттар жоқ."},
    # ── Обмен ──
    "Пока нет товаров в разделе «Обмен».":
                                         {"en": "No items in the 'Exchange' section.",
                                          "kk": "«Айырбас» бөліміндегі заттар жоқ."},
    # ── Аренда ──
    "Пока нет товаров для аренды.":      {"en": "No rental items yet.",    "kk": "Жалдауға арналған заттар жоқ."},
    # ── Карточка товара ──
    "Забрать":                           {"en": "Take",                    "kk": "Алу"},
    "Обменяться":                        {"en": "Exchange",                "kk": "Айырбасу"},
    "Арендовать":                        {"en": "Rent",                    "kk": "Жалдау"},
    "Войти, чтобы арендовать":           {"en": "Login to rent",           "kk": "Жалдау үшін кіру"},
    "♥ В избранном":                     {"en": "♥ Favorited",             "kk": "♥ Таңдаулыда"},
    "♡ В избранное":                     {"en": "♡ Add to favorites",      "kk": "♡ Таңдаулыға"},
    "Написать":                          {"en": "Message",                 "kk": "Жазу"},
    # ── Мои объявления ──
    "Избранное":                         {"en": "Favorites",               "kk": "Таңдаулылар"},
    "Мои объявления":                    {"en": "My ads",                  "kk": "Менің жарнамаларым"},
    "Избранных":                         {"en": "Favorites",               "kk": "Таңдаулы"},
    "Объявлений":                        {"en": "Listings",                "kk": "Хабарландырулар"},
    "Отдам даром":                       {"en": "Free",                    "kk": "Тегін"},
    "Убрать из избранного":              {"en": "Remove from favorites",   "kk": "Таңдаулыдан алу"},
    "Убрать из избранного?":             {"en": "Remove from favorites?",  "kk": "Таңдаулыдан алу?"},
    "Пока нет избранных товаров.":       {"en": "No favorites yet.",       "kk": "Таңдаулы заттар жоқ."},
    "Перейти на главную":                {"en": "Go to home",              "kk": "Басты бетке өту"},
    "Активно":                           {"en": "Active",                  "kk": "Белсенді"},
    "На модерации":                      {"en": "Under review",            "kk": "Тексеруде"},
    "✎ Редактировать":                   {"en": "✎ Edit",                  "kk": "✎ Өңдеу"},
    "Удалить объявление?":               {"en": "Delete listing?",         "kk": "Хабарландыруды жою?"},
    "🗑 Удалить":                         {"en": "🗑 Delete",               "kk": "🗑 Жою"},
    "У вас пока нет объявлений.":        {"en": "No listings yet.",        "kk": "Хабарландырулар жоқ."},
    "Добавить объявление":               {"en": "Add listing",             "kk": "Хабарландыру қосу"},
    "Чтобы избранное сохранялось, выполните в терминале в папке проекта:":
                                         {"en": "To save favorites, run in the project terminal:",
                                          "kk": "Таңдаулыларды сақтау үшін терминалда іске қосыңыз:"},
    # ── Заявки ──
    "Исходящие заявки":                  {"en": "Outgoing requests",       "kk": "Шыққан өтінімдер"},
    "Входящие заявки":                   {"en": "Incoming requests",       "kk": "Кіріс өтінімдер"},
    "Продавец:":                         {"en": "Owner:",                  "kk": "Иесі:"},
    "Действие:":                         {"en": "Action:",                 "kk": "Іс-әрекет:"},
    "Статус:":                           {"en": "Status:",                 "kk": "Мәртебесі:"},
    "Отменить":                          {"en": "Cancel",                  "kk": "Болдырмау"},
    "Завершить":                         {"en": "Complete",                "kk": "Аяқтау"},
    "Нет исходящих заявок.":             {"en": "No outgoing requests.",   "kk": "Шыққан өтінімдер жоқ."},
    "Запросил:":                         {"en": "Requested by:",           "kk": "Сұраған:"},
    "Принять":                           {"en": "Accept",                  "kk": "Қабылдау"},
    "Отклонить":                         {"en": "Decline",                 "kk": "Қабылдамау"},
    "Нет входящих заявок.":              {"en": "No incoming requests.",   "kk": "Кіріс өтінімдер жоқ."},
    # ── Добавить товар ──
    "Добавить товар":                    {"en": "Add listing",             "kk": "Хабарландыру қосу"},
    "Фото":                              {"en": "Photo",                   "kk": "Фото"},
    "Добавить фото":                     {"en": "Add photo",               "kk": "Фото қосу"},
    "Фото 1 (главное)":                  {"en": "Photo 1 (main)",          "kk": "Фото 1 (негізгі)"},
    "Фото 2":                            {"en": "Photo 2",                 "kk": "Фото 2"},
    "Фото 3":                            {"en": "Photo 3",                 "kk": "Фото 3"},
    "Фото 4":                            {"en": "Photo 4",                 "kk": "Фото 4"},
    "Фото 5":                            {"en": "Photo 5",                 "kk": "Фото 5"},
    "Удалить":                           {"en": "Delete",                  "kk": "Жою"},
    "Название объявления":               {"en": "Listing title",           "kk": "Хабарландыру атауы"},
    "Название заполнится автоматически по фото (можно изменить вручную)":
                                         {"en": "Title will be filled automatically from photo (can be changed manually)",
                                          "kk": "Атауы фотодан автоматты толтырылады (қолмен өзгертуге болады)"},
    "Описание":                          {"en": "Description",             "kk": "Сипаттама"},
    "Опишите характеристики товара, условия аренды, цену за сутки или час...":
                                         {"en": "Describe the item, rental conditions, price per day or hour...",
                                          "kk": "Заттың сипаттамасын, жалдау шарттарын, тәулік немесе сағат бағасын сипаттаңыз..."},
    "Имя и номер телефона":              {"en": "Name and phone",          "kk": "Аты және телефон"},
    "Ваше имя":                          {"en": "Your name",               "kk": "Атыңыз"},
    "Номер телефона":                    {"en": "Phone number",            "kk": "Телефон нөмірі"},
    "Длительность аренды":               {"en": "Rental duration",         "kk": "Жалдау мерзімі"},
    "Выберите срок":                     {"en": "Select duration",         "kk": "Мерзімді таңдаңыз"},
    "Час":                               {"en": "Hour",                    "kk": "Сағат"},
    "Сутки":                             {"en": "Day",                     "kk": "Тәулік"},
    "Неделя":                            {"en": "Week",                    "kk": "Апта"},
    "Месяц":                             {"en": "Month",                   "kk": "Ай"},
    "Расположение":                      {"en": "Location",                "kk": "Орналасу"},
    "Выберите город":                    {"en": "Select city",             "kk": "Қаланы таңдаңыз"},
    "Алматы":                            {"en": "Almaty",                  "kk": "Алматы"},
    "Астана":                            {"en": "Astana",                  "kk": "Астана"},
    "Шымкент":                           {"en": "Shymkent",                "kk": "Шымкент"},
    "Другой":                            {"en": "Other",                   "kk": "Басқа"},
    "Категория":                         {"en": "Category",                "kk": "Санат"},
    "— Основная категория —":            {"en": "— Main category —",       "kk": "— Негізгі санат —"},
    "— Подкатегория —":                  {"en": "— Subcategory —",         "kk": "— Қосымша санат —"},
    "— Под-подкатегория —":              {"en": "— Sub-subcategory —",     "kk": "— Қосымша санат —"},
    "Отмена":                            {"en": "Cancel",                  "kk": "Болдырмау"},
    "Опубликовать":                      {"en": "Publish",                 "kk": "Жариялау"},
    # ── Логин ──
    "Вход":                              {"en": "Login",                   "kk": "Кіру"},
    "Вход через Microsoft":              {"en": "Sign in with Microsoft",  "kk": "Microsoft арқылы кіру"},
    "Войти с помощью Microsoft":         {"en": "Sign in with Microsoft",  "kk": "Microsoft арқылы кіру"},
    "Войдите через корпоративную почту AlmaU для авторизации в":
                                         {"en": "Sign in with your AlmaU corporate email to access",
                                          "kk": "AlmaU корпоративтік поштасымен кіріңіз"},
    "Входить на платформу могут только сотрудники и студенты":
                                         {"en": "Only employees and students of",
                                          "kk": "Платформаға тек"},
    "через данные корпоративной почты":  {"en": "can access using their corporate email",
                                          "kk": "корпоративтік поштасы арқылы кіре алады"},
    # ── Чаты ──
    "Нет чатов":                         {"en": "No chats",                "kk": "Чаттар жоқ"},
    "Начните общение с владельцем интересующего вас товара.":
                                         {"en": "Start a conversation with the owner of an item you are interested in.",
                                          "kk": "Сізді қызықтыратын зат иесімен сөйлесуді бастаңыз."},
    "Написать сообщение...":             {"en": "Write a message...",      "kk": "Хабарлама жазыңыз..."},
    "Отправить":                         {"en": "Send",                    "kk": "Жіберу"},
    # ── Онбординг / О платформе ──
    "О платформе":                       {"en": "About the platform",      "kk": "Платформа туралы"},
    "Пропустить":                        {"en": "Skip",                    "kk": "Өткізіп жіберу"},
    "Далее":                             {"en": "Next",                    "kk": "Келесі"},
    "Начать":                            {"en": "Get started",             "kk": "Бастау"},
    # ── Редактировать / Добавить ──
    "Сохранить":                         {"en": "Save",                    "kk": "Сақтау"},
    "Редактировать":                     {"en": "Edit",                    "kk": "Өңдеу"},
    "Редактировать объявление":          {"en": "Edit listing",            "kk": "Хабарландыруды өңдеу"},
}

# ─────────────────────────────────────────────
# 2.  Замены в шаблонах (exact-string replace)
# ─────────────────────────────────────────────
# Формат: (путь, old, new)
TEMPLATE_REPLACEMENTS = []

def T(s):
    """Вернуть {% trans "s" %}"""
    return '{%% trans "%s" %%}' % s

def BT(s):
    """Вернуть {% blocktrans %}s{% endblocktrans %}"""
    return '{%% blocktrans %%}%s{%% endblocktrans %%}' % s

def add(path_str, old, new):
    TEMPLATE_REPLACEMENTS.append((BASE / path_str, old, new))

# ─── home.html ───────────────────────────────
H = 'core/templates/home.html'
add(H, '{% block title %}Главная{% endblock %}',
        '{%% block title %%}%s{%% endblock %%}' % T('Главная'))
add(H, 'placeholder="Найти вещь"',
        'placeholder="' + T('Найти вещь') + '"')
add(H, '<option value="">Все</option>',
        '<option value="">' + T('Все') + '</option>')
add(H, '<div class="product-card__empty">Нет фото</div>',
        '<div class="product-card__empty">' + T('Нет фото') + '</div>')
add(H,
    '{% if search_query %}Результаты по запросу «{{ search_query }}»{% else %}Добавлено недавно{% endif %}',
    '{% if search_query %}{% blocktrans %}Результаты по запросу «{{ search_query }}»{% endblocktrans %}{% else %}' + T('Добавлено недавно') + '{% endif %}')
add(H,
    '{% if search_query %}По запросу «{{ search_query }}» ничего не найдено. Попробуйте другие слова.{% else %}Пока нет объявлений.{% endif %}',
    '{% if search_query %}{% blocktrans %}По запросу «{{ search_query }}» ничего не найдено. Попробуйте другие слова.{% endblocktrans %}{% else %}' + T('Пока нет объявлений.') + '{% endif %}')
# favorite aria-labels
add(H,
    'aria-label="{% if product.id in favorite_ids %}В избранном{% else %}В избранное{% endif %}"',
    'aria-label="{% if product.id in favorite_ids %}' + T('В избранном') + '{% else %}' + T('В избранное') + '{% endif %}"')

# ─── free.html ───────────────────────────────
F = 'core/templates/free.html'
add(F, '{% block title %}Отдать даром{% endblock %}',
        '{%% block title %%}%s{%% endblock %%}' % T('Отдать даром'))
add(F, '<span>Нет подкатегорий</span>',
        '<span>' + T('Нет подкатегорий') + '</span>')
add(F, 'Категории\n                        </span>',
        T('Категории') + '\n                        </span>')
add(F, '<span>Категории пока не добавлены</span>',
        '<span>' + T('Категории пока не добавлены') + '</span>')
add(F, 'alt="Отдать даром"', 'alt="' + T('Отдать даром') + '"')
add(F, '<span class="card__empty">Нет фото</span>',
        '<span class="card__empty">' + T('Нет фото') + '</span>')
add(F, '<span class="tag">Отдать даром</span>',
        '<span class="tag">' + T('Отдать даром') + '</span>')
add(F,
    'aria-label="{% if product.id in favorite_ids %}В избранном{% else %}В избранное{% endif %}"',
    'aria-label="{% if product.id in favorite_ids %}' + T('В избранном') + '{% else %}' + T('В избранное') + '{% endif %}"')
add(F, '<p class="empty-list">Пока нет товаров в разделе «Отдать даром».</p>',
        '<p class="empty-list">' + T('Пока нет товаров в разделе «Отдать даром».') + '</p>')

# ─── exchange.html ────────────────────────────
E = 'core/templates/exchange.html'
add(E, '{% block title %}Обмен{% endblock %}',
        '{%% block title %%}%s{%% endblock %%}' % T('Обмен'))
add(E, '<span>Нет подкатегорий</span>',
        '<span>' + T('Нет подкатегорий') + '</span>')
add(E, 'Категории\n                        </span>',
        T('Категории') + '\n                        </span>')
add(E, '<span>Категории пока не добавлены</span>',
        '<span>' + T('Категории пока не добавлены') + '</span>')
add(E, 'alt="Обмен"', 'alt="' + T('Обмен') + '"')
add(E, '<span class="card__empty">Нет фото</span>',
        '<span class="card__empty">' + T('Нет фото') + '</span>')
add(E, '<span class="tag">Обмен</span>',
        '<span class="tag">' + T('Обмен') + '</span>')
add(E,
    'aria-label="{% if product.id in favorite_ids %}В избранном{% else %}В избранное{% endif %}"',
    'aria-label="{% if product.id in favorite_ids %}' + T('В избранном') + '{% else %}' + T('В избранное') + '{% endif %}"')
add(E, '<p class="empty-list">Пока нет товаров в разделе «Обмен».</p>',
        '<p class="empty-list">' + T('Пока нет товаров в разделе «Обмен».') + '</p>')

# ─── product_detail.html ──────────────────────
PD = 'core/templates/product_detail.html'
add(PD, '<span class="pd-main-empty">Нет фото</span>',
        '<span class="pd-main-empty">' + T('Нет фото') + '</span>')
add(PD, '>Забрать</a>', '>' + T('Забрать') + '</a>')
add(PD, '>Обменяться</a>', '>' + T('Обменяться') + '</a>')
add(PD, '>Арендовать</button>', '>' + T('Арендовать') + '</button>')
add(PD, '>Войти, чтобы арендовать</a>', '>' + T('Войти, чтобы арендовать') + '</a>')
add(PD,
    '>{% if in_favorites %}♥ В избранном{% else %}♡ В избранное{% endif %}</a>',
    '>{% if in_favorites %}' + T('♥ В избранном') + '{% else %}' + T('♡ В избранное') + '{% endif %}</a>')
add(PD, '>Написать</a>', '>' + T('Написать') + '</a>')

# ─── requests.html ────────────────────────────
R = 'core/templates/requests.html'
add(R, '{% block title %}Заявки{% endblock %}',
        '{%% block title %%}%s{%% endblock %%}' % T('Заявки'))
add(R, '>Исходящие заявки<', '>' + T('Исходящие заявки') + '<')
add(R, '>Продавец: <', '>' + T('Продавец:') + ' <')
add(R, '>Действие: <', '>' + T('Действие:') + ' <')
add(R, '>Статус: <', '>' + T('Статус:') + ' <')
add(R, 'value="cancel" class="req-btn req-btn--secondary">Отменить<',
        'value="cancel" class="req-btn req-btn--secondary">' + T('Отменить') + '<')
add(R, 'value="complete" class="req-btn req-btn--primary">Завершить<',
        'value="complete" class="req-btn req-btn--primary">' + T('Завершить') + '<')
add(R, '>Нет исходящих заявок.<', '>' + T('Нет исходящих заявок.') + '<')
add(R, '>Входящие заявки<', '>' + T('Входящие заявки') + '<')
add(R, '>Запросил: <', '>' + T('Запросил:') + ' <')
add(R, 'value="accept" class="req-btn req-btn--primary">Принять<',
        'value="accept" class="req-btn req-btn--primary">' + T('Принять') + '<')
add(R, 'value="decline" class="req-btn req-btn--secondary">Отклонить<',
        'value="decline" class="req-btn req-btn--secondary">' + T('Отклонить') + '<')
add(R, '>Нет входящих заявок.<', '>' + T('Нет входящих заявок.') + '<')

# ─── login.html ───────────────────────────────
L = 'core/templates/login.html'
add(L, '{% block title %}Вход{% endblock %}',
        '{%% block title %%}%s{%% endblock %%}' % T('Вход'))
add(L, '<h1 class="login-title">Вход через Microsoft</h1>',
        '<h1 class="login-title">' + T('Вход через Microsoft') + '</h1>')
add(L, 'Войти с помощью Microsoft\n            </a>',
        T('Войти с помощью Microsoft') + '\n            </a>')
add(L, '{% load static %}\n{% load socialaccount %}',
        '{% load static %}\n{% load socialaccount %}\n{% load i18n %}')
add(L,
    'Войдите через корпоративную почту AlmaU для авторизации в <strong>AlmaCharity</strong>',
    '{% blocktrans %}Войдите через корпоративную почту AlmaU для авторизации в {% endblocktrans %}<strong>AlmaCharity</strong>')
add(L,
    'Входить на платформу могут только сотрудники и студенты <strong>AlmaU</strong>\n            через данные корпоративной почты <strong>@almau.edu.kz</strong>.',
    '{% blocktrans %}Входить на платформу могут только сотрудники и студенты{% endblocktrans %} <strong>AlmaU</strong>\n            {% blocktrans %}через данные корпоративной почты{% endblocktrans %} <strong>@almau.edu.kz</strong>.')

# ─── my_ads.html ──────────────────────────────
MA = 'core/templates/my_ads.html'
# Tabs
add(MA, '>Избранное<', '>' + T('Избранное') + '<')
add(MA, '>Мои объявления<', '>' + T('Мои объявления') + '<')
add(MA, '>Выйти<', '>' + T('Выйти') + '<')
add(MA, 'Нет фото', T('Нет фото'))
add(MA, '>Отдам даром<', '>' + T('Отдам даром') + '<')
add(MA, 'confirm(\'Убрать из избранного?\')', 'confirm(\'' + T('Убрать из избранного?') + '\')')
add(MA, 'title="Убрать из избранного"', 'title="' + T('Убрать из избранного') + '"')
add(MA, '>Пока нет избранных товаров.<', '>' + T('Пока нет избранных товаров.') + '<')
add(MA, '>Перейти на главную<', '>' + T('Перейти на главную') + '<')
add(MA, '>Активно<', '>' + T('Активно') + '<')
add(MA, '>На модерации<', '>' + T('На модерации') + '<')
add(MA, '>✎ Редактировать<', '>' + T('✎ Редактировать') + '<')
add(MA, 'confirm(\'Удалить объявление?\')', 'confirm(\'' + T('Удалить объявление?') + '\')')
add(MA, '>🗑 Удалить<', '>' + T('🗑 Удалить') + '<')
add(MA, '>У вас пока нет объявлений.<', '>' + T('У вас пока нет объявлений.') + '<')
add(MA, '>Добавить объявление<', '>' + T('Добавить объявление') + '<')

# ─── rentals/index.html ───────────────────────
RI = 'core/apps/rentals/templates/rentals/index.html'
add(RI, '<span>Нет подкатегорий</span>',
        '<span>' + T('Нет подкатегорий') + '</span>')
add(RI, '<span>Категории пока не добавлены</span>',
        '<span>' + T('Категории пока не добавлены') + '</span>')
add(RI, '<span class="card__empty">Нет фото</span>',
        '<span class="card__empty">' + T('Нет фото') + '</span>')
add(RI, '>Пока нет товаров для аренды.<', '>' + T('Пока нет товаров для аренды.') + '<')
add(RI,
    'aria-label="{% if product.id in favorite_ids %}В избранном{% else %}В избранное{% endif %}"',
    'aria-label="{% if product.id in favorite_ids %}' + T('В избранном') + '{% else %}' + T('В избранное') + '{% endif %}"')

# ─── add_product.html ─────────────────────────
AP = 'core/templates/add_product.html'
add(AP, '{% block title %}Добавить товар{% endblock %}',
        '{%% block title %%}%s{%% endblock %%}' % T('Добавить товар'))
add(AP, '>Фото</', '>' + T('Фото') + '</')
add(AP, 'title="Добавить фото"', 'title="' + T('Добавить фото') + '"')
add(AP, '>Фото 1 (главное)<', '>' + T('Фото 1 (главное)') + '<')
add(AP, '>Фото 2<', '>' + T('Фото 2') + '<')
add(AP, '>Фото 3<', '>' + T('Фото 3') + '<')
add(AP, '>Фото 4<', '>' + T('Фото 4') + '<')
add(AP, '>Фото 5<', '>' + T('Фото 5') + '<')
add(AP, '>Название объявления</', '>' + T('Название объявления') + '</')
add(AP, 'placeholder="Название заполнится автоматически по фото (можно изменить вручную)"',
        'placeholder="' + T('Название заполнится автоматически по фото (можно изменить вручную)') + '"')
add(AP, '>Описание</', '>' + T('Описание') + '</')
add(AP, 'placeholder="Опишите характеристики товара, условия аренды, цену за сутки или час..."',
        'placeholder="' + T('Опишите характеристики товара, условия аренды, цену за сутки или час...') + '"')
add(AP, '>Имя и номер телефона</', '>' + T('Имя и номер телефона') + '</')
add(AP, 'placeholder="Ваше имя"', 'placeholder="' + T('Ваше имя') + '"')
add(AP, 'placeholder="Номер телефона"', 'placeholder="' + T('Номер телефона') + '"')
add(AP, '>Длительность аренды</', '>' + T('Длительность аренды') + '</')
add(AP, '>Выберите срок<', '>' + T('Выберите срок') + '<')
add(AP, '>Час</', '>' + T('Час') + '</')
add(AP, '>Сутки</', '>' + T('Сутки') + '</')
add(AP, '>Неделя</', '>' + T('Неделя') + '</')
add(AP, '>Месяц</', '>' + T('Месяц') + '</')
add(AP, '>Расположение</', '>' + T('Расположение') + '</')
add(AP, '>Выберите город<', '>' + T('Выберите город') + '<')
add(AP, '>Алматы</', '>' + T('Алматы') + '</')
add(AP, '>Астана</', '>' + T('Астана') + '</')
add(AP, '>Шымкент</', '>' + T('Шымкент') + '</')
add(AP, '>Другой</', '>' + T('Другой') + '</')
add(AP, '>Категория</', '>' + T('Категория') + '</')
add(AP, '>— Основная категория —<', '>' + T('— Основная категория —') + '<')
add(AP, '>— Подкатегория —<', '>' + T('— Подкатегория —') + '<')
add(AP, '>— Под-подкатегория —<', '>' + T('— Под-подкатегория —') + '<')
add(AP, '>Отмена<', '>' + T('Отмена') + '<')
add(AP, '>Опубликовать<', '>' + T('Опубликовать') + '<')

# ─────────────────────────────────────────────
# 3.  Применяем замены к шаблонам
# ─────────────────────────────────────────────
print("=== Обновление шаблонов ===")
counts = {}
for (path, old, new) in TEMPLATE_REPLACEMENTS:
    if not path.exists():
        print(f"  SKIP (not found): {path.name}")
        continue
    text = path.read_text(encoding='utf-8')
    # Resolve %% → % in the new string (we used %% to avoid .format issues)
    resolved_new = new.replace('%%', '%')
    if old in text:
        text = text.replace(old, resolved_new)
        path.write_text(text, encoding='utf-8')
        counts[path.name] = counts.get(path.name, 0) + 1
    else:
        print(f"  NOT FOUND in {path.name}: {old[:60]!r}")

for name, cnt in counts.items():
    print(f"  {name}: {cnt} replacements")

# ─────────────────────────────────────────────
# 4.  Обновляем .po файлы
# ─────────────────────────────────────────────
# Дополнительные blocktrans-строки, которые нужны в .po
EXTRA_TRANSLATIONS = {
    "Результаты по запросу «%(search_query)s»":
        {"en": "Results for «%(search_query)s»",
         "kk": "«%(search_query)s» іздеу нәтижелері"},
    "По запросу «%(search_query)s» ничего не найдено. Попробуйте другие слова.":
        {"en": "No results for «%(search_query)s». Try different words.",
         "kk": "«%(search_query)s» бойынша ештеңе табылмады. Басқа сөздерді қолданып көріңіз."},
    "Войдите через корпоративную почту AlmaU для авторизации в":
        {"en": "Sign in with your AlmaU corporate email to access",
         "kk": "AlmaU корпоративтік поштасымен кіріңіз"},
    "Входить на платформу могут только сотрудники и студенты":
        {"en": "Only employees and students of AlmaU",
         "kk": "Платформаға тек AlmaU қызметкерлері мен студенттері"},
    "через данные корпоративной почты":
        {"en": "can access using their corporate email",
         "kk": "корпоративтік поштасы арқылы кіре алады"},
}
ALL_TRANSLATIONS = {**TRANSLATIONS, **EXTRA_TRANSLATIONS}

def update_po(lang, translations_dict):
    po_path = BASE / f'locale/{lang}/LC_MESSAGES/django.po'
    po = polib.pofile(str(po_path))
    existing = {e.msgid for e in po}
    added = 0
    for msgid, langs in translations_dict.items():
        msgstr = langs.get(lang, '')
        if msgid not in existing:
            entry = polib.POEntry(msgid=msgid, msgstr=msgstr)
            po.append(entry)
            added += 1
        else:
            # Update empty msgstr
            for e in po:
                if e.msgid == msgid and not e.msgstr:
                    e.msgstr = msgstr
    po.save(str(po_path))
    print(f"  {lang}: +{added} новых записей")

print("\n=== Обновление .po файлов ===")
update_po('en', ALL_TRANSLATIONS)
update_po('kk', ALL_TRANSLATIONS)

# ─────────────────────────────────────────────
# 5.  Компилируем .mo
# ─────────────────────────────────────────────
print("\n=== Компиляция .mo ===")
for po_path in (BASE / 'locale').rglob('django.po'):
    mo_path = po_path.with_suffix('.mo')
    po = polib.pofile(str(po_path))
    po.save_as_mofile(str(mo_path))
    print(f"  Compiled: {mo_path.relative_to(BASE)}")

print("\nГотово!")

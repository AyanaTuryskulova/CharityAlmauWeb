# CharityAlmauWeb

Веб-приложение для студентов AlmaU: обмен, дарение и аренда вещей внутри университета.

## Что есть в проекте

- Лента объявлений с категориями, фильтрами и карточкой товара
- Типы объявлений: `free`, `exchange`, `rental` (аренда через заявки)
- Личный кабинет: мои объявления, редактирование и удаление
- Чаты между пользователями (HTTP + WebSocket через Django Channels)
- Профиль пользователя (аватар, тёмная тема)
- Избранное
- Мультиязычность: русский, казахский, английский
- Push-уведомления (Web Push, VAPID)
- Автоподсказка названия/категории по фото (HuggingFace `transformers` + `torch`)

## Технологии

- Python 3.12 (см. `Dockerfile`)
- Django 5.2
- Django Channels 4
- django-allauth (включая Microsoft provider)
- WhiteNoise для статики
- База данных: SQLite (для локальной разработки) или MySQL (основной сценарий)

## Быстрый старт (локально)

### 1) Установить зависимости

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

### 2) Настроить `.env`

Проект читает переменные из файла `.env` в корне. Минимальный пример:

```env
SECRET_KEY=change-me
DEBUG=True
ALLOWED_HOSTS=127.0.0.1,localhost
CSRF_TRUSTED_ORIGINS=http://127.0.0.1:8000,http://localhost:8000

# Для локальной разработки проще начать с SQLite
USE_SQLITE=true

# Если нужен MySQL, переключите USE_SQLITE=false и задайте:
# SQL_ENGINE=django.db.backends.mysql
# SQL_DB=charity_db
# SQL_USER=root
# SQL_PASSWORD=your_password
# SQL_HOST=127.0.0.1
# SQL_PORT=3306

# Опционально: Microsoft OAuth
# MS_TENANT=common
# MS_CLIENT_ID=
# MS_CLIENT_SECRET=

# Опционально: Web Push
# VAPID_PUBLIC_KEY=
# VAPID_PRIVATE_KEY=
# VAPID_ADMIN_EMAIL=
```

### 3) Применить миграции и (опционально) заполнить категории

```bash
python manage.py migrate
python manage.py populate_categories
```

### 4) Запустить сервер

```bash
python manage.py runserver
```

Приложение будет доступно на `http://127.0.0.1:8000`.

## Запуск через Docker

В репозитории есть `docker-compose.yml` и `Dockerfile`.

```bash
docker compose up --build
```

По текущей конфигурации сервис публикуется на порту `8004`:

- `http://localhost:8004`

При старте контейнер автоматически выполняет:

- `collectstatic`
- `migrate`
- создание суперпользователя (если заданы `DJANGO_SUPERUSER_*` в `.env`)
- запуск `gunicorn`

## Полезные команды

```bash
python manage.py createsuperuser
python manage.py test
python manage.py compilemessages
```

## Важные замечания

- Для WebSocket-чата используется endpoint вида `ws://<host>/ws/chat/<chat_id>/`.
- Модель для распознавания по фото загружается при первом вызове (`google/vit-base-patch16-224`), поэтому первый запрос может быть дольше обычного.
- Не храните секреты в репозитории; используйте только `.env`.


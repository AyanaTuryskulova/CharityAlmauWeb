# Архитектура CharityAlmauWeb

Этот документ описывает текущую архитектуру проекта: модули, связи, потоки данных и окружения запуска.

## 1. Общая схема

Проект построен как Django-монолит с разделением по Django apps:

- `core` — базовый домен (товары, категории, заявки, избранное, общие страницы)
- `core.apps.chat` — чаты, сообщения, push-подписки, WebSocket
- `core.apps.rentals` — аренда товаров
- `core.apps.tenant_profile` — профиль пользователя для сценариев аренды
- `CharityAlmaWeb` — конфигурация проекта (`settings.py`, `urls.py`, `asgi.py`, `wsgi.py`)

Архитектурный стиль:

- Presentation layer: Django views + templates
- Domain/data layer: Django models (ORM)
- Integration layer: allauth (auth/OAuth), Channels (WebSocket), Web Push, HuggingFace inference

## 2. Входные точки и маршрутизация

### HTTP

- Корневые маршруты задаются в `CharityAlmaWeb/urls.py`
- Основной роутер приложения: `core/urls.py`
- Подмодули подключаются через include:
  - `chat/`
  - `rentals/`
  - `profile/`
  - `accounts/` (django-allauth)

### WebSocket

- ASGI entrypoint: `CharityAlmaWeb/asgi.py`
- Канал `websocket` подключает маршруты из `core.apps.chat.routing`
- Текущий ws endpoint чата: `ws/chat/<chat_id>/`

## 3. Данные и доменная модель

### Основные сущности (`core`)

- `Category`
  - Иерархическая структура через self-FK (`parent`)
- `Product`
  - Объявление пользователя: тип (`free`, `exchange`, `rental`), статус, категории, медиа
  - Флаг `is_approved` для модерации
- `ProductImage`
  - Дополнительные фотографии объявления
- `TradeRequest`
  - Заявки на действие с товаром (`take`, `rent`, `exchange`) + жизненный цикл статусов
- `Favorite`
  - Избранное пользователя (unique пара `user + product`)

### Чат (`core.apps.chat`)

- `Chat`
  - Участники (M2M с `User`) + опциональная привязка к `Product`
- `Message`
  - Сообщения, статус прочтения, опциональное изображение
- `PushSubscription`
  - Данные браузерной push-подписки пользователя

### Аренда (`core.apps.rentals`)

- `RentItem`
  - Связь `product` + `renter` + `owner`
  - Статусы: `rented`, `returned`, `cancelled`
  - Периоды аренды и ожидаемая дата возврата

### Профиль (`core.apps.tenant_profile`)

- `UserProfile` (OneToOne c `User`)
  - Телефон, адрес, bio
  - Автосоздание профиля через `post_save` сигнал для новых пользователей

## 4. Ключевые бизнес-потоки

### 4.1 Публикация объявления

1. Пользователь создаёт `Product` (+ основное фото и дополнительные `ProductImage`)
2. При необходимости вызывается сервис автоопределения по фото (`core/services/image_autofill.py`)
3. Объявление проходит модерацию (`is_approved`)
4. После одобрения становится доступно в ленте

### 4.2 Заявки на товар

1. Заинтересованный пользователь создаёт `TradeRequest`
2. Владелец товара обрабатывает заявку (accept/reject)
3. Статусы `TradeRequest` и `Product` синхронно отражают состояние сделки

### 4.3 Чат и обмен сообщениями

1. Между пользователями создаётся/открывается `Chat`
2. Сообщения идут через HTTP endpoints и/или WebSocket канал
3. Непрочитанные сообщения помечаются через `is_read`/`status`
4. При наличии push-подписки возможна доставка Web Push уведомлений

### 4.4 Аренда

1. По товару типа `rental` создаётся `RentItem`
2. Сценарий меняет статус аренды (`rented` -> `returned` / `cancelled`)
3. История аренды доступна пользователю через rentals views

## 5. Конфигурация и окружение

### Переменные окружения (основные)

- Безопасность/хосты: `SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS`, `CSRF_TRUSTED_ORIGINS`
- БД: `USE_SQLITE` или набор `SQL_*` (`SQL_ENGINE`, `SQL_DB`, `SQL_USER`, ...)
- OAuth Microsoft: `MS_TENANT`, `MS_CLIENT_ID`, `MS_CLIENT_SECRET`
- Web Push: `VAPID_PUBLIC_KEY`, `VAPID_PRIVATE_KEY`, `VAPID_ADMIN_EMAIL`

### База данных

- Локально: SQLite (если `USE_SQLITE=true`)
- Основной вариант: MySQL (`mysqlclient`)

### Статика и медиа

- `WhiteNoise` обслуживает статику
- `STATIC_ROOT`: `staticfiles`
- `MEDIA_ROOT`: `media`

## 6. Runtime и деплой

### Локальная разработка

- `python manage.py runserver`
- ASGI-конфигурация уже готова для WebSocket сценариев

### Docker

- `Dockerfile`: Python 3.12 + установка зависимостей
- `docker-compose.yml`:
  - сборка `web` сервиса
  - `collectstatic` + `migrate` при старте
  - опциональное авто-создание superuser по env
  - запуск через `gunicorn`

## 7. Архитектурные ограничения и точки роста

- В `settings.py` Channel Layer сейчас `InMemoryChannelLayer`; для production лучше `channels_redis` + внешний Redis.
- Кодовая база использует function-based views; при росте доменной логики полезно выделять сервисный слой/сценарии use-case.
- API и веб-страницы смешаны в одном слое views; при дальнейшем масштабировании можно вынести явный REST API слой.

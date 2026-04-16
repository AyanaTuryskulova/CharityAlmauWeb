# Charity AlmaU — Как устроен код

> Подробное объяснение архитектуры и кода проекта для IT-студентов.
> Если вы знаете основы JavaScript/TypeScript — вы поймёте всё.

---

## Содержание

1. [Общая картина](#1-общая-картина)
2. [Бэкенд — архитектура](#2-бэкенд--архитектура)
3. [Бэкенд — как запрос проходит от браузера до БД](#3-как-запрос-проходит)
4. [Бэкенд — каждая папка и файл](#4-бэкенд--каждая-папка)
5. [База данных — схема Prisma](#5-база-данных)
6. [Фронтенд — архитектура](#6-фронтенд--архитектура)
7. [Фронтенд — каждая папка и файл](#7-фронтенд--каждая-папка)
8. [Как фронт общается с бэком](#8-как-фронт-общается-с-бэком)
9. [WebSocket и реал-тайм чат](#9-websocket-и-чат)
10. [Аутентификация (кто ты?)](#10-аутентификация)
11. [Загрузка фото](#11-загрузка-фото)
12. [Мультиязычность (i18n)](#12-мультиязычность)

---

## 1. Общая картина

Проект состоит из **двух отдельных приложений**:

```
┌──────────────┐         HTTP/WebSocket         ┌──────────────┐
│   ФРОНТЕНД   │  ←─────────────────────────→   │   БЭКЕНД     │
│   (React)    │       JSON запросы/ответы       │   (Express)  │
│   порт 3000  │                                 │   порт 4000  │
└──────────────┘                                 └──────┬───────┘
                                                        │
                                                        ↓
                                                 ┌──────────────┐
                                                 │  PostgreSQL   │
                                                 │  (База данных)│
                                                 │  порт 5432    │
                                                 └──────────────┘
```

- **Фронтенд** — то, что видит пользователь в браузере. React + TypeScript.
- **Бэкенд** — сервер, который обрабатывает запросы, хранит данные, управляет логикой. Express + TypeScript.
- **PostgreSQL** — база данных, где хранятся пользователи, объявления, сообщения и т.д.

Они общаются через **HTTP API** (REST) и **WebSocket** (для чата в реальном времени).

---

## 2. Бэкенд — архитектура

Бэкенд построен по паттерну **"Контроллер → Сервис → БД"** (он же MVC без V):

```
Запрос от браузера
    ↓
[Middleware] — проверка токена, валидация, фильтр мата
    ↓
[Route]     — определяет какой контроллер вызвать
    ↓
[Controller] — принимает запрос, вызывает сервис, отправляет ответ
    ↓
[Service]    — бизнес-логика (что делать с данными)
    ↓
[Prisma]     — ORM, общается с PostgreSQL
    ↓
[PostgreSQL] — хранит данные
```

### Зачем разделять?

- **Middleware** — переиспользуемая проверка (авторизация на всех роутах)
- **Controller** — только "принять запрос, отдать ответ" (тонкий)
- **Service** — вся логика (можно тестировать отдельно, переиспользовать)

---

## 3. Как запрос проходит

Пример: пользователь открывает каталог объявлений.

```
1. Браузер делает GET http://localhost:4000/api/listings?type=FREE&page=1

2. Express принимает запрос

3. Middleware (auth.ts → optionalAuth):
   — Если есть токен → декодирует → добавляет userId в запрос
   — Если нет → пропускает дальше (объявления можно смотреть без логина)

4. Route (listings.routes.ts):
   — GET /api/listings → вызывает listingsController.getAll

5. Controller (listings.controller.ts → getAll):
   — Достаёт параметры из query: type, page, limit, search...
   — Вызывает listingsService.getAll(params, userId)

6. Service (listings.service.ts → getAll):
   — Строит Prisma-запрос с фильтрами
   — Добавляет пагинацию (offset, limit)
   — Добавляет данные о продавце (user: { name, rating })
   — Проверяет, добавлено ли в избранное (isFavorited)
   — Возвращает { data: [...], meta: { page, total, ... } }

7. Controller отправляет JSON-ответ:
   { success: true, data: [...15 объявлений...], meta: { page: 1, total: 15 } }

8. Браузер получает JSON и рисует карточки
```

---

## 4. Бэкенд — каждая папка

### `src/index.ts` — Точка входа
Запускает HTTP-сервер и WebSocket (Socket.IO). Всё начинается здесь:
```
1. Импортирует Express app из app.ts
2. Создаёт HTTP сервер
3. Инициализирует Socket.IO (для чатов)
4. Запускает сервер на порту из .env
```

### `src/app.ts` — Настройка Express
Здесь собирается приложение:
```
1. Создаёт Express app
2. Подключает middleware: CORS, Helmet (безопасность), JSON-парсер, Morgan (логи)
3. Подключает статику: /uploads → раздаёт загруженные фото
4. Подключает все маршруты: /api/auth, /api/listings, /api/chat и т.д.
5. Подключает обработчик ошибок (самый последний middleware)
```

### `src/config/`

| Файл | Что делает |
|------|------------|
| `env.ts` | Загружает `.env` файл. Проверяет что все нужные переменные заданы. Экспортирует объект `env`. |
| `prisma.ts` | Создаёт единственный экземпляр Prisma Client (синглтон). Все сервисы используют один и тот же объект для работы с БД. |

### `src/middleware/`

| Файл | Что делает |
|------|------------|
| `auth.ts` | **`auth`** — проверяет JWT-токен из заголовка `Authorization: Bearer xxx`. Если токен невалидный → 401. Добавляет данные пользователя в `req.user`. **`optionalAuth`** — то же, но не блокирует если токена нет. |
| `admin.ts` | Проверяет что `req.user.role === 'ADMIN'`. Если нет → 403 Forbidden. Используется после `auth`. |
| `upload.ts` | Настраивает Multer для загрузки файлов в память. Ограничения: 5MB, 5 файлов, только JPEG/PNG/WebP. После загрузки конвертирует в WebP через Sharp. |
| `validate.ts` | Принимает Zod-схему и проверяет тело запроса. Если данные невалидны → 400 с описанием ошибки. |
| `badWords.ts` | Фильтрует мат на русском, казахском и английском. Проверяет title, description, message. Нормализует символы (@→a, 0→o). |
| `errorHandler.ts` | Глобальный обработчик ошибок. Ловит все ошибки, форматирует в `{ success: false, error: { code, message } }`. |

### `src/routes/`

Каждый файл определяет URL-адреса и привязывает их к контроллерам:

| Файл | Основные эндпоинты |
|------|---------------------|
| `auth.routes.ts` | `GET /login` (редирект на Microsoft), `GET /callback` (обработка OAuth), `POST /dev-login` (для разработки), `GET /me` (текущий пользователь) |
| `listings.routes.ts` | `GET /` (все объявления), `GET /:id` (одно), `POST /` (создать), `PUT /:id` (обновить), `DELETE /:id` (удалить), `GET /:id/similar` (похожие) |
| `requests.routes.ts` | `POST /` (откликнуться), `GET /incoming` (входящие), `GET /outgoing` (исходящие), `PATCH /:id/accept`, `PATCH /:id/reject`, `PATCH /:id/cancel` |
| `chat.routes.ts` | `GET /rooms` (комнаты), `POST /rooms` (создать), `GET /rooms/:id/messages` (история), `POST /rooms/:id/read` (прочитано) |
| `users.routes.ts` | `GET /:id` (профиль), `PUT /me` (обновить свой), `GET /:id/ratings` (отзывы), `POST /:id/ratings` (оставить отзыв) |
| `favorites.routes.ts` | `POST /` (добавить), `DELETE /:listingId` (убрать), `GET /` (мои избранные) |
| `admin.routes.ts` | `GET /listings` (на модерации), `PATCH /listings/:id/approve`, `PATCH /listings/:id/reject`, `GET /stats` |
| `ai.routes.ts` | `POST /analyze-image` (AI определяет что на фото) |

### `src/controllers/`

Контроллеры — тонкие. Они:
1. Достают данные из `req.params`, `req.query`, `req.body`
2. Вызывают соответствующий сервис
3. Отправляют ответ через `res.json()`

Пример (упрощённо):
```typescript
async getAll(req, res) {
  const { page, type, search } = req.query;
  const userId = req.user?.userId; // из middleware auth
  const result = await listingsService.getAll({ page, type, search }, userId);
  res.json({ success: true, ...result });
}
```

### `src/services/`

Здесь вся бизнес-логика:

| Файл | Что делает |
|------|------------|
| `auth.service.ts` | Обмен OAuth кода на токен через MSAL, проверка @almau.edu.kz, создание/обновление пользователя в БД, генерация JWT |
| `listings.service.ts` | CRUD объявлений, поиск (ILIKE), фильтрация по типу/категории, пагинация, похожие объявления, проверка isFavorited |
| `requests.service.ts` | Создание запроса (с проверкой: нельзя на своё, нельзя дважды), принятие/отклонение/отмена |
| `chat.service.ts` | Создание комнат (с дедупликацией), получение сообщений с пагинацией, отправка, пометка прочитанным |
| `users.service.ts` | Получение профиля, обновление (имя, аватар), рейтинги |
| `favorites.service.ts` | Добавление/удаление избранного, получение списка |
| `admin.service.ts` | Список на модерации, одобрение/отклонение, статистика |
| `ai.service.ts` | Отправка фото в OpenAI GPT-4o-mini, получение предложенных title и category |
| `badWords.service.ts` | Массивы мат-слов (RU/KZ/EN), функция проверки с нормализацией символов |

### `src/socket/`

| Файл | Что делает |
|------|------------|
| `index.ts` | Инициализация Socket.IO. Проверяет JWT при подключении. Автоматически добавляет пользователя в комнату `user:{userId}` для уведомлений. |
| `chatHandler.ts` | Обрабатывает события: `chat:join` (войти в комнату), `chat:message` (отправить), `chat:typing` (печатает...), `chat:read` (прочитал). |

### `src/utils/`

| Файл | Что делает |
|------|------------|
| `jwt.ts` | `signToken(payload)` — создаёт JWT. `verifyToken(token)` — проверяет и возвращает payload. |
| `pagination.ts` | Вычисляет `skip` и `take` для Prisma из `page` и `limit`. Формирует объект `meta`. |
| `errors.ts` | Класс `AppError` с кодом и HTTP-статусом. Коды: `LISTING_NOT_FOUND`, `AUTH_REQUIRED` и т.д. |
| `imageProcessing.ts` | Обработка фото через Sharp: ресайз (макс 1200px ширина), конвертация в WebP, сжатие. Для аватаров — квадратный кроп 400×400. |

### `src/types/index.ts`

TypeScript-интерфейсы:
- `JwtPayload` — что внутри JWT-токена: `{ userId, email, role }`
- `AuthRequest` — Express Request с добавленным `user`
- `PaginationMeta` — `{ page, limit, total, totalPages }`

### `prisma/`

| Файл | Что делает |
|------|------------|
| `schema.prisma` | Описание всех таблиц БД (модели, связи, индексы). Prisma по нему генерирует TypeScript-клиент и SQL-миграции. |
| `seed.ts` | Скрипт для заполнения БД тестовыми данными: 1 админ, 5 студентов, 15 объявлений, запросы, чаты, рейтинги. |
| `migrations/` | SQL-файлы миграций (автогенерация). Каждая миграция = изменение схемы БД. |

---

## 5. База данных

### Модели и связи

```
User (пользователь)
  ├── Listing[]        — его объявления
  ├── Favorite[]       — его избранное
  ├── Request[] (sent) — его отклики
  ├── Request[] (recv) — отклики на его объявления
  ├── ChatRoom[]       — его чаты
  ├── Message[]        — его сообщения
  └── Rating[]         — его отзывы (данные и полученные)

Listing (объявление)
  ├── User             — автор
  ├── Favorite[]       — кто добавил в избранное
  └── Request[]        — отклики

ChatRoom (чат-комната)
  ├── User (user1)     — первый участник
  ├── User (user2)     — второй участник
  └── Message[]        — сообщения
```

### Enum-ы (перечисления)

```
ListingType:   FREE (бесплатно), EXCHANGE (обмен), RENT (аренда)
ListingStatus: PENDING (на модерации), APPROVED, REJECTED, CLOSED
Category:      TEXTBOOKS, TECH, FURNITURE, CLOTHING, SPORTS, STATIONERY, OTHER
RequestStatus: PENDING, ACCEPTED, REJECTED, CANCELLED
Role:          USER, ADMIN
```

### Как Prisma работает

Prisma — это ORM (Object-Relational Mapping). Вместо написания SQL, вы пишете TypeScript:

```typescript
// SQL: SELECT * FROM listings WHERE type = 'FREE' AND status = 'APPROVED' LIMIT 20
// Prisma:
const listings = await prisma.listing.findMany({
  where: { type: 'FREE', status: 'APPROVED' },
  take: 20,
  include: { user: { select: { name: true, rating: true } } },
});
```

Prisma генерирует типы автоматически — если в схеме есть модель `Listing`, то в коде будет тип `Listing` со всеми полями.

---

## 6. Фронтенд — архитектура

Фронтенд — React SPA (Single Page Application). Одна HTML-страница, всё переключается через JavaScript.

### Структура:

```
src/
├── main.tsx          — точка входа, рендерит <App />
├── App.tsx           — оборачивает в провайдеры (Auth, Chat, i18n)
├── router.tsx        — все маршруты (URL → какую страницу показать)
├── types/            — TypeScript-типы (что приходит с бэкенда)
├── config/           — настройки (i18n, Microsoft OAuth)
├── contexts/         — глобальное состояние (React Context)
├── services/         — функции для вызова API (axios)
├── hooks/            — кастомные хуки (переиспользуемая логика)
├── components/       — UI-компоненты
│   ├── layout/       — Header, Footer, навигация
│   ├── common/       — кнопки, модалки, аватары (переиспользуемые)
│   ├── listings/     — карточки, фильтры, формы объявлений
│   ├── chat/         — окно чата, сообщения
│   ├── profile/      — профиль, отзывы
│   ├── requests/     — заявки
│   └── admin/        — модерация
└── pages/            — страницы (собирают компоненты)
```

### Как данные текут:

```
[Страница]
    ↓ вызывает
[Хук] (useListings, useChats...)
    ↓ вызывает
[Сервис] (listingsService.getAll())
    ↓ делает HTTP-запрос через
[Axios] → бэкенд API
    ↓ ответ
[Хук] сохраняет в useState
    ↓
[Страница] рендерит [Компоненты] с данными
```

---

## 7. Фронтенд — каждая папка

### `src/types/`

TypeScript-типы, описывающие данные с бэкенда:

| Файл | Содержит |
|------|----------|
| `user.ts` | `User` — id, email, name, role, rating, avatarUrl... |
| `listing.ts` | `Listing` — id, title, type, category, images, user, isFavorited... |
| `chat.ts` | `ChatRoom` — otherUser, lastMessage, unreadCount. `Message` — text, senderId, createdAt. |
| `request.ts` | `Request` — listing, sender, receiver, status, message |
| `rating.ts` | `Rating` — score, comment, author |
| `api.ts` | `ApiResponse<T>` — обёртка ответа: `{ success, data, meta? }` |

### `src/contexts/`

React Context — глобальное состояние, доступное в любом компоненте:

| Файл | Что хранит |
|------|------------|
| `AuthContext.tsx` | Текущий пользователь (`user`), токен, функции `login()` и `logout()`. При загрузке приложения проверяет токен из localStorage и загружает данные пользователя. |
| `ChatContext.tsx` | Список чат-комнат, количество непрочитанных, WebSocket-соединение. Подключается к Socket.IO при логине. Обрабатывает новые сообщения, typing-индикаторы. |
| `NotificationContext.tsx` | Уведомления (новые запросы, результаты модерации). Слушает Socket.IO события. |

### `src/services/`

Функции для вызова API через Axios:

| Файл | Что делает |
|------|------------|
| `api.ts` | Создаёт Axios-инстанс. Автоматически добавляет JWT-токен в заголовки. При 401 ошибке — удаляет токен и перенаправляет на логин. |
| `authService.ts` | `devLogin(email, name)`, `getMe()`, `getLoginUrl()` |
| `listingsService.ts` | `getListings(params)`, `getListing(id)`, `createListing(formData)`, `updateListing()`, `deleteListing()` |
| `chatService.ts` | `getRooms()`, `createRoom(otherUserId)`, `getMessages(roomId)`, `markRead(roomId)` |
| `requestsService.ts` | `createRequest(listingId)`, `getIncoming()`, `getOutgoing()`, `accept()`, `reject()`, `cancel()` |
| `userService.ts` | `getUser(id)`, `updateMe(formData)`, `getRatings()`, `postRating()` |
| `favoritesService.ts` | `addFavorite(id)`, `removeFavorite(id)`, `getFavorites()` |
| `adminService.ts` | `getPendingListings()`, `approve(id)`, `reject(id, reason)`, `getStats()` |
| `socketService.ts` | Управление WebSocket: `connect(token)`, `sendMessage()`, `joinRoom()`, обработчики событий |
| `aiService.ts` | `analyzeImage(file)` — отправляет фото для AI-анализа |

### `src/hooks/`

Кастомные хуки — переиспользуемая логика с состоянием:

| Файл | Что делает |
|------|------------|
| `useListings.ts` | Загружает список объявлений с фильтрами и пагинацией. Возвращает `{ listings, meta, loading, error, refetch }`. |
| `useListing.ts` | Загружает одно объявление по ID. |
| `useChats.ts` | Обёртка над ChatContext — возвращает комнаты, загрузку, ошибки. |
| `useMessages.ts` | Загружает сообщения комнаты, подписывается на новые, поддерживает "загрузить ещё". |
| `useRequests.ts` | Загружает входящие/исходящие запросы. |
| `useFavorites.ts` | Загружает избранное. |
| `useUserProfile.ts` | Загружает профиль пользователя и его отзывы. |
| `useDebounce.ts` | Задерживает значение (для поиска — не отправлять запрос на каждую букву, а подождать 400мс). |

### `src/pages/`

Каждая страница — отдельный файл + CSS Module:

| Страница | URL | Что делает |
|----------|-----|------------|
| `LoginPage` | `/login` | Форма входа (Microsoft OAuth + Dev Login) |
| `AuthCallbackPage` | `/auth/callback` | Обрабатывает редирект после Microsoft OAuth |
| `HomePage` | `/` | Каталог объявлений с фильтрами по типу и категории |
| `ListingDetailPage` | `/listings/:id` | Детальная страница объявления с фото, описанием, кнопками "Откликнуться" и "Написать" |
| `CreateListingPage` | `/listings/new` | Форма создания объявления |
| `EditListingPage` | `/listings/:id/edit` | Редактирование объявления |
| `MyListingsPage` | `/my-listings` | Мои объявления (все статусы) |
| `FavoritesPage` | `/favorites` | Избранные объявления |
| `RequestsPage` | `/requests` | Входящие и исходящие заявки |
| `ChatsPage` | `/chats` `/chats/:chatId` | Список чатов + окно переписки |
| `ProfilePage` | `/profile` | Свой профиль (объявления, избранное, отзывы) |
| `EditProfilePage` | `/profile/edit` | Редактирование профиля |
| `UserProfilePage` | `/users/:userId` | Профиль другого пользователя |
| `AdminPage` | `/admin` | Панель модерации (только для ADMIN) |

### `src/components/`

#### `layout/` — Каркас страницы

- **Layout.tsx** — оборачивает все страницы (Header + контент + Footer)
- **Header.tsx** — логотип, навигация, поиск, кнопка "+ Добавить", аватар
- **Footer.tsx** — копирайт, ссылки, переключатель языков
- **MobileNav.tsx** — нижняя навигация на мобильных

#### `common/` — Переиспользуемые компоненты

- **Button** — кнопка с вариантами (primary, secondary, accent) и состоянием загрузки
- **Input** — поле ввода с лейблом и ошибкой
- **Modal** — модальное окно (оверлей, закрытие по Esc)
- **Avatar** — аватар пользователя (фото или первая буква имени)
- **Badge** — бейдж ("Даром", "Обмен", "Аренда")
- **Loader** — спиннер загрузки
- **EmptyState** — заглушка "Пока ничего нет"
- **ErrorState** — заглушка "Что-то пошло не так" с кнопкой "Повторить"
- **Pagination** — переключатель страниц
- **StarRating** — звёздочки рейтинга (1-5)
- **ImageUpload** — загрузка фото с превью и drag-n-drop
- **ProtectedRoute** — редирект на /login если не авторизован
- **AdminRoute** — редирект если не админ
- **LanguageSwitcher** — переключатель RU/KZ/EN

#### `listings/` — Компоненты объявлений

- **ListingCard** — карточка (фото, название, цена, сердечко)
- **ListingGrid** — сетка карточек
- **ListingFilters** — фильтры по типу и категории
- **ListingForm** — форма создания/редактирования
- **PhotoGallery** — галерея фото с переключением
- **SellerCard** — блок продавца (аватар, имя, рейтинг)
- **SimilarItems** — похожие объявления
- **RentalTerms** — условия аренды (цена за день/неделю/месяц)
- **SearchBar** — строка поиска

#### `chat/` — Компоненты чата

- **ChatSidebar** — список чат-комнат (слева)
- **ChatWindow** — окно переписки (справа)
- **MessageBubble** — одно сообщение (своё справа, чужое слева)
- **MessageInput** — поле ввода сообщения
- **TypingIndicator** — "печатает..."

#### `profile/` — Компоненты профиля

- **ProfileHeader** — аватар, имя, рейтинг, количество объявлений
- **ProfileTabs** — вкладки (объявления / избранное / отзывы)
- **ReviewCard** — карточка отзыва
- **ReviewForm** — форма оставить отзыв

#### `requests/` — Компоненты заявок

- **RequestList** — список заявок (входящие/исходящие)
- **RequestCard** — карточка заявки с кнопками (принять/отклонить/отменить)

#### `admin/` — Компоненты админки

- **ModerationQueue** — очередь на модерацию
- **ModerationCard** — карточка объявления с кнопками "Одобрить" / "Отклонить"

---

## 8. Как фронт общается с бэком

### HTTP-запросы (REST API)

Фронтенд делает запросы через Axios:

```typescript
// services/api.ts — настроенный Axios
const api = axios.create({
  baseURL: 'http://localhost:4000/api',
});

// Автоматически добавляет токен:
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

// Автоматически разворачивает ответ:
api.interceptors.response.use(
  (response) => response.data,  // { success, data, meta }
  (error) => { /* обработка ошибок */ }
);
```

### Формат ответов бэкенда

Все ответы имеют одинаковую структуру:

```json
// Успех:
{
  "success": true,
  "data": { ... },
  "meta": { "page": 1, "total": 42, "totalPages": 3 }
}

// Ошибка:
{
  "success": false,
  "error": { "code": "LISTING_NOT_FOUND", "message": "Listing not found" }
}
```

---

## 9. WebSocket и чат

### Зачем WebSocket?

HTTP работает так: клиент спрашивает → сервер отвечает. Сервер **не может** сам послать данные клиенту.

WebSocket — постоянное соединение. Сервер может отправить данные клиенту **в любой момент** (новое сообщение, "печатает...", уведомление).

### Как это работает:

```
1. Пользователь логинится → фронтенд подключается к Socket.IO с JWT-токеном
2. Сервер проверяет токен → добавляет в личную комнату user:{id}
3. Пользователь открывает чат → фронтенд шлёт chat:join {roomId}
4. Сервер добавляет в комнату chatroom:{roomId}
5. Пользователь пишет → фронтенд шлёт chat:message {roomId, text}
6. Сервер сохраняет в БД → шлёт chat:message всем в комнате
7. У получателя моментально появляется сообщение (без перезагрузки)
```

### События:

| Событие | Направление | Данные |
|---------|-------------|--------|
| `chat:join` | Клиент → Сервер | `{ roomId }` |
| `chat:message` | Оба направления | `{ roomId, text }` / `{ id, text, senderId, createdAt }` |
| `chat:typing` | Оба направления | `{ roomId }` / `{ roomId, userId }` |
| `chat:read` | Оба направления | `{ roomId }` / `{ roomId, userId }` |
| `notification:request` | Сервер → Клиент | `{ requestId, senderName, listingTitle }` |

---

## 10. Аутентификация

### Как работает вход:

**Microsoft OAuth (production):**
```
1. Пользователь нажимает "Войти через Microsoft"
2. Редирект на login.microsoftonline.com
3. Вводит @almau.edu.kz логин/пароль
4. Microsoft редиректит обратно с кодом: /api/auth/callback?code=xxx
5. Бэкенд обменивает код на данные пользователя (email, имя)
6. Проверяет что email заканчивается на @almau.edu.kz
7. Создаёт/обновляет пользователя в БД
8. Генерирует JWT-токен
9. Редиректит фронтенд с токеном: /auth/callback?token=xxx
10. Фронтенд сохраняет токен в localStorage
```

**Dev Login (разработка):**
```
1. POST /api/auth/dev-login { email, name }
2. Бэкенд создаёт пользователя (если нет) и генерирует JWT
3. Возвращает { token, user }
```

### JWT (JSON Web Token):

Токен — зашифрованная строка, содержащая:
```json
{ "userId": "abc-123", "email": "student@almau.edu.kz", "role": "USER" }
```

Фронтенд хранит токен в `localStorage` и отправляет в каждом запросе:
```
Authorization: Bearer eyJhbGciOiJIUzI1NiIs...
```

Бэкенд проверяет и декодирует токен → знает кто делает запрос.

---

## 11. Загрузка фото

### Как работает:

```
1. Пользователь выбирает фото в <ImageUpload />
2. Фронтенд создаёт FormData с файлами
3. POST /api/listings (multipart/form-data)
4. Бэкенд middleware (upload.ts):
   — Multer сохраняет файл в память (Buffer)
   — Проверяет: тип (JPEG/PNG/WebP), размер (до 5MB), количество (до 5)
5. imageProcessing.ts:
   — Sharp ресайзит до 1200px по ширине
   — Конвертирует в WebP (quality 80)
   — Сохраняет в папку uploads/ с UUID-именем
6. В БД сохраняется путь: "/uploads/abc123.webp"
7. Фронтенд показывает: <img src="http://backend/uploads/abc123.webp" />
```

---

## 12. Мультиязычность

Проект поддерживает 3 языка: русский, казахский, английский.

### Как устроено:

- Библиотека: `i18next` + `react-i18next`
- Переводы хранятся в JSON-файлах: `public/locales/{язык}/{модуль}.json`
- Каждый модуль — отдельный файл: `common.json`, `listings.json`, `chat.json` и т.д.

### Пример использования:

```typescript
// В компоненте:
const { t } = useTranslation('listings');
return <h1>{t('types.FREE')}</h1>; // → "Даром" (ru) / "Тегін" (kz) / "Free" (en)
```

### Структура перевода:

```json
// public/locales/ru/listings.json
{
  "types": {
    "FREE": "Даром",
    "EXCHANGE": "Обмен",
    "RENT": "Аренда"
  },
  "categories": {
    "TEXTBOOKS": "Учебники",
    "TECH": "Техника"
  }
}
```

Чтобы добавить перевод: добавьте ключ в JSON-файл **каждого** языка (ru, kz, en).

---

## Итого: что где искать

| Хочу... | Куда смотреть |
|---------|---------------|
| Добавить новый API-эндпоинт | `routes/` → `controllers/` → `services/` |
| Изменить структуру БД | `prisma/schema.prisma` → `npx prisma migrate dev` |
| Добавить новую страницу | `pages/` + `router.tsx` |
| Изменить UI компонента | `components/` + `.module.css` |
| Добавить перевод | `public/locales/{ru,kz,en}/` |
| Изменить бизнес-логику | `services/` (бэкенд) |
| Добавить валидацию | `middleware/validate.ts` + Zod-схема |
| Исправить стили | `.module.css` файл рядом с компонентом |
| Изменить глобальные стили/цвета | `src/global.css` (CSS variables) |

# Charity AlmaU — Гайд по запуску и деплою

> Этот гайд написан для тех, кто впервые работает с этим проектом.
> Читайте по порядку, не пропускайте шаги.

---

## Содержание

1. [Что нужно установить](#1-что-нужно-установить)
2. [Запуск локально (на своём компьютере)](#2-запуск-локально)
3. [Деплой бэкенда](#3-деплой-бэкенда)
4. [Деплой фронтенда](#4-деплой-фронтенда)
5. [Как связать фронт и бэк между собой](#5-как-связать-фронт-и-бэк)
6. [Настройка Microsoft OAuth (вход через AlmaU)](#6-настройка-microsoft-oauth)
7. [Частые проблемы и решения](#7-частые-проблемы)

---

## 1. Что нужно установить

Перед началом убедитесь, что на компьютере стоят:

| Программа | Зачем | Как проверить | Где скачать |
|-----------|-------|---------------|-------------|
| **Node.js 20+** | Запускает JavaScript на сервере | `node --version` | https://nodejs.org |
| **npm** | Менеджер пакетов (идёт с Node.js) | `npm --version` | Вместе с Node.js |
| **PostgreSQL 16** | База данных | `psql --version` | https://www.postgresql.org/download/ |
| **Git** | Контроль версий | `git --version` | https://git-scm.com |

### Для macOS (через Homebrew):
```bash
brew install node postgresql@16 git
brew services start postgresql@16
```

### Для Windows:
1. Скачайте Node.js с https://nodejs.org (LTS версию)
2. Скачайте PostgreSQL с https://www.postgresql.org/download/windows/
3. При установке PostgreSQL запомните пароль для пользователя `postgres`
4. Скачайте Git с https://git-scm.com/download/win

### Для Linux (Ubuntu/Debian):
```bash
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install -y nodejs postgresql git
sudo systemctl start postgresql
```

---

## 2. Запуск локально

### Шаг 1: Создайте базу данных

```bash
# macOS / Linux:
createdb charity_almau

# Windows (в командной строке PostgreSQL):
psql -U postgres
CREATE DATABASE charity_almau;
\q
```

### Шаг 2: Запустите бэкенд

```bash
# Перейдите в папку бэкенда
cd charity-almau-backend

# Установите зависимости
npm install

# Создайте файл .env (скопируйте из примера)
cp .env.example .env
```

Теперь откройте файл `.env` в любом редакторе и заполните:

```env
PORT=4000
NODE_ENV=development

# Строка подключения к PostgreSQL
# Формат: postgresql://ПОЛЬЗОВАТЕЛЬ:ПАРОЛЬ@ХОСТ:ПОРТ/ИМЯ_БАЗЫ
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/charity_almau
# ⚠️ На Windows замените пароль на тот, что указали при установке PostgreSQL

JWT_SECRET=charity-almau-super-secret-key-2026-min32chars!!
JWT_EXPIRES_IN=7d

# Microsoft OAuth (пока оставьте как есть, см. раздел 6)
MSAL_CLIENT_ID=your-azure-app-client-id
MSAL_CLIENT_SECRET=your-azure-app-client-secret
MSAL_TENANT_ID=your-azure-tenant-id
MSAL_REDIRECT_URI=http://localhost:4000/api/auth/callback

# OpenAI API ключ (для AI-анализа фото, необязательно)
OPENAI_API_KEY=sk-your-openai-key

UPLOAD_DIR=./uploads
MAX_FILE_SIZE_MB=5
MAX_FILES_PER_LISTING=5

CORS_ORIGIN=http://localhost:3000
```

Продолжаем:

```bash
# Примените миграции (создаст таблицы в БД)
npx prisma migrate dev

# Заполните БД тестовыми данными
npm run db:seed

# Запустите сервер
npm run dev
```

Вы должны увидеть: `Server running on http://localhost:4000 [development]`

Проверьте: откройте http://localhost:4000 в браузере — должен показать ответ.

### Шаг 3: Запустите фронтенд

```bash
# В НОВОМ терминале (бэкенд пусть работает)
cd charity-almau-frontend

# Установите зависимости
npm install

# Создайте файл .env
```

Создайте файл `.env` в корне фронтенда:

```env
VITE_API_URL=http://localhost:4000
VITE_WS_URL=http://localhost:4000
VITE_MSAL_CLIENT_ID=your-azure-app-client-id
VITE_MSAL_AUTHORITY=https://login.microsoftonline.com/your-tenant-id
VITE_MSAL_REDIRECT_URI=http://localhost:3000/auth/callback
```

```bash
# Запустите фронтенд
npm run dev
```

Вы увидите: `Local: http://localhost:3000/`

Откройте http://localhost:3000 в браузере. Готово!

### Как войти (без Microsoft OAuth):

На странице логина внизу есть раздел "Dev Login". Введите:
- Email: `student1@almau.edu.kz` (или любой @almau.edu.kz)
- Имя: любое

Для входа как админ: `admin@almau.edu.kz`

> ⚠️ Dev Login работает ТОЛЬКО когда `NODE_ENV=development` в бэкенде.

---

## 3. Деплой бэкенда

### Вариант A: Railway (самый простой, бесплатный)

[Railway](https://railway.app) — платформа для деплоя, есть бесплатный тариф.

1. Зарегистрируйтесь на https://railway.app
2. Создайте новый проект → "Deploy from GitHub repo" (или "Empty project")
3. Добавьте **PostgreSQL** сервис: нажмите "+ New" → "Database" → "PostgreSQL"
4. Добавьте **бэкенд** сервис: "+ New" → "GitHub Repo" или загрузите код
5. В настройках бэкенд-сервиса → Variables, добавьте:

```
DATABASE_URL=<скопируйте из PostgreSQL сервиса>
PORT=4000
NODE_ENV=production
JWT_SECRET=<придумайте длинный случайный ключ>
JWT_EXPIRES_IN=7d
CORS_ORIGIN=https://ваш-фронтенд.vercel.app
UPLOAD_DIR=./uploads
MAX_FILE_SIZE_MB=5
MAX_FILES_PER_LISTING=5
```

6. В Settings → Build Command: `npm install && npx prisma migrate deploy && npm run build`
7. Start Command: `npm start`
8. После деплоя Railway даст URL вроде `https://charity-almau-backend-xxx.railway.app`

### Вариант B: Supabase (только база данных) + любой хостинг для сервера

Supabase даёт бесплатную PostgreSQL базу данных.

**Шаг 1: Получите базу данных от Supabase**

1. Зарегистрируйтесь на https://supabase.com
2. Создайте новый проект, придумайте пароль для БД
3. Перейдите в Settings → Database → Connection string → URI
4. Скопируйте строку подключения, она выглядит так:
   ```
   postgresql://postgres.[ref]:[password]@aws-0-[region].pooler.supabase.com:6543/postgres
   ```
5. Замените `[password]` на пароль, который вы указали при создании проекта

**Шаг 2: Задеплойте сервер**

Сервер можно разместить на:
- **Railway** (см. выше, но без их PostgreSQL — используйте Supabase URL)
- **Render.com** — бесплатный тариф, похож на Railway
- **VPS сервер** (университетский) — см. Вариант C

Где бы вы ни разместили сервер, укажите `DATABASE_URL` от Supabase.

**Шаг 3: Примените миграции к Supabase БД**

```bash
# Локально, в папке бэкенда:
DATABASE_URL="postgresql://postgres.[ref]:[password]@aws-0-[region].pooler.supabase.com:6543/postgres" npx prisma migrate deploy
```

### Вариант C: Docker на университетском сервере

Если университет даёт доступ к серверу (VPS/VM), используйте Docker.

**Шаг 1: Создайте `Dockerfile` в папке бэкенда:**

```dockerfile
FROM node:20-alpine

WORKDIR /app

COPY package*.json ./
RUN npm ci --only=production

COPY prisma ./prisma/
RUN npx prisma generate

COPY . .
RUN npm run build

RUN mkdir -p uploads

EXPOSE 4000
CMD ["sh", "-c", "npx prisma migrate deploy && node dist/index.js"]
```

**Шаг 2: Создайте `docker-compose.yml` (в корне проекта, рядом с обеими папками):**

```yaml
version: "3.8"

services:
  db:
    image: postgres:16-alpine
    restart: always
    environment:
      POSTGRES_DB: charity_almau
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: supersecretpassword
    volumes:
      - pgdata:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  backend:
    build: ./charity-almau-backend
    restart: always
    depends_on:
      - db
    environment:
      DATABASE_URL: postgresql://postgres:supersecretpassword@db:5432/charity_almau
      PORT: "4000"
      NODE_ENV: production
      JWT_SECRET: your-super-secret-jwt-key-min-32-chars!!
      JWT_EXPIRES_IN: 7d
      CORS_ORIGIN: https://your-frontend-domain.com
      UPLOAD_DIR: ./uploads
      MAX_FILE_SIZE_MB: "5"
      MAX_FILES_PER_LISTING: "5"
    volumes:
      - uploads:/app/uploads
    ports:
      - "4000:4000"

  frontend:
    build:
      context: ./charity-almau-frontend
      args:
        VITE_API_URL: https://your-backend-domain.com
        VITE_WS_URL: https://your-backend-domain.com
    restart: always
    ports:
      - "3000:80"

volumes:
  pgdata:
  uploads:
```

**Шаг 3: Создайте `Dockerfile` в папке фронтенда:**

```dockerfile
FROM node:20-alpine AS build

WORKDIR /app

ARG VITE_API_URL
ARG VITE_WS_URL

ENV VITE_API_URL=$VITE_API_URL
ENV VITE_WS_URL=$VITE_WS_URL

COPY package*.json ./
RUN npm ci

COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html

# Для SPA роутинга
RUN echo 'server { \
  listen 80; \
  location / { \
    root /usr/share/nginx/html; \
    try_files $uri $uri/ /index.html; \
  } \
}' > /etc/nginx/conf.d/default.conf

EXPOSE 80
```

**Шаг 4: Запуск на сервере:**

```bash
# Скопируйте оба проекта и docker-compose.yml на сервер
scp -r . user@server:/home/user/charity-almau/

# На сервере:
ssh user@server
cd /home/user/charity-almau
docker compose up -d --build

# Заполнить тестовыми данными:
docker compose exec backend npx tsx prisma/seed.ts
```

Сайт будет доступен на `http://server-ip:3000`, API на `http://server-ip:4000`.

---

## 4. Деплой фронтенда

### Вариант A: Vercel (рекомендуется, бесплатно)

1. Зарегистрируйтесь на https://vercel.com
2. Нажмите "Add New Project"
3. Импортируйте репозиторий с GitHub (или загрузите папку)
4. В настройках:
   - **Framework Preset**: Vite
   - **Build Command**: `npm run build`
   - **Output Directory**: `dist`
5. Добавьте Environment Variables:

```
VITE_API_URL=https://ваш-бэкенд-url.railway.app
VITE_WS_URL=https://ваш-бэкенд-url.railway.app
VITE_MSAL_CLIENT_ID=ваш-azure-client-id
VITE_MSAL_AUTHORITY=https://login.microsoftonline.com/ваш-tenant-id
VITE_MSAL_REDIRECT_URI=https://ваш-сайт.vercel.app/auth/callback
```

6. Нажмите "Deploy"
7. Vercel даст URL вроде `https://charity-almau.vercel.app`

> ⚠️ После деплоя фронтенда обновите `CORS_ORIGIN` в бэкенде на URL фронтенда!

### Вариант B: Netlify (альтернатива Vercel)

1. https://netlify.com → "Add new site"
2. Перетащите папку `dist` (после `npm run build`) или свяжите с GitHub
3. Build settings: `npm run build`, publish: `dist`
4. Environment Variables — те же что для Vercel
5. Для SPA роутинга создайте файл `public/_redirects`:
   ```
   /* /index.html 200
   ```

### Вариант C: Docker (если через университетский сервер)

См. docker-compose.yml в разделе 3C — фронтенд уже включён.

---

## 5. Как связать фронт и бэк

Вот что нужно сделать после деплоя обоих частей:

### 1. В бэкенде (`.env` или переменные окружения на хостинге):

```env
CORS_ORIGIN=https://ваш-фронтенд-url.vercel.app
```

Это разрешает фронтенду делать запросы к бэкенду. Без этого браузер заблокирует запросы (CORS ошибка).

### 2. В фронтенде (`.env` или переменные окружения):

```env
VITE_API_URL=https://ваш-бэкенд-url.railway.app
VITE_WS_URL=https://ваш-бэкенд-url.railway.app
```

Это говорит фронтенду, куда отправлять API-запросы и WebSocket-соединения.

### 3. Перезапустите оба сервиса

После изменения переменных окружения нужно перезапустить:
- На Railway/Render — это происходит автоматически
- На Vercel — нужно переделать деплой (Redeploy)
- На Docker — `docker compose down && docker compose up -d`

### Схема связи:

```
Пользователь
    ↓
[Браузер] → http://charity-almau.vercel.app (фронтенд)
    ↓ API-запросы (axios)          ↓ WebSocket (socket.io)
[Бэкенд] → https://backend.railway.app:4000
    ↓
[PostgreSQL] → Supabase / Railway DB / Docker DB
```

---

## 6. Настройка Microsoft OAuth

Чтобы студенты входили через свой @almau.edu.kz аккаунт:

### Шаг 1: Зарегистрируйте приложение в Azure

1. Войдите в https://portal.azure.com с аккаунтом администратора AlmaU
2. Azure Active Directory → App registrations → New registration
3. Заполните:
   - Name: `Charity AlmaU`
   - Supported account types: **Single tenant** (только AlmaU)
   - Redirect URI: `https://ваш-бэкенд/api/auth/callback` (Web)
4. Нажмите Register

### Шаг 2: Получите ключи

В созданном приложении:
- **Application (client) ID** → это `MSAL_CLIENT_ID`
- **Directory (tenant) ID** → это `MSAL_TENANT_ID`
- Certificates & secrets → New client secret → скопируйте Value → это `MSAL_CLIENT_SECRET`

### Шаг 3: Обновите переменные окружения

**Бэкенд:**
```env
MSAL_CLIENT_ID=скопированный-client-id
MSAL_CLIENT_SECRET=скопированный-secret
MSAL_TENANT_ID=скопированный-tenant-id
MSAL_REDIRECT_URI=https://ваш-бэкенд/api/auth/callback
```

**Фронтенд:**
```env
VITE_MSAL_CLIENT_ID=тот-же-client-id
VITE_MSAL_AUTHORITY=https://login.microsoftonline.com/тот-же-tenant-id
VITE_MSAL_REDIRECT_URI=https://ваш-фронтенд/auth/callback
```

> Пока OAuth не настроен, используйте Dev Login (работает только в development).
> Для production отключите Dev Login или удалите этот эндпоинт.

---

## 7. Частые проблемы

### "ECONNREFUSED" при запуске бэкенда
PostgreSQL не запущен. Запустите:
```bash
# macOS
brew services start postgresql@16

# Linux
sudo systemctl start postgresql

# Windows — запустите PostgreSQL через Services (services.msc)
```

### "Database does not exist"
```bash
createdb charity_almau
# или через psql:
psql -U postgres -c "CREATE DATABASE charity_almau;"
```

### Фронтенд не может достучаться до бэкенда (CORS ошибка)
Проверьте `CORS_ORIGIN` в `.env` бэкенда — он должен совпадать с URL фронтенда. Без `https://`, без `/` в конце:
```
# Правильно:
CORS_ORIGIN=http://localhost:3000

# Неправильно:
CORS_ORIGIN=http://localhost:3000/
```

### "Prisma migrate" падает
```bash
# Сбросьте и пересоздайте БД:
dropdb charity_almau
createdb charity_almau
npx prisma migrate dev
npm run db:seed
```

### Фото не отображаются
Убедитесь что папка `uploads/` существует в корне бэкенда:
```bash
mkdir -p uploads
```

### WebSocket не работает (чаты)
- Проверьте что `VITE_WS_URL` указывает на бэкенд
- Для production с HTTPS нужен `wss://` протокол — Railway и Render поддерживают его автоматически

### Порт занят
```bash
# Найти процесс на порту 4000:
lsof -i :4000
# Убить:
kill -9 <PID>
```

---

## Полезные команды

```bash
# Бэкенд
npm run dev          # Запуск в dev-режиме
npm run build        # Сборка для production
npm start            # Запуск собранного проекта
npm run db:migrate   # Применить миграции
npm run db:seed      # Заполнить тестовыми данными
npm run db:studio    # Открыть визуальный редактор БД (Prisma Studio)

# Фронтенд
npm run dev          # Запуск в dev-режиме
npm run build        # Сборка для production
npm run preview      # Предпросмотр собранного проекта
```

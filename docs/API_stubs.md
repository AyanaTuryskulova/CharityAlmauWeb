# API Stubs — CharityAlmau Web

## Чат (chat/)
| Endpoint | Method | Описание |
|-----------|---------|----------|
| `/chat/` | GET | Страница списка чатов пользователя |
| `/chat/<chat_id>/` | GET | Открыть конкретный чат |
| `/chat/send/` | POST | Отправить сообщение |
| `/chat/messages/<chat_id>/` | GET | Получить сообщения конкретного чата |

## Аренда (rentals/)
| Endpoint | Method | Описание |
|-----------|---------|----------|
| `/rentals/` | GET | Список всех аренд пользователя |
| `/rentals/<id>/` | GET | Детали аренды |
| `/rentals/create/` | POST | Создать новую аренду |
| `/rentals/update/<id>/` | PATCH | Обновить статус аренды |

## Профиль арендатора (tenant_profile/)
| Endpoint | Method | Описание |
|-----------|---------|----------|
| `/profile/` | GET | Просмотр профиля |
| `/profile/update/` | POST | Редактировать профиль |

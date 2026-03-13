"""
Уведомления для действий с объявлениями (Забрать / Обменяться / Арендовать).
Отправляет push-уведомление в браузер + email (если настроен SMTP).
"""
import json
from django.conf import settings
from django.core.mail import send_mail


ACTION_LABELS = {
    'take':     {'ru': 'хочет забрать',     'url_suffix': 'take'},
    'exchange': {'ru': 'хочет обменяться',  'url_suffix': 'exchange'},
    'rent':     {'ru': 'хочет арендовать',  'url_suffix': 'rent'},
}


def notify_trade_request(product, requester, action: str) -> None:
    """
    Уведомляет автора объявления о новой заявке.
    product  — объект Product
    requester — User, кто нажал кнопку
    action  — 'take' | 'exchange' | 'rent'
    """
    owner = product.user
    label = ACTION_LABELS.get(action, {}).get('ru', 'откликнулся на')

    title = f'Новая заявка на «{product.title}»'
    body  = f'{requester.username} {label} ваш товар «{product.title}»'
    url   = f'/requests/'

    # 1. Push-уведомление (работает без паролей)
    _send_push(owner, title, body, url)

    # 2. Email (работает если EMAIL_HOST_PASSWORD настроен в .env)
    _send_email(owner, title, body, url, requester, product, label)


def _send_push(user, title, body, url):
    try:
        from core.apps.chat.email_utils import send_push_notification
        send_push_notification(user=user, title=title, body=body, url=url)
    except Exception:
        pass


def _send_email(owner, subject, push_body, url, requester, product, label):
    if not owner.email:
        return
    try:
        full_body = (
            f'Привет, {owner.first_name or owner.username}!\n\n'
            f'Пользователь {requester.username} {label} ваш товар «{product.title}».\n\n'
            f'Перейдите в раздел «Заявки», чтобы ответить:\n'
            f'https://charity.almau.edu.kz/requests/\n\n'
            f'— Команда Charity AlmaU'
        )
        send_mail(
            subject=subject,
            message=full_body,
            from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', None),
            recipient_list=[owner.email],
            fail_silently=True,
        )
    except Exception:
        pass

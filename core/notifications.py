"""
Уведомления для действий с объявлениями (Забрать / Обменяться / Арендовать).
Отправляет push-уведомление в браузер (VAPID).
"""

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
    url   = '/requests/'

    _send_push(owner, title, body, url)


def _send_push(user, title, body, url):
    try:
        from .email_utils import send_push_notification
        send_push_notification(user=user, title=title, body=body, url=url)
    except Exception:
        pass

"""
Браузерные push-уведомления через VAPID (без паролей и внешних сервисов).
"""
import json
from django.conf import settings


def send_push_notification(user, title: str, body: str, url: str = '/chat/') -> None:
    """Отправляет push-уведомление всем активным подпискам пользователя."""
    from .models import PushSubscription
    try:
        from pywebpush import webpush, WebPushException
    except ImportError:
        return

    subscriptions = PushSubscription.objects.filter(user=user)
    dead = []

    for sub in subscriptions:
        try:
            webpush(
                subscription_info={
                    'endpoint': sub.endpoint,
                    'keys': {'p256dh': sub.p256dh, 'auth': sub.auth},
                },
                data=json.dumps({'title': title, 'body': body, 'url': url}),
                vapid_private_key=settings.VAPID_PRIVATE_KEY,
                vapid_claims={'sub': f'mailto:{settings.VAPID_ADMIN_EMAIL}'},
            )
        except WebPushException as e:
            if e.response and e.response.status_code in (404, 410):
                dead.append(sub.id)
        except Exception:
            pass

    if dead:
        PushSubscription.objects.filter(id__in=dead).delete()


def notify_new_message(chat, sender, text: str) -> None:
    """Уведомляет получателя о новом сообщении через push."""
    recipient = chat.participants.exclude(id=sender.id).first()
    if not recipient:
        return

    product = getattr(chat, 'product', None)
    product_title = product.title if product else '—'

    send_push_notification(
        user=recipient,
        title=f'Новое сообщение от {sender.username}',
        body=f'По объявлению «{product_title}»: {text[:80]}',
        url='/chat/',
    )

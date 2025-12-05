"""
ASGI config for CharityAlmaWeb project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/asgi/
"""

import os

from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
import core.apps.chat.routing as chat_routing

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'CharityAlmaWeb.settings')

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AuthMiddlewareStack(URLRouter(chat_routing.websocket_urlpatterns)),
})

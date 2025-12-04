from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
import core.apps.chat.routing as chat_routing

application = ProtocolTypeRouter({
    "websocket": AuthMiddlewareStack(URLRouter(chat_routing.websocket_urlpatterns)),
})

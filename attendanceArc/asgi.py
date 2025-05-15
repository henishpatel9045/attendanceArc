import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
import core.routing

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'attendanceArc.settings')

application = ProtocolTypeRouter({
    # HTTP→Django views
    "http": get_asgi_application(),
    # WebSocket→your core.routing websocket_urlpatterns
    "websocket": URLRouter(
        core.routing.websocket_urlpatterns
    ),
})

from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    # e.g. ws://<host>/ws/events/<event_id>/
    re_path(r'ws/events/(?P<event_id>\d+)/$', consumers.AttendanceConsumer.as_asgi()),
]

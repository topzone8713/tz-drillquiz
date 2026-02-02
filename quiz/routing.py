"""
WebSocket URL 라우팅 설정
"""
from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'^ws/realtime/(?P<session_id>[^/]+)/$', consumers.RealtimeProxyConsumer.as_asgi()),
]


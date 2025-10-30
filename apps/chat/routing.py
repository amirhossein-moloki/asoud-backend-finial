"""
WebSocket Routing for Chat and Support System
"""

from django.urls import path
from apps.chat.consumers import ChatConsumer, SupportConsumer

websocket_urlpatterns = [
    path('ws/chat/<str:room_name>/', ChatConsumer.as_asgi()),
    path('ws/support/<str:ticket_id>/', SupportConsumer.as_asgi()),
]
"""
Analytics WebSocket Routing
"""

from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/analytics/$', consumers.AnalyticsConsumer.as_asgi()),
    re_path(r'ws/analytics/dashboard/$', consumers.RealTimeDashboardConsumer.as_asgi()),
    re_path(r'ws/analytics/tracking/$', consumers.EventTrackingConsumer.as_asgi()),
]


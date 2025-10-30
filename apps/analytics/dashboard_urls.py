"""
Dashboard URL patterns for Analytics
"""

from django.urls import path
from . import dashboard_views

urlpatterns = [
    path('', dashboard_views.analytics_dashboard, name='analytics_dashboard'),
    path('dashboard/', dashboard_views.analytics_dashboard, name='analytics_dashboard'),
    path('real-time/', dashboard_views.real_time_dashboard, name='real_time_dashboard'),
    path('user/', dashboard_views.user_analytics, name='user_analytics'),
    path('product/', dashboard_views.product_analytics, name='product_analytics'),
    path('market/', dashboard_views.market_analytics, name='market_analytics'),
    path('ml/', dashboard_views.ml_recommendations, name='ml_recommendations'),
]


from django.urls import path

from apps.market.views.user_views import (
    MarketListAPIView,
    PublicMarketListAPIView,
    MarketReportAPIView,
    MarketBookmarkAPIView,
)
from apps.market.views.market_schedule import MarketScheduleUserListView

app_name = 'market_user'

urlpatterns = [
    path(
        'list/',
        MarketListAPIView.as_view(),
        name='list',
    ),
    path(
        'public/list/',
        PublicMarketListAPIView.as_view(),
        name='public-list',
    ),
    path(
        'report/<str:pk>/',
        MarketReportAPIView.as_view(),
        name='report',
    ),
    path(
        'bookmark/',
        MarketBookmarkAPIView.as_view(),
        name='bookmark',
    ),
    path(
        'bookmark/<str:pk>/',
        MarketBookmarkAPIView.as_view(),
        name='bookmark',
    ),

    path(
        'schedule/<str:pk>/',
        MarketScheduleUserListView.as_view(),
        name='schedule-list',
    ),
]

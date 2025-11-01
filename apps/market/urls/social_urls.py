from django.urls import path
from apps.market.views.social_views import (
    MarketLikeAPIView,
    MarketBookmarkToggleAPIView,
    MarketViewTrackAPIView,
    MarketShareTrackAPIView,
    MarketReportCreateAPIView,
    MarketSocialStatsAPIView,
    NotificationIconsAPIView,
    HelpRequestAPIView,
    mark_notifications_read
)

app_name = 'market_social'

urlpatterns = [
    # Like functionality
    path('markets/<int:market_id>/like/', MarketLikeAPIView.as_view(), name='market_like'),
    
    # Bookmark functionality
    path('markets/<int:market_id>/bookmark/', MarketBookmarkToggleAPIView.as_view(), name='market_bookmark'),
    
    # View tracking
    path('markets/<int:market_id>/view/', MarketViewTrackAPIView.as_view(), name='market_view'),
    
    # Share tracking
    path('markets/<int:market_id>/share/', MarketShareTrackAPIView.as_view(), name='market_share'),
    
    # Report functionality
    path('markets/<int:market_id>/report/', MarketReportCreateAPIView.as_view(), name='market_report'),
    
    # Social statistics
    path('markets/<int:market_id>/stats/', MarketSocialStatsAPIView.as_view(), name='market_social_stats'),
    
    # Notification icons
    path('notifications/icons/', NotificationIconsAPIView.as_view(), name='notification_icons'),
    path('notifications/mark-read/', mark_notifications_read, name='mark_notifications_read'),
    
    # Help requests
    path('help/request/', HelpRequestAPIView.as_view(), name='help_request'),
]
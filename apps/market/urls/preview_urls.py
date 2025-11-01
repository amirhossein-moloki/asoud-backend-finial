from django.urls import path
from apps.market.views.preview_views import (
    MarketPreviewView,
    MarketPreviewSettingsAPIView,
    MarketPreviewModeToggleView,
    MarketLivePreviewAPIView,
    market_preview_iframe
)

app_name = 'market_preview'

urlpatterns = [
    # Store Preview URLs
    path('preview/<int:market_id>/', MarketPreviewView.as_view(), name='market_preview'),
    path('preview/<int:market_id>/iframe/', market_preview_iframe, name='market_preview_iframe'),
    
    # Preview Settings API
    path('api/preview/<int:market_id>/settings/', MarketPreviewSettingsAPIView.as_view(), name='preview_settings'),
    path('api/preview/<int:market_id>/toggle-mode/', MarketPreviewModeToggleView.as_view(), name='preview_toggle_mode'),
    path('api/preview/<int:market_id>/live/', MarketLivePreviewAPIView.as_view(), name='live_preview'),
]
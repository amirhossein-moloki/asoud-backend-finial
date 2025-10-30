"""
Analytics URLs for ASOUD Platform
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    UserBehaviorEventViewSet, UserSessionViewSet, ProductAnalyticsViewSet,
    MarketAnalyticsViewSet, UserAnalyticsViewSet, AnalyticsDashboardViewSet,
    MLRecommendationsViewSet
)
from .advanced_views import (
    SalesAnalyticsViewSet, BusinessIntelligenceViewSet, AdvancedAnalyticsViewSet
)
from .optimization_views import (
    PriceOptimizationViewSet, DemandForecastingViewSet, MLOptimizationViewSet
)
from .fraud_views import (
    FraudDetectionViewSet, CustomerSegmentationViewSet, SecurityAnalyticsViewSet
)
from .dashboard_views import (
    AnalyticsAPIView, RealTimeAnalyticsAPIView, MLRecommendationsAPIView, EventTrackingAPIView
)

router = DefaultRouter()
# Basic Analytics
router.register(r'events', UserBehaviorEventViewSet, basename='user-behavior-events')
router.register(r'sessions', UserSessionViewSet, basename='user-sessions')
router.register(r'products', ProductAnalyticsViewSet, basename='product-analytics')
router.register(r'markets', MarketAnalyticsViewSet, basename='market-analytics')
router.register(r'users', UserAnalyticsViewSet, basename='user-analytics')
router.register(r'dashboard', AnalyticsDashboardViewSet, basename='analytics-dashboard')
router.register(r'recommendations', MLRecommendationsViewSet, basename='ml-recommendations')

# Advanced Analytics
router.register(r'sales', SalesAnalyticsViewSet, basename='sales-analytics')
router.register(r'business-intelligence', BusinessIntelligenceViewSet, basename='business-intelligence')
router.register(r'advanced', AdvancedAnalyticsViewSet, basename='advanced-analytics')

# ML Optimization
router.register(r'price-optimization', PriceOptimizationViewSet, basename='price-optimization')
router.register(r'demand-forecasting', DemandForecastingViewSet, basename='demand-forecasting')
router.register(r'ml-optimization', MLOptimizationViewSet, basename='ml-optimization')

# Fraud Detection & Security
router.register(r'fraud-detection', FraudDetectionViewSet, basename='fraud-detection')
router.register(r'customer-segmentation', CustomerSegmentationViewSet, basename='customer-segmentation')
router.register(r'security', SecurityAnalyticsViewSet, basename='security-analytics')

urlpatterns = [
    path('', include(router.urls)),
    
    # Additional API endpoints
    path('api/analytics/', AnalyticsAPIView.as_view(), name='analytics-api'),
    path('api/real-time/', RealTimeAnalyticsAPIView.as_view(), name='real-time-api'),
    path('api/ml-recommendations/', MLRecommendationsAPIView.as_view(), name='ml-recommendations-api'),
    path('api/event-tracking/', EventTrackingAPIView.as_view(), name='event-tracking-api'),
]

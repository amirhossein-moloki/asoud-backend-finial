from django.urls import path
from ..views.subscription_views import (
    SubscriptionPlansAPIView,
    MarketSubscriptionCreateAPIView,
    MarketSubscriptionListAPIView,
    MarketSubscriptionDetailAPIView,
    SubscriptionPaymentVerifyAPIView,
    SubscriptionRenewAPIView,
    SubscriptionCancelAPIView,
    AdminSubscriptionListAPIView,
    AdminSubscriptionStatsAPIView,
)

app_name = 'subscription'

urlpatterns = [
    # Public subscription plans
    path('plans/', SubscriptionPlansAPIView.as_view(), name='plans'),
    
    # User subscription management
    path('', MarketSubscriptionListAPIView.as_view(), name='list'),
    path('<uuid:pk>/', MarketSubscriptionDetailAPIView.as_view(), name='detail'),
    path('market/<uuid:market_id>/create/', MarketSubscriptionCreateAPIView.as_view(), name='create'),
    path('payment/verify/', SubscriptionPaymentVerifyAPIView.as_view(), name='payment_verify'),
    path('<uuid:subscription_id>/renew/', SubscriptionRenewAPIView.as_view(), name='renew'),
    path('<uuid:subscription_id>/cancel/', SubscriptionCancelAPIView.as_view(), name='cancel'),
    
    # Admin subscription management
    path('admin/list/', AdminSubscriptionListAPIView.as_view(), name='admin_list'),
    path('admin/stats/', AdminSubscriptionStatsAPIView.as_view(), name='admin_stats'),
]
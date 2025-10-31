from django.urls import path

# Import views with correct paths
try:
    from ..views.office_registration_views import (
        MarketCreateAPIView, MarketLocationCreateAPIView, MarketContactCreateAPIView,
        PaymentGatewayAPIView, SubscriptionFeeCalculatorAPIView, SubscriptionPaymentAPIView,
        IntegratedMarketCreateAPIView
    )
except ImportError:
    try:
        from .views import (
            MarketCreateAPIView, MarketLocationCreateAPIView, MarketContactCreateAPIView,
            PaymentGatewayAPIView, SubscriptionFeeCalculatorAPIView, SubscriptionPaymentAPIView,
            IntegratedMarketCreateAPIView
        )
    except ImportError:
        # Fallback empty views if not available
        from django.http import JsonResponse
        from django.views import View
        
        class MarketCreateAPIView(View):
            def get(self, request):
                return JsonResponse({'error': 'View not implemented'})
        
        MarketLocationCreateAPIView = MarketContactCreateAPIView = MarketCreateAPIView
        PaymentGatewayAPIView = SubscriptionFeeCalculatorAPIView = MarketCreateAPIView
        SubscriptionPaymentAPIView = IntegratedMarketCreateAPIView = MarketCreateAPIView

urlpatterns = [
    # موجود: Market creation endpoints
    path('create/', MarketCreateAPIView.as_view(), name='create'),
    path('location/create/', MarketLocationCreateAPIView.as_view(), name='location-create'),
    path('contact/create/', MarketContactCreateAPIView.as_view(), name='contact-create'),
    
    # اضافه شده: Integrated market creation
    path('integrated/create/', IntegratedMarketCreateAPIView.as_view(), name='integrated-create'),
    
    # اضافه شده: Payment gateway selection
    path('payment/gateway/<str:market_id>/', PaymentGatewayAPIView.as_view(), name='payment-gateway'),
    
    # اضافه شده: Subscription payment endpoints
    path('subscription/fee/calculate/', SubscriptionFeeCalculatorAPIView.as_view(), name='subscription-fee-calculate'),
    path('subscription/payment/<str:market_id>/', SubscriptionPaymentAPIView.as_view(), name='subscription-payment'),
]
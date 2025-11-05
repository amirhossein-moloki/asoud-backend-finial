from django.urls import path
from .views import (
    PaymentGatewayAPIView, SubscriptionFeeCalculatorAPIView, SubscriptionPaymentAPIView
)

urlpatterns = [
    # اضافه شده: Payment and subscription endpoints
    path('payment/gateway/<str:market_id>/', PaymentGatewayAPIView.as_view(), name='payment-gateway'),
    path('subscription/fee/calculate/', SubscriptionFeeCalculatorAPIView.as_view(), name='subscription-fee-calculate'),
    path('subscription/payment/<str:market_id>/', SubscriptionPaymentAPIView.as_view(), name='subscription-payment'),
]
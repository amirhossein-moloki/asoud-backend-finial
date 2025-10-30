from django.urls import path
from apps.flutter.views import (
    MarketDetailView,
    ProductDetailView,
    AdvertizeDetailView,
    VisitCardView,
)
app_name = 'flutter_urls'

urlpatterns = [
    path('markets', MarketDetailView.as_view(), name='market-detail'),
    path('products', ProductDetailView.as_view(), name='product-detail'),
    path('advertisements', AdvertizeDetailView.as_view(), name='advertise-detail'),
    path('visit/<str:business_id>', VisitCardView.as_view(), name='visit-card'),
]
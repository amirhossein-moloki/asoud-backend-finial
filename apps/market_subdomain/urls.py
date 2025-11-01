from django.urls import path
from . import views

app_name = 'market_subdomain'

urlpatterns = [
    path('', views.MarketStoreView.as_view(), name='store_home'),
    path('api/', views.MarketDetailView.as_view(), name='api_detail'),
    path('products/', views.ProductListView.as_view(), name='products'),
    path('products/<uuid:pk>/', views.ProductDetailView.as_view(), name='product_detail'),
]
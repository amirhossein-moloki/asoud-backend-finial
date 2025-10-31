from django.urls import path

# Import views with correct paths
try:
    from ..views.category_views import MarketFeeUpdateAPIView, MarketFeeListAPIView
except ImportError:
    try:
        from .views import MarketFeeUpdateAPIView, MarketFeeListAPIView
    except ImportError:
        # Fallback empty views if not available
        from django.http import JsonResponse
        from django.views import View
        
        class MarketFeeUpdateAPIView(View):
            def get(self, request, *args, **kwargs):
                return JsonResponse({'error': 'View not implemented'})
        
        class MarketFeeListAPIView(View):
            def get(self, request, *args, **kwargs):
                return JsonResponse({'error': 'View not implemented'})

urlpatterns = [
    # اضافه شده: URLs برای مدیریت حق اشتراک
    path('market-fee/<str:model_type>/<str:pk>/', MarketFeeUpdateAPIView.as_view(), name='market-fee-update'),
    path('market-fee/<str:model_type>/', MarketFeeListAPIView.as_view(), name='market-fee-list'),
]

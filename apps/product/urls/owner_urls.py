from django.urls import path

from apps.product.views.owner_views import (
    ProductCreateAPIView,
    ProductDiscountCreateAPIView,
    ProductListAPIView,
    ProductDetailAPIView,
    ProductThemeCreateAPIView,
    ProductThemeListAPIView,
    ProductThemeUpdateAPIView,
    ProductThemeDeleteAPIView,
    ProductShippingCreateAPIView,
    ProductShippingListAPIView
)

app_name = 'product_owner'

urlpatterns = [
    path(
        'create/',
        ProductCreateAPIView.as_view(),
        name='create',
    ),
    path(
        'discount/create/<str:pk>/',
        ProductDiscountCreateAPIView.as_view(),
        name='discount-create'
    ),
    path(
        'ship/create/<str:pk>/',
        ProductShippingCreateAPIView.as_view(),
        name='ship-create'
    ),
    path(
        'ship/list/<str:pk>/',
        ProductShippingListAPIView.as_view(),
        name='ship-list'
    ),
    path(
        'list/<str:pk>/',
        ProductListAPIView.as_view(),
        name='list',
    ),
    path(
        'detail/<str:pk>/',
        ProductDetailAPIView.as_view(),
        name='detail',
    ),
    path(
        'theme/create/<str:pk>/',
        ProductThemeCreateAPIView.as_view(),
        name='theme-create',
    ),
    path(
        'theme/list/<str:pk>/',
        ProductThemeListAPIView.as_view(),
        name='theme-list',
    ),
    path(
        'theme/update/<str:pk>/',
        ProductThemeUpdateAPIView.as_view(),
        name='theme-update',
    ),
    path(
        'theme/delete/<str:pk>/',
        ProductThemeDeleteAPIView.as_view(),
        name='theme-delete',
    ),
]

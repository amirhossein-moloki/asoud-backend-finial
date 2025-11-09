from django.urls import path

from apps.item.views.owner_views import (
    ItemCreateAPIView,
    ItemDiscountCreateAPIView,
    ItemListAPIView,
    ItemDetailAPIView,
    MarketThemeCreateAPIView,
    MarketThemeListAPIView,
    ItemThemeUpdateAPIView,
    ItemThemeDeleteAPIView,
    ItemShippingCreateAPIView,
    ItemShippingListAPIView
)

app_name = 'item_owner'

urlpatterns = [
    path(
        'create/',
        ItemCreateAPIView.as_view(),
        name='create',
    ),
    path(
        'discount/create/<str:pk>/',
        ItemDiscountCreateAPIView.as_view(),
        name='discount-create'
    ),
    path(
        'ship/create/<str:pk>/',
        ItemShippingCreateAPIView.as_view(),
        name='ship-create'
    ),
    path(
        'ship/list/<str:pk>/',
        ItemShippingListAPIView.as_view(),
        name='ship-list'
    ),
    path(
        'list/<str:pk>/',
        ItemListAPIView.as_view(),
        name='list',
    ),
    path(
        'detail/<str:pk>/',
        ItemDetailAPIView.as_view(),
        name='detail',
    ),
    path(
        'theme/create/<str:pk>/',
        MarketThemeCreateAPIView.as_view(),
        name='theme-create',
    ),
    path(
        'theme/list/<str:pk>/',
        MarketThemeListAPIView.as_view(),
        name='theme-list',
    ),
    path(
        'theme/update/<str:pk>/',
        ItemThemeUpdateAPIView.as_view(),
        name='theme-update',
    ),
    path(
        'theme/delete/<str:pk>/',
        ItemThemeDeleteAPIView.as_view(),
        name='theme-delete',
    ),
]

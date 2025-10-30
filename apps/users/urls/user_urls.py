from django.urls import path

from apps.users.views.user_views import (
    PinCreateAPIView, PinVerifyAPIView,
    BankInfoCreateView, BankInfoUpdateView,
    BankInfoListView, BankInfoDeleteView,
    BankInfoDetailView, BanksListView)


app_name = 'users_user'

urlpatterns = [
    path('pin/create/', PinCreateAPIView.as_view(), name='pin-create'),
    path('pin/verify/', PinVerifyAPIView.as_view(), name='pin-verify'),
    path('bank-info/list/', BanksListView.as_view(), name='banks-list'),
    path('bank/info/create/', BankInfoCreateView.as_view(), name= 'bank-create'),
    path('bank/info/list/', BankInfoListView.as_view(), name= 'bank-list'),
    path('bank/info/detail/<str:pk>/', BankInfoDetailView.as_view(), name= 'bank-detail'),
    path('bank/info/update/<str:pk>/', BankInfoUpdateView.as_view(), name= 'bank-update'),
    path('bank/info/delete/<str:pk>/', BankInfoDeleteView.as_view(), name= 'bank-delete')
]

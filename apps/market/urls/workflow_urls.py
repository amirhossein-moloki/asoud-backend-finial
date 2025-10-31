from django.urls import path

from apps.market.views.workflow_views import (
    MarketStatusTransitionAPIView,
    MarketActionsAPIView,
    MarketWorkflowHistoryAPIView,
    MarketApprovalRequestCreateAPIView,
    MarketApprovalRequestListAPIView,
    MarketShareAPIView,
    MarketShareAnalyticsAPIView,
    MarketSubscriptionCreateAPIView,
    MarketSubscriptionListAPIView,
    AdminMarketApprovalListAPIView,
    AdminMarketApprovalActionAPIView,
)

app_name = 'market_workflow'

urlpatterns = [
    # Market Status Workflow
    path(
        '<str:market_id>/transition/',
        MarketStatusTransitionAPIView.as_view(),
        name='status_transition',
    ),
    path(
        '<str:market_id>/actions/',
        MarketActionsAPIView.as_view(),
        name='available_actions',
    ),
    path(
        '<str:market_id>/history/',
        MarketWorkflowHistoryAPIView.as_view(),
        name='workflow_history',
    ),
    
    # Approval Requests
    path(
        '<str:market_id>/approval-request/',
        MarketApprovalRequestCreateAPIView.as_view(),
        name='create_approval_request',
    ),
    path(
        'approval-requests/',
        MarketApprovalRequestListAPIView.as_view(),
        name='list_approval_requests',
    ),
    
    # Market Sharing
    path(
        '<str:market_id>/share/',
        MarketShareAPIView.as_view(),
        name='market_share',
    ),
    path(
        '<str:market_id>/share/analytics/',
        MarketShareAnalyticsAPIView.as_view(),
        name='market_share_analytics',
    ),
    
    # Subscriptions
    path(
        '<str:market_id>/subscription/',
        MarketSubscriptionCreateAPIView.as_view(),
        name='create_subscription',
    ),
    path(
        'subscriptions/',
        MarketSubscriptionListAPIView.as_view(),
        name='list_subscriptions',
    ),
    
    # Admin Approval Management
    path(
        'admin/approvals/',
        AdminMarketApprovalListAPIView.as_view(),
        name='admin_approval_list',
    ),
    path(
        'admin/approvals/<str:approval_id>/action/',
        AdminMarketApprovalActionAPIView.as_view(),
        name='admin_approval_action',
    ),
]
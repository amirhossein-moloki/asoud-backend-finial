from rest_framework import views, status, permissions, generics
from rest_framework.response import Response
from django.utils.translation import gettext_lazy as _
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db import models

from utils.response import ApiResponse
from apps.users.authentication import IsOwnerOrReadOnly

from apps.market.models import (
    Market,
    MarketWorkflowHistory,
    MarketApprovalRequest,
    MarketSubscription,
)

from apps.market.serializers.workflow_serializers import (
    MarketStatusTransitionSerializer,
    MarketWorkflowHistorySerializer,
    MarketApprovalRequestSerializer,
    MarketSubscriptionSerializer,
    MarketActionsSerializer,
)


class MarketStatusTransitionAPIView(views.APIView):
    """
    API view for transitioning market status in the 8-state workflow.
    
    Handles status transitions with proper validation and history tracking.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, market_id):
        market = get_object_or_404(Market, id=market_id, user=request.user)
        
        serializer = MarketStatusTransitionSerializer(
            data=request.data,
            context={'market': market, 'user': request.user}
        )
        
        if serializer.is_valid():
            try:
                new_status = serializer.validated_data['new_status']
                reason = serializer.validated_data.get('reason', '')
                
                result = market.transition_status(
                    new_status=new_status,
                    user=request.user,
                    reason=reason
                )
                
                return Response(
                    ApiResponse(
                        success=True,
                        code=200,
                        message=result,
                        data={
                            'market_id': market.id,
                            'old_status': serializer.validated_data.get('old_status'),
                            'new_status': new_status,
                            'available_actions': market.get_available_actions()
                        }
                    ),
                    status=status.HTTP_200_OK
                )
                
            except ValueError as e:
                return Response(
                    ApiResponse(
                        success=False,
                        code=400,
                        message=str(e)
                    ),
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        return Response(
            ApiResponse(
                success=False,
                code=400,
                message=_("Invalid data provided"),
                error=serializer.errors
            ),
            status=status.HTTP_400_BAD_REQUEST
        )


class MarketActionsAPIView(views.APIView):
    """
    API view to get available actions for a market based on its current status.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, market_id):
        market = get_object_or_404(Market, id=market_id, user=request.user)
        
        serializer = MarketActionsSerializer(market)
        
        return Response(
            ApiResponse(
                success=True,
                code=200,
                data=serializer.data
            ),
            status=status.HTTP_200_OK
        )


class MarketWorkflowHistoryAPIView(generics.ListAPIView):
    """
    API view to list workflow history for a specific market.
    """
    serializer_class = MarketWorkflowHistorySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        market_id = self.kwargs['market_id']
        market = get_object_or_404(Market, id=market_id, user=self.request.user)
        return MarketWorkflowHistory.objects.filter(market=market)


class MarketApprovalRequestCreateAPIView(views.APIView):
    """
    API view for creating approval requests (publication, editing, etc.).
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, market_id):
        market = get_object_or_404(Market, id=market_id, user=request.user)
        
        serializer = MarketApprovalRequestSerializer(
            data=request.data,
            context={'market': market, 'user': request.user}
        )
        
        if serializer.is_valid():
            approval_request = serializer.save(
                market=market,
                requested_by=request.user
            )
            
            return Response(
                ApiResponse(
                    success=True,
                    code=201,
                    message=_("Approval request submitted successfully"),
                    data=MarketApprovalRequestSerializer(approval_request).data
                ),
                status=status.HTTP_201_CREATED
            )
        
        return Response(
            ApiResponse(
                success=False,
                code=400,
                message=_("Invalid data provided"),
                error=serializer.errors
            ),
            status=status.HTTP_400_BAD_REQUEST
        )


class MarketApprovalRequestListAPIView(generics.ListAPIView):
    """
    API view to list approval requests for user's markets.
    """
    serializer_class = MarketApprovalRequestSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return MarketApprovalRequest.objects.filter(
            market__user=self.request.user
        )


class MarketShareAPIView(views.APIView):
    """
    Enhanced API view for comprehensive market sharing functionality.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, market_id):
        """Get comprehensive share data for a published market"""
        market = get_object_or_404(Market, id=market_id, user=request.user)
        
        if market.status != Market.PUBLISHED:
            return Response(
                ApiResponse(
                    success=False,
                    code=400,
                    message=_("Market must be published to generate share data")
                ),
                status=status.HTTP_400_BAD_REQUEST
            )
        
        share_data = market.get_share_data(request)
        
        # Get share analytics
        from apps.market.models import MarketShare
        share_stats = {
            'total_shares': market.shares.count(),
            'platform_breakdown': {},
            'recent_shares': market.shares.select_related('shared_by')[:5]
        }
        
        # Calculate platform breakdown
        platform_counts = market.shares.values('platform').annotate(
            count=models.Count('platform')
        ).order_by('-count')
        
        for item in platform_counts:
            platform_display = dict(MarketShare.SHARE_PLATFORMS).get(item['platform'], item['platform'])
            share_stats['platform_breakdown'][platform_display] = item['count']
        
        return Response(
            ApiResponse(
                success=True,
                code=200,
                data={
                    'share_data': share_data,
                    'analytics': share_stats,
                    'qr_code_url': f"{share_data['url']}?qr=1" if share_data else None,
                },
                message=_("Share data retrieved successfully")
            ),
            status=status.HTTP_200_OK
        )
    
    def post(self, request, market_id):
        """Track a share action"""
        market = get_object_or_404(Market, id=market_id, user=request.user)
        
        if market.status != Market.PUBLISHED:
            return Response(
                ApiResponse(
                    success=False,
                    code=400,
                    message=_("Market must be published to share")
                ),
                status=status.HTTP_400_BAD_REQUEST
            )
        
        platform = request.data.get('platform', 'direct')
        
        # Validate platform
        from apps.market.models import MarketShare
        valid_platforms = [choice[0] for choice in MarketShare.SHARE_PLATFORMS]
        if platform not in valid_platforms:
            return Response(
                ApiResponse(
                    success=False,
                    code=400,
                    message=_("Invalid share platform")
                ),
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create share record
        share_record = MarketShare.objects.create(
            market=market,
            shared_by=request.user,
            platform=platform,
            ip_address=self.get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            referrer=request.META.get('HTTP_REFERER', ''),
        )
        
        # Increment market view count for sharing
        market.view_count = models.F('view_count') + 1
        market.save(update_fields=['view_count'])
        
        return Response(
            ApiResponse(
                success=True,
                code=200,
                data={
                    'share_id': share_record.id,
                    'platform': share_record.get_platform_display(),
                    'share_url': market.get_share_url(request),
                    'message': _("Share tracked successfully")
                }
            ),
            status=status.HTTP_200_OK
        )
    
    def get_client_ip(self, request):
        """Get client IP address from request"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class MarketSubscriptionCreateAPIView(views.APIView):
    """
    API view for creating market subscriptions.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, market_id):
        market = get_object_or_404(Market, id=market_id, user=request.user)
        
        serializer = MarketSubscriptionSerializer(
            data=request.data,
            context={'market': market, 'user': request.user}
        )
        
        if serializer.is_valid():
            subscription = serializer.save(market=market)
            
            # Update market payment status
            market.is_paid = True
            market.subscription_start_date = subscription.start_date
            market.subscription_end_date = subscription.end_date
            
            # Transition to paid status if currently unpaid
            if market.status == Market.UNPAID_UNDER_CREATION:
                market.transition_status(
                    Market.PAID_UNDER_CREATION,
                    user=request.user,
                    reason="Subscription payment completed"
                )
            
            market.save()
            
            return Response(
                ApiResponse(
                    success=True,
                    code=201,
                    message=_("Subscription created successfully"),
                    data=MarketSubscriptionSerializer(subscription).data
                ),
                status=status.HTTP_201_CREATED
            )
        
        return Response(
            ApiResponse(
                success=False,
                code=400,
                message=_("Invalid data provided"),
                error=serializer.errors
            ),
            status=status.HTTP_400_BAD_REQUEST
        )


class MarketSubscriptionListAPIView(generics.ListAPIView):
    """
    API view to list subscriptions for user's markets.
    """
    serializer_class = MarketSubscriptionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return MarketSubscription.objects.filter(
            market__user=self.request.user
        )


# Admin Views for Approval Management
class AdminMarketApprovalListAPIView(generics.ListAPIView):
    """
    Admin API view to list pending approval requests.
    """
    serializer_class = MarketApprovalRequestSerializer
    permission_classes = [permissions.IsAuthenticated, permissions.IsAdminUser]

    def get_queryset(self):
        return MarketApprovalRequest.objects.filter(
            status=MarketApprovalRequest.PENDING
        )


class AdminMarketApprovalActionAPIView(views.APIView):
    """
    Admin API view to approve or reject market approval requests.
    """
    permission_classes = [permissions.IsAuthenticated, permissions.IsAdminUser]

    def post(self, request, approval_id):
        approval_request = get_object_or_404(
            MarketApprovalRequest, 
            id=approval_id
        )
        
        action = request.data.get('action')  # 'approve' or 'reject'
        admin_response = request.data.get('admin_response', '')
        
        if action not in ['approve', 'reject']:
            return Response(
                ApiResponse(
                    success=False,
                    code=400,
                    message=_("Invalid action. Use 'approve' or 'reject'")
                ),
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Update approval request
        approval_request.status = (
            MarketApprovalRequest.APPROVED if action == 'approve' 
            else MarketApprovalRequest.REJECTED
        )
        approval_request.reviewed_by = request.user
        approval_request.admin_response = admin_response
        approval_request.reviewed_at = timezone.now()
        approval_request.save()
        
        # Update market status based on approval
        market = approval_request.market
        
        if action == 'approve':
            if approval_request.request_type == 'publication':
                if market.status == Market.PAID_IN_PUBLICATION_QUEUE:
                    market.transition_status(
                        Market.PUBLISHED,
                        user=request.user,
                        reason=f"Admin approved publication: {admin_response}"
                    )
            elif approval_request.request_type == 'editing':
                market.transition_status(
                    Market.PAID_NEEDS_EDITING,
                    user=request.user,
                    reason=f"Admin approved editing request: {admin_response}"
                )
        else:  # reject
            if approval_request.request_type == 'publication':
                market.transition_status(
                    Market.PAID_NON_PUBLICATION,
                    user=request.user,
                    reason=f"Admin rejected publication: {admin_response}"
                )
        
        return Response(
            ApiResponse(
                success=True,
                code=200,
                message=_("Approval request processed successfully"),
                data={
                    'approval_id': approval_request.id,
                    'action': action,
                    'market_status': market.status,
                    'admin_response': admin_response
                }
            ),
            status=status.HTTP_200_OK
        )


class MarketShareAnalyticsAPIView(views.APIView):
    """
    API view for detailed market sharing analytics.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, market_id):
        """Get detailed sharing analytics for a market"""
        market = get_object_or_404(Market, id=market_id, user=request.user)
        
        from apps.market.models import MarketShare
        from django.db.models import Count, Q
        from django.utils import timezone
        from datetime import timedelta
        
        # Time-based analytics
        now = timezone.now()
        last_30_days = now - timedelta(days=30)
        last_7_days = now - timedelta(days=7)
        
        analytics_data = {
            'total_shares': market.shares.count(),
            'shares_last_30_days': market.shares.filter(created_at__gte=last_30_days).count(),
            'shares_last_7_days': market.shares.filter(created_at__gte=last_7_days).count(),
            'shares_today': market.shares.filter(created_at__date=now.date()).count(),
            
            # Platform breakdown
            'platform_stats': list(
                market.shares.values('platform')
                .annotate(count=Count('platform'))
                .order_by('-count')
            ),
            
            # Daily shares for the last 30 days
            'daily_shares': [],
            
            # Top sharers
            'top_sharers': list(
                market.shares.filter(shared_by__isnull=False)
                .values('shared_by__mobile_number', 'shared_by__email')
                .annotate(share_count=Count('id'))
                .order_by('-share_count')[:10]
            ),
            
            # Share conversion metrics
            'conversion_metrics': {
                'share_to_view_ratio': 0,
                'total_views': market.view_count,
                'estimated_reach': market.shares.count() * 5,  # Estimated reach multiplier
            }
        }
        
        # Calculate daily shares for chart
        for i in range(30):
            date = (now - timedelta(days=i)).date()
            daily_count = market.shares.filter(created_at__date=date).count()
            analytics_data['daily_shares'].append({
                'date': date.isoformat(),
                'shares': daily_count
            })
        
        # Calculate share to view ratio
        if market.shares.count() > 0:
            analytics_data['conversion_metrics']['share_to_view_ratio'] = round(
                (market.view_count / market.shares.count()), 2
            )
        
        # Add platform display names
        for platform_stat in analytics_data['platform_stats']:
            platform_display = dict(MarketShare.SHARE_PLATFORMS).get(
                platform_stat['platform'], 
                platform_stat['platform']
            )
            platform_stat['platform_display'] = platform_display
        
        return Response(
            ApiResponse(
                success=True,
                code=200,
                data=analytics_data
            ),
            status=status.HTTP_200_OK
        )
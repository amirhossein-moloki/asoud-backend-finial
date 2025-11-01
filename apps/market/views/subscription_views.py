from rest_framework import views, generics, status, permissions
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.utils.translation import gettext_lazy as _
from utils.response import ApiResponse
from ..models import Market, MarketSubscription
from ..serializers.workflow_serializers import MarketSubscriptionSerializer
from ..services import SubscriptionService, PaymentService
from rest_framework import serializers


class SubscriptionPlanSerializer(serializers.Serializer):
    """Serializer for subscription plan information"""
    plan_type = serializers.CharField()
    name = serializers.CharField()
    price = serializers.DecimalField(max_digits=10, decimal_places=2)
    duration_days = serializers.IntegerField()
    features = serializers.ListField(child=serializers.CharField())


class PaymentRequestSerializer(serializers.Serializer):
    """Serializer for payment request data"""
    gateway = serializers.CharField()
    amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    subscription_id = serializers.UUIDField()
    payment_url = serializers.URLField()
    reference_id = serializers.CharField()


class SubscriptionPlansAPIView(views.APIView):
    """
    API view to get available subscription plans with pricing.
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        plans = SubscriptionService.get_subscription_plans()
        
        # Convert to list format for serialization
        plan_list = []
        for plan_type, plan_data in plans.items():
            plan_list.append({
                'plan_type': plan_type,
                **plan_data
            })
        
        serializer = SubscriptionPlanSerializer(plan_list, many=True)
        
        return Response(
            ApiResponse(
                success=True,
                code=200,
                message=_("Subscription plans retrieved successfully"),
                data=serializer.data
            )
        )


class MarketSubscriptionCreateAPIView(views.APIView):
    """
    API view for creating market subscriptions with payment integration.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, market_id):
        market = get_object_or_404(Market, id=market_id, user=request.user)
        
        plan_type = request.data.get('plan_type')
        gateway = request.data.get('gateway', 'zarinpal')
        
        if not plan_type:
            return Response(
                ApiResponse(
                    success=False,
                    code=400,
                    message=_("Plan type is required")
                ),
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Create subscription
            subscription = SubscriptionService.create_subscription(
                market=market,
                plan_type=plan_type
            )
            
            # Create payment request
            payment_data = PaymentService.create_payment_request(
                subscription=subscription,
                gateway=gateway
            )
            
            return Response(
                ApiResponse(
                    success=True,
                    code=201,
                    message=_("Subscription created successfully"),
                    data={
                        'subscription': MarketSubscriptionSerializer(subscription).data,
                        'payment': PaymentRequestSerializer(payment_data).data
                    }
                ),
                status=status.HTTP_201_CREATED
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


class MarketSubscriptionListAPIView(generics.ListAPIView):
    """
    API view to list subscriptions for user's markets.
    """
    serializer_class = MarketSubscriptionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return MarketSubscription.objects.filter(
            market__user=self.request.user
        ).order_by('-created_at')


class MarketSubscriptionDetailAPIView(generics.RetrieveAPIView):
    """
    API view to get subscription details.
    """
    serializer_class = MarketSubscriptionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return MarketSubscription.objects.filter(
            market__user=self.request.user
        )


class SubscriptionPaymentVerifyAPIView(views.APIView):
    """
    API view to verify subscription payment.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        payment_reference = request.data.get('payment_reference')
        gateway = request.data.get('gateway', 'zarinpal')
        
        if not payment_reference:
            return Response(
                ApiResponse(
                    success=False,
                    code=400,
                    message=_("Payment reference is required")
                ),
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Get subscription by payment reference
            subscription = get_object_or_404(
                MarketSubscription,
                payment_reference=payment_reference,
                market__user=request.user
            )
            
            # Verify payment with gateway
            payment_result = PaymentService.verify_payment(
                payment_reference=payment_reference,
                gateway=gateway
            )
            
            if payment_result['success']:
                # Activate subscription
                SubscriptionService.activate_subscription(subscription)
                
                return Response(
                    ApiResponse(
                        success=True,
                        code=200,
                        message=_("Payment verified and subscription activated"),
                        data=MarketSubscriptionSerializer(subscription).data
                    )
                )
            else:
                return Response(
                    ApiResponse(
                        success=False,
                        code=400,
                        message=_("Payment verification failed")
                    ),
                    status=status.HTTP_400_BAD_REQUEST
                )
                
        except Exception as e:
            return Response(
                ApiResponse(
                    success=False,
                    code=500,
                    message=_("Payment verification error"),
                    error=str(e)
                ),
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class SubscriptionRenewAPIView(views.APIView):
    """
    API view to renew a subscription.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, subscription_id):
        subscription = get_object_or_404(
            MarketSubscription,
            id=subscription_id,
            market__user=request.user
        )
        
        new_plan_type = request.data.get('plan_type')
        gateway = request.data.get('gateway', 'zarinpal')
        
        try:
            # Create renewal subscription
            new_subscription = SubscriptionService.renew_subscription(
                subscription=subscription,
                new_plan_type=new_plan_type
            )
            
            # Create payment request
            payment_data = PaymentService.create_payment_request(
                subscription=new_subscription,
                gateway=gateway
            )
            
            return Response(
                ApiResponse(
                    success=True,
                    code=201,
                    message=_("Subscription renewal created successfully"),
                    data={
                        'subscription': MarketSubscriptionSerializer(new_subscription).data,
                        'payment': PaymentRequestSerializer(payment_data).data
                    }
                ),
                status=status.HTTP_201_CREATED
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


class SubscriptionCancelAPIView(views.APIView):
    """
    API view to cancel a subscription.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, subscription_id):
        subscription = get_object_or_404(
            MarketSubscription,
            id=subscription_id,
            market__user=request.user,
            status=MarketSubscription.ACTIVE
        )
        
        reason = request.data.get('reason', 'User requested cancellation')
        
        try:
            # Cancel subscription
            SubscriptionService.cancel_subscription(
                subscription=subscription,
                reason=reason
            )
            
            return Response(
                ApiResponse(
                    success=True,
                    code=200,
                    message=_("Subscription cancelled successfully"),
                    data=MarketSubscriptionSerializer(subscription).data
                )
            )
            
        except Exception as e:
            return Response(
                ApiResponse(
                    success=False,
                    code=500,
                    message=_("Subscription cancellation error"),
                    error=str(e)
                ),
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


# Admin Views
class AdminSubscriptionListAPIView(generics.ListAPIView):
    """
    Admin API view to list all subscriptions.
    """
    serializer_class = MarketSubscriptionSerializer
    permission_classes = [permissions.IsAuthenticated, permissions.IsAdminUser]
    queryset = MarketSubscription.objects.all().order_by('-created_at')


class AdminSubscriptionStatsAPIView(views.APIView):
    """
    Admin API view to get subscription statistics.
    """
    permission_classes = [permissions.IsAuthenticated, permissions.IsAdminUser]

    def get(self, request):
        stats = {
            'total_subscriptions': MarketSubscription.objects.count(),
            'active_subscriptions': MarketSubscription.objects.filter(
                status=MarketSubscription.ACTIVE
            ).count(),
            'expired_subscriptions': MarketSubscription.objects.filter(
                status=MarketSubscription.EXPIRED
            ).count(),
            'cancelled_subscriptions': MarketSubscription.objects.filter(
                status=MarketSubscription.CANCELLED
            ).count(),
            'pending_subscriptions': MarketSubscription.objects.filter(
                status=MarketSubscription.PENDING
            ).count(),
        }
        
        # Revenue statistics
        from django.db.models import Sum
        revenue_stats = {
            'total_revenue': MarketSubscription.objects.filter(
                status__in=[MarketSubscription.ACTIVE, MarketSubscription.EXPIRED]
            ).aggregate(Sum('amount'))['amount__sum'] or 0,
            'monthly_revenue': MarketSubscription.objects.filter(
                status__in=[MarketSubscription.ACTIVE, MarketSubscription.EXPIRED],
                plan_type=MarketSubscription.MONTHLY
            ).aggregate(Sum('amount'))['amount__sum'] or 0,
            'quarterly_revenue': MarketSubscription.objects.filter(
                status__in=[MarketSubscription.ACTIVE, MarketSubscription.EXPIRED],
                plan_type=MarketSubscription.QUARTERLY
            ).aggregate(Sum('amount'))['amount__sum'] or 0,
            'yearly_revenue': MarketSubscription.objects.filter(
                status__in=[MarketSubscription.ACTIVE, MarketSubscription.EXPIRED],
                plan_type=MarketSubscription.YEARLY
            ).aggregate(Sum('amount'))['amount__sum'] or 0,
        }
        
        return Response(
            ApiResponse(
                success=True,
                code=200,
                message=_("Subscription statistics retrieved successfully"),
                data={
                    'subscription_stats': stats,
                    'revenue_stats': revenue_stats
                }
            )
        )
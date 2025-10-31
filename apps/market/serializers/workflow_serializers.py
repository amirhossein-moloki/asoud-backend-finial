from rest_framework import serializers
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from datetime import timedelta

from apps.market.models import (
    Market,
    MarketWorkflowHistory,
    MarketApprovalRequest,
    MarketSubscription,
)


class MarketStatusTransitionSerializer(serializers.Serializer):
    """
    Serializer for market status transitions in the 8-state workflow.
    """
    new_status = serializers.ChoiceField(
        choices=Market.STATUS_CHOICES,
        help_text=_("New status to transition to")
    )
    reason = serializers.CharField(
        max_length=500,
        required=False,
        allow_blank=True,
        help_text=_("Reason for status change")
    )

    def validate(self, attrs):
        market = self.context['market']
        new_status = attrs['new_status']
        
        if not market.can_transition_to(new_status):
            raise serializers.ValidationError(
                f"Cannot transition from {market.status} to {new_status}"
            )
        
        attrs['old_status'] = market.status
        return attrs


class MarketActionsSerializer(serializers.ModelSerializer):
    """
    Serializer to show available actions for a market based on its status.
    """
    available_actions = serializers.SerializerMethodField()
    is_editable = serializers.SerializerMethodField()
    is_publishable = serializers.SerializerMethodField()
    share_url = serializers.SerializerMethodField()
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = Market
        fields = [
            'id', 'name', 'status', 'status_display', 'is_paid',
            'available_actions', 'is_editable', 'is_publishable', 'share_url'
        ]

    def get_available_actions(self, obj):
        return obj.get_available_actions()

    def get_is_editable(self, obj):
        return obj.is_editable()

    def get_is_publishable(self, obj):
        return obj.is_publishable()

    def get_share_url(self, obj):
        return obj.get_share_url()


class MarketWorkflowHistorySerializer(serializers.ModelSerializer):
    """
    Serializer for market workflow history records.
    """
    from_status_display = serializers.CharField(source='get_from_status_display', read_only=True)
    to_status_display = serializers.CharField(source='get_to_status_display', read_only=True)
    changed_by_name = serializers.CharField(source='changed_by.get_full_name', read_only=True)

    class Meta:
        model = MarketWorkflowHistory
        fields = [
            'id', 'from_status', 'from_status_display', 'to_status', 'to_status_display',
            'changed_by', 'changed_by_name', 'reason', 'admin_notes', 'created_at'
        ]


class MarketApprovalRequestSerializer(serializers.ModelSerializer):
    """
    Serializer for market approval requests.
    """
    requested_by_name = serializers.CharField(source='requested_by.get_full_name', read_only=True)
    reviewed_by_name = serializers.CharField(source='reviewed_by.get_full_name', read_only=True)
    market_name = serializers.CharField(source='market.name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = MarketApprovalRequest
        fields = [
            'id', 'market', 'market_name', 'requested_by', 'requested_by_name',
            'reviewed_by', 'reviewed_by_name', 'status', 'status_display',
            'request_type', 'message', 'admin_response', 'created_at', 'reviewed_at'
        ]
        read_only_fields = ['requested_by', 'reviewed_by', 'reviewed_at']

    def validate(self, attrs):
        market = attrs.get('market') or self.context.get('market')
        request_type = attrs['request_type']
        
        # Validate request type based on market status
        if request_type == 'publication':
            if market.status not in [Market.PAID_UNDER_CREATION, Market.PAID_NEEDS_EDITING]:
                raise serializers.ValidationError(
                    _("Publication requests can only be made for markets in 'Paid - Under Creation' or 'Paid - Needs Editing' status")
                )
        elif request_type == 'editing':
            if market.status != Market.PUBLISHED:
                raise serializers.ValidationError(
                    _("Editing requests can only be made for published markets")
                )
        elif request_type == 'reactivation':
            if market.status != Market.INACTIVE:
                raise serializers.ValidationError(
                    _("Reactivation requests can only be made for inactive markets")
                )
        
        # Check for existing pending requests
        existing_request = MarketApprovalRequest.objects.filter(
            market=market,
            request_type=request_type,
            status=MarketApprovalRequest.PENDING
        ).exists()
        
        if existing_request:
            raise serializers.ValidationError(
                _("A pending request of this type already exists for this market")
            )
        
        return attrs


class MarketSubscriptionSerializer(serializers.ModelSerializer):
    """
    Serializer for market subscriptions.
    """
    market_name = serializers.CharField(source='market.name', read_only=True)
    plan_type_display = serializers.CharField(source='get_plan_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    is_active = serializers.SerializerMethodField()
    days_remaining = serializers.SerializerMethodField()

    class Meta:
        model = MarketSubscription
        fields = [
            'id', 'market', 'market_name', 'plan_type', 'plan_type_display',
            'status', 'status_display', 'amount', 'start_date', 'end_date',
            'payment_reference', 'auto_renew', 'is_active', 'days_remaining',
            'created_at'
        ]
        read_only_fields = ['market']

    def get_is_active(self, obj):
        return obj.is_active()

    def get_days_remaining(self, obj):
        if obj.status == MarketSubscription.ACTIVE and obj.end_date:
            remaining = (obj.end_date - timezone.now()).days
            return max(0, remaining)
        return 0

    def validate(self, attrs):
        plan_type = attrs['plan_type']
        
        # Set subscription duration based on plan type
        start_date = timezone.now()
        
        if plan_type == MarketSubscription.MONTHLY:
            end_date = start_date + timedelta(days=30)
        elif plan_type == MarketSubscription.QUARTERLY:
            end_date = start_date + timedelta(days=90)
        elif plan_type == MarketSubscription.YEARLY:
            end_date = start_date + timedelta(days=365)
        else:
            raise serializers.ValidationError(_("Invalid plan type"))
        
        attrs['start_date'] = start_date
        attrs['end_date'] = end_date
        
        return attrs

    def create(self, validated_data):
        # Set status to active for new subscriptions
        validated_data['status'] = MarketSubscription.ACTIVE
        return super().create(validated_data)


class MarketStatusSummarySerializer(serializers.Serializer):
    """
    Serializer for market status summary and statistics.
    """
    total_markets = serializers.IntegerField()
    unpaid_under_creation = serializers.IntegerField()
    paid_under_creation = serializers.IntegerField()
    paid_in_publication_queue = serializers.IntegerField()
    paid_non_publication = serializers.IntegerField()
    published = serializers.IntegerField()
    paid_needs_editing = serializers.IntegerField()
    inactive = serializers.IntegerField()
    payment_pending = serializers.IntegerField()


class MarketPublicShareSerializer(serializers.ModelSerializer):
    """
    Serializer for public market sharing (limited information).
    """
    category_name = serializers.CharField(source='sub_category.category.name', read_only=True)
    subcategory_name = serializers.CharField(source='sub_category.name', read_only=True)
    city_name = serializers.CharField(source='location.city.name', read_only=True)

    class Meta:
        model = Market
        fields = [
            'id', 'name', 'type', 'description', 'slogan',
            'logo_img', 'background_img', 'view_count',
            'category_name', 'subcategory_name', 'city_name'
        ]
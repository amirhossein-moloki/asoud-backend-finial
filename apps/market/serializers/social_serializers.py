from rest_framework import serializers
from django.utils.translation import gettext_lazy as _
from django.contrib.contenttypes.models import ContentType

from apps.market.models import (
    Market, MarketLike, MarketBookmark, MarketShare, 
    MarketReport, MarketView
)
from apps.comment.models import Comment
from apps.notification.models import Notification
from apps.users.serializers import UserSerializer as UserBasicSerializer


class MarketLikeSerializer(serializers.ModelSerializer):
    """Serializer for market likes"""
    user = UserBasicSerializer(read_only=True)
    market_title = serializers.CharField(source='market.title', read_only=True)

    class Meta:
        model = MarketLike
        fields = [
            'id', 'user', 'market', 'market_title', 
            'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class MarketBookmarkSerializer(serializers.ModelSerializer):
    """Serializer for market bookmarks"""
    user = UserBasicSerializer(read_only=True)
    market_title = serializers.CharField(source='market.title', read_only=True)
    market_image = serializers.SerializerMethodField()

    class Meta:
        model = MarketBookmark
        fields = [
            'id', 'user', 'market', 'market_title', 'market_image',
            'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_market_image(self, obj):
        """Get market main image"""
        if obj.market.image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.market.image.url)
        return None


class MarketShareSerializer(serializers.ModelSerializer):
    """Serializer for market shares"""
    shared_by = UserBasicSerializer(read_only=True)
    platform_display = serializers.CharField(source='get_platform_display', read_only=True)
    market_title = serializers.CharField(source='market.title', read_only=True)

    class Meta:
        model = MarketShare
        fields = [
            'id', 'shared_by', 'market', 'market_title', 'platform', 
            'platform_display', 'ip_address', 'created_at'
        ]
        read_only_fields = ['id', 'created_at', 'ip_address']


class MarketReportSerializer(serializers.ModelSerializer):
    """Serializer for market reports"""
    creator = UserBasicSerializer(read_only=True)
    market_title = serializers.CharField(source='market.title', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = MarketReport
        fields = [
            'id', 'creator', 'market', 'market_title', 'reason', 
            'description', 'status', 'status_display', 'created_at'
        ]
        read_only_fields = ['id', 'created_at', 'status']

    def validate_reason(self, value):
        """Validate report reason"""
        if not value or len(value.strip()) < 3:
            raise serializers.ValidationError(
                _('Report reason must be at least 3 characters long')
            )
        return value.strip()

    def validate_description(self, value):
        """Validate report description"""
        if value and len(value.strip()) > 1000:
            raise serializers.ValidationError(
                _('Description cannot exceed 1000 characters')
            )
        return value.strip() if value else ''


class MarketViewSerializer(serializers.ModelSerializer):
    """Serializer for market views"""
    user = UserBasicSerializer(read_only=True)
    market_title = serializers.CharField(source='market.title', read_only=True)

    class Meta:
        model = MarketView
        fields = [
            'id', 'user', 'market', 'market_title', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class SocialStatsSerializer(serializers.Serializer):
    """Serializer for social statistics"""
    likes = serializers.IntegerField()
    bookmarks = serializers.IntegerField()
    shares = serializers.IntegerField()
    views = serializers.IntegerField()
    comments = serializers.IntegerField()
    reports = serializers.IntegerField()

    # User-specific interactions
    is_liked = serializers.BooleanField(required=False)
    is_bookmarked = serializers.BooleanField(required=False)
    has_reported = serializers.BooleanField(required=False)


class NotificationIconSerializer(serializers.Serializer):
    """Serializer for notification icon counts"""
    total = serializers.IntegerField()
    likes = serializers.IntegerField()
    shares = serializers.IntegerField()
    comments = serializers.IntegerField()
    reports = serializers.IntegerField()
    bookmarks = serializers.IntegerField()
    help_requests = serializers.IntegerField()


class NotificationSerializer(serializers.ModelSerializer):
    """Enhanced notification serializer"""
    sender = UserBasicSerializer(read_only=True)
    recipient = UserBasicSerializer(read_only=True)
    time_ago = serializers.SerializerMethodField()
    icon = serializers.SerializerMethodField()
    action_url = serializers.SerializerMethodField()

    class Meta:
        model = Notification
        fields = [
            'id', 'sender', 'recipient', 'notification_type', 'title', 
            'message', 'data', 'is_read', 'read_at', 'created_at',
            'time_ago', 'icon', 'action_url'
        ]
        read_only_fields = ['id', 'created_at']

    def get_time_ago(self, obj):
        """Get human-readable time ago"""
        from django.utils.timesince import timesince
        return timesince(obj.created_at)

    def get_icon(self, obj):
        """Get appropriate icon for notification type"""
        icon_map = {
            'market_like': 'heart',
            'market_share': 'share',
            'market_report': 'flag',
            'comment': 'message-circle',
            'comment_reply': 'reply',
            'help_request': 'help-circle',
            'system': 'bell',
            'market_approved': 'check-circle',
            'market_rejected': 'x-circle',
            'subscription_expiry': 'clock',
            'payment_success': 'credit-card',
            'payment_failed': 'alert-circle'
        }
        return icon_map.get(obj.notification_type, 'bell')

    def get_action_url(self, obj):
        """Get action URL based on notification type and data"""
        if not obj.data:
            return None

        data = obj.data
        notification_type = obj.notification_type

        if notification_type in ['market_like', 'market_share', 'market_report']:
            market_id = data.get('market_id')
            if market_id:
                return f'/markets/{market_id}/'

        elif notification_type in ['comment', 'comment_reply']:
            market_id = data.get('market_id')
            comment_id = data.get('comment_id')
            if market_id:
                url = f'/markets/{market_id}/'
                if comment_id:
                    url += f'#comment-{comment_id}'
                return url

        elif notification_type == 'help_request':
            return '/help/requests/'

        elif notification_type in ['market_approved', 'market_rejected']:
            market_id = data.get('market_id')
            if market_id:
                return f'/owner/markets/{market_id}/'

        elif notification_type in ['subscription_expiry', 'payment_success', 'payment_failed']:
            return '/owner/subscription/'

        return None


class CommentNotificationSerializer(serializers.Serializer):
    """Serializer for comment-related notifications"""
    market_id = serializers.IntegerField()
    comment_text = serializers.CharField(max_length=500)
    parent_comment_id = serializers.IntegerField(required=False, allow_null=True)

    def validate_comment_text(self, value):
        """Validate comment text"""
        if not value or len(value.strip()) < 1:
            raise serializers.ValidationError(
                _('Comment text is required')
            )
        if len(value.strip()) > 500:
            raise serializers.ValidationError(
                _('Comment cannot exceed 500 characters')
            )
        return value.strip()

    def validate_market_id(self, value):
        """Validate market exists"""
        try:
            Market.objects.get(id=value)
        except Market.DoesNotExist:
            raise serializers.ValidationError(
                _('Market not found')
            )
        return value


class HelpRequestSerializer(serializers.Serializer):
    """Serializer for help requests"""
    subject = serializers.CharField(max_length=200)
    message = serializers.CharField(max_length=2000)
    category = serializers.ChoiceField(
        choices=[
            ('general', _('General')),
            ('technical', _('Technical Issue')),
            ('billing', _('Billing')),
            ('account', _('Account')),
            ('market', _('Market Related')),
            ('bug', _('Bug Report')),
            ('feature', _('Feature Request'))
        ],
        default='general'
    )
    priority = serializers.ChoiceField(
        choices=[
            ('low', _('Low')),
            ('medium', _('Medium')),
            ('high', _('High')),
            ('urgent', _('Urgent'))
        ],
        default='medium'
    )

    def validate_subject(self, value):
        """Validate subject"""
        if not value or len(value.strip()) < 5:
            raise serializers.ValidationError(
                _('Subject must be at least 5 characters long')
            )
        return value.strip()

    def validate_message(self, value):
        """Validate message"""
        if not value or len(value.strip()) < 10:
            raise serializers.ValidationError(
                _('Message must be at least 10 characters long')
            )
        return value.strip()


class SocialInteractionSummarySerializer(serializers.Serializer):
    """Summary serializer for all social interactions"""
    market_id = serializers.IntegerField()
    market_title = serializers.CharField()
    
    # Counts
    total_likes = serializers.IntegerField()
    total_bookmarks = serializers.IntegerField()
    total_shares = serializers.IntegerField()
    total_views = serializers.IntegerField()
    total_comments = serializers.IntegerField()
    total_reports = serializers.IntegerField()
    
    # User interactions (if authenticated)
    user_liked = serializers.BooleanField(required=False)
    user_bookmarked = serializers.BooleanField(required=False)
    user_reported = serializers.BooleanField(required=False)
    
    # Recent activity
    recent_likes = MarketLikeSerializer(many=True, required=False)
    recent_shares = MarketShareSerializer(many=True, required=False)
    
    # Trending indicators
    is_trending = serializers.BooleanField(required=False)
    trend_score = serializers.FloatField(required=False)


class NotificationPreferenceSerializer(serializers.Serializer):
    """Serializer for notification preferences"""
    email_notifications = serializers.BooleanField(default=True)
    push_notifications = serializers.BooleanField(default=True)
    
    # Specific notification types
    likes_notifications = serializers.BooleanField(default=True)
    comments_notifications = serializers.BooleanField(default=True)
    shares_notifications = serializers.BooleanField(default=True)
    reports_notifications = serializers.BooleanField(default=True)
    system_notifications = serializers.BooleanField(default=True)
    marketing_notifications = serializers.BooleanField(default=False)
    
    # Frequency settings
    notification_frequency = serializers.ChoiceField(
        choices=[
            ('instant', _('Instant')),
            ('hourly', _('Hourly')),
            ('daily', _('Daily')),
            ('weekly', _('Weekly'))
        ],
        default='instant'
    )
    
    quiet_hours_start = serializers.TimeField(required=False, allow_null=True)
    quiet_hours_end = serializers.TimeField(required=False, allow_null=True)
"""
Analytics Serializers for ASOUD Platform
Advanced analytics and machine learning serializers
"""

from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import (
    UserBehaviorEvent,
    UserSession,
    ItemAnalytics, 
    MarketAnalytics, UserAnalytics, AnalyticsAggregation
)

User = get_user_model()


class UserBehaviorEventSerializer(serializers.ModelSerializer):
    """
    Serializer for user behavior events
    """
    user_username = serializers.CharField(source='user.username', read_only=True)
    event_type_display = serializers.CharField(source='get_event_type_display', read_only=True)
    content_object_name = serializers.SerializerMethodField()
    
    class Meta:
        model = UserBehaviorEvent
        fields = [
            'id', 'user', 'user_username', 'session_id', 'event_type', 
            'event_type_display', 'page_url', 'referrer_url', 'event_data',
            'device_type', 'browser', 'os', 'country', 'city', 
            'content_object_name', 'timestamp'
        ]
        read_only_fields = ['id', 'timestamp']
    
    def get_content_object_name(self, obj) -> str:
        """Get the name of the content object"""
        if obj.content_object:
            if hasattr(obj.content_object, 'name'):
                return str(obj.content_object.name)
            elif hasattr(obj.content_object, 'title'):
                return str(obj.content_object.title)
            elif hasattr(obj.content_object, 'username'):
                return str(obj.content_object.username)
        return ""


class UserSessionSerializer(serializers.ModelSerializer):
    """
    Serializer for user sessions
    """
    user_username = serializers.CharField(source='user.username', read_only=True)
    duration_display = serializers.SerializerMethodField()
    
    class Meta:
        model = UserSession
        fields = [
            'id', 'user', 'user_username', 'session_id', 'ip_address',
            'device_type', 'browser', 'os', 'country', 'city',
            'start_time', 'end_time', 'duration', 'duration_display',
            'page_views', 'events_count', 'converted', 'conversion_value'
        ]
        read_only_fields = ['id', 'duration']
    
    def get_duration_display(self, obj) -> str:
        """Get human-readable duration"""
        if obj.duration:
            total_seconds = int(obj.duration.total_seconds())
            hours = total_seconds // 3600
            minutes = (total_seconds % 3600) // 60
            seconds = total_seconds % 60
            
            if hours > 0:
                return f"{hours}h {minutes}m {seconds}s"
            elif minutes > 0:
                return f"{minutes}m {seconds}s"
            else:
                return f"{seconds}s"
        return "0s"


class ItemAnalyticsSerializer(serializers.ModelSerializer):
    """
    Serializer for item analytics
    """
    item_name = serializers.CharField(source='item.name', read_only=True)
    item_price = serializers.DecimalField(source='item.price', max_digits=10, decimal_places=2, read_only=True)
    item_category = serializers.CharField(source='item.category.name', read_only=True)
    
    class Meta:
        model = ItemAnalytics
        fields = [
            'id', 'item', 'item_name', 'item_price', 'item_category',
            'total_views', 'unique_views', 'views_today', 'views_this_week', 'views_this_month',
            'total_clicks', 'click_through_rate', 'add_to_cart_count', 'add_to_cart_rate',
            'total_purchases', 'conversion_rate', 'revenue', 'search_appearances',
            'search_rank_avg', 'last_viewed', 'last_purchased', 'popularity_score',
            'trending_score', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class MarketAnalyticsSerializer(serializers.ModelSerializer):
    """
    Serializer for market analytics
    """
    market_name = serializers.CharField(source='market.name', read_only=True)
    market_owner = serializers.CharField(source='market.user.username', read_only=True)
    avg_session_duration_display = serializers.SerializerMethodField()
    
    class Meta:
        model = MarketAnalytics
        fields = [
            'id', 'market', 'market_name', 'market_owner',
            'total_visits', 'unique_visitors', 'bounce_rate', 'avg_session_duration',
            'avg_session_duration_display', 'total_products', 'active_products',
            'total_views', 'total_orders', 'total_revenue', 'avg_order_value',
            'total_customers', 'repeat_customers', 'customer_retention_rate',
            'conversion_rate', 'revenue_per_visit', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_avg_session_duration_display(self, obj) -> str:
        """Get human-readable session duration"""
        if obj.avg_session_duration:
            total_seconds = int(obj.avg_session_duration.total_seconds())
            hours = total_seconds // 3600
            minutes = (total_seconds % 3600) // 60
            seconds = total_seconds % 60
            
            if hours > 0:
                return f"{hours}h {minutes}m {seconds}s"
            elif minutes > 0:
                return f"{minutes}m {seconds}s"
            else:
                return f"{seconds}s"
        return "0s"


class UserAnalyticsSerializer(serializers.ModelSerializer):
    """
    Serializer for user analytics
    """
    username = serializers.CharField(source='user.username', read_only=True)
    email = serializers.CharField(source='user.email', read_only=True)
    avg_session_duration_display = serializers.SerializerMethodField()
    
    class Meta:
        model = UserAnalytics
        fields = [
            'id', 'user', 'username', 'email',
            'total_sessions', 'total_page_views', 'avg_session_duration',
            'avg_session_duration_display', 'last_activity', 'total_orders',
            'total_spent', 'avg_order_value', 'last_purchase', 'products_viewed',
            'products_purchased', 'reviews_written', 'chat_messages',
            'preferred_categories', 'preferred_price_range', 'shopping_patterns',
            'customer_segment', 'churn_probability', 'lifetime_value',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_avg_session_duration_display(self, obj) -> str:
        """Get human-readable session duration"""
        if obj.avg_session_duration:
            total_seconds = int(obj.avg_session_duration.total_seconds())
            hours = total_seconds // 3600
            minutes = (total_seconds % 3600) // 60
            seconds = total_seconds % 60
            
            if hours > 0:
                return f"{hours}h {minutes}m {seconds}s"
            elif minutes > 0:
                return f"{minutes}m {seconds}s"
            else:
                return f"{seconds}s"
        return "0s"


class AnalyticsAggregationSerializer(serializers.ModelSerializer):
    """
    Serializer for analytics aggregations
    """
    aggregation_type_display = serializers.CharField(source='get_aggregation_type_display', read_only=True)
    
    class Meta:
        model = AnalyticsAggregation
        fields = [
            'id', 'aggregation_type', 'aggregation_type_display', 'date',
            'total_users', 'total_sessions', 'total_page_views', 'total_orders',
            'total_revenue', 'conversion_rate', 'avg_order_value', 'bounce_rate',
            'new_users', 'returning_users', 'active_users', 'total_products',
            'products_sold', 'top_products', 'total_markets', 'active_markets',
            'top_markets', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class AnalyticsDashboardSerializer(serializers.Serializer):
    """
    Serializer for analytics dashboard data
    """
    # Overview metrics
    total_users = serializers.IntegerField()
    total_sessions = serializers.IntegerField()
    total_page_views = serializers.IntegerField()
    total_orders = serializers.IntegerField()
    total_revenue = serializers.DecimalField(max_digits=12, decimal_places=2)
    
    # Conversion metrics
    conversion_rate = serializers.FloatField()
    avg_order_value = serializers.DecimalField(max_digits=10, decimal_places=2)
    bounce_rate = serializers.FloatField()
    
    # User metrics
    new_users = serializers.IntegerField()
    returning_users = serializers.IntegerField()
    active_users = serializers.IntegerField()
    
    # Product metrics
    total_products = serializers.IntegerField()
    products_sold = serializers.IntegerField()
    top_products = serializers.ListField()
    
    # Market metrics
    total_markets = serializers.IntegerField()
    active_markets = serializers.IntegerField()
    top_markets = serializers.ListField()
    
    # Time-based data
    daily_data = serializers.ListField()
    weekly_data = serializers.ListField()
    monthly_data = serializers.ListField()
    
    # Real-time metrics
    real_time_users = serializers.IntegerField()
    real_time_orders = serializers.IntegerField()
    real_time_revenue = serializers.DecimalField(max_digits=12, decimal_places=2)


class UserBehaviorInsightsSerializer(serializers.Serializer):
    """
    Serializer for user behavior insights
    """
    user_id = serializers.IntegerField()
    username = serializers.CharField()
    
    # Activity insights
    total_sessions = serializers.IntegerField()
    total_page_views = serializers.IntegerField()
    avg_session_duration = serializers.DurationField()
    last_activity = serializers.DateTimeField()
    
    # Purchase insights
    total_orders = serializers.IntegerField()
    total_spent = serializers.DecimalField(max_digits=10, decimal_places=2)
    avg_order_value = serializers.DecimalField(max_digits=10, decimal_places=2)
    last_purchase = serializers.DateTimeField()
    
    # Behavioral insights
    preferred_categories = serializers.ListField()
    preferred_price_range = serializers.DictField()
    shopping_patterns = serializers.DictField()
    
    # ML insights
    customer_segment = serializers.CharField()
    churn_probability = serializers.FloatField()
    lifetime_value = serializers.DecimalField(max_digits=10, decimal_places=2)
    
    # Recommendations
    recommended_products = serializers.ListField()
    recommended_categories = serializers.ListField()
    recommended_markets = serializers.ListField()


class ProductPerformanceSerializer(serializers.Serializer):
    """
    Serializer for product performance analytics
    """
    product_id = serializers.IntegerField()
    product_name = serializers.CharField()
    product_price = serializers.DecimalField(max_digits=10, decimal_places=2)
    product_category = serializers.CharField()
    
    # Performance metrics
    total_views = serializers.IntegerField()
    unique_views = serializers.IntegerField()
    click_through_rate = serializers.FloatField()
    add_to_cart_rate = serializers.FloatField()
    conversion_rate = serializers.FloatField()
    revenue = serializers.DecimalField(max_digits=10, decimal_places=2)
    
    # Ranking metrics
    popularity_score = serializers.FloatField()
    trending_score = serializers.FloatField()
    search_rank_avg = serializers.FloatField()
    
    # Time-based metrics
    views_today = serializers.IntegerField()
    views_this_week = serializers.IntegerField()
    views_this_month = serializers.IntegerField()
    
    # Recommendations
    similar_products = serializers.ListField()
    improvement_suggestions = serializers.ListField()


class MarketPerformanceSerializer(serializers.Serializer):
    """
    Serializer for market performance analytics
    """
    market_id = serializers.IntegerField()
    market_name = serializers.CharField()
    market_owner = serializers.CharField()
    
    # Traffic metrics
    total_visits = serializers.IntegerField()
    unique_visitors = serializers.IntegerField()
    bounce_rate = serializers.FloatField()
    avg_session_duration = serializers.DurationField()
    
    # Sales metrics
    total_orders = serializers.IntegerField()
    total_revenue = serializers.DecimalField(max_digits=12, decimal_places=2)
    avg_order_value = serializers.DecimalField(max_digits=10, decimal_places=2)
    conversion_rate = serializers.FloatField()
    
    # Customer metrics
    total_customers = serializers.IntegerField()
    repeat_customers = serializers.IntegerField()
    customer_retention_rate = serializers.FloatField()
    
    # Performance metrics
    revenue_per_visit = serializers.DecimalField(max_digits=10, decimal_places=2)
    products_count = serializers.IntegerField()
    active_products = serializers.IntegerField()
    
    # Recommendations
    improvement_suggestions = serializers.ListField()
    growth_opportunities = serializers.ListField()


class RealTimeMetricsSerializer(serializers.Serializer):
    """
    Serializer for real-time metrics
    """
    timestamp = serializers.DateTimeField()
    
    # Current activity
    active_users = serializers.IntegerField()
    active_sessions = serializers.IntegerField()
    current_orders = serializers.IntegerField()
    current_revenue = serializers.DecimalField(max_digits=12, decimal_places=2)
    
    # Real-time events
    recent_events = serializers.ListField()
    top_products = serializers.ListField()
    top_markets = serializers.ListField()
    
    # System metrics
    server_load = serializers.FloatField()
    database_connections = serializers.IntegerField()
    cache_hit_rate = serializers.FloatField()
    
    # Alerts
    alerts = serializers.ListField()
    warnings = serializers.ListField()

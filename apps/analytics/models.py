"""
Analytics Models for ASOUD Platform
Advanced analytics and machine learning data models
"""

from django.db import models
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from django.utils import timezone
import json

User = get_user_model()


def default_dict():
    return {}


def default_list():
    return []


class UserBehaviorEvent(models.Model):
    """
    User behavior tracking events
    """
    EVENT_TYPES = [
        ('page_view', 'Page View'),
        ('product_view', 'Product View'),
        ('product_click', 'Product Click'),
        ('add_to_cart', 'Add to Cart'),
        ('remove_from_cart', 'Remove from Cart'),
        ('purchase', 'Purchase'),
        ('search', 'Search'),
        ('filter', 'Filter'),
        ('login', 'Login'),
        ('logout', 'Logout'),
        ('signup', 'Signup'),
        ('profile_update', 'Profile Update'),
        ('chat_message', 'Chat Message'),
        ('review', 'Review'),
        ('bookmark', 'Bookmark'),
        ('share', 'Share'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    session_id = models.CharField(max_length=255, db_index=True)
    event_type = models.CharField(max_length=50, choices=EVENT_TYPES, db_index=True)
    page_url = models.URLField(max_length=500, null=True, blank=True)
    referrer_url = models.URLField(max_length=500, null=True, blank=True)
    
    # Generic foreign key for any object
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, null=True, blank=True)
    object_id = models.PositiveIntegerField(null=True, blank=True)
    content_object = GenericForeignKey('content_type', 'object_id')
    
    # Event data
    event_data = models.JSONField(default=default_dict, blank=True)
    user_agent = models.TextField(null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    device_type = models.CharField(max_length=50, null=True, blank=True)
    browser = models.CharField(max_length=100, null=True, blank=True)
    os = models.CharField(max_length=100, null=True, blank=True)
    
    # Location data
    country = models.CharField(max_length=100, null=True, blank=True)
    city = models.CharField(max_length=100, null=True, blank=True)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    
    # Timestamps
    timestamp = models.DateTimeField(default=timezone.now, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['user', 'timestamp']),
            models.Index(fields=['event_type', 'timestamp']),
            models.Index(fields=['session_id', 'timestamp']),
            models.Index(fields=['content_type', 'object_id']),
        ]
    
    def __str__(self):
        return f"{self.event_type} - {self.user or 'Anonymous'} - {self.timestamp}"


class UserSession(models.Model):
    """
    User session tracking
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    session_id = models.CharField(max_length=255, unique=True, db_index=True)
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField()
    device_type = models.CharField(max_length=50)
    browser = models.CharField(max_length=100)
    os = models.CharField(max_length=100)
    
    # Location
    country = models.CharField(max_length=100, null=True, blank=True)
    city = models.CharField(max_length=100, null=True, blank=True)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    
    # Session data
    start_time = models.DateTimeField(default=timezone.now)
    end_time = models.DateTimeField(null=True, blank=True)
    duration = models.DurationField(null=True, blank=True)
    page_views = models.PositiveIntegerField(default=0)
    events_count = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    
    # Conversion data
    converted = models.BooleanField(default=False)
    conversion_value = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    class Meta:
        ordering = ['-start_time']
        indexes = [
            models.Index(fields=['user', 'start_time']),
            models.Index(fields=['session_id']),
            models.Index(fields=['converted', 'start_time']),
        ]
    
    def __str__(self):
        return f"Session {self.session_id} - {self.user or 'Anonymous'}"


class ProductAnalytics(models.Model):
    """
    Product-specific analytics
    """
    from apps.product.models import Product
    
    product = models.OneToOneField(Product, on_delete=models.CASCADE, related_name='analytics')
    
    # View metrics
    total_views = models.PositiveIntegerField(default=0)
    unique_views = models.PositiveIntegerField(default=0)
    views_today = models.PositiveIntegerField(default=0)
    views_this_week = models.PositiveIntegerField(default=0)
    views_this_month = models.PositiveIntegerField(default=0)
    
    # Interaction metrics
    total_clicks = models.PositiveIntegerField(default=0)
    click_through_rate = models.FloatField(default=0.0)
    add_to_cart_count = models.PositiveIntegerField(default=0)
    add_to_cart_rate = models.FloatField(default=0.0)
    
    # Conversion metrics
    total_purchases = models.PositiveIntegerField(default=0)
    conversion_rate = models.FloatField(default=0.0)
    revenue = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Search metrics
    search_appearances = models.PositiveIntegerField(default=0)
    search_rank_avg = models.FloatField(default=0.0)
    
    # Time-based metrics
    last_viewed = models.DateTimeField(null=True, blank=True)
    last_purchased = models.DateTimeField(null=True, blank=True)
    
    # Calculated fields
    popularity_score = models.FloatField(default=0.0)
    trending_score = models.FloatField(default=0.0)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-popularity_score']
    
    def __str__(self):
        return f"Analytics for {self.product.name}"
    
    def calculate_metrics(self):
        """Calculate all analytics metrics"""
        from django.db.models import Count, Avg, Sum
        from django.utils import timezone
        from datetime import timedelta
        
        now = timezone.now()
        today = now.date()
        week_ago = now - timedelta(days=7)
        month_ago = now - timedelta(days=30)
        
        # Get events for this product
        events = UserBehaviorEvent.objects.filter(
            content_type__model='product',
            object_id=self.product.id
        )
        
        # Calculate view metrics
        self.total_views = events.filter(event_type='product_view').count()
        self.unique_views = events.filter(event_type='product_view').values('user').distinct().count()
        self.views_today = events.filter(event_type='product_view', timestamp__date=today).count()
        self.views_this_week = events.filter(event_type='product_view', timestamp__gte=week_ago).count()
        self.views_this_month = events.filter(event_type='product_view', timestamp__gte=month_ago).count()
        
        # Calculate interaction metrics
        self.total_clicks = events.filter(event_type='product_click').count()
        if self.total_views > 0:
            self.click_through_rate = (self.total_clicks / self.total_views) * 100
        
        self.add_to_cart_count = events.filter(event_type='add_to_cart').count()
        if self.total_views > 0:
            self.add_to_cart_rate = (self.add_to_cart_count / self.total_views) * 100
        
        # Calculate conversion metrics
        self.total_purchases = events.filter(event_type='purchase').count()
        if self.total_views > 0:
            self.conversion_rate = (self.total_purchases / self.total_views) * 100
        
        # Calculate revenue
        from apps.cart.models import OrderItem
        order_items = OrderItem.objects.filter(product=self.product, order__is_paid=True)
        self.revenue = sum(item.quantity * item.price for item in order_items)
        
        # Calculate popularity and trending scores
        self.popularity_score = self._calculate_popularity_score()
        self.trending_score = self._calculate_trending_score()
        
        self.save()
    
    def _calculate_popularity_score(self):
        """Calculate popularity score based on multiple factors"""
        score = 0
        
        # Views weight: 30%
        score += (self.total_views * 0.3)
        
        # Clicks weight: 25%
        score += (self.total_clicks * 0.25)
        
        # Add to cart weight: 20%
        score += (self.add_to_cart_count * 0.2)
        
        # Purchases weight: 25%
        score += (self.total_purchases * 0.25)
        
        return score
    
    def _calculate_trending_score(self):
        """Calculate trending score based on recent activity"""
        from django.utils import timezone
        from datetime import timedelta
        
        now = timezone.now()
        week_ago = now - timedelta(days=7)
        
        # Get recent events
        recent_events = UserBehaviorEvent.objects.filter(
            content_type__model='product',
            object_id=self.product.id,
            timestamp__gte=week_ago
        )
        
        recent_views = recent_events.filter(event_type='product_view').count()
        recent_clicks = recent_events.filter(event_type='product_click').count()
        recent_purchases = recent_events.filter(event_type='purchase').count()
        
        # Calculate trending score
        score = (recent_views * 0.4) + (recent_clicks * 0.3) + (recent_purchases * 0.3)
        
        return score


class MarketAnalytics(models.Model):
    """
    Market-specific analytics
    """
    from apps.market.models import Market
    
    market = models.OneToOneField(Market, on_delete=models.CASCADE, related_name='analytics')
    
    # Traffic metrics
    total_visits = models.PositiveIntegerField(default=0)
    unique_visitors = models.PositiveIntegerField(default=0)
    bounce_rate = models.FloatField(default=0.0)
    avg_session_duration = models.DurationField(null=True, blank=True)
    
    # Product metrics
    total_products = models.PositiveIntegerField(default=0)
    active_products = models.PositiveIntegerField(default=0)
    total_views = models.PositiveIntegerField(default=0)
    
    # Sales metrics
    total_orders = models.PositiveIntegerField(default=0)
    total_revenue = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    avg_order_value = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Customer metrics
    total_customers = models.PositiveIntegerField(default=0)
    repeat_customers = models.PositiveIntegerField(default=0)
    customer_retention_rate = models.FloatField(default=0.0)
    
    # Performance metrics
    conversion_rate = models.FloatField(default=0.0)
    revenue_per_visit = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-total_revenue']
    
    def __str__(self):
        return f"Analytics for {self.market.name}"


class UserAnalytics(models.Model):
    """
    User-specific analytics
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='analytics')
    
    # Activity metrics
    total_sessions = models.PositiveIntegerField(default=0)
    total_page_views = models.PositiveIntegerField(default=0)
    avg_session_duration = models.DurationField(null=True, blank=True)
    last_activity = models.DateTimeField(null=True, blank=True)
    
    # Purchase metrics
    total_orders = models.PositiveIntegerField(default=0)
    total_spent = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    avg_order_value = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    last_purchase = models.DateTimeField(null=True, blank=True)
    
    # Engagement metrics
    products_viewed = models.PositiveIntegerField(default=0)
    products_purchased = models.PositiveIntegerField(default=0)
    reviews_written = models.PositiveIntegerField(default=0)
    chat_messages = models.PositiveIntegerField(default=0)
    
    # Behavioral metrics
    preferred_categories = models.JSONField(default=default_list, blank=True)
    preferred_price_range = models.JSONField(default=default_dict, blank=True)
    shopping_patterns = models.JSONField(default=default_dict, blank=True)
    
    # ML features
    customer_segment = models.CharField(max_length=50, null=True, blank=True)
    churn_probability = models.FloatField(default=0.0)
    lifetime_value = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-total_spent']
    
    def __str__(self):
        return f"Analytics for {self.user.mobile_number}"
    
    def calculate_metrics(self):
        """Calculate and update user analytics metrics"""
        from django.db.models import Count, Sum, Avg, Max
        from datetime import timedelta
        
        # Calculate session metrics
        sessions = UserSession.objects.filter(user=self.user)
        self.total_sessions = sessions.count()
        
        if self.total_sessions > 0:
            durations = [s.duration for s in sessions if s.duration]
            if durations:
                self.avg_session_duration = sum(durations, timedelta()) / len(durations)
        
        # Calculate page view metrics
        page_views = UserBehaviorEvent.objects.filter(
            user=self.user,
            event_type='page_view'
        )
        self.total_page_views = page_views.count()
        
        # Calculate purchase metrics
        purchases = UserBehaviorEvent.objects.filter(
            user=self.user,
            event_type='purchase'
        )
        self.total_orders = purchases.count()
        
        if self.total_orders > 0:
            total_value = sum(
                float(p.event_data.get('value', 0)) 
                for p in purchases 
                if p.event_data.get('value')
            )
            self.total_spent = total_value
            self.avg_order_value = total_value / self.total_orders
        
        # Calculate engagement metrics
        self.products_viewed = UserBehaviorEvent.objects.filter(
            user=self.user,
            event_type='product_view'
        ).count()
        
        self.products_purchased = UserBehaviorEvent.objects.filter(
            user=self.user,
            event_type='purchase'
        ).count()
        
        self.reviews_written = UserBehaviorEvent.objects.filter(
            user=self.user,
            event_type='review'
        ).count()
        
        self.chat_messages = UserBehaviorEvent.objects.filter(
            user=self.user,
            event_type='chat_message'
        ).count()
        
        # Update last activity
        last_event = UserBehaviorEvent.objects.filter(
            user=self.user
        ).order_by('-timestamp').first()
        
        if last_event:
            self.last_activity = last_event.timestamp
        
        # Update last purchase
        last_purchase = purchases.order_by('-timestamp').first()
        if last_purchase:
            self.last_purchase = last_purchase.timestamp
        
        self.save()
    
    @property
    def duration(self):
        """Calculate session duration"""
        if hasattr(self, 'start_time') and hasattr(self, 'end_time'):
            if self.end_time and self.start_time:
                return self.end_time - self.start_time
        return None


class AnalyticsAggregation(models.Model):
    """
    Pre-aggregated analytics data for performance
    """
    AGGREGATION_TYPES = [
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('yearly', 'Yearly'),
    ]
    
    aggregation_type = models.CharField(max_length=20, choices=AGGREGATION_TYPES)
    date = models.DateField()
    
    # General metrics
    total_users = models.PositiveIntegerField(default=0)
    total_sessions = models.PositiveIntegerField(default=0)
    total_page_views = models.PositiveIntegerField(default=0)
    total_orders = models.PositiveIntegerField(default=0)
    total_revenue = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    # Conversion metrics
    conversion_rate = models.FloatField(default=0.0)
    avg_order_value = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    bounce_rate = models.FloatField(default=0.0)
    
    # User metrics
    new_users = models.PositiveIntegerField(default=0)
    returning_users = models.PositiveIntegerField(default=0)
    active_users = models.PositiveIntegerField(default=0)
    
    # Product metrics
    total_products = models.PositiveIntegerField(default=0)
    products_sold = models.PositiveIntegerField(default=0)
    top_products = models.JSONField(default=default_list, blank=True)
    
    # Market metrics
    total_markets = models.PositiveIntegerField(default=0)
    active_markets = models.PositiveIntegerField(default=0)
    top_markets = models.JSONField(default=default_list, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['aggregation_type', 'date']
        ordering = ['-date']
    
    def __str__(self):
        return f"{self.aggregation_type.title()} Analytics - {self.date}"


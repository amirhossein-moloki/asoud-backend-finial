"""
Analytics Admin for ASOUD Platform
"""

from django.contrib import admin
from .models import (
    UserBehaviorEvent, UserSession, ItemAnalytics, 
    MarketAnalytics, UserAnalytics, AnalyticsAggregation
)


@admin.register(UserBehaviorEvent)
class UserBehaviorEventAdmin(admin.ModelAdmin):
    list_display = ['event_type', 'user', 'session_id', 'timestamp', 'device_type', 'country']
    list_filter = ['event_type', 'device_type', 'country', 'timestamp']
    search_fields = ['user__username', 'session_id', 'page_url']
    readonly_fields = ['timestamp', 'created_at']
    date_hierarchy = 'timestamp'
    
    fieldsets = (
        ('Event Information', {
            'fields': ('user', 'session_id', 'event_type', 'page_url', 'referrer_url')
        }),
        ('Content', {
            'fields': ('content_type', 'object_id', 'event_data')
        }),
        ('Device Information', {
            'fields': ('user_agent', 'ip_address', 'device_type', 'browser', 'os')
        }),
        ('Location', {
            'fields': ('country', 'city', 'latitude', 'longitude')
        }),
        ('Timestamps', {
            'fields': ('timestamp', 'created_at')
        })
    )


@admin.register(UserSession)
class UserSessionAdmin(admin.ModelAdmin):
    list_display = ['user', 'session_id', 'start_time', 'end_time', 'duration', 'converted', 'conversion_value']
    list_filter = ['device_type', 'browser', 'os', 'country', 'converted', 'start_time']
    search_fields = ['user__username', 'session_id', 'ip_address']
    readonly_fields = ['duration']
    date_hierarchy = 'start_time'
    
    fieldsets = (
        ('Session Information', {
            'fields': ('user', 'session_id', 'ip_address', 'start_time', 'end_time', 'duration')
        }),
        ('Device Information', {
            'fields': ('user_agent', 'device_type', 'browser', 'os')
        }),
        ('Location', {
            'fields': ('country', 'city', 'latitude', 'longitude')
        }),
        ('Metrics', {
            'fields': ('page_views', 'events_count', 'converted', 'conversion_value')
        })
    )


@admin.register(ItemAnalytics)
class ItemAnalyticsAdmin(admin.ModelAdmin):
    list_display = ['item', 'total_views', 'conversion_rate', 'revenue', 'popularity_score', 'trending_score']
    list_filter = ['created_at', 'updated_at']
    search_fields = ['item__name', 'item__subcategory__name']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Item', {
            'fields': ('item',)
        }),
        ('View Metrics', {
            'fields': ('total_views', 'unique_views', 'views_today', 'views_this_week', 'views_this_month')
        }),
        ('Interaction Metrics', {
            'fields': ('total_clicks', 'click_through_rate', 'add_to_cart_count', 'add_to_cart_rate')
        }),
        ('Conversion Metrics', {
            'fields': ('total_purchases', 'conversion_rate', 'revenue', 'search_appearances', 'search_rank_avg')
        }),
        ('Time-based Metrics', {
            'fields': ('last_viewed', 'last_purchased')
        }),
        ('Scores', {
            'fields': ('popularity_score', 'trending_score')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        })
    )
    
    actions = ['calculate_metrics']
    
    def calculate_metrics(self, request, queryset):
        """Calculate metrics for selected items"""
        for item_analytics in queryset:
            item_analytics.calculate_metrics()
        
        self.message_user(request, f'Metrics calculated for {queryset.count()} items.')


@admin.register(MarketAnalytics)
class MarketAnalyticsAdmin(admin.ModelAdmin):
    list_display = ['market', 'total_visits', 'total_revenue', 'conversion_rate', 'customer_retention_rate']
    list_filter = ['created_at', 'updated_at']
    search_fields = ['market__name', 'market__user__username']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Market', {
            'fields': ('market',)
        }),
        ('Traffic Metrics', {
            'fields': ('total_visits', 'unique_visitors', 'bounce_rate', 'avg_session_duration')
        }),
        ('Product Metrics', {
            'fields': ('total_products', 'active_products', 'total_views')
        }),
        ('Sales Metrics', {
            'fields': ('total_orders', 'total_revenue', 'avg_order_value')
        }),
        ('Customer Metrics', {
            'fields': ('total_customers', 'repeat_customers', 'customer_retention_rate')
        }),
        ('Performance Metrics', {
            'fields': ('conversion_rate', 'revenue_per_visit')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        })
    )


@admin.register(UserAnalytics)
class UserAnalyticsAdmin(admin.ModelAdmin):
    list_display = ['user', 'total_sessions', 'total_spent', 'customer_segment', 'churn_probability', 'lifetime_value']
    list_filter = ['customer_segment', 'created_at', 'updated_at']
    search_fields = ['user__username', 'user__email']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('User', {
            'fields': ('user',)
        }),
        ('Activity Metrics', {
            'fields': ('total_sessions', 'total_page_views', 'avg_session_duration', 'last_activity')
        }),
        ('Purchase Metrics', {
            'fields': ('total_orders', 'total_spent', 'avg_order_value', 'last_purchase')
        }),
        ('Engagement Metrics', {
            'fields': ('products_viewed', 'products_purchased', 'reviews_written', 'chat_messages')
        }),
        ('Behavioral Metrics', {
            'fields': ('preferred_categories', 'preferred_price_range', 'shopping_patterns')
        }),
        ('ML Features', {
            'fields': ('customer_segment', 'churn_probability', 'lifetime_value')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        })
    )


@admin.register(AnalyticsAggregation)
class AnalyticsAggregationAdmin(admin.ModelAdmin):
    list_display = ['aggregation_type', 'date', 'total_users', 'total_revenue', 'conversion_rate']
    list_filter = ['aggregation_type', 'date']
    search_fields = ['aggregation_type']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Aggregation', {
            'fields': ('aggregation_type', 'date')
        }),
        ('General Metrics', {
            'fields': ('total_users', 'total_sessions', 'total_page_views', 'total_orders', 'total_revenue')
        }),
        ('Conversion Metrics', {
            'fields': ('conversion_rate', 'avg_order_value', 'bounce_rate')
        }),
        ('User Metrics', {
            'fields': ('new_users', 'returning_users', 'active_users')
        }),
        ('Product Metrics', {
            'fields': ('total_products', 'products_sold', 'top_products')
        }),
        ('Market Metrics', {
            'fields': ('total_markets', 'active_markets', 'top_markets')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        })
    )

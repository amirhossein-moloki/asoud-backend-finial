"""
Analytics Services for ASOUD Platform
Advanced analytics and machine learning services
"""

import logging
try:
    import numpy as np
    import pandas as pd
    HAS_ML_LIBS = True
except ImportError:
    HAS_ML_LIBS = False
    # Define dummy functions for when ML libraries are not available
    class DummyArray:
        def __init__(self, *args, **kwargs):
            pass
        def __getitem__(self, key):
            return 0
        def __setitem__(self, key, value):
            pass
        def __len__(self):
            return 0
        def mean(self):
            return 0
        def sum(self):
            return 0
        def std(self):
            return 0
        def max(self):
            return 0
        def min(self):
            return 0
    
    np = type('numpy', (), {
        'array': lambda x: DummyArray(),
        'mean': lambda x: 0,
        'std': lambda x: 0,
        'sum': lambda x: 0,
        'max': lambda x: 0,
        'min': lambda x: 0,
    })()
    
    pd = type('pandas', (), {
        'DataFrame': lambda x: x,
        'Series': lambda x: x,
    })()
from datetime import timedelta, datetime
from django.utils import timezone
from django.db.models import Count, Sum, Avg, Q, F
from django.core.cache import cache
from django.contrib.contenttypes.models import ContentType
from apps.cart.models import Order
from apps.category.models import Category

from .models import (
    UserBehaviorEvent, UserSession, ItemAnalytics, 
    MarketAnalytics, UserAnalytics, AnalyticsAggregation
)

logger = logging.getLogger(__name__)


class AnalyticsService:
    """
    Core analytics service for data processing and insights
    """
    
    def __init__(self):
        self.cache_timeout = 300  # 5 minutes
    
    def get_dashboard_data(self, user):
        """Get comprehensive dashboard data"""
        cache_key = f"dashboard_data_{user.id}"
        cached_data = cache.get(cache_key)
        
        if cached_data:
            return cached_data
        
        # Get time ranges
        now = timezone.now()
        today = now.date()
        week_ago = now - timedelta(days=7)
        month_ago = now - timedelta(days=30)
        
        # Overview metrics
        total_users = UserAnalytics.objects.filter(user=user).count()
        total_sessions = UserSession.objects.filter(user=user).count()
        total_page_views = UserBehaviorEvent.objects.filter(
            user=user, event_type='page_view'
        ).count()
        total_orders = UserBehaviorEvent.objects.filter(
            user=user, event_type='purchase'
        ).count()
        
        # Revenue calculation
        purchase_events = UserBehaviorEvent.objects.filter(
            user=user, event_type='purchase'
        )
        total_revenue = sum(float(event.event_data.get('value', 0)) for event in purchase_events)

        # Conversion metrics
        conversion_rate = self._calculate_conversion_rate(user=user)
        avg_order_value = self._calculate_avg_order_value(user=user)
        bounce_rate = self._calculate_bounce_rate(user=user)
        
        # User metrics
        new_users = UserAnalytics.objects.filter(
            user=user, created_at__gte=week_ago
        ).count()
        returning_users = UserSession.objects.filter(
            user=user, start_time__gte=week_ago
        ).values('user').distinct().count()
        active_users = UserSession.objects.filter(
            user=user, start_time__gte=today
        ).values('user').distinct().count()
        
        # Product metrics
        total_products = ItemAnalytics.objects.count()
        products_sold = UserBehaviorEvent.objects.filter(
            user=user, event_type='purchase'
        ).values('object_id').distinct().count()
        top_products = self._get_top_items(limit=5)
        
        # Market metrics
        total_markets = MarketAnalytics.objects.count()
        active_markets = MarketAnalytics.objects.filter(
            total_visits__gt=0
        ).count()
        top_markets = self._get_top_markets(limit=5)
        
        # Time-based data
        daily_data = self._get_daily_data(user=user, days=30)
        weekly_data = self._get_weekly_data(user=user, weeks=12)
        monthly_data = self._get_monthly_data(user=user, months=12)
        
        dashboard_data = {
            'total_users': total_users,
            'total_sessions': total_sessions,
            'total_page_views': total_page_views,
            'total_orders': total_orders,
            'total_revenue': total_revenue,
            'conversion_rate': conversion_rate,
            'avg_order_value': avg_order_value,
            'bounce_rate': bounce_rate,
            'new_users': new_users,
            'returning_users': returning_users,
            'active_users': active_users,
            'total_products': total_products,
            'products_sold': products_sold,
            'top_products': top_products,
            'total_markets': total_markets,
            'active_markets': active_markets,
            'top_markets': top_markets,
            'daily_data': daily_data,
            'weekly_data': weekly_data,
            'monthly_data': monthly_data,
            'real_time_users': active_users,
            'real_time_orders': 0,  # Will be calculated by real-time service
            'real_time_revenue': 0,  # Will be calculated by real-time service
        }
        
        # Cache the data
        cache.set(cache_key, dashboard_data, self.cache_timeout)
        
        return dashboard_data
    
    def get_time_series_data(self, days=30, metric='revenue'):
        """Get time series data for charts"""
        cache_key = f"time_series_{days}_{metric}"
        cached_data = cache.get(cache_key)
        
        if cached_data:
            return cached_data
        
        end_date = timezone.now()
        start_date = end_date - timedelta(days=days-1)
        
        # Create date range
        date_range = pd.date_range(start=start_date, end=end_date, freq='D')
        
        time_series_data = []
        
        for date in date_range:
            date_start = timezone.make_aware(datetime.combine(date.date(), datetime.min.time()))
            date_end = timezone.make_aware(datetime.combine(date.date(), datetime.max.time()))
            
            if metric == 'revenue':
                value = UserBehaviorEvent.objects.filter(
                    event_type='purchase',
                    timestamp__range=[date_start, date_end]
                ).aggregate(
                    total=Sum('event_data__value', default=0)
                )['total'] or 0
            elif metric == 'orders':
                value = UserBehaviorEvent.objects.filter(
                    event_type='purchase',
                    timestamp__range=[date_start, date_end]
                ).count()
            elif metric == 'users':
                value = UserSession.objects.filter(
                    start_time__range=[date_start, date_end]
                ).values('user').distinct().count()
            else:
                value = 0
            
            time_series_data.append({
                'date': date.date().isoformat(),
                'value': float(value)
            })
        
        # Cache the data
        cache.set(cache_key, time_series_data, self.cache_timeout)
        
        return time_series_data
    
    def get_top_performers(self, entity_type='products', limit=10):
        """Get top performing entities"""
        cache_key = f"top_performers_{entity_type}_{limit}"
        cached_data = cache.get(cache_key)
        
        if cached_data:
            return cached_data
        
        if entity_type == 'products':
            performers = ItemAnalytics.objects.order_by('-popularity_score')[:limit]
            data = []
            for performer in performers:
                data.append({
                    'id': performer.item.id,
                    'name': performer.item.name,
                    'score': performer.popularity_score,
                    'views': performer.total_views,
                    'revenue': float(performer.revenue)
                })
        elif entity_type == 'markets':
            performers = MarketAnalytics.objects.order_by('-total_revenue')[:limit]
            data = []
            for performer in performers:
                data.append({
                    'id': performer.market.id,
                    'name': performer.market.name,
                    'revenue': float(performer.total_revenue),
                    'visits': performer.total_visits,
                    'conversion_rate': performer.conversion_rate
                })
        else:
            data = []
        
        # Cache the data
        cache.set(cache_key, data, self.cache_timeout)
        
        return data
    
    def get_conversion_funnel(self, days=30):
        """Get conversion funnel data"""
        cache_key = f"conversion_funnel_{days}"
        cached_data = cache.get(cache_key)
        
        if cached_data:
            return cached_data
        
        start_date = timezone.now() - timedelta(days=days)
        
        # Get funnel steps
        funnel_data = {
            'visitors': UserSession.objects.filter(start_time__gte=start_date).count(),
            'page_views': UserBehaviorEvent.objects.filter(
                event_type='page_view',
                timestamp__gte=start_date
            ).count(),
            'product_views': UserBehaviorEvent.objects.filter(
                event_type='product_view',
                timestamp__gte=start_date
            ).count(),
            'add_to_cart': UserBehaviorEvent.objects.filter(
                event_type='add_to_cart',
                timestamp__gte=start_date
            ).count(),
            'purchases': UserBehaviorEvent.objects.filter(
                event_type='purchase',
                timestamp__gte=start_date
            ).count(),
        }
        
        # Calculate conversion rates
        funnel_data['conversion_rates'] = {
            'visitor_to_page_view': (funnel_data['page_views'] / funnel_data['visitors'] * 100) if funnel_data['visitors'] > 0 else 0,
            'page_view_to_product_view': (funnel_data['product_views'] / funnel_data['page_views'] * 100) if funnel_data['page_views'] > 0 else 0,
            'product_view_to_cart': (funnel_data['add_to_cart'] / funnel_data['product_views'] * 100) if funnel_data['product_views'] > 0 else 0,
            'cart_to_purchase': (funnel_data['purchases'] / funnel_data['add_to_cart'] * 100) if funnel_data['add_to_cart'] > 0 else 0,
        }
        
        # Cache the data
        cache.set(cache_key, funnel_data, self.cache_timeout)
        
        return funnel_data
    
    def get_geographic_analysis(self, days=30):
        """Get geographic analysis data"""
        cache_key = f"geographic_analysis_{days}"
        cached_data = cache.get(cache_key)
        
        if cached_data:
            return cached_data
        
        start_date = timezone.now() - timedelta(days=days)
        
        # Get geographic data
        geo_data = UserSession.objects.filter(
            start_time__gte=start_date
        ).values('country', 'city').annotate(
            sessions=Count('id'),
            unique_users=Count('user', distinct=True),
            revenue=Sum('conversion_value', default=0)
        ).order_by('-sessions')
        
        # Cache the data
        cache.set(cache_key, list(geo_data), self.cache_timeout)
        
        return list(geo_data)
    
    def get_device_analysis(self, days=30):
        """Get device analysis data"""
        cache_key = f"device_analysis_{days}"
        cached_data = cache.get(cache_key)
        
        if cached_data:
            return cached_data
        
        start_date = timezone.now() - timedelta(days=days)
        
        # Get device data
        device_data = UserSession.objects.filter(
            start_time__gte=start_date
        ).values('device_type', 'browser', 'os').annotate(
            sessions=Count('id'),
            unique_users=Count('user', distinct=True),
            avg_duration=Avg('duration'),
            conversion_rate=Avg('converted')
        ).order_by('-sessions')
        
        # Cache the data
        cache.set(cache_key, list(device_data), self.cache_timeout)
        
        return list(device_data)
    
    def _calculate_conversion_rate(self, user):
        """Calculate overall conversion rate"""
        total_sessions = UserSession.objects.filter(user=user).count()
        converted_sessions = UserSession.objects.filter(user=user, converted=True).count()
        
        return (converted_sessions / total_sessions * 100) if total_sessions > 0 else 0
    
    def _calculate_avg_order_value(self, user):
        """Calculate average order value"""
        purchase_events = UserBehaviorEvent.objects.filter(
            user=user, event_type='purchase'
        )
        total_revenue = sum(float(event.event_data.get('value', 0)) for event in purchase_events)
        total_orders = purchase_events.count()
        
        return (total_revenue / total_orders) if total_orders > 0 else 0
    
    def _calculate_bounce_rate(self, user):
        """Calculate bounce rate"""
        total_sessions = UserSession.objects.filter(user=user).count()
        bounced_sessions = UserSession.objects.filter(
            user=user,
            page_views=1,
            duration__lt=timedelta(seconds=30)
        ).count()
        
        return (bounced_sessions / total_sessions * 100) if total_sessions > 0 else 0
    
    def _get_top_items(self, limit=5):
        """Get top items"""
        return list(ItemAnalytics.objects.order_by('-popularity_score')[:limit].values(
            'item__name', 'popularity_score', 'total_views', 'revenue'
        ))
    
    def _get_top_markets(self, limit=5):
        """Get top markets"""
        return list(MarketAnalytics.objects.order_by('-total_revenue')[:limit].values(
            'market__name', 'total_revenue', 'total_visits', 'conversion_rate'
        ))
    
    def _get_daily_data(self, user, days=30):
        """Get daily data"""
        end_date = timezone.now()
        start_date = end_date - timedelta(days=days)
        
        daily_data = []
        for i in range(days):
            date = start_date + timedelta(days=i)
            date_start = timezone.make_aware(datetime.combine(date.date(), datetime.min.time()))
            date_end = timezone.make_aware(datetime.combine(date.date(), datetime.max.time()))
            
            purchase_events = UserBehaviorEvent.objects.filter(
                user=user, event_type='purchase',
                timestamp__range=[date_start, date_end]
            )
            revenue = sum(float(event.event_data.get('value', 0)) for event in purchase_events)

            daily_data.append({
                'date': date.date().isoformat(),
                'sessions': UserSession.objects.filter(
                    user=user, start_time__range=[date_start, date_end]
                ).count(),
                'revenue': revenue
            })
        
        return daily_data
    
    def _get_weekly_data(self, user, weeks=12):
        """Get weekly data"""
        end_date = timezone.now()
        start_date = end_date - timedelta(weeks=weeks)
        
        weekly_data = []
        for i in range(weeks):
            week_start = start_date + timedelta(weeks=i)
            week_end = week_start + timedelta(days=7)
            
            purchase_events = UserBehaviorEvent.objects.filter(
                user=user, event_type='purchase',
                timestamp__range=[week_start, week_end]
            )
            revenue = sum(float(event.event_data.get('value', 0)) for event in purchase_events)

            weekly_data.append({
                'week': week_start.date().isoformat(),
                'sessions': UserSession.objects.filter(
                    user=user, start_time__range=[week_start, week_end]
                ).count(),
                'revenue': revenue
            })
        
        return weekly_data
    
    def _get_monthly_data(self, user, months=12):
        """Get monthly data"""
        end_date = timezone.now()
        start_date = end_date - timedelta(days=months*30)
        
        monthly_data = []
        for i in range(months):
            month_start = start_date + timedelta(days=i*30)
            month_end = month_start + timedelta(days=30)
            
            purchase_events = UserBehaviorEvent.objects.filter(
                user=user, event_type='purchase',
                timestamp__range=[month_start, month_end]
            )
            revenue = sum(float(event.event_data.get('value', 0)) for event in purchase_events)

            monthly_data.append({
                'month': month_start.date().isoformat(),
                'sessions': UserSession.objects.filter(
                    user=user, start_time__range=[month_start, month_end]
                ).count(),
                'revenue': revenue
            })
        
        return monthly_data


class MLService:
    """
    Machine Learning service for recommendations and predictions
    """
    
    def __init__(self):
        self.cache_timeout = 600  # 10 minutes
    
    def get_product_recommendations(self, user_id, limit=10):
        """Get product recommendations for a user"""
        cache_key = f"product_recommendations_{user_id}_{limit}"
        cached_data = cache.get(cache_key)
        
        if cached_data:
            return cached_data
        
        # Simple collaborative filtering implementation
        recommendations = self._collaborative_filtering(user_id, limit)
        
        # Cache the data
        cache.set(cache_key, recommendations, self.cache_timeout)
        
        return recommendations
    
    def get_similar_products(self, product_id, limit=10):
        """Get similar products based on content similarity"""
        cache_key = f"similar_products_{product_id}_{limit}"
        cached_data = cache.get(cache_key)
        
        if cached_data:
            return cached_data
        
        # Simple content-based filtering
        similar_products = self._content_based_filtering(product_id, limit)
        
        # Cache the data
        cache.set(cache_key, similar_products, self.cache_timeout)
        
        return similar_products
    
    def get_price_optimization(self, product_id):
        """Get price optimization suggestions"""
        cache_key = f"price_optimization_{product_id}"
        cached_data = cache.get(cache_key)
        
        if cached_data:
            return cached_data
        
        # Simple price optimization algorithm
        price_suggestions = self._price_optimization_algorithm(product_id)
        
        # Cache the data
        cache.set(cache_key, price_suggestions, self.cache_timeout)
        
        return price_suggestions
    
    def get_demand_forecast(self, product_id, days=30):
        """Get demand forecast for a product"""
        cache_key = f"demand_forecast_{product_id}_{days}"
        cached_data = cache.get(cache_key)
        
        if cached_data:
            return cached_data
        
        # Simple time series forecasting
        forecast = self._demand_forecasting(product_id, days)
        
        # Cache the data
        cache.set(cache_key, forecast, self.cache_timeout)
        
        return forecast
    
    def get_customer_segmentation(self):
        """Get customer segmentation analysis"""
        cache_key = "customer_segmentation"
        cached_data = cache.get(cache_key)
        
        if cached_data:
            return cached_data
        
        # Simple clustering algorithm
        segmentation = self._customer_segmentation_algorithm()
        
        # Cache the data
        cache.set(cache_key, segmentation, self.cache_timeout)
        
        return segmentation
    
    def get_fraud_detection(self, days=7):
        """Get fraud detection analysis"""
        cache_key = f"fraud_detection_{days}"
        cached_data = cache.get(cache_key)
        
        if cached_data:
            return cached_data
        
        # Simple fraud detection algorithm
        fraud_analysis = self._fraud_detection_algorithm(days)
        
        # Cache the data
        cache.set(cache_key, fraud_analysis, self.cache_timeout)
        
        return fraud_analysis
    
    def get_user_recommendations(self, user):
        """Get comprehensive recommendations for a user"""
        user_id = user.id
        
        recommendations = {
            'products': self.get_product_recommendations(user_id, 5),
            'categories': self._get_category_recommendations(user_id),
            'markets': self._get_market_recommendations(user_id)
        }
        
        return recommendations
    
    def _collaborative_filtering(self, user_id, limit):
        """Simple collaborative filtering for product recommendations"""
        # Get user's purchase history
        user_events = UserBehaviorEvent.objects.filter(
            user_id=user_id,
            event_type='purchase'
        ).values_list('object_id', flat=True)
        
        if not user_events:
            # If no purchase history, return popular products
            return list(ItemAnalytics.objects.order_by('-popularity_score')[:limit].values(
                'item__name', 'item__base_price', 'popularity_score'
            ))
        
        # Find similar users based on purchase history
        similar_users = UserBehaviorEvent.objects.filter(
            event_type='purchase',
            object_id__in=user_events
        ).exclude(user_id=user_id).values_list('user_id', flat=True).distinct()
        
        # Get products purchased by similar users
        recommended_products = UserBehaviorEvent.objects.filter(
            user_id__in=similar_users,
            event_type='purchase'
        ).exclude(object_id__in=user_events).values(
            'object_id'
        ).annotate(
            count=Count('id')
        ).order_by('-count')[:limit]
        
        return list(recommended_products)
    
    def _content_based_filtering(self, product_id, limit):
        """Simple content-based filtering for similar products"""
        from apps.product.models import Product
        
        try:
            product = Product.objects.get(id=product_id)
            
            # Find products in the same category
            similar_products = Product.objects.filter(
                category=product.category
            ).exclude(id=product_id).annotate(
                views=Count('analytics__total_views')
            ).order_by('-views')[:limit]
            
            return list(similar_products.values(
                'id', 'name', 'price', 'category__name'
            ))
        except Product.DoesNotExist:
            return []
    
    def _price_optimization_algorithm(self, product_id):
        """Simple price optimization algorithm"""
        from apps.product.models import Product
        
        try:
            product = Product.objects.get(id=product_id)
            analytics = product.analytics
            
            # Simple price optimization based on demand elasticity
            current_price = float(product.price)
            demand = analytics.total_views
            conversion_rate = analytics.conversion_rate
            
            # Calculate optimal price
            if demand > 0 and conversion_rate > 0:
                # Simple elasticity calculation
                elasticity = -0.5  # Assumed elasticity
                optimal_price = current_price * (1 + (1 / elasticity))
                
                return {
                    'current_price': current_price,
                    'optimal_price': optimal_price,
                    'price_change': optimal_price - current_price,
                    'expected_demand_change': abs(elasticity) * 0.1,
                    'confidence': 0.7
                }
            else:
                return {
                    'current_price': current_price,
                    'optimal_price': current_price,
                    'price_change': 0,
                    'expected_demand_change': 0,
                    'confidence': 0.3
                }
        except Product.DoesNotExist:
            return {}
    
    def _demand_forecasting(self, product_id, days):
        """Simple demand forecasting algorithm"""
        from apps.product.models import Product
        
        try:
            product = Product.objects.get(id=product_id)
            
            # Get historical demand data
            end_date = timezone.now()
            start_date = end_date - timedelta(days=30)
            
            historical_demand = []
            for i in range(30):
                date = start_date + timedelta(days=i)
                date_start = timezone.make_aware(datetime.combine(date.date(), datetime.min.time()))
                date_end = timezone.make_aware(datetime.combine(date.date(), datetime.max.time()))
                
                demand = UserBehaviorEvent.objects.filter(
                    content_type__model='product',
                    object_id=product_id,
                    event_type='purchase',
                    timestamp__range=[date_start, date_end]
                ).count()
                
                historical_demand.append(demand)
            
            # Simple moving average forecast
            window_size = 7
            if len(historical_demand) >= window_size:
                avg_demand = sum(historical_demand[-window_size:]) / window_size
            else:
                avg_demand = sum(historical_demand) / len(historical_demand) if historical_demand else 0
            
            # Generate forecast
            forecast = []
            for i in range(days):
                forecast.append({
                    'date': (end_date + timedelta(days=i+1)).date().isoformat(),
                    'predicted_demand': max(0, int(avg_demand * (1 + np.random.normal(0, 0.1)))),
                    'confidence': 0.6
                })
            
            return forecast
        except Product.DoesNotExist:
            return []
    
    def _customer_segmentation_algorithm(self):
        """Simple customer segmentation algorithm"""
        # Get customer data
        customers = UserAnalytics.objects.all()
        
        segments = {
            'high_value': customers.filter(total_spent__gte=1000).count(),
            'medium_value': customers.filter(total_spent__gte=100, total_spent__lt=1000).count(),
            'low_value': customers.filter(total_spent__lt=100).count(),
            'new_customers': customers.filter(total_orders=0).count(),
            'loyal_customers': customers.filter(total_orders__gte=5).count(),
        }
        
        return segments
    
    def _fraud_detection_algorithm(self, days):
        """Simple fraud detection algorithm"""
        start_date = timezone.now() - timedelta(days=days)
        
        # Get suspicious activities
        suspicious_activities = UserBehaviorEvent.objects.filter(
            timestamp__gte=start_date,
            event_type='purchase'
        ).extra(
            select={'hour': "date_trunc('hour', timestamp)"}
        ).values('user', 'hour').annotate(
            purchase_count=Count('id')
        ).filter(purchase_count__gte=5)  # More than 5 purchases in an hour
        
        fraud_analysis = {
            'suspicious_activities': list(suspicious_activities),
            'risk_score': len(suspicious_activities) / 100,
            'alerts': []
        }
        
        # Generate alerts
        for activity in suspicious_activities:
            fraud_analysis['alerts'].append({
                'user_id': activity['user'],
                'hour': activity['hour'],
                'purchase_count': activity['purchase_count'],
                'risk_level': 'high' if activity['purchase_count'] > 10 else 'medium'
            })
        
        return fraud_analysis
    
    def _get_category_recommendations(self, user_id):
        """Get category recommendations for a user."""
        # 1. Try to get pre-calculated preferred categories
        user_analytics = UserAnalytics.objects.filter(user_id=user_id).first()
        if user_analytics and user_analytics.preferred_categories:
            # Assuming preferred_categories is a list of category objects or IDs
            return list(user_analytics.preferred_categories[:5])

        # 2. If not available, get categories from user's purchase history
        purchased_categories = Category.objects.filter(
            subcategory__item__orderitem__order__user_id=user_id
        ).annotate(
            purchase_count=Count('subcategory__item__orderitem')
        ).order_by('-purchase_count')[:5]

        if purchased_categories.exists():
            return list(purchased_categories)

        # 3. As a fallback, return globally popular categories
        popular_categories = Category.objects.annotate(
            product_count=Count('subcategory__item')
        ).order_by('-product_count')[:5]

        return list(popular_categories)
    
    def _get_market_recommendations(self, user_id):
        """Get market recommendations for a user"""
        # Get user's preferred markets
        user_events = UserBehaviorEvent.objects.filter(
            user_id=user_id,
            event_type='page_view'
        ).values_list('object_id', flat=True)
        
        if user_events:
            # Find markets with similar products
            from apps.market.models import Market
            return list(Market.objects.filter(
                product__id__in=user_events
            ).distinct()[:3].values_list('name', flat=True))
        
        # Return popular markets
        return list(MarketAnalytics.objects.order_by('-total_visits')[:3].values_list(
            'market__name', flat=True
        ))


class RealTimeAnalyticsService:
    """
    Real-time analytics service for live metrics
    """
    
    def __init__(self):
        self.cache_timeout = 60  # 1 minute
    
    def get_real_time_metrics(self):
        """Get real-time metrics"""
        cache_key = "real_time_metrics"
        cached_data = cache.get(cache_key)
        
        if cached_data:
            return cached_data
        
        now = timezone.now()
        last_hour = now - timedelta(hours=1)
        
        # Current activity
        active_users = UserSession.objects.filter(
            end_time__isnull=True
        ).count()
        
        active_sessions = UserSession.objects.filter(
            start_time__gte=last_hour
        ).count()
        
        current_orders = UserBehaviorEvent.objects.filter(
            event_type='purchase',
            timestamp__gte=last_hour
        ).count()
        
        current_revenue = UserBehaviorEvent.objects.filter(
            event_type='purchase',
            timestamp__gte=last_hour
        ).aggregate(
            total=Sum('event_data__value', default=0)
        )['total'] or 0
        
        # Recent events
        recent_events = UserBehaviorEvent.objects.filter(
            timestamp__gte=last_hour
        ).order_by('-timestamp')[:10].values(
            'event_type', 'user__email', 'timestamp'
        )
        
        # Top products (last hour)
        top_products = UserBehaviorEvent.objects.filter(
            event_type='product_view',
            timestamp__gte=last_hour
        ).values('object_id').annotate(
            views=Count('id')
        ).order_by('-views')[:5]
        
        # Top markets (last hour)
        top_markets = UserBehaviorEvent.objects.filter(
            event_type='page_view',
            timestamp__gte=last_hour
        ).values('object_id').annotate(
            views=Count('id')
        ).order_by('-views')[:5]
        
        # System metrics
        server_load = self._get_server_load()
        database_connections = self._get_database_connections()
        cache_hit_rate = self._get_cache_hit_rate()
        
        # Alerts and warnings
        alerts = self._get_alerts()
        warnings = self._get_warnings()
        
        real_time_data = {
            'timestamp': now.isoformat(),
            'active_users': active_users,
            'active_sessions': active_sessions,
            'current_orders': current_orders,
            'current_revenue': float(current_revenue),
            'recent_events': list(recent_events),
            'top_products': list(top_products),
            'top_markets': list(top_markets),
            'server_load': server_load,
            'database_connections': database_connections,
            'cache_hit_rate': cache_hit_rate,
            'alerts': alerts,
            'warnings': warnings
        }
        
        # Cache the data
        cache.set(cache_key, real_time_data, self.cache_timeout)
        
        return real_time_data
    
    def _get_server_load(self):
        """Get server load (simplified)"""
        try:
            import psutil
            return psutil.cpu_percent()
        except ImportError:
            return 0.0
    
    def _get_database_connections(self):
        """Get database connections count"""
        from django.db import connection
        from django.db.utils import OperationalError, ProgrammingError
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT count(*) FROM pg_stat_activity")
                return cursor.fetchone()[0]
        except (OperationalError, ProgrammingError):
            # This query is PostgreSQL-specific.
            # In a different DB environment (like SQLite in tests), it will fail.
            return 0
    
    def _get_cache_hit_rate(self):
        """Get cache hit rate"""
        try:
            from django.core.cache import cache
            # This is a simplified implementation
            return 85.0  # Placeholder
        except:
            return 0.0
    
    def _get_alerts(self):
        """Get system alerts"""
        alerts = []
        
        # Check for high error rate
        error_count = UserBehaviorEvent.objects.filter(
            event_type='error',
            timestamp__gte=timezone.now() - timedelta(minutes=5)
        ).count()
        
        if error_count > 10:
            alerts.append({
                'type': 'error_rate',
                'message': f'High error rate: {error_count} errors in last 5 minutes',
                'severity': 'high'
            })
        
        return alerts
    
    def _get_warnings(self):
        """Get system warnings"""
        warnings = []
        
        # Check for low cache hit rate
        cache_hit_rate = self._get_cache_hit_rate()
        if cache_hit_rate < 80:
            warnings.append({
                'type': 'cache_performance',
                'message': f'Low cache hit rate: {cache_hit_rate}%',
                'severity': 'medium'
            })
        
        return warnings

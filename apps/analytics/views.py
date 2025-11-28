"""
Analytics Views for ASOUD Platform
Advanced analytics and machine learning views
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django.db.models import Count, Sum, Avg, Q, F
from django.utils import timezone
from datetime import timedelta, datetime
from django.core.cache import cache
from django.contrib.contenttypes.models import ContentType

from .models import (
    UserBehaviorEvent,
    UserSession,
    ItemAnalytics, 
    MarketAnalytics, UserAnalytics, AnalyticsAggregation
)
from .serializers import (
    UserBehaviorEventSerializer, UserSessionSerializer, ItemAnalyticsSerializer,
    MarketAnalyticsSerializer, UserAnalyticsSerializer, AnalyticsAggregationSerializer,
    AnalyticsDashboardSerializer, UserBehaviorInsightsSerializer,
    ProductPerformanceSerializer, MarketPerformanceSerializer, RealTimeMetricsSerializer
)
from .services import AnalyticsService, MLService, RealTimeAnalyticsService


class UserBehaviorEventViewSet(viewsets.ModelViewSet):
    """
    ViewSet for user behavior events
    """
    queryset = UserBehaviorEvent.objects.all()
    serializer_class = UserBehaviorEventSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filter events based on user permissions"""
        queryset = super().get_queryset()
        
        # If user is not admin, only show their own events
        if not self.request.user.is_staff:
            queryset = queryset.filter(user=self.request.user)
        
        return queryset
    
    @action(detail=False, methods=['get'])
    def by_event_type(self, request):
        """Get events grouped by event type"""
        event_type = request.query_params.get('event_type')
        days = int(request.query_params.get('days', 30))
        
        start_date = timezone.now() - timedelta(days=days)
        
        queryset = self.get_queryset().filter(
            timestamp__gte=start_date
        )
        
        if event_type:
            queryset = queryset.filter(event_type=event_type)
        
        # Group by event type
        events_by_type = queryset.values('event_type').annotate(
            count=Count('id'),
            unique_users=Count('user', distinct=True)
        ).order_by('-count')
        
        return Response(events_by_type)
    
    @action(detail=False, methods=['get'])
    def timeline(self, request):
        """Get events timeline"""
        days = int(request.query_params.get('days', 7))
        event_type = request.query_params.get('event_type')
        
        start_date = timezone.now() - timedelta(days=days)
        
        queryset = self.get_queryset().filter(timestamp__gte=start_date)
        
        if event_type:
            queryset = queryset.filter(event_type=event_type)
        
        # Group by hour
        timeline_data = queryset.extra(
            select={'hour': "date_trunc('hour', timestamp)"}
        ).values('hour').annotate(
            count=Count('id')
        ).order_by('hour')
        
        return Response(timeline_data)


class UserSessionViewSet(viewsets.ModelViewSet):
    """
    ViewSet for user sessions
    """
    queryset = UserSession.objects.all()
    serializer_class = UserSessionSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filter sessions based on user permissions"""
        queryset = super().get_queryset()
        
        # If user is not admin, only show their own sessions
        if not self.request.user.is_staff:
            queryset = queryset.filter(user=self.request.user)
        
        return queryset
    
    @action(detail=False, methods=['get'])
    def active_sessions(self, request):
        """Get active sessions"""
        active_sessions = self.get_queryset().filter(
            end_time__isnull=True
        ).order_by('-start_time')
        
        serializer = self.get_serializer(active_sessions, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def conversion_analysis(self, request):
        """Get conversion analysis"""
        days = int(request.query_params.get('days', 30))
        start_date = timezone.now() - timedelta(days=days)
        
        sessions = self.get_queryset().filter(start_time__gte=start_date)
        
        total_sessions = sessions.count()
        converted_sessions = sessions.filter(converted=True).count()
        conversion_rate = (converted_sessions / total_sessions * 100) if total_sessions > 0 else 0
        
        avg_session_duration = sessions.aggregate(
            avg_duration=Avg('duration')
        )['avg_duration']
        
        avg_conversion_value = sessions.filter(converted=True).aggregate(
            avg_value=Avg('conversion_value')
        )['avg_value']
        
        return Response({
            'total_sessions': total_sessions,
            'converted_sessions': converted_sessions,
            'conversion_rate': round(conversion_rate, 2),
            'avg_session_duration': avg_session_duration,
            'avg_conversion_value': avg_conversion_value
        })


class ItemAnalyticsViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for item analytics
    """
    serializer_class = ItemAnalyticsSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Filter events based on user permissions"""
        queryset = ItemAnalytics.objects.all()

        # If user is not admin, only show their own events
        if not self.request.user.is_staff:
            queryset = queryset.filter(item__owner=self.request.user)

        return queryset
    
    @action(detail=False, methods=['get'])
    def top_products(self, request):
        """Get top performing products"""
        limit = int(request.query_params.get('limit', 10))
        metric = request.query_params.get('metric', 'popularity_score')
        
        queryset = self.get_queryset().order_by(f'-{metric}')[:limit]
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def trending_products(self, request):
        """Get trending products"""
        limit = int(request.query_params.get('limit', 10))
        
        queryset = self.get_queryset().order_by('-trending_score')[:limit]
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def calculate_metrics(self, request, pk=None):
        """Calculate metrics for a specific product"""
        item_analytics = self.get_object()
        item_analytics.calculate_metrics()
        
        serializer = self.get_serializer(item_analytics)
        return Response(serializer.data)


class MarketAnalyticsViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for market analytics
    """
    serializer_class = MarketAnalyticsSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Filter events based on user permissions"""
        queryset = MarketAnalytics.objects.all()

        # If user is not admin, only show their own events
        if not self.request.user.is_staff:
            queryset = queryset.filter(market__owner=self.request.user)

        return queryset
    
    @action(detail=False, methods=['get'])
    def top_markets(self, request):
        """Get top performing markets"""
        limit = int(request.query_params.get('limit', 10))
        metric = request.query_params.get('metric', 'total_revenue')
        
        queryset = self.get_queryset().order_by(f'-{metric}')[:limit]
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def market_comparison(self, request):
        """Compare market performance"""
        market_ids = request.query_params.getlist('market_ids')
        
        if not market_ids:
            return Response(
                {'error': 'market_ids parameter is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        queryset = self.get_queryset().filter(market_id__in=market_ids)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class UserAnalyticsViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for user analytics
    """
    serializer_class = UserAnalyticsSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Filter events based on user permissions"""
        queryset = UserAnalytics.objects.all()

        # If user is not admin, only show their own events
        if not self.request.user.is_staff:
            queryset = queryset.filter(user=self.request.user)

        return queryset
    
    @action(detail=False, methods=['get'])
    def top_customers(self, request):
        """Get top customers by spending"""
        limit = int(request.query_params.get('limit', 10))
        
        queryset = self.get_queryset().order_by('-total_spent')[:limit]
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def customer_segments(self, request):
        """Get customer segmentation data"""
        segments = self.get_queryset().values('customer_segment').annotate(
            count=Count('id'),
            avg_spent=Avg('total_spent'),
            avg_orders=Avg('total_orders')
        ).order_by('-count')
        
        return Response(segments)
    
    @action(detail=True, methods=['get'])
    def insights(self, request, pk=None):
        """Get detailed insights for a user"""
        user_analytics = self.get_object()
        
        # Get ML recommendations
        ml_service = MLService()
        recommendations = ml_service.get_user_recommendations(user_analytics.user)
        
        insights_data = {
            'user_id': user_analytics.user.id,
            'username': user_analytics.user.username,
            'total_sessions': user_analytics.total_sessions,
            'total_page_views': user_analytics.total_page_views,
            'avg_session_duration': user_analytics.avg_session_duration,
            'last_activity': user_analytics.last_activity,
            'total_orders': user_analytics.total_orders,
            'total_spent': user_analytics.total_spent,
            'avg_order_value': user_analytics.avg_order_value,
            'last_purchase': user_analytics.last_purchase,
            'preferred_categories': user_analytics.preferred_categories,
            'preferred_price_range': user_analytics.preferred_price_range,
            'shopping_patterns': user_analytics.shopping_patterns,
            'customer_segment': user_analytics.customer_segment,
            'churn_probability': user_analytics.churn_probability,
            'lifetime_value': user_analytics.lifetime_value,
            'recommended_products': recommendations.get('products', []),
            'recommended_categories': recommendations.get('categories', []),
            'recommended_markets': recommendations.get('markets', [])
        }
        
        serializer = UserBehaviorInsightsSerializer(insights_data)
        return Response(serializer.data)


class AnalyticsDashboardViewSet(viewsets.ViewSet):
    """
    ViewSet for analytics dashboard
    """
    permission_classes = [IsAuthenticated]
    serializer_class = AnalyticsDashboardSerializer
    
    def list(self, request):
        """Get dashboard overview data"""
        cache_key = f"analytics_dashboard_{request.user.id}"
        cached_data = cache.get(cache_key)
        
        if cached_data:
            return Response(cached_data)
        
        analytics_service = AnalyticsService()
        dashboard_data = analytics_service.get_dashboard_data(request.user)
        
        # Cache for 5 minutes
        cache.set(cache_key, dashboard_data, 300)
        
        serializer = AnalyticsDashboardSerializer(dashboard_data)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def real_time(self, request):
        """Get real-time metrics"""
        real_time_service = RealTimeAnalyticsService()
        real_time_data = real_time_service.get_real_time_metrics()
        
        serializer = RealTimeMetricsSerializer(real_time_data)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def time_series(self, request):
        """Get time series data"""
        days = int(request.query_params.get('days', 30))
        metric = request.query_params.get('metric', 'revenue')
        
        analytics_service = AnalyticsService()
        time_series_data = analytics_service.get_time_series_data(
            days=days, 
            metric=metric
        )
        
        return Response(time_series_data)
    
    @action(detail=False, methods=['get'])
    def top_performers(self, request):
        """Get top performing entities"""
        entity_type = request.query_params.get('type', 'products')
        limit = int(request.query_params.get('limit', 10))
        
        analytics_service = AnalyticsService()
        top_performers = analytics_service.get_top_performers(
            entity_type=entity_type,
            limit=limit
        )
        
        return Response(top_performers)
    
    @action(detail=False, methods=['get'])
    def conversion_funnel(self, request):
        """Get conversion funnel data"""
        days = int(request.query_params.get('days', 30))
        
        analytics_service = AnalyticsService()
        funnel_data = analytics_service.get_conversion_funnel(days=days)
        
        return Response(funnel_data)
    
    @action(detail=False, methods=['get'])
    def geographic_analysis(self, request):
        """Get geographic analysis"""
        days = int(request.query_params.get('days', 30))
        
        analytics_service = AnalyticsService()
        geo_data = analytics_service.get_geographic_analysis(days=days)
        
        return Response(geo_data)
    
    @action(detail=False, methods=['get'])
    def device_analysis(self, request):
        """Get device analysis"""
        days = int(request.query_params.get('days', 30))
        
        analytics_service = AnalyticsService()
        device_data = analytics_service.get_device_analysis(days=days)
        
        return Response(device_data)


class MLRecommendationsViewSet(viewsets.ViewSet):
    """
    ViewSet for ML recommendations
    """
    permission_classes = [IsAuthenticated]
    serializer_class = AnalyticsDashboardSerializer
    
    @action(detail=False, methods=['get'])
    def product_recommendations(self, request):
        """Get product recommendations for user"""
        user_id = request.user.id
        limit = int(request.query_params.get('limit', 10))
        
        ml_service = MLService()
        recommendations = ml_service.get_product_recommendations(
            user_id=user_id,
            limit=limit
        )
        
        return Response(recommendations)
    
    @action(detail=False, methods=['get'])
    def similar_products(self, request):
        """Get similar products"""
        product_id = request.query_params.get('product_id')
        limit = int(request.query_params.get('limit', 10))
        
        if not product_id:
            return Response(
                {'error': 'product_id parameter is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        ml_service = MLService()
        similar_products = ml_service.get_similar_products(
            product_id=int(product_id),
            limit=limit
        )
        
        return Response(similar_products)
    
    @action(detail=False, methods=['get'])
    def price_optimization(self, request):
        """Get price optimization suggestions"""
        product_id = request.query_params.get('product_id')
        
        if not product_id:
            return Response(
                {'error': 'product_id parameter is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        ml_service = MLService()
        price_suggestions = ml_service.get_price_optimization(
            product_id=int(product_id)
        )
        
        return Response(price_suggestions)
    
    @action(detail=False, methods=['get'])
    def demand_forecast(self, request):
        """Get demand forecast"""
        product_id = request.query_params.get('product_id')
        days = int(request.query_params.get('days', 30))
        
        if not product_id:
            return Response(
                {'error': 'product_id parameter is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        ml_service = MLService()
        forecast = ml_service.get_demand_forecast(
            product_id=int(product_id),
            days=days
        )
        
        return Response(forecast)
    
    @action(detail=False, methods=['get'])
    def customer_segmentation(self, request):
        """Get customer segmentation analysis"""
        ml_service = MLService()
        segmentation = ml_service.get_customer_segmentation()
        
        return Response(segmentation)
    
    @action(detail=False, methods=['get'])
    def fraud_detection(self, request):
        """Get fraud detection analysis"""
        days = int(request.query_params.get('days', 7))
        
        ml_service = MLService()
        fraud_analysis = ml_service.get_fraud_detection(days=days)
        
        return Response(fraud_analysis)

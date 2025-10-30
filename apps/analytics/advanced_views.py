"""
Advanced Analytics Views for ASOUD Platform
Sales, Revenue, and Business Intelligence Views
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django.utils import timezone
from datetime import timedelta
from django.core.cache import cache
import logging

from .advanced_analytics import SalesAnalytics, BusinessIntelligence
from .serializers import (
    AnalyticsDashboardSerializer, UserBehaviorInsightsSerializer,
    ProductPerformanceSerializer, MarketPerformanceSerializer
)

logger = logging.getLogger(__name__)


class SalesAnalyticsViewSet(viewsets.ViewSet):
    """
    ViewSet for sales analytics
    """
    permission_classes = [IsAuthenticated]
    serializer_class = None  # Custom responses
    
    def list(self, request):
        """Get sales overview"""
        try:
            days = int(request.query_params.get('days', 30))
            
            sales_analytics = SalesAnalytics()
            sales_overview = sales_analytics.get_sales_overview(days)
            
            return Response({
                'success': True,
                'data': sales_overview,
                'timestamp': timezone.now().isoformat()
            })
            
        except Exception as e:
            logger.error(f"Error getting sales overview: {e}")
            return Response({
                'success': False,
                'error': str(e),
                'timestamp': timezone.now().isoformat()
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['get'])
    def revenue_analytics(self, request):
        """Get detailed revenue analytics"""
        try:
            days = int(request.query_params.get('days', 30))
            
            sales_analytics = SalesAnalytics()
            revenue_analytics = sales_analytics.get_revenue_analytics(days)
            
            return Response({
                'success': True,
                'data': revenue_analytics,
                'timestamp': timezone.now().isoformat()
            })
            
        except Exception as e:
            logger.error(f"Error getting revenue analytics: {e}")
            return Response({
                'success': False,
                'error': str(e),
                'timestamp': timezone.now().isoformat()
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['get'])
    def customer_analytics(self, request):
        """Get customer analytics and segmentation"""
        try:
            days = int(request.query_params.get('days', 30))
            
            sales_analytics = SalesAnalytics()
            customer_analytics = sales_analytics.get_customer_analytics(days)
            
            return Response({
                'success': True,
                'data': customer_analytics,
                'timestamp': timezone.now().isoformat()
            })
            
        except Exception as e:
            logger.error(f"Error getting customer analytics: {e}")
            return Response({
                'success': False,
                'error': str(e),
                'timestamp': timezone.now().isoformat()
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['get'])
    def product_analytics(self, request):
        """Get product performance analytics"""
        try:
            days = int(request.query_params.get('days', 30))
            
            sales_analytics = SalesAnalytics()
            product_analytics = sales_analytics.get_product_analytics(days)
            
            return Response({
                'success': True,
                'data': product_analytics,
                'timestamp': timezone.now().isoformat()
            })
            
        except Exception as e:
            logger.error(f"Error getting product analytics: {e}")
            return Response({
                'success': False,
                'error': str(e),
                'timestamp': timezone.now().isoformat()
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['get'])
    def sales_trends(self, request):
        """Get sales trends analysis"""
        try:
            days = int(request.query_params.get('days', 30))
            trend_type = request.query_params.get('type', 'revenue')
            
            sales_analytics = SalesAnalytics()
            
            if trend_type == 'revenue':
                data = sales_analytics.get_revenue_analytics(days)
                trends = data.get('daily_revenue', [])
            elif trend_type == 'orders':
                data = sales_analytics.get_sales_overview(days)
                trends = data.get('daily_sales', [])
            else:
                return Response({
                    'success': False,
                    'error': 'Invalid trend type. Use "revenue" or "orders"',
                    'timestamp': timezone.now().isoformat()
                }, status=status.HTTP_400_BAD_REQUEST)
            
            return Response({
                'success': True,
                'data': trends,
                'trend_type': trend_type,
                'timestamp': timezone.now().isoformat()
            })
            
        except Exception as e:
            logger.error(f"Error getting sales trends: {e}")
            return Response({
                'success': False,
                'error': str(e),
                'timestamp': timezone.now().isoformat()
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['get'])
    def top_performers(self, request):
        """Get top performing entities"""
        try:
            days = int(request.query_params.get('days', 30))
            entity_type = request.query_params.get('type', 'products')
            limit = int(request.query_params.get('limit', 10))
            
            sales_analytics = SalesAnalytics()
            
            if entity_type == 'products':
                data = sales_analytics.get_product_analytics(days)
                performers = data.get('top_products', {})
            elif entity_type == 'customers':
                data = sales_analytics.get_sales_overview(days)
                performers = data.get('top_customers', {})
            else:
                return Response({
                    'success': False,
                    'error': 'Invalid entity type. Use "products" or "customers"',
                    'timestamp': timezone.now().isoformat()
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Limit results
            limited_performers = dict(list(performers.items())[:limit])
            
            return Response({
                'success': True,
                'data': limited_performers,
                'entity_type': entity_type,
                'limit': limit,
                'timestamp': timezone.now().isoformat()
            })
            
        except Exception as e:
            logger.error(f"Error getting top performers: {e}")
            return Response({
                'success': False,
                'error': str(e),
                'timestamp': timezone.now().isoformat()
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['get'])
    def sales_forecast(self, request):
        """Get sales forecast"""
        try:
            days = int(request.query_params.get('days', 30))
            forecast_days = int(request.query_params.get('forecast_days', 7))
            
            sales_analytics = SalesAnalytics()
            revenue_analytics = sales_analytics.get_revenue_analytics(days)
            
            forecast = revenue_analytics.get('forecast', [])
            
            # Limit forecast to requested days
            limited_forecast = forecast[:forecast_days]
            
            return Response({
                'success': True,
                'data': limited_forecast,
                'forecast_days': forecast_days,
                'timestamp': timezone.now().isoformat()
            })
            
        except Exception as e:
            logger.error(f"Error getting sales forecast: {e}")
            return Response({
                'success': False,
                'error': str(e),
                'timestamp': timezone.now().isoformat()
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['get'])
    def sales_distribution(self, request):
        """Get sales distribution analysis"""
        try:
            days = int(request.query_params.get('days', 30))
            distribution_type = request.query_params.get('type', 'hourly')
            
            sales_analytics = SalesAnalytics()
            sales_overview = sales_analytics.get_sales_overview(days)
            
            if distribution_type == 'hourly':
                distribution = sales_overview.get('sales_by_hour', [])
            elif distribution_type == 'daily':
                distribution = sales_overview.get('sales_by_day', [])
            else:
                return Response({
                    'success': False,
                    'error': 'Invalid distribution type. Use "hourly" or "daily"',
                    'timestamp': timezone.now().isoformat()
                }, status=status.HTTP_400_BAD_REQUEST)
            
            return Response({
                'success': True,
                'data': distribution,
                'distribution_type': distribution_type,
                'timestamp': timezone.now().isoformat()
            })
            
        except Exception as e:
            logger.error(f"Error getting sales distribution: {e}")
            return Response({
                'success': False,
                'error': str(e),
                'timestamp': timezone.now().isoformat()
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class BusinessIntelligenceViewSet(viewsets.ViewSet):
    """
    ViewSet for business intelligence and KPI analytics
    """
    permission_classes = [IsAuthenticated, IsAdminUser]
    serializer_class = None  # Custom responses
    
    def list(self, request):
        """Get KPI dashboard"""
        try:
            days = int(request.query_params.get('days', 30))
            
            bi = BusinessIntelligence()
            kpi_dashboard = bi.get_kpi_dashboard(days)
            
            return Response({
                'success': True,
                'data': kpi_dashboard,
                'timestamp': timezone.now().isoformat()
            })
            
        except Exception as e:
            logger.error(f"Error getting KPI dashboard: {e}")
            return Response({
                'success': False,
                'error': str(e),
                'timestamp': timezone.now().isoformat()
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['get'])
    def kpis(self, request):
        """Get key performance indicators"""
        try:
            days = int(request.query_params.get('days', 30))
            
            bi = BusinessIntelligence()
            kpi_dashboard = bi.get_kpi_dashboard(days)
            
            kpis = kpi_dashboard.get('kpis', {})
            
            return Response({
                'success': True,
                'data': kpis,
                'timestamp': timezone.now().isoformat()
            })
            
        except Exception as e:
            logger.error(f"Error getting KPIs: {e}")
            return Response({
                'success': False,
                'error': str(e),
                'timestamp': timezone.now().isoformat()
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['get'])
    def trends(self, request):
        """Get trend analysis"""
        try:
            days = int(request.query_params.get('days', 30))
            
            bi = BusinessIntelligence()
            kpi_dashboard = bi.get_kpi_dashboard(days)
            
            trends = kpi_dashboard.get('trends', {})
            
            return Response({
                'success': True,
                'data': trends,
                'timestamp': timezone.now().isoformat()
            })
            
        except Exception as e:
            logger.error(f"Error getting trends: {e}")
            return Response({
                'success': False,
                'error': str(e),
                'timestamp': timezone.now().isoformat()
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['get'])
    def insights(self, request):
        """Get business insights"""
        try:
            days = int(request.query_params.get('days', 30))
            priority = request.query_params.get('priority', 'all')
            
            bi = BusinessIntelligence()
            kpi_dashboard = bi.get_kpi_dashboard(days)
            
            insights = kpi_dashboard.get('insights', [])
            
            # Filter by priority if specified
            if priority != 'all':
                insights = [insight for insight in insights if insight.get('priority') == priority]
            
            return Response({
                'success': True,
                'data': insights,
                'priority': priority,
                'timestamp': timezone.now().isoformat()
            })
            
        except Exception as e:
            logger.error(f"Error getting insights: {e}")
            return Response({
                'success': False,
                'error': str(e),
                'timestamp': timezone.now().isoformat()
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['get'])
    def performance_summary(self, request):
        """Get performance summary"""
        try:
            days = int(request.query_params.get('days', 30))
            
            bi = BusinessIntelligence()
            kpi_dashboard = bi.get_kpi_dashboard(days)
            
            # Extract key metrics for summary
            kpis = kpi_dashboard.get('kpis', {})
            insights = kpi_dashboard.get('insights', [])
            
            summary = {
                'revenue': kpis.get('revenue', {}),
                'orders': kpis.get('orders', {}),
                'customers': kpis.get('customers', {}),
                'products': kpis.get('products', {}),
                'key_insights': [insight for insight in insights if insight.get('priority') == 'high'],
                'overall_status': self._calculate_overall_status(kpis)
            }
            
            return Response({
                'success': True,
                'data': summary,
                'timestamp': timezone.now().isoformat()
            })
            
        except Exception as e:
            logger.error(f"Error getting performance summary: {e}")
            return Response({
                'success': False,
                'error': str(e),
                'timestamp': timezone.now().isoformat()
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def _calculate_overall_status(self, kpis: dict) -> str:
        """Calculate overall performance status"""
        statuses = []
        
        for kpi_name, kpi_data in kpis.items():
            if isinstance(kpi_data, dict) and 'status' in kpi_data:
                statuses.append(kpi_data['status'])
        
        if not statuses:
            return 'unknown'
        
        if all(status == 'good' for status in statuses):
            return 'excellent'
        elif any(status == 'needs_attention' for status in statuses):
            return 'needs_attention'
        else:
            return 'good'


class AdvancedAnalyticsViewSet(viewsets.ViewSet):
    """
    ViewSet for advanced analytics features
    """
    permission_classes = [IsAuthenticated]
    serializer_class = None  # Custom responses
    
    @action(detail=False, methods=['get'])
    def cohort_analysis(self, request):
        """Get cohort analysis"""
        try:
            days = int(request.query_params.get('days', 90))
            cohort_type = request.query_params.get('type', 'monthly')
            
            # This is a simplified cohort analysis
            # In a real implementation, you would have more sophisticated cohort tracking
            
            sales_analytics = SalesAnalytics()
            customer_analytics = sales_analytics.get_customer_analytics(days)
            
            # Simulate cohort data
            cohorts = self._generate_cohort_data(customer_analytics, cohort_type)
            
            return Response({
                'success': True,
                'data': cohorts,
                'cohort_type': cohort_type,
                'timestamp': timezone.now().isoformat()
            })
            
        except Exception as e:
            logger.error(f"Error getting cohort analysis: {e}")
            return Response({
                'success': False,
                'error': str(e),
                'timestamp': timezone.now().isoformat()
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['get'])
    def funnel_analysis(self, request):
        """Get funnel analysis"""
        try:
            days = int(request.query_params.get('days', 30))
            
            # Get funnel data from analytics service
            from .services import AnalyticsService
            analytics_service = AnalyticsService()
            funnel_data = analytics_service.get_conversion_funnel(days)
            
            return Response({
                'success': True,
                'data': funnel_data,
                'timestamp': timezone.now().isoformat()
            })
            
        except Exception as e:
            logger.error(f"Error getting funnel analysis: {e}")
            return Response({
                'success': False,
                'error': str(e),
                'timestamp': timezone.now().isoformat()
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['get'])
    def retention_analysis(self, request):
        """Get customer retention analysis"""
        try:
            days = int(request.query_params.get('days', 90))
            
            sales_analytics = SalesAnalytics()
            customer_analytics = sales_analytics.get_customer_analytics(days)
            
            retention_data = {
                'retention_rate': customer_analytics.get('retention_rate', 0),
                'churn_rate': customer_analytics.get('churn_rate', 0),
                'customer_distribution': customer_analytics.get('customer_distribution', {}),
                'segments': customer_analytics.get('segments', {})
            }
            
            return Response({
                'success': True,
                'data': retention_data,
                'timestamp': timezone.now().isoformat()
            })
            
        except Exception as e:
            logger.error(f"Error getting retention analysis: {e}")
            return Response({
                'success': False,
                'error': str(e),
                'timestamp': timezone.now().isoformat()
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def _generate_cohort_data(self, customer_analytics: dict, cohort_type: str) -> dict:
        """Generate cohort analysis data"""
        # This is a simplified implementation
        # In a real scenario, you would analyze actual cohort data
        
        segments = customer_analytics.get('segments', {})
        
        cohorts = {
            'cohort_type': cohort_type,
            'total_customers': customer_analytics.get('total_customers', 0),
            'cohorts': []
        }
        
        # Simulate cohort data
        for i in range(6):  # 6 months of cohorts
            cohort = {
                'period': f"Month {i+1}",
                'customers': len(segments.get('new_customers', [])) // 6,
                'retention_rate': max(0, 100 - (i * 15)),  # Simulate decreasing retention
                'revenue': 1000 * (6 - i)  # Simulate decreasing revenue
            }
            cohorts['cohorts'].append(cohort)
        
        return cohorts

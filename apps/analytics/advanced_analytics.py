"""
Advanced Analytics for ASOUD Platform
Sales, Revenue, and Business Intelligence Analytics
"""

import logging
try:
    import numpy as np
    import pandas as pd
    HAS_ML_LIBS = True
except ImportError:
    HAS_ML_LIBS = False
    # Define dummy classes for when ML libraries are not available
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
        'linspace': lambda a, b, c: [a, b],
        'arange': lambda x: [0, 1],
        'polyfit': lambda x, y, z: [0, 0],
    })()
    
    pd = type('pandas', (), {
        'DataFrame': lambda x: x,
        'Series': lambda x: x,
        'to_datetime': lambda x: x,
    })()
from datetime import timedelta, datetime
from django.utils import timezone
from django.db.models import Count, Sum, Avg, Q, F, Max, Min
from django.core.cache import cache
from typing import List, Dict, Any, Optional, Tuple
import json

from .models import UserBehaviorEvent, UserSession, ItemAnalytics, UserAnalytics
from .services import AnalyticsService

logger = logging.getLogger(__name__)


class SalesAnalytics:
    """
    Advanced Sales Analytics
    """
    
    def __init__(self):
        self.cache_timeout = 1800  # 30 minutes
    
    def get_sales_overview(self, days: int = 30) -> Dict[str, Any]:
        """Get comprehensive sales overview"""
        cache_key = f"sales_overview_{days}"
        cached_data = cache.get(cache_key)
        
        if cached_data:
            return cached_data
        
        try:
            start_date = timezone.now() - timedelta(days=days)
            
            # Get sales data
            sales_data = UserBehaviorEvent.objects.filter(
                event_type='purchase',
                timestamp__gte=start_date
            ).values('timestamp', 'event_data__value', 'user_id', 'object_id')
            
            if not sales_data.exists():
                return self._empty_sales_overview()
            
            # Convert to DataFrame for analysis
            df = pd.DataFrame(list(sales_data))
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df['value'] = pd.to_numeric(df['event_data__value'], errors='coerce').fillna(0)
            df['date'] = df['timestamp'].dt.date
            
            # Calculate metrics
            total_revenue = df['value'].sum()
            total_orders = len(df)
            avg_order_value = df['value'].mean()
            unique_customers = df['user_id'].nunique()
            unique_products = df['object_id'].nunique()
            
            # Daily sales trend
            daily_sales = df.groupby('date').agg({
                'value': ['sum', 'count', 'mean'],
                'user_id': 'nunique'
            }).round(2)
            
            daily_sales.columns = ['revenue', 'orders', 'avg_order_value', 'unique_customers']
            daily_sales = daily_sales.reset_index()
            
            # Top products
            top_products = df.groupby('object_id').agg({
                'value': ['sum', 'count', 'mean']
            }).round(2)
            
            top_products.columns = ['revenue', 'orders', 'avg_order_value']
            top_products = top_products.sort_values('revenue', ascending=False).head(10)
            
            # Top customers
            top_customers = df.groupby('user_id').agg({
                'value': ['sum', 'count', 'mean']
            }).round(2)
            
            top_customers.columns = ['revenue', 'orders', 'avg_order_value']
            top_customers = top_customers.sort_values('revenue', ascending=False).head(10)
            
            # Sales by day of week
            df['day_of_week'] = df['timestamp'].dt.day_name()
            sales_by_day = df.groupby('day_of_week').agg({
                'value': ['sum', 'count']
            }).round(2)
            
            sales_by_day.columns = ['revenue', 'orders']
            sales_by_day = sales_by_day.reset_index()
            
            # Sales by hour
            df['hour'] = df['timestamp'].dt.hour
            sales_by_hour = df.groupby('hour').agg({
                'value': ['sum', 'count']
            }).round(2)
            
            sales_by_hour.columns = ['revenue', 'orders']
            sales_by_hour = sales_by_hour.reset_index()
            
            # Growth metrics
            if len(daily_sales) > 1:
                first_half = daily_sales[:len(daily_sales)//2]['revenue'].sum()
                second_half = daily_sales[len(daily_sales)//2:]['revenue'].sum()
                revenue_growth = ((second_half - first_half) / first_half * 100) if first_half > 0 else 0
            else:
                revenue_growth = 0
            
            # Customer acquisition cost (simplified)
            cac = total_revenue / unique_customers if unique_customers > 0 else 0
            
            # Customer lifetime value (simplified)
            clv = total_revenue / unique_customers if unique_customers > 0 else 0
            
            overview = {
                'total_revenue': float(total_revenue),
                'total_orders': int(total_orders),
                'avg_order_value': float(avg_order_value),
                'unique_customers': int(unique_customers),
                'unique_products': int(unique_products),
                'revenue_growth': float(revenue_growth),
                'customer_acquisition_cost': float(cac),
                'customer_lifetime_value': float(clv),
                'daily_sales': daily_sales.to_dict('records'),
                'top_products': top_products.to_dict('index'),
                'top_customers': top_customers.to_dict('index'),
                'sales_by_day': sales_by_day.to_dict('records'),
                'sales_by_hour': sales_by_hour.to_dict('records'),
                'period': f"{days} days",
                'generated_at': timezone.now().isoformat()
            }
            
            # Cache the data
            cache.set(cache_key, overview, self.cache_timeout)
            
            return overview
            
        except Exception as e:
            logger.error(f"Error generating sales overview: {e}")
            return self._empty_sales_overview()
    
    def get_revenue_analytics(self, days: int = 30) -> Dict[str, Any]:
        """Get detailed revenue analytics"""
        cache_key = f"revenue_analytics_{days}"
        cached_data = cache.get(cache_key)
        
        if cached_data:
            return cached_data
        
        try:
            start_date = timezone.now() - timedelta(days=days)
            
            # Get revenue data
            revenue_data = UserBehaviorEvent.objects.filter(
                event_type='purchase',
                timestamp__gte=start_date
            ).values('timestamp', 'event_data__value', 'user_id', 'object_id')
            
            if not revenue_data.exists():
                return self._empty_revenue_analytics()
            
            # Convert to DataFrame
            df = pd.DataFrame(list(revenue_data))
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df['value'] = pd.to_numeric(df['event_data__value'], errors='coerce').fillna(0)
            df['date'] = df['timestamp'].dt.date
            
            # Revenue trends
            daily_revenue = df.groupby('date')['value'].sum().reset_index()
            daily_revenue['cumulative_revenue'] = daily_revenue['value'].cumsum()
            daily_revenue['revenue_growth'] = daily_revenue['value'].pct_change().fillna(0) * 100
            
            # Revenue by product category (simplified)
            # In a real implementation, you would join with product categories
            revenue_by_product = df.groupby('object_id')['value'].sum().sort_values(ascending=False)
            
            # Revenue by customer segment
            revenue_by_customer = df.groupby('user_id')['value'].sum().sort_values(ascending=False)
            
            # Revenue distribution
            revenue_stats = {
                'min': float(revenue_by_customer.min()),
                'max': float(revenue_by_customer.max()),
                'mean': float(revenue_by_customer.mean()),
                'median': float(revenue_by_customer.median()),
                'std': float(revenue_by_customer.std())
            }
            
            # Revenue forecasting (simple linear trend)
            if len(daily_revenue) > 7:
                x = np.arange(len(daily_revenue))
                y = daily_revenue['value'].values
                z = np.polyfit(x, y, 1)
                trend_slope = z[0]
                trend_intercept = z[1]
                
                # Forecast next 7 days
                forecast_days = 7
                forecast_dates = []
                forecast_values = []
                
                for i in range(forecast_days):
                    future_date = (timezone.now() + timedelta(days=i+1)).date()
                    forecast_dates.append(future_date.isoformat())
                    forecast_value = trend_slope * (len(daily_revenue) + i) + trend_intercept
                    forecast_values.append(max(0, forecast_value))  # Ensure non-negative
                
                forecast = list(zip(forecast_dates, forecast_values))
            else:
                forecast = []
                trend_slope = 0
                trend_intercept = 0
            
            # Revenue concentration (Pareto analysis)
            total_revenue = revenue_by_customer.sum()
            revenue_by_customer_sorted = revenue_by_customer.sort_values(ascending=False)
            cumulative_revenue = revenue_by_customer_sorted.cumsum()
            pareto_80_percent = (cumulative_revenue <= total_revenue * 0.8).sum()
            pareto_80_revenue = cumulative_revenue.iloc[pareto_80_percent] if pareto_80_percent < len(cumulative_revenue) else total_revenue
            
            analytics = {
                'total_revenue': float(total_revenue),
                'daily_revenue': daily_revenue.to_dict('records'),
                'revenue_by_product': revenue_by_product.to_dict(),
                'revenue_by_customer': revenue_by_customer.to_dict(),
                'revenue_stats': revenue_stats,
                'trend_slope': float(trend_slope),
                'trend_intercept': float(trend_intercept),
                'forecast': forecast,
                'pareto_80_percent': int(pareto_80_percent),
                'pareto_80_revenue': float(pareto_80_revenue),
                'period': f"{days} days",
                'generated_at': timezone.now().isoformat()
            }
            
            # Cache the data
            cache.set(cache_key, analytics, self.cache_timeout)
            
            return analytics
            
        except Exception as e:
            logger.error(f"Error generating revenue analytics: {e}")
            return self._empty_revenue_analytics()
    
    def get_customer_analytics(self, days: int = 30) -> Dict[str, Any]:
        """Get customer analytics and segmentation"""
        cache_key = f"customer_analytics_{days}"
        cached_data = cache.get(cache_key)
        
        if cached_data:
            return cached_data
        
        try:
            start_date = timezone.now() - timedelta(days=days)
            
            # Get customer data
            customer_data = UserBehaviorEvent.objects.filter(
                event_type='purchase',
                timestamp__gte=start_date
            ).values('user_id', 'timestamp', 'event_data__value')
            
            if not customer_data.exists():
                return self._empty_customer_analytics()
            
            # Convert to DataFrame
            df = pd.DataFrame(list(customer_data))
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df['value'] = pd.to_numeric(df['event_data__value'], errors='coerce').fillna(0)
            
            # Customer metrics
            customer_metrics = df.groupby('user_id').agg({
                'value': ['sum', 'count', 'mean'],
                'timestamp': ['min', 'max']
            }).round(2)
            
            customer_metrics.columns = ['total_spent', 'total_orders', 'avg_order_value', 'first_purchase', 'last_purchase']
            customer_metrics['days_since_last_purchase'] = (timezone.now() - customer_metrics['last_purchase']).dt.days
            customer_metrics['days_since_first_purchase'] = (timezone.now() - customer_metrics['first_purchase']).dt.days
            
            # Customer segmentation
            segments = self._segment_customers(customer_metrics)
            
            # Customer lifetime value
            clv = customer_metrics['total_spent'].mean()
            
            # Customer acquisition cost (simplified)
            cac = customer_metrics['total_spent'].sum() / len(customer_metrics)
            
            # Customer retention rate
            total_customers = len(customer_metrics)
            returning_customers = len(customer_metrics[customer_metrics['total_orders'] > 1])
            retention_rate = (returning_customers / total_customers * 100) if total_customers > 0 else 0
            
            # Churn analysis
            churned_customers = len(customer_metrics[customer_metrics['days_since_last_purchase'] > 30])
            churn_rate = (churned_customers / total_customers * 100) if total_customers > 0 else 0
            
            # Customer distribution
            customer_distribution = {
                'high_value': len(segments['high_value']),
                'medium_value': len(segments['medium_value']),
                'low_value': len(segments['low_value']),
                'new_customers': len(segments['new_customers']),
                'churned_customers': len(segments['churned_customers'])
            }
            
            analytics = {
                'total_customers': int(total_customers),
                'returning_customers': int(returning_customers),
                'retention_rate': float(retention_rate),
                'churn_rate': float(churn_rate),
                'customer_lifetime_value': float(clv),
                'customer_acquisition_cost': float(cac),
                'customer_distribution': customer_distribution,
                'segments': segments,
                'period': f"{days} days",
                'generated_at': timezone.now().isoformat()
            }
            
            # Cache the data
            cache.set(cache_key, analytics, self.cache_timeout)
            
            return analytics
            
        except Exception as e:
            logger.error(f"Error generating customer analytics: {e}")
            return self._empty_customer_analytics()
    
    def get_product_analytics(self, days: int = 30) -> Dict[str, Any]:
        """Get product performance analytics"""
        cache_key = f"product_analytics_{days}"
        cached_data = cache.get(cache_key)
        
        if cached_data:
            return cached_data
        
        try:
            start_date = timezone.now() - timedelta(days=days)
            
            # Get product data
            product_data = UserBehaviorEvent.objects.filter(
                event_type='purchase',
                timestamp__gte=start_date
            ).values('object_id', 'timestamp', 'event_data__value', 'user_id')
            
            if not product_data.exists():
                return self._empty_product_analytics()
            
            # Convert to DataFrame
            df = pd.DataFrame(list(product_data))
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df['value'] = pd.to_numeric(df['event_data__value'], errors='coerce').fillna(0)
            
            # Product metrics
            product_metrics = df.groupby('object_id').agg({
                'value': ['sum', 'count', 'mean'],
                'user_id': 'nunique',
                'timestamp': ['min', 'max']
            }).round(2)
            
            product_metrics.columns = ['revenue', 'orders', 'avg_order_value', 'unique_customers', 'first_sale', 'last_sale']
            product_metrics['days_since_last_sale'] = (timezone.now() - product_metrics['last_sale']).dt.days
            
            # Product performance categories
            performance_categories = self._categorize_products(product_metrics)
            
            # Product trends
            daily_product_sales = df.groupby(['object_id', df['timestamp'].dt.date])['value'].sum().reset_index()
            daily_product_sales.columns = ['product_id', 'date', 'revenue']
            
            # Top performing products
            top_products = product_metrics.sort_values('revenue', ascending=False).head(10)
            
            # Product velocity
            product_velocity = product_metrics['orders'] / product_metrics['days_since_last_sale'].replace(0, 1)
            product_velocity = product_velocity.sort_values(ascending=False)
            
            analytics = {
                'total_products': len(product_metrics),
                'total_revenue': float(product_metrics['revenue'].sum()),
                'total_orders': int(product_metrics['orders'].sum()),
                'avg_order_value': float(product_metrics['avg_order_value'].mean()),
                'performance_categories': performance_categories,
                'top_products': top_products.to_dict('index'),
                'product_velocity': product_velocity.to_dict(),
                'daily_product_sales': daily_product_sales.to_dict('records'),
                'period': f"{days} days",
                'generated_at': timezone.now().isoformat()
            }
            
            # Cache the data
            cache.set(cache_key, analytics, self.cache_timeout)
            
            return analytics
            
        except Exception as e:
            logger.error(f"Error generating product analytics: {e}")
            return self._empty_product_analytics()
    
    def _segment_customers(self, customer_metrics: pd.DataFrame) -> Dict[str, List[int]]:
        """Segment customers based on their behavior"""
        segments = {
            'high_value': [],
            'medium_value': [],
            'low_value': [],
            'new_customers': [],
            'churned_customers': []
        }
        
        for customer_id, row in customer_metrics.iterrows():
            total_spent = row['total_spent']
            total_orders = row['total_orders']
            days_since_last_purchase = row['days_since_last_purchase']
            
            if days_since_last_purchase > 30:
                segments['churned_customers'].append(customer_id)
            elif total_orders == 1:
                segments['new_customers'].append(customer_id)
            elif total_spent > 1000:
                segments['high_value'].append(customer_id)
            elif total_spent > 100:
                segments['medium_value'].append(customer_id)
            else:
                segments['low_value'].append(customer_id)
        
        return segments
    
    def _categorize_products(self, product_metrics: pd.DataFrame) -> Dict[str, List[int]]:
        """Categorize products based on their performance"""
        categories = {
            'stars': [],
            'cash_cows': [],
            'question_marks': [],
            'dogs': []
        }
        
        for product_id, row in product_metrics.iterrows():
            revenue = row['revenue']
            orders = row['orders']
            days_since_last_sale = row['days_since_last_sale']
            
            # Simple categorization based on revenue and recency
            if revenue > 1000 and days_since_last_sale < 7:
                categories['stars'].append(product_id)
            elif revenue > 1000 and days_since_last_sale >= 7:
                categories['cash_cows'].append(product_id)
            elif revenue < 1000 and days_since_last_sale < 7:
                categories['question_marks'].append(product_id)
            else:
                categories['dogs'].append(product_id)
        
        return categories
    
    def _empty_sales_overview(self) -> Dict[str, Any]:
        """Return empty sales overview"""
        return {
            'total_revenue': 0.0,
            'total_orders': 0,
            'avg_order_value': 0.0,
            'unique_customers': 0,
            'unique_products': 0,
            'revenue_growth': 0.0,
            'customer_acquisition_cost': 0.0,
            'customer_lifetime_value': 0.0,
            'daily_sales': [],
            'top_products': {},
            'top_customers': {},
            'sales_by_day': [],
            'sales_by_hour': [],
            'period': '0 days',
            'generated_at': timezone.now().isoformat()
        }
    
    def _empty_revenue_analytics(self) -> Dict[str, Any]:
        """Return empty revenue analytics"""
        return {
            'total_revenue': 0.0,
            'daily_revenue': [],
            'revenue_by_product': {},
            'revenue_by_customer': {},
            'revenue_stats': {'min': 0, 'max': 0, 'mean': 0, 'median': 0, 'std': 0},
            'trend_slope': 0.0,
            'trend_intercept': 0.0,
            'forecast': [],
            'pareto_80_percent': 0,
            'pareto_80_revenue': 0.0,
            'period': '0 days',
            'generated_at': timezone.now().isoformat()
        }
    
    def _empty_customer_analytics(self) -> Dict[str, Any]:
        """Return empty customer analytics"""
        return {
            'total_customers': 0,
            'returning_customers': 0,
            'retention_rate': 0.0,
            'churn_rate': 0.0,
            'customer_lifetime_value': 0.0,
            'customer_acquisition_cost': 0.0,
            'customer_distribution': {'high_value': 0, 'medium_value': 0, 'low_value': 0, 'new_customers': 0, 'churned_customers': 0},
            'segments': {'high_value': [], 'medium_value': [], 'low_value': [], 'new_customers': [], 'churned_customers': []},
            'period': '0 days',
            'generated_at': timezone.now().isoformat()
        }
    
    def _empty_product_analytics(self) -> Dict[str, Any]:
        """Return empty product analytics"""
        return {
            'total_products': 0,
            'total_revenue': 0.0,
            'total_orders': 0,
            'avg_order_value': 0.0,
            'performance_categories': {'stars': [], 'cash_cows': [], 'question_marks': [], 'dogs': []},
            'top_products': {},
            'product_velocity': {},
            'daily_product_sales': [],
            'period': '0 days',
            'generated_at': timezone.now().isoformat()
        }


class BusinessIntelligence:
    """
    Business Intelligence and KPI Analytics
    """
    
    def __init__(self):
        self.cache_timeout = 3600  # 1 hour
    
    def get_kpi_dashboard(self, days: int = 30) -> Dict[str, Any]:
        """Get comprehensive KPI dashboard"""
        cache_key = f"kpi_dashboard_{days}"
        cached_data = cache.get(cache_key)
        
        if cached_data:
            return cached_data
        
        try:
            # Get sales analytics
            sales_analytics = SalesAnalytics()
            sales_overview = sales_analytics.get_sales_overview(days)
            revenue_analytics = sales_analytics.get_revenue_analytics(days)
            customer_analytics = sales_analytics.get_customer_analytics(days)
            product_analytics = sales_analytics.get_product_analytics(days)
            
            # Calculate KPIs
            kpis = self._calculate_kpis(sales_overview, revenue_analytics, customer_analytics, product_analytics)
            
            # Get trends
            trends = self._calculate_trends(sales_overview, revenue_analytics)
            
            # Get insights
            insights = self._generate_insights(sales_overview, revenue_analytics, customer_analytics, product_analytics)
            
            dashboard = {
                'kpis': kpis,
                'trends': trends,
                'insights': insights,
                'sales_overview': sales_overview,
                'revenue_analytics': revenue_analytics,
                'customer_analytics': customer_analytics,
                'product_analytics': product_analytics,
                'period': f"{days} days",
                'generated_at': timezone.now().isoformat()
            }
            
            # Cache the data
            cache.set(cache_key, dashboard, self.cache_timeout)
            
            return dashboard
            
        except Exception as e:
            logger.error(f"Error generating KPI dashboard: {e}")
            return self._empty_kpi_dashboard()
    
    def _calculate_kpis(self, sales_overview: Dict, revenue_analytics: Dict, customer_analytics: Dict, product_analytics: Dict) -> Dict[str, Any]:
        """Calculate key performance indicators"""
        return {
            'revenue': {
                'current': sales_overview['total_revenue'],
                'growth': sales_overview['revenue_growth'],
                'target': sales_overview['total_revenue'] * 1.2,  # 20% growth target
                'status': 'good' if sales_overview['revenue_growth'] > 0 else 'needs_attention'
            },
            'orders': {
                'current': sales_overview['total_orders'],
                'growth': 0,  # Calculate based on previous period
                'target': sales_overview['total_orders'] * 1.15,  # 15% growth target
                'status': 'good'
            },
            'customers': {
                'current': customer_analytics['total_customers'],
                'retention_rate': customer_analytics['retention_rate'],
                'churn_rate': customer_analytics['churn_rate'],
                'status': 'good' if customer_analytics['retention_rate'] > 70 else 'needs_attention'
            },
            'products': {
                'current': product_analytics['total_products'],
                'active_products': len([p for p in product_analytics['performance_categories']['stars'] + product_analytics['performance_categories']['cash_cows']]),
                'status': 'good'
            },
            'conversion': {
                'current': 0,  # Calculate from funnel data
                'target': 5.0,  # 5% conversion target
                'status': 'needs_attention'
            }
        }
    
    def _calculate_trends(self, sales_overview: Dict, revenue_analytics: Dict) -> Dict[str, Any]:
        """Calculate trend analysis"""
        return {
            'revenue_trend': {
                'direction': 'up' if revenue_analytics['trend_slope'] > 0 else 'down',
                'strength': abs(revenue_analytics['trend_slope']),
                'forecast': revenue_analytics['forecast']
            },
            'growth_trend': {
                'direction': 'up' if sales_overview['revenue_growth'] > 0 else 'down',
                'strength': abs(sales_overview['revenue_growth']),
                'period': sales_overview['period']
            }
        }
    
    def _generate_insights(self, sales_overview: Dict, revenue_analytics: Dict, customer_analytics: Dict, product_analytics: Dict) -> List[Dict[str, Any]]:
        """Generate business insights"""
        insights = []
        
        # Revenue insights
        if sales_overview['revenue_growth'] > 10:
            insights.append({
                'type': 'positive',
                'category': 'revenue',
                'title': 'Strong Revenue Growth',
                'description': f"Revenue has grown by {sales_overview['revenue_growth']:.1f}% over the period",
                'priority': 'high'
            })
        elif sales_overview['revenue_growth'] < -5:
            insights.append({
                'type': 'negative',
                'category': 'revenue',
                'title': 'Revenue Decline',
                'description': f"Revenue has declined by {abs(sales_overview['revenue_growth']):.1f}% over the period",
                'priority': 'high'
            })
        
        # Customer insights
        if customer_analytics['retention_rate'] > 80:
            insights.append({
                'type': 'positive',
                'category': 'customers',
                'title': 'High Customer Retention',
                'description': f"Customer retention rate is {customer_analytics['retention_rate']:.1f}%",
                'priority': 'medium'
            })
        elif customer_analytics['churn_rate'] > 20:
            insights.append({
                'type': 'negative',
                'category': 'customers',
                'title': 'High Customer Churn',
                'description': f"Customer churn rate is {customer_analytics['churn_rate']:.1f}%",
                'priority': 'high'
            })
        
        # Product insights
        stars_count = len(product_analytics['performance_categories']['stars'])
        if stars_count > 0:
            insights.append({
                'type': 'positive',
                'category': 'products',
                'title': 'Star Products Identified',
                'description': f"{stars_count} products are performing exceptionally well",
                'priority': 'medium'
            })
        
        dogs_count = len(product_analytics['performance_categories']['dogs'])
        if dogs_count > 0:
            insights.append({
                'type': 'negative',
                'category': 'products',
                'title': 'Underperforming Products',
                'description': f"{dogs_count} products may need attention or discontinuation",
                'priority': 'medium'
            })
        
        return insights
    
    def _empty_kpi_dashboard(self) -> Dict[str, Any]:
        """Return empty KPI dashboard"""
        return {
            'kpis': {},
            'trends': {},
            'insights': [],
            'sales_overview': {},
            'revenue_analytics': {},
            'customer_analytics': {},
            'product_analytics': {},
            'period': '0 days',
            'generated_at': timezone.now().isoformat()
        }

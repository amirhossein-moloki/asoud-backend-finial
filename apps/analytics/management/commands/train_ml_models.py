"""
Management command to train ML models
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
import logging

from apps.analytics.models import UserBehaviorEvent, UserSession, ProductAnalytics, UserAnalytics
from apps.analytics.ml_models import (
    CollaborativeFilteringModel, ContentBasedFilteringModel, PriceOptimizationModel,
    DemandForecastingModel, CustomerSegmentationModel, FraudDetectionModel
)

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Train machine learning models for analytics'

    def add_arguments(self, parser):
        parser.add_argument(
            '--model',
            type=str,
            choices=['collaborative', 'content', 'price', 'demand', 'segmentation', 'fraud', 'all'],
            default='all',
            help='ML model to train'
        )
        parser.add_argument(
            '--days',
            type=int,
            default=90,
            help='Number of days of historical data to use'
        )

    def handle(self, *args, **options):
        model_type = options['model']
        days = options['days']
        
        self.stdout.write(self.style.SUCCESS('Starting ML model training...'))
        
        if model_type in ['collaborative', 'all']:
            self.train_collaborative_filtering(days)
        
        if model_type in ['content', 'all']:
            self.train_content_based_filtering(days)
        
        if model_type in ['price', 'all']:
            self.train_price_optimization(days)
        
        if model_type in ['demand', 'all']:
            self.train_demand_forecasting(days)
        
        if model_type in ['segmentation', 'all']:
            self.train_customer_segmentation(days)
        
        if model_type in ['fraud', 'all']:
            self.train_fraud_detection(days)
        
        self.stdout.write(self.style.SUCCESS('ML model training completed!'))

    def train_collaborative_filtering(self, days):
        """Train collaborative filtering model"""
        self.stdout.write('Training collaborative filtering model...')
        
        try:
            # Get user behavior events
            start_date = timezone.now() - timedelta(days=days)
            events = UserBehaviorEvent.objects.filter(
                timestamp__gte=start_date,
                event_type__in=['purchase', 'add_to_cart', 'product_view']
            ).select_related('user')
            
            if not events.exists():
                self.stdout.write(self.style.WARNING('No events found for collaborative filtering'))
                return
            
            # Train model
            model = CollaborativeFilteringModel()
            model.fit(list(events))
            
            # Cache the model
            from django.core.cache import cache
            cache.set('collaborative_filtering_model', model, 3600)
            
            self.stdout.write(self.style.SUCCESS('Collaborative filtering model trained successfully'))
            
        except Exception as e:
            logger.error(f"Error training collaborative filtering model: {e}")
            self.stdout.write(self.style.ERROR(f'Error training collaborative filtering model: {e}'))

    def train_content_based_filtering(self, days):
        """Train content-based filtering model"""
        self.stdout.write('Training content-based filtering model...')
        
        try:
            # Get product data
            products = ProductAnalytics.objects.select_related('product__category').all()
            
            if not products.exists():
                self.stdout.write(self.style.WARNING('No products found for content-based filtering'))
                return
            
            # Prepare product data
            products_data = []
            for product in products:
                products_data.append({
                    'product_id': product.product.id,
                    'category_id': product.product.category.id if product.product.category else 0,
                    'price': float(product.product.price),
                    'rating': 4.0,  # Placeholder rating
                    'popularity_score': float(product.popularity_score)
                })
            
            # Train model
            model = ContentBasedFilteringModel()
            model.fit(products_data)
            
            # Cache the model
            from django.core.cache import cache
            cache.set('content_based_filtering_model', model, 3600)
            
            self.stdout.write(self.style.SUCCESS('Content-based filtering model trained successfully'))
            
        except Exception as e:
            logger.error(f"Error training content-based filtering model: {e}")
            self.stdout.write(self.style.ERROR(f'Error training content-based filtering model: {e}'))

    def train_price_optimization(self, days):
        """Train price optimization model"""
        self.stdout.write('Training price optimization model...')
        
        try:
            # Get historical price and demand data
            start_date = timezone.now() - timedelta(days=days)
            
            # This is a simplified implementation
            # In a real scenario, you would have historical price changes and demand data
            historical_data = []
            
            for product in ProductAnalytics.objects.select_related('product').all():
                # Simulate historical data
                for i in range(30):  # Last 30 days
                    date = start_date + timedelta(days=i)
                    
                    historical_data.append({
                        'price': float(product.product.price),
                        'category_id': product.product.category.id if product.product.category else 0,
                        'competitor_price': float(product.product.price) * (0.8 + 0.4 * (i % 10) / 10),
                        'demand_score': float(product.popularity_score) / 100,
                        'seasonality': 1.0 + 0.2 * np.sin(2 * np.pi * i / 365),
                        'promotion_active': i % 7 == 0,
                        'stock_level': 100 - i,
                        'demand': float(product.total_views) / 100
                    })
            
            if not historical_data:
                self.stdout.write(self.style.WARNING('No historical data found for price optimization'))
                return
            
            # Train model
            model = PriceOptimizationModel()
            model.fit(historical_data)
            
            # Cache the model
            from django.core.cache import cache
            cache.set('price_optimization_model', model, 3600)
            
            self.stdout.write(self.style.SUCCESS('Price optimization model trained successfully'))
            
        except Exception as e:
            logger.error(f"Error training price optimization model: {e}")
            self.stdout.write(self.style.ERROR(f'Error training price optimization model: {e}'))

    def train_demand_forecasting(self, days):
        """Train demand forecasting model"""
        self.stdout.write('Training demand forecasting model...')
        
        try:
            # Get time series data
            start_date = timezone.now() - timedelta(days=days)
            
            # Aggregate daily demand
            daily_demand = {}
            for i in range(days):
                date = start_date + timedelta(days=i)
                date_start = timezone.make_aware(datetime.combine(date.date(), datetime.min.time()))
                date_end = timezone.make_aware(datetime.combine(date.date(), datetime.max.time()))
                
                demand = UserBehaviorEvent.objects.filter(
                    event_type='purchase',
                    timestamp__range=[date_start, date_end]
                ).count()
                
                daily_demand[date.date().isoformat()] = demand
            
            # Prepare time series data
            time_series_data = [
                {'date': date, 'demand': demand}
                for date, demand in daily_demand.items()
            ]
            
            if not time_series_data:
                self.stdout.write(self.style.WARNING('No time series data found for demand forecasting'))
                return
            
            # Train model
            model = DemandForecastingModel()
            model.fit(time_series_data)
            
            # Cache the model
            from django.core.cache import cache
            cache.set('demand_forecasting_model', model, 3600)
            
            self.stdout.write(self.style.SUCCESS('Demand forecasting model trained successfully'))
            
        except Exception as e:
            logger.error(f"Error training demand forecasting model: {e}")
            self.stdout.write(self.style.ERROR(f'Error training demand forecasting model: {e}'))

    def train_customer_segmentation(self, days):
        """Train customer segmentation model"""
        self.stdout.write('Training customer segmentation model...')
        
        try:
            # Get customer data
            customers = UserAnalytics.objects.select_related('user').all()
            
            if not customers.exists():
                self.stdout.write(self.style.WARNING('No customer data found for segmentation'))
                return
            
            # Prepare customer data
            customer_data = []
            for customer in customers:
                customer_data.append({
                    'user_id': customer.user.id,
                    'total_spent': float(customer.total_spent),
                    'total_orders': customer.total_orders,
                    'avg_order_value': float(customer.avg_order_value),
                    'days_since_last_purchase': (timezone.now() - customer.last_purchase).days if customer.last_purchase else 365,
                    'total_sessions': customer.total_sessions,
                    'avg_session_duration': customer.avg_session_duration.total_seconds() / 3600 if customer.avg_session_duration else 0
                })
            
            # Train model
            model = CustomerSegmentationModel()
            model.fit(customer_data)
            
            # Cache the model
            from django.core.cache import cache
            cache.set('customer_segmentation_model', model, 3600)
            
            self.stdout.write(self.style.SUCCESS('Customer segmentation model trained successfully'))
            
        except Exception as e:
            logger.error(f"Error training customer segmentation model: {e}")
            self.stdout.write(self.style.ERROR(f'Error training customer segmentation model: {e}'))

    def train_fraud_detection(self, days):
        """Train fraud detection model"""
        self.stdout.write('Training fraud detection model...')
        
        try:
            # Get transaction data
            start_date = timezone.now() - timedelta(days=days)
            
            # Get purchase events
            purchases = UserBehaviorEvent.objects.filter(
                event_type='purchase',
                timestamp__gte=start_date
            ).select_related('user')
            
            if not purchases.exists():
                self.stdout.write(self.style.WARNING('No transaction data found for fraud detection'))
                return
            
            # Prepare transaction data
            transaction_data = []
            for purchase in purchases:
                # Get user statistics
                user_orders = UserBehaviorEvent.objects.filter(
                    user=purchase.user,
                    event_type='purchase'
                ).count()
                
                user_avg_value = UserBehaviorEvent.objects.filter(
                    user=purchase.user,
                    event_type='purchase'
                ).aggregate(
                    avg_value=Avg('event_data__value')
                )['avg_value'] or 0
                
                # Get IP and device frequency
                ip_frequency = UserBehaviorEvent.objects.filter(
                    ip_address=purchase.ip_address,
                    timestamp__gte=start_date
                ).count()
                
                device_frequency = UserBehaviorEvent.objects.filter(
                    device_type=purchase.device_type,
                    timestamp__gte=start_date
                ).count()
                
                transaction_data.append({
                    'amount': purchase.event_data.get('value', 0),
                    'hour_of_day': purchase.timestamp.hour,
                    'day_of_week': purchase.timestamp.weekday(),
                    'user_orders_count': user_orders,
                    'user_avg_order_value': float(user_avg_value),
                    'ip_frequency': ip_frequency,
                    'device_frequency': device_frequency
                })
            
            if not transaction_data:
                self.stdout.write(self.style.WARNING('No transaction data found for fraud detection'))
                return
            
            # Train model
            model = FraudDetectionModel()
            model.fit(transaction_data)
            
            # Cache the model
            from django.core.cache import cache
            cache.set('fraud_detection_model', model, 3600)
            
            self.stdout.write(self.style.SUCCESS('Fraud detection model trained successfully'))
            
        except Exception as e:
            logger.error(f"Error training fraud detection model: {e}")
            self.stdout.write(self.style.ERROR(f'Error training fraud detection model: {e}'))


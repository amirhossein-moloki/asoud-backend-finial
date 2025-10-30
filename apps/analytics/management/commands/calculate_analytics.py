"""
Management command to calculate analytics metrics
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from apps.analytics.models import ProductAnalytics, MarketAnalytics, UserAnalytics
from apps.analytics.services import MLService
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Calculate analytics metrics for all entities'

    def add_arguments(self, parser):
        parser.add_argument(
            '--entity',
            type=str,
            choices=['products', 'markets', 'users', 'all'],
            default='all',
            help='Entity type to calculate metrics for'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force recalculation even if recently calculated'
        )

    def handle(self, *args, **options):
        entity = options['entity']
        force = options['force']
        
        self.stdout.write(self.style.SUCCESS('Starting analytics calculation...'))
        
        if entity in ['products', 'all']:
            self.calculate_product_analytics(force)
        
        if entity in ['markets', 'all']:
            self.calculate_market_analytics(force)
        
        if entity in ['users', 'all']:
            self.calculate_user_analytics(force)
        
        if entity == 'all':
            self.update_ml_models()
        
        self.stdout.write(self.style.SUCCESS('Analytics calculation completed!'))

    def calculate_product_analytics(self, force=False):
        """Calculate product analytics metrics"""
        self.stdout.write('Calculating product analytics...')
        
        products = ProductAnalytics.objects.all()
        if not force:
            # Only calculate for products updated more than 1 hour ago
            from datetime import timedelta
            cutoff_time = timezone.now() - timedelta(hours=1)
            products = products.filter(updated_at__lt=cutoff_time)
        
        count = 0
        for product_analytics in products:
            try:
                product_analytics.calculate_metrics()
                count += 1
                if count % 100 == 0:
                    self.stdout.write(f'Processed {count} products...')
            except Exception as e:
                logger.error(f"Error calculating metrics for product {product_analytics.product.id}: {e}")
        
        self.stdout.write(self.style.SUCCESS(f'Calculated metrics for {count} products'))

    def calculate_market_analytics(self, force=False):
        """Calculate market analytics metrics"""
        self.stdout.write('Calculating market analytics...')
        
        markets = MarketAnalytics.objects.all()
        if not force:
            # Only calculate for markets updated more than 1 hour ago
            from datetime import timedelta
            cutoff_time = timezone.now() - timedelta(hours=1)
            markets = markets.filter(updated_at__lt=cutoff_time)
        
        count = 0
        for market_analytics in markets:
            try:
                market_analytics.calculate_metrics()
                count += 1
                if count % 50 == 0:
                    self.stdout.write(f'Processed {count} markets...')
            except Exception as e:
                logger.error(f"Error calculating metrics for market {market_analytics.market.id}: {e}")
        
        self.stdout.write(self.style.SUCCESS(f'Calculated metrics for {count} markets'))

    def calculate_user_analytics(self, force=False):
        """Calculate user analytics metrics"""
        self.stdout.write('Calculating user analytics...')
        
        users = UserAnalytics.objects.all()
        if not force:
            # Only calculate for users updated more than 1 hour ago
            from datetime import timedelta
            cutoff_time = timezone.now() - timedelta(hours=1)
            users = users.filter(updated_at__lt=cutoff_time)
        
        count = 0
        for user_analytics in users:
            try:
                user_analytics.calculate_metrics()
                count += 1
                if count % 100 == 0:
                    self.stdout.write(f'Processed {count} users...')
            except Exception as e:
                logger.error(f"Error calculating metrics for user {user_analytics.user.id}: {e}")
        
        self.stdout.write(self.style.SUCCESS(f'Calculated metrics for {count} users'))

    def update_ml_models(self):
        """Update ML models"""
        self.stdout.write('Updating ML models...')
        
        try:
            ml_service = MLService()
            
            # Update customer segmentation
            self.stdout.write('Updating customer segmentation...')
            ml_service.get_customer_segmentation()
            
            # Update fraud detection
            self.stdout.write('Updating fraud detection...')
            ml_service.get_fraud_detection()
            
            self.stdout.write(self.style.SUCCESS('ML models updated successfully'))
            
        except Exception as e:
            logger.error(f"Error updating ML models: {e}")
            self.stdout.write(self.style.ERROR(f'Error updating ML models: {e}'))


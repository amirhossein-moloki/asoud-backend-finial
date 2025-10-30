"""
Management command to update ML recommendations
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.utils import timezone
import logging

from apps.analytics.models import UserAnalytics, ProductAnalytics
from apps.analytics.services import MLService

User = get_user_model()
logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Update ML recommendations for all users'

    def add_arguments(self, parser):
        parser.add_argument(
            '--user-id',
            type=int,
            help='Update recommendations for specific user only'
        )
        parser.add_argument(
            '--batch-size',
            type=int,
            default=100,
            help='Batch size for processing users'
        )

    def handle(self, *args, **options):
        user_id = options.get('user_id')
        batch_size = options['batch_size']
        
        self.stdout.write(self.style.SUCCESS('Starting ML recommendations update...'))
        
        if user_id:
            self.update_user_recommendations(user_id)
        else:
            self.update_all_users_recommendations(batch_size)
        
        self.stdout.write(self.style.SUCCESS('ML recommendations update completed!'))

    def update_user_recommendations(self, user_id):
        """Update recommendations for a specific user"""
        try:
            user = User.objects.get(id=user_id)
            user_analytics = UserAnalytics.objects.get(user=user)
            
            self.stdout.write(f'Updating recommendations for user {user.username}...')
            
            # Get ML service
            ml_service = MLService()
            
            # Get product recommendations
            product_recommendations = ml_service.get_product_recommendations(user_id, 10)
            
            # Get category recommendations
            category_recommendations = ml_service._get_category_recommendations(user_id)
            
            # Get market recommendations
            market_recommendations = ml_service._get_market_recommendations(user_id)
            
            # Update user analytics
            user_analytics.preferred_categories = category_recommendations
            user_analytics.save()
            
            # Cache recommendations
            cache_key = f"user_recommendations_{user_id}"
            recommendations = {
                'products': product_recommendations,
                'categories': category_recommendations,
                'markets': market_recommendations,
                'updated_at': timezone.now().isoformat()
            }
            cache.set(cache_key, recommendations, 3600)  # Cache for 1 hour
            
            self.stdout.write(self.style.SUCCESS(f'Updated recommendations for user {user.username}'))
            
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'User with ID {user_id} not found'))
        except UserAnalytics.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'UserAnalytics for user {user_id} not found'))
        except Exception as e:
            logger.error(f"Error updating recommendations for user {user_id}: {e}")
            self.stdout.write(self.style.ERROR(f'Error updating recommendations: {e}'))

    def update_all_users_recommendations(self, batch_size):
        """Update recommendations for all users"""
        try:
            # Get all users with analytics
            users = User.objects.filter(analytics__isnull=False).select_related('analytics')
            total_users = users.count()
            
            self.stdout.write(f'Updating recommendations for {total_users} users...')
            
            # Process users in batches
            processed = 0
            for i in range(0, total_users, batch_size):
                batch_users = users[i:i + batch_size]
                
                for user in batch_users:
                    try:
                        self.update_user_recommendations(user.id)
                        processed += 1
                        
                        if processed % 10 == 0:
                            self.stdout.write(f'Processed {processed}/{total_users} users...')
                            
                    except Exception as e:
                        logger.error(f"Error updating recommendations for user {user.id}: {e}")
                        continue
                
                # Clear cache periodically
                if i % (batch_size * 5) == 0:
                    cache.clear()
            
            self.stdout.write(self.style.SUCCESS(f'Updated recommendations for {processed} users'))
            
        except Exception as e:
            logger.error(f"Error updating all users recommendations: {e}")
            self.stdout.write(self.style.ERROR(f'Error updating all users recommendations: {e}'))


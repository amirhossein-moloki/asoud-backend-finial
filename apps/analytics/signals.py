"""
Analytics Signals for ASOUD Platform
Automatic analytics tracking and ML model updates
"""

import logging
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone

from .models import UserBehaviorEvent, UserSession, ProductAnalytics, UserAnalytics
from .services import MLService

User = get_user_model()
logger = logging.getLogger(__name__)


@receiver(post_save, sender=User)
def create_user_analytics(sender, instance, created, **kwargs):
    """Create UserAnalytics when a new user is created"""
    if created:
        UserAnalytics.objects.get_or_create(user=instance)
        logger.info(f"Created UserAnalytics for user {instance.username}")


@receiver(post_save, sender='product.Product')
def create_product_analytics(sender, instance, created, **kwargs):
    """Create ProductAnalytics when a new product is created"""
    if created:
        ProductAnalytics.objects.get_or_create(product=instance)
        logger.info(f"Created ProductAnalytics for product {instance.name}")


@receiver(post_save, sender='market.Market')
def create_market_analytics(sender, instance, created, **kwargs):
    """Create MarketAnalytics when a new market is created"""
    if created:
        from .models import MarketAnalytics
        MarketAnalytics.objects.get_or_create(market=instance)
        logger.info(f"Created MarketAnalytics for market {instance.name}")


@receiver(post_save, sender=UserBehaviorEvent)
def update_analytics_on_event(sender, instance, created, **kwargs):
    """Update analytics when a new event is created"""
    if created:
        try:
            # Update product analytics if it's a product-related event
            if (instance.content_type and 
                instance.content_type.model == 'product' and 
                instance.object_id):
                
                try:
                    product_analytics = ProductAnalytics.objects.get(
                        product_id=instance.object_id
                    )
                    product_analytics.calculate_metrics()
                    logger.debug(f"Updated ProductAnalytics for product {instance.object_id}")
                except ProductAnalytics.DoesNotExist:
                    pass
            
            # Update user analytics
            if instance.user:
                try:
                    user_analytics = UserAnalytics.objects.get(user=instance.user)
                    user_analytics.calculate_metrics()
                    logger.debug(f"Updated UserAnalytics for user {instance.user.username}")
                except UserAnalytics.DoesNotExist:
                    pass
            
            # Update market analytics if it's a market-related event
            if (instance.content_type and 
                instance.content_type.model == 'market' and 
                instance.object_id):
                
                try:
                    from .models import MarketAnalytics
                    market_analytics = MarketAnalytics.objects.get(
                        market_id=instance.object_id
                    )
                    market_analytics.calculate_metrics()
                    logger.debug(f"Updated MarketAnalytics for market {instance.object_id}")
                except MarketAnalytics.DoesNotExist:
                    pass
                    
        except Exception as e:
            logger.error(f"Error updating analytics for event {instance.id}: {e}")


@receiver(post_save, sender=UserSession)
def update_analytics_on_session(sender, instance, created, **kwargs):
    """Update analytics when a session is created or updated"""
    if created:
        try:
            # Update user analytics
            if instance.user:
                try:
                    user_analytics = UserAnalytics.objects.get(user=instance.user)
                    user_analytics.calculate_metrics()
                    logger.debug(f"Updated UserAnalytics for user {instance.user.username}")
                except UserAnalytics.DoesNotExist:
                    pass
        except Exception as e:
            logger.error(f"Error updating analytics for session {instance.id}: {e}")


@receiver(post_save, sender='cart.Order')
def update_analytics_on_order(sender, instance, created, **kwargs):
    """Update analytics when an order is created or updated"""
    if created or instance.is_paid:
        try:
            # Update product analytics for all products in the order
            for order_item in instance.items.all():
                try:
                    product_analytics = ProductAnalytics.objects.get(
                        product=order_item.product
                    )
                    product_analytics.calculate_metrics()
                    logger.debug(f"Updated ProductAnalytics for product {order_item.product.id}")
                except ProductAnalytics.DoesNotExist:
                    pass
            
            # Update user analytics
            if instance.user:
                try:
                    user_analytics = UserAnalytics.objects.get(user=instance.user)
                    user_analytics.calculate_metrics()
                    logger.debug(f"Updated UserAnalytics for user {instance.user.username}")
                except UserAnalytics.DoesNotExist:
                    pass
                    
        except Exception as e:
            logger.error(f"Error updating analytics for order {instance.id}: {e}")


def track_user_behavior(user, session_id, event_type, content_object=None, **kwargs):
    """
    Helper function to track user behavior
    """
    try:
        # Get content type and object id if content_object is provided
        content_type = None
        object_id = None
        
        if content_object:
            content_type = ContentType.objects.get_for_model(content_object)
            object_id = content_object.id
        
        # Create the event
        event = UserBehaviorEvent.objects.create(
            user=user,
            session_id=session_id,
            event_type=event_type,
            content_type=content_type,
            object_id=object_id,
            event_data=kwargs.get('event_data', {}),
            page_url=kwargs.get('page_url'),
            referrer_url=kwargs.get('referrer_url'),
            user_agent=kwargs.get('user_agent'),
            ip_address=kwargs.get('ip_address'),
            device_type=kwargs.get('device_type'),
            browser=kwargs.get('browser'),
            os=kwargs.get('os'),
            country=kwargs.get('country'),
            city=kwargs.get('city'),
            latitude=kwargs.get('latitude'),
            longitude=kwargs.get('longitude')
        )
        
        logger.debug(f"Tracked event {event_type} for user {user.username if user else 'Anonymous'}")
        return event
        
    except Exception as e:
        logger.error(f"Error tracking user behavior: {e}")
        return None


def update_ml_models():
    """
    Update ML models periodically
    """
    try:
        ml_service = MLService()
        
        # Update customer segmentation
        ml_service.get_customer_segmentation()
        
        # Update fraud detection
        ml_service.get_fraud_detection()
        
        logger.info("ML models updated successfully")
        
    except Exception as e:
        logger.error(f"Error updating ML models: {e}")

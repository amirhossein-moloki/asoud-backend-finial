import logging
from datetime import date, timedelta
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings

try:
    from celery import shared_task
except ImportError:
    # Celery not available, define a dummy decorator
    def shared_task(func):
        return func

from .models import MarketSubscription
from .services import SubscriptionService

logger = logging.getLogger(__name__)


@shared_task
def check_expired_subscriptions():
    """
    Check for expired subscriptions and update their status.
    This task should be run daily via cron or Celery beat.
    """
    logger.info("Starting expired subscription check...")
    
    # Get all active subscriptions that have expired
    expired_subscriptions = MarketSubscription.objects.filter(
        status='active',
        end_date__lt=date.today()
    )
    
    if not expired_subscriptions.exists():
        logger.info("No expired subscriptions found.")
        return {"status": "success", "expired_count": 0, "renewed_count": 0}
    
    expired_count = expired_subscriptions.count()
    renewed_count = 0
    
    logger.info(f"Found {expired_count} expired subscription(s).")
    
    service = SubscriptionService()
    
    for subscription in expired_subscriptions:
        try:
            if subscription.auto_renew:
                # Try to auto-renew
                new_subscription = service.renew_subscription(subscription.id)
                if new_subscription:
                    renewed_count += 1
                    logger.info(f"Auto-renewed subscription for market: {subscription.market.title}")
                else:
                    # Mark as expired if renewal failed
                    subscription.status = 'expired'
                    subscription.save()
                    logger.warning(f"Failed to auto-renew subscription for market: {subscription.market.title}")
            else:
                # Mark as expired
                subscription.status = 'expired'
                subscription.save()
                logger.info(f"Marked subscription as expired for market: {subscription.market.title}")
                
        except Exception as e:
            logger.error(f"Error processing subscription {subscription.id}: {str(e)}")
            # Mark as expired on error
            subscription.status = 'expired'
            subscription.save()
    
    logger.info(f"Expired subscription check completed. Renewed: {renewed_count}, Expired: {expired_count - renewed_count}")
    
    return {
        "status": "success",
        "expired_count": expired_count,
        "renewed_count": renewed_count
    }


@shared_task
def send_subscription_expiry_notifications():
    """
    Send notifications to market owners about upcoming subscription expiry.
    This task should be run daily to notify users 7, 3, and 1 days before expiry.
    """
    logger.info("Starting subscription expiry notifications...")
    
    today = date.today()
    notification_days = [7, 3, 1]  # Days before expiry to send notifications
    
    notifications_sent = 0
    
    for days in notification_days:
        expiry_date = today + timedelta(days=days)
        
        # Get active subscriptions expiring on this date
        expiring_subscriptions = MarketSubscription.objects.filter(
            status='active',
            end_date=expiry_date
        ).select_related('market', 'market__owner')
        
        for subscription in expiring_subscriptions:
            try:
                market = subscription.market
                owner = market.owner
                
                if owner and owner.email:
                    subject = f"Your {market.title} subscription expires in {days} day{'s' if days > 1 else ''}"
                    message = f"""
                    Dear {owner.get_full_name() or owner.username},
                    
                    Your subscription for "{market.title}" will expire in {days} day{'s' if days > 1 else ''} on {subscription.end_date}.
                    
                    Plan: {subscription.get_plan_type_display()}
                    Amount: ${subscription.amount}
                    
                    To avoid service interruption, please renew your subscription before the expiry date.
                    
                    Best regards,
                    The Asoud Team
                    """
                    
                    send_mail(
                        subject=subject,
                        message=message,
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        recipient_list=[owner.email],
                        fail_silently=False,
                    )
                    
                    notifications_sent += 1
                    logger.info(f"Sent expiry notification to {owner.email} for market: {market.title}")
                    
            except Exception as e:
                logger.error(f"Error sending notification for subscription {subscription.id}: {str(e)}")
    
    logger.info(f"Subscription expiry notifications completed. Sent: {notifications_sent}")
    
    return {
        "status": "success",
        "notifications_sent": notifications_sent
    }


@shared_task
def generate_subscription_reports():
    """
    Generate monthly subscription reports and statistics.
    This task should be run monthly.
    """
    logger.info("Starting subscription report generation...")
    
    today = date.today()
    first_day_of_month = today.replace(day=1)
    
    # Get subscription statistics for the current month
    monthly_subscriptions = MarketSubscription.objects.filter(
        start_date__gte=first_day_of_month,
        start_date__lt=today
    )
    
    stats = {
        'total_new_subscriptions': monthly_subscriptions.count(),
        'monthly_revenue': sum(sub.amount for sub in monthly_subscriptions),
        'plan_breakdown': {},
        'active_subscriptions': MarketSubscription.objects.filter(status='active').count(),
        'expired_subscriptions': MarketSubscription.objects.filter(
            status='expired',
            end_date__gte=first_day_of_month,
            end_date__lt=today
        ).count(),
    }
    
    # Plan breakdown
    for plan_choice in MarketSubscription.PLAN_CHOICES:
        plan_type = plan_choice[0]
        plan_count = monthly_subscriptions.filter(plan_type=plan_type).count()
        plan_revenue = sum(
            sub.amount for sub in monthly_subscriptions.filter(plan_type=plan_type)
        )
        stats['plan_breakdown'][plan_type] = {
            'count': plan_count,
            'revenue': plan_revenue
        }
    
    logger.info(f"Monthly subscription report generated: {stats}")
    
    # Here you could save the report to database, send to admin email, etc.
    
    return {
        "status": "success",
        "report_date": today.isoformat(),
        "statistics": stats
    }


@shared_task
def cleanup_cancelled_subscriptions():
    """
    Clean up old cancelled subscriptions (older than 1 year).
    This task should be run monthly.
    """
    logger.info("Starting cancelled subscription cleanup...")
    
    one_year_ago = date.today() - timedelta(days=365)
    
    old_cancelled_subscriptions = MarketSubscription.objects.filter(
        status='cancelled',
        updated_at__lt=one_year_ago
    )
    
    deleted_count = old_cancelled_subscriptions.count()
    
    if deleted_count > 0:
        old_cancelled_subscriptions.delete()
        logger.info(f"Cleaned up {deleted_count} old cancelled subscriptions")
    else:
        logger.info("No old cancelled subscriptions to clean up")
    
    return {
        "status": "success",
        "deleted_count": deleted_count
    }
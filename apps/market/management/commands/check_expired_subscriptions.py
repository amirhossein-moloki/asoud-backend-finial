from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import date
from apps.market.models import MarketSubscription
from apps.market.services import SubscriptionService


class Command(BaseCommand):
    help = 'Check for expired subscriptions and update their status'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be done without making changes',
        )
        parser.add_argument(
            '--auto-renew',
            action='store_true',
            help='Automatically renew subscriptions with auto_renew enabled',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        auto_renew = options['auto_renew']
        
        self.stdout.write(
            self.style.SUCCESS('Checking for expired subscriptions...')
        )
        
        # Get all active subscriptions that have expired
        expired_subscriptions = MarketSubscription.objects.filter(
            status='active',
            end_date__lt=date.today()
        )
        
        if not expired_subscriptions.exists():
            self.stdout.write(
                self.style.SUCCESS('No expired subscriptions found.')
            )
            return
        
        expired_count = expired_subscriptions.count()
        self.stdout.write(
            f'Found {expired_count} expired subscription(s).'
        )
        
        renewed_count = 0
        expired_updated_count = 0
        
        for subscription in expired_subscriptions:
            market_title = subscription.market.title
            plan_type = subscription.get_plan_type_display()
            
            if auto_renew and subscription.auto_renew:
                # Try to auto-renew
                if not dry_run:
                    try:
                        service = SubscriptionService()
                        new_subscription = service.renew_subscription(subscription.id)
                        if new_subscription:
                            renewed_count += 1
                            self.stdout.write(
                                self.style.SUCCESS(
                                    f'Auto-renewed {plan_type} subscription for "{market_title}"'
                                )
                            )
                        else:
                            # Mark as expired if renewal failed
                            subscription.status = 'expired'
                            subscription.save()
                            expired_updated_count += 1
                            self.stdout.write(
                                self.style.WARNING(
                                    f'Failed to auto-renew {plan_type} subscription for "{market_title}" - marked as expired'
                                )
                            )
                    except Exception as e:
                        self.stdout.write(
                            self.style.ERROR(
                                f'Error renewing subscription for "{market_title}": {str(e)}'
                            )
                        )
                        # Mark as expired on error
                        subscription.status = 'expired'
                        subscription.save()
                        expired_updated_count += 1
                else:
                    self.stdout.write(
                        f'Would auto-renew {plan_type} subscription for "{market_title}"'
                    )
            else:
                # Mark as expired
                if not dry_run:
                    subscription.status = 'expired'
                    subscription.save()
                    expired_updated_count += 1
                    
                self.stdout.write(
                    self.style.WARNING(
                        f'{"Would mark" if dry_run else "Marked"} {plan_type} subscription for "{market_title}" as expired'
                    )
                )
        
        # Summary
        if not dry_run:
            self.stdout.write(
                self.style.SUCCESS(
                    f'\nSummary:\n'
                    f'- Renewed: {renewed_count} subscription(s)\n'
                    f'- Expired: {expired_updated_count} subscription(s)'
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f'\nDry run completed. Found {expired_count} expired subscription(s).'
                )
            )
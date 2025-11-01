from decimal import Decimal
from datetime import timedelta
from django.conf import settings
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from .models import Market, MarketSubscription


class SubscriptionService:
    """Service class for handling subscription operations"""
    
    @staticmethod
    def get_subscription_plans():
        """Get all available subscription plans with pricing"""
        return settings.SUBSCRIPTION_PLANS
    
    @staticmethod
    def get_plan_details(plan_type):
        """Get details for a specific subscription plan"""
        plans = settings.SUBSCRIPTION_PLANS
        return plans.get(plan_type)
    
    @staticmethod
    def calculate_subscription_price(plan_type, discount_code=None):
        """Calculate subscription price with optional discount"""
        plan = SubscriptionService.get_plan_details(plan_type)
        if not plan:
            raise ValueError(_("Invalid subscription plan"))
        
        base_price = Decimal(str(plan['price']))
        
        # Apply discount if provided
        if discount_code:
            # Here you can implement discount logic
            # For now, we'll just return the base price
            pass
        
        return base_price
    
    @staticmethod
    def create_subscription(market, plan_type, payment_reference=None):
        """Create a new subscription for a market"""
        plan = SubscriptionService.get_plan_details(plan_type)
        if not plan:
            raise ValueError(_("Invalid subscription plan"))
        
        # Calculate dates
        start_date = timezone.now()
        end_date = start_date + timedelta(days=plan['duration_days'])
        
        # Calculate price
        amount = SubscriptionService.calculate_subscription_price(plan_type)
        
        # Create subscription
        subscription = MarketSubscription.objects.create(
            market=market,
            plan_type=plan_type,
            status=MarketSubscription.PENDING,
            amount=amount,
            start_date=start_date,
            end_date=end_date,
            payment_reference=payment_reference
        )
        
        return subscription
    
    @staticmethod
    def activate_subscription(subscription):
        """Activate a subscription after successful payment"""
        subscription.status = MarketSubscription.ACTIVE
        subscription.save()
        
        # Update market subscription dates
        market = subscription.market
        market.is_paid = True
        market.subscription_start_date = subscription.start_date
        market.subscription_end_date = subscription.end_date
        
        # Transition market status if needed
        if market.status == Market.UNPAID_UNDER_CREATION:
            market.transition_status(
                Market.PAID_UNDER_CREATION,
                reason="Subscription activated"
            )
        
        market.save()
        return subscription
    
    @staticmethod
    def renew_subscription(subscription, new_plan_type=None):
        """Renew an existing subscription"""
        plan_type = new_plan_type or subscription.plan_type
        plan = SubscriptionService.get_plan_details(plan_type)
        
        if not plan:
            raise ValueError(_("Invalid subscription plan"))
        
        # Calculate new dates from current end date or now (whichever is later)
        start_date = max(subscription.end_date, timezone.now())
        end_date = start_date + timedelta(days=plan['duration_days'])
        
        # Calculate price
        amount = SubscriptionService.calculate_subscription_price(plan_type)
        
        # Create new subscription
        new_subscription = MarketSubscription.objects.create(
            market=subscription.market,
            plan_type=plan_type,
            status=MarketSubscription.PENDING,
            amount=amount,
            start_date=start_date,
            end_date=end_date
        )
        
        return new_subscription
    
    @staticmethod
    def cancel_subscription(subscription, reason=None):
        """Cancel an active subscription"""
        subscription.status = MarketSubscription.CANCELLED
        subscription.save()
        
        # Update market status
        market = subscription.market
        market.is_paid = False
        
        # Transition to unpaid status if currently paid
        if market.status in [Market.PAID_UNDER_CREATION, Market.PUBLISHED]:
            market.transition_status(
                Market.UNPAID_UNDER_CREATION,
                reason=reason or "Subscription cancelled"
            )
        
        market.save()
        return subscription
    
    @staticmethod
    def check_expired_subscriptions():
        """Check and update expired subscriptions"""
        now = timezone.now()
        expired_subscriptions = MarketSubscription.objects.filter(
            status=MarketSubscription.ACTIVE,
            end_date__lt=now
        )
        
        for subscription in expired_subscriptions:
            subscription.status = MarketSubscription.EXPIRED
            subscription.save()
            
            # Update market status
            market = subscription.market
            market.is_paid = False
            
            if market.status == Market.PUBLISHED:
                market.transition_status(
                    Market.UNPAID_UNDER_CREATION,
                    reason="Subscription expired"
                )
            
            market.save()
        
        return expired_subscriptions.count()
    
    @staticmethod
    def get_market_active_subscription(market):
        """Get the active subscription for a market"""
        return MarketSubscription.objects.filter(
            market=market,
            status=MarketSubscription.ACTIVE
        ).first()
    
    @staticmethod
    def is_market_subscription_active(market):
        """Check if market has an active subscription"""
        subscription = SubscriptionService.get_market_active_subscription(market)
        return subscription and subscription.is_active()


class PaymentService:
    """Service class for handling payment operations"""
    
    @staticmethod
    def get_available_gateways():
        """Get all available payment gateways"""
        return settings.PAYMENT_GATEWAYS
    
    @staticmethod
    def create_payment_request(subscription, gateway='zarinpal'):
        """Create a payment request for a subscription"""
        gateway_config = settings.PAYMENT_GATEWAYS.get(gateway)
        if not gateway_config:
            raise ValueError(_("Invalid payment gateway"))
        
        # Here you would integrate with the actual payment gateway
        # For now, we'll return a mock payment URL
        payment_data = {
            'gateway': gateway,
            'amount': float(subscription.amount),
            'subscription_id': subscription.id,
            'payment_url': f"https://payment.{gateway}.com/pay/{subscription.id}",
            'reference_id': f"SUB_{subscription.id}_{timezone.now().timestamp()}"
        }
        
        # Update subscription with payment reference
        subscription.payment_reference = payment_data['reference_id']
        subscription.save()
        
        return payment_data
    
    @staticmethod
    def verify_payment(payment_reference, gateway='zarinpal'):
        """Verify a payment with the gateway"""
        # Here you would verify the payment with the actual gateway
        # For now, we'll return a mock verification
        return {
            'success': True,
            'transaction_id': f"TXN_{payment_reference}",
            'amount': 0,  # This would come from the gateway
            'status': 'completed'
        }
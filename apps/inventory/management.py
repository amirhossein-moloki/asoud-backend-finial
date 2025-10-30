"""
Advanced Inventory Management System for ASOUD Platform
"""

import logging
from decimal import Decimal
from django.db import transaction
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.db.models import F, Q, Sum, Count
from django.core.cache import cache
from celery import shared_task
from apps.product.models import Product
from apps.cart.models import Order, OrderItem
from apps.notification.models import Notification
from apps.core.performance import CacheManager

logger = logging.getLogger(__name__)

class InventoryManager:
    """
    Comprehensive inventory management system
    """
    
    def __init__(self):
        self.cache_manager = CacheManager()
    
    def check_stock_availability(self, product_id, quantity):
        """Check if product has sufficient stock"""
        try:
            product = Product.objects.select_for_update().get(id=product_id)
            
            if product.stock >= quantity:
                return True, product.stock
            else:
                return False, product.stock
                
        except Product.DoesNotExist:
            return False, 0
        except Exception as e:
            logger.error(f"Error checking stock availability: {e}")
            return False, 0
    
    def reserve_stock(self, product_id, quantity, order_id=None):
        """Reserve stock for an order"""
        with transaction.atomic():
            try:
                product = Product.objects.select_for_update().get(id=product_id)
                
                if product.stock < quantity:
                    raise ValidationError(f"Insufficient stock. Available: {product.stock}, Required: {quantity}")
                
                # Reserve stock
                product.stock = F('stock') - quantity
                product.reserved_stock = F('reserved_stock') + quantity
                product.save()
                
                # Log reservation
                self.log_inventory_action(
                    product_id=product_id,
                    action='reserve',
                    quantity=quantity,
                    order_id=order_id,
                    remaining_stock=product.stock - quantity
                )
                
                # Check for low stock alert
                self.check_low_stock_alert(product)
                
                return True, product.stock - quantity
                
            except Product.DoesNotExist:
                raise ValidationError("Product not found")
            except Exception as e:
                logger.error(f"Error reserving stock: {e}")
                raise ValidationError("Failed to reserve stock")
    
    def release_stock(self, product_id, quantity, order_id=None):
        """Release reserved stock"""
        with transaction.atomic():
            try:
                product = Product.objects.select_for_update().get(id=product_id)
                
                # Release stock
                product.stock = F('stock') + quantity
                product.reserved_stock = F('reserved_stock') - quantity
                product.save()
                
                # Log release
                self.log_inventory_action(
                    product_id=product_id,
                    action='release',
                    quantity=quantity,
                    order_id=order_id,
                    remaining_stock=product.stock + quantity
                )
                
                return True, product.stock + quantity
                
            except Product.DoesNotExist:
                raise ValidationError("Product not found")
            except Exception as e:
                logger.error(f"Error releasing stock: {e}")
                raise ValidationError("Failed to release stock")
    
    def confirm_stock_reduction(self, product_id, quantity, order_id=None):
        """Confirm stock reduction after successful payment"""
        with transaction.atomic():
            try:
                product = Product.objects.select_for_update().get(id=product_id)
                
                # Reduce reserved stock
                product.reserved_stock = F('reserved_stock') - quantity
                product.save()
                
                # Log confirmation
                self.log_inventory_action(
                    product_id=product_id,
                    action='confirm',
                    quantity=quantity,
                    order_id=order_id,
                    remaining_stock=product.stock
                )
                
                # Check for low stock alert
                self.check_low_stock_alert(product)
                
                return True, product.stock
                
            except Product.DoesNotExist:
                raise ValidationError("Product not found")
            except Exception as e:
                logger.error(f"Error confirming stock reduction: {e}")
                raise ValidationError("Failed to confirm stock reduction")
    
    def add_stock(self, product_id, quantity, reason="manual_addition"):
        """Add stock to product"""
        with transaction.atomic():
            try:
                product = Product.objects.select_for_update().get(id=product_id)
                
                # Add stock
                product.stock = F('stock') + quantity
                product.save()
                
                # Log addition
                self.log_inventory_action(
                    product_id=product_id,
                    action='add',
                    quantity=quantity,
                    reason=reason,
                    remaining_stock=product.stock + quantity
                )
                
                return True, product.stock + quantity
                
            except Product.DoesNotExist:
                raise ValidationError("Product not found")
            except Exception as e:
                logger.error(f"Error adding stock: {e}")
                raise ValidationError("Failed to add stock")
    
    def check_low_stock_alert(self, product):
        """Check if product needs low stock alert"""
        low_stock_threshold = getattr(product, 'low_stock_threshold', 10)
        
        if product.stock <= low_stock_threshold:
            self.send_low_stock_alert(product)
    
    def send_low_stock_alert(self, product):
        """Send low stock alert to product owner"""
        try:
            # Create notification
            Notification.objects.create(
                user=product.market.owner,
                title="Low Stock Alert",
                message=f"Product '{product.name}' is running low on stock. Current stock: {product.stock}",
                type="inventory",
                data={
                    'product_id': str(product.id),
                    'product_name': product.name,
                    'current_stock': product.stock,
                    'low_stock_threshold': getattr(product, 'low_stock_threshold', 10)
                }
            )
            
            logger.info(f"Low stock alert sent for product {product.id}")
            
        except Exception as e:
            logger.error(f"Error sending low stock alert: {e}")
    
    def log_inventory_action(self, product_id, action, quantity, order_id=None, reason=None, remaining_stock=None):
        """Log inventory action"""
        try:
            from apps.inventory.models import InventoryLog
            
            InventoryLog.objects.create(
                product_id=product_id,
                action=action,
                quantity=quantity,
                order_id=order_id,
                reason=reason,
                remaining_stock=remaining_stock
            )
            
        except Exception as e:
            logger.error(f"Error logging inventory action: {e}")
    
    def get_inventory_summary(self, market_id=None):
        """Get inventory summary"""
        try:
            queryset = Product.objects.all()
            
            if market_id:
                queryset = queryset.filter(market_id=market_id)
            
            summary = queryset.aggregate(
                total_products=Count('id'),
                total_stock=Sum('stock'),
                total_reserved=Sum('reserved_stock'),
                low_stock_products=Count('id', filter=Q(stock__lte=10)),
                out_of_stock_products=Count('id', filter=Q(stock=0))
            )
            
            return summary
            
        except Exception as e:
            logger.error(f"Error getting inventory summary: {e}")
            return {}
    
    def get_low_stock_products(self, market_id=None, threshold=10):
        """Get products with low stock"""
        try:
            queryset = Product.objects.filter(stock__lte=threshold)
            
            if market_id:
                queryset = queryset.filter(market_id=market_id)
            
            return queryset.select_related('market', 'category')
            
        except Exception as e:
            logger.error(f"Error getting low stock products: {e}")
            return Product.objects.none()
    
    def get_out_of_stock_products(self, market_id=None):
        """Get out of stock products"""
        try:
            queryset = Product.objects.filter(stock=0)
            
            if market_id:
                queryset = queryset.filter(market_id=market_id)
            
            return queryset.select_related('market', 'category')
            
        except Exception as e:
            logger.error(f"Error getting out of stock products: {e}")
            return Product.objects.none()
    
    def get_inventory_movements(self, product_id, days=30):
        """Get inventory movements for a product"""
        try:
            from apps.inventory.models import InventoryLog
            from django.utils import timezone
            from datetime import timedelta
            
            start_date = timezone.now() - timedelta(days=days)
            
            return InventoryLog.objects.filter(
                product_id=product_id,
                created_at__gte=start_date
            ).order_by('-created_at')
            
        except Exception as e:
            logger.error(f"Error getting inventory movements: {e}")
            return []

class OrderInventoryManager:
    """
    Order-specific inventory management
    """
    
    def __init__(self):
        self.inventory_manager = InventoryManager()
    
    def process_order_inventory(self, order):
        """Process inventory for an order"""
        try:
            with transaction.atomic():
                # Reserve stock for all items
                for item in order.items.all():
                    if item.product:
                        success, remaining_stock = self.inventory_manager.reserve_stock(
                            product_id=item.product.id,
                            quantity=item.quantity,
                            order_id=order.id
                        )
                        
                        if not success:
                            # Release already reserved stock
                            self.release_order_stock(order)
                            raise ValidationError(f"Insufficient stock for product {item.product.name}")
                
                return True
                
        except Exception as e:
            logger.error(f"Error processing order inventory: {e}")
            raise ValidationError("Failed to process order inventory")
    
    def confirm_order_inventory(self, order):
        """Confirm inventory reduction after successful payment"""
        try:
            with transaction.atomic():
                # Confirm stock reduction for all items
                for item in order.items.all():
                    if item.product:
                        self.inventory_manager.confirm_stock_reduction(
                            product_id=item.product.id,
                            quantity=item.quantity,
                            order_id=order.id
                        )
                
                return True
                
        except Exception as e:
            logger.error(f"Error confirming order inventory: {e}")
            raise ValidationError("Failed to confirm order inventory")
    
    def release_order_stock(self, order):
        """Release stock for cancelled order"""
        try:
            with transaction.atomic():
                # Release stock for all items
                for item in order.items.all():
                    if item.product:
                        self.inventory_manager.release_stock(
                            product_id=item.product.id,
                            quantity=item.quantity,
                            order_id=order.id
                        )
                
                return True
                
        except Exception as e:
            logger.error(f"Error releasing order stock: {e}")
            raise ValidationError("Failed to release order stock")
    
    def check_order_availability(self, order_items):
        """Check if all items in order are available"""
        try:
            for item in order_items:
                if item.product:
                    available, stock = self.inventory_manager.check_stock_availability(
                        product_id=item.product.id,
                        quantity=item.quantity
                    )
                    
                    if not available:
                        return False, f"Insufficient stock for {item.product.name}. Available: {stock}"
            
            return True, "All items available"
            
        except Exception as e:
            logger.error(f"Error checking order availability: {e}")
            return False, "Error checking availability"

class InventoryAnalytics:
    """
    Inventory analytics and reporting
    """
    
    def __init__(self):
        self.cache_manager = CacheManager()
    
    def get_sales_velocity(self, product_id, days=30):
        """Calculate sales velocity for a product"""
        try:
            from django.utils import timezone
            from datetime import timedelta
            
            start_date = timezone.now() - timedelta(days=days)
            
            # Get total quantity sold
            total_sold = OrderItem.objects.filter(
                product_id=product_id,
                order__is_paid=True,
                order__created_at__gte=start_date
            ).aggregate(total=Sum('quantity'))['total'] or 0
            
            # Calculate velocity (units per day)
            velocity = total_sold / days if days > 0 else 0
            
            return {
                'product_id': product_id,
                'period_days': days,
                'total_sold': total_sold,
                'velocity': round(velocity, 2),
                'velocity_per_week': round(velocity * 7, 2),
                'velocity_per_month': round(velocity * 30, 2)
            }
            
        except Exception as e:
            logger.error(f"Error calculating sales velocity: {e}")
            return {}
    
    def get_inventory_turnover(self, market_id=None, days=30):
        """Calculate inventory turnover rate"""
        try:
            from django.utils import timezone
            from datetime import timedelta
            
            start_date = timezone.now() - timedelta(days=days)
            
            # Get products queryset
            products = Product.objects.all()
            if market_id:
                products = products.filter(market_id=market_id)
            
            turnover_data = []
            
            for product in products:
                # Get total sold
                total_sold = OrderItem.objects.filter(
                    product=product,
                    order__is_paid=True,
                    order__created_at__gte=start_date
                ).aggregate(total=Sum('quantity'))['total'] or 0
                
                # Calculate turnover rate
                if product.stock > 0:
                    turnover_rate = total_sold / product.stock
                else:
                    turnover_rate = 0
                
                turnover_data.append({
                    'product_id': product.id,
                    'product_name': product.name,
                    'current_stock': product.stock,
                    'total_sold': total_sold,
                    'turnover_rate': round(turnover_rate, 2)
                })
            
            return turnover_data
            
        except Exception as e:
            logger.error(f"Error calculating inventory turnover: {e}")
            return []
    
    def get_stock_forecast(self, product_id, days=30):
        """Forecast stock requirements"""
        try:
            # Get sales velocity
            velocity_data = self.get_sales_velocity(product_id, days)
            velocity = velocity_data.get('velocity', 0)
            
            # Get current stock
            try:
                product = Product.objects.get(id=product_id)
                current_stock = product.stock
            except Product.DoesNotExist:
                return {}
            
            # Calculate forecast
            forecast_days = 30  # Forecast for next 30 days
            forecasted_sales = velocity * forecast_days
            days_until_out_of_stock = current_stock / velocity if velocity > 0 else float('inf')
            
            # Calculate recommended reorder point
            safety_stock = velocity * 7  # 7 days safety stock
            reorder_point = velocity * 14  # 14 days lead time
            
            return {
                'product_id': product_id,
                'current_stock': current_stock,
                'daily_velocity': velocity,
                'forecasted_sales_30_days': round(forecasted_sales, 2),
                'days_until_out_of_stock': round(days_until_out_of_stock, 2),
                'recommended_safety_stock': round(safety_stock, 2),
                'recommended_reorder_point': round(reorder_point, 2),
                'recommended_order_quantity': round(max(0, reorder_point - current_stock), 2)
            }
            
        except Exception as e:
            logger.error(f"Error calculating stock forecast: {e}")
            return {}

# Celery tasks for async inventory operations
@shared_task
def process_inventory_alerts():
    """Process inventory alerts asynchronously"""
    try:
        inventory_manager = InventoryManager()
        
        # Get low stock products
        low_stock_products = inventory_manager.get_low_stock_products()
        
        for product in low_stock_products:
            inventory_manager.send_low_stock_alert(product)
        
        logger.info(f"Processed inventory alerts for {low_stock_products.count()} products")
        
    except Exception as e:
        logger.error(f"Error processing inventory alerts: {e}")

@shared_task
def generate_inventory_report():
    """Generate inventory report asynchronously"""
    try:
        inventory_manager = InventoryManager()
        analytics = InventoryAnalytics()
        
        # Get inventory summary
        summary = inventory_manager.get_inventory_summary()
        
        # Get turnover data
        turnover_data = analytics.get_inventory_turnover()
        
        # Cache the report
        report_data = {
            'summary': summary,
            'turnover_data': turnover_data,
            'generated_at': timezone.now().isoformat()
        }
        
        cache.set('inventory_report', report_data, 3600)  # Cache for 1 hour
        
        logger.info("Inventory report generated and cached")
        
    except Exception as e:
        logger.error(f"Error generating inventory report: {e}")

@shared_task
def cleanup_inventory_logs():
    """Clean up old inventory logs"""
    try:
        from apps.inventory.models import InventoryLog
        from django.utils import timezone
        from datetime import timedelta
        
        # Delete logs older than 1 year
        old_logs = InventoryLog.objects.filter(
            created_at__lt=timezone.now() - timedelta(days=365)
        )
        
        deleted_count = old_logs.count()
        old_logs.delete()
        
        logger.info(f"Cleaned up {deleted_count} old inventory logs")
        
    except Exception as e:
        logger.error(f"Error cleaning up inventory logs: {e}")





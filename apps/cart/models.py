from django.utils.translation import gettext_lazy as _

from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models, transaction
from decimal import Decimal

from apps.base.models import BaseModel
from apps.users.models import User
from apps.item.models import Item
from apps.affiliate.models import AffiliateProduct

# Create your models here.

class Cart(BaseModel):
    """Cart model for managing user shopping cart"""
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='cart',
        verbose_name=_('User')
    )

    class Meta:
        db_table = 'cart'
        verbose_name = _('Cart')
        verbose_name_plural = _('Carts')

    def __str__(self):
        return f"Cart for {self.user.username}"

    def total_price(self):
        """Calculate total price of items in cart"""
        return sum(item.total_price() for item in self.items.all())

    def total_items(self):
        """Calculate total number of items in cart"""
        return sum(item.quantity for item in self.items.all())

    def clear(self):
        """Clear all items from cart"""
        self.items.all().delete()


class CartItem(BaseModel):
    """Cart item model"""
    cart = models.ForeignKey(
        'Cart',
        related_name='items',
        on_delete=models.CASCADE,
        verbose_name=_('Cart')
    )
    product = models.ForeignKey(
        Item,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        verbose_name=_('Product'),
    )
    affiliate = models.ForeignKey(
        AffiliateProduct,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        verbose_name=_('Affiliate Product')
    )
    quantity = models.PositiveSmallIntegerField(
        default=1,
        validators=[MinValueValidator(1)],
        verbose_name=_('Quantity'),
    )
    
    unit_price = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        verbose_name=_('Unit Price'),
        help_text=_('Price per unit at the time of adding to cart')
    )
    
    shipping_cost = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        null=True,
        blank=True,
        verbose_name=_('Shipping Cost')
    )
    
    shipping_method = models.CharField(
        max_length=50,
        choices=Item.SHIP_COST_PAY_TYPE_CHOICES,
        null=True,
        blank=True,
        verbose_name=_('Shipping Method')
    )
    
    appointment_datetime = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Appointment Date & Time'),
        help_text=_('Required for service items')
    )
    
    applied_discounts = models.JSONField(
        default=dict,
        verbose_name=_('Applied Discounts'),
        help_text=_('Discounts applied to this item')
    )

    class Meta:
        db_table = 'cart_item'
        verbose_name = _('Cart Item')
        verbose_name_plural = _('Cart Items')
        unique_together = ['cart', 'product', 'affiliate']
        indexes = [
            models.Index(fields=['cart', 'created_at']),
            models.Index(fields=['product', 'cart']),
        ]

    def __str__(self):
        if self.product:
            name = self.product.name
        elif self.affiliate:
            name = self.affiliate.name
        else:
            name = "unknown"
        return f"{self.quantity} x {name}"

    def total_price(self):
        """Calculate total price for this cart item including shipping and discounts"""
        # Calculate base price
        base_total = Decimal(str(self.quantity)) * self.unit_price
        
        # Add shipping cost if applicable
        if self.shipping_cost and self.shipping_method != Item.FREE:
            if self.shipping_method == Item.CUSTOMER:
                base_total += self.shipping_cost
        
        # Apply discounts
        total_discount = Decimal('0')
        for discount in self.applied_discounts.values():
            if discount.get('type') == 'percentage':
                discount_amount = base_total * (Decimal(str(discount['value'])) / Decimal('100'))
            else:  # Fixed amount discount
                discount_amount = Decimal(str(discount['value']))
            total_discount += discount_amount
        
        return base_total - total_discount
    
    def clean(self):
        """Validate cart item"""
        super().clean()
        
        if not self.product and not self.affiliate:
            raise ValidationError(_('Either product or affiliate product must be specified'))
        
        if self.product:
            # Check if product is available
            if not self.product.is_active:
                raise ValidationError(_('This product is not available'))
            
            # Validate stock for products
            if self.product.type == Item.GOOD and self.quantity > self.product.stock:
                raise ValidationError(_('Requested quantity exceeds available stock'))
            
            # Validate appointment for services
            if self.product.type == Item.SERVICE:
                if not self.appointment_datetime:
                    raise ValidationError(_('Services require an appointment datetime'))
            else:
                # Products shouldn't have appointment times
                if self.appointment_datetime:
                    raise ValidationError(_('Products cannot have appointment times'))
            
            # Validate shipping method
            if self.product.type == Item.SERVICE and self.shipping_method:
                raise ValidationError(_('Services cannot have shipping methods'))
            elif self.product.type == Item.GOOD and not self.shipping_method:
                raise ValidationError(_('Products must have a shipping method'))
    
    @transaction.atomic
    def save(self, *args, **kwargs):
        if not self.unit_price:
            if self.product:
                self.unit_price = self.product.main_price
            elif self.affiliate:
                self.unit_price = self.affiliate.price
        
        self.full_clean()
        super().save(*args, **kwargs)


class Order(BaseModel):
    CASH = "cash"
    ONLINE = "online"

    TYPE_CHOICES = (
        (CASH, _("Cash")),
        (ONLINE, _("Online")),
    )

    DRAFT = "draft"
    PENDING = "pending"
    CONFIRMED = "confirmed"
    VERIFIED = "verified"
    REJECTED = "rejected"
    COMPLETED = "completed"
    FAILED = "failed"

    STATUS_CHOICES = (
        (DRAFT, _("Draft")),
        (PENDING, _("Pending")),
        (CONFIRMED, _("Confirmed")),
        (REJECTED, _("Rejected")),
        (COMPLETED, _("Completed")),
        (FAILED, _("Failed")),
    )

    user = models.ForeignKey(
        User,
        related_name="orders",
        on_delete=models.CASCADE,
        verbose_name=_('User')
    )
    description = models.TextField(
        null=True,
        blank=True,
        verbose_name=_('Description')
    )
    type = models.CharField(
        max_length=10,
        choices=TYPE_CHOICES,
        verbose_name=_('Type'),
    )
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default=PENDING,
        verbose_name=_('Status'),
    )
    owner_description = models.TextField(
        null=True,
        blank=True,
        verbose_name=_('Owner Descriptions')
    )
    is_paid = models.BooleanField(
        default=False,
        verbose_name=_('Is Paid')
    )
    
    shipping_address = models.JSONField(
        null=True,
        blank=True,
        verbose_name=_('Shipping Address'),
        help_text=_('Shipping address details')
    )
    
    billing_address = models.JSONField(
        null=True,
        blank=True,
        verbose_name=_('Billing Address'),
        help_text=_('Billing address details')
    )
    
    payment_method = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        verbose_name=_('Payment Method'),
        help_text=_('Payment method used for this order')
    )
    
    payment_details = models.JSONField(
        null=True,
        blank=True,
        verbose_name=_('Payment Details'),
        help_text=_('Additional payment related information')
    )
    
    contact_phone = models.CharField(
        max_length=20,
        null=True,
        blank=True,
        verbose_name=_('Contact Phone'),
        help_text=_('Phone number for order-related communication')
    )
    
    applied_discounts = models.JSONField(
        default=dict,
        verbose_name=_('Applied Discounts'),
        help_text=_('Discounts applied to the entire order')
    )
    
    class Meta:
        ordering = ['-created_at']
        db_table = 'order'
        verbose_name = _('Order')
        verbose_name_plural = _('Orders')
        indexes = [
            # Performance optimization indexes
            models.Index(fields=['user', 'status'], name='idx_order_user_status'),
            models.Index(fields=['user', 'created_at'], name='idx_order_user_created'),
            models.Index(fields=['status', 'is_paid'], name='idx_order_status_paid'),
            models.Index(fields=['is_paid', 'created_at'], name='idx_order_paid_created'),
            models.Index(fields=['type', 'status'], name='idx_order_type_status'),
        ]

    def __str__(self):
        return f"Order {str(self.id)[:6]}"

    def calculate_subtotal(self):
        """Calculate subtotal before order-level discounts"""
        return sum(item.total_price() for item in self.items.all())
    
    def calculate_shipping_total(self):
        """Calculate total shipping cost"""
        return sum(
            item.shipping_cost
            for item in self.items.all()
            if item.shipping_cost and item.shipping_method == Item.CUSTOMER
        )
    
    def calculate_order_discount(self):
        """Calculate discounts at the order level"""
        subtotal = self.calculate_subtotal()
        total_discount = Decimal('0')
        
        for discount in self.applied_discounts.values():
            if discount.get('type') == 'percentage':
                discount_amount = subtotal * (Decimal(str(discount['value'])) / Decimal('100'))
            else:  # Fixed amount discount
                discount_amount = Decimal(str(discount['value']))
            total_discount += discount_amount
            
        return total_discount
    
    def total_price(self):
        """Calculate final total including shipping and all discounts"""
        subtotal = self.calculate_subtotal()
        shipping_total = self.calculate_shipping_total()
        order_discount = self.calculate_order_discount()
        
        return subtotal + shipping_total - order_discount
    
    def validate_items(self):
        """Validate all items in the order"""
        # Check if we have any items
        if not self.items.exists():
            raise ValidationError(_('Order must contain at least one item'))
            
        # Validate shipping address for physical products
        has_physical_items = any(
            item.product and item.product.type == Item.GOOD
            for item in self.items.all()
        )
        if has_physical_items and not self.shipping_address:
            raise ValidationError(_('Shipping address is required for orders with physical products'))
            
        # Validate appointment times for services
        service_items = [
            item for item in self.items.all()
            if item.product and item.product.type == Item.SERVICE
        ]
        if service_items:
            for item in service_items:
                if not item.appointment_datetime:
                    raise ValidationError(_('All service items must have appointment times'))
    
    def clean(self):
        """Validate the order"""
        super().clean()
        
        if self.status not in [self.DRAFT, self.PENDING] and not self.payment_method:
            raise ValidationError(_('Payment method is required for non-draft orders'))
            
        if self.is_paid and self.status not in [self.CONFIRMED, self.COMPLETED]:
            raise ValidationError(_('Paid orders must be confirmed or completed'))
            
        self.validate_items()
    
    def confirm_order(self):
        """Confirm the order after payment"""
        with transaction.atomic():
            self.status = self.CONFIRMED
            self.save()
            
            # Update product stock
            for item in self.items.all():
                if item.product and item.product.type == Item.GOOD:
                    item.product.stock -= item.quantity
                    item.product.save()
    
    def cancel_order(self, reason=None):
        """Cancel the order and restore stock"""
        if self.status in [self.COMPLETED, self.FAILED]:
            raise ValidationError(_('Cannot cancel completed or failed orders'))
            
        with transaction.atomic():
            old_status = self.status
            self.status = self.REJECTED
            if reason:
                self.description = f'{self.description}\nCancellation reason: {reason}' if self.description else f'Cancellation reason: {reason}'
            self.save()
            
            # Restore product stock if order was confirmed
            if old_status == self.CONFIRMED:
                for item in self.items.all():
                    if item.product and item.product.type == Item.GOOD:
                        item.product.stock += item.quantity
                        item.product.save()
    
    def total_items(self):
        return sum(item.quantity for item in self.items.all())
    
    @classmethod
    def get_or_create_order(cls, user):
        """Get or create a order (pending order) for the user"""
        order, created = cls.objects.get_or_create(
            user=user,
            status=cls.PENDING,
            defaults={
                'type': cls.ONLINE,  # default to online, can be changed at checkout
                'description': 'Shopping order'
            }
        )
        return order

class OrderItem(BaseModel):
    order = models.ForeignKey(
        Order,
        related_name="items",
        on_delete=models.CASCADE,
        verbose_name=_('Order'),
    )
    product = models.ForeignKey(
        Item,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        verbose_name=_('Product'),
    )
    affiliate = models.ForeignKey(
        AffiliateProduct,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        verbose_name=_('Affiliate Product')
    )
    quantity = models.PositiveSmallIntegerField(
        default=1,
        verbose_name=_('Quantity'),
    )

    class Meta:
        ordering = ['-created_at']
        db_table = 'order_item'
        verbose_name = _('Order item')
        verbose_name_plural = _('Order items')

    def __str__(self):
        if self.product:
            name = self.product.name
        elif self.affiliate:
            name = self.affiliate.name
        else:
            name = "unknown"
        return f"{self.quantity} x {name}"

    def total_price(self):
        if self.product:
            price = self.product.main_price
        elif self.affiliate:
            price = self.affiliate.price
        else: 
            price = 0
        return price * self.quantity



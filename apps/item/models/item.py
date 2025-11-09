from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.core.validators import MinValueValidator
from django.contrib.contenttypes.fields import GenericRelation
from django.db import transaction
from django.core.exceptions import ValidationError
from apps.base.models import models, BaseModel
from .managers import ItemManager
from apps.users.models import User
from apps.comment.models import Comment
from apps.category.models import SubCategory

class Item(BaseModel):
    """Unified model for both Product and Service"""
    
    objects = ItemManager()
    
    # Item Type Choices
    PRODUCT = "product"
    SERVICE = "service"
    
    ITEM_TYPE_CHOICES = (
        (PRODUCT, _("Product")),
        (SERVICE, _("Service")),
    )
    
    # Status Choices
    DRAFT = "draft"
    PENDING_APPROVAL = "pending_approval"
    NOT_PUBLISHED = "not_published"
    PUBLISHED = "published"
    NEEDS_EDITING = "needs_editing"
    INACTIVE = "inactive"

    STATUS_CHOICES = (
        (DRAFT, _("Draft")),
        (PENDING_APPROVAL, _("Pending Approval")),
        (NOT_PUBLISHED, _("Not Published")),
        (PUBLISHED, _("Published")),
        (NEEDS_EDITING, _("Needs Editing")),
        (INACTIVE, _("Inactive")),
    )

    NEW = "new"
    SPECIAL_OFFER = "special_offer"
    COMING_SOON = "coming_soon"
    NONE = "none"

    LABEL_CHOICES = (
        (NEW, _("New")),
        (SPECIAL_OFFER, _("Special Offer")),
        (COMING_SOON, _("Coming Soon")),
        (NONE, _("None")),
    )

    ONLINE = "online"
    OFFLINE = "offline"
    BOTH = "both"

    SELL_TYPE_CHOICES = (
        (ONLINE, _("Online")),
        (OFFLINE, _("Offline")),
        (BOTH, _("Both")),
    )
    
    # Shipping Payment Types
    STORE_PAID = "store"
    BUYER_PAID = "buyer"
    FREE_SHIPPING = "free"
    
    SHIP_COST_PAY_TYPE_CHOICES = (
        (STORE_PAID, _("Paid by Store")),
        (BUYER_PAID, _("Paid by Buyer")),
        (FREE_SHIPPING, _("Free Shipping")),
    )

    # Discount Types
    NO_DISCOUNT = 'none'
    PERCENTAGE = 'percentage'
    TIME_LIMITED = 'time_limited'
    GROUP = 'group'

    DISCOUNT_CHOICES = (
        (NO_DISCOUNT, _('No Discount')),
        (PERCENTAGE, _('Percentage Discount')),
        (TIME_LIMITED, _('Time-Limited Discount')),
        (GROUP, _('Group Discount')),
    )

    item_type = models.CharField(
        max_length=10,
        choices=ITEM_TYPE_CHOICES,
        verbose_name=_("Item Type"),
        help_text=_("Choose whether this is a product or service")
    )

    name = models.CharField(max_length=255, verbose_name=_("Name"))
    description = models.TextField(verbose_name=_("Description"))
    technical_specs = models.JSONField(blank=True, null=True, verbose_name=_("Technical Specifications"))
    
    subcategory = models.ForeignKey(
        SubCategory,
        on_delete=models.PROTECT,
        verbose_name=_("Category")
    )
    
    keywords = models.ManyToManyField(
        "ItemKeyword",
        blank=True,
        verbose_name=_("Keywords")
    )
    
    main_image = models.ImageField(
        upload_to='items/images/',
        verbose_name=_("Main Image")
    )
    
    additional_images = models.JSONField(
        blank=True,
        null=True,
        verbose_name=_("Additional Images")
    )

    base_price = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        verbose_name=_("Base Price")
    )
    
    stock_quantity = models.PositiveIntegerField(
        default=0,
        verbose_name=_("Stock Quantity"),
        help_text=_("Only applicable for products")
    )
    
    # Shipping Configuration
    shipping_payment_type = models.CharField(
        max_length=10,
        choices=SHIP_COST_PAY_TYPE_CHOICES,
        default=BUYER_PAID,
        verbose_name=_("Shipping Payment Type"),
        help_text=_("Who pays for shipping")
    )
    
    shipping_cost = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
        verbose_name=_("Shipping Cost"),
        help_text=_("Required if shipping is not free")
    )
    
    # Service-specific fields
    requires_appointment = models.BooleanField(
        default=False,
        verbose_name=_("Requires Appointment"),
        help_text=_("Whether this service requires scheduling appointments")
    )
    
    appointment_duration = models.DurationField(
        null=True,
        blank=True,
        verbose_name=_("Appointment Duration"),
        help_text=_("Expected duration of each appointment")
    )
    
    available_slots = models.JSONField(
        null=True,
        blank=True,
        verbose_name=_("Available Time Slots"),
        help_text=_("Configuration for available appointment times")
    )

    is_advertisement = models.BooleanField(
        default=False,
        verbose_name=_("Post as Advertisement")
    )

    sell_via_marketer = models.BooleanField(
        default=False,
        verbose_name=_("Sell via Marketer")
    )

    commission_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
        verbose_name=_("Commission Percentage")
    )

    related_item = models.ForeignKey(
        'self',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='related_items',
        verbose_name=_("Related Item")
    )

    gift_item = models.ForeignKey(
        'self',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='gift_items',
        verbose_name=_("Gift Item")
    )

    label = models.CharField(
        max_length=20,
        choices=LABEL_CHOICES,
        default=NONE,
        verbose_name=_("Label")
    )

    sell_type = models.CharField(
        max_length=20,
        choices=SELL_TYPE_CHOICES,
        default=ONLINE,
        verbose_name=_("Sales Method")
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=DRAFT,
        verbose_name=_("Status")
    )

    owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name=_("Owner")
    )
    
    # Discount Configuration
    discount_type = models.CharField(
        max_length=20,
        choices=DISCOUNT_CHOICES,
        default='none',
        verbose_name=_("Discount Type")
    )
    
    discount_value = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
        verbose_name=_("Discount Value"),
        help_text=_("Percentage or fixed amount depending on discount type")
    )
    
    discount_start_date = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Discount Start Date")
    )
    
    discount_end_date = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Discount End Date")
    )
        
    comments = GenericRelation(Comment)

    class Meta:
        db_table = 'item'
        verbose_name = _('Item')
        verbose_name_plural = _('Items')

    def __str__(self):
        return self.name

    def clean(self):
        super().clean()
        if self.item_type == self.SERVICE:
            self.stock_quantity = 0
            self.shipping_payment_type = self.FREE_SHIPPING
            self.shipping_cost = 0
        
        if self.sell_via_marketer and self.commission_percentage is None:
            raise ValidationError(_("Commission percentage is required when selling via marketer."))
            
        if not self.sell_via_marketer and self.base_price is None:
            raise ValidationError(_("Base price is required when not selling via marketer."))

        if self.shipping_payment_type == self.STORE_PAID and self.shipping_cost is None:
            raise ValidationError(_("Shipping cost is required when shipping is paid by the store."))

    def save(self, *args, **kwargs):
        self.full_clean()
        with transaction.atomic():
            super().save(*args, **kwargs)
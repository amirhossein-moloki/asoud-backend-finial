from django.utils.translation import gettext_lazy as _
from django.contrib.contenttypes.fields import GenericRelation

from apps.base.models import models, BaseModel

from apps.users.models import User
from apps.category.models import SubCategory
from apps.region.models import City
from apps.comment.models import Comment
from apps.market.upload import (
    upload_market_logo,
    upload_market_background,
    upload_market_userOnly,
    upload_market_slider
)
# Create your models here.


# old images are not removed, fix it later
class Market(BaseModel):
    COMPANY = "company"
    SHOP = "shop"

    TYPE_CHOICES = (
        (COMPANY, _("Company")),
        (SHOP, _("Shop")),
    )

    # 8-State Virtual Office Workflow (as per PDF requirements)
    UNPAID_UNDER_CREATION = "unpaid_under_creation"
    PAID_UNDER_CREATION = "paid_under_creation"
    PAID_IN_PUBLICATION_QUEUE = "paid_in_publication_queue"
    PAID_NON_PUBLICATION = "paid_non_publication"
    PUBLISHED = "published"
    PAID_NEEDS_EDITING = "paid_needs_editing"
    INACTIVE = "inactive"
    PAYMENT_PENDING = "payment_pending"

    STATUS_CHOICES = (
        (UNPAID_UNDER_CREATION, _("Unpaid - Under Creation")),
        (PAID_UNDER_CREATION, _("Paid - Under Creation")),
        (PAID_IN_PUBLICATION_QUEUE, _("Paid - In Publication Queue")),
        (PAID_NON_PUBLICATION, _("Paid - Non-Publication")),
        (PUBLISHED, _("Published")),
        (PAID_NEEDS_EDITING, _("Paid - Needs Editing")),
        (INACTIVE, _("Inactive")),
        (PAYMENT_PENDING, _("Payment Pending")),
    )

    # Payment Gateway Options (as per PDF requirements)
    PERSONAL_GATEWAY = "personal"
    ASOUD_GATEWAY = "asoud"

    GATEWAY_CHOICES = (
        (PERSONAL_GATEWAY, _("Personal Gateway")),
        (ASOUD_GATEWAY, _("ASOUD Gateway")),
    )

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="markets",
        verbose_name=_('User'),
    )

    type = models.CharField(
        max_length=10,
        choices=TYPE_CHOICES,
        verbose_name=_('Type'),
    )

    status = models.CharField(
        max_length=30,
        choices=STATUS_CHOICES,
        default=UNPAID_UNDER_CREATION,
        verbose_name=_('Status'),
    )

    is_paid = models.BooleanField(
        default=False,
        verbose_name=_('Is paid'),
    )

    subscription_start_date = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name=_('Subscription start date'),
    )

    subscription_end_date = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name=_('Subscription end date'),
    )

    business_id = models.CharField(
        max_length=20,
        verbose_name=_('Business id'),
    )

    name = models.CharField(
        max_length=100,
        verbose_name=_('Name'),
    )

    description = models.TextField(
        blank=True,
        null=True,
        verbose_name=_('Description'),
    )

    national_code = models.CharField(
        max_length=10,
        blank=True,
        null=True,
        verbose_name=_('National code'),
    )

    sub_category = models.ForeignKey(
        SubCategory,
        on_delete=models.CASCADE,
        verbose_name=_('Sub Category'),
    )

    slogan = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name=_('Slogan'),
    )

    logo_img = models.ImageField(
        upload_to=upload_market_logo,
        blank=True,
        null=True,
        verbose_name=_('Logo image'),
    )

    background_img = models.ImageField(
        upload_to=upload_market_background,
        blank=True,
        null=True,
        verbose_name=_('Background image'),
    )

    view_count = models.PositiveBigIntegerField(
        default=0,
        verbose_name=_('View count'),
    )

    # Payment Gateway Configuration (as per PDF requirements)
    payment_gateway_type = models.CharField(
        max_length=20,
        choices=GATEWAY_CHOICES,
        default=ASOUD_GATEWAY,
        verbose_name=_('Payment Gateway Type'),
        help_text=_('Choose between personal gateway or ASOUD gateway'),
    )

    personal_gateway_config = models.JSONField(
        blank=True,
        null=True,
        verbose_name=_('Personal Gateway Configuration'),
        help_text=_('Configuration for personal payment gateway (if selected)'),
    )

    comments = GenericRelation(
        Comment,
        related_query_name='market_comments',
    )

    user_only_img = models.ImageField(
        upload_to=upload_market_userOnly,
        blank=True,
        null=True,
        verbose_name=_('Image'),
        help_text=_('The image is not visible to the market owner.')
    )

    class Meta:
        db_table = 'market'
        verbose_name = _('Market')
        verbose_name_plural = _('Markets')
        indexes = [
            # Performance optimization indexes
            models.Index(fields=['user', 'status'], name='idx_market_user_status'),
            models.Index(fields=['status', 'created_at'], name='idx_market_status_created'),
            models.Index(fields=['sub_category', 'status'], name='idx_market_category_status'),
            models.Index(fields=['business_id'], name='idx_market_business_id'),
            models.Index(fields=['is_paid', 'status'], name='idx_market_paid_status'),
        ]

    def __str__(self):
        return self.name

    # 8-State Workflow Management Methods
    def can_transition_to(self, new_status):
        """Check if transition to new status is allowed"""
        valid_transitions = {
            self.UNPAID_UNDER_CREATION: [
                self.PAID_UNDER_CREATION,
                self.PAYMENT_PENDING,
                self.INACTIVE
            ],
            self.PAID_UNDER_CREATION: [
                self.PAID_IN_PUBLICATION_QUEUE,
                self.PAID_NON_PUBLICATION,
                self.INACTIVE
            ],
            self.PAID_IN_PUBLICATION_QUEUE: [
                self.PUBLISHED,
                self.PAID_NEEDS_EDITING,
                self.PAID_NON_PUBLICATION,
                self.INACTIVE
            ],
            self.PAID_NON_PUBLICATION: [
                self.PAID_IN_PUBLICATION_QUEUE,
                self.PAID_NEEDS_EDITING,
                self.INACTIVE
            ],
            self.PUBLISHED: [
                self.PAID_NEEDS_EDITING,
                self.INACTIVE
            ],
            self.PAID_NEEDS_EDITING: [
                self.PAID_IN_PUBLICATION_QUEUE,
                self.PUBLISHED,
                self.INACTIVE
            ],
            self.INACTIVE: [
                self.PAID_UNDER_CREATION,
                self.UNPAID_UNDER_CREATION
            ],
            self.PAYMENT_PENDING: [
                self.PAID_UNDER_CREATION,
                self.UNPAID_UNDER_CREATION,
                self.INACTIVE
            ]
        }
        return new_status in valid_transitions.get(self.status, [])

    def transition_status(self, new_status, user=None, reason=None):
        """Safely transition to new status with validation and history tracking"""
        if not self.can_transition_to(new_status):
            raise ValueError(f"Cannot transition from {self.status} to {new_status}")
        
        old_status = self.status
        self.status = new_status
        
        # Update payment status based on new status
        if new_status in [self.PAID_UNDER_CREATION, self.PAID_IN_PUBLICATION_QUEUE, 
                         self.PAID_NON_PUBLICATION, self.PAID_NEEDS_EDITING]:
            self.is_paid = True
        elif new_status == self.UNPAID_UNDER_CREATION:
            self.is_paid = False
            
        self.save()
        
        # Create workflow history record
        MarketWorkflowHistory.objects.create(
            market=self,
            from_status=old_status,
            to_status=new_status,
            changed_by=user,
            reason=reason
        )
        
        return f"Status changed from {old_status} to {new_status}"

    def get_available_actions(self):
        """Get available actions based on current status"""
        actions = {
            self.UNPAID_UNDER_CREATION: ['edit', 'pay', 'deactivate'],
            self.PAID_UNDER_CREATION: ['edit', 'submit_for_publication', 'deactivate'],
            self.PAID_IN_PUBLICATION_QUEUE: ['preview', 'request_editing'],
            self.PAID_NON_PUBLICATION: ['edit', 'resubmit_for_publication'],
            self.PUBLISHED: ['preview', 'share', 'request_editing', 'deactivate'],
            self.PAID_NEEDS_EDITING: ['edit', 'resubmit'],
            self.INACTIVE: ['reactivate'],
            self.PAYMENT_PENDING: ['complete_payment', 'cancel']
        }
        return actions.get(self.status, [])

    def is_editable(self):
        """Check if market can be edited in current status"""
        editable_statuses = [
            self.UNPAID_UNDER_CREATION,
            self.PAID_UNDER_CREATION,
            self.PAID_NEEDS_EDITING,
            self.PAID_NON_PUBLICATION
        ]
        return self.status in editable_statuses

    def is_publishable(self):
        """Check if market can be published"""
        return self.status == self.PAID_IN_PUBLICATION_QUEUE and self.is_paid

    def get_share_url(self, request=None):
        """Get shareable URL for published markets"""
        if self.status == self.PUBLISHED:
            base_url = "https://asoud.com" if not request else request.build_absolute_uri('/')[:-1]
            return f"{base_url}/market/{self.id}/view/"
        return None

    def get_share_data(self, request=None):
        """Get comprehensive share data for social media and messaging"""
        if self.status != self.PUBLISHED:
            return None
            
        share_url = self.get_share_url(request)
        
        return {
            'url': share_url,
            'title': f"{self.name} - Virtual Office",
            'description': self.description or f"Check out {self.name} virtual office on ASOUD platform",
            'image': self.logo_img.url if self.logo_img else None,
            'market_name': self.name,
            'market_id': self.id,
            'slogan': self.slogan,
            'view_count': self.view_count,
            'social_links': {
                'whatsapp': f"https://wa.me/?text=Check out {self.name} virtual office: {share_url}",
                'telegram': f"https://t.me/share/url?url={share_url}&text=Check out {self.name} virtual office",
                'twitter': f"https://twitter.com/intent/tweet?text=Check out {self.name} virtual office&url={share_url}",
                'facebook': f"https://www.facebook.com/sharer/sharer.php?u={share_url}",
                'linkedin': f"https://www.linkedin.com/sharing/share-offsite/?url={share_url}",
            }
        }


class MarketLocation(BaseModel):
    market = models.OneToOneField(
        Market,
        on_delete=models.CASCADE,
        related_name='location',
        verbose_name=_('Market'),
    )

    city = models.ForeignKey(
        City,
        on_delete=models.CASCADE,
        verbose_name=_('City'),
    )

    address = models.TextField(
        verbose_name=_('Address'),
    )

    zip_code = models.CharField(
        max_length=15,
        verbose_name=_('Zip code'),
    )

    latitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
    )

    longitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
    )

    class Meta:
        db_table = 'market_location'
        verbose_name = _('Market location')
        verbose_name_plural = _('Market locations')

    def __str__(self):
        return self.market.name


class MarketContact(BaseModel):
    market = models.OneToOneField(
        Market,
        on_delete=models.CASCADE,
        related_name='contact',
        verbose_name=_('Market'),
    )

    first_mobile_number = models.CharField(
        max_length=15,
        verbose_name=_('First mobile number'),
    )

    second_mobile_number = models.CharField(
        max_length=15,
        blank=True,
        null=True,
        verbose_name=_('Second mobile number'),
    )

    telephone = models.CharField(
        max_length=15,
        blank=True,
        null=True,
        verbose_name=_('Telephone'),
    )

    fax = models.CharField(
        max_length=15,
        blank=True,
        null=True,
        verbose_name=_('Fax'),
    )

    email = models.CharField(
        max_length=64,
        blank=True,
        null=True,
        verbose_name=_('Email'),
    )

    website_url = models.CharField(
        max_length=64,
        blank=True,
        null=True,
        verbose_name=_('Website url'),
    )

    messenger_ids = models.JSONField(
        blank=True,
        null=True,
        verbose_name=_('Messenger IDs'),
    )

    class Meta:
        db_table = 'market_contact'
        verbose_name = _('Market contact')
        verbose_name_plural = _('Market contacts')

    def __str__(self):
        return self.market.name


class MarketSlider(BaseModel):
    market = models.ForeignKey(
        Market,
        on_delete=models.CASCADE,
        related_name='slider',
        verbose_name=_('Market')
    )

    image = models.ImageField(
        upload_to=upload_market_slider,
        verbose_name=_('Image'),
    )

    url = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name=_('Url'),
    )

    class Meta:
        db_table = 'market_slider'
        verbose_name = _('Market slider')
        verbose_name_plural = _('Market sliders')

    def __str__(self):
        return self.market.name


class MarketTheme(BaseModel):
    market = models.OneToOneField(
        Market,
        related_name='theme',
        on_delete=models.CASCADE,
        verbose_name=_('Market'),
    )
    color = models.CharField(
        max_length=7,
        verbose_name=_('Color'),
        blank=True,
        null=True,
    )
    secondary_color = models.CharField(
        max_length=7,
        verbose_name=_('Color'),
        blank=True,
        null=True,
    )
    background_color = models.CharField(
        max_length=7,
        verbose_name=_('Color'),
        blank=True,
        null=True,
    )
    font = models.CharField(
        max_length=100,
        verbose_name=_('Font'),
        blank=True,
        null=True,
    )
    font_color = models.CharField(
        max_length=7,
        verbose_name=_('Font color'),
        blank=True,
        null=True,
    )
    secondary_font_color = models.CharField(
        max_length=7,
        verbose_name=_('Font color'),
        blank=True,
        null=True,
    )

    class Meta:
        db_table = 'market_theme'
        verbose_name = _('Market theme')
        verbose_name_plural = _('Market themes')

    def __str__(self):
        return f"{self.market}-{self.font}"


class MarketReport(BaseModel):
    DRAFT = "draft"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    ARCHIVED = "archived"

    STATUS_CHOICES = [
        (DRAFT, _("Draft")),
        (IN_PROGRESS, _("In Progress")),
        (COMPLETED, _("Completed")),
        (ARCHIVED, _("Archived")),
    ]

    market = models.ForeignKey(
        Market,
        on_delete=models.CASCADE,
        verbose_name=_('Market'),
    )
    creator = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        verbose_name=_('Creator'),
        null=True,
    )
    description = models.TextField(
        verbose_name=_('Description'),
        blank=True,
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=DRAFT,
        verbose_name=_('Status'),
    )

    class Meta:
        db_table = 'market_report'
        verbose_name = _('Market report')
        verbose_name_plural = _('Market reports')

    def __str__(self):
        return self.market.name


class MarketBookmark(BaseModel):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='bookmarks',
        verbose_name=_('User'),
    )
    market = models.ForeignKey(
        Market,
        on_delete=models.CASCADE,
        related_name='bookmarked_by',
        verbose_name=_('Market'),
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name=_('Is active'),
    )

    class Meta:
        db_table = 'market_bookmark'
        unique_together = ('user', 'market')
        verbose_name = _('Market bookmark')
        verbose_name_plural = _('Market bookmarks')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user} bookmarked {self.market}"


class MarketLike(BaseModel):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='likes',
        verbose_name=_('User'),
    )
    market = models.ForeignKey(
        Market,
        on_delete=models.CASCADE,
        related_name='liked_by',
        verbose_name=_('Market'),
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name=_('Is active'),
    )

    class Meta:
        db_table = 'market_like'
        unique_together = ('user', 'market')
        verbose_name = _('Market like')
        verbose_name_plural = _('Market likes')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user} liked {self.market}"


class MarketWorkflowHistory(BaseModel):
    """Track workflow status changes for audit trail"""
    market = models.ForeignKey(
        Market,
        on_delete=models.CASCADE,
        related_name='workflow_history',
        verbose_name=_('Market'),
    )
    
    from_status = models.CharField(
        max_length=30,
        choices=Market.STATUS_CHOICES,
        verbose_name=_('From Status'),
    )
    
    to_status = models.CharField(
        max_length=30,
        choices=Market.STATUS_CHOICES,
        verbose_name=_('To Status'),
    )
    
    changed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_('Changed By'),
    )
    
    reason = models.TextField(
        blank=True,
        null=True,
        verbose_name=_('Reason'),
        help_text=_('Reason for status change'),
    )
    
    admin_notes = models.TextField(
        blank=True,
        null=True,
        verbose_name=_('Admin Notes'),
        help_text=_('Internal admin notes'),
    )

    class Meta:
        db_table = 'market_workflow_history'
        verbose_name = _('Market Workflow History')
        verbose_name_plural = _('Market Workflow Histories')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.market.name}: {self.from_status} → {self.to_status}"


class MarketApprovalRequest(BaseModel):
    """Handle admin approval requests for publication"""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    
    STATUS_CHOICES = (
        (PENDING, _("Pending")),
        (APPROVED, _("Approved")),
        (REJECTED, _("Rejected")),
    )
    
    market = models.ForeignKey(
        Market,
        on_delete=models.CASCADE,
        related_name='approval_requests',
        verbose_name=_('Market'),
    )
    
    requested_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='approval_requests',
        verbose_name=_('Requested By'),
    )
    
    reviewed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_approvals',
        verbose_name=_('Reviewed By'),
    )
    
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=PENDING,
        verbose_name=_('Status'),
    )
    
    request_type = models.CharField(
        max_length=50,
        choices=[
            ('publication', _('Publication Request')),
            ('editing', _('Editing Request')),
            ('reactivation', _('Reactivation Request')),
        ],
        verbose_name=_('Request Type'),
    )
    
    message = models.TextField(
        blank=True,
        null=True,
        verbose_name=_('Message'),
        help_text=_('Message from user to admin'),
    )
    
    admin_response = models.TextField(
        blank=True,
        null=True,
        verbose_name=_('Admin Response'),
        help_text=_('Admin response to the request'),
    )
    
    reviewed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Reviewed At'),
    )

    class Meta:
        db_table = 'market_approval_request'
        verbose_name = _('Market Approval Request')
        verbose_name_plural = _('Market Approval Requests')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.market.name} - {self.request_type} ({self.status})"


class MarketSubscription(BaseModel):
    """Handle subscription payments and management"""
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"
    
    PLAN_CHOICES = (
        (MONTHLY, _("Monthly")),
        (QUARTERLY, _("Quarterly")),
        (YEARLY, _("Yearly")),
    )
    
    ACTIVE = "active"
    EXPIRED = "expired"
    CANCELLED = "cancelled"
    PENDING = "pending"
    
    STATUS_CHOICES = (
        (ACTIVE, _("Active")),
        (EXPIRED, _("Expired")),
        (CANCELLED, _("Cancelled")),
        (PENDING, _("Pending")),
    )
    
    market = models.ForeignKey(
        Market,
        on_delete=models.CASCADE,
        related_name='subscriptions',
        verbose_name=_('Market'),
    )
    
    plan_type = models.CharField(
        max_length=20,
        choices=PLAN_CHOICES,
        verbose_name=_('Plan Type'),
    )
    
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=PENDING,
        verbose_name=_('Status'),
    )
    
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name=_('Amount'),
    )
    
    start_date = models.DateTimeField(
        verbose_name=_('Start Date'),
    )
    
    end_date = models.DateTimeField(
        verbose_name=_('End Date'),
    )
    
    payment_reference = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name=_('Payment Reference'),
    )
    
    auto_renew = models.BooleanField(
        default=False,
        verbose_name=_('Auto Renew'),
    )

    class Meta:
        db_table = 'market_subscription'
        verbose_name = _('Market Subscription')
        verbose_name_plural = _('Market Subscriptions')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.market.name} - {self.plan_type} ({self.status})"

    def is_active(self):
        """Check if subscription is currently active"""
        from django.utils import timezone
        return (self.status == self.ACTIVE and 
                self.start_date <= timezone.now() <= self.end_date)


class MarketView(BaseModel):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='viewed_markets',
        verbose_name=_('User'),
    )
    market = models.ForeignKey(
        Market,
        on_delete=models.CASCADE,
        related_name='viewed_by',
        verbose_name=_('Market'),
    )

    class Meta:
        db_table = 'market_view'
        unique_together = ('user', 'market')
        verbose_name = _('Market view')
        verbose_name_plural = _('Market views')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user} bookmarked {self.market}"


class MarketDiscount(BaseModel):
    market = models.ForeignKey(
        Market,
        on_delete=models.CASCADE,
        verbose_name=_('Market'),
    )
    code = models.CharField(
        max_length=10,
        verbose_name=_('Code'),
    )
    title = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name=_('Title'),
    )
    description = models.TextField(
        blank=True,
        null=True,
        verbose_name=_('Description'),
    )
    percentage = models.PositiveSmallIntegerField(
        verbose_name=_('Percentage'),
    )
    usage_count = models.PositiveBigIntegerField(
        default=0,
        verbose_name=_('View count'),
    )

    class Meta:
        db_table = 'market_discount'
        verbose_name = _('Market discount')
        verbose_name_plural = _('Market discounts')

    def __str__(self):
        return self.code


class MarketSchedule(BaseModel):
    DAYS_OF_WEEK = [
        (0, _('Saturday')),
        (1, _('Sunday')),
        (2, _('Monday')),
        (3, _('Tuesday')),
        (4, _('Wednesday')),
        (5, _('Thursday')),
        (6, _('Friday')),
    ]

    market = models.ForeignKey(
        Market,
        related_name='schedules',
        on_delete=models.CASCADE,
        verbose_name=_('Market'),
    )
    day_of_week = models.PositiveSmallIntegerField(
        choices=DAYS_OF_WEEK,
        verbose_name=_('Day of week'),
    )
    start_time = models.TimeField(
        verbose_name=_('Start time'),
    )
    end_time = models.TimeField(
        verbose_name=_('End time'),
    )

    class Meta:
        db_table = 'market_schedule'
        unique_together = ('market', 'day_of_week', 'start_time', 'end_time')
        ordering = ['day_of_week', 'start_time']

    def __str__(self):
        day_name = dict(self.DAYS_OF_WEEK).get(self.day_of_week, "Unknown")
        return f"{self.market.name}: {day_name} {self.start_time} - {self.end_time}"


class MarketShare(BaseModel):
    """Model to track market sharing analytics"""
    
    SHARE_PLATFORMS = [
        ('whatsapp', _('WhatsApp')),
        ('telegram', _('Telegram')),
        ('twitter', _('Twitter')),
        ('facebook', _('Facebook')),
        ('linkedin', _('LinkedIn')),
        ('email', _('Email')),
        ('sms', _('SMS')),
        ('copy_link', _('Copy Link')),
        ('qr_code', _('QR Code')),
        ('direct', _('Direct Link')),
    ]
    
    market = models.ForeignKey(
        Market,
        related_name='shares',
        on_delete=models.CASCADE,
        verbose_name=_('Market'),
    )
    
    shared_by = models.ForeignKey(
        'users.User',
        related_name='market_shares',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_('Shared by'),
    )
    
    platform = models.CharField(
        max_length=20,
        choices=SHARE_PLATFORMS,
        verbose_name=_('Share platform'),
    )
    
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        verbose_name=_('IP Address'),
    )
    
    user_agent = models.TextField(
        null=True,
        blank=True,
        verbose_name=_('User Agent'),
    )
    
    referrer = models.URLField(
        null=True,
        blank=True,
        verbose_name=_('Referrer URL'),
    )
    
    class Meta:
        db_table = 'market_share'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['market', 'platform'], name='idx_market_share_platform'),
            models.Index(fields=['shared_by', 'created_at'], name='idx_market_share_user'),
            models.Index(fields=['created_at'], name='idx_market_share_created'),
        ]
    
    def __str__(self):
        return f"{self.market.name} shared via {self.get_platform_display()}"

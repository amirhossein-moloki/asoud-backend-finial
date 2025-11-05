from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone

from apps.base.models import models, BaseModel
from apps.users.models import User
from apps.category.models import SubCategory
from apps.region.models import City, Province, Country
from apps.office_registration.validators import (
    validate_business_id, validate_iranian_national_code, 
    validate_iranian_mobile_number, validate_postal_code,
    validate_working_hours, validate_instagram_id, validate_telegram_id
)


# اضافه شده: انتخاب‌های قالب
TEMPLATE_CHOICES = [
    ('corporate', 'شرکتی'),
    ('store', 'فروشگاهی'),
]

DAY_CHOICES = [
    ('saturday', 'شنبه'),
    ('sunday', 'یکشنبه'),
    ('monday', 'دوشنبه'),
    ('tuesday', 'سه‌شنبه'),
    ('wednesday', 'چهارشنبه'),
    ('thursday', 'پنج‌شنبه'),
    ('friday', 'جمعه'),
]

IMAGE_TYPE_CHOICES = [
    ('logo', 'لوگو'),
    ('banner', 'بنر'),
    ('gallery', 'گالری'),
]


class OfficeRegistration(BaseModel):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name=_('User'),
    )

    # اصلاح شده: اضافه کردن template
    template = models.CharField(
        max_length=20,
        choices=TEMPLATE_CHOICES,
        verbose_name=_('Template'),
        help_text=_('Select corporate or store template')
    )

    # اصلاح شده: اضافه کردن unique=True و validator
    business_id = models.CharField(
        max_length=20,
        unique=True,
        validators=[validate_business_id],
        verbose_name=_('Business ID'),
        help_text=_('Unique business identifier (5-20 characters, English letters and numbers only)')
    )

    name = models.CharField(
        max_length=255,
        verbose_name=_('Name'),
    )

    description = models.TextField(
        blank=True,
        null=True,
        verbose_name=_('Description'),
    )

    # اصلاح شده: اضافه کردن validator
    national_code = models.CharField(
        max_length=10,
        blank=True,
        null=True,
        validators=[validate_iranian_national_code],
        verbose_name=_('National code'),
        help_text=_('Iranian national code (10 digits)'),
    )

    sub_category = models.ForeignKey(
        SubCategory,
        on_delete=models.CASCADE,
        verbose_name=_('Sub Category'),
    )

    slogan = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name=_('Slogan'),
    )

    # اضافه شده: ساعت کاری
    working_hours = models.JSONField(
        blank=True,
        null=True,
        default=dict,
        validators=[validate_working_hours],
        verbose_name=_('Working Hours'),
        help_text=_('Working hours for each day of the week')
    )

    # اضافه شده: فیلدهای پرداخت
    payment_gateway_type = models.CharField(
        max_length=20,
        choices=[
            ('personal', 'درگاه شخصی'),
            ('asoud', 'درگاه آسود'),
            ('later', 'بعداً')
        ],
        blank=True,
        null=True,
        verbose_name=_('Payment Gateway Type')
    )

    payment_gateway_key = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name=_('Payment Gateway Key')
    )

    # اضافه شده: فیلدهای حق اشتراک
    subscription_fee = models.DecimalField(
        max_digits=14,
        decimal_places=3,
        null=True,
        blank=True,
        verbose_name=_('Subscription Fee'),
        help_text=_('Fee calculated based on sub_category market_fee')
    )

    subscription_payment_status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'در انتظار پرداخت'),
            ('paid', 'پرداخت شده'),
            ('failed', 'ناموفق'),
            ('cancelled', 'لغو شده'),
        ],
        default='pending',
        verbose_name=_('Subscription Payment Status')
    )

    subscription_payment_date = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Subscription Payment Date')
    )

    subscription_payment_reference = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        verbose_name=_('Payment Reference')
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

    class Meta:
        db_table = 'office_registration'
        verbose_name = _('Office Registration')
        verbose_name_plural = _('Office Registrations')

    def __str__(self):
        return self.name


class OfficeRegistrationLocation(BaseModel):
    market = models.OneToOneField(
        OfficeRegistration,
        on_delete=models.CASCADE,
        verbose_name=_('Market'),
    )

    # اصلاح شده: اضافه کردن country و province
    country = models.ForeignKey(
        Country,
        on_delete=models.CASCADE,
        verbose_name=_('Country'),
        default=1  # Default to Iran
    )

    province = models.ForeignKey(
        Province,
        on_delete=models.CASCADE,
        verbose_name=_('Province'),
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
        max_length=10,
        blank=True,
        null=True,
        validators=[validate_postal_code],
        verbose_name=_('Zip code'),
    )

    latitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        blank=True,
        null=True,
        verbose_name=_('Latitude'),
    )

    longitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        blank=True,
        null=True,
        verbose_name=_('Longitude'),
    )

    class Meta:
        db_table = 'office_registration_location'
        verbose_name = _('Office Registration Location')
        verbose_name_plural = _('Office Registration Locations')

    def __str__(self):
        return f"{self.market.name} - {self.city.name}"


class OfficeRegistrationContact(BaseModel):
    market = models.OneToOneField(
        OfficeRegistration,
        on_delete=models.CASCADE,
        verbose_name=_('Market'),
    )

    first_mobile_number = models.CharField(
        max_length=11,
        validators=[validate_iranian_mobile_number],
        verbose_name=_('First mobile number'),
    )

    second_mobile_number = models.CharField(
        max_length=11,
        blank=True,
        null=True,
        validators=[validate_iranian_mobile_number],
        verbose_name=_('Second mobile number'),
    )

    telephone = models.CharField(
        max_length=11,
        blank=True,
        null=True,
        verbose_name=_('Telephone'),
    )

    fax = models.CharField(
        max_length=11,
        blank=True,
        null=True,
        verbose_name=_('Fax'),
    )

    email = models.EmailField(
        blank=True,
        null=True,
        verbose_name=_('Email'),
    )

    website_url = models.URLField(
        blank=True,
        null=True,
        verbose_name=_('Website URL'),
    )

    # اصلاح شده: جداسازی instagram و telegram
    instagram_id = models.CharField(
        max_length=30,
        blank=True,
        null=True,
        validators=[validate_instagram_id],
        verbose_name=_('Instagram ID'),
    )

    telegram_id = models.CharField(
        max_length=32,
        blank=True,
        null=True,
        validators=[validate_telegram_id],
        verbose_name=_('Telegram ID'),
    )

    # اضافه شده: messenger_ids برای سایر پیام‌رسان‌ها
    messenger_ids = models.JSONField(
        blank=True,
        null=True,
        default=dict,
        verbose_name=_('Messenger IDs'),
        help_text=_('Other messenger IDs in JSON format')
    )

    class Meta:
        db_table = 'office_registration_contact'
        verbose_name = _('Office Registration Contact')
        verbose_name_plural = _('Office Registration Contacts')

    def __str__(self):
        return self.market.name


class OfficeRegistrationSchedule(BaseModel):
    market = models.ForeignKey(
        OfficeRegistration,
        on_delete=models.CASCADE,
        related_name='schedules',
        verbose_name=_('Market'),
    )
    day_of_week = models.CharField(
        max_length=10,
        choices=DAY_CHOICES,
        verbose_name=_('Day of week'),
    )
    start_time = models.TimeField(
        verbose_name=_('Start time'),
    )
    end_time = models.TimeField(
        verbose_name=_('End time'),
    )

    class Meta:
        db_table = 'office_registration_schedule'
        verbose_name = _('Office Registration Schedule')
        verbose_name_plural = _('Office Registration Schedules')

    def __str__(self):
        return f"{self.market.name} - {self.day_of_week}"


class OfficeRegistrationSocialMedia(BaseModel):
    market = models.OneToOneField(
        OfficeRegistration,
        on_delete=models.CASCADE,
        verbose_name=_('Market'),
    )
    instagram = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        validators=[validate_instagram_id],
        verbose_name=_('Instagram'),
    )
    telegram = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        validators=[validate_telegram_id],
        verbose_name=_('Telegram'),
    )
    whatsapp = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name=_('WhatsApp'),
    )

    class Meta:
        db_table = 'office_registration_social_media'
        verbose_name = _('Office Registration Social Media')
        verbose_name_plural = _('Office Registration Social Media')

    def __str__(self):
        return self.market.name


class OfficeRegistrationImage(BaseModel):
    market = models.ForeignKey(
        OfficeRegistration,
        on_delete=models.CASCADE,
        related_name='images',
        verbose_name=_('Market'),
    )
    image = models.ImageField(
        upload_to='market_images/',
        verbose_name=_('Image'),
    )
    image_type = models.CharField(
        max_length=20,
        choices=IMAGE_TYPE_CHOICES,
        verbose_name=_('Image type'),
    )

    class Meta:
        db_table = 'office_registration_image'
        verbose_name = _('Office Registration Image')
        verbose_name_plural = _('Office Registration Images')

    def __str__(self):
        return f"{self.market.name} - {self.image_type}"
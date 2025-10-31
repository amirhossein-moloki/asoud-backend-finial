from rest_framework import serializers
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.core.exceptions import ValidationError as DjangoValidationError

# Import models with correct paths
try:
    from ..models.office_registration_models import Market, MarketLocation, MarketContact, MarketSchedule
except ImportError:
    from .models import Market, MarketLocation, MarketContact, MarketSchedule

try:
    from apps.category.models import SubCategory
except ImportError:
    from ..models.category_models import SubCategory

try:
    from apps.location.models import City, Province, Country
except ImportError:
    # Fallback for location models if not available
    City = Province = Country = None

try:
    from apps.users.models import User
except ImportError:
    from django.contrib.auth.models import User

try:
    from apps.discount.models import Discount
except ImportError:
    # Fallback if discount models not available
    Discount = None

# Import validators
try:
    from ..validators import (
        validate_business_id, validate_iranian_national_code, 
        validate_iranian_mobile_number, validate_postal_code,
        validate_working_hours, validate_instagram_id, validate_telegram_id
    )
except ImportError:
    # Fallback validators if not available
    validate_business_id = validate_iranian_national_code = None
    validate_iranian_mobile_number = validate_postal_code = None
    validate_working_hours = validate_instagram_id = validate_telegram_id = None


class MarketCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Market
        fields = [
            'template',
            'business_id',
            'name',
            'description',
            'national_code',
            'sub_category',
            'slogan',
            'working_hours'
        ]

    def validate_business_id(self, value):
        if len(value) < 5:
            raise serializers.ValidationError('شناسه کسب‌وکار باید حداقل 5 کاراکتر باشد')
        if not value.isascii():
            raise serializers.ValidationError('شناسه کسب‌وکار باید به زبان انگلیسی باشد')
        return value

    def validate_national_code(self, value):
        if value and len(value) != 10:
            raise serializers.ValidationError('کد ملی باید 10 رقم باشد')
        return value


class MarketLocationCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = MarketLocation
        fields = [
            'market',
            'country',
            'province',
            'city',
            'address',
            'zip_code',
            'latitude',
            'longitude'
        ]


class MarketContactCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = MarketContact
        fields = [
            'market',
            'first_mobile_number',
            'second_mobile_number',
            'telephone',
            'fax',
            'email',
            'website_url',
            'instagram_id',
            'telegram_id',
            'messenger_ids'
        ]


class MarketScheduleSerializer(serializers.ModelSerializer):
    class Meta:
        model = MarketSchedule
        fields = [
            'market',
            'day_of_week',
            'start_time',
            'end_time',
            'is_working_day'
        ]


# اضافه شده: Serializer برای انتخاب درگاه پرداخت
class PaymentGatewaySerializer(serializers.Serializer):
    GATEWAY_CHOICES = [
        ('personal', 'درگاه شخصی'),
        ('asoud', 'درگاه آسود'),
        ('later', 'بعداً')
    ]
    
    gateway_type = serializers.ChoiceField(choices=GATEWAY_CHOICES)
    gateway_key = serializers.CharField(max_length=255, required=False)
    
    def validate(self, data):
        gateway_type = data.get('gateway_type')
        gateway_key = data.get('gateway_key')
        
        if gateway_type == 'personal' and not gateway_key:
            raise serializers.ValidationError({
                'gateway_key': 'کلید درگاه شخصی الزامی است'
            })
        
        return data


# اضافه شده: Serializer برای محاسبه حق اشتراک
class SubscriptionFeeCalculatorSerializer(serializers.Serializer):
    sub_category_id = serializers.IntegerField()
    
    def validate_sub_category_id(self, value):
        try:
            sub_category = SubCategory.objects.get(id=value)
            return value
        except SubCategory.DoesNotExist:
            raise serializers.ValidationError("زیردسته انتخاب شده وجود ندارد")


# اضافه شده: Serializer برای پرداخت حق اشتراک
class SubscriptionPaymentSerializer(serializers.Serializer):
    payment_method = serializers.ChoiceField(
        choices=[
            ('wallet', 'کیف پول'),
            ('gateway', 'درگاه پرداخت'),
        ]
    )
    
    discount_code = serializers.CharField(max_length=50, required=False)
    
    def validate_discount_code(self, value):
        if value:
            try:
                discount = Discount.objects.get(code=value, is_active=True)
                if discount.expiry < timezone.now():
                    raise serializers.ValidationError("کد تخفیف منقضی شده است")
            except Discount.DoesNotExist:
                raise serializers.ValidationError("کد تخفیف معتبر نیست")
        return value


# اضافه شده: Serializer برای ایجاد فروشگاه یکپارچه
class IntegratedMarketCreateSerializer(serializers.Serializer):
    # مشخصات پایه
    template = serializers.ChoiceField(choices=[('corporate', 'شرکتی'), ('store', 'فروشگاهی')])
    business_id = serializers.CharField(max_length=20)
    name = serializers.CharField(max_length=255)
    description = serializers.CharField(required=False, allow_blank=True)
    national_code = serializers.CharField(max_length=10, required=False, allow_blank=True)
    sub_category = serializers.IntegerField()
    slogan = serializers.CharField(max_length=255, required=False, allow_blank=True)
    working_hours = serializers.JSONField(required=False)
    
    # مشخصات ارتباطی
    first_mobile_number = serializers.CharField(max_length=11)
    second_mobile_number = serializers.CharField(max_length=11, required=False, allow_blank=True)
    telephone = serializers.CharField(max_length=11, required=False, allow_blank=True)
    fax = serializers.CharField(max_length=11, required=False, allow_blank=True)
    email = serializers.EmailField(required=False, allow_blank=True)
    website_url = serializers.URLField(required=False, allow_blank=True)
    instagram_id = serializers.CharField(max_length=100, required=False, allow_blank=True)
    telegram_id = serializers.CharField(max_length=100, required=False, allow_blank=True)
    messenger_ids = serializers.JSONField(required=False)
    
    # مشخصات مکانی
    country = serializers.IntegerField()
    province = serializers.IntegerField()
    city = serializers.IntegerField()
    address = serializers.CharField()
    zip_code = serializers.CharField(max_length=10, required=False, allow_blank=True)
    latitude = serializers.DecimalField(max_digits=9, decimal_places=6, required=False)
    longitude = serializers.DecimalField(max_digits=9, decimal_places=6, required=False)
    
    def validate_business_id(self, value):
        if len(value) < 5:
            raise serializers.ValidationError('شناسه کسب‌وکار باید حداقل 5 کاراکتر باشد')
        if not value.isascii():
            raise serializers.ValidationError('شناسه کسب‌وکار باید به زبان انگلیسی باشد')
        return value

    def validate_national_code(self, value):
        if value and len(value) != 10:
            raise serializers.ValidationError('کد ملی باید 10 رقم باشد')
        return value
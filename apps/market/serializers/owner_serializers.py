from rest_framework import serializers
from django.urls import reverse
import jdatetime

from apps.market.models import (
    Market,
    MarketLocation,
    MarketContact,
    MarketSlider,
    MarketTheme,
)


class MarketCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Market
        fields = [
            'type',
            'business_id',
            'name',
            'description',
            'national_code',
            'sub_category',
            'slogan',
            'payment_gateway_type',  # New field for PDF compliance
            'personal_gateway_config',  # New field for PDF compliance
        ]

    def validate(self, data):
        """
        Validate payment gateway configuration based on PDF requirements.
        """
        gateway_type = data.get('payment_gateway_type')
        gateway_config = data.get('personal_gateway_config')
        
        # If personal gateway is selected, configuration should be provided
        if gateway_type == Market.PERSONAL_GATEWAY:
            if not gateway_config:
                raise serializers.ValidationError({
                    'personal_gateway_config': 'Personal gateway configuration is required when personal gateway is selected.'
                })
            
            # Validate required fields in personal gateway config
            required_fields = ['gateway_name', 'api_key', 'merchant_id']
            for field in required_fields:
                if field not in gateway_config:
                    raise serializers.ValidationError({
                        'personal_gateway_config': f'Field "{field}" is required in personal gateway configuration.'
                    })
        
        return data


class MarketUpdateSerializer(MarketCreateSerializer):
    def update(self, instance, validated_data):
        return super().update(instance, validated_data)


class MarketLocationCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = MarketLocation
        fields = [
            'market',
            'city',
            'address',
            'zip_code',
            'latitude',
            'longitude',
        ]


class MarketLocationUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = MarketLocation
        fields = [
            'city',
            'address',
            'zip_code',
            'latitude',
            'longitude',
        ]

    def update(self, instance, validated_data):
        return super().update(instance, validated_data)


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
            'messenger_ids',
        ]


class MarketContactUpdaterSerializer(serializers.ModelSerializer):
    class Meta:
        model = MarketContact
        fields = [
            'first_mobile_number',
            'second_mobile_number',
            'telephone',
            'fax',
            'email',
            'website_url',
            'messenger_ids',
        ]


class MarketLocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = MarketLocation
        fields = '__all__'


class MarketContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = MarketContact
        fields = '__all__'


class MarketGetSerializer(serializers.ModelSerializer):
    location = MarketLocationSerializer(read_only=True)
    contact = MarketContactSerializer(read_only=True)

    class Meta:
        model = Market
        fields = [
            'id',
            'type',
            'business_id',
            'name',
            'description',
            'national_code',
            'sub_category',
            'slogan',
            'status',
            'is_paid',
            'subscription_start_date',
            'subscription_end_date',
            'logo_img',
            'background_img',
            'view_count',
            'payment_gateway_type',
            'personal_gateway_config',
            'subdomain',
            'location',
            'contact',
        ]


class MarketThemeCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = MarketTheme
        fields = [
            'color',
            'secondary_color',
            'background_color',
            'font',
            'font_color',
            'secondary_font_color',
        ]


class MarketListSerializer(serializers.ModelSerializer):
    created_at = serializers.SerializerMethodField()
    inactive_url = serializers.SerializerMethodField()
    queue_url = serializers.SerializerMethodField()
    sub_category_title = serializers.SerializerMethodField()
    view_count = serializers.SerializerMethodField()

    theme = MarketThemeCreateSerializer()

    class Meta:
        model = Market
        fields = [
            'id',
            'business_id',
            'name',
            'sub_category',
            'sub_category_title',
            'status',
            'is_paid',
            'created_at',
            'inactive_url',
            'queue_url',
            'logo_img',
            'background_img',
            'theme',
            'view_count',
        ]

    def get_created_at(self, obj):
        created_at_date = obj.created_at.date()
        jalali_date = jdatetime.date.fromgregorian(date=created_at_date)
        return jalali_date.strftime("%Y/%m/%d")

    def get_inactive_url(self, obj):
        request = self.context.get('request')
        return request.build_absolute_uri(
            reverse(
                'market_owner:inactive',
                kwargs={'pk': obj.id},
            )
        )

    def get_queue_url(self, obj):
        request = self.context.get('request')
        return request.build_absolute_uri(
            reverse(
                'market_owner:queue',
                kwargs={'pk': obj.id},
            )
        )

    def get_sub_category_title(self, obj):
        return obj.sub_category.title if obj.sub_category else None

    def get_view_count(self, obj):
        market_viewed_by = obj.viewed_by.all()
        return market_viewed_by.count()


class MarketSliderListSerializer(serializers.ModelSerializer):
    class Meta:
        model = MarketSlider
        fields = [
            'id',
            'image',
            'url',
        ]

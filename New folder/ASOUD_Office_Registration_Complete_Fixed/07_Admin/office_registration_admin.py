from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _
from django.db.models import Q
from django.contrib.admin import SimpleListFilter
from ..models.office_registration_models import (
    Market, MarketLocation, MarketContact, MarketSchedule, PaymentRequest
)


class MarketStatusFilter(SimpleListFilter):
    """Custom filter for market status"""
    title = _('Market Status')
    parameter_name = 'status'

    def lookups(self, request, model_admin):
        return (
            ('active', _('Active')),
            ('pending', _('Pending')),
            ('inactive', _('Inactive')),
            ('suspended', _('Suspended')),
        )

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(status=self.value())
        return queryset


class MarketTypeFilter(SimpleListFilter):
    """Custom filter for market type"""
    title = _('Market Type')
    parameter_name = 'market_type'

    def lookups(self, request, model_admin):
        return (
            ('individual', _('Individual')),
            ('company', _('Company')),
        )

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(market_type=self.value())
        return queryset


class PaymentGatewayFilter(SimpleListFilter):
    """Custom filter for payment gateway"""
    title = _('Payment Gateway')
    parameter_name = 'payment_gateway_type'

    def lookups(self, request, model_admin):
        return (
            ('zarinpal', _('ZarinPal')),
            ('mellat', _('Mellat')),
            ('personal', _('Personal')),
        )

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(payment_gateway_type=self.value())
        return queryset


class MarketLocationInline(admin.StackedInline):
    """Inline admin for MarketLocation"""
    model = MarketLocation
    extra = 0
    fields = (
        ('province', 'city'),
        'address',
        ('zip_code', 'latitude', 'longitude'),
    )


class MarketContactInline(admin.StackedInline):
    """Inline admin for MarketContact"""
    model = MarketContact
    extra = 0
    fields = (
        ('first_mobile_number', 'second_mobile_number'),
        ('landline_number', 'email'),
        'website',
        ('instagram_id', 'telegram_id'),
    )


class MarketScheduleInline(admin.TabularInline):
    """Inline admin for MarketSchedule"""
    model = MarketSchedule
    extra = 0
    fields = ('day_of_week', 'start_time', 'end_time', 'is_working')
    ordering = ['day_of_week']


class PaymentRequestInline(admin.TabularInline):
    """Inline admin for PaymentRequest"""
    model = PaymentRequest
    extra = 0
    readonly_fields = ('created_at', 'transaction_id', 'gateway_url')
    fields = (
        'amount', 'final_amount', 'discount_amount',
        'status', 'gateway_type', 'transaction_id', 'created_at'
    )
    ordering = ['-created_at']


@admin.register(Market)
class MarketAdmin(admin.ModelAdmin):
    """Admin configuration for Market model"""
    
    list_display = (
        'market_name', 'business_id', 'user', 'market_type', 
        'status_badge', 'subscription_status', 'payment_gateway_type',
        'created_at', 'is_active'
    )
    
    list_filter = (
        MarketStatusFilter, MarketTypeFilter, PaymentGatewayFilter,
        'is_active', 'created_at', 'subscription_start_date'
    )
    
    search_fields = (
        'market_name', 'business_id', 'national_code',
        'user__username', 'user__email', 'user__first_name', 'user__last_name'
    )
    
    readonly_fields = (
        'created_at', 'updated_at', 'subscription_status_display',
        'payment_info_display', 'working_hours_display'
    )
    
    fieldsets = (
        (_('Basic Information'), {
            'fields': (
                ('market_name', 'business_id'),
                ('user', 'market_type'),
                ('national_code', 'sub_category'),
                ('status', 'is_active'),
            )
        }),
        (_('Subscription Information'), {
            'fields': (
                ('subscription_start_date', 'subscription_end_date'),
                'subscription_status_display',
            )
        }),
        (_('Payment Gateway'), {
            'fields': (
                ('payment_gateway_type', 'payment_gateway_key'),
                'payment_info_display',
            )
        }),
        (_('Working Hours'), {
            'fields': ('working_hours', 'working_hours_display'),
            'classes': ('collapse',),
        }),
        (_('Timestamps'), {
            'fields': (('created_at', 'updated_at'),),
            'classes': ('collapse',),
        }),
    )
    
    inlines = [MarketLocationInline, MarketContactInline, MarketScheduleInline, PaymentRequestInline]
    
    actions = ['activate_markets', 'deactivate_markets', 'suspend_markets']
    
    def status_badge(self, obj):
        """Display status with colored badge"""
        colors = {
            'active': 'green',
            'pending': 'orange',
            'inactive': 'red',
            'suspended': 'darkred'
        }
        color = colors.get(obj.status, 'gray')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = _('Status')
    
    def subscription_status(self, obj):
        """Display subscription status"""
        if obj.subscription_start_date and obj.subscription_end_date:
            from django.utils import timezone
            now = timezone.now()
            if now < obj.subscription_start_date:
                return format_html('<span style="color: orange;">Not Started</span>')
            elif now > obj.subscription_end_date:
                return format_html('<span style="color: red;">Expired</span>')
            else:
                return format_html('<span style="color: green;">Active</span>')
        return format_html('<span style="color: gray;">No Subscription</span>')
    subscription_status.short_description = _('Subscription')
    
    def subscription_status_display(self, obj):
        """Detailed subscription status for readonly field"""
        if obj.subscription_start_date and obj.subscription_end_date:
            return f"From {obj.subscription_start_date} to {obj.subscription_end_date}"
        return "No active subscription"
    subscription_status_display.short_description = _('Subscription Status')
    
    def payment_info_display(self, obj):
        """Display payment gateway information"""
        if obj.payment_gateway_type:
            gateway_info = f"Type: {obj.get_payment_gateway_type_display()}"
            if obj.payment_gateway_key:
                gateway_info += f"\nKey: {obj.payment_gateway_key[:20]}..."
            return gateway_info
        return "No payment gateway configured"
    payment_info_display.short_description = _('Payment Gateway Info')
    
    def working_hours_display(self, obj):
        """Display formatted working hours"""
        if obj.working_hours:
            formatted_hours = []
            for day, hours in obj.working_hours.items():
                if hours.get('is_working', False):
                    formatted_hours.append(
                        f"{day.title()}: {hours.get('start_time', 'N/A')} - {hours.get('end_time', 'N/A')}"
                    )
                else:
                    formatted_hours.append(f"{day.title()}: Closed")
            return "\n".join(formatted_hours)
        return "No working hours set"
    working_hours_display.short_description = _('Working Hours')
    
    def activate_markets(self, request, queryset):
        """Bulk action to activate markets"""
        updated = queryset.update(status='active', is_active=True)
        self.message_user(request, f'{updated} markets were successfully activated.')
    activate_markets.short_description = _('Activate selected markets')
    
    def deactivate_markets(self, request, queryset):
        """Bulk action to deactivate markets"""
        updated = queryset.update(status='inactive', is_active=False)
        self.message_user(request, f'{updated} markets were successfully deactivated.')
    deactivate_markets.short_description = _('Deactivate selected markets')
    
    def suspend_markets(self, request, queryset):
        """Bulk action to suspend markets"""
        updated = queryset.update(status='suspended')
        self.message_user(request, f'{updated} markets were successfully suspended.')
    suspend_markets.short_description = _('Suspend selected markets')


@admin.register(MarketLocation)
class MarketLocationAdmin(admin.ModelAdmin):
    """Admin configuration for MarketLocation model"""
    
    list_display = ('market', 'province', 'city', 'zip_code', 'coordinates', 'is_active')
    list_filter = ('province', 'city', 'is_active', 'created_at')
    search_fields = ('market__market_name', 'province', 'city', 'address', 'zip_code')
    
    fieldsets = (
        (_('Market'), {
            'fields': ('market',)
        }),
        (_('Location Information'), {
            'fields': (
                ('province', 'city'),
                'address',
                ('zip_code', 'latitude', 'longitude'),
                'is_active',
            )
        }),
        (_('Timestamps'), {
            'fields': (('created_at', 'updated_at'),),
            'classes': ('collapse',),
        }),
    )
    
    readonly_fields = ('created_at', 'updated_at')
    
    def coordinates(self, obj):
        """Display coordinates if available"""
        if obj.latitude and obj.longitude:
            return f"{obj.latitude}, {obj.longitude}"
        return "Not set"
    coordinates.short_description = _('Coordinates')


@admin.register(MarketContact)
class MarketContactAdmin(admin.ModelAdmin):
    """Admin configuration for MarketContact model"""
    
    list_display = (
        'market', 'first_mobile_number', 'email', 
        'has_social_media', 'is_active'
    )
    list_filter = ('is_active', 'created_at')
    search_fields = (
        'market__market_name', 'first_mobile_number', 'second_mobile_number',
        'email', 'instagram_id', 'telegram_id'
    )
    
    fieldsets = (
        (_('Market'), {
            'fields': ('market',)
        }),
        (_('Phone Numbers'), {
            'fields': (
                ('first_mobile_number', 'second_mobile_number'),
                'landline_number',
            )
        }),
        (_('Digital Contact'), {
            'fields': (
                'email',
                'website',
            )
        }),
        (_('Social Media'), {
            'fields': (
                ('instagram_id', 'telegram_id'),
            )
        }),
        (_('Status'), {
            'fields': ('is_active',)
        }),
        (_('Timestamps'), {
            'fields': (('created_at', 'updated_at'),),
            'classes': ('collapse',),
        }),
    )
    
    readonly_fields = ('created_at', 'updated_at')
    
    def has_social_media(self, obj):
        """Check if market has social media presence"""
        return bool(obj.instagram_id or obj.telegram_id)
    has_social_media.boolean = True
    has_social_media.short_description = _('Social Media')


@admin.register(MarketSchedule)
class MarketScheduleAdmin(admin.ModelAdmin):
    """Admin configuration for MarketSchedule model"""
    
    list_display = ('market', 'day_of_week', 'working_hours', 'is_working', 'is_active')
    list_filter = ('day_of_week', 'is_working', 'is_active', 'created_at')
    search_fields = ('market__market_name',)
    
    fieldsets = (
        (_('Market'), {
            'fields': ('market',)
        }),
        (_('Schedule Information'), {
            'fields': (
                'day_of_week',
                ('start_time', 'end_time'),
                ('is_working', 'is_active'),
            )
        }),
        (_('Timestamps'), {
            'fields': (('created_at', 'updated_at'),),
            'classes': ('collapse',),
        }),
    )
    
    readonly_fields = ('created_at', 'updated_at')
    
    def working_hours(self, obj):
        """Display working hours"""
        if obj.is_working:
            return f"{obj.start_time} - {obj.end_time}"
        return "Closed"
    working_hours.short_description = _('Working Hours')


@admin.register(PaymentRequest)
class PaymentRequestAdmin(admin.ModelAdmin):
    """Admin configuration for PaymentRequest model"""
    
    list_display = (
        'market', 'amount', 'final_amount', 'status_badge',
        'gateway_type', 'created_at', 'is_active'
    )
    list_filter = ('status', 'gateway_type', 'is_active', 'created_at')
    search_fields = ('market__market_name', 'transaction_id')
    
    fieldsets = (
        (_('Market'), {
            'fields': ('market',)
        }),
        (_('Payment Information'), {
            'fields': (
                ('amount', 'discount_amount', 'final_amount'),
                ('status', 'gateway_type'),
                ('transaction_id', 'gateway_url'),
            )
        }),
        (_('Status'), {
            'fields': ('is_active',)
        }),
        (_('Timestamps'), {
            'fields': (('created_at', 'updated_at'),),
            'classes': ('collapse',),
        }),
    )
    
    readonly_fields = ('created_at', 'updated_at', 'transaction_id', 'gateway_url')
    
    def status_badge(self, obj):
        """Display status with colored badge"""
        colors = {
            'pending': 'orange',
            'completed': 'green',
            'failed': 'red',
            'cancelled': 'gray'
        }
        color = colors.get(obj.status, 'black')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = _('Status')


# Admin site customization
admin.site.site_header = _('ASOUD Office Registration Admin')
admin.site.site_title = _('ASOUD Admin')
admin.site.index_title = _('Office Registration Management')
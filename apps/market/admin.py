from apps.base.admin import admin, BaseAdmin, BaseTabularInline

from .models import (
    Market,
    MarketLocation,
    MarketContact,
    MarketSlider,
    MarketTheme,
    MarketReport,
    MarketBookmark,
    MarketLike,
    MarketView,
    MarketDiscount,
    MarketSchedule,
    MarketWorkflowHistory,
    MarketApprovalRequest,
    MarketSubscription,
    MarketShare,
)

# Register your models here.


class MarketLocationTabularInline(BaseTabularInline):
    model = MarketLocation

    fields = (
        'city',
        'address',
        'zip_code',
        'latitude',
        'longitude',
    )


class MarketContactTabularInline(BaseTabularInline):
    model = MarketContact

    fields = (
        'first_mobile_number',
        'second_mobile_number',
        'telephone',
        'fax',
        'email',
        'website_url',
        'messenger_ids',
    )


class MarketSliderTabularInline(BaseTabularInline):
    model = MarketSlider
    extra = 1

    fields = (
        'image',
        'url',
    )


class MarketThemeTabularInline(BaseTabularInline):
    model = MarketTheme
    fields = (
        'color',
        'font',
        'font_color',
    )


class MarketScheduleTabularInline(BaseTabularInline):
    model = MarketSchedule
    extra = 1

    fields = (
        'day_of_week',
        'start_time',
        'end_time',
    )


class MarketAdmin(BaseAdmin):
    inlines = [
        MarketLocationTabularInline,
        MarketContactTabularInline,
        MarketSliderTabularInline,
        MarketThemeTabularInline,
        MarketScheduleTabularInline,
    ]

    list_display = [
        'name',
        'user',
    ]

    fields = (
        'user',
        'type',
        'status',
        'is_paid',
        'subscription_start_date',
        'subscription_end_date',
        'business_id',
        'name',
        'description',
        'national_code',
        'sub_category',
        'slogan',
        'logo_img',
        'background_img',
        'user_only_img',
    ) + BaseAdmin.fields

    readonly_fields = BaseAdmin.readonly_fields


admin.site.register(Market, MarketAdmin)


class MarketReportAdmin(BaseAdmin):
    list_display = [
        'market',
    ]

    fields = (
        'market',
        'creator',
        'description',
        'status',
    ) + BaseAdmin.fields

    readonly_fields = BaseAdmin.readonly_fields


admin.site.register(MarketReport, MarketReportAdmin)


class MarketBookmarkAdmin(BaseAdmin):
    list_display = [
        'user',
        'market',
        'is_active',
    ]

    fields = (
        'user',
        'market',
        'is_active',
    ) + BaseAdmin.fields

    readonly_fields = BaseAdmin.readonly_fields


admin.site.register(MarketBookmark, MarketBookmarkAdmin)


class MarketLikeAdmin(BaseAdmin):
    list_display = [
        'user',
        'market',
        'is_active',
    ]

    fields = (
        'user',
        'market',
        'is_active',
    ) + BaseAdmin.fields

    readonly_fields = BaseAdmin.readonly_fields


admin.site.register(MarketLike, MarketLikeAdmin)


class MarketViewAdmin(BaseAdmin):
    list_display = [
        'user',
        'market',
    ]

    fields = (
        'user',
        'market',
    ) + BaseAdmin.fields

    readonly_fields = BaseAdmin.readonly_fields


admin.site.register(MarketView, MarketViewAdmin)


class MarketDiscountAdmin(BaseAdmin):
    list_display = [
        'code',
        'title',
    ]

    fields = (
        'market',
        'code',
        'title',
        'description',
        'percentage',
        'usage_count',
    ) + BaseAdmin.fields

    readonly_fields = BaseAdmin.readonly_fields


admin.site.register(MarketDiscount, MarketDiscountAdmin)


class MarketWorkflowHistoryAdmin(BaseAdmin):
    list_display = [
        'market',
        'from_status',
        'to_status',
        'changed_by',
        'created_at',
    ]
    
    list_filter = [
        'from_status',
        'to_status',
        'created_at',
    ]
    
    search_fields = [
        'market__title',
        'changed_by__username',
        'reason',
    ]
    
    fields = (
        'market',
        'from_status',
        'to_status',
        'changed_by',
        'reason',
    ) + BaseAdmin.fields
    
    readonly_fields = BaseAdmin.readonly_fields


admin.site.register(MarketWorkflowHistory, MarketWorkflowHistoryAdmin)


class MarketApprovalRequestAdmin(BaseAdmin):
    list_display = [
        'market',
        'request_type',
        'status',
        'requested_by',
        'reviewed_by',
        'created_at',
    ]
    
    list_filter = [
        'request_type',
        'status',
        'created_at',
    ]
    
    search_fields = [
        'market__title',
        'requested_by__username',
        'reviewed_by__username',
        'message',
    ]
    
    fields = (
        'market',
        'request_type',
        'status',
        'requested_by',
        'reviewed_by',
        'message',
        'admin_response',
    ) + BaseAdmin.fields
    
    readonly_fields = BaseAdmin.readonly_fields


admin.site.register(MarketApprovalRequest, MarketApprovalRequestAdmin)


class MarketSubscriptionAdmin(BaseAdmin):
    list_display = [
        'market',
        'plan_type',
        'status',
        'amount',
        'start_date',
        'end_date',
    ]
    
    list_filter = [
        'plan_type',
        'status',
        'start_date',
        'end_date',
    ]
    
    search_fields = [
        'market__title',
        'transaction_id',
    ]
    
    fields = (
        'market',
        'plan_type',
        'status',
        'amount',
        'start_date',
        'end_date',
        'transaction_id',
        'auto_renew',
    ) + BaseAdmin.fields
    
    readonly_fields = BaseAdmin.readonly_fields


admin.site.register(MarketSubscription, MarketSubscriptionAdmin)


@admin.register(MarketShare)
class MarketShareAdmin(BaseAdmin):
    list_display = [
        'market',
        'shared_by',
        'platform',
        'ip_address',
        'created_at',
    ]
    
    list_filter = [
        'platform',
        'created_at',
        'market__status',
    ]
    
    search_fields = [
        'market__name',
        'shared_by__mobile_number',
        'shared_by__email',
        'ip_address',
    ]
    
    fields = (
        'market',
        'shared_by',
        'platform',
        'ip_address',
        'user_agent',
        'referrer',
    ) + BaseAdmin.fields
    
    readonly_fields = BaseAdmin.readonly_fields + ('ip_address', 'user_agent', 'referrer')
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('market', 'shared_by')

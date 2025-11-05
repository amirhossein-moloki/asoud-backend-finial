from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from django.db.models import Count, Sum
from django.contrib.admin import SimpleListFilter
from ..models.category_models import (
    Group, Category, SubCategory, 
    ProductGroup, ProductCategory, ProductSubCategory
)


class MarketFeeRangeFilter(SimpleListFilter):
    """Custom filter for market fee ranges"""
    title = _('Market Fee Range')
    parameter_name = 'market_fee_range'

    def lookups(self, request, model_admin):
        return (
            ('0', _('Free (0)')),
            ('1-1000', _('1 - 1,000')),
            ('1001-10000', _('1,001 - 10,000')),
            ('10001-100000', _('10,001 - 100,000')),
            ('100001+', _('100,001+')),
        )

    def queryset(self, request, queryset):
        if self.value() == '0':
            return queryset.filter(market_fee=0)
        elif self.value() == '1-1000':
            return queryset.filter(market_fee__gte=1, market_fee__lte=1000)
        elif self.value() == '1001-10000':
            return queryset.filter(market_fee__gte=1001, market_fee__lte=10000)
        elif self.value() == '10001-100000':
            return queryset.filter(market_fee__gte=10001, market_fee__lte=100000)
        elif self.value() == '100001+':
            return queryset.filter(market_fee__gte=100001)
        return queryset


class CategoryInline(admin.TabularInline):
    """Inline admin for Category"""
    model = Category
    extra = 0
    fields = ('name', 'market_fee', 'is_active')
    readonly_fields = ('created_at', 'updated_at')
    show_change_link = True


class SubCategoryInline(admin.TabularInline):
    """Inline admin for SubCategory"""
    model = SubCategory
    extra = 0
    fields = ('name', 'market_fee', 'is_active')
    readonly_fields = ('created_at', 'updated_at')
    show_change_link = True


class ProductGroupInline(admin.TabularInline):
    """Inline admin for ProductGroup"""
    model = ProductGroup
    extra = 0
    fields = ('name', 'is_active')
    readonly_fields = ('created_at', 'updated_at')
    show_change_link = True


class ProductCategoryInline(admin.TabularInline):
    """Inline admin for ProductCategory"""
    model = ProductCategory
    extra = 0
    fields = ('name', 'is_active')
    readonly_fields = ('created_at', 'updated_at')
    show_change_link = True


class ProductSubCategoryInline(admin.TabularInline):
    """Inline admin for ProductSubCategory"""
    model = ProductSubCategory
    extra = 0
    fields = ('name', 'is_active')
    readonly_fields = ('created_at', 'updated_at')
    show_change_link = True


@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    """Admin configuration for Group model"""
    
    list_display = (
        'name', 'market_fee_display', 'categories_count', 
        'has_slider', 'is_active', 'created_at'
    )
    list_filter = (MarketFeeRangeFilter, 'is_active', 'created_at')
    search_fields = ('name', 'description')
    
    fieldsets = (
        (_('Basic Information'), {
            'fields': (
                'name',
                'description',
                'is_active',
            )
        }),
        (_('Market Configuration'), {
            'fields': (
                'market_fee',
                ('market_slider_img', 'market_slider_url'),
            )
        }),
        (_('Timestamps'), {
            'fields': (('created_at', 'updated_at'),),
            'classes': ('collapse',),
        }),
    )
    
    readonly_fields = ('created_at', 'updated_at', 'categories_count_display')
    inlines = [CategoryInline, ProductGroupInline]
    
    actions = ['activate_groups', 'deactivate_groups', 'reset_market_fee']
    
    def get_queryset(self, request):
        """Optimize queryset with annotations"""
        queryset = super().get_queryset(request)
        return queryset.annotate(
            categories_count=Count('categories'),
            total_market_fee=Sum('categories__market_fee')
        )
    
    def market_fee_display(self, obj):
        """Display market fee with formatting"""
        if obj.market_fee == 0:
            return format_html('<span style="color: green; font-weight: bold;">Free</span>')
        elif obj.market_fee < 1000:
            return format_html('<span style="color: blue;">{:,.0f}</span>', obj.market_fee)
        else:
            return format_html('<span style="color: red; font-weight: bold;">{:,.0f}</span>', obj.market_fee)
    market_fee_display.short_description = _('Market Fee')
    market_fee_display.admin_order_field = 'market_fee'
    
    def categories_count(self, obj):
        """Display number of categories"""
        return obj.categories_count
    categories_count.short_description = _('Categories')
    categories_count.admin_order_field = 'categories_count'
    
    def has_slider(self, obj):
        """Check if group has slider image or URL"""
        return bool(obj.market_slider_img or obj.market_slider_url)
    has_slider.boolean = True
    has_slider.short_description = _('Has Slider')
    
    def categories_count_display(self, obj):
        """Detailed categories count for readonly field"""
        return f"Total Categories: {obj.categories_count}"
    categories_count_display.short_description = _('Categories Count')
    
    def activate_groups(self, request, queryset):
        """Bulk action to activate groups"""
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} groups were successfully activated.')
    activate_groups.short_description = _('Activate selected groups')
    
    def deactivate_groups(self, request, queryset):
        """Bulk action to deactivate groups"""
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} groups were successfully deactivated.')
    deactivate_groups.short_description = _('Deactivate selected groups')
    
    def reset_market_fee(self, request, queryset):
        """Bulk action to reset market fee to 0"""
        updated = queryset.update(market_fee=0)
        self.message_user(request, f'Market fee reset to 0 for {updated} groups.')
    reset_market_fee.short_description = _('Reset market fee to 0')


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    """Admin configuration for Category model"""
    
    list_display = (
        'name', 'group', 'market_fee_display', 'subcategories_count',
        'has_slider', 'is_active', 'created_at'
    )
    list_filter = ('group', MarketFeeRangeFilter, 'is_active', 'created_at')
    search_fields = ('name', 'description', 'group__name')
    
    fieldsets = (
        (_('Basic Information'), {
            'fields': (
                'name',
                'group',
                'description',
                'is_active',
            )
        }),
        (_('Market Configuration'), {
            'fields': (
                'market_fee',
                ('market_slider_img', 'market_slider_url'),
            )
        }),
        (_('Timestamps'), {
            'fields': (('created_at', 'updated_at'),),
            'classes': ('collapse',),
        }),
    )
    
    readonly_fields = ('created_at', 'updated_at')
    inlines = [SubCategoryInline]
    
    actions = ['activate_categories', 'deactivate_categories', 'copy_group_fee']
    
    def get_queryset(self, request):
        """Optimize queryset with annotations"""
        queryset = super().get_queryset(request)
        return queryset.select_related('group').annotate(
            subcategories_count=Count('subcategories')
        )
    
    def market_fee_display(self, obj):
        """Display market fee with formatting"""
        if obj.market_fee == 0:
            return format_html('<span style="color: green; font-weight: bold;">Free</span>')
        elif obj.market_fee < 1000:
            return format_html('<span style="color: blue;">{:,.0f}</span>', obj.market_fee)
        else:
            return format_html('<span style="color: red; font-weight: bold;">{:,.0f}</span>', obj.market_fee)
    market_fee_display.short_description = _('Market Fee')
    market_fee_display.admin_order_field = 'market_fee'
    
    def subcategories_count(self, obj):
        """Display number of subcategories"""
        return obj.subcategories_count
    subcategories_count.short_description = _('SubCategories')
    subcategories_count.admin_order_field = 'subcategories_count'
    
    def has_slider(self, obj):
        """Check if category has slider image or URL"""
        return bool(obj.market_slider_img or obj.market_slider_url)
    has_slider.boolean = True
    has_slider.short_description = _('Has Slider')
    
    def activate_categories(self, request, queryset):
        """Bulk action to activate categories"""
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} categories were successfully activated.')
    activate_categories.short_description = _('Activate selected categories')
    
    def deactivate_categories(self, request, queryset):
        """Bulk action to deactivate categories"""
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} categories were successfully deactivated.')
    deactivate_categories.short_description = _('Deactivate selected categories')
    
    def copy_group_fee(self, request, queryset):
        """Bulk action to copy group fee to categories"""
        updated = 0
        for category in queryset:
            category.market_fee = category.group.market_fee
            category.save()
            updated += 1
        self.message_user(request, f'Group fee copied to {updated} categories.')
    copy_group_fee.short_description = _('Copy group fee to categories')


@admin.register(SubCategory)
class SubCategoryAdmin(admin.ModelAdmin):
    """Admin configuration for SubCategory model"""
    
    list_display = (
        'name', 'category', 'group_name', 'market_fee_display',
        'markets_count', 'has_slider', 'is_active', 'created_at'
    )
    list_filter = ('category__group', 'category', MarketFeeRangeFilter, 'is_active', 'created_at')
    search_fields = ('name', 'description', 'category__name', 'category__group__name')
    
    fieldsets = (
        (_('Basic Information'), {
            'fields': (
                'name',
                'category',
                'description',
                'is_active',
            )
        }),
        (_('Market Configuration'), {
            'fields': (
                'market_fee',
                ('market_slider_img', 'market_slider_url'),
            )
        }),
        (_('Timestamps'), {
            'fields': (('created_at', 'updated_at'),),
            'classes': ('collapse',),
        }),
    )
    
    readonly_fields = ('created_at', 'updated_at')
    
    actions = ['activate_subcategories', 'deactivate_subcategories', 'copy_category_fee']
    
    def get_queryset(self, request):
        """Optimize queryset with annotations"""
        queryset = super().get_queryset(request)
        return queryset.select_related('category__group').annotate(
            markets_count=Count('markets')
        )
    
    def group_name(self, obj):
        """Display group name"""
        return obj.category.group.name
    group_name.short_description = _('Group')
    group_name.admin_order_field = 'category__group__name'
    
    def market_fee_display(self, obj):
        """Display market fee with formatting"""
        if obj.market_fee == 0:
            return format_html('<span style="color: green; font-weight: bold;">Free</span>')
        elif obj.market_fee < 1000:
            return format_html('<span style="color: blue;">{:,.0f}</span>', obj.market_fee)
        else:
            return format_html('<span style="color: red; font-weight: bold;">{:,.0f}</span>', obj.market_fee)
    market_fee_display.short_description = _('Market Fee')
    market_fee_display.admin_order_field = 'market_fee'
    
    def markets_count(self, obj):
        """Display number of markets using this subcategory"""
        return obj.markets_count
    markets_count.short_description = _('Markets')
    markets_count.admin_order_field = 'markets_count'
    
    def has_slider(self, obj):
        """Check if subcategory has slider image or URL"""
        return bool(obj.market_slider_img or obj.market_slider_url)
    has_slider.boolean = True
    has_slider.short_description = _('Has Slider')
    
    def activate_subcategories(self, request, queryset):
        """Bulk action to activate subcategories"""
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} subcategories were successfully activated.')
    activate_subcategories.short_description = _('Activate selected subcategories')
    
    def deactivate_subcategories(self, request, queryset):
        """Bulk action to deactivate subcategories"""
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} subcategories were successfully deactivated.')
    deactivate_subcategories.short_description = _('Deactivate selected subcategories')
    
    def copy_category_fee(self, request, queryset):
        """Bulk action to copy category fee to subcategories"""
        updated = 0
        for subcategory in queryset:
            subcategory.market_fee = subcategory.category.market_fee
            subcategory.save()
            updated += 1
        self.message_user(request, f'Category fee copied to {updated} subcategories.')
    copy_category_fee.short_description = _('Copy category fee to subcategories')


@admin.register(ProductGroup)
class ProductGroupAdmin(admin.ModelAdmin):
    """Admin configuration for ProductGroup model"""
    
    list_display = ('name', 'group', 'product_categories_count', 'is_active', 'created_at')
    list_filter = ('group', 'is_active', 'created_at')
    search_fields = ('name', 'description', 'group__name')
    
    fieldsets = (
        (_('Basic Information'), {
            'fields': (
                'name',
                'group',
                'description',
                'is_active',
            )
        }),
        (_('Timestamps'), {
            'fields': (('created_at', 'updated_at'),),
            'classes': ('collapse',),
        }),
    )
    
    readonly_fields = ('created_at', 'updated_at')
    inlines = [ProductCategoryInline]
    
    def get_queryset(self, request):
        """Optimize queryset with annotations"""
        queryset = super().get_queryset(request)
        return queryset.select_related('group').annotate(
            product_categories_count=Count('product_categories')
        )
    
    def product_categories_count(self, obj):
        """Display number of product categories"""
        return obj.product_categories_count
    product_categories_count.short_description = _('Product Categories')
    product_categories_count.admin_order_field = 'product_categories_count'


@admin.register(ProductCategory)
class ProductCategoryAdmin(admin.ModelAdmin):
    """Admin configuration for ProductCategory model"""
    
    list_display = ('name', 'product_group', 'group_name', 'product_subcategories_count', 'is_active', 'created_at')
    list_filter = ('product_group__group', 'product_group', 'is_active', 'created_at')
    search_fields = ('name', 'description', 'product_group__name', 'product_group__group__name')
    
    fieldsets = (
        (_('Basic Information'), {
            'fields': (
                'name',
                'product_group',
                'description',
                'is_active',
            )
        }),
        (_('Timestamps'), {
            'fields': (('created_at', 'updated_at'),),
            'classes': ('collapse',),
        }),
    )
    
    readonly_fields = ('created_at', 'updated_at')
    inlines = [ProductSubCategoryInline]
    
    def get_queryset(self, request):
        """Optimize queryset with annotations"""
        queryset = super().get_queryset(request)
        return queryset.select_related('product_group__group').annotate(
            product_subcategories_count=Count('product_subcategories')
        )
    
    def group_name(self, obj):
        """Display group name"""
        return obj.product_group.group.name
    group_name.short_description = _('Group')
    group_name.admin_order_field = 'product_group__group__name'
    
    def product_subcategories_count(self, obj):
        """Display number of product subcategories"""
        return obj.product_subcategories_count
    product_subcategories_count.short_description = _('Product SubCategories')
    product_subcategories_count.admin_order_field = 'product_subcategories_count'


@admin.register(ProductSubCategory)
class ProductSubCategoryAdmin(admin.ModelAdmin):
    """Admin configuration for ProductSubCategory model"""
    
    list_display = ('name', 'product_category', 'product_group_name', 'group_name', 'is_active', 'created_at')
    list_filter = ('product_category__product_group__group', 'product_category__product_group', 'product_category', 'is_active', 'created_at')
    search_fields = ('name', 'description', 'product_category__name', 'product_category__product_group__name')
    
    fieldsets = (
        (_('Basic Information'), {
            'fields': (
                'name',
                'product_category',
                'description',
                'is_active',
            )
        }),
        (_('Timestamps'), {
            'fields': (('created_at', 'updated_at'),),
            'classes': ('collapse',),
        }),
    )
    
    readonly_fields = ('created_at', 'updated_at')
    
    def get_queryset(self, request):
        """Optimize queryset with select_related"""
        queryset = super().get_queryset(request)
        return queryset.select_related('product_category__product_group__group')
    
    def product_group_name(self, obj):
        """Display product group name"""
        return obj.product_category.product_group.name
    product_group_name.short_description = _('Product Group')
    product_group_name.admin_order_field = 'product_category__product_group__name'
    
    def group_name(self, obj):
        """Display group name"""
        return obj.product_category.product_group.group.name
    group_name.short_description = _('Group')
    group_name.admin_order_field = 'product_category__product_group__group__name'
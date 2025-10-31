from apps.base.admin import admin, BaseAdmin, BaseTabularInline

from .models import(
    Group, Category, SubCategory,
    ProductGroup, ProductCategory, ProductSubCategory
)

# Register your models here.

class SubCategoryTabularInline(BaseTabularInline):
    model = SubCategory

    fields = (
        'title',
        'market_fee',
        'market_slider_img',
        'market_slider_url',
    )

    # اضافه شده: Validation
    def get_formset(self, request, obj=None, **kwargs):
        formset = super().get_formset(request, obj, **kwargs)
        formset.form.base_fields['market_fee'].help_text = 'مبلغ حق اشتراک به تومان'
        return formset


class CategoryAdmin(BaseAdmin):
    inlines = [
        SubCategoryTabularInline,
    ]

    # اصلاح شده: اضافه کردن market_fee
    list_display = [
        'title',
        'group',
        'market_fee',  # اضافه شده
    ]

    # اضافه شده: فیلترها
    list_filter = [
        'group',
        'market_fee',  # اضافه شده
    ]

    # اضافه شده: جستجو
    search_fields = [
        'title',
        'market_fee',  # اضافه شده
    ]

    fields = (
        'group',
        'title',
        'market_fee',
        'market_slider_img',
        'market_slider_url',
    ) + BaseAdmin.fields

    readonly_fields = BaseAdmin.readonly_fields


admin.site.register(Category, CategoryAdmin)


class GroupAdmin(BaseAdmin):
    # اصلاح شده: اضافه کردن market_fee
    list_display = [
        'title',
        'market_fee',  # اضافه شده
    ]

    # اضافه شده: فیلترها
    list_filter = [
        'market_fee',  # اضافه شده
    ]

    # اضافه شده: جستجو
    search_fields = [
        'title',
        'market_fee',  # اضافه شده
    ]

    fields = (
        'title', 
        'market_fee', 
        'market_slider_img', 
        'market_slider_url'
    ) + BaseAdmin.fields

    readonly_fields = BaseAdmin.readonly_fields


admin.site.register(Group, GroupAdmin)


# اضافه شده: Custom Admin برای مدیریت حق اشتراک
class MarketFeeAdmin(BaseAdmin):
    list_display = [
        'title',
        'market_fee',
        'fee_status',
    ]
    
    list_filter = [
        'market_fee',
        'fee_status',
    ]
    
    search_fields = [
        'title',
        'market_fee',
    ]
    
    def fee_status(self, obj):
        if obj.market_fee > 0:
            return 'فعال'
        return 'غیرفعال'
    fee_status.short_description = 'وضعیت حق اشتراک'


class ProductGroupAdmin(BaseAdmin):
    list_display = [
        'sub_category'
    ]

    fields = (
     'sub_category', 
    ) + BaseAdmin.fields

    readonly_fields = BaseAdmin.readonly_fields


class ProductSubCategoryTabularInline(BaseTabularInline):
    model = ProductSubCategory

    fields = (
        'title',
    )

class ProductCategoryAdmin(BaseAdmin):
    inlines = [
        ProductSubCategoryTabularInline,
    ]

    list_display = [
        'title',
        'product_group',
    ]
    fields = (
        'product_group',
        'title',
    ) + BaseAdmin.fields

    readonly_fields = BaseAdmin.readonly_fields

admin.site.register(ProductCategory, ProductCategoryAdmin)
admin.site.register(ProductGroup, ProductGroupAdmin)

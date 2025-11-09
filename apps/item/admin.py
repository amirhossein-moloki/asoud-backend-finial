from apps.base.admin import admin, BaseAdmin, BaseTabularInline

from .models import (
    Item,
    ItemImage,
    ItemKeyword,
    ItemDiscount,
    ItemTheme,
    ItemShipping,
)

# Register your models here.


class ItemImageTabularInline(BaseTabularInline):
    model = ItemImage

    fields = (
        'image',
    ) + BaseTabularInline.fields

    readonly_fields = BaseTabularInline.readonly_fields


class ItemDiscountTabularInline(BaseTabularInline):
    model = ItemDiscount

    fields = (
        'discount_value',
        'discount_type',
    )


class ItemAdmin(BaseAdmin):
    inlines = [
        ItemImageTabularInline,
        ItemDiscountTabularInline,
    ]

    list_display = [
        'name'
    ]

    fields = (
        'item_type',
        'name',
        'description',
        'technical_specs',
        'subcategory',
        'keywords',
        'main_image',
        'additional_images',
        'base_price',
        'stock_quantity',
        'shipping_payment_type',
        'shipping_cost',
        'requires_appointment',
        'appointment_duration',
        'available_slots',
        'is_advertisement',
        'sell_via_marketer',
        'commission_percentage',
        'related_item',
        'status',
        'label',
        'sell_type',
    ) + BaseAdmin.fields

    readonly_fields = BaseAdmin.readonly_fields


admin.site.register(Item, ItemAdmin)
class ItemShipAdmin(BaseAdmin):
    list_display = ('id', 'shipping_cost', 'shipping_type')
admin.site.register(ItemShipping, ItemShipAdmin)

class ItemKeywordAdmin(BaseAdmin):
    list_display = [
        'name',
    ]

    fields = (
        'name',
    ) + BaseAdmin.fields

    readonly_fields = BaseAdmin.readonly_fields


admin.site.register(ItemKeyword, ItemKeywordAdmin)


class ItemThemeAdmin(BaseAdmin):
    list_display = [
        'name',
    ]

    fields = (
        'name',
        'item',
    ) + BaseAdmin.fields

    readonly_fields = BaseAdmin.readonly_fields


admin.site.register(ItemTheme, ItemThemeAdmin)

from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.base.models import BaseModel
from .item import Item


class ItemDiscount(BaseModel):
    item = models.ForeignKey(Item, on_delete=models.CASCADE, related_name='discounts')
    discount_value = models.DecimalField(max_digits=5, decimal_places=2)
    discount_type = models.CharField(max_length=10, choices=Item.DISCOUNT_CHOICES)

    class Meta:
        db_table = 'item_discount'
        verbose_name = _('Item Discount')
        verbose_name_plural = _('Item Discounts')
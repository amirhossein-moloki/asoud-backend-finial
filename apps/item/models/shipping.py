from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.base.models import BaseModel
from .item import Item


class ItemShipping(BaseModel):
    item = models.ForeignKey(Item, on_delete=models.CASCADE, related_name='shipping_options')
    shipping_cost = models.DecimalField(max_digits=10, decimal_places=2)
    shipping_type = models.CharField(max_length=10, choices=Item.SHIP_COST_PAY_TYPE_CHOICES)

    class Meta:
        db_table = 'item_shipping'
        verbose_name = _('Item Shipping')
        verbose_name_plural = _('Item Shipping Options')
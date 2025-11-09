from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.base.models import BaseModel
from .item import Item


class ItemTheme(BaseModel):
    item = models.ForeignKey(Item, on_delete=models.CASCADE, related_name='themes')
    name = models.CharField(max_length=100)

    class Meta:
        db_table = 'item_theme'
        verbose_name = _('Item Theme')
        verbose_name_plural = _('Item Themes')
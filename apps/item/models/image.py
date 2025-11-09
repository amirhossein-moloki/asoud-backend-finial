from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.base.models import BaseModel
from .item import Item


class ItemImage(BaseModel):
    item = models.ForeignKey(Item, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='item_images/')

    class Meta:
        db_table = 'item_image'
        verbose_name = _('Item Image')
        verbose_name_plural = _('Item Images')
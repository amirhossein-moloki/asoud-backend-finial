from django.db import models
from django.utils.translation import gettext_lazy as _

class ItemKeyword(models.Model):
    """Model for item keywords"""
    name = models.CharField(max_length=255, unique=True, verbose_name=_("Name"))

    class Meta:
        db_table = 'item_keyword'
        verbose_name = _('Item Keyword')
        verbose_name_plural = _('Item Keywords')

    def __str__(self):
        return self.name
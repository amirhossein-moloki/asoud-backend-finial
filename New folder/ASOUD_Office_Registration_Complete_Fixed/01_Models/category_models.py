from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator, MaxValueValidator
from .validators import validate_market_fee

from apps.base.models import models, BaseModel

# Create your models here.

class Group(BaseModel):
    title = models.CharField(
        max_length=255,
        verbose_name=_('Title'),
    )
    
    # اصلاح شده: اضافه کردن validation
    market_fee = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        validators=[validate_market_fee],
        verbose_name=_('Market fee'),
        help_text=_('Fee for this category in the market'),
    )
    
    market_slider_img = models.ImageField(
        upload_to='market/admin/',
        blank=True,
        null=True,
        verbose_name=_('Market slider image'),
        help_text=_('This image is not visible to owners.'),
    )

    market_slider_url = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name=_('Market slider url'),
    )

    class Meta:
        db_table = 'group'
        verbose_name = _('Group')
        verbose_name_plural = _('Groups')

    def __str__(self):
        return self.title


class Category(BaseModel):
    group = models.ForeignKey(
        Group,
        on_delete=models.CASCADE,
        verbose_name=_('Group')
    )

    title = models.CharField(
        max_length=255,
        verbose_name=_('Title'),
    )

    # اصلاح شده: اضافه کردن validation
    market_fee = models.DecimalField(
        max_digits=14,
        decimal_places=3,
        validators=[
            MinValueValidator(0, message='مبلغ نمی‌تواند منفی باشد'),
            MaxValueValidator(999999999999, message='مبلغ نمی‌تواند بیش از 999 میلیارد باشد'),
        ],
        verbose_name=_('Market Fee'),
        help_text=_('Fee to be paid by the market owner for this category.'),
    )

    market_slider_img = models.ImageField(
        upload_to='market/admin/',
        blank=True,
        null=True,
        verbose_name=_('Market slider image'),
        help_text=_('This image is not visible to owners.'),
    )

    market_slider_url = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name=_('Market slider url'),
    )

    class Meta:
        db_table = 'category'
        verbose_name = _('Category')
        verbose_name_plural = _('Categories')

    def __str__(self):
        return self.title


class SubCategory(BaseModel):
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        verbose_name=_('Category'),
    )

    title = models.CharField(
        max_length=255,
        verbose_name=_('Title'),
    )

    # اصلاح شده: اضافه کردن validation
    market_fee = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        validators=[validate_market_fee],
        verbose_name=_('Market fee'),
        help_text=_('Fee for this subcategory in the market'),
    )

    market_slider_img = models.ImageField(
        upload_to='market/admin/',
        blank=True,
        null=True,
        verbose_name=_('Market slider image'),
        help_text=_('This image is not visible to owners.'),
    )

    market_slider_url = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name=_('Market slider url'),
    )

    class Meta:
        db_table = 'sub_category'
        verbose_name = _('Sub Category')
        verbose_name_plural = _('Sub Categories')

    def __str__(self):
        return self.title


class ProductGroup(BaseModel):
    sub_category = models.ForeignKey(
        SubCategory,
        on_delete=models.CASCADE,
        verbose_name=_('Sub Category'),
    )

    class Meta:
        db_table = 'product_group'
        verbose_name = _('Product Group')
        verbose_name_plural = _('product Groups')

    def __str__(self):
        return self.sub_category.title
    

class ProductCategory(BaseModel):
    product_group = models.ForeignKey(
        ProductGroup,
        on_delete=models.CASCADE,
        verbose_name=_('Product Group')
    )
    title = models.CharField(
        max_length=255,
        verbose_name=_('Title'),
    )
    class Meta:
        db_table = 'product_category'
        verbose_name = _('Product Category')
        verbose_name_plural = _('product Categories')

    def __str__(self):
        return self.title
    
class ProductSubCategory(BaseModel):
    product_category = models.ForeignKey(
        ProductCategory,
        on_delete=models.CASCADE,
        verbose_name=_('Product Category'),
    )

    title = models.CharField(
        max_length=255,
        verbose_name=_('Title'),
    )

    class Meta:
        db_table = 'product_subcategory'
        verbose_name = _('Product Sub Category')
        verbose_name_plural = _('product sub categories')

    def __str__(self):
        return self.title

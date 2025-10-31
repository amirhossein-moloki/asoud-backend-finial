from rest_framework import serializers
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError as DjangoValidationError

# Import models with correct paths
try:
    from ..models.category_models import Group, Category, SubCategory, ProductGroup, ProductCategory, ProductSubCategory
except ImportError:
    try:
        from .models import Group, Category, SubCategory, ProductGroup, ProductCategory, ProductSubCategory
    except ImportError:
        Group = Category = SubCategory = None
        ProductGroup = ProductCategory = ProductSubCategory = None

# Import validators with fallback
try:
    from ..validators.validators import validate_market_fee
except ImportError:
    try:
        from .validators import validate_market_fee
    except ImportError:
        def validate_market_fee(value):
            if value < 0:
                raise DjangoValidationError(_('Market fee cannot be negative'))
            return value


class GroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = Group
        fields = ['id', 'title', 'market_fee', 'market_slider_img', 'market_slider_url']


class CategorySerializer(serializers.ModelSerializer):
    group = GroupSerializer(read_only=True)
    group_id = serializers.IntegerField(write_only=True)
    
    class Meta:
        model = Category
        fields = ['id', 'title', 'market_fee', 'market_slider_img', 'market_slider_url', 'group', 'group_id']


class SubCategorySerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    category_id = serializers.IntegerField(write_only=True)
    
    class Meta:
        model = SubCategory
        fields = ['id', 'title', 'market_fee', 'market_slider_img', 'market_slider_url', 'category', 'category_id']


class ProductGroupSerializer(serializers.ModelSerializer):
    sub_category = SubCategorySerializer(read_only=True)
    sub_category_id = serializers.IntegerField(write_only=True)
    
    class Meta:
        model = ProductGroup
        fields = ['id', 'sub_category', 'sub_category_id']


class ProductCategorySerializer(serializers.ModelSerializer):
    product_group = ProductGroupSerializer(read_only=True)
    product_group_id = serializers.IntegerField(write_only=True)
    
    class Meta:
        model = ProductCategory
        fields = ['id', 'title', 'product_group', 'product_group_id']


class ProductSubCategorySerializer(serializers.ModelSerializer):
    product_category = ProductCategorySerializer(read_only=True)
    product_category_id = serializers.IntegerField(write_only=True)
    
    class Meta:
        model = ProductSubCategory
        fields = ['id', 'title', 'product_category', 'product_category_id']


# اضافه شده: Serializer برای مدیریت حق اشتراک
class MarketFeeUpdateSerializer(serializers.Serializer):
    market_fee = serializers.DecimalField(
        max_digits=14,
        decimal_places=3,
        help_text='مبلغ حق اشتراک به تومان'
    )
    
    def validate_market_fee(self, value):
        if value < 0:
            raise serializers.ValidationError('مبلغ نمی‌تواند منفی باشد')
        if value > 999999999999:
            raise serializers.ValidationError('مبلغ نمی‌تواند بیش از 999 میلیارد باشد')
        return value


class MarketFeeListSerializer(serializers.Serializer):
    model_type = serializers.ChoiceField(
        choices=[
            ('group', 'گروه'),
            ('category', 'دسته'),
            ('subcategory', 'زیردسته'),
        ]
    )
    
    def get_queryset(self, model_type):
        if model_type == 'group':
            return Group.objects.all()
        elif model_type == 'category':
            return Category.objects.all()
        elif model_type == 'subcategory':
            return SubCategory.objects.all()
        return None

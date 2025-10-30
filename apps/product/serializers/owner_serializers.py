from rest_framework import serializers
from django.urls import reverse

from apps.users.models import User
from apps.product.models import (
    Product,
    ProductShipping,
    ProductDiscount,
    ProductTheme,
    ProductKeyword,
    ProductImage,
)

class KeywordField(serializers.RelatedField):

    def to_representation(self, value):
        return value.name

    def to_internal_value(self, data):
        keyword_obj, created = ProductKeyword.objects.get_or_create(name=data.strip())
        return keyword_obj
    
class UserField(serializers.RelatedField):
    def to_representation(self, value):
        return value.id

    def to_internal_value(self, data):
        try:
            return User.objects.get(id=data)
        except User.DoesNotExist:
            raise serializers.ValidationError(f"User with ID {data} does not exist.")


class ProductImageSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(read_only=True)

    class Meta:
        model = ProductImage
        fields = [
            'id',
            'image'
        ]


class ProductCreateSerializer(serializers.ModelSerializer):
    keywords = KeywordField(
        many=True,
        queryset=ProductKeyword.objects.all(),
        required=False
    )
    type = serializers.ChoiceField(
        choices=Product.TYPE_CHOICES,
    )
    tag = serializers.ChoiceField(
        choices=Product.TAG_CHOICES,
        default=Product.NONE,
    )
    tag_position = serializers.ChoiceField(
        choices=Product.TAG_POSITION_CHOICES,
        default=Product.TOP_LEFT,
    )
    sell_type = serializers.ChoiceField(
        choices=Product.SELL_TYPE_CHOICES,
        default=Product.ONLINE,
    )
    ship_cost_pay_type = serializers.ChoiceField(
        choices=Product.SHIP_COST_PAY_TYPE_CHOICES,
    )
    uploaded_images = serializers.ListField(
        child=serializers.ImageField(allow_empty_file=False), 
        required=False,
        write_only=True
    )

    class Meta:
        model = Product
        fields = [
            'market',
            'type',
            'name',
            'description',
            'technical_detail',
            'sub_category',
            'keywords',
            'stock',
            'main_price',
            'colleague_price',
            'marketer_price',
            'maximum_sell_price',
            'required_product',
            'gift_product',
            'is_marketer',
            'is_requirement',
            'status',
            'tag',
            'tag_position',
            'sell_type',
            # 'ship_cost',
            'ship_cost_pay_type',
            'uploaded_images',
        ]

    def create(self, validated_data):
        # remove images 
        images = validated_data.pop('uploaded_images', [])

        keywords_data = validated_data.pop('keywords', [])
        product = Product.objects.create(**validated_data)

        product.keywords.set(keywords_data)
        
        for image in images:
            _ = ProductImage.objects.create(
                product=product,
                image=image
            )

        return product

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        # Add existing images to response
        representation['images'] = [
            {'id': img.id, 'image': img.image.url} 
            for img in instance.images.all()  # Uses related_name
        ]
        return representation


class ProductShippingCreateSerializer(serializers.ModelSerializer):
    product = serializers.UUIDField(read_only=True)
    class Meta:
        model = ProductShipping
        fields = ('product', 'name', 'price', )

class ProductShipListSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductShipping
        fields = ('product','name', 'price', )
        
class ProductDiscountCreateSerializer(serializers.ModelSerializer):
    users = UserField(
        many=True,
        queryset=User.objects.all(),
        required=False
    )
    position = serializers.ChoiceField(choices=ProductDiscount.POSITION_CHOICES)

    class Meta:
        model = ProductDiscount
        fields = [
            'users',
            'position',
            'percentage',
            'duration',
        ]

    def create(self, validated_data):
        users_data = validated_data.pop('users', [])
        discount = ProductDiscount.objects.create(**validated_data)

        if users_data:
            discount.users.set(users_data)
        return discount


class ProductListSerializer(serializers.ModelSerializer):
    images = ProductImageSerializer(many=True)
    class Meta:
        model = Product
        fields = [
            'id',
            'name',
            'description',
            'main_price',
            'stock',
            'images',
        ]

class ProductWithIndexListSerializer(serializers.ModelSerializer):
    images = ProductImageSerializer(many=True)
    class Meta:
        model = Product
        fields = [
            'id',
            'name',
            'description',
            'main_price',
            'stock',
            'images',
            'theme_index',
        ]

class ProductDetailSerializer(serializers.ModelSerializer):
    required_product = ProductListSerializer(read_only=True)
    gift_product = ProductListSerializer(read_only=True)
    keywords = KeywordField(many=True, read_only=True)
    images = ProductImageSerializer(many=True, read_only=True)
    
    # Handle shipping cost
    shipping_cost = serializers.SerializerMethodField()
    
    # Handle discounts
    active_discounts = serializers.SerializerMethodField()
    
    # Handle comments count (since GenericRelation might be complex)
    comments_count = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            'id',
            'name',
            'description',
            'technical_detail',
            'keywords',
            'stock',
            'main_price',
            'colleague_price',
            'marketer_price',
            'maximum_sell_price',
            'required_product',
            'gift_product',
            'is_marketer',
            'marketer_price',
            'tag',
            'tag_position',
            'sell_type',
            'ship_cost_pay_type',
            'shipping_cost',
            'images',
            'active_discounts',
            'comments_count',
            'status',
            'created_at',
            'updated_at',
        ]

    def get_shipping_cost(self, obj):
        """Get shipping cost information"""
        try:
            shipping_options = obj.shipping_options.all()
            return [
                {
                    'id': option.id,
                    'name': option.name,
                    'price': option.price
                }
                for option in shipping_options
            ]
        except:
            return []

    def get_active_discounts(self, obj):
        """Get active discount information"""
        try:
            from django.utils import timezone
            active_discounts = obj.discounts.filter(
                duration__gte=timezone.now()
            )
            return [
                {
                    'id': discount.id,
                    'percentage': discount.percentage,
                    'position': discount.position,
                    'duration': discount.duration
                }
                for discount in active_discounts
            ]
        except:
            return []

    def get_comments_count(self, obj):
        """Get comments count for the product"""
        try:
            # Assuming you have a comment model with GenericForeignKey
            from django.contrib.contenttypes.models import ContentType
            content_type = ContentType.objects.get_for_model(obj)
            # You might need to adjust this based on your actual comment model
            # from apps.comment.models import Comment
            # return Comment.objects.filter(
            #     content_type=content_type,
            #     object_id=obj.id
            # ).count()
            return 0  # Placeholder until comment model is properly implemented
        except:
            return 0

class ProductThemeListSerializer(serializers.ModelSerializer):
    products = serializers.SerializerMethodField()

    class Meta:
        model = ProductTheme
        fields = [
            'id',
            'name',
            'order',
            'products',
        ]

    def get_products(self, obj):
        products = obj.products.all()
        return ProductWithIndexListSerializer(products, many=True, context=self.context).data


class ProductThemeCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductTheme
        fields = [
            'name',
            'order',
        ]

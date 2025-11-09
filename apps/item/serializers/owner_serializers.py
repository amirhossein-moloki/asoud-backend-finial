from rest_framework import serializers
from django.urls import reverse

from apps.users.models import User
from apps.item.models import (
    Item,
    ItemImage,
    ItemKeyword,
    ItemTheme,
    ItemDiscount,
    ItemShipping,
)

class KeywordField(serializers.RelatedField):

    def to_representation(self, value):
        return value.name

    def to_internal_value(self, data):
        keyword_obj, created = ItemKeyword.objects.get_or_create(name=data.strip())
        return keyword_obj
    
class UserField(serializers.RelatedField):
    def to_representation(self, value):
        return value.id

    def to_internal_value(self, data):
        try:
            return User.objects.get(id=data)
        except User.DoesNotExist:
            raise serializers.ValidationError(f"User with ID {data} does not exist.")


class ItemImageSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(read_only=True)

    class Meta:
        model = ItemImage
        fields = [
            'id',
            'image'
        ]


class ItemCreateSerializer(serializers.ModelSerializer):
    keywords = KeywordField(
        many=True,
        queryset=ItemKeyword.objects.all(),
        required=False
    )
    type = serializers.ChoiceField(
        choices=Item.ITEM_TYPE_CHOICES,
    )
    tag = serializers.ChoiceField(
        choices=Item.LABEL_CHOICES,
        default=Item.NONE,
    )
    sell_type = serializers.ChoiceField(
        choices=Item.SELL_TYPE_CHOICES,
        default=Item.ONLINE,
    )
    ship_cost_pay_type = serializers.ChoiceField(
        choices=Item.SHIP_COST_PAY_TYPE_CHOICES,
    )
    uploaded_images = serializers.ListField(
        child=serializers.ImageField(allow_empty_file=False), 
        required=False,
        write_only=True
    )

    class Meta:
        model = Item
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
            'required_item',
            'gift_item',
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
        item = Item.objects.create(**validated_data)

        item.keywords.set(keywords_data)
        
        for image in images:
            _ = ItemImage.objects.create(
                item=item,
                image=image
            )

        return item

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        # Add existing images to response
        representation['images'] = [
            {'id': img.id, 'image': img.image.url} 
            for img in instance.images.all()  # Uses related_name
        ]
        return representation


class ItemShippingCreateSerializer(serializers.ModelSerializer):
    item = serializers.UUIDField(read_only=True)
    class Meta:
        model = ItemShipping
        fields = ('item', 'name', 'price', )

class ItemShipListSerializer(serializers.ModelSerializer):
    class Meta:
        model = ItemShipping
        fields = ('item','name', 'price', )
        
class ItemDiscountCreateSerializer(serializers.ModelSerializer):
    users = UserField(
        many=True,
        queryset=User.objects.all(),
        required=False
    )

    class Meta:
        model = ItemDiscount
        fields = [
            'users',
            'percentage',
            'duration',
        ]

    def create(self, validated_data):
        users_data = validated_data.pop('users', [])
        discount = ItemDiscount.objects.create(**validated_data)

        if users_data:
            discount.users.set(users_data)
        return discount


class ItemListSerializer(serializers.ModelSerializer):
    images = ItemImageSerializer(many=True)
    class Meta:
        model = Item
        fields = [
            'id',
            'name',
            'description',
            'main_price',
            'stock',
            'images',
        ]

class ItemWithIndexListSerializer(serializers.ModelSerializer):
    images = ItemImageSerializer(many=True)
    class Meta:
        model = Item
        fields = [
            'id',
            'name',
            'description',
            'main_price',
            'stock',
            'images',
            'theme_index',
        ]

class ItemDetailSerializer(serializers.ModelSerializer):
    required_item = ItemListSerializer(read_only=True)
    gift_item = ItemListSerializer(read_only=True)
    keywords = KeywordField(many=True, read_only=True)
    images = ItemImageSerializer(many=True, read_only=True)
    
    # Handle shipping cost
    shipping_cost = serializers.SerializerMethodField()
    
    # Handle discounts
    active_discounts = serializers.SerializerMethodField()
    
    # Handle comments count (since GenericRelation might be complex)
    comments_count = serializers.SerializerMethodField()

    class Meta:
        model = Item
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
            'required_item',
            'gift_item',
            'is_marketer',
            'marketer_price',
            'label',
            'tag_position',
            'sell_type',
            'shipping_payment_type',
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
        """Get comments count for the item"""
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

class ItemThemeListSerializer(serializers.ModelSerializer):
    items = serializers.SerializerMethodField()

    class Meta:
        model = ItemTheme
        fields = [
            'id',
            'name',
            'order',
            'items',
        ]

    def get_items(self, obj):
        items = obj.items.all()
        return ItemWithIndexListSerializer(items, many=True, context=self.context).data


class ItemThemeCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ItemTheme
        fields = [
            'name',
            'order',
        ]

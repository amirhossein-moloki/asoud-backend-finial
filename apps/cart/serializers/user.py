from rest_framework import serializers
from apps.cart.models import (
    Order, 
    OrderItem
)
from apps.product.models import Product, ProductImage
from apps.affiliate.models import AffiliateProduct, AffiliateProductImage
from django.db import transaction


class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ('id', 'image')


class ProductSimpleSerializer(serializers.ModelSerializer):
    images = ProductImageSerializer(many=True, read_only=True)

    class Meta:
        model = Product
        fields = ('id', 'name', 'images')


class AffiliateImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = AffiliateProductImage
        fields = ('id', 'image')


class AffiliateSimpleSerializer(serializers.ModelSerializer):
    images = AffiliateImageSerializer(many=True, read_only=True)

    class Meta:
        model = AffiliateProduct
        fields = ('id', 'name', 'images')

class OrderItem2Serializer(serializers.ModelSerializer):
    product = ProductSimpleSerializer(read_only=True)
    product_name = serializers.CharField(required=False, allow_blank=True)
    product_id = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.all(),
        source='product',  # Maps to the 'product' FK field
        write_only=True,    # Only used for input, not output
        required=False,
        allow_null=True
    )
    affiliate = AffiliateSimpleSerializer(read_only=True)
    affiliate_name = serializers.CharField(required=False, allow_blank=True)
    affiliate_id = serializers.PrimaryKeyRelatedField(
        queryset=AffiliateProduct.objects.all(),
        source='affiliate',
        write_only=True,
        required=False,  # Since affiliate is optional
        allow_null=True  # Allows null in POST data
    )
    class Meta:
        model = OrderItem
        fields = (
            'id',
            'product',
            'product_id',
            'affiliate',
            'affiliate_id',
            'quantity',
            'product_name',
            'affiliate_name'
        )
    
    def save(self, order):
        
        try:
            return super().create(self.validated_data)
        except:
            product_name = self.validated_data.get("product_name", None)
            affiliate_name = self.validated_data.get("affiliate_name", None)
            
            q = self.validated_data.get('quantity', None)
            if product_name:
                
                p = Product.objects.get(name=product_name)
                o = OrderItem.objects.create(order=order, product=p, quantity=q)
                return {
	                "id": o.id,
	                "product": ProductSimpleSerializer(p).data,
	                "affiliate": None,
	                "quantity": q
                }
            elif affiliate_name:
                a = AffiliateProduct.objects.get(name=affiliate_name)
                o = OrderItem.objects.create(order=order, affiliate=a, quantity=q)
                return {
	                "id": o.id,
	                "affiliate": AffiliateSimpleSerializer(a).data,
	                "product": None,
	                "quantity": q
                }


class OrderItemUpdateSerializer(serializers.ModelSerializer):
    # Keep these read-only for display purposes
    item = serializers.SerializerMethodField(read_only=True)
    item_type = serializers.SerializerMethodField(read_only=True)
    total_price = serializers.SerializerMethodField(read_only=True)
    
    class Meta:
        model = OrderItem
        fields = ['id', 'quantity', 'item', 'item_type', 'total_price']
    
    def get_item(self, obj):
        if obj.product:
            return Product1Serializer(obj.product).data
        elif obj.affiliate:
            return AffiliateProduct1Serializer(obj.affiliate).data
        return None
    
    def get_item_type(self, obj):
        if obj.product:
            return 'product'
        elif obj.affiliate:
            return 'affiliate'
        return None
    
    def get_total_price(self, obj):
        return obj.total_price()
    
    def validate_quantity(self, value):
        if value < 1:
            raise serializers.ValidationError("Quantity must be at least 1")
        return value
    # price = serializers.SerializerMethodField()
    # total_price = serializers.SerializerMethodField()
    # def get_price(self, obj):
    #     if obj.product:
    #         print("PRICE", obj.product.price)
    #         return obj.product.price
    #     elif obj.affiliate:
    #         print("PRICE1", obj.product.price)
    #         return obj.affiliate.price
    #     return 0
    
    # def get_total_price(self, obj):
    #     print("total_price", obj.product.price)
    #     return obj.total_price()
    
    # def get_product(self, obj):
        
    # def get_product(self, obj):
    #     print("###", obj)
    #     if obj.product:
    #         return obj.product.name
    #     elif obj.affiliate:
    #         return obj.affiliate.name
    #     return "unknown"

class Product1Serializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ['id', 'name']  

class AffiliateProduct1Serializer(serializers.ModelSerializer):
    class Meta:
        model = AffiliateProduct
        fields = ['id', 'name']


class OrderItem1Serializer(serializers.ModelSerializer):
    item = serializers.SerializerMethodField()
    item_type = serializers.SerializerMethodField()
    total_price = serializers.SerializerMethodField()

    class Meta:
        model = OrderItem
        fields = ['id', 'quantity', 'total_price', 'item', 'item_type']
    
    def get_item(self, obj):
        if obj.product:
            return Product1Serializer(obj.product).data
        elif obj.affiliate:
            return AffiliateProduct1Serializer(obj.affiliate).data
        return None
    
    def get_item_type(self, obj):
        if obj.product:
            return 'product'
        elif obj.affiliate:
            return 'affiliate'
        return None
    
    def get_total_price(self, obj):
        return obj.total_price()
    

class Order2Serializer(serializers.ModelSerializer):
    items = OrderItem1Serializer(many=True, read_only=True)
    total_price = serializers.SerializerMethodField()
    total_items = serializers.SerializerMethodField()
    
    class Meta:
        model = Order
        fields = ['id', 'items', 'total_price', 'total_items', 'created_at', 'updated_at']
    
    def get_total_price(self, obj):
        return obj.total_price()
    
    def get_total_items(self, obj):
        return obj.total_items()
    

class OrderCheckOutSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = [
            'description', 
            'type',
        ]

class OrderItemSerializer(serializers.ModelSerializer):
    product_name = serializers.SerializerMethodField()
    class Meta:
        model = OrderItem
        fields = [
            'product_name', 
            'quantity'
        ]

    def get_product_name(self, obj):
        if obj.product:
            return obj.product.name
        elif obj.affiliate:
            return obj.affiliate.name
        return "unknown"

class OrderItemCreateSerializer(serializers.ModelSerializer):
    product_id = serializers.UUIDField()
    class Meta:
        model = OrderItem
        fields = [
            'product_id', 
            'quantity'
        ]


class OrderListSerializer(serializers.ModelSerializer):
    total = serializers.SerializerMethodField()
    class Meta:
        model = Order
        fields = [
            'id',
            'description', 
            'created_at', 
            'is_paid',
            'total'
        ]

    def get_total(self, obj):
        return obj.total_price()

class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True)
    total = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = [
            'id', 
            'description', 
            'created_at', 
            'is_paid',
            'total',
            'type',
            'status',
            'owner_description',
            'items'
        ]
        read_only_fields = [
            'id', 
            'user', 
            'created_at', 
            'is_paid'
        ]

    def get_total(self, obj):
        return obj.total_price()
    
class OrderCreateSerializer(serializers.ModelSerializer):
    items = OrderItemCreateSerializer(many=True)
    description = serializers.CharField(required=False)
    type = serializers.ChoiceField(choices=['online', 'cash'])

    class Meta:
        model = Order
        fields = [
            'description', 
            'type',
            'items'
        ]

    def create(self, validated_data):
        items_data = validated_data.pop('items')
        
        order = Order.objects.create(**validated_data)
        
        # add items
        for item_data in items_data:
            
            try:
                product = Product.objects.get(id=item_data['product_id'])
            except:
                product = None
            try:
                affiliate = AffiliateProduct.objects.get(id=item_data['product_id'])
            except:
                affiliate = None
            
            if not product and not affiliate:
                order.delete()
                raise Exception('One or More Products were Not Found')
            
            OrderItem.objects.create(
                order=order, 
                product=product, 
                affiliate=affiliate,
                quantity=item_data['quantity'], 
            )
        
        return order
    

    def update(self, instance, validated_data):
        items_data = validated_data.pop('items', None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        with transaction.atomic():
            # If new items are provided, replace the old ones
            if items_data is not None:
                # Delete existing items
                instance.items.all().delete()

                # Add new items
                for item_data in items_data:
                    product_id = item_data.get('product_id')
                    quantity = item_data.get('quantity')

                    product = None
                    affiliate = None

                    # Fetch product or affiliate
                    if product_id:
                        try:
                            product = Product.objects.get(id=product_id)
                        except Product.DoesNotExist:
                            pass

                        try:
                            affiliate = AffiliateProduct.objects.get(id=product_id)
                        except AffiliateProduct.DoesNotExist:
                            pass  

                    if not product and not affiliate:
                        raise serializers.ValidationError(f"Neither product nor affiliate found for id {product_id}.")

                    # Create the OrderItem
                    OrderItem.objects.create(
                        order=instance,
                        product=product,
                        affiliate=affiliate,
                        quantity=quantity
                    )

        # Save the updated Order instance
        instance.save()

        return instance
    

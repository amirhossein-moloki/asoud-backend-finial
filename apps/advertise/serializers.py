from rest_framework import serializers
from apps.advertise.models import (
    Advertisement, 
    AdvImage,
    AdvKeyword
)
from drf_spectacular.utils import extend_schema_field
from typing import Dict, Any, Optional
from apps.product.models import Product
from apps.product.serializers.owner_serializers import ProductDetailSerializer
from apps.users.serializers import UserSerializer
from jdatetime import datetime as jdatetime

class AdvertiseImageSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(read_only=True)

    class Meta:
        model = AdvImage
        fields = [
            'id',
            'image'
        ]

class AdvertiseSerializer(serializers.ModelSerializer):
    product = ProductDetailSerializer()
    user = UserSerializer()
    images = AdvertiseImageSerializer(many=True)

    class Meta:
        model = Advertisement
        fields = '__all__'
    
class AdvertiseCreateSerializer(serializers.ModelSerializer):
    product = serializers.UUIDField(required=False)
    user = serializers.UUIDField(read_only=True)
    keywords = serializers.ListField(child=serializers.CharField(), required=False)
    images = serializers.ListField(child=serializers.ImageField(), required=False)

    class Meta:
        model = Advertisement
        fields = '__all__' 
        extra_kwargs = {
            'name': {'required': False},
            'type': {'required': False},
            'description': {'required': False},
            'price': {'required': False},
            'category': {'required': False},
            'email': {'required': False},
            'images': {'required': False},
            'keywords': {'required': False},
        }

    def create(self, validated_data):
        # Implement logic for creating a new instance
        try:

            # create or get keywords
            keywords = []
            if 'keywords' in validated_data and validated_data['keywords']:
                for keyword in validated_data['keywords']:
                    key, _ = AdvKeyword.objects.get_or_create(
                        name=keyword
                    )
                    keywords.append(key)
            
                # remove keywords from validated_data
                del validated_data['keywords']

            # remove images from validated_Data
            images = validated_data.pop('images', None)

            if 'product' in list(validated_data.keys()):
                try:
                    product = Product.objects.get(id=validated_data['product'])

                    fields_to_exclude = ['product', 'name', 'description', 'price', 'category', 'type']
                    for field in fields_to_exclude:
                        validated_data.pop(field, None)

                    advertisement = Advertisement.objects.create(
                        **validated_data,
                        product=product,
                        type=product.type,
                        name=product.name,
                        description=product.description,
                        price=product.main_price,
                        category=product.sub_category.category,
                    )
                except Product.DoesNotExist:
                    raise serializers.ValidationError({"product": "Product does not exist"})
            
            else:
                advertisement = Advertisement.objects.create(**validated_data)
            
            # add keywords
            advertisement.keywords.clear()
            advertisement.keywords.add(*keywords)
            
            # add images
            if images:
                for image in images:
                    _ = AdvImage.objects.create(
                        advertise = advertisement,
                        image=image
                    )

            # Additional logic can be added here
            return advertisement
        
        except Exception as e:
            raise serializers.ValidationError({"error": str(e)})
        
    def update(self, instance, validated_data):
        # Implement logic for updating an existing instance
        
        # create or get keywords
        keywords = []
        if 'keywords' in validated_data and validated_data['keywords']:
            for keyword in validated_data['keywords']:
                key, _ = AdvKeyword.objects.get_or_create(
                    name=keyword
                )
                keywords.append(key)
        
            # remove keywords from validated_data
            del validated_data['keywords']

        # remove images from validated_Data
        images = validated_data.pop('images', None)
        
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        # add keywords
        if keywords:
            instance.keywords.clear()
            instance.keywords.add(*keywords)

        # add images
        if images:
            for image in instance.images.all():
                image.delete()

            for image in images:
                _ = AdvImage.objects.create(
                    advertise = instance,
                    image=image
                )

        instance.save()
        return instance
    
class AdvertiseListSerializer(serializers.ModelSerializer):
    category = serializers.SerializerMethodField()
    updated_at = serializers.SerializerMethodField()
    images = AdvertiseImageSerializer(many=True)

    class Meta:
        model = Advertisement
        fields = [
            'id',
            'name',
            'category',
            'price',
            'updated_at',
            'images',
        ]
    
    @extend_schema_field(serializers.CharField())
    def get_updated_at(self, obj) -> str:
        _date = obj.updated_at
        jalali_date = jdatetime.fromgregorian(date=_date)
        return jalali_date.strftime("%Y/%m/%d %H:%M")

    @extend_schema_field(serializers.DictField())
    def get_category(self, obj) -> Dict[str, Any]:
        if not obj.category:
            return {}
        return {
            'id': obj.category.id,
            'title': obj.category.title,
        }

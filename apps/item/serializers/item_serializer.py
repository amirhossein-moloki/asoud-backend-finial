from rest_framework import serializers
from apps.product.models import Item, ProductKeyword

class ProductKeywordSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductKeyword
        fields = ["name"]

class ItemSerializer(serializers.ModelSerializer):
    keywords = ProductKeywordSerializer(many=True, required=False)

    class Meta:
        model = Item
        fields = '__all__'

    def create(self, validated_data):
        keywords_data = validated_data.pop('keywords', [])
        item = Item.objects.create(**validated_data)
        for keyword_data in keywords_data:
            keyword, _ = ProductKeyword.objects.get_or_create(name=keyword_data['name'])
            item.keywords.add(keyword)
        return item

    def update(self, instance, validated_data):
        keywords_data = validated_data.pop('keywords', [])
        instance = super().update(instance, validated_data)
        if keywords_data:
            instance.keywords.clear()
            for keyword_data in keywords_data:
                keyword, _ = ProductKeyword.objects.get_or_create(name=keyword_data['name'])
                instance.keywords.add(keyword)
        return instance
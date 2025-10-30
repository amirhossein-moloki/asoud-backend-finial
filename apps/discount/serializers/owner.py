from rest_framework import serializers
from apps.discount.models import Discount
from django.contrib.contenttypes.models import ContentType


class DiscountCreateSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(read_only=True)
    code = serializers.CharField(read_only=True)
    content_type = serializers.SlugRelatedField(
        queryset=ContentType.objects.filter(
            model__in=['product', 'market']
        ),
        slug_field='model', 
    )
    object_id = serializers.UUIDField()
    expiry = serializers.DateTimeField(required=False)
    limitation = serializers.IntegerField(required=False)
    position = serializers.CharField(required=False)

    class Meta:
        model = Discount
        fields = [
            'id', 
            'code', 
            'content_type',
            'object_id',
            'percentage',
            'expiry',
            'limitation',
            'users',
            'position',
            'created_at'
        ]
    
    def validate(self, data):
        """
        Validate that the object_id corresponds to a valid Product or Market.
        """
        content_type = data['content_type']
        object_id = data['object_id']

        # Get the model class from the content type
        model_class = content_type.model_class()

        # Check if the object exists
        if not model_class.objects.filter(id=object_id).exists():
            raise serializers.ValidationError(
                f"No {content_type.model} found with id {object_id}."
            )

        return data
    
class DiscountListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Discount
        fields = ['id', 'code', 'percentage', 'expiry']

class DiscountDetailSerializer(DiscountCreateSerializer):
    pass


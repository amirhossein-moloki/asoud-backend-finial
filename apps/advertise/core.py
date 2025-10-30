from apps.advertise.serializers import (
    AdvertiseCreateSerializer,
    AdvertiseSerializer
)

def model_to_dict(instance):
    return {field.name: getattr(instance, field.name) for field in instance._meta.fields}
        

class AdvertisementCore:
    @staticmethod
    def create_advertisement(request):
        serializer = AdvertiseCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # check user
        
        obj = serializer.save(
            user = request.user
        )
        
        serialized_data = AdvertiseSerializer(obj).data

        return serialized_data
        
    @staticmethod
    def create_advertisement_for_product(product):
        
        data = model_to_dict(product)
        
        # allow advertisements from product to publish
        data['is_paid'] = True

        serializer = AdvertiseCreateSerializer(data=data)
        serializer.is_valid(raise_exception=True)

        # check user
        
        obj = serializer.save(
            user = product.market.user
        )
        
        serialized_data = AdvertiseSerializer(obj).data

        return serialized_data
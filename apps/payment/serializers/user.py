from rest_framework import serializers
from apps.payment.models import Payment, Zarinpal
from apps.wallet.models import Wallet
from apps.wallet.serializer import WalletSerializer
from apps.advertise.models import Advertisement
from apps.advertise.serializers import AdvertiseSerializer

class PaymentSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(read_only=True)
    target = serializers.SerializerMethodField()
    target_content = serializers.SerializerMethodField()

    class Meta:
        model = Payment
        fields = [
            'id',
            'amount',
            'target',
            'target_content',
            'status',
            'created_at',
        ]

    def get_target(self, obj):
        target_model = obj.target_content_type.model_class()

        if target_model == Wallet:
            target = Wallet.objects.get(id=obj.target_id)
            serializer = WalletSerializer(target)
        
        elif target_model == Advertisement:
            target = Advertisement.objects.get(id=obj.target_id)
            serializer = AdvertiseSerializer(target)

        else :
            return {'id': 'cart'}
        
        return serializer.data

    def get_target_content(self, obj):
        target_model = obj.target_content_type.model_class()

        if target_model == Wallet:
            return "wallet"
        
        elif target_model == Advertisement:
            return "advertisement"

        else :
            return "cart"
            
class PaymentDetailSerializer(serializers.ModelSerializer):
    target = serializers.SerializerMethodField()
    target_content = serializers.SerializerMethodField()
    gateway = serializers.SerializerMethodField()

    class Meta:
        model = Payment
        fields = [
            'id',
            'amount',
            'target',
            'target_id',
            'target_content',
            'gateway',
        ]

    def get_target(self, obj):
        target_model = obj.target_content_type.model_class()

        if target_model == Wallet:
            target = Wallet.objects.get(id=obj.target_id)
            serializer = WalletSerializer(target)
        
        elif target_model == Advertisement:
            target = Advertisement.objects.get(id=obj.target_id)
            serializer = AdvertiseSerializer(target)

        else :
            return {'id': 'cart'}
        
        return serializer.data
    
    def get_gateway(self, obj):
        gateway_model = obj.gateway_content_type.model_class()
        if gateway_model == Zarinpal:
            return {
                'id' : obj.gateway_id,
                'name': 'zarinpal'
            }
        else:
            return {
                'name': 'none'
            }

    def get_target_content(self, obj):
        target_model = obj.target_content_type.model_class()

        if target_model == Wallet:
            return "wallet"
        
        elif target_model == Advertisement:
            return "advertisement"

        else :
            return "cart"
        
class PaymentCreateSerializer(serializers.Serializer):
    amount = serializers.FloatField()
    target = serializers.CharField()
    target_id = serializers.CharField()
    gateway = serializers.CharField()



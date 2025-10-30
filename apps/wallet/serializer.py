from rest_framework import serializers
from apps.wallet.models import Wallet, Transaction


class WalletCheckSerializer(serializers.Serializer):
    amount = serializers.FloatField()

class WalletSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(read_only=True)
    class Meta:
        model = Wallet
        fields = [
            'id',
            'balance',
        ]

class WalletPaySerializer(serializers.Serializer):
    amount = serializers.FloatField()
    target_id = serializers.CharField()
    target_content = serializers.CharField()


class TransactionSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(read_only=True)
    from_wallet = WalletSerializer()
    to_wallet = WalletSerializer()
    class Meta:
        model = Transaction
        fields = [
            'id',
            'from_wallet',
            'to_wallet',
            'action',
            'amount',
            'created_at',
        ]
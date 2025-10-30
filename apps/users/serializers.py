from rest_framework import serializers
from apps.users.models import User, UserBankInfo, BankInfo


class UserSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(read_only=True)
    class Meta:
        model = User
        fields = [
            'id', 
            'mobile_number'
        ]


class BankInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = BankInfo
        fields = (
            'id',
            'name',
            'logo'
        )


class UserBankInfoCreateSerializer(serializers.ModelSerializer):
    bank_info = serializers.UUIDField(write_only=True)
    class Meta:
        model = UserBankInfo
        fields = (
            'bank_info',
            'card_number',
            'account_number',
            'iban',
            'full_name',
            'branch_id',
            'branch_name',
            'description'
        )
    def create(self, validated_data):
        bank_info_id = validated_data.pop('bank_info')
        try:
            bank_info = BankInfo.objects.get(id=bank_info_id)
        except BankInfo.DoesNotExist:
            raise serializers.ValidationError({"bank_info": "Bank info not found"})
            
        user_bank_info = UserBankInfo.objects.create(
            bank_info=bank_info,
            **validated_data
        )
        return user_bank_info
    
    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['bank_info'] = instance.bank_info.name if instance.bank_info else None
        return representation


class UserBankInfoUpdateSerializer(UserBankInfoCreateSerializer):
    bank_info = serializers.UUIDField(required=False)  # Make it optional for updates
    
    class Meta:
        model = UserBankInfo
        fields = (
            'id',
            'bank_info',
            'card_number',
            'account_number',
            'iban',
            'full_name',
            'branch_id',
            'branch_name',
            'description'
        )
    def update(self, instance, validated_data):
        bank_info_id = validated_data.pop('bank_info', None)
        
        if bank_info_id is not None:
            try:
                bank_info = BankInfo.objects.get(id=bank_info_id)
                instance.bank_info = bank_info
            except BankInfo.DoesNotExist:
                raise serializers.ValidationError({"bank_info": "Bank info not found"})
        
        # Update other fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        instance.save()
        return instance
    
    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['bank_info'] = instance.bank_info.name if instance.bank_info else None
        return representation    

class UserBankInfoListSerializer(serializers.ModelSerializer):
    bank_info = serializers.SerializerMethodField()
    class Meta:
        model = UserBankInfo
        fields = '__all__'
    def get_bank_info(self, obj):
        return obj.bank_info.name

from rest_framework import serializers
from apps.referral.models import Referral
from apps.users.models import User
from apps.users.serializers import UserSerializer

class ReferalCreateSerializer(serializers.Serializer):
    code = serializers.CharField()

class ReferalListSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(read_only=True)
    referrees = serializers.SerializerMethodField()
    referral_count = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = [
            'id',
            'referral_count',
            'referrees'
        ]

    def get_referrees(self, obj):
        referrals = obj.referrals_made.all()

        return UserSerializer(
            [referral.referred_user for referral in referrals],
            many=True
        ).data
        
    def get_referral_count(self, obj):
        return obj.referrals_made.count()
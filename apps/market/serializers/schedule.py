from rest_framework import serializers
from apps.reserve.models import (
    Service,
    Specialist,
    ReserveTime,
    DayOff,
    Reservation
)
from apps.market.serializers.user_serializers import MarketListSerializer
from apps.users.serializers import UserSerializer
from jdatetime import datetime as jdatetime

class MarketScheduleSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(read_only=True)
    market = serializers.SerializerMethodField()

    class Meta:
        model = ReserveTime
        fields = [
            'id',
            'market',
            'day',
            'start',
            'end',
        ]

    def get_market(self, obj:ReserveTime):
        return MarketListSerializer(obj.service.market).data

class MarketScheduleCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReserveTime
        fields = [
            'id',
            'service',
            'day',
            'start',
            'end',
        ]
    
class MarketScheduleInputSerializer(MarketScheduleSerializer):
    market = serializers.UUIDField()
    day = serializers.CharField()
    start = serializers.TimeField()
    end = serializers.TimeField(required=False)

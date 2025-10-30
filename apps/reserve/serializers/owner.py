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


class ServiceSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(read_only=True)
    market = MarketListSerializer()

    class Meta:
        model = Service
        fields = [
            'id',
            'market',
            'name',
        ]

class ServiceCreateSerializer(ServiceSerializer):
    market = serializers.UUIDField()


class SpecialistSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(read_only=True)
    services = ServiceSerializer(many=True)

    class Meta:
        model = Specialist
        fields = [
            'id',
            'user',
            'services',
            'field'
        ]

class SpecialistCreateSerializer(SpecialistSerializer):
    services = serializers.ListField(child=serializers.UUIDField())
    field = serializers.CharField(required=False)


class ReserveTimeSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(read_only=True)
    service = ServiceSerializer()
    end = serializers.TimeField(required=False)

    class Meta:
        model = ReserveTime
        fields = [
            'id',
            'service',
            'day',
            'start',
            'end'
        ]

class ReserveTimeCreateSerializer(ReserveTimeSerializer):
    service = serializers.UUIDField()

class DayOffSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(read_only=True)
    market = MarketListSerializer()
    date_jalali = serializers.SerializerMethodField()
    
    class Meta:
        model = DayOff
        fields = [
            'id',
            'market',
            'date_jalali'
        ]
    
    def get_date_jalali(self, obj):
        _date = obj.date
        jalali_date = jdatetime.fromgregorian(date=_date)
        return jalali_date.strftime("%Y/%m/%d")

class DayOffCreateSerializer(serializers.ModelSerializer):
    market = serializers.UUIDField()

    class Meta:
        model = DayOff
        fields = [
            'market',
            'date'
        ]

class ReservationSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(read_only=True)
    user = UserSerializer()
    reserve = ReserveTimeSerializer()

    class Meta:
        model = Reservation
        fields = [
            'id',
            'user',
            'reserve',
            'specialist',
            'is_paid'
        ]


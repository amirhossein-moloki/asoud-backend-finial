from rest_framework import serializers
from apps.reserve.models import (
    Service,
    Specialist,
    ReserveTime,
    Reservation
)
from apps.market.serializers.user_serializers import MarketListSerializer
from apps.users.serializers import UserSerializer
from apps.reserve.serializers.owner import (
    ServiceSerializer,
    SpecialistSerializer,
    ReserveTimeSerializer,
    DayOffSerializer,
    ReservationSerializer
)

class ServiceListSerializer(ServiceSerializer):
    pass

class SpecialistListSerializer(SpecialistSerializer):
    pass

class ReserveTimeListSerializer(ReserveTimeSerializer):
    pass

class DayoffListSerializer(DayOffSerializer):
    pass

class ReservationCreateSerializer(ReservationSerializer):
    user = serializers.UUIDField(read_only=True)
    reserve = serializers.UUIDField()


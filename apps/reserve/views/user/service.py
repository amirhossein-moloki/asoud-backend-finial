from rest_framework import views, status
from rest_framework.response import Response
from utils.response import ApiResponse
from apps.reserve.models import (
    Service,
    Specialist,
    ReserveTime,
    DayOff
)
from apps.reserve.serializers.user import (
    ServiceListSerializer,
    SpecialistListSerializer,
    ReserveTimeListSerializer,
    DayoffListSerializer,
)
# from apps.reserve.sms_core import send_pattern

class ServiceListView(views.APIView):
    def get(self, request):
    
        if market := request.GET.get('market'):
            services = Service.objects.filter(market=market)
        else :
            return Response(
                ApiResponse(
                    success=False,
                    code=400,
                    error="Market Not Provided"
                ),
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if name := request.GET.get('name'):
            services = services.filter(name=name)

        serializer = ServiceListSerializer(services, many=True)
        return Response(
            ApiResponse(
                success=True,
                code=200,
                data=serializer.data
            )
        )

class SpecialistListView(views.APIView):
    def get(self, request):
        if service_id := request.GET.get('service'):
            try:
                service = Service.objects.get(id=service_id)
                specialists = Specialist.objects.filter(services=service)
            except Service.DoesNotExist:
                return Response (
                    ApiResponse(
                        success=False,
                        code=404,
                        error="Service Not Found"
                    ),
                    status=status.HTTP_404_NOT_FOUND
                )
        else:
            return Response (
                ApiResponse(
                    success=False,
                    code=400,
                    error="Service Not Provided"
                ),
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = SpecialistListSerializer(specialists, many=True)
        return Response(
            ApiResponse(
                success=True,
                code=200,
                data=serializer.data
            )
        )
    
class ReserveTimeListView(views.APIView):
    def get(self, request):
        if service_id := request.GET.get('service'):
            try:
                service = Service.objects.get(id=service_id)
                reserve_times = ReserveTime.objects.filter(service=service)
            except Service.DoesNotExist:
                return Response (
                    ApiResponse(
                        success=False,
                        code=404,
                        error="Service Not Found"
                    ),
                    status=status.HTTP_404_NOT_FOUND
                )
        else:
            return Response (
                ApiResponse(
                    success=False,
                    code=400,
                    error="Service Not Provided"
                ),
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = ReserveTimeListSerializer(reserve_times, many=True)
        return Response(
            ApiResponse(
                success=True,
                code=200,
                data=serializer.data
            )
        )

class DayOffListView(views.APIView):
    def get(self, request):
        if market := request.GET.get('market'):
            daysoff = DayOff.objects.filter(market=market)
        else :
            return Response(
                ApiResponse(
                    success=False,
                    code=400,
                    error="Market Not Provided"
                ),
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = DayoffListSerializer(daysoff, many=True)
        return Response(
            ApiResponse(
                success=True,
                code=200,
                data=serializer.data
            )
        )


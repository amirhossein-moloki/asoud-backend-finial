from rest_framework import views, status
from rest_framework.response import Response
from django.utils.translation import gettext_lazy as _

from utils.response import ApiResponse

from apps.market.models import (
    Market,
    MarketSchedule
)
from apps.reserve.models import ReserveTime, Service
from apps.market.serializers.schedule import (
    MarketScheduleCreateSerializer,
    MarketScheduleSerializer,
    MarketScheduleInputSerializer
)
class MarketScheduleAPIView(views.APIView):
    def post(self, request):
        serializer = MarketScheduleInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            market = Market.objects.get(id=serializer.validated_data['market'])

            service, _ = Service.objects.get_or_create(
                market=market,
                name="-",
                defaults={
                    'name':'-',
                })
        except Market.DoesNotExist:
            
            return Response(
                ApiResponse(
                    success=False,
                    code=404,
                    error="Market Not Found"
               ),
               status=status.HTTP_404_NOT_FOUND
            )

        if request.user != service.market.user:
            return Response(
                ApiResponse(
                    success=False,
                    code=403,
                    error='UnAuthorized'
                ),
                status=status.HTTP_403_FORBIDDEN
            )
        
        data = {
            'service': str(service.id),
            'day': serializer.validated_data['day'],
            'start': serializer.validated_data['start'],
            'end': serializer.validated_data['end'],
        }

        serializer = MarketScheduleCreateSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        obj = serializer.save(service=service)

        serializer = MarketScheduleSerializer(obj)
        return Response(
            ApiResponse(
                success=True,
                code=201,
                data=serializer.data
            ),
            status=status.HTTP_201_CREATED
        )

class MarketScheduleListView(views.APIView):
    def get(self, request):
        reserves = ReserveTime.objects.filter(service__market__user=request.user)
        serializer = MarketScheduleSerializer(reserves, many=True)

        return Response(
            ApiResponse(
                success=True,
                code=200,
                data=serializer.data
            ),
            status=status.HTTP_200_OK
        )

class MarketScheduleUpdateView(views.APIView):
    def put(self, request, pk):
        try:
            reserve = ReserveTime.objects.get(id=pk)
        except ReserveTime.DoesNotExist:
            return Response(
                ApiResponse(
                    success=False,
                    code=404,
                    error="ReserveTime Not Found"
               ),
               status=status.HTTP_404_NOT_FOUND
            )

        if request.user != reserve.service.market.user:
            return Response(
                ApiResponse(
                    success=False,
                    code=403,
                    error='UnAuthorized'
                ),
                status=status.HTTP_403_FORBIDDEN
            )
        
        # service not changing
        if request.data.get('service'):
            del request.data['service']
        
        serializer = MarketScheduleCreateSerializer(reserve, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(
            ApiResponse(
                success=True,
                code=200,
                data=serializer.data
            ),
            status=status.HTTP_200_OK
        )

class MarketScheduleDeleteView(views.APIView):
    def delete(self, request, pk):
        try:
            reserve = ReserveTime.objects.get(id=pk)
        except ReserveTime.DoesNotExist:
            return Response(
                ApiResponse(
                    success=False,
                    code=404,
                    error="ReserveTime Not Found"
               ),
               status=status.HTTP_404_NOT_FOUND
            )

        if request.user != reserve.service.market.user:
            return Response(
                ApiResponse(
                    success=False,
                    code=403,
                    error='UnAuthorized'
                ),
                status=status.HTTP_403_FORBIDDEN
            )
        
        reserve.delete()

        return Response(
            ApiResponse(
                success=True,
                code=204
            ),
            status=status.HTTP_204_NO_CONTENT
        )



class MarketScheduleUserListView(views.APIView):
    def get(self, request, pk:str):
        reserve = ReserveTime.objects.filter(service__market__id=pk)

        serializer = MarketScheduleSerializer(reserve, many=True)

        return Response(
            ApiResponse(
                success=True,
                code=200,
                data=serializer.data
            ),
            status=status.HTTP_200_OK
        )
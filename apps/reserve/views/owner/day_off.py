from rest_framework import views, status
from rest_framework.response import Response
from utils.response import ApiResponse
from apps.reserve.models import (
    DayOff,
)
from apps.reserve.serializers.owner import (
    DayOffSerializer,
    DayOffCreateSerializer,
)
from apps.market.models import Market


class DayOffCreateView(views.APIView):
    def post(self, request):
        serializer = DayOffCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            market = Market.objects.get(id=serializer.validated_data['market'])
        except Market.DoesNotExist:
            return Response(
                ApiResponse(
                    success=False,
                    code=404,
                    error="Market Not Found"
               ),
               status=status.HTTP_404_NOT_FOUND
            )

        if request.user != market.user:
            return Response(
                ApiResponse(
                    success=False,
                    code=403,
                    error='UnAuthorized'
                ),
                status=status.HTTP_403_FORBIDDEN
            )
        
        # prevent duplicated
        obj, _ = DayOff.objects.get_or_create(
            market=market,
            date=serializer.validated_data['date'],
            defaults={
                'market': market,
                'date': serializer.validated_data['date']
            }
        )

        serialized_data = DayOffSerializer(obj).data

        return Response(
            ApiResponse(
                success=True,
                code=201,
                data=serialized_data
            ),
            status=status.HTTP_201_CREATED
        )

class DayOffListView(views.APIView):
    def get(self, request):
        dayoffs = DayOff.objects.filter(market__user=request.user)

        if market :=request.GET.get('market'):
            dayoffs = dayoffs.filter(market=market)

        serializer = DayOffSerializer(dayoffs, many=True)

        return Response(
            ApiResponse(
                success=True,
                code=200,
                data=serializer.data
            ),
            status=status.HTTP_200_OK
        )

class DayOffDeleteView(views.APIView):
    def delete(self, request, pk):
        try:
            dayoff = DayOff.objects.get(id=pk)
        except DayOff.DoesNotExist:
            return Response(
                ApiResponse(
                    success=False,
                    code=404,
                    error="DayOff Not Found"
               ),
               status=status.HTTP_404_NOT_FOUND
            )

        if request.user != dayoff.market.user:
            return Response(
                ApiResponse(
                    success=False,
                    code=403,
                    error='UnAuthorized'
                ),
                status=status.HTTP_403_FORBIDDEN
            )
        
        dayoff.delete()

        return Response(
            ApiResponse(
                success=True,
                code=204
            ),
            status=status.HTTP_204_NO_CONTENT
        )


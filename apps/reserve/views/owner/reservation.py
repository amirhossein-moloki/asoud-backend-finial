from rest_framework import views, status
from rest_framework.response import Response
from utils.response import ApiResponse
from apps.reserve.models import Reservation
from apps.reserve.serializers.owner import ReservationSerializer



class ReservationDetailView(views.APIView):
    def get(self, request, pk):
        try:
            reservation = Reservation.objects.get(id=pk)
        except Reservation.DoesNotExist:
            return Response(
                ApiResponse(
                    success=False,
                    code=404,
                    error="Reservation Not Found"
               ),
               status=status.HTTP_404_NOT_FOUND
            )

        if request.user != reservation.reserve.service.market.user:
            return Response(
                ApiResponse(
                    success=False,
                    code=403,
                    error='UnAuthorized'
                ),
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = ReservationSerializer(reservation)

        return Response(
                ApiResponse(
                    success=True,
                    code=200,
                    data=serializer.data
               ),
               status=status.HTTP_200_OK
            )

class ReservationListView(views.APIView):
    def get(self, request):
        reservations = Reservation.objects.filter(reserve__service__market__user=request.user)

        serializer = ReservationSerializer(reservations, many=True)

        return Response(
            ApiResponse(
                success=True,
                code=200,
                data=serializer.data
            ),
            status=status.HTTP_200_OK
        )

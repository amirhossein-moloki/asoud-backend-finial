from rest_framework import views, status
from rest_framework.response import Response
from utils.response import ApiResponse
from apps.reserve.models import (
    ReserveTime,
    Reservation
)
from apps.reserve.serializers.user import (
    ReservationSerializer,
    ReservationCreateSerializer
)

class ReservationListView(views.APIView):
    def get(self, request):
        reservations = Reservation.objects.filter(user=request.user)

        serializer = ReservationSerializer(reservations, many=True)

        return Response(
            ApiResponse(
                success=True,
                code=200,
                data=serializer.data
            )
        )

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
        
        if reservation.user != request.user:
            return Response(
                ApiResponse(
                    success=False,
                    code=403,
                    error="UnAuthorized"
                ),
                status=status.HTTP_403_FORBIDDEN
            )
        serializer = ReservationSerializer(reservation)

        return Response(
            ApiResponse(
                success=True,
                code=200,
                data=serializer.data
            )
        )

class ReservationCreateView(views.APIView):
    def post(self, request):
        serializer = ReservationCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            reserve = ReserveTime.objects.get(id=serializer.validated_data['reserve'])
        except ReserveTime.DoesNotExist:
            return Response(
                ApiResponse(
                    success=False,
                    code=404,
                    error="Reserve Time Not Found"
                ),
                status=status.HTTP_404_NOT_FOUND
            )
        
        obj = serializer.save(
            user=request.user,
            reserve=reserve
        )

        serialized_data = ReservationSerializer(obj).data

        return Response(
            ApiResponse(
                success=True,
                code=201,
                data=serialized_data
            ),
            status=status.HTTP_201_CREATED
        )

class ReservationPaymentView(views.APIView):
    def get(self, request):
        # 1- get the user and the reservation
        # 2- communicate with payment gateway to get initial data
        # 3- save the data and send user to gateway
        ""

class ReservationPaymentCompleteView(views.APIView):
    def get(self, request):
        # 1- get the data from gateway and communicate to validate the data
        # 2- save the data to reservation and verify it
        # 3- send user back to app
        ""
        
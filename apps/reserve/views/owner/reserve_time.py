from rest_framework import views, status
from rest_framework.response import Response
from utils.response import ApiResponse
from apps.reserve.models import (
    Service,
    ReserveTime,
)
from apps.reserve.serializers.owner import (
    ReserveTimeSerializer,
    ReserveTimeCreateSerializer,
)
from apps.market.models import Market



class ReserveTimeCreateView(views.APIView):
    def post(self, request):
        serializer = ReserveTimeCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            print(serializer.validated_data['service'])
            service = Service.objects.get(id=serializer.validated_data['service'])
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
        
        # make sure there isn't another reserve time for the same day and same service
        try:
            reserve = ReserveTime.objects.get(service=service, day=serializer.validated_data['day'])
            serializer = ReserveTimeCreateSerializer(reserve, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
        except:
            pass

        serializer.save(service=service)

        return Response(
            ApiResponse(
                success=True,
                code=201,
                data=serializer.data
            ),
            status=status.HTTP_201_CREATED
        )

class ReserveTimeDetailView(views.APIView):
    def get(self, request, pk):
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
        
        serializer = ReserveTimeSerializer(reserve)

        return Response(
                ApiResponse(
                    success=True,
                    code=200,
                    data=serializer.data
               ),
               status=status.HTTP_200_OK
            )

class ReserveTimeListView(views.APIView):
    def get(self, request):
        reserves = ReserveTime.objects.filter(service__market__user=request.user)

        serializer = ReserveTimeSerializer(reserves, many=True)

        return Response(
            ApiResponse(
                success=True,
                code=200,
                data=serializer.data
            ),
            status=status.HTTP_200_OK
        )

class ReserveTimeUpdateView(views.APIView):
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
        
        serializer = ReserveTimeCreateSerializer(reserve, data=request.data, partial=True)
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

class ReserveTimeDeleteView(views.APIView):
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


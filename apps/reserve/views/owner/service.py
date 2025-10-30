from rest_framework import views, status
from rest_framework.response import Response
from utils.response import ApiResponse
from apps.reserve.models import (
    Service,
)
from apps.reserve.serializers.owner import (
    ServiceSerializer,
    ServiceCreateSerializer,
)
from apps.market.models import Market


class ServiceCreateView(views.APIView):
    def post(self, request):
        serializer = ServiceCreateSerializer(data=request.data)
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
        
        serializer.save(market=market)

        return Response(
            ApiResponse(
                success=True,
                code=201,
                data=serializer.data
            ),
            status=status.HTTP_201_CREATED
        )

class ServiceDetailView(views.APIView):
    def get(self, request, pk):
        try:
            service = Service.objects.get(id=pk)
        except Service.DoesNotExist:
            return Response(
                ApiResponse(
                    success=False,
                    code=404,
                    error="Service Not Found"
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
        
        serializer = ServiceSerializer(service)

        return Response(
                ApiResponse(
                    success=True,
                    code=200,
                    data=serializer.data
               ),
               status=status.HTTP_200_OK
            )

class ServiceListView(views.APIView):
    def get(self, request):        
        services = Service.objects.filter(market__user=request.user)

        serializer = ServiceSerializer(services, many=True)

        return Response(
            ApiResponse(
                success=True,
                code=200,
                data=serializer.data
            ),
            status=status.HTTP_200_OK
        )

class ServiceUpdateView(views.APIView):
    def put(self, request, pk):
        try:
            service = Service.objects.get(id=pk)
        except Service.DoesNotExist:
            return Response(
                ApiResponse(
                    success=False,
                    code=404,
                    error="Service Not Found"
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
        
        # no change of market
        if request.data.get('market'):
            del request.data['market']

        serializer = ServiceCreateSerializer(service, data=request.data, partial=True)
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

class ServiceDeleteView(views.APIView):
    def delete(self, request, pk):
        try:
            service = Service.objects.get(id=pk)
        except Service.DoesNotExist:
            return Response(
                ApiResponse(
                    success=False,
                    code=404,
                    error="Service Not Found"
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
        
        service.delete()

        return Response(
            ApiResponse(
                success=True,
                code=204
            ),
            status=status.HTTP_204_NO_CONTENT
        )


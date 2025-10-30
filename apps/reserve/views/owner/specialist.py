from rest_framework import views, status
from rest_framework.response import Response
from utils.response import ApiResponse
from apps.reserve.models import (
    Service,
    Specialist,
)
from apps.reserve.serializers.owner import (
    SpecialistSerializer,
    SpecialistCreateSerializer,
)



class SpecialistCreateView(views.APIView):
    def post(self, request):
        serializer = SpecialistCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        services = Service.objects.filter(id__in=serializer.validated_data['services'])
        if len(services) == 0:
            return Response(
                ApiResponse(
                    success=False,
                    code=400,
                    error="No Service Found"
                ),
                status=status.HTTP_400_BAD_REQUEST
            )        
        for service in services:
            if request.user != service.market.user:
                return Response(
                    ApiResponse(
                        success=False,
                        code=403,
                        error='UnAuthorized'
                    ),
                    status=status.HTTP_403_FORBIDDEN
                )
        
        specialist = serializer.save()
        
        # Add services to the specialist
        specialist.services.set(services)

        specialist_serializer = SpecialistSerializer(specialist)
        return Response(
            ApiResponse(
                success=True,
                code=201,
                data=specialist_serializer.data
            ),
            status=status.HTTP_201_CREATED
        )

class SpecialistDetailView(views.APIView):
    def get(self, request, pk):
        try:
            specialist = Specialist.objects.get(id=pk)
        except Specialist.DoesNotExist:
            return Response(
                ApiResponse(
                    success=False,
                    code=404,
                    error="Specialist Not Found"
               ),
               status=status.HTTP_404_NOT_FOUND
            )

        services = specialist.services.all()
        if not services:
            return Response(
                ApiResponse(
                    success=False,
                    code=400,
                    error="No Services Found"
                ),
                status=status.HTTP_400_BAD_REQUEST
            )
    
        if request.user != services[0].market.user:
            return Response(
                ApiResponse(
                    success=False,
                    code=403,
                    error='UnAuthorized'
                ),
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = SpecialistSerializer(specialist)

        return Response(
                ApiResponse(
                    success=True,
                    code=200,
                    data=serializer.data
               ),
               status=status.HTTP_200_OK
            )

class SpecialistListView(views.APIView):
    def get(self, request):        
        specialists = Specialist.objects.filter(services__market__user=request.user)

        serializer = SpecialistSerializer(specialists, many=True)

        return Response(
            ApiResponse(
                success=True,
                code=200,
                data=serializer.data
            ),
            status=status.HTTP_200_OK
        )

class SpecialistUpdateView(views.APIView):
    def put(self, request, pk):
        try:
            specialist = Specialist.objects.get(id=pk)
        except Specialist.DoesNotExist:
            return Response(
                ApiResponse(
                    success=False,
                    code=404,
                    error="Specialist Not Found"
               ),
               status=status.HTTP_404_NOT_FOUND
            )

        services = specialist.services.all()
        if not services:
            return Response(
                ApiResponse(
                    success=False,
                    code=400,
                    error="No Services Found"
                ),
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if request.user != services[0].market.user:
            return Response(
                ApiResponse(
                    success=False,
                    code=403,
                    error='UnAuthorized'
                ),
                status=status.HTTP_403_FORBIDDEN
            )

        input_services = request.data.get('services')
        del request.data['services']
        
        serializer = SpecialistCreateSerializer(specialist, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        obj = serializer.save()

        # update many to many field
        if input_services:
            services = Service.objects.filter(id__in=input_services)
            specialist.services.set(services)

        serialized_data = SpecialistSerializer(obj).data
        return Response(
            ApiResponse(
                success=True,
                code=200,
                data=serialized_data
            ),
            status=status.HTTP_200_OK
        )

class SpecialistDeleteView(views.APIView):
    def delete(self, request, pk):
        try:
            specialist = Specialist.objects.get(id=pk)
        except Specialist.DoesNotExist:
            return Response(
                ApiResponse(
                    success=False,
                    code=404,
                    error="Specialist Not Found"
               ),
               status=status.HTTP_404_NOT_FOUND
            )

        services = specialist.services.all()
        if not services:
            return Response(
                ApiResponse(
                    success=False,
                    code=400,
                    error="No Services Found"
                ),
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if request.user != services[0].market.user:
            return Response(
                ApiResponse(
                    success=False,
                    code=403,
                    error='UnAuthorized'
                ),
                status=status.HTTP_403_FORBIDDEN
            )
        
        specialist.delete()

        return Response(
            ApiResponse(
                success=True,
                code=204
            ),
            status=status.HTTP_204_NO_CONTENT
        )


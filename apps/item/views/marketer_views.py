from rest_framework import views, status
from rest_framework.response import Response

from utils.response import ApiResponse

from apps.item.models import Item
from apps.item.serializers.marketer_serializers import (
    ItemListSerializer,
    ItemCreateSerializer,
)


class ItemListAPIView(views.APIView):
    def get(self, request, pk):
        item_list = Item.objects.filter(
            is_marketer=True,
        )

        serializer = ItemListSerializer(
            item_list,
            many=True,
            context={"request": request},
        )

        success_response = ApiResponse(
            success=True,
            code=200,
            data=serializer.data,
            message='Data retrieved successfully'
        )

        return Response(success_response)


class ItemCreateAPIView(views.APIView):
    def post(self, request):
        serializer = ItemCreateSerializer(
            data=request.data,
            context={'request': request},
        )

        if serializer.is_valid(raise_exception=True):
            item = serializer.save()

            item_id = item.id

            success_response = ApiResponse(
                success=True,
                code=200,
                data={
                    'item': item_id,
                    **serializer.data,
                },
                message='Product created successfully.',
            )

            return Response(success_response, status=status.HTTP_201_CREATED)

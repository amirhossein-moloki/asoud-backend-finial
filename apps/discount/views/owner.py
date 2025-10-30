from rest_framework import views, status
from rest_framework.response import Response
from apps.discount.models import Discount
from utils.response import ApiResponse
from apps.discount.serializers.owner import (
    DiscountCreateSerializer,
    DiscountDetailSerializer,
    DiscountListSerializer
)
import string, random

class DiscountCreateView(views.APIView):
    def post(self, request):
        """
        create discount
        """

        serializer = DiscountCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Get market or product object
        content_type = serializer.validated_data['content_type']
        object_id = serializer.validated_data['object_id']

        model_class = content_type.model_class()

        try:
            content_object = model_class.objects.get(id=object_id)
        except model_class.DoesNotExist:
            return Response(
                ApiResponse(
                    success=False,
                    code=404,
                    error=f"No {content_type.model} found with id {object_id}."
                ),
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Authorize user
        if  ( "Market"  in str(content_type) and content_object.user        != request.user ) or \
            ( "Product" in str(content_type) and content_object.market.user != request.user ):
            return Response(
                ApiResponse(
                    success=False,
                    code=403,
                    error='UnAuthorized'
                ),
                status=status.HTTP_403_FORBIDDEN
            )
        
        characters = string.ascii_letters + string.digits
        code = ''.join(random.choice(characters) for _ in range(8))

        discount = serializer.save(
            content_object = content_object,
            code=code,
            owner = request.user
        )
        
        return Response(
            ApiResponse(
                success=True,
                code=201,
                data=DiscountDetailSerializer(discount).data
            ),
            status=status.HTTP_201_CREATED
        )

class DiscountDetailView(views.APIView):
    def get(self, request, pk):
        """
        get the details of a discount
        """
        try:
            discount = Discount.objects.get(id=pk)
        except:
            return Response(
                ApiResponse(
                    success=False,
                    code=404,
                    error="Discount Not Found"
                ),
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = DiscountDetailSerializer(discount)

        return Response(
            ApiResponse(
                success=True,
                code=200,
                data=serializer.data
            )
        )

class DiscountListView(views.APIView):
    def get(self, request):
        """
        get the list of discounts created by user
        both product and market discounts are returned
        """
        discounts = Discount.objects.filter(owner=request.user)
        
        serializer = DiscountListSerializer(discounts, many=True)

        return Response(
            ApiResponse(
                success=True,
                code=200,
                data=serializer.data
            )
        )

class DiscountDeleteView(views.APIView):
    def delete(self, request, pk):
        """
        delete discount with id
        """

        try:
            discount = Discount.objects.get(id=pk)
        except:
            return Response(
                ApiResponse(
                    success=False,
                    code=404,
                    error="Discount Not Found"
                ),
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Authorize user
        if discount.owner != request.user:
            return Response(
                ApiResponse(
                    success=False,
                    code=403,
                    error="UnAuthorized"
                ),
                status=status.HTTP_403_FORBIDDEN
            )
        
        discount.delete()
        return Response(
            ApiResponse(
                success=True,
                code=204
            ),
            status=status.HTTP_204_NO_CONTENT
        )
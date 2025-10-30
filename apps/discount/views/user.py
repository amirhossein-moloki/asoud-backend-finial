from rest_framework import views, status
from rest_framework.response import Response
from apps.discount.models import Discount
from utils.response import ApiResponse
from django.db import models, transaction
from apps.discount.serializers.user import (
    DiscountValidateSerializer,
    DiscountValidateResponseSerializer
)
from django.utils import timezone


DISCOUNT_NOT_VALID = "Discount Code Not Valid"
DISCOUNT_LIMIT_REACHED = "Discount Code Limitation Reached"
DISCOUNT_EXPIRED = "Discount Code Expired"


class DiscountValidateView(views.APIView):
    def post(self, request):
        """
        validate discount for users when finalizing cart 
        """

        serializer = DiscountValidateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        with transaction.atomic():
            try:
                discount = Discount.objects.select_for_update().get(
                    code=serializer.validated_data['code'],
                    content_type=serializer.validated_data['content_type'],
                    object_id=serializer.validated_data['object_id']
                )
            except Discount.DoesNotExist:
                return Response(
                    ApiResponse(
                        success=False,
                        code=404,
                        error=DISCOUNT_NOT_VALID
                    ),
                    status=status.HTTP_404_NOT_FOUND
                )
            print (discount.code, "   ", discount.expiry)
            if discount.limitation !=0 and discount.consumed >= discount.limitation :
                return Response(
                    ApiResponse(
                        success=False,
                        code=400,
                        error=DISCOUNT_LIMIT_REACHED
                    ),
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            if discount.expiry and discount.expiry < timezone.now():
                return Response(
                    ApiResponse(
                        success=False,
                        code=400,
                        error=DISCOUNT_EXPIRED
                    ),
                    status=status.HTTP_400_BAD_REQUEST
                )

            if discount.users and request.user.mobile_number not in discount.users:
                return Response(
                    ApiResponse(
                        success=False,
                        code=400,
                        error=DISCOUNT_NOT_VALID
                    ),
                    status=status.HTTP_400_BAD_REQUEST
                )
            
        serialized_data = DiscountValidateResponseSerializer(discount)
        return Response(
            ApiResponse(
                success=True,
                code=200,
                data=serialized_data.data
            )
        )
        

from rest_framework import views, status
from rest_framework.response import Response
from utils.response import ApiResponse
from apps.users.models import User
from apps.referral.models import Referral
from apps.referral.serializers.user import (
    ReferalCreateSerializer,
    ReferalListSerializer
)

# Create your views here.
class ReferalCreateView(views.APIView):
    def post(self, request):
        serializer = ReferalCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            referrer = User.objects.get(mobile_number=serializer.validated_data['code'])
        except User.DoesNotExist:
            return Response(
                ApiResponse(
                    success=False,
                    code=404,
                    error="User Not Found"
                ),
                status=status.HTTP_404_NOT_FOUND
            )

        if referrer == request.user:
            return Response(
                ApiResponse(
                    success=False,
                    code=400,
                    error="Cannot Refer Yourself"
                ),
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if the user already has a referrer
        if Referral.objects.filter(referred_user=request.user).exists():
            return Response(
                ApiResponse(
                    success=False,
                    code=404,
                    error="Referral code already applied"
                ),
                status=status.HTTP_404_NOT_FOUND
            )

        # Create the referral relationship
        Referral.objects.create(referred_by=referrer, referred_user=request.user)
        return Response(
                ApiResponse(
                    success=True,
                    code=201,
                    data={}
                ),
                status=status.HTTP_201_CREATED
            )
    
class ReferalListView(views.APIView):
    def get(self, request):
        serializer = ReferalListSerializer(request.user)

        return Response(
            ApiResponse(
                success=True,
                code=200,
                data=serializer.data
            )
        )


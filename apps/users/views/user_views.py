from rest_framework import views, status, permissions
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK
from rest_framework.authtoken.models import Token
from utils.response import ApiResponse
from apps.users.models import User, UserBankInfo, BankInfo
from apps.sms.sms_core import SMSCoreHandler
import random
from django.utils import timezone
from datetime import datetime, timedelta
from apps.users import serializers


class PinCreateAPIView(views.APIView):
    """
    API view for creating PIN codes for user authentication.
    
    This view handles user signup/login by creating a PIN code
    and sending it via SMS to the provided mobile number.
    
    Attributes:
        permission_classes: AllowAny - No authentication required
    """
    permission_classes = (AllowAny,)
    
    def post(self, request, format=None):
        """
        User Singup/Login
        required fields: mobile_number(Unique)
        return: 200: {}, 500: Error
        """
        mobile_number = request.data.get("mobile_number")

        try:
            user_obj, is_created_user = User.objects.get_or_create(
                mobile_number=mobile_number,
            )

            # send verification pin by sms
            pin = random.randrange(1111, 9999)

            user_obj.pin = pin
            user_obj.pin_expiry = timezone.now() + timedelta(minutes=2)
            user_obj.save()
            
            print("--->   ", mobile_number, "   ", pin)
            try:
                result = SMSCoreHandler.send_verification_code(mobile_number, str(pin))
                print("SMS API result: ", result)
            except Exception as e:
                print("SMS API error: ", str(e))
            data = {"pin": pin}

            success_response = ApiResponse(
                success=True,
                code=200,
                data=data,
                message='Pin has been created successfully',
            )

            return Response(success_response, status=HTTP_200_OK)

        except Exception as e:
            response = ApiResponse(
                success=False,
                code=500,
                error={
                    'code': str(e),
                    'detail': 'Server error',
                }
            )

            return Response(response, status=HTTP_200_OK)


class PinVerifyAPIView(views.APIView):
    """
    API view for verifying PIN codes and creating authentication tokens.
    
    This view verifies the PIN code sent to the user's mobile number
    and creates a Django REST Framework token for authentication.
    
    Attributes:
        permission_classes: AllowAny - No authentication required
    """
    permission_classes = (AllowAny,)

    def post(self, request, format=None):
        mobile_number = request.data.get("mobile_number")
        pin = request.data.get("pin")

        try:
            user = User.objects.get(mobile_number=mobile_number)

        except User.DoesNotExist as e:
            response = ApiResponse(
                success=False,
                code=404,
                error={
                    'code': 'user_not_found',
                    'detail': 'User not found in the database',
                }
            )
            return Response(response, status=status.HTTP_404_NOT_FOUND)

        try:
            if user.pin_expiry < timezone.now():
                response = ApiResponse(
                    success=False,
                    code=400,
                    error={
                        'code': "Code Expired",
                        'detail': 'Code is only valid for 2 minutes',
                    }
                )
                return Response(response, status=status.HTTP_400_BAD_REQUEST)

            if str(pin) == str(user.pin):
                token, _ = Token.objects.get_or_create(user=user)

                data = {
                    'token': token.key,
                }

                success_response = ApiResponse(
                    success=True,
                    code=200,
                    data=data,
                    message='Token has been created successfully',
                )

                return Response(success_response, status=status.HTTP_200_OK)

            else:
                response = ApiResponse(
                    success=False,
                    code=401,
                    error={
                        'code': 'pin_not_valid',
                        'detail': 'Pin not valid',
                    }
                )
                return Response(response, status=status.HTTP_401_UNAUTHORIZED)

        except Exception as e:
            response = ApiResponse(
                success=False,
                code=500,
                error={
                    'code': 'server_error',
                    'detail': 'Server error',
                }
            )

            return Response(response, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class BanksListView(views.APIView):
    permission_classes = [AllowAny, ]
    def get(self, request):
        objs = BankInfo.objects.all()
        serializer = serializers.BankInfoSerializer(objs, many=True)
        success_response = ApiResponse(
                success=True,
                code=200,
                data=serializer.data,
                message='successful.',
            )
        return Response(success_response, status=status.HTTP_200_OK)
    

class BankInfoCreateView(views.APIView):
    def post(self, request):
        user = request.user
        serializer = serializers.UserBankInfoCreateSerializer(
            data=request.data, context={"request": request}
        )
        if serializer.is_valid(raise_exception=True):
            user_bank_info = serializer.save(
                user=user,
            )
            success_response = ApiResponse(
                success=True,
                code=200,
                data={
                    "user": user.id,
                    "id": user_bank_info.id,
                    **serializer.data,
                },
                message='Created successfully.',
            )
            return Response(success_response, status=status.HTTP_201_CREATED)


class BankInfoUpdateView(views.APIView):
    """
    Update bank info with ownership verification
    
    Security: Only owner can update their bank information
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def put(self, request, pk):
        try:
            # ✅ FIXED: Add ownership check in query
            user_bank_info = UserBankInfo.objects.get(
                id=pk,
                user=request.user  # Ownership check!
            )
        except UserBankInfo.DoesNotExist:
            response = ApiResponse(
                success=False,
                code=404,
                error={
                    'code': 'Not Found',
                    'detail': 'Bank information not found',
                }
            )
            return Response(response, status=status.HTTP_404_NOT_FOUND)

        serializer = serializers.UserBankInfoUpdateSerializer(
            user_bank_info,
            data=request.data,
            partial=True,
            context={'request': request},
        )

        if serializer.is_valid(raise_exception=True):
            serializer.save()

            success_response = ApiResponse(
                success=True,
                code=200,
                data=serializer.data,
                message='User Bank Info updated successfully.',
            )
            return Response(success_response, status=status.HTTP_200_OK)


class BankInfoListView(views.APIView):
    def get(self, request):
        user = request.user

        user_bank_info_list = UserBankInfo.objects.filter(
            user=user,
        )

        serializer = serializers.UserBankInfoListSerializer(
            user_bank_info_list,
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

class BankInfoDeleteView(views.APIView):
    """
    Delete bank info with ownership verification
    
    Security: Only owner can delete their bank information
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def delete(self, request, pk):
        try:
            # ✅ FIXED: Add ownership check in query
            user_bank_info = UserBankInfo.objects.get(
                id=pk,
                user=request.user  # Ownership check!
            )
        except UserBankInfo.DoesNotExist:
            response = ApiResponse(
                success=False,
                code=404,
                error={
                    'code': 'Not Found',
                    'detail': 'Bank information not found',
                }
            )
            return Response(response, status=status.HTTP_404_NOT_FOUND)

        user_bank_info.delete()
        success_response = ApiResponse(
                success=True,
                code=204,
                message='User Bank Info deleted successfully.',
            )
        return Response(success_response, status=status.HTTP_204_NO_CONTENT)

class BankInfoDetailView(views.APIView):
    """
    Get bank info details with ownership verification
    
    Security: Only owner can view their bank information
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, pk):
        try:
            # ✅ FIXED: Add ownership check in query
            user_bank_info = UserBankInfo.objects.get(
                id=pk,
                user=request.user  # Ownership check!
            )
        except UserBankInfo.DoesNotExist:
            response = ApiResponse(
                success=False,
                code=404,
                error={
                    'code': 'Not Found',
                    'detail': 'Bank information not found',
                }
            )
            return Response(response, status=status.HTTP_404_NOT_FOUND)

        serializer = serializers.UserBankInfoListSerializer(
            user_bank_info,
            context={'request': request},
        )

        success_response = ApiResponse(
            success=True,
            code=200,
            data=serializer.data,
            message='Data retrieved successfully.',
        )
        return Response(success_response, status=status.HTTP_200_OK)

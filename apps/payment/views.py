from rest_framework import views, status, permissions
from rest_framework.response import Response
from django.shortcuts import redirect
from django.conf import settings
from utils.response import ApiResponse
from apps.payment.core import PaymentCore
from apps.payment.models import Payment, Zarinpal
from apps.payment.serializers.user import (
    PaymentCreateSerializer,
    PaymentSerializer,
    PaymentDetailSerializer
)

payment = PaymentCore()

# Create your views here.
class PaymentCreateView(views.APIView):
    def post(self, request):
        serializer = PaymentCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            success, data = payment.pay(
                request.user,
                serializer.validated_data
            )

            if success:
                return Response(
                    ApiResponse(
                        success=True,
                        code=201,
                        data= {'id': str(data.id)}
                    )
                )
            else:
                return Response(
                    ApiResponse(
                        success=False,
                        code=500,
                        error=data
                    ),
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        
        except Exception as e:
            return Response(
                ApiResponse(
                    success=False,
                    code=500,
                    error=str(e)
                )
            )

class PaymentRedirectView(views.APIView):
    permission_classes = [permissions.AllowAny]
    def get(self, request):
        try:
            zarinpal = Zarinpal.objects.get(id=request.GET.get('id'))
            url = f'https://{settings.ZARINPAL_URL}.zarinpal.com/pg/StartPay/{zarinpal.authority}'

            return redirect(url)
        
        except Exception as e:
            return Response(
                ApiResponse(
                    success=False,
                    code=500,
                    error=str(e)
                )
            ) 

class PaymentVerifyView(views.APIView):
    permission_classes = [permissions.AllowAny]
    def get(self, request):
        success, data = payment.verify(request)
        
        if success:
            return Response(
                ApiResponse(
                    success=True,
                    code=200,
                    message = data
                )
            )
        
        else:
            return Response(
                ApiResponse(
                    success=False,
                    code=400,
                    message = data
                )
            )

class PaymentListView(views.APIView):
    def get(self, request):
        payments = Payment.objects.filter(user=request.user)

        serializer = PaymentSerializer(payments, many=True)

        return Response(
            ApiResponse(
                success=True,
                code=200,
                data=serializer.data
            )
        )

class PaymentDetailView(views.APIView):
    def get(self, request, pk):
        try:
            payment = Payment.objects.get(id=pk)

            if payment.user != request.user:
                raise Exception('UnAuthorized')
            
            serializer = PaymentDetailSerializer(payment)

            return Response(
                ApiResponse(
                    success=True,
                    code=200,
                    data=serializer.data
                )
            )
        except Exception as e:
            return Response(
                ApiResponse(
                    success=False,
                    code=500,
                    error=str(e)
                )
            ) 

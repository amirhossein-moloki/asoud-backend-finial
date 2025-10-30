from rest_framework import views, status, permissions
from rest_framework.response import Response
from utils.response import ApiResponse
from apps.wallet.models import Wallet, Transaction
from apps.wallet.serializer import (
    WalletCheckSerializer,
    TransactionSerializer,
    WalletPaySerializer,
    WalletSerializer
)
from apps.payment.core import PostPaymentCore
# Create your views here.


class WalletBalanceView(views.APIView):
    def get(self, request):
        try:
            wallet, _ = Wallet.objects.get_or_create(user=request.user)
            
            serializer = WalletSerializer(wallet)
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
                    error=str(e),
                ), 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
class WalletCheckView(views.APIView):
    def post(self, request):
        try:
            wallet, _ = Wallet.objects.get_or_create(user=request.user)
            
            serializer = WalletCheckSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)

            amount = serializer.validated_data['amount']
            
            if wallet.balance >= float(amount):
                return Response(
                    ApiResponse(
                        success=True,
                        code=200,
                        message="Sufficient Balance"
                    )
                )
            
            else :
                return Response(
                    ApiResponse(
                        success=False,
                        code=200,
                        message="Insufficient Balance"
                    )
                )
            
        except Exception as e:
            return Response(
                ApiResponse(
                    success=False,
                    code=500,
                    error=str(e),
                ), 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class WalletPayView(views.APIView):
    def post(self, request):
        try:
            wallet, _ = Wallet.objects.get_or_create(user=request.user)
            
            serializer = WalletPaySerializer(data=request.data)
            serializer.is_valid(raise_exception=True)

            amount = float(serializer.validated_data['amount'])
            
            if wallet.balance >= amount:
                
                post_payment = PostPaymentCore(request.user)
                post_payment.wallet_process(
                    target=serializer.validated_data['target_content'],
                    pk=serializer.validated_data['target_id'],
                    amount=amount,
                    wallet_id=str(wallet.id)
                )

                return Response(
                    ApiResponse(
                        success=True,
                        code=200,
                        message="payment successfull"
                    )
                )
            else :
                return Response(
                    ApiResponse(
                        success=False,
                        code=200,
                        message="Insufficient Balance"
                    )
                )
            
        except Exception as e:
            return Response(
                ApiResponse(
                    success=False,
                    code=500,
                    error=str(e),
                ), 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class TransactionListView(views.APIView):
    def get(self, request):
        try:
            transactions = Transaction.objects.filter(user=request.user)
            
            serializer = TransactionSerializer(transactions, many=True)
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
                    success=True,
                    code=500,
                    error=str(e)
                ),
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


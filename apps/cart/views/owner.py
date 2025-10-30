from rest_framework import views, status, permissions
from rest_framework.response import Response
from utils.response import ApiResponse
from django.db.models import Q
from apps.cart.models import (
    Order,
    OrderItem
)
from apps.cart.serializers.owner import (
    OrderSerializer,
    OrderListSerializer,
    OrderVerifySerializer
)
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer


class OrderVerifyView(views.APIView):
    def put(self, request):
        serializer = OrderVerifySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            order = Order.objects.get(id=serializer.validated_data['id'])
            if order.status != Order.PENDING:
                return Response(
                    ApiResponse(
                        success=False,
                        code=500,
                        error="Order is Not Pending"
                    )
                )

            if serializer.validated_data['verified']:
                order.status = Order.VERIFIED
            else:
                order.status = Order.REJECTED
            
            order.owner_description = serializer.validated_data['description']
            order.save()

            user_id = order.user.id

            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                f"user_{user_id}",
                {
                    "type": "send_notification",
                    "data": {
                        "type": "order",
                        "message": "Order Status Updated By Owner",
                        "order": {
                            "id": str(order.id),
                        },
                    }
                }
            )

            serializer = OrderSerializer(order)

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
        

class OrderListView(views.APIView):
    def get(self, request):
        market_owner_orders = Order.objects.filter(
            Q( items__product__market__user=request.user ) | 
            Q( items__affiliate__market__user=request.user )
        ).distinct()

        serializer = OrderListSerializer(market_owner_orders, many=True)

        return Response(
            ApiResponse(
                success=True,
                code=200,
                data=serializer.data
            )
        )
    
class OrderDetailView(views.APIView):
    def get(self, request, pk:str):
        try:
            order = Order.objects.get(id=pk)
            
            serializer = OrderSerializer(order)
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

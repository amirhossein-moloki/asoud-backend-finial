from rest_framework import views, viewsets, status, permissions
from rest_framework.response import Response
from rest_framework.decorators import action
from utils.response import ApiResponse
from apps.cart.models import (
    Order,
    OrderItem
)
from apps.cart.serializers.user import(
    OrderSerializer,
    Order2Serializer,
    OrderItem2Serializer,
    OrderCreateSerializer,
    OrderCheckOutSerializer,
    OrderItemSerializer,
    OrderItemUpdateSerializer
)
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
import logging
logger = logging.getLogger(__name__)


class CartViewSet(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated]
    
    def get_order(self, request):
        """Helper method to get or create order"""
        return Order.get_or_create_order(request.user)
    
    def list(self, request):
        """Get order contents"""
        order = self.get_order(request)
        print('order', order)
        serializer = Order2Serializer(order)
        return Response(serializer.data)
    
    def add_item(self, request):
        """Add item to cart"""
        order = self.get_order(request)
        serializer = OrderItem2Serializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        product = serializer.validated_data.get('product', None)
        product_name = serializer.validated_data.get('product_name', None)
        affiliate = serializer.validated_data.get('affiliate', None)
        affiliate_name = serializer.validated_data.get('affiliate_name', None)
        quantity = serializer.validated_data.get('quantity', None)
        if product:
            if existing_product := order.items.filter(product=product).first():
                existing_product.quantity += quantity
                existing_product.save()
                serializer = OrderItem2Serializer(existing_product)
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            serializer.save(order=order)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        elif product_name:
            if existing_product := order.items.filter(product__name=product_name).first():
                existing_product.quantity += quantity
                existing_product.save()
                serializer = OrderItem2Serializer(existing_product)
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.save(order=order), status=status.HTTP_201_CREATED)
        if affiliate:
            if existing_affiliate := order.items.filter(affiliate=affiliate).first():
                existing_affiliate.quantity += quantity
                existing_affiliate.save()
                serializer = OrderItem2Serializer(existing_affiliate) 
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            serializer.save(order=order)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        elif affiliate_name:
            if existing_affiliate := order.items.filter(affiliate__name=affiliate_name).first():
                existing_affiliate.quantity += quantity
                existing_affiliate.save()
                serializer = OrderItem2Serializer(existing_affiliate)
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.save(order=order), status=status.HTTP_201_CREATED)
           
    def update_item(self, request, pk=None):
        """Update item quantity in cart"""
        order = self.get_order(request)
        try:
            item = order.items.get(pk=pk)
        except OrderItem.DoesNotExist:
            return Response(
                {"error": "Item not found in order"}, 
                status=status.HTTP_404_NOT_FOUND
            )
    
        serializer = OrderItemUpdateSerializer(
            item, 
            data=request.data, 
            partial=True,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()  # No need to pass order since it's already set
    
        return Response(serializer.data)
    
    def remove_item(self, request, pk=None):
        """Remove item from order"""
        order = self.get_order(request)
        try:
            item = order.items.get(pk=pk)
            item.delete()
            serializer = Order2Serializer(order)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except OrderItem.DoesNotExist:
            return Response(
                {"error": "Item not found in order"}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
    def checkout(self, request):
        order = self.get_order(request)
        serializer = OrderCheckOutSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        
        # Check if item already exists in cart
        if not order.items.exists():
            return Response(
                {"error": "order is empty"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        order.status = Order.PENDING 
        order.description = serializer.validated_data.get('description', 'Order placed')
        order.type = serializer.validated_data.get('type', Order.ONLINE)
        order.save()

        serializer = Order2Serializer(order)
        return Response(
            {"message": "Order placed successfully", "order": serializer.data},
            status=status.HTTP_200_OK
        )

class OrderCreateView(views.APIView):
    def post(self, request):
        serializer = OrderCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        obj = serializer.save(user=request.user)
        
        if obj.items.first().product:
            user_id = obj.items.first().product.market.user.id
        else:
            user_id = obj.items.first().affiliate.market.user.id

        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f"user_{user_id}",
            {
                "type": "send_notification",
                "data": {
                    "type": "order",
                    "message": "New Order Added",
                    "order": {
                        "id": str(obj.id),
                    },
                }
            }
        )

        serialized_data = OrderSerializer(obj).data

        return Response(
            ApiResponse(
                success=True,
                code=200,
                data=serialized_data
            )
        )

class OrderListView(views.APIView):
    def get(self, request):
        orders = Order.objects.filter(user=request.user)

        serializer = OrderSerializer(orders, many=True)
        return Response(
            ApiResponse(
                success=True,
                code=200,
                data=serializer.data
            )
        )

class OrderDetailView(views.APIView):
    """
    Get order details with ownership verification
    
    Security: Only owner can view their orders
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, pk:str):
        try:
            # ✅ FIXED: Add ownership check
            order = Order.objects.select_related('user').get(
                id=pk,
                user=request.user  # Ownership check!
            )

            serializer = OrderSerializer(order)
            return Response(
                ApiResponse(
                    success=True,
                    code=200,
                    data=serializer.data
                ),
                status=status.HTTP_200_OK
            )
        
        except Order.DoesNotExist:
            # ✅ FIXED: Proper exception handling
            return Response(
                ApiResponse(
                    success=False,
                    code=404,
                    error="Order not found"  # Generic message
                ),
                status=status.HTTP_404_NOT_FOUND
            )
        
        except Exception as e:
            # ✅ FIXED: Log but don't expose details
            logger.error(f"Error in OrderDetailView: {str(e)}", exc_info=True)
            return Response(
                ApiResponse(
                    success=False,
                    code=500,
                    error="An internal error occurred"  # Generic message
                ),
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class OrderUpdateView(views.APIView):
    """
    Update order with ownership verification
    
    Security: Only owner can update their own orders
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def put(self, request, pk:str):
        try:
            # ✅ FIXED: Add ownership check and select_related
            order = Order.objects.select_related('user').prefetch_related('items').get(
                id=pk,
                user=request.user  # Ownership check!
            )
            
            # ✅ Check if order is editable
            if order.status not in [Order.PENDING, Order.DRAFT]:
                return Response(
                    ApiResponse(
                        success=False,
                        code=400,
                        error="Order cannot be modified in current status"
                    ),
                    status=status.HTTP_400_BAD_REQUEST
                )

            serializer = OrderCreateSerializer(order, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)

            # ✅ FIXED: Don't override user
            obj = serializer.save()

            # ✅ FIXED: Safe navigation with proper checks
            try:
                first_item = obj.items.first()
                if first_item:
                    if first_item.product and first_item.product.market:
                        market_owner_id = first_item.product.market.user.id
                    elif first_item.affiliate and first_item.affiliate.market:
                        market_owner_id = first_item.affiliate.market.user.id
                    else:
                        market_owner_id = None
                    
                    if market_owner_id:
                        channel_layer = get_channel_layer()
                        async_to_sync(channel_layer.group_send)(
                            f"user_{market_owner_id}",
                            {
                                "type": "send_notification",
                                "data": {
                                    "type": "order",
                                    "message": "An Order Updated",
                                    "order": {
                                        "id": str(obj.id),
                                    },
                                }
                            }
                        )
            except Exception as notif_error:
                # ✅ Don't fail if notification fails
                logger.warning(f"Failed to send notification: {notif_error}")

            serialized_data = OrderSerializer(obj).data

            return Response(
                ApiResponse(
                    success=True,
                    code=200,
                    data=serialized_data
                ),
                status=status.HTTP_200_OK
            )
        
        except Order.DoesNotExist:
            return Response(
                ApiResponse(
                    success=False,
                    code=404,
                    error="Order not found"
                ),
                status=status.HTTP_404_NOT_FOUND
            )
        
        except Exception as e:
            logger.error(f"Error in OrderUpdateView: {str(e)}", exc_info=True)
            return Response(
                ApiResponse(
                    success=False,
                    code=500,
                    error="An unexpected error occurred."
                ),
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class OrderDeleteView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def delete(self, request, pk:str):
        try:
            # ✅ FIXED: Add ownership check
            order = Order.objects.get(
                id=pk,
                user=request.user  # Ownership check!
            )
            
            # ✅ Business rule: Only draft orders can be deleted
            if order.status != Order.DRAFT:
                return Response(
                    ApiResponse(
                        success=False,
                        code=400,
                        error="Only draft orders can be deleted"
                    ),
                    status=status.HTTP_400_BAD_REQUEST
                )

            order.delete()
        
            return Response(
                ApiResponse(
                    success=True,
                    code=204,
                    message="Order deleted successfully"
                ),
                status=status.HTTP_204_NO_CONTENT
            )
        
        except Order.DoesNotExist:
            return Response(
                ApiResponse(
                    success=False,
                    code=404,
                    error="Order not found"
                ),
                status=status.HTTP_404_NOT_FOUND
            )
        
        except Exception as e:
            logger.error(f"Error in OrderDeleteView: {str(e)}", exc_info=True)
            return Response(
                ApiResponse(
                    success=False,
                    code=500,
                    error="An internal error occurred"
                ),
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

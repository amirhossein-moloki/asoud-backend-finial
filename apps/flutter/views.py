from rest_framework import views, status, permissions
from rest_framework.response import Response
from utils.response import ApiResponse
from apps.core.base_views import BaseDetailView

from apps.market.models import Market
from apps.market.serializers.user_serializers import (
    MarketListSerializer,
    MarketDetailSerializer
)
from apps.item.models import Item
from apps.item.serializers.owner_serializers import ItemDetailSerializer
from apps.advertise.models import Advertisement
from apps.advertise.serializers import AdvertiseSerializer
from apps.users.models import UserBankInfo
from apps.users.serializers import UserBankInfoListSerializer
# Create your views here.


class MarketDetailView(views.APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        market_id = request.GET.get('id')
        if not market_id:
            return Response(
                ApiResponse(
                    success=False,
                    code=400,
                    error="Market Id Not Provided"
                ),
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            market = Market.objects.get(id=market_id)
        except Market.DoesNotExist:
            return Response(
                ApiResponse(
                    success=False,
                    code=404,
                    error="Market Not Found"
                ),
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = MarketListSerializer(market)
        return Response(
            ApiResponse(
                success=True,
                code=200,
                data=serializer.data
            )
        )
        

class ItemDetailView(views.APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        item_id = request.GET.get('id')
        if not item_id:
            return Response(
                ApiResponse(
                    success=False,
                    code=400,
                    error="Item Id Not Provided"
                ),
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            item = Item.objects.get(id=item_id)
        except Item.DoesNotExist:
            return Response(
                ApiResponse(
                    success=False,
                    code=404,
                    error="Item Not Found"
                ),
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = ItemDetailSerializer(item)

        return Response(
            ApiResponse(
                success=True,
                code=200,
                data=serializer.data
            )
        )


class AdvertizeDetailView(views.APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        ad_id = request.GET.get('id')
        if not ad_id:
            return Response(
                ApiResponse(
                    success=False,
                    code=400,
                    error="Advertisement Id Not Provided"
                ),
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            ad = Advertisement.objects.get(id=ad_id)
        except Advertisement.DoesNotExist:
            return Response(
                ApiResponse(
                    success=False,
                    code=404,
                    error="Advertisement Not Found"
                ),
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = AdvertiseSerializer(ad)

        return Response(
            ApiResponse(
                success=True,
                code=200,
                data=serializer.data
            )
        )


class VisitCardView(BaseDetailView):
    """
    Get market visit card details
    """
    permission_classes = [permissions.AllowAny]
    
    def get_queryset(self):
        return Market.objects.select_related(
            'sub_category',
            'location',
            'contact'
        ).prefetch_related(
            'viewed_by'
        )
    
    def get_serializer_class(self):
        return MarketDetailSerializer

    def get(self, request, business_id):
        try:
            market = self.get_queryset().get(business_id=business_id)
            serializer = MarketDetailSerializer(market)
            return self.success_response(data=serializer.data)
        
        except Market.DoesNotExist:
            return self.error_response("Market not found", 404)
        except Exception as e:
            return self.error_response(f"Error retrieving market: {str(e)}", 500)
        

class BankCardView(BaseDetailView):
    """
    Get bank card information
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return UserBankInfo.objects.filter(user=self.request.user)
    
    def get_serializer_class(self):
        return UserBankInfoListSerializer

    def get(self, request, pk):
        try:
            bank_info = self.get_queryset().get(id=pk)
            serializer = UserBankInfoListSerializer(bank_info)
            return self.success_response(data=serializer.data)
        
        except UserBankInfo.DoesNotExist:
            return self.error_response("Bank info not found", 404)
        except Exception as e:
            return self.error_response(f"Error retrieving bank info: {str(e)}", 500)

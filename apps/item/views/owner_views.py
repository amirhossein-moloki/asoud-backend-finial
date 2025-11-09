from rest_framework import views, status
from rest_framework.response import Response
from django.utils.translation import gettext_lazy as _

from utils.response import ApiResponse

from apps.item.serializers.owner_serializers import (
    ItemCreateSerializer,
    ItemDiscountCreateSerializer,
    ItemDetailSerializer,
    ItemListSerializer,
    ItemThemeListSerializer,
    ItemThemeCreateSerializer,
    ItemShippingCreateSerializer,
    ItemShipListSerializer
)
from apps.item.models import Item, ItemTheme
from apps.market.models import Market
from apps.advertise.core  import AdvertisementCore

# affiliate products
from apps.affiliate.models import (
    AffiliateProduct, 
    AffiliateProductTheme
)
from apps.affiliate.serializers.user import (
    AffiliateProductThemeListSerializer,
    AffiliateProductListSerializer
)

class ItemCreateAPIView(views.APIView):
    def post(self, request):
        serializer = ItemCreateSerializer(
            data=request.data,
            context={'request': request},
        )

        if serializer.is_valid(raise_exception=True):
            item = serializer.save()

            item_id = item.id

            if item.is_requirement:
                ad_data = AdvertisementCore.create_advertisement_for_item(item)


            success_response = ApiResponse(
                success=True,
                code=200,
                data={
                    'item': item_id,
                    **serializer.data,
                },
                message='Item created successfully.',
            )

            return Response(success_response, status=status.HTTP_201_CREATED)


class ItemDiscountCreateAPIView(views.APIView):
    def post(self, request, pk):
        item = Item.objects.get(id=pk)

        serializer = ItemDiscountCreateSerializer(
            data=request.data,
            context={'request': request},
        )
        serializer.is_valid()
        serializer.save(item=item)
        percentage = serializer.validated_data.get('percentage')
        item.main_price = item.main_price - (item.main_price * percentage / 100)
        item.save()
        success_response = ApiResponse(
                success=True,
                code=200,
                data={
                    **serializer.data,
                    },
                message='ItemDiscount created successfully.',
                )

        return Response(success_response, status=status.HTTP_201_CREATED)
    
class ItemShippingCreateAPIView(views.APIView):
    def post(self, request, pk):
        try:
            item = Item.objects.get(id=pk)
        except  Item.DoesNotExist:
            return Response(
                ApiResponse(
                    success=False,
                    code=404,
                    error="Item Not Found"
                )
            )
        serializer = ItemShippingCreateSerializer(
            data=request.data,
            context={'request': request},
        )
        serializer.is_valid()
        serializer.save(item=item)
        success_response = ApiResponse(
                success=True,
                code=200,
                data={
                    **serializer.data,
                    },
                message='Item ship created successfully.',
                )

        return Response(success_response, status=status.HTTP_201_CREATED)


class ItemShippingListAPIView(views.APIView):
    def get(self, request, pk):
        try:
            item = Item.objects.get(id=pk)
            shipping_options = item.ships.all()
        except Item.DoesNotExist:
            return Response(
                ApiResponse(
                    success=False,
                    code=404,
                    error="Item Not Found"
                )
            )
        serializer = ItemShipListSerializer(
            shipping_options,
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

class ItemListAPIView(views.APIView):
    def get(self, request, pk):
        item_list = Item.objects.filter(
            market=pk
        )

        serializer = ItemListSerializer(
            item_list,
            many=True,
            context={"request": request},
        )

        with_affiliate = request.GET.get('affiliate')

        if with_affiliate:
            affiliate_product_list = AffiliateProduct.objects.filter(
                market=pk
            )
            
            aff_serializer = AffiliateProductListSerializer(
                affiliate_product_list,
                many=True,
                context={"request": request},
            )

            success_response = ApiResponse(
                success=True,
                code=200,
                data=serializer.data + aff_serializer.data,
                message='Data retrieved successfully'
            )
            
        else:
            success_response = ApiResponse(
                success=True,
                code=200,
                data=serializer.data,
                message='Data retrieved successfully'
            )

        return Response(success_response)


class ItemDetailAPIView(views.APIView):
    def get(self, request, pk):
        try:
            item = Item.objects.get(id=pk)
        except:
            return Response(
                ApiResponse(
                    success=False,
                    code=404,
                    error="Item Not Found"
                )
            )
        
        serializer = ItemDetailSerializer(
            item,
            context={"request": request},
        )

        success_response = ApiResponse(
            success=True,
            code=200,
            data=serializer.data,
            message='Data retrieved successfully',
        )

        return Response(success_response)


class MarketThemeCreateAPIView(views.APIView):
    def post(self, request, pk):
        try:
            market = Market.objects.get(id=pk)
        except:
            return Response(
                ApiResponse(
                    success=False,
                    code=404,
                    error="Market Not Found"
                )
            )
        
        serializer = ItemThemeCreateSerializer(
            data=request.data,
            context={'request': request},
        )

        if serializer.is_valid(raise_exception=True):
            serializer.save(
                market=market,
            )

            success_response = ApiResponse(
                success=True,
                code=200,
                data={
                    **serializer.data,
                },
                message='Item theme created successfully.',
            )

            return Response(success_response, status=status.HTTP_201_CREATED)


class MarketThemeListAPIView(views.APIView):
    def get(self, request, pk):
        try:
            market = Market.objects.get(id=pk)
        except:
            return Response(
                ApiResponse(
                    success=False,
                    code=404,
                    error="Market Not Found"
                )
            )
    
        product_theme_list = ItemTheme.objects.filter(market=market)

        serializer = ItemThemeListSerializer(
            product_theme_list,
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


class ItemThemeUpdateAPIView(views.APIView):
    def put(self, request, pk):
        try:
            product_theme = ItemTheme.objects.get(id=pk)
        except:
            return Response(
                ApiResponse(
                    success=False,
                    code=404,
                    error="Item Theme Not Found"
                )
            )
        item_id = request.data.get("item")
        index = request.data.get("index")

        if not item_id or not index:
            response = ApiResponse(
                success=False,
                code=400,
                error={
                    'code': 'bad_request',
                    'detail': 'Invalid format. "both item and index must be provided"',
                }
            )
            return Response(response)

        try:
            item = Item.objects.get(id=item_id)
            item.theme = product_theme
            item.theme_index = index
            item.save()
        except Exception as e:
            fail_response = ApiResponse(
                success=False,
                code=400,
                data={},
                message=str(e),
            )
            return Response (
                fail_response, 
                status=status.HTTP_400_BAD_REQUEST
            )
            
        success_response = ApiResponse(
            success=True,
            code=200,
            data={},
            message='Item theme updated successfully.',
        )
        return Response(success_response, status=status.HTTP_200_OK)

class ItemThemeDeleteAPIView(views.APIView):
    def delete(self, request, pk):

        try:
            item = Item.objects.get(id=pk)
            item.theme = None
            item.theme_index = None
            item.save()
        except:
            pass
            
        success_response = ApiResponse(
            success=True,
            code=200,
            data={},
            message='Item theme removed successfully.',
        )
        return Response(success_response, status=status.HTTP_200_OK)

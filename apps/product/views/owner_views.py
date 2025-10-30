from rest_framework import views, status
from rest_framework.response import Response
from django.utils.translation import gettext_lazy as _

from utils.response import ApiResponse

from apps.product.serializers.owner_serializers import (
    ProductCreateSerializer,
    ProductDiscountCreateSerializer,
    ProductDetailSerializer,
    ProductListSerializer,
    ProductThemeListSerializer,
    ProductThemeCreateSerializer,
    ProductShippingCreateSerializer,
    ProductShipListSerializer
)
from apps.product.models import Product, ProductTheme
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

class ProductCreateAPIView(views.APIView):
    def post(self, request):
        serializer = ProductCreateSerializer(
            data=request.data,
            context={'request': request},
        )

        if serializer.is_valid(raise_exception=True):
            product = serializer.save()

            product_id = product.id

            if product.is_requirement:
                ad_data = AdvertisementCore.create_advertisement_for_product(product)


            success_response = ApiResponse(
                success=True,
                code=200,
                data={
                    'product': product_id,
                    **serializer.data,
                },
                message='Product created successfully.',
            )

            return Response(success_response, status=status.HTTP_201_CREATED)


class ProductDiscountCreateAPIView(views.APIView):
    def post(self, request, pk):
        product = Product.objects.get(id=pk)

        serializer = ProductDiscountCreateSerializer(
            data=request.data,
            context={'request': request},
        )
        serializer.is_valid()
        serializer.save(product=product)
        percentage = serializer.validated_data.get('percentage')
        product.main_price = product.main_price - (product.main_price * percentage / 100)
        product.save()
        success_response = ApiResponse(
                success=True,
                code=200,
                data={
                    **serializer.data,
                    },
                message='ProductDiscount created successfully.',
                )

        return Response(success_response, status=status.HTTP_201_CREATED)
    
class ProductShippingCreateAPIView(views.APIView):
    def post(self, request, pk):
        try:
            product = Product.objects.get(id=pk)
        except  Product.DoesNotExist:
            return Response(
                ApiResponse(
                    success=False,
                    code=404,
                    error="Product Not Found"
                )
            )
        serializer = ProductShippingCreateSerializer(
            data=request.data,
            context={'request': request},
        )
        serializer.is_valid()
        serializer.save(product=product)
        success_response = ApiResponse(
                success=True,
                code=200,
                data={
                    **serializer.data,
                    },
                message='Product ship created successfully.',
                )

        return Response(success_response, status=status.HTTP_201_CREATED)


class ProductShippingListAPIView(views.APIView):
    def get(self, request, pk):
        try:
            product = Product.objects.get(id=pk)
            shipping_options = product.ships.all()
        except Product.DoesNotExist:
            return Response(
                ApiResponse(
                    success=False,
                    code=404,
                    error="Product Not Found"
                )
            )
        serializer = ProductShipListSerializer(
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

class ProductListAPIView(views.APIView):
    def get(self, request, pk):
        product_list = Product.objects.filter(
            market=pk
        )

        serializer = ProductListSerializer(
            product_list,
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


class ProductDetailAPIView(views.APIView):
    def get(self, request, pk):
        try:
            product = Product.objects.get(id=pk)
        except:
            return Response(
                ApiResponse(
                    success=False,
                    code=404,
                    error="Product Not Found"
                )
            )
        
        serializer = ProductDetailSerializer(
            product,
            context={"request": request},
        )

        success_response = ApiResponse(
            success=True,
            code=200,
            data=serializer.data,
            message='Data retrieved successfully',
        )

        return Response(success_response)
    
    
class ProductDetailAPIView(views.APIView):
    def get(self, request, pk):
        try:
            product = Product.objects.get(id=pk)
        except:
            return Response(
                ApiResponse(
                    success=False,
                    code=404,
                    error="Product Not Found"
                )
            )
        
        serializer = ProductDetailSerializer(
            product,
            context={"request": request},
        )

        success_response = ApiResponse(
            success=True,
            code=200,
            data=serializer.data,
            message='Data retrieved successfully',
        )

        return Response(success_response)


class ProductThemeCreateAPIView(views.APIView):
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
        
        serializer = ProductThemeCreateSerializer(
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
                message='Product theme created successfully.',
            )

            return Response(success_response, status=status.HTTP_201_CREATED)


class ProductThemeListAPIView(views.APIView):
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
    
        product_theme_list = ProductTheme.objects.filter(market=market)

        serializer = ProductThemeListSerializer(
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


class ProductThemeUpdateAPIView(views.APIView):
    def put(self, request, pk):
        try:
            product_theme = ProductTheme.objects.get(id=pk)
        except:
            return Response(
                ApiResponse(
                    success=False,
                    code=404,
                    error="Product Theme Not Found"
                )
            )
        product = request.data.get("product")
        index = request.data.get("index")

        if not product or not index:
            response = ApiResponse(
                success=False,
                code=400,
                error={
                    'code': 'bad_request',
                    'detail': 'Invalid format. "both product and index must be provided"',
                }
            )
            return Response(response)

        try:
            product = Product.objects.get(id=product)
            product.theme = product_theme
            product.theme_index = index
            product.save()
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
            message='Product theme updated successfully.',
        )
        return Response(success_response, status=status.HTTP_200_OK)

class ProductThemeDeleteAPIView(views.APIView):
    def delete(self, request, pk):

        try:
            product = Product.objects.get(id=pk)
            product.theme = None
            product.theme_index = None
            product.save()
        except:
            pass
            
        success_response = ApiResponse(
            success=True,
            code=200,
            data={},
            message='Product theme removed successfully.',
        )
        return Response(success_response, status=status.HTTP_200_OK)

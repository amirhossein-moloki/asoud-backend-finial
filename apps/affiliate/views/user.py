from rest_framework import views, status
from rest_framework.response import Response
from utils.response import ApiResponse
from apps.product.models import Product
from apps.product.serializers.owner_serializers import (
    ProductDetailSerializer,
    ProductListSerializer
)
from apps.affiliate.serializers.user import (
    AffiliateProductCreateSerializer,
    AffiliateProductDetailSerializer,
    AffiliateProductListSerializer,
    AffiliateProductThemeCreateSerializer,
    AffiliateProductThemeListSerializer
)
from apps.affiliate.models import (
    AffiliateProduct,
    AffiliateProductImage,
    AffiliateProductTheme
)
from apps.market.models import Market

# authorization will be done later 

class ProductsForAffiliateListView(views.APIView):
    def get(self, request):
        products = Product.objects.filter(
            is_marketer=True, 
            status='published'
        )

        if price_lt := request.GET.get('price_lt'):
            products = products.filter(main_price__lte=price_lt)
        
        if price_gt := request.GET.get('price_gt'):
            products = products.filter(main_price__gte=price_gt)

        if type := request.GET.get('type'):
            products = products.filter(type=type)
        
        if order_by := request.GET.get('order_by') and \
            order_by in ['price', '-price' 'created_at', '-created_at']:
            products = products.order_by(order_by)
        
        serializer = ProductListSerializer(products, many=True)

        return Response(
            ApiResponse(
                success=True,
                code=200,
                data=serializer.data
            )
        )

class AffiliateProductDetailBeforeCreateView(views.APIView):
    def get(self, request, pk):
        try:
            product = Product.objects.get(id=pk)
        except Product.DoesNotExist:
            return Response(
                ApiResponse(
                    success=False,
                    code=404,
                    error="Product Not Found"
                )
            )
        
        serializer = ProductDetailSerializer(product)

        return Response(
            ApiResponse(
                success=True,
                code=200,
                data=serializer.data
            )
        )

class AffiliateProductCreateView(views.APIView):
    def post(self, request):
        serializer = AffiliateProductCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        obj = serializer.save()

        serialized_data = AffiliateProductDetailSerializer(obj).data
        
        return Response(
            ApiResponse(
                success=True,
                code=201,
                data=serialized_data
            )
        )

class AffiliateProductsListView(views.APIView):
    def get(self, request, pk):
        try:
            market = Market.objects.get(id=pk)

            products = AffiliateProduct.objects.filter(
                market=market
            )

            serializer = AffiliateProductListSerializer(products, many=True)

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
                ),
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class AffiliateProductDetailView(views.APIView):
    def get(self, request, pk):
        try:
            product = AffiliateProduct.objects.get(id=pk)
        except Product.DoesNotExist:
            return Response(
                ApiResponse(
                    success=False,
                    code=404,
                    error="Affiliate Product Not Found"
                )
            )
        
        serializer = AffiliateProductDetailSerializer(product)

        return Response(
            ApiResponse(
                success=True,
                code=200,
                data=serializer.data
            )
        )

class AffiliateProductUpdateView(views.APIView):
    def put(self, request, pk):
        try:
            product = AffiliateProduct.objects.get(id=pk)
            serializer = AffiliateProductCreateSerializer(product, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)

            obj = serializer.save(
                user = request.user
            )

            serialized_data = AffiliateProductDetailSerializer(obj).data
            
            return Response(
                ApiResponse(
                    success=True,
                    code=200,
                    data=serialized_data
                )
            )
        
        except Exception as e:
            return Response(
                ApiResponse(
                    success=False,
                    code=500,
                    error=str(e)
                ),
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class AffiliateProductDeleteView(views.APIView):
    def delete(self, request, pk):
        try:
            product = AffiliateProduct.objects.get(id=pk)
            
            # authorize
            product.delete()

            return Response(
                ApiResponse(
                    success=True,
                    code=204
                ),
                status=status.HTTP_204_NO_CONTENT
            )

        except Exception as e:
            return Response(
                ApiResponse(
                    success=False,
                    code=500,
                    error=str(e)
                ),
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class AffiliateProductThemeCreateAPIView(views.APIView):
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
        
        serializer = AffiliateProductThemeCreateSerializer(
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
                message='Affiliate Product theme created successfully.',
            )

            return Response(success_response, status=status.HTTP_201_CREATED)

class AffiliateProductThemeListAPIView(views.APIView):
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
    
        product_theme_list = AffiliateProductTheme.objects.filter(market=market)

        serializer = AffiliateProductThemeListSerializer(
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

class AffiliateProductThemeUpdateAPIView(views.APIView):
    def put(self, request, pk):
        try:
            product_theme = AffiliateProductTheme.objects.get(id=pk)
        except:
            return Response(
                ApiResponse(
                    success=False,
                    code=404,
                    error="Affiliate Product Theme Not Found"
                )
            )
        products = request.data.get("products", [])

        if not isinstance(products, list):
            response = ApiResponse(
                success=False,
                code=400,
                error={
                    'code': 'bad_request',
                    'detail': 'Invalid format. "products" should be a list.',
                }
            )
            return Response(response)

        for product_id in products:
            try:
                product = AffiliateProduct.objects.get(id=product_id)
                product.theme = product_theme
                product.save()
            except:
                pass
            
        success_response = ApiResponse(
            success=True,
            code=200,
            data={},
            message='Affiliate Product theme updated successfully.',
        )
        return Response(success_response, status=status.HTTP_200_OK)



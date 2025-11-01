from rest_framework import views, status, permissions
from rest_framework.response import Response
from utils.response import ApiResponse
from apps.market.models import Market, MarketView
from apps.market.serializers.user_serializers import MarketListSerializer
from apps.product.models import Product
from apps.product.serializers.owner_serializers import (
    ProductDetailSerializer,
    ProductListSerializer    
)
from django.shortcuts import render
from django.http import Http404

# Create your views here.
class MarketDetailView(views.APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request): 
        host = request.get_host()
        market_identifier = host.split('.')[0]
        
        try:
            # Try to find by subdomain first, then by business_id
            market = Market.objects.filter(
                subdomain=market_identifier,
                status=Market.PUBLISHED
            ).first()
            
            if not market:
                market = Market.objects.get(
                    business_id=market_identifier,
                    status=Market.PUBLISHED
                )
        except Market.DoesNotExist:
            return Response(
                ApiResponse(
                    success=False,
                    code=404,
                    error="Market Not Found"
                ),
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Track view if user is authenticated
        if request.user.is_authenticated:
            MarketView.objects.get_or_create(
                user=request.user,
                market=market
            )
        
        # Increment view count
        market.view_count += 1
        market.save(update_fields=['view_count'])
        
        serializer = MarketListSerializer(market, context={'request': request})

        return Response(
            ApiResponse(
                success=True,
                code=200,
                data=serializer.data
            )
        )


class MarketStoreView(views.APIView):
    """Render the store frontend template"""
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        host = request.get_host()
        market_identifier = host.split('.')[0]
        
        try:
            # Try to find by subdomain first, then by business_id
            market = Market.objects.filter(
                subdomain=market_identifier,
                status=Market.PUBLISHED
            ).first()
            
            if not market:
                market = Market.objects.get(
                    business_id=market_identifier,
                    status=Market.PUBLISHED
                )
        except Market.DoesNotExist:
            raise Http404("Store not found")
        
        # Track view if user is authenticated
        if request.user.is_authenticated:
            MarketView.objects.get_or_create(
                user=request.user,
                market=market
            )
        
        # Increment view count
        market.view_count += 1
        market.save(update_fields=['view_count'])
        
        context = {
            'market': market,
            'products': market.products.filter(is_active=True)[:12],  # Show first 12 products
            'slider_images': market.slider.all()[:5],  # Show up to 5 slider images
        }
        
        return render(request, 'market/store.html', context)
        

class ProductListView(views.APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        host = request.get_host()
        market_identifier = host.split('.')[0]

        try:
            market = Market.objects.get(business_id=market_identifier)
        except Market.DoesNotExist:
            return Response(
                ApiResponse(
                    success=False,
                    code=404,
                    error="Market Not Found"
                ),
                status=status.HTTP_404_NOT_FOUND
            )
        
        products = Product.objects.filter(market=market)
        
        serializer = ProductListSerializer(products, many=True)

        return Response(
            ApiResponse(
                success=True,
                code=200,
                data=serializer.data
            )
        )


class ProductDetailView(views.APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request, pk):
        host = request.get_host()
        market_identifier = host.split('.')[0]
        
        try:
            product = Product.objects.get(id=pk)
        except Product.DoesNotExist:
            return Response(
                ApiResponse(
                    success=False,
                    code=404,
                    error="Product Not Found"
                ),
                status=status.HTTP_404_NOT_FOUND
            )

        try:
            market = Market.objects.get(business_id=market_identifier)
        except Market.DoesNotExist:
            return Response(
                ApiResponse(
                    success=False,
                    code=404,
                    error="Market Not Found"
                ),
                status=status.HTTP_404_NOT_FOUND
            )
        
        if product.market != market:
            return Response(
                ApiResponse(
                    success=False,
                    code=400,
                    error="Product and Market Mismatch"
                ),
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = ProductDetailSerializer(product)

        return Response(
            ApiResponse(
                success=True,
                code=200,
                data=serializer.data
            )
        )
        
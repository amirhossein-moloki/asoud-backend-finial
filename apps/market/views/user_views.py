from rest_framework import views, status
from rest_framework.response import Response
from django.utils.translation import gettext_lazy as _
from django.core.paginator import Paginator
from django.db.models import Q, Count, Sum, Avg, F
from django.utils import timezone

from utils.response import ApiResponse
from apps.core.api_optimization import OptimizedAPIView, APIResponseOptimizer
from apps.core.caching import cache_manager, cache_result
from apps.core.performance import QueryProfiler

from apps.market.models import (
    Market,
    MarketBookmark,
)

from apps.market.serializers.user_serializers import (
    MarketListSerializer,
    MarketReportCreateSerializer,
)


class MarketListAPIView(OptimizedAPIView):
    """
    Optimized market list view with performance enhancements.
    
    This view provides a list of markets owned by the authenticated user
    with advanced performance optimizations including query profiling,
    select_related, and prefetch_related for efficient database access.
    
    Attributes:
        permission_classes: IsAuthenticated - Requires authentication
    """
    
    def get(self, request, format=None):
        user_obj = self.request.user
        
        with QueryProfiler():
            # Get optimized queryset with select_related and prefetch_related
            market_list = Market.objects.filter(
                user=user_obj,
            ).select_related(
                'sub_category',
                'location',
                'contact'
            ).prefetch_related(
                'products',
                'viewed_by'
            ).annotate(
                products_count=Count('products'),
                published_products=Count('products', filter=Q(products__status='published')),
                total_sales=Sum(
                    'products__orderitem__quantity',
                    filter=Q(products__orderitem__order__is_paid=True)
                ),
                total_revenue=Sum(
                    F('products__orderitem__quantity') * F('products__main_price'),
                    filter=Q(products__orderitem__order__is_paid=True)
                ),
                average_product_price=Avg('products__main_price'),
                low_stock_products=Count('products', filter=Q(products__stock__lte=10))
            ).order_by('-created_at')

            # Apply pagination
            page_size = int(request.GET.get('page_size', 20))
            page_number = int(request.GET.get('page', 1))
            
            paginator = Paginator(market_list, page_size)
            page = paginator.get_page(page_number)

            serializer = MarketListSerializer(
                page.object_list,
                many=True,
                context={"request": request},
            )

            # Create optimized response
            response_data = {
                'results': serializer.data,
                'pagination': {
                    'count': paginator.count,
                    'total_pages': paginator.num_pages,
                    'current_page': page.number,
                    'has_next': page.has_next(),
                    'has_previous': page.has_previous(),
                    'next_page': page.next_page_number() if page.has_next() else None,
                    'previous_page': page.previous_page_number() if page.has_previous() else None,
                }
            }

            success_response = ApiResponse(
                success=True,
                code=200,
                data=response_data,
                message='Data retrieved successfully'
            )

            return Response(success_response)


class PublicMarketListAPIView(OptimizedAPIView):
    """
    Optimized public market list view with caching and performance enhancements.
    
    This view provides a public list of published markets with advanced
    caching, filtering, and pagination capabilities for optimal performance.
    
    Attributes:
        permission_classes: [] - No authentication required (public access)
    """
    permission_classes = []  # Allow any user to access
    
    @cache_result(timeout=300, key_prefix="public_markets")
    def get(self, request, format=None):
        with QueryProfiler():
            # Get search and filter parameters
            search_term = request.GET.get('search', '').strip()
            category_id = request.GET.get('category', None)
            verified_only = request.GET.get('verified', 'false').lower() == 'true'
            
            # Build optimized queryset
            market_list = Market.objects.filter(
                status=Market.PUBLISHED  # Only show published markets
            ).select_related(
                'sub_category',
                'location',
                'contact',
                'user'
            ).prefetch_related(
                'viewed_by',
                'products'
            ).annotate(
                products_count=Count('products'),
                published_products=Count('products', filter=Q(products__status='published')),
                average_product_price=Avg('products__main_price'),
                total_views=Count('viewed_by')
            ).order_by('-total_views', '-created_at')

            # Apply filters
            if verified_only:
                market_list = market_list.filter(is_verified=True)
            
            if category_id:
                market_list = market_list.filter(sub_category_id=category_id)
            
            if search_term:
                market_list = market_list.filter(
                    Q(name__icontains=search_term) |
                    Q(description__icontains=search_term) |
                    Q(business_id__icontains=search_term)
                )

            # Apply pagination (robust parsing)
            try:
                page_size = int(request.GET.get('page_size', 20))
            except (TypeError, ValueError):
                page_size = 20
            page_size = min(max(page_size, 1), 100)
            try:
                page_number = int(request.GET.get('page', 1))
            except (TypeError, ValueError):
                page_number = 1
            
            paginator = Paginator(market_list, page_size)
            page = paginator.get_page(page_number)

            serializer = MarketListSerializer(
                page.object_list,
                many=True,
                context={"request": request},
            )

            # Create optimized response
            response_data = {
                'results': serializer.data,
                'pagination': {
                    'count': paginator.count,
                    'total_pages': paginator.num_pages,
                    'current_page': page.number,
                    'has_next': page.has_next(),
                    'has_previous': page.has_previous(),
                    'next_page': page.next_page_number() if page.has_next() else None,
                    'previous_page': page.previous_page_number() if page.has_previous() else None,
                },
                'filters': {
                    'search_term': search_term,
                    'category_id': category_id,
                    'verified_only': verified_only,
                }
            }

            success_response = ApiResponse(
                success=True,
                code=200,
                data=response_data,
                message='Data retrieved successfully'
            )

            return Response(success_response)


class MarketReportAPIView(views.APIView):
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
        
        user = self.request.user

        serializer = MarketReportCreateSerializer(
            data=request.data,
            context={'request': request},
        )

        if serializer.is_valid(raise_exception=True):
            serializer.save(
                market=market,
                creator=user,
            )

            success_response = ApiResponse(
                success=True,
                code=200,
                data={
                    **serializer.data,
                },
                message='Market report created successfully.',
            )

            return Response(success_response, status=status.HTTP_201_CREATED)

        response = ApiResponse(
            success=False,
            code=500,
            error={
                'code': 'server_error',
                'detail': 'Server error',
            }
        )

        return Response(response, status=status.HTTP_200_OK)


class MarketBookmarkAPIView(views.APIView):
    def post(self, request, pk):
        user = self.request.user
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
        
        market_bookmark, is_created = MarketBookmark.objects.get_or_create(
            user=user,
            market=market,
        )

        # If the market is already bookmarked by the user
        # Then deactivate the bookmark
        if not is_created:
            if market_bookmark.is_active == False:
                market_bookmark.is_active = True
                market_bookmark.save()

                success_response = ApiResponse(
                    success=True,
                    code=200,
                    data={},
                    message='Market bookmarked successfully.',
                )

                return Response(success_response, status=status.HTTP_201_CREATED)
            
            market_bookmark.is_active = False
            market_bookmark.save()

            response = ApiResponse(
                success=True,
                code=200,
                data={},
                message='Market unbookmarked successfully.',
            )

            return Response(response, status=status.HTTP_200_OK)

        success_response = ApiResponse(
            success=True,
            code=200,
            data={},
            message='Market bookmarked successfully.',
        )

        return Response(success_response, status=status.HTTP_201_CREATED)

    def get(self, request):
        user = self.request.user

        market_bookmark_list = MarketBookmark.objects.filter(
            user=user,
            is_active=True,
        ).select_related('market')

        market_list = [book_mark.market for book_mark in market_bookmark_list]

        serializer = MarketListSerializer(
            market_list,
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

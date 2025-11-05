"""
Views بهبود یافته برای Market Management
شامل: Transaction Management, Logging, Error Handling, Permission Checks
"""

from rest_framework import views, status, permissions
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.utils.translation import gettext_lazy as _

from utils.response import ApiResponse
from utils.logging_config import (
    log_info, log_user_action, log_error, log_warning, log_security_event
)
from utils.error_handlers import (
    ErrorHandlerMixin, create_error_response, 
    handle_validation_errors, ValidationError, 
    BusinessLogicError, PermissionError
)

from apps.market.models import (
    Market,
    MarketLocation,
    MarketContact,
    MarketSlider,
    MarketTheme,
)

from apps.market.serializers.owner_serializers import (
    MarketCreateSerializer,
    MarketUpdateSerializer,
    MarketLocationCreateSerializer,
    MarketLocationUpdateSerializer,
    MarketContactCreateSerializer,
    MarketContactUpdaterSerializer,
    MarketListSerializer,
    MarketSliderListSerializer,
    MarketThemeCreateSerializer,
)


class MarketCreateAPIView(ErrorHandlerMixin, views.APIView):
    """
    MarketCreateAPIView بهبود یافته
    
    ویژگی‌ها:
    - ✅ Transaction Management
    - ✅ Logging کامل
    - ✅ Error Handling پیشرفته
    - ✅ Permission Check
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        try:
            # ✅ Log درخواست
            log_info("Market creation request received", 
                    context={'user_id': request.user.id}, 
                    user=request.user)
            
            # ✅ بررسی Authentication
            if not request.user.is_authenticated:
                log_security_event(
                    "Unauthenticated market creation attempt",
                    ip_address=request.META.get('REMOTE_ADDR')
                )
                return Response(
                    ApiResponse(
                        success=False,
                        code=401,
                        error={'code': 'authentication_required', 'detail': 'Authentication required'}
                    ),
                    status=status.HTTP_401_UNAUTHORIZED
                )
            
            serializer = MarketCreateSerializer(
                data=request.data,
                context={'request': request},
            )
            
            if not serializer.is_valid():
                # ✅ Log Validation Error
                log_warning("Market creation validation failed", 
                           context={'errors': serializer.errors}, 
                           user=request.user)
                return Response(
                    handle_validation_errors(serializer.errors), 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # ✅ Transaction Management
            with transaction.atomic():
                market = serializer.save(user=request.user)
                
                # ✅ Log موفقیت
                log_user_action(
                    request.user, 
                    'CREATE', 
                    'Market', 
                    market.id, 
                    {
                        'business_id': market.business_id, 
                        'name': market.name
                    }
                )
                
                log_info("Market created successfully", 
                        context={'market_id': market.id, 'business_id': market.business_id}, 
                        user=request.user)
            
            success_response = ApiResponse(
                success=True,
                code=201,
                data={
                    'market_id': market.id,
                    **serializer.data,
                },
                message='Market created successfully.',
            )
            
            return Response(success_response, status=status.HTTP_201_CREATED)
            
        except ValidationError as e:
            log_error(e, context={'request_data': request.data}, user=request.user)
            return create_error_response(e, status.HTTP_400_BAD_REQUEST)
            
        except BusinessLogicError as e:
            log_error(e, context={'request_data': request.data}, user=request.user)
            return create_error_response(e, status.HTTP_422_UNPROCESSABLE_ENTITY)
            
        except Exception as e:
            log_error(e, context={'request_data': request.data, 'view': 'MarketCreateAPIView'}, user=request.user)
            return create_error_response(e, status.HTTP_500_INTERNAL_SERVER_ERROR)


class MarketUpdateAPIView(ErrorHandlerMixin, views.APIView):
    """
    MarketUpdateAPIView بهبود یافته
    
    ویژگی‌ها:
    - ✅ Permission Check (Ownership)
    - ✅ Transaction Management
    - ✅ Logging
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def put(self, request, pk):
        try:
            log_info("Market update request", 
                    context={'market_id': pk}, 
                    user=request.user)
            
            # ✅ Permission Check (Ownership)
            try:
                market = Market.objects.get(id=pk, user=request.user)
            except Market.DoesNotExist:
                log_security_event(
                    "Unauthorized market update attempt",
                    user=request.user,
                    ip_address=request.META.get('REMOTE_ADDR'),
                    details={'market_id': pk}
                )
                return Response(
                    ApiResponse(
                        success=False,
                        code=404,
                        error={
                            'code': 'market_not_found',
                            'detail': 'Market not found or you do not have permission to update it',
                        }
                    ),
                    status=status.HTTP_404_NOT_FOUND
                )
            
            serializer = MarketUpdateSerializer(
                market,
                data=request.data,
                partial=False,
                context={'request': request},
            )
            
            if not serializer.is_valid():
                log_warning("Market update validation failed", 
                          context={'errors': serializer.errors}, 
                          user=request.user)
                return Response(
                    handle_validation_errors(serializer.errors), 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # ✅ Transaction Management
            with transaction.atomic():
                market = serializer.save()
                
                log_user_action(
                    request.user, 
                    'UPDATE', 
                    'Market', 
                    market.id,
                    {'changes': request.data}
                )
                
                log_info("Market updated successfully", 
                        context={'market_id': market.id}, 
                        user=request.user)
            
            success_response = ApiResponse(
                success=True,
                code=200,
                data=serializer.data,
                message='Market updated successfully.',
            )
            return Response(success_response, status=status.HTTP_200_OK)
            
        except Exception as e:
            log_error(e, context={'market_id': pk}, user=request.user)
            return create_error_response(e, status.HTTP_500_INTERNAL_SERVER_ERROR)


class MarketGetAPIView(ErrorHandlerMixin, views.APIView):
    """
    MarketGetAPIView بهبود یافته
    
    ویژگی‌ها:
    - ✅ Permission Check
    - ✅ Query Optimization
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, pk, format=None):
        try:
            log_info("Market get request", 
                    context={'market_id': pk}, 
                    user=request.user)
            
            # ✅ Permission Check + Query Optimization
            try:
                market = Market.objects.select_related(
                    'sub_category', 'location', 'contact'
                ).get(id=pk, user=request.user)
            except Market.DoesNotExist:
                log_security_event(
                    "Unauthorized market access attempt",
                    user=request.user,
                    ip_address=request.META.get('REMOTE_ADDR'),
                    details={'market_id': pk}
                )
                return Response(
                    ApiResponse(
                        success=False,
                        code=404,
                        error={
                            'code': 'market_not_found',
                            'detail': 'Market not found or you do not have permission to view it',
                        }
                    ),
                    status=status.HTTP_404_NOT_FOUND
                )
            
            serializer = MarketUpdateSerializer(
                market,
                context={'request': request},
            )
            
            log_user_action(request.user, 'VIEW', 'Market', market.id)
            
            success_response = ApiResponse(
                success=True,
                code=200,
                data=serializer.data,
                message='Data retrieved successfully.',
            )
            return Response(success_response, status=status.HTTP_200_OK)
            
        except Exception as e:
            log_error(e, context={'market_id': pk}, user=request.user)
            return create_error_response(e)


class MarketListAPIView(ErrorHandlerMixin, views.APIView):
    """
    MarketListAPIView بهبود یافته
    
    ویژگی‌ها:
    - ✅ Query Optimization
    - ✅ Logging
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, format=None):
        try:
            log_info("Market list request", 
                    context={'user_id': request.user.id}, 
                    user=request.user)
            
            # ✅ Query Optimization
            market_list = Market.objects.filter(
                user=request.user,
            ).select_related(
                'sub_category', 'location', 'contact'
            ).prefetch_related(
                'theme', 'sliders'
            ).order_by('-created_at')
            
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
            
        except Exception as e:
            log_error(e, context={'user_id': request.user.id}, user=request.user)
            return create_error_response(e)


class MarketLocationCreateAPIView(ErrorHandlerMixin, views.APIView):
    """
    MarketLocationCreateAPIView بهبود یافته
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        try:
            log_info("Market location creation request", 
                    context={'user_id': request.user.id}, 
                    user=request.user)
            
            serializer = MarketLocationCreateSerializer(
                data=request.data,
                context={'request': request},
            )
            
            if not serializer.is_valid():
                log_warning("Location creation validation failed", 
                           context={'errors': serializer.errors}, 
                           user=request.user)
                return Response(
                    handle_validation_errors(serializer.errors), 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # ✅ Ownership check
            market = serializer.validated_data.get('market')
            if market.user != request.user:
                log_security_event(
                    "Unauthorized location creation attempt",
                    user=request.user,
                    ip_address=request.META.get('REMOTE_ADDR'),
                    details={'market_id': market.id}
                )
                return Response(
                    ApiResponse(
                        success=False,
                        code=403,
                        error={
                            'code': 'permission_denied',
                            'detail': 'You do not have permission to modify this market',
                        }
                    ),
                    status=status.HTTP_403_FORBIDDEN,
                )
            
            # ✅ Prevent duplicate location
            if MarketLocation.objects.filter(market=market).exists():
                log_warning("Duplicate location creation attempt", 
                           context={'market_id': market.id}, 
                           user=request.user)
                return Response(
                    ApiResponse(
                        success=False,
                        code=400,
                        error={
                            'code': 'location_exists',
                            'detail': 'Location for this market already exists',
                        }
                    ),
                    status=status.HTTP_400_BAD_REQUEST,
                )
            
            # ✅ Transaction Management
            with transaction.atomic():
                market_location = serializer.save()
                
                log_user_action(
                    request.user, 
                    'CREATE', 
                    'MarketLocation', 
                    market_location.id,
                    {'market_id': market.id}
                )
                
                log_info("Location created successfully", 
                        context={'location_id': market_location.id}, 
                        user=request.user)
            
            success_response = ApiResponse(
                success=True,
                code=201,
                data=serializer.data,
                message='Market location created successfully.',
            )
            return Response(success_response, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            log_error(e, context={'request_data': request.data}, user=request.user)
            return create_error_response(e)


class MarketLocationUpdateAPIView(ErrorHandlerMixin, views.APIView):
    """
    MarketLocationUpdateAPIView بهبود یافته
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def put(self, request, pk):
        try:
            log_info("Market location update request", 
                    context={'market_id': pk}, 
                    user=request.user)
            
            # ✅ Permission Check
            try:
                market = Market.objects.select_related('location').get(
                    id=pk, 
                    user=request.user
                )
                market_location = market.location
            except Market.DoesNotExist:
                log_security_event(
                    "Unauthorized location update attempt",
                    user=request.user,
                    ip_address=request.META.get('REMOTE_ADDR'),
                    details={'market_id': pk}
                )
                return Response(
                    ApiResponse(
                        success=False,
                        code=404,
                        error={
                            'code': 'market_not_found',
                            'detail': 'Market not found or you do not have permission',
                        }
                    ),
                    status=status.HTTP_404_NOT_FOUND
                )
            except MarketLocation.DoesNotExist:
                return Response(
                    ApiResponse(
                        success=False,
                        code=404,
                        error={
                            'code': 'market_location_not_found',
                            'detail': 'Market location not found',
                        }
                    ),
                    status=status.HTTP_404_NOT_FOUND
                )
            
            serializer = MarketLocationUpdateSerializer(
                market_location,
                data=request.data,
                partial=False,
                context={'request': request},
            )
            
            if not serializer.is_valid():
                log_warning("Location update validation failed", 
                          context={'errors': serializer.errors}, 
                          user=request.user)
                return Response(
                    handle_validation_errors(serializer.errors), 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # ✅ Transaction Management
            with transaction.atomic():
                serializer.save()
                
                log_user_action(
                    request.user, 
                    'UPDATE', 
                    'MarketLocation', 
                    market_location.id,
                    {'market_id': market.id}
                )
                
                log_info("Location updated successfully", 
                        context={'location_id': market_location.id}, 
                        user=request.user)
            
            success_response = ApiResponse(
                success=True,
                code=200,
                data=serializer.data,
                message='Market location updated successfully.',
            )
            return Response(success_response, status=status.HTTP_200_OK)
            
        except Exception as e:
            log_error(e, context={'market_id': pk}, user=request.user)
            return create_error_response(e)


# برای بقیه Views هم همین الگو را ادامه دهید...
# MarketContactCreateAPIView, MarketContactUpdateAPIView, ...


from rest_framework import views, status, permissions
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError as DjangoValidationError
import logging

# Import base utilities with fallback
try:
    from apps.base.utils import ApiResponse
except ImportError:
    # Fallback ApiResponse if not available
    class ApiResponse:
        def __init__(self, success=True, code=200, data=None, message='', error=None):
            self.success = success
            self.code = code
            self.data = data or {}
            self.message = message
            self.error = error or {}

# Import models with correct paths
try:
    from ..models.category_models import Group, Category, SubCategory
except ImportError:
    try:
        from .models import Group, Category, SubCategory
    except ImportError:
        Group = Category = SubCategory = None

# Import serializers with correct paths
try:
    from ..serializers.category_serializers import MarketFeeUpdateSerializer, MarketFeeListSerializer
except ImportError:
    try:
        from .serializers import MarketFeeUpdateSerializer, MarketFeeListSerializer
    except ImportError:
        # Fallback serializers if not available
        MarketFeeUpdateSerializer = MarketFeeListSerializer = None

# Import error handling utilities
try:
    from ..utils.error_handlers import (
        ErrorHandlerMixin, log_error, log_info, log_warning,
        ValidationError, BusinessLogicError,
        create_error_response, handle_validation_errors
    )
except ImportError:
    # Fallback error handling
    class ErrorHandlerMixin:
        pass
    
    def log_error(error, context=None, user=None):
        logging.error(f"Error: {error}")
    
    def log_info(message, context=None, user=None):
        logging.info(f"Info: {message}")
    
    def log_warning(message, context=None, user=None):
        logging.warning(f"Warning: {message}")
    
    class ValidationError(Exception):
        pass
    
    class BusinessLogicError(Exception):
        pass
    
    def create_error_response(error, status_code=400):
        return Response({'error': str(error)}, status=status_code)
    
    def handle_validation_errors(errors):
        return {'success': False, 'errors': errors}

try:
    from ..utils.logging_config import log_user_action
except ImportError:
    # Fallback logging function
    def log_user_action(user, action, model_name=None, object_id=None, details=None):
        logging.info(f"User {user} performed {action} on {model_name}:{object_id}")

# Configure logger
logger = logging.getLogger('category')


class MarketFeeUpdateAPIView(views.APIView):
    permission_classes = [permissions.IsAuthenticated, permissions.IsAdminUser]
    
    def put(self, request, model_type, pk):
        """
        Update market fee for a specific model instance
        """
        try:
            if model_type == 'group':
                model_class = Group
            elif model_type == 'category':
                model_class = Category
            elif model_type == 'subcategory':
                model_class = SubCategory
            else:
                return Response(
                    ApiResponse(
                        success=False,
                        code=400,
                        error={'code': 'invalid_model_type', 'detail': 'Invalid model type'}
                    ),
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            instance = get_object_or_404(model_class, id=pk)
            serializer = MarketFeeUpdateSerializer(data=request.data)
            
            if serializer.is_valid(raise_exception=True):
                instance.market_fee = serializer.validated_data['market_fee']
                instance.save()
                
                success_response = ApiResponse(
                    success=True,
                    code=200,
                    data={
                        'id': instance.id,
                        'title': instance.title,
                        'market_fee': float(instance.market_fee),
                        'model_type': model_type
                    },
                    message='Market fee updated successfully.',
                )
                
                return Response(success_response, status=status.HTTP_200_OK)
                
        except Exception as e:
            return Response(
                ApiResponse(
                    success=False,
                    code=500,
                    error={'code': 'update_failed', 'detail': str(e)}
                ),
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class MarketFeeListAPIView(views.APIView):
    permission_classes = [permissions.IsAuthenticated, permissions.IsAdminUser]
    
    def get(self, request, model_type):
        """
        List all instances with their market fees
        """
        try:
            if model_type == 'group':
                queryset = Group.objects.all()
                model_name = 'گروه'
            elif model_type == 'category':
                queryset = Category.objects.all()
                model_name = 'دسته'
            elif model_type == 'subcategory':
                queryset = SubCategory.objects.all()
                model_name = 'زیردسته'
            else:
                return Response(
                    ApiResponse(
                        success=False,
                        code=400,
                        error={'code': 'invalid_model_type', 'detail': 'Invalid model type'}
                    ),
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            data = []
            for instance in queryset:
                data.append({
                    'id': instance.id,
                    'title': instance.title,
                    'market_fee': float(instance.market_fee),
                    'fee_status': 'فعال' if instance.market_fee > 0 else 'غیرفعال'
                })
            
            success_response = ApiResponse(
                success=True,
                code=200,
                data={
                    'model_type': model_name,
                    'count': len(data),
                    'instances': data
                },
                message='Market fees retrieved successfully.',
            )
            
            return Response(success_response, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response(
                ApiResponse(
                    success=False,
                    code=500,
                    error={'code': 'retrieve_failed', 'detail': str(e)}
                ),
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

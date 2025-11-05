"""
Error Handling System for Market Registration
سیستم کامل مدیریت خطا با Exception Types مختلف و Response استاندارد
"""

import logging
import traceback
from typing import Dict, Any
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import IntegrityError, DatabaseError
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import exception_handler
from django.utils.translation import gettext_lazy as _


logger = logging.getLogger('market')


class MarketError(Exception):
    """Base exception for market errors"""
    def __init__(self, message: str, error_code: str = None, details: Dict = None):
        self.message = message
        self.error_code = error_code or 'MARKET_ERROR'
        self.details = details or {}
        super().__init__(self.message)


class ValidationError(MarketError):
    """Validation error for market data"""
    def __init__(self, message: str, field: str = None, details: Dict = None):
        self.field = field
        super().__init__(message, 'VALIDATION_ERROR', details)


class BusinessLogicError(MarketError):
    """Business logic error"""
    def __init__(self, message: str, details: Dict = None):
        super().__init__(message, 'BUSINESS_LOGIC_ERROR', details)


class PaymentError(MarketError):
    """Payment processing error"""
    def __init__(self, message: str, gateway_type: str = None, details: Dict = None):
        self.gateway_type = gateway_type
        super().__init__(message, 'PAYMENT_ERROR', details)


class PermissionError(MarketError):
    """Permission/Access error"""
    def __init__(self, message: str, details: Dict = None):
        super().__init__(message, 'PERMISSION_ERROR', details)


def create_error_response(error: Exception, status_code: int = status.HTTP_400_BAD_REQUEST) -> Response:
    """
    ایجاد Response استاندارد برای خطاها
    
    Args:
        error: Exception رخ داده
        status_code: کد HTTP
        
    Returns:
        Response: Response استاندارد
    """
    if isinstance(error, MarketError):
        response_data = {
            'success': False,
            'error': {
                'code': error.error_code,
                'message': error.message,
            }
        }
        if error.details:
            response_data['error']['details'] = error.details
        if hasattr(error, 'field') and error.field:
            response_data['error']['field'] = error.field
    else:
        response_data = {
            'success': False,
            'error': {
                'code': 'INTERNAL_ERROR',
                'message': _('An internal error occurred. Please try again later.'),
            }
        }
    
    return Response(response_data, status=status_code)


def handle_validation_errors(serializer_errors: Dict) -> Dict[str, Any]:
    """
    مدیریت خطاهای Validation از Serializer
    
    Args:
        serializer_errors: خطاهای Serializer
        
    Returns:
        Dict: Response فرمت شده
    """
    formatted_errors = {}
    for field, errors in serializer_errors.items():
        if isinstance(errors, list):
            formatted_errors[field] = errors[0] if errors else _('Invalid value')
        else:
            formatted_errors[field] = str(errors)
    
    return {
        'success': False,
        'error': {
            'code': 'VALIDATION_ERROR',
            'message': _('Validation failed'),
            'details': formatted_errors
        }
    }


class ErrorHandlerMixin:
    """
    Mixin برای اضافه کردن Error Handling به Views
    
    استفاده:
        class MyView(ErrorHandlerMixin, views.APIView):
            ...
    """
    
    def handle_exception(self, exc):
        """
        مدیریت Exception‌ها در Views
        
        Args:
            exc: Exception رخ داده
            
        Returns:
            Response: Error Response
        """
        user = getattr(self.request, 'user', None) if hasattr(self, 'request') else None
        
        from utils.logging_config import log_error
        log_error(exc, context={
            'view': self.__class__.__name__,
            'action': getattr(self, 'action', None),
            'request_data': getattr(self.request, 'data', None) if hasattr(self, 'request') else None
        }, user=user)
        
        return create_error_response(exc)
    
    def validate_and_save(self, serializer, **kwargs):
        """
        Validate و Save با Error Handling
        
        Args:
            serializer: Serializer instance
            **kwargs: Arguments اضافی برای save()
            
        Returns:
            Tuple: (success: bool, instance_or_errors)
        """
        try:
            if serializer.is_valid():
                instance = serializer.save(**kwargs)
                from utils.logging_config import log_info
                log_info(f"{instance.__class__.__name__} created/updated successfully", 
                        context={'instance_id': instance.id}, 
                        user=getattr(self.request, 'user', None) if hasattr(self, 'request') else None)
                return True, instance
            else:
                return False, handle_validation_errors(serializer.errors)
        except Exception as e:
            from utils.logging_config import log_error
            log_error(e, context={'serializer': serializer.__class__.__name__})
            return False, create_error_response(e)


def custom_exception_handler(exc, context):
    """
    Custom Exception Handler برای DRF
    
    Args:
        exc: Exception
        context: Context information
        
    Returns:
        Response: Error Response
    """
    # دریافت Standard Response
    response = exception_handler(exc, context)
    
    # دریافت Request و User
    request = context.get('request')
    user = getattr(request, 'user', None) if request else None
    
    # Log کردن خطا
    from utils.logging_config import log_error
    log_error(exc, context={
        'view': context.get('view'),
        'request_data': getattr(request, 'data', None) if request else None
    }, user=user)
    
    # مدیریت Custom Exceptions
    if isinstance(exc, MarketError):
        return create_error_response(exc, include_details=True)
    
    # مدیریت Django Validation Errors
    elif isinstance(exc, DjangoValidationError):
        return Response({
            'success': False,
            'error': {
                'code': 'VALIDATION_ERROR',
                'message': _('Validation failed'),
                'details': exc.message_dict if hasattr(exc, 'message_dict') else str(exc)
            }
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # مدیریت Database Errors
    elif isinstance(exc, IntegrityError):
        return Response({
            'success': False,
            'error': {
                'code': 'INTEGRITY_ERROR',
                'message': _('Data integrity error. Please check your input.'),
            }
        }, status=status.HTTP_400_BAD_REQUEST)
    
    elif isinstance(exc, DatabaseError):
        return Response({
            'success': False,
            'error': {
                'code': 'DATABASE_ERROR',
                'message': _('Database error occurred. Please try again later.'),
            }
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    # بازگرداندن Standard Response
    if response is not None:
        custom_response_data = {
            'success': False,
            'error': {
                'code': 'API_ERROR',
                'message': _('Request failed'),
                'details': response.data
            }
        }
        response.data = custom_response_data
    
    return response


import logging
import traceback
from typing import Dict, Any, Optional
from django.http import JsonResponse
from django.core.exceptions import ValidationError
from django.db import IntegrityError, DatabaseError
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import exception_handler
from django.utils.translation import gettext_lazy as _


# Configure logger
logger = logging.getLogger('office_registration')


class OfficeRegistrationError(Exception):
    """Base exception for office registration errors"""
    def __init__(self, message: str, error_code: str = None, details: Dict = None):
        self.message = message
        self.error_code = error_code or 'OFFICE_REGISTRATION_ERROR'
        self.details = details or {}
        super().__init__(self.message)


class ValidationError(OfficeRegistrationError):
    """Validation error for office registration"""
    def __init__(self, message: str, field: str = None, details: Dict = None):
        self.field = field
        super().__init__(message, 'VALIDATION_ERROR', details)


class BusinessLogicError(OfficeRegistrationError):
    """Business logic error for office registration"""
    def __init__(self, message: str, details: Dict = None):
        super().__init__(message, 'BUSINESS_LOGIC_ERROR', details)


class PaymentError(OfficeRegistrationError):
    """Payment processing error"""
    def __init__(self, message: str, gateway_type: str = None, details: Dict = None):
        self.gateway_type = gateway_type
        super().__init__(message, 'PAYMENT_ERROR', details)


class AuthenticationError(OfficeRegistrationError):
    """Authentication error"""
    def __init__(self, message: str, details: Dict = None):
        super().__init__(message, 'AUTHENTICATION_ERROR', details)


class PermissionError(OfficeRegistrationError):
    """Permission error"""
    def __init__(self, message: str, details: Dict = None):
        super().__init__(message, 'PERMISSION_ERROR', details)


def log_error(error: Exception, context: Dict[str, Any] = None, user=None):
    """
    Log error with context information
    
    Args:
        error: The exception that occurred
        context: Additional context information
        user: User instance if available
    """
    context = context or {}
    
    error_info = {
        'error_type': type(error).__name__,
        'error_message': str(error),
        'traceback': traceback.format_exc(),
        'context': context,
    }
    
    if user:
        error_info['user'] = {
            'id': user.id,
            'username': user.username,
            'email': getattr(user, 'email', None),
        }
    
    logger.error(f"Office Registration Error: {error_info}")


def log_info(message: str, context: Dict[str, Any] = None, user=None):
    """
    Log informational message
    
    Args:
        message: Information message
        context: Additional context information
        user: User instance if available
    """
    context = context or {}
    
    info = {
        'message': message,
        'context': context,
    }
    
    if user:
        info['user'] = {
            'id': user.id,
            'username': user.username,
        }
    
    logger.info(f"Office Registration Info: {info}")


def log_warning(message: str, context: Dict[str, Any] = None, user=None):
    """
    Log warning message
    
    Args:
        message: Warning message
        context: Additional context information
        user: User instance if available
    """
    context = context or {}
    
    warning_info = {
        'message': message,
        'context': context,
    }
    
    if user:
        warning_info['user'] = {
            'id': user.id,
            'username': user.username,
        }
    
    logger.warning(f"Office Registration Warning: {warning_info}")


def create_error_response(
    error: Exception,
    status_code: int = status.HTTP_400_BAD_REQUEST,
    include_details: bool = False
) -> Response:
    """
    Create standardized error response
    
    Args:
        error: The exception that occurred
        status_code: HTTP status code
        include_details: Whether to include detailed error information
    
    Returns:
        Response: Standardized error response
    """
    if isinstance(error, OfficeRegistrationError):
        response_data = {
            'success': False,
            'error': {
                'code': error.error_code,
                'message': error.message,
            }
        }
        
        if include_details and error.details:
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
        
        if include_details:
            response_data['error']['details'] = {
                'type': type(error).__name__,
                'message': str(error),
            }
    
    return Response(response_data, status=status_code)


def custom_exception_handler(exc, context):
    """
    Custom exception handler for DRF
    
    Args:
        exc: The exception that occurred
        context: Context information
    
    Returns:
        Response: Error response
    """
    # Get the standard error response first
    response = exception_handler(exc, context)
    
    # Get request and user from context
    request = context.get('request')
    user = getattr(request, 'user', None) if request else None
    
    # Log the error
    log_error(exc, context={'view': context.get('view'), 'request_data': getattr(request, 'data', None)}, user)
    
    # Handle custom exceptions
    if isinstance(exc, OfficeRegistrationError):
        return create_error_response(exc, include_details=True)
    
    # Handle Django validation errors
    elif isinstance(exc, ValidationError):
        return Response({
            'success': False,
            'error': {
                'code': 'VALIDATION_ERROR',
                'message': _('Validation failed'),
                'details': exc.message_dict if hasattr(exc, 'message_dict') else str(exc)
            }
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Handle database errors
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
    
    # Return the standard response if we don't have a custom handler
    if response is not None:
        # Customize the response format
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


def handle_validation_errors(serializer_errors: Dict) -> Dict[str, Any]:
    """
    Handle serializer validation errors
    
    Args:
        serializer_errors: Serializer errors dictionary
    
    Returns:
        Dict: Formatted error response
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


def safe_execute(func, *args, **kwargs):
    """
    Safely execute a function with error handling
    
    Args:
        func: Function to execute
        *args: Function arguments
        **kwargs: Function keyword arguments
    
    Returns:
        Tuple: (success, result_or_error)
    """
    try:
        result = func(*args, **kwargs)
        return True, result
    except Exception as e:
        log_error(e, context={'function': func.__name__, 'args': args, 'kwargs': kwargs})
        return False, e


class ErrorHandlerMixin:
    """
    Mixin to add error handling capabilities to views
    """
    
    def handle_exception(self, exc):
        """
        Handle exceptions in views
        
        Args:
            exc: The exception that occurred
        
        Returns:
            Response: Error response
        """
        user = getattr(self.request, 'user', None) if hasattr(self, 'request') else None
        
        log_error(exc, context={
            'view': self.__class__.__name__,
            'action': getattr(self, 'action', None),
            'request_data': getattr(self.request, 'data', None) if hasattr(self, 'request') else None
        }, user=user)
        
        return create_error_response(exc)
    
    def validate_and_save(self, serializer, **kwargs):
        """
        Validate and save serializer with error handling
        
        Args:
            serializer: Serializer instance
            **kwargs: Additional save arguments
        
        Returns:
            Tuple: (success, instance_or_errors)
        """
        try:
            if serializer.is_valid():
                instance = serializer.save(**kwargs)
                log_info(f"{instance.__class__.__name__} created/updated successfully", 
                        context={'instance_id': instance.id}, 
                        user=getattr(self.request, 'user', None))
                return True, instance
            else:
                return False, handle_validation_errors(serializer.errors)
        except Exception as e:
            log_error(e, context={'serializer': serializer.__class__.__name__})
            return False, create_error_response(e)


def require_authentication(view_func):
    """
    Decorator to require authentication for views
    
    Args:
        view_func: View function to decorate
    
    Returns:
        Function: Decorated view function
    """
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            error = AuthenticationError(_('Authentication required'))
            log_warning("Unauthenticated access attempt", context={'view': view_func.__name__})
            return create_error_response(error, status.HTTP_401_UNAUTHORIZED)
        return view_func(request, *args, **kwargs)
    return wrapper


def require_permission(permission_check):
    """
    Decorator to require specific permissions for views
    
    Args:
        permission_check: Function that checks permissions
    
    Returns:
        Function: Decorator function
    """
    def decorator(view_func):
        def wrapper(request, *args, **kwargs):
            if not permission_check(request.user):
                error = PermissionError(_('Insufficient permissions'))
                log_warning("Permission denied", context={
                    'view': view_func.__name__,
                    'user': request.user.username if request.user.is_authenticated else 'anonymous'
                })
                return create_error_response(error, status.HTTP_403_FORBIDDEN)
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator
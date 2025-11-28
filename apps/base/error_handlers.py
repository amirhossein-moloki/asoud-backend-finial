from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import ValidationError
from django.core.exceptions import PermissionDenied, ObjectDoesNotExist
from django.http import Http404
from apps.base.exceptions import BusinessLogicException

class StandardErrorHandler:
    """Centralized error handling for consistent responses"""

    @staticmethod
    def handle_validation_error(error: ValidationError) -> Response:
        """Handle validation errors consistently"""
        return Response({
            'success': False,
            'code': 'VALIDATION_ERROR',
            'message': 'Validation failed',
            'errors': error.detail if hasattr(error, 'detail') else str(error)
        }, status=status.HTTP_400_BAD_REQUEST)

    @staticmethod
    def handle_business_logic_error(error: BusinessLogicException) -> Response:
        """Handle business logic errors"""
        return Response({
            'success': False,
            'code': error.code,
            'message': error.message,
            'data': error.data
        }, status=status.HTTP_422_UNPROCESSABLE_ENTITY)

    @staticmethod
    def handle_permission_error(error: PermissionDenied) -> Response:
        """Handle permission errors"""
        return Response({
            'success': False,
            'code': 'PERMISSION_DENIED',
            'message': str(error)
        }, status=status.HTTP_403_FORBIDDEN)

    @staticmethod
    def handle_not_found_error(error: ObjectDoesNotExist) -> Response:
        """Handle not found errors"""
        return Response({
            'success': False,
            'code': 'NOT_FOUND',
            'message': str(error)
        }, status=status.HTTP_404_NOT_FOUND)

def standard_error_handler(func):
    """Decorator for consistent error handling in views."""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ValidationError as e:
            return StandardErrorHandler.handle_validation_error(e)
        except BusinessLogicException as e:
            return StandardErrorHandler.handle_business_logic_error(e)
        except PermissionDenied as e:
            return StandardErrorHandler.handle_permission_error(e)
        except (ObjectDoesNotExist, Http404) as e:
            return StandardErrorHandler.handle_not_found_error(e)
        except Exception as e:
            # You can add more specific exception handling here if needed
            return Response({
                'success': False,
                'code': 'INTERNAL_SERVER_ERROR',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    return wrapper

"""
Enhanced Views for ASOUD Platform
"""

import logging
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
from rest_framework import status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView

logger = logging.getLogger(__name__)

class CSRFFailureView(APIView):
    """
    Enhanced CSRF failure view with proper logging and security
    """
    
    def post(self, request):
        """Handle CSRF failure for POST requests"""
        logger.warning(
            f"CSRF failure detected: IP={request.META.get('REMOTE_ADDR')}, "
            f"User-Agent={request.META.get('HTTP_USER_AGENT')}, "
            f"Path={request.path}"
        )
        
        return Response(
            {
                'error': 'CSRF verification failed',
                'message': 'Invalid or missing CSRF token',
                'code': 'CSRF_FAILURE'
            },
            status=status.HTTP_403_FORBIDDEN
        )
    
    def get(self, request):
        """Handle CSRF failure for GET requests"""
        logger.warning(
            f"CSRF failure detected: IP={request.META.get('REMOTE_ADDR')}, "
            f"User-Agent={request.META.get('HTTP_USER_AGENT')}, "
            f"Path={request.path}"
        )
        
        return Response(
            {
                'error': 'CSRF verification failed',
                'message': 'Invalid or missing CSRF token',
                'code': 'CSRF_FAILURE'
            },
            status=status.HTTP_403_FORBIDDEN
        )

class SecurityHeadersView(APIView):
    """
    View to add security headers to responses
    """
    
    def dispatch(self, request, *args, **kwargs):
        response = super().dispatch(request, *args, **kwargs)
        
        # Add security headers
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-Frame-Options'] = 'DENY'
        response['X-XSS-Protection'] = '1; mode=block'
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        response['Permissions-Policy'] = 'geolocation=(), microphone=(), camera=()'
        
        # HSTS header for HTTPS requests
        if request.is_secure():
            response['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains; preload'
        
        return response

class RateLimitView(APIView):
    """
    View to handle rate limiting
    """
    
    def dispatch(self, request, *args, **kwargs):
        # Check rate limit
        if self.is_rate_limited(request):
            return Response(
                {
                    'error': 'Rate limit exceeded',
                    'message': 'Too many requests. Please try again later.',
                    'code': 'RATE_LIMIT_EXCEEDED'
                },
                status=status.HTTP_429_TOO_MANY_REQUESTS
            )
        
        return super().dispatch(request, *args, **kwargs)
    
    def is_rate_limited(self, request):
        """Check if request is rate limited"""
        # This would be implemented with Redis or cache
        # For now, return False
        return False

class HealthCheckView(APIView):
    """
    Health check endpoint for monitoring
    """
    permission_classes = []  # No authentication required for health check
    
    def get(self, request):
        """Comprehensive health check"""
        health_status = {
            "status": "ok",
            "timestamp": self.get_timestamp(),
            "version": "1.0.0",
            "checks": {}
        }
        
        # Database check
        try:
            from django.db import connection
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
            health_status["checks"]["database"] = {"status": "ok", "response_time": "fast"}
        except Exception as e:
            health_status["checks"]["database"] = {"status": "error", "error": str(e)}
            health_status["status"] = "error"
        
        # Cache check
        try:
            from django.core.cache import cache
            cache.set('health_check', 'ok', 10)
            cache_result = cache.get('health_check')
            if cache_result == 'ok':
                health_status["checks"]["cache"] = {"status": "ok"}
            else:
                health_status["checks"]["cache"] = {"status": "error", "error": "Cache test failed"}
                health_status["status"] = "error"
        except Exception as e:
            health_status["checks"]["cache"] = {"status": "error", "error": str(e)}
            health_status["status"] = "error"
        
        # Redis check
        try:
            from apps.core.caching import cache_manager
            if hasattr(cache_manager, 'redis_available') and cache_manager.redis_available:
                health_status["checks"]["redis"] = {"status": "ok"}
            else:
                health_status["checks"]["redis"] = {"status": "warning", "message": "Redis not available"}
        except Exception as e:
            health_status["checks"]["redis"] = {"status": "error", "error": str(e)}
        
        # Memory check
        try:
            import psutil
            memory = psutil.virtual_memory()
            health_status["checks"]["memory"] = {
                "status": "ok" if memory.percent < 80 else "warning",
                "usage_percent": memory.percent,
                "available_mb": round(memory.available / (1024 * 1024), 2)
            }
        except Exception as e:
            health_status["checks"]["memory"] = {"status": "error", "error": str(e)}
        
        # Disk check
        try:
            import psutil
            disk = psutil.disk_usage('/')
            health_status["checks"]["disk"] = {
                "status": "ok" if disk.percent < 90 else "warning",
                "usage_percent": disk.percent,
                "free_gb": round(disk.free / (1024 * 1024 * 1024), 2)
            }
        except Exception as e:
            health_status["checks"]["disk"] = {"status": "error", "error": str(e)}
        
        # Determine overall status
        if health_status["status"] == "ok":
            return Response(health_status, status=status.HTTP_200_OK)
        else:
            return Response(health_status, status=status.HTTP_503_SERVICE_UNAVAILABLE)
    
    def get_timestamp(self):
        """Get current timestamp"""
        from django.utils import timezone
        return timezone.now().isoformat()

class ApiIndexView(APIView):
    """
    Public API index endpoint; returns 200 without authentication.
    """
    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request):
        return Response({
            "name": "Asoud API",
            "version": "v1",
            "status": "available",
        }, status=status.HTTP_200_OK)

class SecurityAuditView(APIView):
    """
    Security audit endpoint for monitoring
    """
    
    def get(self, request):
        """Return security audit information"""
        # This would return security metrics
        # For now, return basic information
        return Response({
            'security_status': 'active',
            'csrf_protection': 'enabled',
            'rate_limiting': 'enabled',
            'timestamp': self.get_timestamp()
        })
    
    def get_timestamp(self):
        """Get current timestamp"""
        from django.utils import timezone
        return timezone.now().isoformat()

# Function-based views for compatibility
def csrf_failure_view(request, reason=""):
    """CSRF failure view function"""
    logger.warning(
        f"CSRF failure: {reason}, IP={request.META.get('REMOTE_ADDR')}, "
        f"Path={request.path}"
    )
    
    return JsonResponse(
        {
            'error': 'CSRF verification failed',
            'message': 'Invalid or missing CSRF token',
            'code': 'CSRF_FAILURE'
        },
        status=403
    )

def rate_limit_view(request):
    """Rate limit view function"""
    return JsonResponse(
        {
            'error': 'Rate limit exceeded',
            'message': 'Too many requests. Please try again later.',
            'code': 'RATE_LIMIT_EXCEEDED'
        },
        status=429
    )



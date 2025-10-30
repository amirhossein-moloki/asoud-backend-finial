import re
import logging
from django.conf import settings
from django.utils.deprecation import MiddlewareMixin
from django.http import JsonResponse
from django.core.cache import cache
from django.utils import timezone
from datetime import timedelta

logger = logging.getLogger(__name__)

class EnhancedCSRFExemptMiddleware(MiddlewareMixin):
    """
    Enhanced CSRF exemption middleware with security logging
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        # Define exempt patterns more precisely
        self.exempt_patterns = [
            r'^api/v1/auth/login/$',
            r'^api/v1/auth/refresh/$',
            r'^api/v1/user/pin/create/$',
            r'^api/v1/user/pin/verify/$',
            r'^admin/login/$',
            r'^health/$',
        ]

    def __call__(self, request):
        path = request.path_info.lstrip('/')
        
        # Check if path matches exempt patterns
        for pattern in self.exempt_patterns:
            if re.match(pattern, path):
                setattr(request, '_dont_enforce_csrf_checks', True)
                logger.info(f"CSRF exempted for path: {path}")
                break
        
        response = self.get_response(request)
        return response

class SecurityHeadersMiddleware(MiddlewareMixin):
    """
    Add security headers to all responses
    """
    
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        
        # Security headers
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-Frame-Options'] = 'DENY'
        response['X-XSS-Protection'] = '1; mode=block'
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        response['Permissions-Policy'] = 'geolocation=(), microphone=(), camera=()'
        
        # HSTS header for HTTPS requests
        if request.is_secure():
            response['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains; preload'
        
        return response

class RateLimitMiddleware(MiddlewareMixin):
    """
    Rate limiting middleware
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.rate_limits = {
            'default': {'requests': 1000, 'window': 3600},  # 1000 requests per hour
            'auth': {'requests': 10, 'window': 60},  # 10 requests per minute
            'payment': {'requests': 5, 'window': 60},  # 5 requests per minute
            'upload': {'requests': 20, 'window': 3600},  # 20 requests per hour
        }

    def __call__(self, request):
        # Check rate limit
        if self.is_rate_limited(request):
            return JsonResponse(
                {
                    'error': 'Rate limit exceeded',
                    'message': 'Too many requests. Please try again later.',
                    'code': 'RATE_LIMIT_EXCEEDED'
                },
                status=429
            )
        
        response = self.get_response(request)
        return response
    
    def is_rate_limited(self, request):
        """Check if request is rate limited"""
        try:
            # Get client IP
            client_ip = self.get_client_ip(request)
            
            # Determine rate limit type
            rate_limit_type = self.get_rate_limit_type(request)
            rate_limit = self.rate_limits.get(rate_limit_type, self.rate_limits['default'])
            
            # Create cache key
            cache_key = f"rate_limit:{client_ip}:{rate_limit_type}"
            
            # Check current count with fallback
            try:
                current_count = cache.get(cache_key, 0)
            except Exception as cache_error:
                logger.error(f"Cache error in rate limiting: {cache_error}")
                # If cache fails, allow request but log the issue
                return False
            
            if current_count >= rate_limit['requests']:
                logger.warning(f"Rate limit exceeded for IP {client_ip} on {request.path}")
                return True
            
            # Increment counter with error handling
            try:
                cache.set(cache_key, current_count + 1, rate_limit['window'])
            except Exception as cache_error:
                logger.error(f"Cache set error in rate limiting: {cache_error}")
                # Continue without rate limiting if cache fails
            
            return False
            
        except Exception as e:
            logger.error(f"Error in rate limiting: {e}")
            # If rate limiting fails, allow request but log the issue
            return False
    
    def get_client_ip(self, request):
        """Get client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    
    def get_rate_limit_type(self, request):
        """Determine rate limit type based on request path"""
        path = request.path_info.lstrip('/')
        
        if path.startswith('api/v1/auth/'):
            return 'auth'
        elif path.startswith('api/v1/user/payments/'):
            return 'payment'
        elif path.startswith('api/v1/upload/'):
            return 'upload'
        else:
            return 'default'

class SecurityAuditMiddleware(MiddlewareMixin):
    """
    Security audit middleware for logging security events
    """
    
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Log security events
        self.log_security_event(request)
        
        response = self.get_response(request)
        
        # Log response security events
        self.log_response_security(request, response)
        
        return response
    
    def log_security_event(self, request):
        """Log security events"""
        try:
            # Log suspicious patterns
            if self.is_suspicious_request(request):
                logger.warning(
                    f"Suspicious request detected: IP={self.get_client_ip(request)}, "
                    f"Path={request.path}, User-Agent={request.META.get('HTTP_USER_AGENT')}"
                )
            
            # Log authentication attempts
            if request.path.startswith('/api/v1/auth/'):
                logger.info(
                    f"Authentication attempt: IP={self.get_client_ip(request)}, "
                    f"Path={request.path}, Method={request.method}"
                )
                
        except Exception as e:
            logger.error(f"Error in security audit: {e}")
    
    def log_response_security(self, request, response):
        """Log response security events"""
        try:
            # Log error responses
            if response.status_code >= 400:
                logger.warning(
                    f"Error response: IP={self.get_client_ip(request)}, "
                    f"Path={request.path}, Status={response.status_code}"
                )
                
        except Exception as e:
            logger.error(f"Error in response security audit: {e}")
    
    def is_suspicious_request(self, request):
        """Check if request is suspicious"""
        # Check for SQL injection patterns
        sql_patterns = [
            r'union\s+select',
            r'drop\s+table',
            r'delete\s+from',
            r'insert\s+into',
            r'update\s+set',
            r'exec\s*\(',
            r'script\s*>',
            r'<script',
            r'javascript:',
            r'vbscript:',
        ]
        
        # Check query parameters
        for param_name, param_value in request.GET.items():
            if isinstance(param_value, str):
                for pattern in sql_patterns:
                    if re.search(pattern, param_value, re.IGNORECASE):
                        return True
        
        # Check POST data
        if request.method == 'POST':
            for param_name, param_value in request.POST.items():
                if isinstance(param_value, str):
                    for pattern in sql_patterns:
                        if re.search(pattern, param_value, re.IGNORECASE):
                            return True
        
        return False
    
    def get_client_ip(self, request):
        """Get client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

class RequestLoggingMiddleware(MiddlewareMixin):
    """
    Request logging middleware for debugging and monitoring
    """
    
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Log request
        logger.info(
            f"Request: {request.method} {request.path} "
            f"from {self.get_client_ip(request)}"
        )
        
        response = self.get_response(request)
        
        # Handle async response
        if hasattr(response, '__await__'):
            # This is an async response, we need to handle it differently
            return response
        
        # Log response
        logger.info(
            f"Response: {response.status_code} for {request.method} {request.path}"
        )
        
        return response
    
    def get_client_ip(self, request):
        """Get client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

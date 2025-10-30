"""
Enhanced Authentication System for ASOUD Platform
"""

import jwt
import hashlib
import secrets
from datetime import datetime, timedelta
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.utils import timezone
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.permissions import BasePermission
from .models import User
from apps.analytics.models import UserSession
import logging

logger = logging.getLogger(__name__)
User = get_user_model()

class JWTAuthentication(BaseAuthentication):
    """
    Enhanced JWT Authentication with security features
    """
    
    def authenticate(self, request):
        """Authenticate user using JWT token"""
        auth_header = request.META.get('HTTP_AUTHORIZATION')
        
        if not auth_header:
            return None
        
        # Support both Bearer and Token authentication
        if auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]
        elif auth_header.startswith('Token '):
            token = auth_header.split(' ')[1]
        else:
            return None
        
        try:
            payload = self.decode_token(token)
            user_id = payload.get('user_id')
            
            if not user_id:
                raise AuthenticationFailed('Invalid token')
            
            try:
                user = User.objects.get(id=user_id)
            except User.DoesNotExist:
                raise AuthenticationFailed('User not found')
            
            # Check if user is active
            if not user.is_active:
                raise AuthenticationFailed('User account is disabled')
            
            # Check if token is blacklisted
            if self.is_token_blacklisted(token):
                raise AuthenticationFailed('Token has been revoked')
            
            # Update last activity
            self.update_user_activity(user, request)
            
            return (user, token)
            
        except jwt.ExpiredSignatureError:
            raise AuthenticationFailed('Token has expired')
        except jwt.InvalidTokenError:
            raise AuthenticationFailed('Invalid token')
        except User.DoesNotExist:
            raise AuthenticationFailed('User not found')
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            raise AuthenticationFailed('Authentication failed')
    
    def decode_token(self, token):
        """Decode JWT token with enhanced security"""
        try:
            payload = jwt.decode(
                token,
                settings.SECRET_KEY,
                algorithms=['HS256'],
                options={
                    'verify_exp': True,
                    'verify_iat': True,
                    'verify_aud': False,
                }
            )
            return payload
        except jwt.ExpiredSignatureError:
            raise AuthenticationFailed('Token has expired')
        except jwt.InvalidTokenError:
            raise AuthenticationFailed('Invalid token')
    
    def is_token_blacklisted(self, token):
        """Check if token is blacklisted"""
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        return cache.get(f"blacklisted_token:{token_hash}") is not None
    
    def update_user_activity(self, user, request):
        """Update user's last activity"""
        user.last_activity = timezone.now()
        user.save(update_fields=['last_activity'])
        
        # Log user activity
        logger.info(f"User {user.id} accessed {request.path}")

class EnhancedPermissionMixin:
    """
    Enhanced permission checking mixin
    """
    
    def has_permission(self, request, view):
        """Check if user has permission"""
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Check if user is active
        if not request.user.is_active:
            return False
        
        # Check if user account is locked
        if self.is_account_locked(request.user):
            return False
        
        return True
    
    def is_account_locked(self, user):
        """Check if user account is locked due to failed attempts"""
        recent_attempts = LoginAttempt.objects.filter(
            user=user,
            success=False,
            created_at__gte=timezone.now() - timedelta(minutes=15)
        ).count()
        
        return recent_attempts >= 5

class IsOwnerOrReadOnly(BasePermission):
    """
    Custom permission to only allow owners to edit their objects
    """
    
    def has_object_permission(self, request, view, obj):
        # Read permissions for any request
        if request.method in ['GET', 'HEAD', 'OPTIONS']:
            return True
        
        # Write permissions only for the owner
        return obj.owner == request.user

class IsOwner(BasePermission):
    """
    Custom permission to only allow owners to access their objects
    """
    
    def has_object_permission(self, request, view, obj):
        return obj.owner == request.user

class IsVerifiedUser(BasePermission):
    """
    Custom permission to only allow verified users
    """
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        return request.user.is_verified

class RateLimitPermission(BasePermission):
    """
    Rate limiting permission
    """
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return True
        
        # Get rate limit from view
        rate_limit = getattr(view, 'rate_limit', '1000/hour')
        
        # Check rate limit
        return self.check_rate_limit(request.user, rate_limit)
    
    def check_rate_limit(self, user, rate_limit):
        """Check if user has exceeded rate limit"""
        cache_key = f"rate_limit:{user.id}:{rate_limit}"
        current_count = cache.get(cache_key, 0)
        
        # Parse rate limit (e.g., "1000/hour")
        limit, period = rate_limit.split('/')
        limit = int(limit)
        
        if period == 'minute':
            ttl = 60
        elif period == 'hour':
            ttl = 3600
        elif period == 'day':
            ttl = 86400
        else:
            ttl = 3600
        
        if current_count >= limit:
            return False
        
        # Increment counter
        cache.set(cache_key, current_count + 1, ttl)
        return True

class LoginAttemptTracker:
    """
    Track login attempts for security
    """
    
    @staticmethod
    def record_attempt(user, ip_address, user_agent, success=False):
        """Record login attempt"""
        LoginAttempt.objects.create(
            user=user,
            ip_address=ip_address,
            user_agent=user_agent,
            success=success
        )
        
        # If failed, check if account should be locked
        if not success:
            LoginAttemptTracker.check_account_lock(user)
    
    @staticmethod
    def check_account_lock(user):
        """Check if account should be locked due to failed attempts"""
        recent_failed_attempts = LoginAttempt.objects.filter(
            user=user,
            success=False,
            created_at__gte=timezone.now() - timedelta(minutes=15)
        ).count()
        
        if recent_failed_attempts >= 5:
            # Lock account for 15 minutes
            user.is_active = False
            user.locked_until = timezone.now() + timedelta(minutes=15)
            user.save()
            
            logger.warning(f"Account {user.id} locked due to multiple failed attempts")
    
    @staticmethod
    def unlock_account(user):
        """Unlock user account"""
        user.is_active = True
        user.locked_until = None
        user.save()
        
        logger.info(f"Account {user.id} unlocked")

class SessionManager:
    """
    Enhanced session management
    """
    
    @staticmethod
    def create_session(user, request):
        """Create new user session"""
        session_id = secrets.token_urlsafe(32)
        
        UserSession.objects.create(
            user=user,
            session_id=session_id,
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            is_active=True
        )
        
        return session_id
    
    @staticmethod
    def invalidate_session(session_id):
        """Invalidate user session"""
        UserSession.objects.filter(session_id=session_id).update(is_active=False)
    
    @staticmethod
    def invalidate_all_sessions(user):
        """Invalidate all user sessions"""
        UserSession.objects.filter(user=user).update(is_active=False)
    
    @staticmethod
    def get_active_sessions(user):
        """Get all active sessions for user"""
        return UserSession.objects.filter(user=user, is_active=True)
    
    @staticmethod
    def cleanup_expired_sessions():
        """Clean up expired sessions"""
        expired_sessions = UserSession.objects.filter(
            created_at__lt=timezone.now() - timedelta(days=30)
        )
        expired_sessions.delete()

class TokenBlacklist:
    """
    JWT Token blacklist management
    """
    
    @staticmethod
    def blacklist_token(token):
        """Add token to blacklist"""
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        cache.set(f"blacklisted_token:{token_hash}", True, timeout=86400)  # 24 hours
    
    @staticmethod
    def is_blacklisted(token):
        """Check if token is blacklisted"""
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        return cache.get(f"blacklisted_token:{token_hash}") is not None
    
    @staticmethod
    def cleanup_blacklist():
        """Clean up expired blacklisted tokens"""
        try:
            from django.core.cache import cache
            # Get all blacklist keys
            blacklist_keys = cache.keys('blacklist:*')
            for key in blacklist_keys:
                # Check if token is expired
                token_data = cache.get(key)
                if token_data and token_data.get('expires_at'):
                    from django.utils import timezone
                    if timezone.now() > token_data['expires_at']:
                        cache.delete(key)
                        logger.info(f"Cleaned up expired blacklisted token: {key}")
        except Exception as e:
            logger.error(f"Error cleaning up blacklist: {e}")

class SecurityAuditLogger:
    """
    Security audit logging
    """
    
    @staticmethod
    def log_login_attempt(user, ip_address, success, reason=None):
        """Log login attempt"""
        logger.info(f"Login attempt: user={user.id}, ip={ip_address}, success={success}, reason={reason}")
    
    @staticmethod
    def log_permission_denied(user, resource, action):
        """Log permission denied"""
        logger.warning(f"Permission denied: user={user.id}, resource={resource}, action={action}")
    
    @staticmethod
    def log_suspicious_activity(user, activity, details):
        """Log suspicious activity"""
        logger.warning(f"Suspicious activity: user={user.id}, activity={activity}, details={details}")
    
    @staticmethod
    def log_data_access(user, resource, action):
        """Log data access"""
        logger.info(f"Data access: user={user.id}, resource={resource}, action={action}")

class PasswordSecurity:
    """
    Enhanced password security
    """
    
    @staticmethod
    def hash_password(password, salt=None):
        """Hash password with salt"""
        if salt is None:
            salt = secrets.token_hex(32)
        
        password_hash = hashlib.pbkdf2_hmac(
            'sha256',
            password.encode('utf-8'),
            salt.encode('utf-8'),
            100000  # iterations
        )
        
        return password_hash.hex(), salt
    
    @staticmethod
    def verify_password(password, password_hash, salt):
        """Verify password against hash"""
        computed_hash, _ = PasswordSecurity.hash_password(password, salt)
        return computed_hash == password_hash
    
    @staticmethod
    def generate_secure_password(length=16):
        """Generate secure random password"""
        import string
        alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
        return ''.join(secrets.choice(alphabet) for _ in range(length))
    
    @staticmethod
    def check_password_strength(password):
        """Check password strength"""
        score = 0
        feedback = []
        
        # Length check
        if len(password) >= 12:
            score += 1
        else:
            feedback.append("Password should be at least 12 characters long")
        
        # Character variety checks
        if any(c.isupper() for c in password):
            score += 1
        else:
            feedback.append("Password should contain uppercase letters")
        
        if any(c.islower() for c in password):
            score += 1
        else:
            feedback.append("Password should contain lowercase letters")
        
        if any(c.isdigit() for c in password):
            score += 1
        else:
            feedback.append("Password should contain numbers")
        
        if any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password):
            score += 1
        else:
            feedback.append("Password should contain special characters")
        
        # Common pattern checks
        if not any(common in password.lower() for common in ['password', '123456', 'qwerty']):
            score += 1
        else:
            feedback.append("Password should not contain common patterns")
        
        return {
            'score': score,
            'max_score': 6,
            'strength': 'weak' if score < 3 else 'medium' if score < 5 else 'strong',
            'feedback': feedback
        }




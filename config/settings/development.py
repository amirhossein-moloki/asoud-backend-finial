"""
Development Settings for ASOUD Platform
Optimized for local development with SQLite
"""

import os
from .base import *

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

# Development hosts
ALLOWED_HOSTS = [
    'localhost',
    '127.0.0.1',
    '0.0.0.0',
    'asoud.ir',
    'api.asoud.ir',
    'dashboard.asoud.ir',
    'metrics.asoud.ir',
]

# Development database - SQLite for simplicity
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
        'OPTIONS': {
            'timeout': 20,
        }
    }
}

# Development cache - In-memory for simplicity
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'unique-snowflake',
    }
}

# Development channel layers - In-memory
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels.layers.InMemoryChannelLayer'
    }
}

# Development email backend
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Development logging - Disabled for now
LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
}

# Development static files
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Development security settings (relaxed)
SECURE_SSL_REDIRECT = False
SECURE_BROWSER_XSS_FILTER = False
SECURE_CONTENT_TYPE_NOSNIFF = False
SECURE_HSTS_INCLUDE_SUBDOMAINS = False
SECURE_HSTS_PRELOAD = False
SECURE_HSTS_SECONDS = 0

# Development CORS settings (more permissive)
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:8080",
    "http://127.0.0.1:8080",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
    "https://asoud.ir",
    "https://api.asoud.ir",
]

CORS_ALLOW_ALL_ORIGINS = True  # Only for development!

# Development session settings
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False

# Development CSRF settings
CSRF_TRUSTED_ORIGINS = [
    "http://localhost:8000",
    "http://127.0.0.1:8000",
    "https://asoud.ir",
    "https://api.asoud.ir",
]

# Development rate limiting (more permissive)
REST_FRAMEWORK = {
    **REST_FRAMEWORK,
    'DEFAULT_THROTTLE_RATES': {
        'anon': '1000/hour',
        'user': '2000/hour',
        'auth': '100/minute',
        'payment': '50/minute',
        'upload': '100/hour',
    }
}

# Development Celery settings (synchronous for testing)
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True

# Development SMS settings (mock)
SMS_API = {
    'API_KEY': 'development-key',
    'BASE_URL': 'http://localhost:8000/api/v1/sms/mock/',
}

# Development file upload settings
FILE_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024  # 10MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024  # 10MB

# Development debug toolbar (if installed)
if DEBUG:
    try:
        import debug_toolbar
        INSTALLED_APPS += ['debug_toolbar']
        MIDDLEWARE += ['debug_toolbar.middleware.DebugToolbarMiddleware']
        INTERNAL_IPS = ['127.0.0.1', 'localhost']
    except ImportError:
        pass

# Development database optimization - disabled for now

print("[DEV] Development settings loaded - SQLite database, in-memory cache, relaxed security")
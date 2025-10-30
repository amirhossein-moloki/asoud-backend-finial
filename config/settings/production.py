# -----------------------------------------------------------------------------
# Production Settings for Asoud API
# -----------------------------------------------------------------------------

import os
from .base import *
import json
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv(os.path.join(BASE_DIR, '.env'))

# Override Redis configuration for production
REDIS_HOST = os.environ.get('REDIS_HOST', 'redis')
REDIS_PORT = os.environ.get('REDIS_PORT', '6379')
REDIS_PASSWORD = os.environ.get('REDIS_PASSWORD', 'redis_password_2024')
REDIS_URL = f"redis://:{REDIS_PASSWORD}@{REDIS_HOST}:{REDIS_PORT}/0"

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

# Dynamic ALLOWED_HOSTS
ALLOWED_HOSTS_FILE = os.path.join(BASE_DIR, "allowed_hosts.json")
def get_persisted_allowed_hosts():
    try:
        with open(ALLOWED_HOSTS_FILE, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []

BASE_ALLOWED_HOSTS = [
    "api.asoud.ir", 
    "37.32.11.190",
    "asoud.ir",
    "www.asoud.ir",
    "app.asoud.ir",
    "asoud.asoud.ir",
    "sinahashemi1.asoud.ir",
    "0019431351.asoud.ir",
    "localhost",
    "127.0.0.1",
    "backend",  # internal docker hostname for backend service
    "asoud_api",  # nginx container hostname
]

ALLOWED_HOSTS = get_persisted_allowed_hosts() + BASE_ALLOWED_HOSTS

# Secret key from environment - NO FALLBACK IN PRODUCTION
SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY")
if not SECRET_KEY:
    raise ValueError("DJANGO_SECRET_KEY environment variable must be set in production!")

# SMS Settings
SMS_API = os.environ.get("SMS_API", "your-sms-api-key-here")

# CSRF Configuration (Compatible with Cloudflare)
env_origins = os.environ.get("CSRF_TRUSTED_ORIGINS", "")
if env_origins:
    env_list = [origin.strip() for origin in env_origins.split(",")]
else:
    env_list = []

CSRF_TRUSTED_ORIGINS = [
    "https://asoud.ir",
    "https://www.asoud.ir", 
    "https://api.asoud.ir",
    "http://localhost",
    "http://127.0.0.1",
    "http://asoud.ir",
    "http://www.asoud.ir", 
    "http://api.asoud.ir",
    "https://37.32.11.190",
    "http://37.32.11.190",
] + env_list

# Remove duplicates
CSRF_TRUSTED_ORIGINS = list(set(CSRF_TRUSTED_ORIGINS))

# Enhanced CSRF Configuration
CSRF_COOKIE_SECURE = True  # Enable secure cookies
CSRF_COOKIE_SAMESITE = "Lax"  # Changed from "Strict" to "Lax" for admin compatibility
CSRF_USE_SESSIONS = False  # Disabled to avoid middleware order conflict
CSRF_COOKIE_HTTPONLY = False  # Changed to False to allow admin panel to read CSRF token
CSRF_COOKIE_DOMAIN = None
CSRF_COOKIE_PATH = '/'
CSRF_COOKIE_AGE = 3600  # 1 hour (reduced from 1 year)
CSRF_FAILURE_VIEW = 'config.views.csrf_failure_view'

# CSRF Exempt URLs (minimal and secure)
CSRF_EXEMPT_URLS = [
    r'^/api/v1/auth/login/$',  # Only login endpoint
    r'^/api/v1/auth/refresh/$',  # Token refresh
]

# Enhanced Session Configuration
SESSION_COOKIE_SECURE = True  # Enable secure cookies
SESSION_COOKIE_SAMESITE = "Strict"  # Strict same-site policy
SESSION_COOKIE_HTTPONLY = True  # Prevent XSS attacks
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
SESSION_COOKIE_AGE = 3600  # 1 hour
SESSION_SAVE_EVERY_REQUEST = True

# Enhanced Security Headers
# SSL Configuration for production
SECURE_SSL_REDIRECT = False  # Disabled for local development
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_HSTS_SECONDS = 31536000  # 1 year
SECURE_REDIRECT_EXEMPT = [
    r"^health/?$",
    r"^api/v1/health/?$",
]

# Additional Security Settings
SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'
X_FRAME_OPTIONS = 'DENY'
SECURE_CROSS_ORIGIN_OPENER_POLICY = 'same-origin'

# Static files
STATIC_ROOT = "/asoud/static"
STATICFILES_DIRS = []

# WhiteNoise configuration for serving static files in production
WHITENOISE_USE_FINDERS = True
WHITENOISE_AUTOREFRESH = True
WHITENOISE_MANIFEST_STRICT = False


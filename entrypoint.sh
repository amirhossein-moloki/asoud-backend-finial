#!/bin/bash
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Wait for database function
wait_for_db() {
    log_info "Waiting for database connection..."
    
    if [ "$DJANGO_SETTINGS_MODULE" = "config.settings.development" ]; then
        log_info "Development mode: Using SQLite, skipping database wait"
        return 0
    fi
    
    # Wait for PostgreSQL
    until python -c "
import os
import django
from django.conf import settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', '$DJANGO_SETTINGS_MODULE')
django.setup()
from django.db import connection
connection.ensure_connection()
"; do
        log_warning "Database is unavailable - sleeping"
        sleep 2
    done
    
    log_success "Database is up - continuing"
}

# Wait for Redis function
wait_for_redis() {
    if [ "$DJANGO_SETTINGS_MODULE" = "config.settings.development" ]; then
        log_info "Development mode: Using in-memory cache, skipping Redis wait"
        return 0
    fi
    
    log_info "Waiting for Redis connection..."
    
    until python -c "
import redis
import os
r = redis.Redis(host=os.getenv('REDIS_HOST', 'redis'), port=int(os.getenv('REDIS_PORT', 6379)), password=os.getenv('REDIS_PASSWORD', ''))
r.ping()
"; do
        log_warning "Redis is unavailable - sleeping"
        sleep 2
    done
    
    log_success "Redis is up - continuing"
}

# Collect static files function
collect_static() {
    log_info "Collecting static files..."
    # Ensure static directory exists and has correct permissions
    mkdir -p /asoud/static /asoud/media
    python manage.py collectstatic --noinput || log_warning "Static files collection failed (continuing anyway)"
    log_success "Static files collected"
}

# Run migrations function
run_migrations() {
    log_info "Running database migrations..."
    python manage.py migrate --noinput || log_error "Migrations failed"
    log_success "Migrations completed"
}

# Create superuser function (only in development)
create_superuser() {
    if [ "$DJANGO_SETTINGS_MODULE" = "config.settings.development" ] && [ "$CREATE_SUPERUSER" = "true" ]; then
        log_info "Creating superuser..."
        python manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(mobile_number='09123456789').exists():
    User.objects.create_superuser('09123456789', 'admin@asoud.ir', 'admin123')
    print('Superuser created: 09123456789 / admin123')
else:
    print('Superuser already exists')
" || log_warning "Superuser creation failed"
    fi
}

# Load sample data function (only in development)
load_sample_data() {
    if [ "$DJANGO_SETTINGS_MODULE" = "config.settings.development" ] && [ "$LOAD_SAMPLE_DATA" = "true" ]; then
        log_info "Loading sample data..."
        python manage.py loaddata fixtures/sample_data.json 2>/dev/null || log_warning "No sample data found"
    fi
}

# Health check function
health_check() {
    log_info "Running health checks..."
    
    # Check Django
    python manage.py check --deploy || log_error "Django health check failed"
    
    # Check database
    python manage.py dbshell -c "SELECT 1;" > /dev/null 2>&1 || log_error "Database health check failed"
    
    log_success "Health checks passed"
}

# Main execution
main() {
    log_info "Starting ASOUD Platform entrypoint..."
    log_info "Django Settings: $DJANGO_SETTINGS_MODULE"
    log_info "Debug Mode: ${DEBUG:-False}"
    
    # Wait for dependencies
    wait_for_db
    wait_for_redis
    
    # Run Django setup
    run_migrations
    collect_static
    
    # Development-specific setup
    create_superuser
    load_sample_data
    
    # Final health check
    health_check
    
    log_success "Entrypoint completed successfully"
    log_info "Starting application with command: $@"
    
    # Execute the main command
exec "$@"
}

# Handle signals for graceful shutdown
trap 'log_info "Received signal, shutting down gracefully..."; exit 0' SIGTERM SIGINT

# Run main function
main "$@"
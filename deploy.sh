#!/bin/bash

# Asoud Project - Automated Deployment Script
# با این script می‌تونی به راحتی پروژه رو deploy کنی

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
ENVIRONMENT="production"
SKIP_BACKUP=false
SKIP_MIGRATIONS=false
SKIP_COLLECTSTATIC=false

# Functions
print_header() {
    echo -e "${BLUE}================================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}================================================${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --env)
            ENVIRONMENT="$2"
            shift 2
            ;;
        --skip-backup)
            SKIP_BACKUP=true
            shift
            ;;
        --skip-migrations)
            SKIP_MIGRATIONS=true
            shift
            ;;
        --skip-collectstatic)
            SKIP_COLLECTSTATIC=true
            shift
            ;;
        -h|--help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --env ENV              Environment to deploy (production|development) [default: production]"
            echo "  --skip-backup          Skip database backup"
            echo "  --skip-migrations      Skip database migrations"
            echo "  --skip-collectstatic   Skip collecting static files"
            echo "  -h, --help             Show this help message"
            exit 0
            ;;
        *)
            print_error "Unknown option: $1"
            echo "Use -h or --help for usage information"
            exit 1
            ;;
    esac
done

# Validate environment
if [[ "$ENVIRONMENT" != "production" && "$ENVIRONMENT" != "development" ]]; then
    print_error "Invalid environment: $ENVIRONMENT"
    echo "Must be 'production' or 'development'"
    exit 1
fi

# Set compose file
if [ "$ENVIRONMENT" = "production" ]; then
    COMPOSE_FILE="docker-compose.prod.yaml"
else
    COMPOSE_FILE="docker-compose.dev.yaml"
fi

print_header "🚀 Asoud Deployment - $ENVIRONMENT"

# Step 1: Check prerequisites
print_info "Checking prerequisites..."

if ! command -v docker &> /dev/null; then
    print_error "Docker is not installed"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    print_error "Docker Compose is not installed"
    exit 1
fi

if [ ! -f ".env" ]; then
    print_error ".env file not found"
    echo "Copy .env.example to .env and configure it"
    exit 1
fi

print_success "Prerequisites check passed"

# Step 2: Backup database (only for production)
if [ "$ENVIRONMENT" = "production" ] && [ "$SKIP_BACKUP" = false ]; then
    print_info "Creating database backup..."
    
    BACKUP_DIR="./backups"
    mkdir -p "$BACKUP_DIR"
    BACKUP_FILE="$BACKUP_DIR/db_backup_$(date +%Y%m%d_%H%M%S).sql.gz"
    
    if docker-compose -f "$COMPOSE_FILE" ps db2 | grep -q "Up"; then
        docker-compose -f "$COMPOSE_FILE" exec -T db2 pg_dump -U asoud_user asoud_db | gzip > "$BACKUP_FILE" 2>/dev/null || true
        
        if [ -f "$BACKUP_FILE" ]; then
            print_success "Backup created: $BACKUP_FILE"
        else
            print_warning "Backup skipped (database not running or empty)"
        fi
    else
        print_warning "Database not running, skipping backup"
    fi
fi

# Step 3: Pull latest images
print_info "Pulling latest images..."
docker-compose -f "$COMPOSE_FILE" pull

# Step 4: Build services
print_info "Building services..."
docker-compose -f "$COMPOSE_FILE" build --no-cache web

# Step 5: Stop old containers
print_info "Stopping old containers..."
docker-compose -f "$COMPOSE_FILE" down

# Step 6: Start services
print_info "Starting services..."
docker-compose -f "$COMPOSE_FILE" up -d

# Wait for services to be ready
print_info "Waiting for services to start..."
sleep 10

# Step 7: Run migrations
if [ "$SKIP_MIGRATIONS" = false ]; then
    print_info "Running database migrations..."
    docker-compose -f "$COMPOSE_FILE" exec -T web python manage.py migrate --noinput
    print_success "Migrations completed"
fi

# Step 8: Collect static files
if [ "$SKIP_COLLECTSTATIC" = false ]; then
    print_info "Collecting static files..."
    docker-compose -f "$COMPOSE_FILE" exec -T web python manage.py collectstatic --noinput
    print_success "Static files collected"
fi

# Step 9: Restart NGINX to pick up new static files
print_info "Reloading NGINX..."
docker-compose -f "$COMPOSE_FILE" exec nginx nginx -s reload 2>/dev/null || print_warning "NGINX reload skipped"

# Step 10: Health checks
print_header "🏥 Health Checks"

# Check web service
if docker-compose -f "$COMPOSE_FILE" ps web | grep -q "Up"; then
    print_success "Django API is running"
else
    print_error "Django API is not running"
fi

# Check nginx
if docker-compose -f "$COMPOSE_FILE" ps nginx | grep -q "Up"; then
    print_success "NGINX is running"
else
    print_error "NGINX is not running"
fi

# Check database
if docker-compose -f "$COMPOSE_FILE" ps | grep -qE "(db|db2)" | grep -q "Up"; then
    print_success "Database is running"
else
    print_error "Database is not running"
fi

# Check redis
if docker-compose -f "$COMPOSE_FILE" ps redis | grep -q "Up"; then
    print_success "Redis is running"
else
    print_error "Redis is not running"
fi

# Step 11: Test endpoints (only for production)
if [ "$ENVIRONMENT" = "production" ]; then
    print_header "🧪 Testing Endpoints"
    
    # Test health endpoint
    if curl -sf -k https://api.asoud.ir/api/v1/health/ > /dev/null 2>&1; then
        print_success "Health endpoint is accessible"
    else
        print_warning "Health endpoint test failed (might take a moment to start)"
    fi
    
    # Test admin panel
    if curl -sf -k -I https://api.asoud.ir/admin/ | grep -q "302"; then
        print_success "Admin panel is accessible"
    else
        print_warning "Admin panel test failed"
    fi
    
    # Test static files
    if curl -sf -k https://api.asoud.ir/static/admin/css/base.css > /dev/null 2>&1; then
        print_success "Static files are accessible"
    else
        print_warning "Static files test failed"
    fi
fi

# Final summary
print_header "📊 Deployment Summary"

echo ""
echo -e "${GREEN}✅ Deployment completed successfully!${NC}"
echo ""
echo "📝 Container Status:"
docker-compose -f "$COMPOSE_FILE" ps
echo ""

if [ "$ENVIRONMENT" = "production" ]; then
    echo "🌐 Access URLs:"
    echo "   - API: https://api.asoud.ir"
    echo "   - Admin Panel: https://api.asoud.ir/admin/"
    echo "   - Health Check: https://api.asoud.ir/api/v1/health/"
else
    echo "🌐 Access URLs:"
    echo "   - API: http://localhost:8000"
    echo "   - Admin Panel: http://localhost/admin/"
fi

echo ""
echo "📋 Useful Commands:"
echo "   - View logs: docker-compose -f $COMPOSE_FILE logs -f"
echo "   - Stop services: docker-compose -f $COMPOSE_FILE down"
echo "   - Restart service: docker-compose -f $COMPOSE_FILE restart [service_name]"
echo ""

print_success "Deployment finished! 🎉"


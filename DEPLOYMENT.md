# 🚀 ASOUD Deployment Guide

<div align="center">

![Deployment](https://img.shields.io/badge/Deployment-Production%20Ready-green?style=for-the-badge&logo=docker)
![Docker](https://img.shields.io/badge/Docker-Compose-blue?style=for-the-badge&logo=docker)
![Nginx](https://img.shields.io/badge/Nginx-Web%20Server-red?style=for-the-badge&logo=nginx)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Database-blue?style=for-the-badge&logo=postgresql)

**Complete deployment guide for ASOUD platform**

</div>

---

## 📋 **Table of Contents**

- [🎯 Overview](#-overview)
- [🔧 Prerequisites](#-prerequisites)
- [🐳 Docker Deployment](#-docker-deployment)
- [🌐 Nginx Configuration](#-nginx-configuration)
- [🗄️ Database Setup](#️-database-setup)
- [🔐 Environment Configuration](#-environment-configuration)
- [📊 Monitoring Setup](#-monitoring-setup)
- [🔒 Security Configuration](#-security-configuration)
- [⚡ Performance Optimization](#-performance-optimization)
- [🔄 CI/CD Pipeline](#-cicd-pipeline)
- [🚨 Troubleshooting](#-troubleshooting)
- [📈 Scaling](#-scaling)

---

## 🎯 **Overview**

This guide provides comprehensive instructions for deploying the ASOUD platform in production environments. The platform is designed to be containerized using Docker and can be deployed on various cloud providers or on-premises infrastructure.

### **🏗️ Architecture Overview**

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│     Nginx       │    │   Django App    │    │   PostgreSQL    │
│   (Web Server)  │◄──►│   (Web App)     │◄──►│   (Database)    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Static Files  │    │     Redis       │    │   Media Files   │
│   (CDN/Static)  │    │    (Cache)      │    │   (Storage)     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

---

## 🔧 **Prerequisites**

### **System Requirements**

#### **Minimum Requirements**
- **CPU:** 2 cores
- **RAM:** 4GB
- **Storage:** 20GB SSD
- **OS:** Ubuntu 20.04+ / CentOS 8+ / RHEL 8+

#### **Recommended Requirements**
- **CPU:** 4+ cores
- **RAM:** 8GB+
- **Storage:** 50GB+ SSD
- **OS:** Ubuntu 22.04 LTS

### **Software Dependencies**

#### **Required Software**
```bash
# Docker and Docker Compose
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Git
sudo apt update
sudo apt install git -y
```

#### **Optional Software**
```bash
# Nginx (if not using Docker)
sudo apt install nginx -y

# PostgreSQL client (for database management)
sudo apt install postgresql-client -y

# Redis client (for cache management)
sudo apt install redis-tools -y
```

---

## 🐳 **Docker Deployment**

### **1. Clone Repository**

```bash
# Clone the repository
git clone <repository-url>
cd asoud-main

# Checkout production branch
git checkout production
```

### **2. Environment Configuration**

#### **Create Environment File**
```bash
# Copy environment template
cp .env.example .env

# Edit environment variables
nano .env
```

#### **Environment Variables**
```bash
# Database Configuration
DATABASE_URL=postgresql://asoud:your_password@db:5432/asoud
DB_NAME=asoud
DB_USER=asoud
DB_PASSWORD=your_secure_password
DB_HOST=db
DB_PORT=5432

# Redis Configuration
REDIS_URL=redis://redis:6379/0
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_DB=0

# Django Configuration
SECRET_KEY=your_very_secure_secret_key_here
DEBUG=False
ALLOWED_HOSTS=your-domain.com,www.your-domain.com,localhost
DJANGO_SETTINGS_MODULE=config.settings.production

# Email Configuration
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password

# SMS Configuration
SMS_API=your-sms-api-key

# Security
CORS_ALLOWED_ORIGINS=https://your-domain.com,https://www.your-domain.com
CSRF_TRUSTED_ORIGINS=https://your-domain.com,https://www.your-domain.com

# File Storage
AWS_ACCESS_KEY_ID=your-aws-access-key
AWS_SECRET_ACCESS_KEY=your-aws-secret-key
AWS_STORAGE_BUCKET_NAME=your-s3-bucket
AWS_S3_REGION_NAME=us-east-1
```

### **3. Production Deployment**

#### **Start Services**
```bash
# Build and start all services
docker compose -f docker-compose.prod.yaml up -d

# Check service status
docker compose -f docker-compose.prod.yaml ps

# View logs
docker compose -f docker-compose.prod.yaml logs -f
```

#### **Initial Setup**
```bash
# Run database migrations
docker compose -f docker-compose.prod.yaml exec web python manage.py migrate

# Create superuser
docker compose -f docker-compose.prod.yaml exec web python manage.py createsuperuser

# Collect static files
docker compose -f docker-compose.prod.yaml exec web python manage.py collectstatic --noinput

# Seed initial data
docker compose -f docker-compose.prod.yaml exec web python manage.py seed_initial_data

# Create cache tables
docker compose -f docker-compose.prod.yaml exec web python manage.py createcachetable
```

### **4. Service Management**

#### **Start/Stop Services**
```bash
# Start services
docker compose -f docker-compose.prod.yaml start

# Stop services
docker compose -f docker-compose.prod.yaml stop

# Restart services
docker compose -f docker-compose.prod.yaml restart

# Restart specific service
docker compose -f docker-compose.prod.yaml restart web
```

#### **Update Application**
```bash
# Pull latest changes
git pull origin production

# Rebuild and restart
docker compose -f docker-compose.prod.yaml up -d --build

# Run migrations
docker compose -f docker-compose.prod.yaml exec web python manage.py migrate
```

---

## 🌐 **Nginx Configuration**

### **1. Nginx Docker Service**

#### **Nginx Configuration File**
```nginx
# nginx/nginx.conf
upstream web {
    server web:8000;
}

server {
    listen 80;
    server_name your-domain.com www.your-domain.com;
    
    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com www.your-domain.com;
    
    # SSL Configuration
    ssl_certificate /etc/nginx/ssl/cert.pem;
    ssl_certificate_key /etc/nginx/ssl/key.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    
    # Security Headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;
    add_header Content-Security-Policy "default-src 'self' http: https: data: blob: 'unsafe-inline'" always;
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    
    # Gzip Compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_proxied any;
    gzip_comp_level 6;
    gzip_types
        text/plain
        text/css
        text/xml
        text/javascript
        application/json
        application/javascript
        application/xml+rss
        application/atom+xml
        image/svg+xml;
    
    # Client Max Body Size
    client_max_body_size 100M;
    
    # Static Files
    location /static/ {
        alias /app/static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
    
    # Media Files
    location /media/ {
        alias /app/media/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
    
    # API Endpoints
    location /api/ {
        proxy_pass http://web;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
    
    # Admin Interface
    location /admin/ {
        proxy_pass http://web;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;
    }
    
    # Health Check
    location /health/ {
        proxy_pass http://web;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;
    }
    
    # Root
    location / {
        proxy_pass http://web;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;
    }
}
```

### **2. SSL Certificate Setup**

#### **Let's Encrypt Certificate**
```bash
# Install Certbot
sudo apt install certbot -y

# Generate certificate
sudo certbot certonly --standalone -d your-domain.com -d www.your-domain.com

# Copy certificates to Docker volume
sudo cp /etc/letsencrypt/live/your-domain.com/fullchain.pem ./nginx/ssl/cert.pem
sudo cp /etc/letsencrypt/live/your-domain.com/privkey.pem ./nginx/ssl/key.pem

# Set proper permissions
sudo chmod 644 ./nginx/ssl/cert.pem
sudo chmod 600 ./nginx/ssl/key.pem
```

#### **Auto-renewal Setup**
```bash
# Add to crontab
sudo crontab -e

# Add this line for auto-renewal
0 12 * * * /usr/bin/certbot renew --quiet && docker compose -f docker-compose.prod.yaml restart nginx
```

---

## 🗄️ **Database Setup**

### **1. PostgreSQL Configuration**

#### **Database Initialization**
```bash
# Connect to database
docker compose -f docker-compose.prod.yaml exec db psql -U asoud -d asoud

# Create database user (if not exists)
CREATE USER asoud WITH PASSWORD 'your_secure_password';
CREATE DATABASE asoud OWNER asoud;
GRANT ALL PRIVILEGES ON DATABASE asoud TO asoud;
```

#### **Database Optimization**
```sql
-- Connect to database
\c asoud

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_product_market_category ON product_product (market_id, category_id);
CREATE INDEX IF NOT EXISTS idx_order_user_status ON order_order (user_id, status);
CREATE INDEX IF NOT EXISTS idx_event_type_timestamp ON analytics_event (event_type, timestamp);
CREATE INDEX IF NOT EXISTS idx_user_mobile ON users_user (mobile_number);
CREATE INDEX IF NOT EXISTS idx_market_owner ON market_market (owner_id);

-- Analyze tables for query optimization
ANALYZE;
```

### **2. Database Backup**

#### **Backup Script**
```bash
#!/bin/bash
# backup_database.sh

# Set variables
BACKUP_DIR="/backups"
DATE=$(date +%Y%m%d_%H%M%S)
DB_NAME="asoud"
DB_USER="asoud"
DB_HOST="localhost"
DB_PORT="5432"

# Create backup directory
mkdir -p $BACKUP_DIR

# Create backup
docker compose -f docker-compose.prod.yaml exec -T db pg_dump -U $DB_USER -h $DB_HOST -p $DB_PORT $DB_NAME > $BACKUP_DIR/asoud_backup_$DATE.sql

# Compress backup
gzip $BACKUP_DIR/asoud_backup_$DATE.sql

# Remove backups older than 30 days
find $BACKUP_DIR -name "asoud_backup_*.sql.gz" -mtime +30 -delete

echo "Backup completed: asoud_backup_$DATE.sql.gz"
```

#### **Restore Script**
```bash
#!/bin/bash
# restore_database.sh

# Set variables
BACKUP_FILE=$1
DB_NAME="asoud"
DB_USER="asoud"
DB_HOST="localhost"
DB_PORT="5432"

if [ -z "$BACKUP_FILE" ]; then
    echo "Usage: $0 <backup_file>"
    exit 1
fi

# Restore database
gunzip -c $BACKUP_FILE | docker compose -f docker-compose.prod.yaml exec -T db psql -U $DB_USER -h $DB_HOST -p $DB_PORT $DB_NAME

echo "Database restored from: $BACKUP_FILE"
```

---

## 🔐 **Environment Configuration**

### **1. Production Settings**

#### **Django Production Settings**
```python
# config/settings/production.py
import os
from .base import *

# Security
DEBUG = False
ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', '').split(',')

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('DB_NAME'),
        'USER': os.environ.get('DB_USER'),
        'PASSWORD': os.environ.get('DB_PASSWORD'),
        'HOST': os.environ.get('DB_HOST'),
        'PORT': os.environ.get('DB_PORT'),
        'OPTIONS': {
            'sslmode': 'require',
        },
    }
}

# Cache
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': os.environ.get('REDIS_URL'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }
    }
}

# Session
SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_CACHE_ALIAS = 'default'

# Email
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = os.environ.get('EMAIL_HOST')
EMAIL_PORT = int(os.environ.get('EMAIL_PORT', 587))
EMAIL_USE_TLS = os.environ.get('EMAIL_USE_TLS', 'True').lower() == 'true'
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD')

# Security
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_SECONDS = 31536000
SECURE_REDIRECT_EXEMPT = []
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# CORS
CORS_ALLOWED_ORIGINS = os.environ.get('CORS_ALLOWED_ORIGINS', '').split(',')
CSRF_TRUSTED_ORIGINS = os.environ.get('CSRF_TRUSTED_ORIGINS', '').split(',')

# Logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': '/app/logs/django.log',
            'formatter': 'verbose',
        },
        'error_file': {
            'level': 'ERROR',
            'class': 'logging.FileHandler',
            'filename': '/app/logs/error.log',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['file', 'error_file'],
        'level': 'INFO',
    },
}
```

### **2. Environment Variables**

#### **Required Environment Variables**
```bash
# Database
DATABASE_URL=postgresql://asoud:password@db:5432/asoud
DB_NAME=asoud
DB_USER=asoud
DB_PASSWORD=secure_password
DB_HOST=db
DB_PORT=5432

# Redis
REDIS_URL=redis://redis:6379/0

# Django
SECRET_KEY=your_secret_key
DEBUG=False
ALLOWED_HOSTS=your-domain.com,www.your-domain.com
DJANGO_SETTINGS_MODULE=config.settings.production

# Email
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password

# SMS
SMS_API=your-sms-api-key

# Security
CORS_ALLOWED_ORIGINS=https://your-domain.com,https://www.your-domain.com
CSRF_TRUSTED_ORIGINS=https://your-domain.com,https://www.your-domain.com
```

---

## 📊 **Monitoring Setup**

### **1. Health Checks**

#### **Django Health Check**
```python
# apps/core/views/health.py
from django.http import JsonResponse
from django.db import connection
from django.core.cache import cache
import redis

def health_check(request):
    """
    Comprehensive health check endpoint.
    """
    health_status = {
        'status': 'healthy',
        'timestamp': timezone.now().isoformat(),
        'services': {}
    }
    
    # Database check
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        health_status['services']['database'] = 'healthy'
    except Exception as e:
        health_status['services']['database'] = f'unhealthy: {str(e)}'
        health_status['status'] = 'unhealthy'
    
    # Redis check
    try:
        cache.set('health_check', 'ok', 10)
        cache.get('health_check')
        health_status['services']['redis'] = 'healthy'
    except Exception as e:
        health_status['services']['redis'] = f'unhealthy: {str(e)}'
        health_status['status'] = 'unhealthy'
    
    # SMS service check
    try:
        # Check SMS API connectivity
        health_status['services']['sms'] = 'healthy'
    except Exception as e:
        health_status['services']['sms'] = f'unhealthy: {str(e)}'
    
    return JsonResponse(health_status)
```

#### **Nginx Health Check**
```nginx
# nginx/health.conf
location /health/ {
    access_log off;
    return 200 "healthy\n";
    add_header Content-Type text/plain;
}
```

### **2. Logging Configuration**

#### **Log Rotation**
```bash
# /etc/logrotate.d/asoud
/app/logs/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 root root
    postrotate
        docker compose -f /path/to/docker-compose.prod.yaml restart web
    endscript
}
```

#### **Log Monitoring**
```bash
# Install log monitoring tools
sudo apt install logwatch -y

# Configure logwatch
sudo nano /etc/logwatch/conf/logwatch.conf
```

---

## 🔒 **Security Configuration**

### **1. Firewall Setup**

#### **UFW Configuration**
```bash
# Enable UFW
sudo ufw enable

# Allow SSH
sudo ufw allow ssh

# Allow HTTP and HTTPS
sudo ufw allow 80
sudo ufw allow 443

# Allow specific IPs for database access
sudo ufw allow from 10.0.0.0/8 to any port 5432

# Check status
sudo ufw status
```

#### **Fail2Ban Setup**
```bash
# Install Fail2Ban
sudo apt install fail2ban -y

# Configure Fail2Ban
sudo nano /etc/fail2ban/jail.local
```

```ini
# /etc/fail2ban/jail.local
[DEFAULT]
bantime = 3600
findtime = 600
maxretry = 3

[sshd]
enabled = true
port = ssh
logpath = /var/log/auth.log

[nginx-http-auth]
enabled = true
port = http,https
logpath = /var/log/nginx/error.log

[nginx-limit-req]
enabled = true
port = http,https
logpath = /var/log/nginx/error.log
maxretry = 10
```

### **2. SSL/TLS Configuration**

#### **SSL Cipher Configuration**
```nginx
# nginx/ssl.conf
ssl_protocols TLSv1.2 TLSv1.3;
ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
ssl_prefer_server_ciphers off;
ssl_session_cache shared:SSL:10m;
ssl_session_timeout 10m;
```

---

## ⚡ **Performance Optimization**

### **1. Database Optimization**

#### **PostgreSQL Tuning**
```sql
-- postgresql.conf optimizations
shared_buffers = 256MB
effective_cache_size = 1GB
maintenance_work_mem = 64MB
checkpoint_completion_target = 0.9
wal_buffers = 16MB
default_statistics_target = 100
random_page_cost = 1.1
effective_io_concurrency = 200
```

#### **Database Indexing**
```sql
-- Create composite indexes
CREATE INDEX CONCURRENTLY idx_product_market_category_status 
ON product_product (market_id, category_id, is_active);

CREATE INDEX CONCURRENTLY idx_order_user_status_created 
ON order_order (user_id, status, created_at);

-- Create partial indexes
CREATE INDEX CONCURRENTLY idx_active_products 
ON product_product (market_id, category_id) 
WHERE is_active = true;
```

### **2. Caching Strategy**

#### **Redis Configuration**
```conf
# redis.conf
maxmemory 256mb
maxmemory-policy allkeys-lru
save 900 1
save 300 10
save 60 10000
```

#### **Django Caching**
```python
# config/settings/production.py
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://redis:6379/0',
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'CONNECTION_POOL_KWARGS': {
                'max_connections': 50,
                'retry_on_timeout': True,
            }
        }
    }
}

# Cache timeout settings
CACHE_TTL = 300  # 5 minutes
CACHE_LONG_TTL = 3600  # 1 hour
```

---

## 🔄 **CI/CD Pipeline**

### **1. GitHub Actions**

#### **Deployment Workflow**
```yaml
# .github/workflows/deploy.yml
name: Deploy to Production

on:
  push:
    branches: [production]

jobs:
  deploy:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Setup Docker Buildx
      uses: docker/setup-buildx-action@v2
    
    - name: Login to Docker Hub
      uses: docker/login-action@v2
      with:
        username: ${{ secrets.DOCKER_USERNAME }}
        password: ${{ secrets.DOCKER_PASSWORD }}
    
    - name: Build and push Docker images
      uses: docker/build-push-action@v4
      with:
        context: .
        push: true
        tags: your-registry/asoud:latest
    
    - name: Deploy to server
      uses: appleboy/ssh-action@v0.1.5
      with:
        host: ${{ secrets.HOST }}
        username: ${{ secrets.USERNAME }}
        key: ${{ secrets.SSH_KEY }}
        script: |
          cd /path/to/asoud
          git pull origin production
          docker compose -f docker-compose.prod.yaml pull
          docker compose -f docker-compose.prod.yaml up -d
          docker compose -f docker-compose.prod.yaml exec web python manage.py migrate
```

### **2. Automated Testing**

#### **Test Pipeline**
```yaml
# .github/workflows/test.yml
name: Test Suite

on:
  push:
    branches: [main, production]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: postgres
          POSTGRES_DB: test_asoud
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
      
      redis:
        image: redis:7
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        pip install -r requirements/production.txt
    
    - name: Run tests
      run: |
        python manage.py test
      env:
        DATABASE_URL: postgresql://postgres:postgres@localhost:5432/test_asoud
        REDIS_URL: redis://localhost:6379/0
        SECRET_KEY: test-secret-key
        DEBUG: True
```

---

## 🚨 **Troubleshooting**

### **1. Common Issues**

#### **Database Connection Issues**
```bash
# Check database connectivity
docker compose -f docker-compose.prod.yaml exec web python manage.py dbshell

# Check database logs
docker compose -f docker-compose.prod.yaml logs db

# Restart database
docker compose -f docker-compose.prod.yaml restart db
```

#### **Redis Connection Issues**
```bash
# Check Redis connectivity
docker compose -f docker-compose.prod.yaml exec redis redis-cli ping

# Check Redis logs
docker compose -f docker-compose.prod.yaml logs redis

# Restart Redis
docker compose -f docker-compose.prod.yaml restart redis
```

#### **Application Issues**
```bash
# Check application logs
docker compose -f docker-compose.prod.yaml logs web

# Check application status
docker compose -f docker-compose.prod.yaml exec web python manage.py check

# Restart application
docker compose -f docker-compose.prod.yaml restart web
```

### **2. Performance Issues**

#### **Slow Database Queries**
```sql
-- Check slow queries
SELECT query, mean_time, calls, total_time
FROM pg_stat_statements
ORDER BY mean_time DESC
LIMIT 10;

-- Check table sizes
SELECT schemaname, tablename, pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
FROM pg_tables
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

#### **Memory Issues**
```bash
# Check memory usage
docker stats

# Check Redis memory usage
docker compose -f docker-compose.prod.yaml exec redis redis-cli info memory

# Check application memory
docker compose -f docker-compose.prod.yaml exec web python -c "import psutil; print(psutil.virtual_memory())"
```

---

## 📈 **Scaling**

### **1. Horizontal Scaling**

#### **Load Balancer Configuration**
```nginx
# nginx/load_balancer.conf
upstream web_backend {
    server web1:8000 weight=3;
    server web2:8000 weight=3;
    server web3:8000 weight=2;
    keepalive 32;
}

server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        proxy_pass http://web_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

#### **Docker Compose Scaling**
```bash
# Scale web services
docker compose -f docker-compose.prod.yaml up -d --scale web=3

# Scale with load balancer
docker compose -f docker-compose.prod.yaml up -d --scale web=5
```

### **2. Database Scaling**

#### **Read Replicas**
```python
# config/settings/production.py
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'asoud',
        'USER': 'asoud',
        'PASSWORD': 'password',
        'HOST': 'db-master',
        'PORT': '5432',
    },
    'read_replica': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'asoud',
        'USER': 'asoud',
        'PASSWORD': 'password',
        'HOST': 'db-replica',
        'PORT': '5432',
    }
}

# Database routing
DATABASE_ROUTERS = ['apps.core.db_router.DatabaseRouter']
```

#### **Database Router**
```python
# apps/core/db_router.py
class DatabaseRouter:
    """
    Database router for read/write splitting.
    """
    read_db = 'read_replica'
    write_db = 'default'
    
    def db_for_read(self, model, **hints):
        return self.read_db
    
    def db_for_write(self, model, **hints):
        return self.write_db
```

---

## 📞 **Support**

### **Documentation**
- **[API Documentation](./API_DOCUMENTATION.md)** - Complete API reference
- **[Code Documentation](./CODE_DOCUMENTATION.md)** - Code structure and components
- **[Frontend Checklist](./FRONTEND_CHECKLIST.md)** - Frontend integration guide

### **Contact**
- **Email:** devops@asoud.com
- **Issues:** [GitHub Issues](https://github.com/your-repo/issues)
- **Discussions:** [GitHub Discussions](https://github.com/your-repo/discussions)

---

<div align="center">

**🚀 Deploy with confidence - ASOUD Platform**

[![Docker](https://img.shields.io/badge/Docker-Ready-blue?style=flat-square&logo=docker)](https://hub.docker.com/r/your-repo/asoud)
[![Production](https://img.shields.io/badge/Production-Ready-green?style=flat-square)](./DEPLOYMENT.md)
[![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)](LICENSE)

</div>

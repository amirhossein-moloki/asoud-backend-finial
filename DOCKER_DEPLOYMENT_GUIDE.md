# 🐳 راهنمای جامع Deploy با Docker

این فایل راهنمای کامل برای راه‌اندازی پروژه Asoud با Docker است.

---

## 📋 پیش‌نیازها

```bash
# بررسی نسخه Docker
docker --version  # باید >= 20.10

# بررسی نسخه Docker Compose
docker-compose --version  # باید >= 2.0
```

---

## 🚀 راه‌اندازی سریع

### 1. Development Environment

```bash
# کپی کردن فایل محیطی
cp .env.example .env

# ویرایش متغیرها
nano .env

# Build و راه‌اندازی
docker-compose -f docker-compose.dev.yaml up -d --build

# مشاهده logs
docker-compose -f docker-compose.dev.yaml logs -f

# بررسی وضعیت
docker-compose -f docker-compose.dev.yaml ps
```

### 2. Production Environment

```bash
# تنظیم متغیرهای محیطی
nano .env

# Build و راه‌اندازی
docker-compose -f docker-compose.prod.yaml up -d --build

# بررسی health
curl -k https://api.asoud.ir/api/v1/health/
```

---

## 🏗️ ساختار Services

### Development (`docker-compose.dev.yaml`):
```
┌─────────────────────────────────────┐
│  asoud_nginx_dev (nginx:alpine)     │ Port 80, 443
│  - Optimized NGINX configs          │
│  - Static & Media files             │
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│  asoud_api (Django)                 │ Port 8000
│  - Development server               │
│  - Hot reload enabled               │
└──────────────┬──────────────────────┘
               │
       ┌───────┴────────┐
       │                │
┌──────▼─────┐   ┌─────▼──────┐
│ PostgreSQL │   │   Redis    │
│  Port 5432 │   │  Port 6379 │
└────────────┘   └────────────┘
```

### Production (`docker-compose.prod.yaml`):
```
┌────────────────────────────────────────┐
│  Traefik (Reverse Proxy)               │
│  - SSL/TLS termination                 │
│  - Let's Encrypt auto-renewal          │
└──────────────┬─────────────────────────┘
               │
┌──────────────▼─────────────────────────┐
│  asoud_nginx (nginx:alpine)            │ Port 80, 443
│  - GZIP compression                    │
│  - Rate limiting                       │
│  - Proxy buffering                     │
│  - WebSocket support                   │
└──────────────┬─────────────────────────┘
               │
┌──────────────▼─────────────────────────┐
│  asoud_api (Django + Daphne)           │ Port 8000
│  - ASGI server for WebSocket           │
│  - Production optimized                │
└──────────────┬─────────────────────────┘
               │
       ┌───────┴────────┐
       │                │
┌──────▼─────┐   ┌─────▼──────┐
│ PostgreSQL │   │   Redis    │
│  (db2)     │   │ (with auth)│
└────────────┘   └────────────┘
```

---

## 📁 فایل‌های NGINX

### 1. `nginx/nginx-main.conf` (Main Config)
**تنظیمات اصلی:**
- Worker processes: `auto`
- Worker connections: `4096`
- Event loop: `epoll`
- GZIP: فعال
- Logging: بهینه شده

### 2. `nginx/nginx.conf` (Site Config)
**قابلیت‌ها:**
- ✅ Rate limiting (Auth: 3/s, Admin: 5/s, API: 10/s)
- ✅ GZIP compression (CSS, JS, JSON)
- ✅ Static files caching (30 days)
- ✅ Media files caching (7 days)
- ✅ WebSocket support (`/ws/`)
- ✅ Proxy buffering
- ✅ Security headers
- ✅ Health check optimization

---

## 🔧 دستورات مفید

### مدیریت Containers

```bash
# شروع همه services
docker-compose -f docker-compose.prod.yaml up -d

# توقف همه services
docker-compose -f docker-compose.prod.yaml down

# Rebuild یک service خاص
docker-compose -f docker-compose.prod.yaml up -d --build web

# مشاهده logs یک service
docker-compose -f docker-compose.prod.yaml logs -f web

# اجرای command در container
docker-compose -f docker-compose.prod.yaml exec web python manage.py shell
```

### مدیریت Django

```bash
# Migrations
docker-compose exec web python manage.py makemigrations
docker-compose exec web python manage.py migrate

# Create superuser
docker-compose exec web python manage.py createsuperuser

# Collect static files
docker-compose exec web python manage.py collectstatic --noinput

# Seed data
docker-compose exec web python manage.py seed_initial_data
docker-compose exec web python manage.py seed_sample_data

# Django shell
docker-compose exec web python manage.py shell
```

### مدیریت Database

```bash
# اتصال به PostgreSQL
docker-compose exec db2 psql -U asoud_user -d asoud_db

# Backup database
docker-compose exec db2 pg_dump -U asoud_user asoud_db > backup_$(date +%Y%m%d).sql

# Restore database
docker-compose exec -T db2 psql -U asoud_user -d asoud_db < backup.sql

# نمایش connection count
docker-compose exec db2 psql -U asoud_user -d asoud_db -c "SELECT count(*) FROM pg_stat_activity;"
```

### مدیریت NGINX

```bash
# تست configuration
docker-compose exec nginx nginx -t

# Reload NGINX (بدون downtime)
docker-compose exec nginx nginx -s reload

# مشاهده access logs
docker-compose exec nginx tail -f /var/log/nginx/access.log

# مشاهده error logs
docker-compose exec nginx tail -f /var/log/nginx/error.log
```

### مدیریت Redis

```bash
# اتصال به Redis CLI
docker-compose exec redis redis-cli -a ${REDIS_PASSWORD}

# بررسی memory usage
docker-compose exec redis redis-cli -a ${REDIS_PASSWORD} INFO memory

# Flush all data (احتیاط!)
docker-compose exec redis redis-cli -a ${REDIS_PASSWORD} FLUSHALL
```

---

## 🔍 Health Checks

### بررسی وضعیت همه services:

```bash
#!/bin/bash

echo "🏥 Health Check Report"
echo "====================="

# Django API
echo -n "Django API: "
curl -sf https://api.asoud.ir/api/v1/health/ > /dev/null && echo "✅ OK" || echo "❌ FAIL"

# NGINX
echo -n "NGINX: "
docker-compose exec nginx nginx -t > /dev/null 2>&1 && echo "✅ OK" || echo "❌ FAIL"

# PostgreSQL
echo -n "PostgreSQL: "
docker-compose exec db2 pg_isready -U asoud_user > /dev/null && echo "✅ OK" || echo "❌ FAIL"

# Redis
echo -n "Redis: "
docker-compose exec redis redis-cli -a ${REDIS_PASSWORD} ping > /dev/null && echo "✅ OK" || echo "❌ FAIL"

# Static Files
echo -n "Static Files: "
curl -sf https://api.asoud.ir/static/admin/css/base.css > /dev/null && echo "✅ OK" || echo "❌ FAIL"

echo "====================="
```

---

## 🐛 رفع مشکلات (Troubleshooting)

### 1. Container Start نمی‌شود

```bash
# بررسی logs
docker-compose logs web

# بررسی resource usage
docker stats

# حذف کامل و راه‌اندازی مجدد
docker-compose down -v
docker-compose up -d --build
```

### 2. NGINX خطای 502 Bad Gateway می‌دهد

```bash
# بررسی Django در حال اجرا است؟
docker-compose ps web

# بررسی network connectivity
docker-compose exec nginx ping -c 3 asoud_api

# بررسی NGINX logs
docker-compose logs nginx | grep error
```

### 3. Static Files load نمی‌شوند

```bash
# Collect static files مجدد
docker-compose exec web python manage.py collectstatic --noinput

# بررسی volume mounting
docker-compose exec nginx ls -la /asoud/static/

# بررسی permissions
docker-compose exec web ls -la /asoud/static/
```

### 4. Database connection error

```bash
# بررسی PostgreSQL در حال اجرا است؟
docker-compose ps db2

# بررسی environment variables
docker-compose exec web env | grep DATABASE

# تست اتصال
docker-compose exec web python manage.py dbshell
```

### 5. Redis connection error

```bash
# بررسی Redis
docker-compose exec redis redis-cli -a ${REDIS_PASSWORD} ping

# بررسی password
docker-compose exec web env | grep REDIS_PASSWORD

# بررسی network
docker-compose exec web ping -c 3 redis
```

---

## 🔒 امنیت

### Environment Variables

**هرگز commit نکنید:**
- `.env`
- `db_password`
- `redis_password`
- `secret_key`
- SSL certificates

### Firewall Rules

```bash
# فقط پورت‌های ضروری باز باشند
ufw allow 80/tcp
ufw allow 443/tcp
ufw deny 5432/tcp  # PostgreSQL نباید از خارج در دسترس باشد
ufw deny 6379/tcp  # Redis نباید از خارج در دسترس باشد
```

### SSL/TLS

Production environment با Traefik به صورت خودکار SSL certificate از Let's Encrypt دریافت می‌کند.

---

## 📊 Monitoring

### نصب Prometheus + Grafana (اختیاری)

```yaml
# اضافه کردن به docker-compose.prod.yaml:

  prometheus:
    image: prom/prometheus
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
    ports:
      - 9090:9090
    networks:
      - main_network

  grafana:
    image: grafana/grafana
    ports:
      - 3000:3000
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
    volumes:
      - grafana_data:/var/lib/grafana
    networks:
      - main_network
```

---

## 🔄 Backup Strategy

### Automatic Daily Backup Script

```bash
#!/bin/bash
# backup.sh

BACKUP_DIR="/backups"
DATE=$(date +%Y%m%d_%H%M%S)

# Database backup
docker-compose exec -T db2 pg_dump -U asoud_user asoud_db | gzip > "$BACKUP_DIR/db_$DATE.sql.gz"

# Media files backup
tar -czf "$BACKUP_DIR/media_$DATE.tar.gz" /path/to/asoud/media/

# Remove old backups (older than 7 days)
find $BACKUP_DIR -type f -mtime +7 -delete

echo "Backup completed: $DATE"
```

**افزودن به crontab:**
```bash
# Daily backup at 2 AM
0 2 * * * /path/to/backup.sh >> /var/log/asoud_backup.log 2>&1
```

---

## 🚀 Deployment Checklist

قبل از deploy production:

- [ ] `.env` file با مقادیر صحیح تنظیم شده
- [ ] `DJANGO_SECRET_KEY` تولید شده و تنظیم شده
- [ ] `DEBUG=False` در production settings
- [ ] Database credentials قوی هستند
- [ ] Redis password تنظیم شده
- [ ] SSL certificates آماده هستند
- [ ] Firewall rules تنظیم شده
- [ ] Backup strategy پیاده‌سازی شده
- [ ] Monitoring فعال است
- [ ] Health checks تست شده
- [ ] Static files collect شده
- [ ] Migrations اجرا شده
- [ ] Superuser ساخته شده
- [ ] Test data seed شده (اختیاری)

---

## 📞 پشتیبانی

در صورت بروز مشکل:

1. بررسی logs: `docker-compose logs -f`
2. بررسی container status: `docker-compose ps`
3. بررسی resource usage: `docker stats`
4. مراجعه به بخش Troubleshooting این سند

---

**نکته:** تمام تنظیمات NGINX به صورت خودکار با docker-compose اعمال می‌شوند. نیازی به تنظیمات دستی نیست! 🎉


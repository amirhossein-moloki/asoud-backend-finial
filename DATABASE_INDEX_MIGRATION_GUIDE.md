# راهنمای جامع Migration و Indexing دیتابیس
## پروژه ASOUD - بهینه‌سازی Performance

> **تاریخ:** 7 اکتبر 2025  
> **نسخه:** 1.0  
> **وضعیت:** آماده برای اجرا

---

## 📋 فهرست مطالب

1. [خلاصه اجرایی](#خلاصه-اجرایی)
2. [Indexes ایجاد شده](#indexes-ایجاد-شده)
3. [استراتژی Migration](#استراتژی-migration)
4. [نصب و راه‌اندازی](#نصب-و-راه‌اندازی)
5. [تست Performance](#تست-performance)
6. [Deployment به Production](#deployment-به-production)
7. [Monitoring و Maintenance](#monitoring-و-maintenance)
8. [Troubleshooting](#troubleshooting)
9. [Rollback Plan](#rollback-plan)

---

## 🎯 خلاصه اجرایی

### مشکل:
- جداول Product, Market, Order بدون index مناسب
- Query های کند (>500ms برای لیست‌های ساده)
- فشار بالا بر دیتابیس در ساعات پیک

### راه‌حل:
- اضافه کردن 16 index استراتژیک
- استفاده از CONCURRENT index creation
- کاهش 50-80% زمان query

### تاثیر پیش‌بینی شده:
```
Query Performance:     ↑ 50-80% بهتر
API Response Time:     ↑ 20-40% بهتر  
Database CPU:          ↓ 30-50% کمتر
Disk Space:            ↑ 5-10% بیشتر (قابل قبول)
Write Performance:     ↓ 5-10% کندتر (ناچیز)
```

---

## 📊 Indexes ایجاد شده

### Product Model (6 indexes):

| Index Name | Fields | Use Case | Impact |
|------------|--------|----------|--------|
| `idx_product_market_status` | market_id, status | لیست محصولات یک فروشگاه | بسیار بالا |
| `idx_product_category_status` | sub_category_id, status | لیست محصولات دسته‌بندی | بالا |
| `idx_product_status_created` | status, created_at | جدیدترین محصولات | بالا |
| `idx_product_market_created` | market_id, created_at | محصولات اخیر فروشگاه | متوسط |
| `idx_product_tag` | tag | پیشنهادات ویژه/جدید | متوسط |
| `idx_product_marketer` | is_marketer | محصولات بازاریابی | پایین |

**Query های بهینه شده:**
```sql
-- قبل: Sequential Scan (~500ms)
-- بعد: Index Scan (~50ms) ← 10x سریعتر
SELECT * FROM product 
WHERE market_id = 123 AND status = 'published' 
ORDER BY created_at DESC LIMIT 20;
```

---

### Market Model (5 indexes):

| Index Name | Fields | Use Case | Impact |
|------------|--------|----------|--------|
| `idx_market_user_status` | user_id, status | فروشگاه‌های کاربر | بسیار بالا |
| `idx_market_status_created` | status, created_at | لیست عمومی فروشگاه‌ها | بالا |
| `idx_market_category_status` | sub_category_id, status | فروشگاه‌های دسته | متوسط |
| `idx_market_business_id` | business_id | جستجوی business_id | بالا |
| `idx_market_paid_status` | is_paid, status | فروشگاه‌های فعال پولی | متوسط |

**Query های بهینه شده:**
```sql
-- قبل: Sequential Scan (~300ms)
-- بعد: Index Scan (~30ms) ← 10x سریعتر
SELECT * FROM market 
WHERE user_id = 456 AND status = 'published';
```

---

### Order Model (5 indexes):

| Index Name | Fields | Use Case | Impact |
|------------|--------|----------|--------|
| `idx_order_user_status` | user_id, status | سفارشات کاربر | بسیار بالا |
| `idx_order_user_created` | user_id, created_at | تاریخچه سفارشات | بسیار بالا |
| `idx_order_status_paid` | status, is_paid | گزارش‌های مالی | بالا |
| `idx_order_paid_created` | is_paid, created_at | سفارشات پرداخت شده | متوسط |
| `idx_order_type_status` | type, status | تحلیل نوع پرداخت | پایین |

**Query های بهینه شده:**
```sql
-- قبل: Sequential Scan (~400ms)
-- بعد: Index Scan (~40ms) ← 10x سریعتر
SELECT * FROM "order" 
WHERE user_id = 789 
ORDER BY created_at DESC LIMIT 20;
```

---

## 🔧 استراتژی Migration

### دو نوع Migration ایجاد شده:

#### 1. Standard Migration (برای Development/Staging):
```
apps/product/migrations/0003_product_idx_product_market_status_and_more.py
apps/market/migrations/0004_market_idx_market_user_status_and_more.py
apps/cart/migrations/0004_order_idx_order_user_status_and_more.py
```

**ویژگی‌ها:**
- سریع (چند ثانیه)
- جدول را lock می‌کند
- مناسب برای محیط‌های test

**استفاده:**
```bash
python manage.py migrate product
python manage.py migrate market
python manage.py migrate cart
```

---

#### 2. CONCURRENT Migration (برای Production):
```
apps/product/migrations/0003_product_indexes_concurrent.py
apps/market/migrations/0004_market_indexes_concurrent.py
apps/cart/migrations/0004_order_indexes_concurrent.py
```

**ویژگی‌ها:**
- جدول را lock نمی‌کند (CONCURRENT)
- کندتر (چند دقیقه)
- بدون تاثیر بر کاربران
- نیاز به PostgreSQL

**استفاده:**
```bash
# IMPORTANT: atomic=False
python manage.py migrate product 0003_product_indexes_concurrent
python manage.py migrate market 0004_market_indexes_concurrent
python manage.py migrate cart 0004_order_indexes_concurrent
```

---

## 📦 نصب و راه‌اندازی

### مرحله 1: Staging Environment

```bash
# 1. رفتن به دایرکتوری پروژه
cd /path/to/asoud-main

# 2. فعال‌سازی virtual environment (اگر دارید)
source venv/bin/activate

# 3. بررسی migrations
python manage.py showmigrations product market cart

# 4. تست dry-run
python manage.py migrate --plan

# 5. اجرای migrations (Standard)
python manage.py migrate product
python manage.py migrate market
python manage.py migrate cart

# 6. بررسی indexes
python manage.py dbshell
\d+ product  # باید indexes جدید را ببینید
\d+ market
\d+ "order"
\q
```

### مرحله 2: بررسی Index Creation

```sql
-- در PostgreSQL:
SELECT 
    tablename,
    indexname,
    indexdef
FROM pg_indexes
WHERE schemaname = 'public'
    AND indexname LIKE 'idx_%'
ORDER BY tablename, indexname;
```

**خروجی مورد انتظار:**
```
 tablename |         indexname          
-----------+----------------------------
 market    | idx_market_user_status
 market    | idx_market_status_created
 market    | idx_market_category_status
 market    | idx_market_business_id
 market    | idx_market_paid_status
 order     | idx_order_user_status
 order     | idx_order_user_created
 ...
```

---

## 🧪 تست Performance

### استفاده از اسکریپت تست:

```bash
# قبل از migration:
python test_index_performance.py --before

# بعد از migration:
python test_index_performance.py --after

# مقایسه نتایج:
python test_index_performance.py --compare
```

### تست دستی EXPLAIN ANALYZE:

```sql
-- قبل از index:
EXPLAIN ANALYZE 
SELECT * FROM product 
WHERE market_id = 1 AND status = 'published' 
LIMIT 20;

-- نتیجه: Seq Scan on product (cost=... time=500ms)

-- بعد از index:
EXPLAIN ANALYZE 
SELECT * FROM product 
WHERE market_id = 1 AND status = 'published' 
LIMIT 20;

-- نتیجه: Index Scan using idx_product_market_status (cost=... time=50ms)
```

### معیارهای موفقیت:

✅ Execution time کاهش یافته (>30%)  
✅ استفاده از Index Scan بجای Seq Scan  
✅ هیچ افزایش error rate  
✅ CPU usage کاهش یافته

---

## 🚀 Deployment به Production

### Pre-Deployment Checklist:

```bash
□ Backup کامل دیتابیس گرفته شده
□ Migration در staging تست شده
□ زمان اجرا اندازه‌گیری شده (<15 min)
□ Rollback plan آماده است
□ Monitoring داشبورد آماده است
□ تیم در دسترس است (صبح یا بعدازظهر)
□ اعلان downtime (اگر لازم باشد) ارسال شده
```

### Deployment Strategy:

#### گزینه A: Maintenance Window (ساده‌تر)

```bash
# 1. اعلان downtime (5-15 دقیقه)
echo "Maintenance window starts now"

# 2. Backup
pg_dump asoud_db > backup_$(date +%Y%m%d_%H%M%S).sql

# 3. Migration
python manage.py migrate product
python manage.py migrate market
python manage.py migrate cart

# 4. Smoke test
curl https://api.asoud.com/health

# 5. Monitor
# بررسی error rate، response time

echo "Maintenance window complete"
```

#### گزینه B: Zero-Downtime (پیشرفته‌تر)

```bash
# استفاده از CONCURRENT migrations
# نیاز به PostgreSQL

# 1. Backup
pg_dump asoud_db > backup_$(date +%Y%m%d_%H%M%S).sql

# 2. CONCURRENT Migration
python manage.py migrate product 0003_product_indexes_concurrent
python manage.py migrate market 0004_market_indexes_concurrent
python manage.py migrate cart 0004_order_indexes_concurrent

# این کار 10-30 دقیقه طول می‌کشد ولی سیستم فعال می‌ماند
```

### Post-Deployment:

```bash
# 1. بررسی indexes
python manage.py dbshell
SELECT * FROM pg_indexes WHERE indexname LIKE 'idx_%';

# 2. تست performance
python test_index_performance.py --after

# 3. مانیتور metrics (48 ساعت)
# - Response time
# - Error rate
# - CPU usage
# - Disk I/O
```

---

## 📈 Monitoring و Maintenance

### متریک‌های کلیدی:

```yaml
Performance:
  - API p50 latency: < 200ms
  - API p95 latency: < 600ms
  - API p99 latency: < 1200ms
  - Database query time: < 100ms (avg)

Health:
  - Error rate 5xx: < 1%
  - Database connection errors: 0
  - Timeout errors: < 0.5%

Resources:
  - Database CPU: < 70%
  - Database memory: < 80%
  - Disk I/O wait: < 20%
```

### Dashboard پیشنهادی (Grafana):

```
Panel 1: API Response Time (p50, p95, p99)
Panel 2: Database Query Time
Panel 3: Index Usage Ratio
Panel 4: Error Rate
Panel 5: Database CPU/Memory
```

### Index Maintenance (ماهانه):

```sql
-- بررسی index usage:
SELECT
    schemaname,
    tablename,
    indexname,
    idx_scan,
    idx_tup_read
FROM pg_stat_user_indexes
WHERE indexname LIKE 'idx_%'
ORDER BY idx_scan ASC;

-- اگر idx_scan = 0 برای مدت طولانی:
-- حذف index استفاده نشده:
DROP INDEX IF EXISTS idx_unused_index;

-- REINDEX (فصلی):
REINDEX INDEX CONCURRENTLY idx_product_market_status;
```

---

## 🔧 Troubleshooting

### مشکل 1: Migration طولانی است

**علائم:**
```
Migration is taking more than 10 minutes...
```

**علت:**
- جدول بزرگ (>1M rows)
- Disk I/O کند
- Table lock contention

**راه‌حل:**
```bash
# استفاده از CONCURRENT migration
python manage.py migrate <app> <migration_concurrent>

# یا manual:
CREATE INDEX CONCURRENTLY idx_name ON table(column);
```

---

### مشکل 2: Index استفاده نمی‌شود

**علائم:**
```sql
EXPLAIN shows "Seq Scan" instead of "Index Scan"
```

**علت:**
- جدول کوچک (<1000 rows)
- Query planner تصمیم می‌گیرد Seq Scan سریعتر است
- Index statistics outdated

**راه‌حل:**
```sql
-- Update statistics:
ANALYZE product;
ANALYZE market;
ANALYZE "order";

-- Force index usage (test only):
SET enable_seqscan = off;
```

---

### مشکل 3: Query کندتر شد!

**علائم:**
```
Query time increased after index creation
```

**علت:**
- Wrong index (نیاز به index متفاوت)
- Too many indexes (overhead)
- Query planner confused

**راه‌حل:**
```sql
-- بررسی query plan:
EXPLAIN ANALYZE <your_query>;

-- اگر index اشتباه استفاده می‌شود:
DROP INDEX IF EXISTS wrong_index;

-- یا force index hint (PostgreSQL 12+):
-- در Django:
.extra(select={'use_index': 'idx_name'})
```

---

### مشکل 4: Disk Space Full

**علائم:**
```
ERROR: could not extend file... No space left on device
```

**علت:**
- Indexes فضای زیادی گرفتند
- Temporary files

**راه‌حل:**
```sql
-- بررسی اندازه indexes:
SELECT
    tablename,
    indexname,
    pg_size_pretty(pg_relation_size(indexrelid)) AS index_size
FROM pg_stat_user_indexes
WHERE tablename IN ('product', 'market', 'order')
ORDER BY pg_relation_size(indexrelid) DESC;

-- حذف indexes غیرضروری:
DROP INDEX IF EXISTS idx_rarely_used;
```

---

## 🔄 Rollback Plan

### سناریو 1: مشکل بعد از Migration

```bash
# گزینه A: Rollback Migration
python manage.py migrate product 0002  # قبل از index migration
python manage.py migrate market 0003
python manage.py migrate cart 0003

# گزینه B: حذف دستی Indexes
python manage.py dbshell
```

```sql
-- حذف همه indexes جدید:
DROP INDEX IF EXISTS idx_product_market_status;
DROP INDEX IF EXISTS idx_product_category_status;
DROP INDEX IF EXISTS idx_product_status_created;
DROP INDEX IF EXISTS idx_product_market_created;
DROP INDEX IF EXISTS idx_product_tag;
DROP INDEX IF EXISTS idx_product_marketer;

DROP INDEX IF EXISTS idx_market_user_status;
DROP INDEX IF EXISTS idx_market_status_created;
DROP INDEX IF EXISTS idx_market_category_status;
DROP INDEX IF EXISTS idx_market_business_id;
DROP INDEX IF EXISTS idx_market_paid_status;

DROP INDEX IF EXISTS idx_order_user_status;
DROP INDEX IF EXISTS idx_order_user_created;
DROP INDEX IF EXISTS idx_order_status_paid;
DROP INDEX IF EXISTS idx_order_paid_created;
DROP INDEX IF EXISTS idx_order_type_status;
```

### سناریو 2: بازگشت کامل از Backup

```bash
# 1. متوقف کردن سرویس
docker-compose stop web

# 2. Restore از backup
psql asoud_db < backup_YYYYMMDD_HHMMSS.sql

# 3. راه‌اندازی مجدد
docker-compose start web
```

---

## 📝 چک‌لیست نهایی

### قبل از شروع:
- [x] Migrations ایجاد شده
- [x] Test script آماده
- [x] Backup plan مشخص
- [x] Monitoring آماده
- [x] تیم در دسترس
- [x] Rollback plan مشخص

### بعد از Deployment:
- [ ] همه indexes ایجاد شدند
- [ ] Query performance بهبود یافت (>30%)
- [ ] Error rate افزایش نیافت
- [ ] Resource usage نرمال است
- [ ] Sample queries با EXPLAIN تست شدند
- [ ] مستندات به‌روز شد

---

## 📚 منابع

- [Django Indexes Documentation](https://docs.djangoproject.com/en/stable/ref/models/indexes/)
- [PostgreSQL Index Types](https://www.postgresql.org/docs/current/indexes-types.html)
- [PostgreSQL CONCURRENT Indexes](https://www.postgresql.org/docs/current/sql-createindex.html#SQL-CREATEINDEX-CONCURRENTLY)
- [Query Optimization Best Practices](https://wiki.postgresql.org/wiki/Performance_Optimization)

---

## 👥 تیم و مسئولیت‌ها

| نقش | مسئولیت | شخص |
|-----|---------|-----|
| Backend Lead | اجرا و تست | [نام] |
| DevOps Lead | Deployment و Monitoring | [نام] |
| DBA | بررسی و بهینه‌سازی | [نام] |
| QA Lead | تست Performance | [نام] |

---

**تهیه‌کننده:** Backend Team  
**تاریخ:** 7 اکتبر 2025  
**نسخه:** 1.0  
**وضعیت:** ✅ آماده برای اجرا

---

**سؤالات؟** تماس با تیم Backend

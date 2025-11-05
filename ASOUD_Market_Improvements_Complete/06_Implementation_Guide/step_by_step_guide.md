# 📋 راهنمای گام به گام پیاده‌سازی اصلاحات

این راهنما به صورت مرحله به مرحله توضیح می‌دهد چگونه اصلاحات را اعمال کنید.

---

## ⚠️ هشدار مهم

**قبل از شروع:**
1. ✅ حتماً از پروژه Backup کامل بگیرید
2. ✅ در محیط Development تست کنید
3. ✅ تدریجی پیش بروید - یک تغییر، تست، بعد تغییر بعدی

---

## 🔧 مرحله 1: Backup

```bash
# ساخت Backup از پروژه
cp -r apps/market apps/market_backup
cp -r utils utils_backup

# یا با Git:
git checkout -b improvements-backup
git commit -am "Backup before improvements"
```

---

## 🔧 مرحله 2: اضافه کردن Utils

### گام 2.1: کپی فایل‌های Utils

```bash
# کپی Logging System
cp ASOUD_Market_Improvements_Complete/01_Utils/logging_config.py utils/logging_config.py

# کپی Error Handlers
cp ASOUD_Market_Improvements_Complete/01_Utils/error_handlers.py utils/error_handlers.py

# کپی Validators
cp ASOUD_Market_Improvements_Complete/01_Utils/validators.py utils/validators.py
```

### گام 2.2: تنظیم settings.py

در `settings.py` اضافه کنید:

```python
# در انتهای فایل
from utils.logging_config import setup_logging
setup_logging()

# یا در بخش LOGGING (اختیاری):
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
}
```

### گام 2.3: ساخت پوشه logs

```bash
mkdir logs
chmod 755 logs
```

---

## 🔧 مرحله 3: اعمال تغییرات Models

### گام 3.1: اضافه کردن Imports

در `apps/market/models.py`:

```python
from utils.validators import (
    validate_business_id,
    validate_iranian_national_code,
    validate_iranian_mobile_number,
    validate_postal_code,
)
```

### گام 3.2: تغییرات Market Model

```python
class Market(BaseModel):
    business_id = models.CharField(
        max_length=20,
        unique=True,  # ✅ اضافه کردن
        validators=[validate_business_id],  # ✅ اضافه کردن
        verbose_name=_('Business id'),
    )
    
    national_code = models.CharField(
        max_length=10,
        blank=True,
        null=True,
        validators=[validate_iranian_national_code],  # ✅ اضافه کردن
        verbose_name=_('National code'),
    )
```

### گام 3.3: تغییرات MarketLocation Model

```python
class MarketLocation(BaseModel):
    zip_code = models.CharField(
        max_length=15,
        validators=[validate_postal_code],  # ✅ اضافه کردن
        verbose_name=_('Zip code'),
    )
    
    latitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        blank=True,  # ✅ اضافه کردن
        null=True,   # ✅ اضافه کردن
    )
    
    longitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        blank=True,  # ✅ اضافه کردن
        null=True,   # ✅ اضافه کردن
    )
```

### گام 3.4: تغییرات MarketContact Model

```python
class MarketContact(BaseModel):
    first_mobile_number = models.CharField(
        max_length=15,
        validators=[validate_iranian_mobile_number],  # ✅ اضافه کردن
        verbose_name=_('First mobile number'),
    )
    
    second_mobile_number = models.CharField(
        max_length=15,
        blank=True,
        null=True,
        validators=[validate_iranian_mobile_number],  # ✅ اضافه کردن
        verbose_name=_('Second mobile number'),
    )
    
    email = models.EmailField(  # ✅ تغییر از CharField به EmailField
        blank=True,
        null=True,
        verbose_name=_('Email'),
    )
    
    website_url = models.URLField(  # ✅ تغییر از CharField به URLField
        blank=True,
        null=True,
        verbose_name=_('Website url'),
    )
```

### گام 3.5: Migration

```bash
python manage.py makemigrations market
python manage.py migrate
```

---

## 🔧 مرحله 4: اعمال تغییرات Views

### گام 4.1: اضافه کردن Imports

در `apps/market/views/owner_views.py`:

```python
from django.db import transaction
from django.shortcuts import get_object_or_404

from utils.logging_config import (
    log_info, log_user_action, log_error, 
    log_warning, log_security_event
)
from utils.error_handlers import (
    ErrorHandlerMixin, create_error_response, 
    handle_validation_errors, ValidationError, 
    BusinessLogicError
)
```

### گام 4.2: بهبود MarketCreateAPIView

**قبل:**
```python
class MarketCreateAPIView(views.APIView):
    def post(self, request):
        user = self.request.user
        serializer = MarketCreateSerializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            market = serializer.save(user=user)
            return Response(...)
```

**بعد:**
```python
class MarketCreateAPIView(ErrorHandlerMixin, views.APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        try:
            log_info("Market creation request", user=request.user)
            
            serializer = MarketCreateSerializer(data=request.data)
            if not serializer.is_valid():
                log_warning("Validation failed", errors=serializer.errors)
                return Response(handle_validation_errors(serializer.errors))
            
            with transaction.atomic():
                market = serializer.save(user=request.user)
                log_user_action(request.user, 'CREATE', 'Market', market.id)
            
            return Response(...)
        except Exception as e:
            log_error(e, user=request.user)
            return create_error_response(e)
```

### گام 4.3: بهبود MarketUpdateAPIView

**قبل:**
```python
class MarketUpdateAPIView(views.APIView):
    def put(self, request, pk):
        try:
            market = Market.objects.get(id=pk)
        except Market.DoesNotExist:
            return Response(...)
        # ...
```

**بعد:**
```python
class MarketUpdateAPIView(ErrorHandlerMixin, views.APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def put(self, request, pk):
        try:
            log_info("Market update request", context={'market_id': pk})
            
            # ✅ Permission Check
            try:
                market = Market.objects.get(id=pk, user=request.user)
            except Market.DoesNotExist:
                log_security_event("Unauthorized update attempt", user=request.user)
                return Response(..., status=404)
            
            serializer = MarketUpdateSerializer(market, data=request.data)
            if not serializer.is_valid():
                return Response(handle_validation_errors(serializer.errors))
            
            with transaction.atomic():
                market = serializer.save()
                log_user_action(request.user, 'UPDATE', 'Market', market.id)
            
            return Response(...)
        except Exception as e:
            log_error(e, user=request.user)
            return create_error_response(e)
```

### گام 4.4: بهبود سایر Views

از فایل `03_Views_Improvements/owner_views_improved.py` استفاده کنید.

**مهم:** یک View را تغییر دهید، تست کنید، بعد View بعدی!

---

## 🧪 مرحله 5: تست

### تست 1: Create Market

```bash
# تست ایجاد بازار
POST /market/create/
{
    "business_id": "shop123",
    "name": "فروشگاه تست",
    ...
}

# بررسی:
# ✅ Log Files: logs/market_info.log
# ✅ User Action Logged
# ✅ Transaction کار کرد
```

### تست 2: Update Market

```bash
# تست به‌روزرسانی
PUT /market/update/123/
{
    "name": "فروشگاه جدید"
}

# بررسی:
# ✅ Permission Check کار کرد
# ✅ Log Files بررسی شد
```

### تست 3: Permission Check

```bash
# تست دسترسی غیرمجاز
PUT /market/update/999/  # با User دیگری

# بررسی:
# ✅ Security Log: logs/security_events.log
# ✅ Response 404
```

### تست 4: Validators

```bash
# تست Business ID نامعتبر
POST /market/create/
{
    "business_id": "ab"  # خیلی کوتاه
}

# بررسی:
# ✅ Validation Error
# ✅ پیام واضح
```

---

## ✅ چک‌لیست نهایی

- [ ] Backup گرفته شد
- [ ] Utils اضافه شدند
- [ ] settings.py تنظیم شد
- [ ] Models بهبود یافتند
- [ ] Migrations اجرا شد
- [ ] Views بهبود یافتند
- [ ] تست Create انجام شد
- [ ] تست Update انجام شد
- [ ] تست Permission انجام شد
- [ ] تست Validators انجام شد
- [ ] Log Files بررسی شدند

---

## 🐛 عیب‌یابی

### مشکل: Import Error

```
ImportError: cannot import name 'log_info' from 'utils.logging_config'
```

**راه حل:**
```bash
# بررسی کنید که فایل کپی شده:
ls -la utils/logging_config.py

# بررسی کنید که setup_logging فراخوانی شده در settings.py
```

### مشکل: Permission Denied در Log Files

```
PermissionError: [Errno 13] Permission denied: 'logs/market_info.log'
```

**راه حل:**
```bash
chmod 755 logs
chmod 644 logs/*.log
```

### مشکل: Migration Error

```
django.db.utils.IntegrityError: ...
```

**راه حل:**
- داده‌های موجود را بررسی کنید
- ممکن است نیاز به Data Migration باشد

---

## 📞 پشتیبانی

اگر مشکلی داشتید:
1. Log Files را بررسی کنید
2. Traceback را بخوانید
3. Backup را Restore کنید

---

**موفق باشید! 🎉**


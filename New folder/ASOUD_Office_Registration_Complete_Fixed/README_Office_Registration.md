# 🏢 اصلاحات سیستم ثبت دفتر کار - ASOUD

## 📁 ساختار فولدر

```
ASOUD_Office_Registration_Fixed/
├── 01_Models/
│   ├── office_registration_models.py    # مدل‌های اصلاح شده Market
│   ├── category_models.py              # مدل‌های اصلاح شده Category
│   └── category_admin.py               # پنل ادمین اصلاح شده Category
├── 02_Serializers/
│   ├── office_registration_serializers.py  # Serializerهای Market
│   └── category_serializers.py            # Serializerهای Category
├── 03_Views/
│   ├── office_registration_views.py        # Viewهای Market
│   └── category_views.py                  # Viewهای Category
├── 04_URLs/
│   ├── office_registration_urls.py         # URLهای Market
│   ├── office_registration_new_endpoints.py # URLهای جدید Market
│   └── category_urls.py                    # URLهای Category
├── 05_Documentation/
│   └── ASOUD_Store_Registration_Documentation.html
├── README.md                              # راهنمای اصلی
└── README_Office_Registration.md          # این فایل
```

## 🎯 هدف اصلاحات

این اصلاحات برای بهبود فرآیند **ثبت دفتر کار** در سیستم ASOUD انجام شده است و شامل موارد زیر می‌باشد:

### **🔧 تغییرات اصلی:**

#### **1. مدل‌های Market (office_registration_models.py):**
- ✅ اضافه کردن فیلد `template` برای انتخاب قالب
- ✅ اضافه کردن `unique=True` به `business_id`
- ✅ اضافه کردن فیلدهای `instagram_id` و `telegram_id` جداگانه
- ✅ اضافه کردن فیلدهای `country` و `province` به `MarketLocation`
- ✅ اضافه کردن فیلدهای پرداخت و حق اشتراک
- ✅ اضافه کردن فیلد `working_hours` برای ساعت کاری

#### **2. مدل‌های Category (category_models.py):**
- ✅ اضافه کردن `MinValueValidator` و `MaxValueValidator` به فیلد `market_fee`
- ✅ بهبود validation برای حق اشتراک
- ✅ اضافه کردن help_text برای فیلدها

#### **3. پنل ادمین Category (category_admin.py):**
- ✅ اضافه کردن `market_fee` به `list_display`
- ✅ اضافه کردن فیلترها و جستجو برای `market_fee`
- ✅ ایجاد `MarketFeeAdmin` برای مدیریت بهتر حق اشتراک

#### **4. Serializerهای جدید:**
- ✅ `PaymentGatewaySerializer` برای انتخاب درگاه
- ✅ `SubscriptionFeeCalculatorSerializer` برای محاسبه حق اشتراک
- ✅ `SubscriptionPaymentSerializer` برای پرداخت حق اشتراک
- ✅ `IntegratedMarketCreateSerializer` برای ایجاد یکپارچه

#### **5. Viewهای جدید:**
- ✅ `PaymentGatewayAPIView` برای انتخاب درگاه
- ✅ `SubscriptionFeeCalculatorAPIView` برای محاسبه حق اشتراک
- ✅ `SubscriptionPaymentAPIView` برای پرداخت حق اشتراک
- ✅ `IntegratedMarketCreateAPIView` برای ایجاد یکپارچه

## 🚀 API Endpoints جدید

### **Office Registration (ثبت دفتر کار):**
```bash
# ایجاد یکپارچه دفتر کار
POST /api/v1/owner/market/integrated/create/

# انتخاب درگاه پرداخت
POST /api/v1/owner/market/payment/gateway/123/

# محاسبه حق اشتراک
POST /api/v1/owner/market/subscription/fee/calculate/

# پرداخت حق اشتراک
POST /api/v1/owner/market/subscription/payment/123/
```

### **Category Management (مدیریت دسته‌بندی):**
```bash
# به‌روزرسانی حق اشتراک
PUT /api/v1/category/market-fee/group/1/
PUT /api/v1/category/market-fee/category/1/
PUT /api/v1/category/market-fee/subcategory/1/

# لیست حق اشتراک‌ها
GET /api/v1/category/market-fee/group/
GET /api/v1/category/market-fee/category/
GET /api/v1/category/market-fee/subcategory/
```

## 🔒 Security & Validation

- ✅ اضافه کردن permission classes مناسب
- ✅ بررسی مالکیت Market
- ✅ اضافه کردن validation برای فیلدها
- ✅ اضافه کردن transaction management
- ✅ اضافه کردن error handling

## 📊 Database Changes

### **جدول Market:**
- اضافه کردن فیلد `template`
- اضافه کردن `unique=True` به `business_id`
- اضافه کردن فیلدهای پرداخت و حق اشتراک

### **جدول MarketLocation:**
- اضافه کردن فیلدهای `country` و `province`

### **جدول MarketContact:**
- اضافه کردن فیلدهای `instagram_id` و `telegram_id` جداگانه

### **جدول Group/Category/SubCategory:**
- اضافه کردن validation به `market_fee`

## 🎯 مزایای تغییرات

1. **بهبود UX:** فرآیند ثبت دفتر کار یکپارچه و ساده‌تر
2. **امنیت بیشتر:** اضافه کردن validation و permission checks
3. **مدیریت بهتر:** امکان مدیریت حق اشتراک از پنل ادمین
4. **انعطاف‌پذیری:** امکان انتخاب درگاه پرداخت مختلف
5. **قابلیت توسعه:** ساختار قابل توسعه برای ویژگی‌های آینده

## 📝 نکات مهم

- تمام تغییرات در فولدر `ASOUD_Office_Registration_Fixed` قرار دارند
- کدهای اصلی تغییر نکرده‌اند
- تمام تغییرات backward compatible هستند
- نیاز به migration برای اعمال تغییرات database
- نیاز به تنظیم URL patterns در main urls.py

## 🔄 مراحل پیاده‌سازی

### **مرحله 1: کپی کردن فایل‌ها**
```bash
# کپی مدل‌ها
cp 01_Models/office_registration_models.py apps/market/models.py
cp 01_Models/category_models.py apps/category/models.py
cp 01_Models/category_admin.py apps/category/admin.py

# کپی serializerها
cp 02_Serializers/office_registration_serializers.py apps/market/serializers.py
cp 02_Serializers/category_serializers.py apps/category/serializers.py

# کپی viewها
cp 03_Views/office_registration_views.py apps/market/views.py
cp 03_Views/category_views.py apps/category/views.py

# کپی URLها
cp 04_URLs/office_registration_urls.py apps/market/urls.py
cp 04_URLs/category_urls.py apps/category/urls.py
```

### **مرحله 2: اجرای migrations**
```bash
python manage.py makemigrations
python manage.py migrate
```

### **مرحله 3: تنظیم URL patterns**
```python
# در main urls.py
urlpatterns = [
    path('api/v1/owner/market/', include('apps.market.urls')),
    path('api/v1/category/', include('apps.category.urls')),
    # ... سایر URLها
]
```

### **مرحله 4: تست کردن**
```bash
# تست endpointهای جدید
python manage.py test apps.market
python manage.py test apps.category
```

## 📞 پشتیبانی

برای سوالات و مشکلات، با تیم توسعه تماس بگیرید.

---
**تاریخ ایجاد:** 28 اکتبر 2025  
**نسخه:** 1.0  
**وضعیت:** آماده برای پیاده‌سازی

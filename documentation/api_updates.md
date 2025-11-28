# مستندات به‌روزرسانی APIهای امن‌شده

این مستند، APIهایی را که برای افزایش امنیت و کنترل دسترسی بر اساس کاربر (`request.user`) به‌روزرسانی شده‌اند، شرح می‌دهد.

---

### 1. اپ `users`

#### `GET /api/users/banks/`

-   **ویو:** `BanksListView`
-   **فایل:** `apps/users/views/user_views.py`

**تغییرات امنیتی:**

-   **احراز هویت**: دسترسی به این API اکنون نیازمند احراز هویت است (`IsAuthenticated`). قبلاً این API برای همه قابل دسترس بود (`AllowAny`).
-   **فیلتر کردن داده‌ها**: کوئری این API اصلاح شده است تا فقط لیست اطلاعات بانکی مربوط به کاربر لاگین‌کرده را برگرداند. قبلاً لیست تمام بانک‌های سیستم برگردانده می‌شد.

**مثال کوئری امن‌شده:**

```python
user_bank_info_list = UserBankInfo.objects.filter(user=request.user)
```

---

### 2. اپ `flutter`

#### `GET /api/flutter/bank-card/<int:pk>/`

-   **ویو:** `BankCardView`
-   **فایل:** `apps/flutter/views.py`

**تغییرات امنیتی:**

-   **احراز هویت**: دسترسی به این API اکنون نیازمند احراز هویت است (`IsAuthenticated`).
-   **فیلتر کردن داده‌ها**: کوئری این API اصلاح شده است تا فقط اطلاعات کارت بانکی‌ای را برگرداند که متعلق به کاربر لاگین‌کرده باشد. این کار از طریق فیلتر کردن `queryset` بر اساس `self.request.user` انجام می‌شود.

**مثال کوئری امن‌شده:**

```python
def get_queryset(self):
    return UserBankInfo.objects.filter(user=self.request.user)
```

---

### 3. اپ `analytics`

#### `GET /api/analytics/user-analytics/`

-   **ویو:** `UserAnalyticsViewSet`
-   **فایل:** `apps/analytics/views.py`

**تغییرات امنیتی:**

-   **فیلتر کردن داده‌ها**: این API اصلاح شده است تا اگر کاربر ادمین نباشد، فقط داده‌های تحلیلی مربوط به خودش را ببیند.

**مثال کوئری امن‌شده:**

```python
def get_queryset(self):
    queryset = UserAnalytics.objects.all()
    if not self.request.user.is_staff:
        queryset = queryset.filter(user=self.request.user)
    return queryset
```

#### `GET /api/analytics/item-analytics/`

-   **ویو:** `ItemAnalyticsViewSet`
-   **فایل:** `apps/analytics/views.py`

**تغییرات امنیتی:**

-   **فیلتر کردن داده‌ها**: این API اصلاح شده است تا اگر کاربر ادمین نباشد، فقط داده‌های تحلیلی آیتم‌هایی را ببیند که مالک آن‌هاست.

**مثال کوئری امن‌شده:**

```python
def get_queryset(self):
    queryset = ItemAnalytics.objects.all()
    if not self.request.user.is_staff:
        queryset = queryset.filter(item__owner=self.request.user)
    return queryset
```

#### `GET /api/analytics/market-analytics/`

-   **ویو:** `MarketAnalyticsViewSet`
-   **فایل:** `apps/analytics/views.py`

**تغییرات امنیتی:**

-   **فیلتر کردن داده‌ها**: این API اصلاح شده است تا اگر کاربر ادمین نباشد، فقط داده‌های تحلیلی مارکت‌هایی را ببیند که مالک آن‌هاست.

**مثال کوئری امن‌شده:**

```python
def get_queryset(self):
    queryset = MarketAnalytics.objects.all()
    if not self.request.user.is_staff:
        queryset = queryset.filter(market__owner=self.request.user)
    return queryset

---

### 4. اپ `market` (بازآرایی معماری)

APIهای زیر به طور کامل بازآرایی شده‌اند تا از **لایه سرویس (Service Layer)** برای جداسازی منطق تجاری و **مدیریت خطای استاندارد** استفاده کنند.

#### `POST /api/market/owner/create/`

-   **ویو:** `MarketCreate`
-   **فایل:** `apps/market/views/owner_views.py`
-   **سرویس:** `MarketService.create_market`

**تغییرات معماری:**

-   **منطق تجاری**: تمام منطق مربوط به اعتبارسنجی و ایجاد مارکت به `MarketService` منتقل شده است.
-   **مدیریت خطا**: این API اکنون از دکوراتور `standard_error_handler` برای مدیریت یکپارچه خطاها (مانند خطاهای اعتبارسنجی یا منطقی) استفاده می‌کند.

#### `PUT /api/market/owner/update/{pk}/`

-   **ویو:** `MarketUpdate`
-   **فایل:** `apps/market/views/owner_views.py`
-   **سرویس:** `MarketService.update_market`

**تغییرات معماری:**

-   **منطق تجاری**: منطق به‌روزرسانی مارکت به `MarketService` منتقل شده و از الگوی استاندارد سریالایزر (`is_valid` و `save`) استفاده می‌کند.
-   **مدیریت خطا**: مدیریت خطاها از طریق دکوراتور `standard_error_handler` انجام می‌شود.
-   **بهبود اعتبارسنجی**: منطق اعتبارسنجی مربوط به پیکربندی درگاه پرداخت به `MarketUpdateSerializer` اضافه شد تا از ورود داده‌های نامعتبر جلوگیری شود.

---

### 5. اپ `item` (بازآرایی معماری)

مشابه اپ `market`، APIهای زیر برای استفاده از **لایه سرویس** و **مدیریت خطای استاندارد** بازآرایی شده‌اند.

#### `POST /api/item/owner/create/`

-   **ویو:** `ItemCreateAPIView`
-   **فایل:** `apps/item/views/owner_views.py`
-   **سرویس:** `ItemService.create_item`

**تغییرات معماری:**

-   **منطق تجاری**: منطق ایجاد آیتم به `ItemService` منتقل شده است.
-   **مدیریت خطا**: خطاها به صورت یکپارچه با `standard_error_handler` مدیریت می‌شوند.
-   **پاسخ API**: پاسخ این API اصلاح شد تا به جای داده‌های ورودی، شیء ساخته‌شده و سریالایزشده را برگرداند.

#### `POST /api/item/owner/discount/create/{pk}/`

-   **ویو:** `ItemDiscountCreateAPIView`
-   **فایل:** `apps/item/views/owner_views.py`
-   **سرویس:** `ItemDiscountService.create_item_discount`

**تغییرات معماری و رفع باگ:**

-   **منطق تجاری**: منطق اعمال تخفیف به `ItemDiscountService` منتقل شد.
-   **رفع باگ**: باگ مهمی که در آن منطق آپدیت قیمت آیتم پس از اعمال تخفیف حذف شده بود، برطرف گردید و این منطق به سرویس بازگردانده شد.

#### `POST /api/item/owner/shipping/create/{pk}/`

-   **ویو:** `ItemShippingCreateAPIView`
-   **فایل:** `apps/item/views/owner_views.py`
-   **سرویس:** `ItemShippingService.create_item_shipping`

**تغییرات معماری:**

-   **منطق تجاری**: منطق افزودن گزینه ارسال به آیتم، به `ItemShippingService` منتقل شد.
-   **مدیریت خطا**: مدیریت خطاها از طریق دکوراتور `standard_error_handler` انجام می‌شود.
```

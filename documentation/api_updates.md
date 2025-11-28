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
```

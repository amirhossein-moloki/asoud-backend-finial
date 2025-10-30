# ✅ چک‌لیست تحویل مستندات API به تیم فرانت

## 📋 اطلاعات اصلی

### Base URL Production
```
https://5.10.248.32
```

### Authentication
```javascript
headers: {
  'Authorization': 'Token YOUR_TOKEN_HERE',
  'Content-Type': 'application/json'
}
```

---

## 📁 فایل‌های تحویلی

### ✅ فایل اصلی (مرجع کامل)
- **فایل:** `API_DOCUMENTATION.md`
- **تعداد Endpoints:** 252 endpoint کامل
- **وضعیت:** آماده استفاده - 100% کامل
- **محتویات:**
  - همه endpoints با جزئیات کامل
  - نمونه‌های cURL برای تست
  - نمونه‌های request/response
  - توضیحات error handling
  - اطلاعات authentication
  - WebSocket endpoints
  - Rate limiting info

### ⚠️ فایل‌های قابل ایمپورت (محدود)
- **فایل:** `openapi.yaml` - فقط 6 endpoint نمونه (2.4%)
- **فایل:** `postman_collection.json` - فقط 6 request نمونه (2.4%)
- **توجه:** این دو فایل ناقص هستند و فقط برای آشنایی با ساختار هستند

---

## 🚀 شروع سریع

### ۱. نصب Token
بعد از Login موفق، token را دریافت و ذخیره کنید:
```javascript
localStorage.setItem('authToken', response.data.token);
```

### ۲. تابع کمکی برای Request
```javascript
const API_BASE_URL = 'https://5.10.248.32';

async function apiRequest(endpoint, options = {}) {
  const token = localStorage.getItem('authToken');
  
  const config = {
    method: options.method || 'GET',
    headers: {
      'Content-Type': 'application/json',
      ...(token && { 'Authorization': `Token ${token}` }),
      ...options.headers
    }
  };
  
  if (options.body) {
    config.body = JSON.stringify(options.body);
  }
  
  try {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, config);
    
    // Handle errors
    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.error?.detail || 'Request failed');
    }
    
    return await response.json();
  } catch (error) {
    console.error('API Error:', error);
    throw error;
  }
}

// نمونه استفاده
const orders = await apiRequest('/api/v1/user/order/list/');
```

### ۳. مثال Authentication
```javascript
// ارسال کد تایید
const sendCode = async (phoneNumber) => {
  return await apiRequest('/api/v1/user/pin/create/', {
    method: 'POST',
    body: { phone_number: phoneNumber }
  });
};

// تایید کد
const verifyCode = async (phoneNumber, pin) => {
  return await apiRequest('/api/v1/user/pin/verify/', {
    method: 'POST',
    body: { phone_number: phoneNumber, pin: pin }
  });
};
```

---

## 📊 بخش‌های اصلی API

| # | بخش | تعداد Endpoints | اولویت |
|---|-----|----------------|--------|
| 1 | Authentication & User Management | ~15 | 🔴 بالا |
| 2 | Market Management | ~30 | 🔴 بالا |
| 3 | Product Management | ~20 | 🔴 بالا |
| 4 | Cart & Order Management | ~15 | 🔴 بالا |
| 5 | Payment System | ~10 | 🔴 بالا |
| 6 | Chat & Support System | ~25 | 🟡 متوسط |
| 7 | Notification System | ~20 | 🟡 متوسط |
| 8 | Analytics & ML | ~20 | 🟢 پایین |
| 9 | SMS Services | ~10 | 🟢 پایین |
| 10 | Wallet System | ~15 | 🟡 متوسط |
| 11 | Affiliate System | ~10 | 🟢 پایین |
| 12 | Referral System | ~8 | 🟢 پایین |
| 13 | Price Inquiry System | ~12 | 🟡 متوسط |
| 14 | Reservation System | ~18 | 🟡 متوسط |
| 15 | Advertisement System | ~8 | 🟢 پایین |
| 16 | Comment System | ~10 | 🟡 متوسط |
| 17 | Discount System | ~8 | 🟡 متوسط |
| 18 | Category Management | ~6 | 🔴 بالا |
| 19 | Region Management | ~6 | 🔴 بالا |
| 20 | Information Services | ~8 | 🟢 پایین |

---

## ⚠️ نکات مهم

### همه URLs باید به `/` ختم شوند
```javascript
✅ صحیح: '/api/v1/user/order/list/'
❌ غلط: '/api/v1/user/order/list'
```

### Pagination
همه list endpoints:
```javascript
// Request
GET /api/v1/user/order/list/?page=2&limit=20

// Response
{
  "count": 100,
  "next": "url-to-next-page",
  "previous": "url-to-previous-page",
  "results": [...]
}
```

### Error Handling
```javascript
{
  "success": false,
  "code": 400,
  "error": {
    "code": "VALIDATION_ERROR",
    "detail": "توضیحات خطا",
    "field_errors": {
      "field_name": ["خطای فیلد"]
    }
  },
  "timestamp": "2024-01-01T00:00:00Z"
}
```

### Rate Limiting
- Anonymous: 10,000 requests/hour
- Authenticated: 50,000 requests/hour
- در صورت دریافت 429، header `Retry-After` را چک کنید

---

## 🔍 Endpoints پرکاربرد

### Authentication
```
POST /api/v1/user/pin/create/       # ارسال کد تایید
POST /api/v1/user/pin/verify/       # تایید کد
```

### Markets
```
GET  /api/v1/user/market/public/list/    # لیست مارکت‌های عمومی
GET  /api/v1/user/market/list/           # لیست مارکت‌ها (با فیلتر)
POST /api/v1/user/market/bookmark/       # نشان‌گذاری مارکت
```

### Products
```
GET  /api/v1/owner/product/list/{market_id}/  # لیست محصولات یک مارکت
GET  /api/v1/owner/product/detail/{pk}/       # جزئیات محصول
POST /api/v1/owner/product/create/            # ایجاد محصول
```

### Orders
```
POST /api/v1/user/order/add_item/            # افزودن به سبد
GET  /api/v1/user/order/orders/              # مشاهده سبد
POST /api/v1/user/order/checkout/            # تسویه حساب
POST /api/v1/user/order/create/              # ثبت سفارش
GET  /api/v1/user/order/list/                # لیست سفارشات
```

### Payments
```
POST /api/v1/user/payments/create/    # ایجاد پرداخت
GET  /api/v1/user/payments/pay/       # redirect به درگاه
POST /api/v1/user/payments/verify/    # تایید پرداخت
GET  /api/v1/user/payments/           # لیست پرداخت‌ها
```

---

## 🧪 تست سریع

### تست با cURL
```bash
# دریافت لیست مارکت‌های عمومی (بدون نیاز به token)
curl -X GET "https://5.10.248.32/api/v1/user/market/public/list/" \
  -H "Content-Type: application/json"

# دریافت لیست سفارشات (با token)
curl -X GET "https://5.10.248.32/api/v1/user/order/list/" \
  -H "Authorization: Token YOUR_TOKEN" \
  -H "Content-Type: application/json"
```

### تست در Browser Console
```javascript
// تست بدون authentication
fetch('https://5.10.248.32/api/v1/user/market/public/list/')
  .then(r => r.json())
  .then(d => console.log(d));
```

---

## 📱 WebSocket Endpoints

برای real-time features (chat, notifications):
```javascript
const ws = new WebSocket('wss://5.10.248.32/ws/chat/room-id/');

ws.onopen = () => {
  // ارسال token برای authentication
  ws.send(JSON.stringify({
    type: 'authenticate',
    token: 'YOUR_TOKEN'
  }));
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('پیام دریافت شد:', data);
};
```

---

## 📞 پشتیبانی

### سوالات متداول
1. **چطور token بگیرم؟**
   - از endpoints `/api/v1/user/pin/create/` و `/api/v1/user/pin/verify/` استفاده کنید

2. **چرا 401 می‌گیرم؟**
   - Token را در header قرار دهید: `Authorization: Token YOUR_TOKEN`

3. **چطور فایل آپلود کنم؟**
   - از `multipart/form-data` استفاده کنید و `Content-Type` را set نکنید (browser خودکار set می‌کند)

4. **Pagination چطور کار می‌کند؟**
   - از query params استفاده کنید: `?page=1&limit=20`

### منابع
- مستند کامل: `API_DOCUMENTATION.md`
- OpenAPI Spec: `openapi.yaml` (محدود)
- Postman Collection: `postman_collection.json` (محدود)

---

## ✅ چک‌لیست پیاده‌سازی

### Phase 1: Authentication (اولویت بالا)
- [ ] صفحه Login/Register با SMS
- [ ] مدیریت Token (ذخیره، حذف)
- [ ] Redirect در صورت 401
- [ ] Logout functionality

### Phase 2: Core Features (اولویت بالا)
- [ ] لیست و جزئیات Markets
- [ ] لیست و جزئیات Products
- [ ] سبد خرید (Cart)
- [ ] ثبت سفارش (Order)
- [ ] پرداخت (Payment)

### Phase 3: User Features (اولویت متوسط)
- [ ] پروفایل کاربر
- [ ] لیست سفارشات من
- [ ] Notifications
- [ ] نشان‌گذاری Markets
- [ ] کامنت‌گذاری

### Phase 4: Advanced Features (اولویت پایین)
- [ ] Chat System
- [ ] Wallet System
- [ ] Affiliate System
- [ ] Reservation System
- [ ] Analytics Dashboard

---

**آخرین بروزرسانی:** ۱۴۰۴/۰۷/۰۸
**ورژن API:** v1.0.0
**Base URL:** `https://5.10.248.32`


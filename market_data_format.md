# 📋 فرمت کامل داده‌های Market برای فرانت‌اند

## 🏪 Market UUID پیش‌فرض
```
5b293630-8df4-4c01-9f8b-e7ea3a3aea49
```

## 📝 فرمت کامل Market Data

### 1️⃣ **Market اصلی**
```json
{
  "id": "5b293630-8df4-4c01-9f8b-e7ea3a3aea49",
  "business_id": "market_001",
  "name": "بازار نمونه",
  "description": "توضیحات بازار نمونه",
  "type": "shop",
  "status": "published",
  "is_paid": true,
  "sub_category": "رستوران ایرانی",
  "sub_category_title": "رستوران ایرانی",
  "national_code": "1234567890",
  "slogan": "بهترین غذاهای ایرانی",
  "logo_img": "https://example.com/logo.jpg",
  "background_img": "https://example.com/background.jpg",
  "view_count": 150,
  "created_at": "1403/07/22"
}
```

### 2️⃣ **Market Location (موقعیت)**
```json
{
  "location": {
    "city": "70fa70b7-2347-4d10-a187-ca6925b66d06",
    "address": "خیابان ولیعصر، پلاک 123، طبقه اول",
    "zip_code": "1234567890",
    "latitude": 35.6892,
    "longitude": 51.3890
  }
}
```

### 3️⃣ **Market Contact (تماس)**
```json
{
  "contact": {
    "first_mobile_number": "09123456789",
    "second_mobile_number": "09123456790",
    "telephone": "02112345678",
    "fax": "02112345679",
    "email": "info@market.com",
    "website_url": "https://market.com",
    "messenger_ids": {
      "telegram": "@market_telegram",
      "whatsapp": "09123456789",
      "instagram": "@market_instagram"
    }
  }
}
```

### 4️⃣ **Market Schedule (ساعات کاری)**
```json
{
  "schedule": [
    {
      "day_of_week": 1,
      "day_name": "دوشنبه",
      "open_time": "09:00",
      "close_time": "21:00",
      "is_open": true
    },
    {
      "day_of_week": 2,
      "day_name": "سه‌شنبه",
      "open_time": "09:00",
      "close_time": "21:00",
      "is_open": true
    }
  ]
}
```

## 🔗 API Endpoints

### **دریافت لیست Market ها**
```
GET /api/v1/user/market/
```

### **دریافت جزئیات Market**
```
GET /api/v1/user/market/{market_uuid}/
```

### **ایجاد Market جدید**
```
POST /api/v1/owner/market/create/
```

### **ویرایش Market**
```
PUT /api/v1/owner/market/{market_uuid}/
```

## 📊 فیلدهای اجباری برای ایجاد Market

### **Market اصلی**
- `type`: "company" یا "shop"
- `business_id`: شناسه یکتا (مثل "market_001")
- `name`: نام بازار
- `sub_category`: UUID زیردسته‌بندی
- `user`: UUID کاربر (مالک)

### **Market Location**
- `city`: UUID شهر
- `address`: آدرس کامل
- `zip_code`: کد پستی
- `latitude`: عرض جغرافیایی
- `longitude`: طول جغرافیایی

### **Market Contact**
- `first_mobile_number`: شماره موبایل اصلی

## 🎯 نمونه کامل برای فرانت‌اند

```json
{
  "success": true,
  "code": 200,
  "data": {
    "id": "5b293630-8df4-4c01-9f8b-e7ea3a3aea49",
    "business_id": "market_001",
    "name": "رستوران سنتی",
    "description": "بهترین غذاهای سنتی ایرانی",
    "type": "shop",
    "status": "published",
    "is_paid": true,
    "sub_category": "3b40e9ff-1c19-416f-a853-477697f27790",
    "sub_category_title": "رستوران ایرانی",
    "national_code": "1234567890",
    "slogan": "طعم اصیل ایرانی",
    "logo_img": null,
    "background_img": null,
    "view_count": 0,
    "created_at": "1403/07/22",
    "location": {
      "city": "70fa70b7-2347-4d10-a187-ca6925b66d06",
      "address": "خیابان ولیعصر، پلاک 123",
      "zip_code": "1234567890",
      "latitude": "35.689200",
      "longitude": "51.389000"
    },
    "contact": {
      "first_mobile_number": "09123456789",
      "second_mobile_number": null,
      "telephone": "02112345678",
      "fax": null,
      "email": "info@restaurant.com",
      "website_url": null,
      "messenger_ids": {}
    }
  },
  "message": "Market retrieved successfully"
}
```

## 💡 نکات مهم

1. **UUID Format**: همه UUIDها از نوع UUID4 هستند
2. **Zip Code**: کد پستی 10 رقمی ایرانی
3. **Phone Numbers**: شماره‌های موبایل با فرمت 09123456789
4. **Coordinates**: مختصات جغرافیایی با 6 رقم اعشار
5. **Date Format**: تاریخ‌ها به شمسی و فرمت YYYY/MM/DD
6. **Status Values**: draft, queue, not_published, published, needs_editing, inactive
7. **Type Values**: company, shop

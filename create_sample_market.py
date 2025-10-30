#!/usr/bin/env python3
"""
اسکریپت ایجاد market نمونه برای فرانت‌اند
Sample Market Creator for Frontend
"""
import os
import sys
import django
import uuid
from datetime import datetime, timedelta

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
os.environ['USE_SQLITE'] = 'true'
django.setup()

from django.db import transaction
from apps.market.models import Market, MarketLocation, MarketContact, MarketSchedule
from apps.category.models import Category, SubCategory
from apps.region.models import City

print("="*60)
print("🏪 ایجاد Market نمونه برای فرانت‌اند")
print("="*60)
print()

def create_sample_market():
    """ایجاد market نمونه"""
    print("1️⃣  ایجاد Market نمونه...")
    print("-" * 40)
    
    # Get first subcategory and city
    subcategory = SubCategory.objects.first()
    city = City.objects.first()
    
    if not subcategory:
        print("❌ هیچ زیردسته‌بندی یافت نشد. ابتدا دسته‌بندی‌ها را ایجاد کنید.")
        return None
    
    if not city:
        print("❌ هیچ شهری یافت نشد. ابتدا شهرها را ایجاد کنید.")
        return None
    
    # Create sample market
    market_uuid = str(uuid.uuid4())
    business_id = f"market_{uuid.uuid4().hex[:8]}"
    
    market = Market.objects.create(
        name='بازار نمونه',
        description='توضیحات بازار نمونه برای تست فرانت‌اند',
        business_id=business_id,
        sub_category=subcategory,
        type=Market.SHOP,
        status=Market.PUBLISHED,
        is_paid=True,
        subscription_start_date=datetime.now(),
        subscription_end_date=datetime.now() + timedelta(days=365)
    )
    
    print(f"✅ Market ایجاد شد:")
    print(f"   نام: {market.name}")
    print(f"   UUID: {market.id}")
    print(f"   Business ID: {market.business_id}")
    print(f"   نوع: {market.get_type_display()}")
    print(f"   وضعیت: {market.get_status_display()}")
    
    # Create market location
    MarketLocation.objects.create(
        market=market,
        city=city,
        address=f'آدرس نمونه در {city.name}',
        latitude=35.6892,
        longitude=51.3890
    )
    print(f"   موقعیت: {city.name}")
    
    # Create market contact
    MarketContact.objects.create(
        market=market,
        phone='09123456789',
        email='sample@example.com'
    )
    print(f"   تماس: 09123456789")
    
    # Create market schedule
    MarketSchedule.objects.create(
        market=market,
        day_of_week=1,  # Monday
        open_time='09:00',
        close_time='21:00',
        is_open=True
    )
    print(f"   ساعات کاری: 09:00 - 21:00")
    
    return market

def main():
    """اجرای اصلی"""
    try:
        with transaction.atomic():
            market = create_sample_market()
        
        if market:
            print()
            print("="*60)
            print("🎉 Market نمونه با موفقیت ایجاد شد!")
            print("="*60)
            
            print()
            print("📋 اطلاعات برای فرانت‌اند:")
            print(f"Market UUID: {market.id}")
            print(f"Business ID: {market.business_id}")
            print(f"Market Name: {market.name}")
            
            print()
            print("🔗 API Endpoints:")
            print(f"GET /api/v1/user/market/{market.id}/")
            print(f"GET /api/v1/owner/market/{market.id}/")
            
            print()
            print("📝 JSON Response Format:")
            print("{")
            print(f'  "id": "{market.id}",')
            print(f'  "name": "{market.name}",')
            print(f'  "business_id": "{market.business_id}",')
            print(f'  "description": "{market.description}",')
            print(f'  "type": "{market.type}",')
            print(f'  "status": "{market.status}"')
            print("}")
        
    except Exception as e:
        print(f"❌ خطا در ایجاد Market: {e}")

if __name__ == "__main__":
    main()

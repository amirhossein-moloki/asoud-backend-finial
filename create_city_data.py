#!/usr/bin/env python3
"""
اسکریپت ساده برای ایجاد داده‌های شهرها
Simple script to create city data
"""
import os
import sys
import django
import uuid

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')

# Disable logging to avoid permission issues
import logging
logging.disable(logging.CRITICAL)

django.setup()

from apps.region.models import Country, Province, City

print("=== Creating City Data ===")

# Create Iran country
country, created = Country.objects.get_or_create(name='ایران')
print(f"Country: {country.name} (ID: {country.id})")

# Sample provinces and cities
iran_provinces = {
    'تهران': ['تهران', 'کرج', 'ورامین', 'دماوند', 'رودهن', 'شهریار', 'اسلامشهر', 'پاکدشت'],
    'اصفهان': ['اصفهان', 'کاشان', 'نجف‌آباد', 'خمینی‌شهر', 'شاهین‌شهر', 'فلاورجان'],
    'فارس': ['شیراز', 'مرودشت', 'جهرم', 'کازرون', 'لار', 'آباده'],
    'خراسان رضوی': ['مشهد', 'نیشابور', 'سبزوار', 'قوچان', 'کاشمر', 'تربت حیدریه'],
    'آذربایجان شرقی': ['تبریز', 'مراغه', 'مرند', 'میانه', 'سراب', 'بناب'],
    'خوزستان': ['اهواز', 'دزفول', 'آبادان', 'خرمشهر', 'اندیمشک', 'شوشتر'],
    'مازندران': ['ساری', 'بابل', 'آمل', 'قائم‌شهر', 'بابلسر', 'نوشهر', 'چالوس'],
    'گیلان': ['رشت', 'انزلی', 'لاهیجان', 'لنگرود', 'رودسر', 'آستارا'],
    'کرمان': ['کرمان', 'رفسنجان', 'سیرجان', 'زرند', 'بم', 'جیرفت'],
    'یزد': ['یزد', 'میبد', 'اردکان', 'بافق', 'مهریز', 'ابرکوه'],
}

total_cities = 0
for prov_name, cities in iran_provinces.items():
    province, created = Province.objects.get_or_create(
        name=prov_name,
        country=country
    )
    print(f"Province: {prov_name} (ID: {province.id})")
    
    for city_name in cities:
        city, created = City.objects.get_or_create(
            name=city_name,
            province=province
        )
        total_cities += 1
        print(f"  City: {city_name} (ID: {city.id})")

print(f"\nTotal: {Province.objects.count()} provinces, {total_cities} cities")

# Show sample data
print("\n=== Sample City UUIDs ===")
cities = City.objects.select_related('province', 'province__country').all()[:10]
for city in cities:
    print(f"City: {city.name}")
    print(f"UUID: {city.id}")
    print(f"Province: {city.province.name}")
    print(f"Country: {city.province.country.name}")
    print("---")

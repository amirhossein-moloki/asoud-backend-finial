"""
اصلاحات Model Market
اضافه کردن Validators به Model Level و بهبود ساختار
"""

# این فایل نشان می‌دهد چه تغییراتی باید در apps/market/models.py اعمال شود

"""
📝 تغییرات لازم در Market Model:

1. اضافه کردن Validators به business_id:
   business_id = models.CharField(
       max_length=20,
       unique=True,  # ✅ اضافه کردن unique=True
       validators=[validate_business_id],  # ✅ اضافه کردن validator
       ...
   )

2. اضافه کردن Validator به national_code:
   national_code = models.CharField(
       max_length=10,
       blank=True,
       null=True,
       validators=[validate_iranian_national_code],  # ✅ اضافه کردن validator
       ...
   )

3. اضافه کردن فیلد working_hours (اختیاری):
   working_hours = models.JSONField(
       blank=True,
       null=True,
       validators=[validate_working_hours],  # ✅ اگر لازم است
       verbose_name=_('Working Hours'),
   )

📝 تغییرات لازم در MarketLocation Model:

1. اضافه کردن Validator به zip_code:
   zip_code = models.CharField(
       max_length=15,
       validators=[validate_postal_code],  # ✅ اضافه کردن validator
       ...
   )

2. بهبود latitude/longitude (اختیاری کردن):
   latitude = models.DecimalField(
       max_digits=9,
       decimal_places=6,
       blank=True,  # ✅ اضافه کردن blank=True
       null=True,   # ✅ اضافه کردن null=True
   )

📝 تغییرات لازم در MarketContact Model:

1. اضافه کردن Validators به شماره موبایل:
   first_mobile_number = models.CharField(
       max_length=15,
       validators=[validate_iranian_mobile_number],  # ✅ اضافه کردن validator
       ...
   )
   
   second_mobile_number = models.CharField(
       max_length=15,
       blank=True,
       null=True,
       validators=[validate_iranian_mobile_number],  # ✅ اضافه کردن validator
       ...
   )

2. تغییر Email Field:
   email = models.EmailField(  # ✅ تغییر از CharField به EmailField
       blank=True,
       null=True,
       ...
   )

3. تغییر Website Field:
   website_url = models.URLField(  # ✅ تغییر از CharField به URLField
       blank=True,
       null=True,
       ...
   )
"""

# Import لازم در apps/market/models.py:
"""
from utils.validators import (
    validate_business_id,
    validate_iranian_national_code,
    validate_iranian_mobile_number,
    validate_postal_code,
    validate_working_hours
)
"""


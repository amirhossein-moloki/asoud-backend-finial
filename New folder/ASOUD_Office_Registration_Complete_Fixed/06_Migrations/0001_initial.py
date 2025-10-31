# Generated migration for ASOUD Office Registration models

from django.db import migrations, models
import django.db.models.deletion
from django.conf import settings
import django.utils.timezone
from ..validators import (
    validate_business_id,
    validate_iranian_national_code,
    validate_iranian_mobile_number,
    validate_postal_code,
    validate_working_hours,
    validate_instagram_id,
    validate_telegram_id,
)


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('category', '0001_initial'),  # Assuming category app exists
    ]

    operations = [
        migrations.CreateModel(
            name='Market',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Created at')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Updated at')),
                ('is_active', models.BooleanField(default=True, verbose_name='Is active')),
                ('market_name', models.CharField(max_length=100, verbose_name='Market name')),
                ('business_id', models.CharField(
                    help_text='Unique business identifier (5-20 characters, English letters and numbers only)',
                    max_length=20,
                    unique=True,
                    validators=[validate_business_id],
                    verbose_name='Business ID'
                )),
                ('national_code', models.CharField(
                    blank=True,
                    help_text='Iranian national code (10 digits)',
                    max_length=10,
                    null=True,
                    validators=[validate_iranian_national_code],
                    verbose_name='National code'
                )),
                ('market_type', models.CharField(
                    choices=[('individual', 'Individual'), ('company', 'Company')],
                    default='individual',
                    max_length=20,
                    verbose_name='Market type'
                )),
                ('status', models.CharField(
                    choices=[
                        ('pending', 'Pending'),
                        ('active', 'Active'),
                        ('inactive', 'Inactive'),
                        ('suspended', 'Suspended')
                    ],
                    default='pending',
                    max_length=20,
                    verbose_name='Status'
                )),
                ('subscription_start_date', models.DateTimeField(blank=True, null=True, verbose_name='Subscription start date')),
                ('subscription_end_date', models.DateTimeField(blank=True, null=True, verbose_name='Subscription end date')),
                ('payment_gateway_type', models.CharField(
                    blank=True,
                    choices=[('zarinpal', 'ZarinPal'), ('mellat', 'Mellat'), ('personal', 'Personal')],
                    max_length=20,
                    null=True,
                    verbose_name='Payment gateway type'
                )),
                ('payment_gateway_key', models.CharField(blank=True, max_length=255, null=True, verbose_name='Payment gateway key')),
                ('working_hours', models.JSONField(
                    blank=True,
                    help_text='Weekly working schedule in JSON format',
                    null=True,
                    validators=[validate_working_hours],
                    verbose_name='Working hours'
                )),
                ('user', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='markets',
                    to=settings.AUTH_USER_MODEL,
                    verbose_name='User'
                )),
                ('sub_category', models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='markets',
                    to='category.subcategory',
                    verbose_name='Sub category'
                )),
            ],
            options={
                'verbose_name': 'Market',
                'verbose_name_plural': 'Markets',
                'db_table': 'market',
            },
        ),
        migrations.CreateModel(
            name='MarketLocation',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Created at')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Updated at')),
                ('is_active', models.BooleanField(default=True, verbose_name='Is active')),
                ('province', models.CharField(max_length=50, verbose_name='Province')),
                ('city', models.CharField(max_length=50, verbose_name='City')),
                ('address', models.TextField(verbose_name='Address')),
                ('zip_code', models.CharField(
                    blank=True,
                    max_length=10,
                    null=True,
                    validators=[validate_postal_code],
                    verbose_name='Zip code'
                )),
                ('latitude', models.DecimalField(blank=True, decimal_places=6, max_digits=9, null=True, verbose_name='Latitude')),
                ('longitude', models.DecimalField(blank=True, decimal_places=6, max_digits=9, null=True, verbose_name='Longitude')),
                ('market', models.OneToOneField(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='location',
                    to='office_registration.market',
                    verbose_name='Market'
                )),
            ],
            options={
                'verbose_name': 'Market Location',
                'verbose_name_plural': 'Market Locations',
                'db_table': 'market_location',
            },
        ),
        migrations.CreateModel(
            name='MarketContact',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Created at')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Updated at')),
                ('is_active', models.BooleanField(default=True, verbose_name='Is active')),
                ('first_mobile_number', models.CharField(
                    max_length=11,
                    validators=[validate_iranian_mobile_number],
                    verbose_name='First mobile number'
                )),
                ('second_mobile_number', models.CharField(
                    blank=True,
                    max_length=11,
                    null=True,
                    validators=[validate_iranian_mobile_number],
                    verbose_name='Second mobile number'
                )),
                ('landline_number', models.CharField(blank=True, max_length=15, null=True, verbose_name='Landline number')),
                ('email', models.EmailField(blank=True, max_length=254, null=True, verbose_name='Email')),
                ('website', models.URLField(blank=True, null=True, verbose_name='Website')),
                ('instagram_id', models.CharField(
                    blank=True,
                    max_length=30,
                    null=True,
                    validators=[validate_instagram_id],
                    verbose_name='Instagram ID'
                )),
                ('telegram_id', models.CharField(
                    blank=True,
                    max_length=32,
                    null=True,
                    validators=[validate_telegram_id],
                    verbose_name='Telegram ID'
                )),
                ('market', models.OneToOneField(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='contact',
                    to='office_registration.market',
                    verbose_name='Market'
                )),
            ],
            options={
                'verbose_name': 'Market Contact',
                'verbose_name_plural': 'Market Contacts',
                'db_table': 'market_contact',
            },
        ),
        migrations.CreateModel(
            name='MarketSchedule',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Created at')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Updated at')),
                ('is_active', models.BooleanField(default=True, verbose_name='Is active')),
                ('day_of_week', models.CharField(
                    choices=[
                        ('saturday', 'Saturday'),
                        ('sunday', 'Sunday'),
                        ('monday', 'Monday'),
                        ('tuesday', 'Tuesday'),
                        ('wednesday', 'Wednesday'),
                        ('thursday', 'Thursday'),
                        ('friday', 'Friday')
                    ],
                    max_length=10,
                    verbose_name='Day of week'
                )),
                ('start_time', models.TimeField(verbose_name='Start time')),
                ('end_time', models.TimeField(verbose_name='End time')),
                ('is_working', models.BooleanField(default=True, verbose_name='Is working')),
                ('market', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='schedules',
                    to='office_registration.market',
                    verbose_name='Market'
                )),
            ],
            options={
                'verbose_name': 'Market Schedule',
                'verbose_name_plural': 'Market Schedules',
                'db_table': 'market_schedule',
                'unique_together': {('market', 'day_of_week')},
            },
        ),
        migrations.CreateModel(
            name='PaymentRequest',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Created at')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Updated at')),
                ('is_active', models.BooleanField(default=True, verbose_name='Is active')),
                ('amount', models.DecimalField(decimal_places=2, max_digits=15, verbose_name='Amount')),
                ('status', models.CharField(
                    choices=[
                        ('pending', 'Pending'),
                        ('completed', 'Completed'),
                        ('failed', 'Failed'),
                        ('cancelled', 'Cancelled')
                    ],
                    default='pending',
                    max_length=20,
                    verbose_name='Status'
                )),
                ('gateway_type', models.CharField(
                    choices=[('zarinpal', 'ZarinPal'), ('mellat', 'Mellat'), ('wallet', 'Wallet')],
                    max_length=20,
                    verbose_name='Gateway type'
                )),
                ('transaction_id', models.CharField(blank=True, max_length=100, null=True, verbose_name='Transaction ID')),
                ('gateway_url', models.URLField(blank=True, null=True, verbose_name='Gateway URL')),
                ('discount_amount', models.DecimalField(decimal_places=2, default=0, max_digits=15, verbose_name='Discount amount')),
                ('final_amount', models.DecimalField(decimal_places=2, max_digits=15, verbose_name='Final amount')),
                ('market', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='payment_requests',
                    to='office_registration.market',
                    verbose_name='Market'
                )),
            ],
            options={
                'verbose_name': 'Payment Request',
                'verbose_name_plural': 'Payment Requests',
                'db_table': 'payment_request',
            },
        ),
    ]
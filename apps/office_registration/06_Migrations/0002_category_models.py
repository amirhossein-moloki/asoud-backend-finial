# Generated migration for Category models with market fee validation

from django.db import migrations, models
import django.db.models.deletion
from ..validators import validate_market_fee


class Migration(migrations.Migration):

    dependencies = [
        ('office_registration', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Group',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Created at')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Updated at')),
                ('is_active', models.BooleanField(default=True, verbose_name='Is active')),
                ('name', models.CharField(max_length=100, verbose_name='Group name')),
                ('description', models.TextField(blank=True, null=True, verbose_name='Description')),
                ('market_fee', models.DecimalField(
                    decimal_places=2,
                    default=0,
                    help_text='Fee for this group in the market',
                    max_digits=15,
                    validators=[validate_market_fee],
                    verbose_name='Market fee'
                )),
                ('market_slider_img', models.ImageField(
                    blank=True,
                    null=True,
                    upload_to='group_sliders/',
                    verbose_name='Market slider image'
                )),
                ('market_slider_url', models.URLField(
                    blank=True,
                    null=True,
                    verbose_name='Market slider URL'
                )),
            ],
            options={
                'verbose_name': 'Group',
                'verbose_name_plural': 'Groups',
                'db_table': 'group',
            },
        ),
        migrations.CreateModel(
            name='Category',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Created at')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Updated at')),
                ('is_active', models.BooleanField(default=True, verbose_name='Is active')),
                ('name', models.CharField(max_length=100, verbose_name='Category name')),
                ('description', models.TextField(blank=True, null=True, verbose_name='Description')),
                ('market_fee', models.DecimalField(
                    decimal_places=2,
                    default=0,
                    help_text='Fee for this category in the market',
                    max_digits=15,
                    validators=[validate_market_fee],
                    verbose_name='Market fee'
                )),
                ('market_slider_img', models.ImageField(
                    blank=True,
                    null=True,
                    upload_to='category_sliders/',
                    verbose_name='Market slider image'
                )),
                ('market_slider_url', models.URLField(
                    blank=True,
                    null=True,
                    verbose_name='Market slider URL'
                )),
                ('group', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='categories',
                    to='office_registration.group',
                    verbose_name='Group'
                )),
            ],
            options={
                'verbose_name': 'Category',
                'verbose_name_plural': 'Categories',
                'db_table': 'category',
            },
        ),
        migrations.CreateModel(
            name='SubCategory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Created at')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Updated at')),
                ('is_active', models.BooleanField(default=True, verbose_name='Is active')),
                ('name', models.CharField(max_length=100, verbose_name='SubCategory name')),
                ('description', models.TextField(blank=True, null=True, verbose_name='Description')),
                ('market_fee', models.DecimalField(
                    decimal_places=2,
                    default=0,
                    help_text='Fee for this subcategory in the market',
                    max_digits=15,
                    validators=[validate_market_fee],
                    verbose_name='Market fee'
                )),
                ('market_slider_img', models.ImageField(
                    blank=True,
                    null=True,
                    upload_to='subcategory_sliders/',
                    verbose_name='Market slider image'
                )),
                ('market_slider_url', models.URLField(
                    blank=True,
                    null=True,
                    verbose_name='Market slider URL'
                )),
                ('category', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='subcategories',
                    to='office_registration.category',
                    verbose_name='Category'
                )),
            ],
            options={
                'verbose_name': 'SubCategory',
                'verbose_name_plural': 'SubCategories',
                'db_table': 'subcategory',
            },
        ),
        migrations.CreateModel(
            name='ProductGroup',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Created at')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Updated at')),
                ('is_active', models.BooleanField(default=True, verbose_name='Is active')),
                ('name', models.CharField(max_length=100, verbose_name='Product group name')),
                ('description', models.TextField(blank=True, null=True, verbose_name='Description')),
                ('group', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='product_groups',
                    to='office_registration.group',
                    verbose_name='Group'
                )),
            ],
            options={
                'verbose_name': 'Product Group',
                'verbose_name_plural': 'Product Groups',
                'db_table': 'product_group',
            },
        ),
        migrations.CreateModel(
            name='ProductCategory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Created at')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Updated at')),
                ('is_active', models.BooleanField(default=True, verbose_name='Is active')),
                ('name', models.CharField(max_length=100, verbose_name='Product category name')),
                ('description', models.TextField(blank=True, null=True, verbose_name='Description')),
                ('product_group', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='product_categories',
                    to='office_registration.productgroup',
                    verbose_name='Product Group'
                )),
            ],
            options={
                'verbose_name': 'Product Category',
                'verbose_name_plural': 'Product Categories',
                'db_table': 'product_category',
            },
        ),
        migrations.CreateModel(
            name='ProductSubCategory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Created at')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Updated at')),
                ('is_active', models.BooleanField(default=True, verbose_name='Is active')),
                ('name', models.CharField(max_length=100, verbose_name='Product subcategory name')),
                ('description', models.TextField(blank=True, null=True, verbose_name='Description')),
                ('product_category', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='product_subcategories',
                    to='office_registration.productcategory',
                    verbose_name='Product Category'
                )),
            ],
            options={
                'verbose_name': 'Product SubCategory',
                'verbose_name_plural': 'Product SubCategories',
                'db_table': 'product_subcategory',
            },
        ),
    ]
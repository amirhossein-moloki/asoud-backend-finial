"""
Management command to generate advanced analytics data
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta, datetime
import random
import json

from apps.analytics.models import UserBehaviorEvent, UserSession, ProductAnalytics, UserAnalytics
from apps.analytics.advanced_analytics import SalesAnalytics, BusinessIntelligence

User = get_user_model()


class Command(BaseCommand):
    help = 'Generate advanced analytics data for testing'

    def add_arguments(self, parser):
        parser.add_argument(
            '--users',
            type=int,
            default=500,
            help='Number of users to generate data for'
        )
        parser.add_argument(
            '--days',
            type=int,
            default=90,
            help='Number of days to generate data for'
        )
        parser.add_argument(
            '--products',
            type=int,
            default=100,
            help='Number of products to generate data for'
        )
        parser.add_argument(
            '--orders-per-day',
            type=int,
            default=50,
            help='Average number of orders per day'
        )

    def handle(self, *args, **options):
        users_count = options['users']
        days = options['days']
        products_count = options['products']
        orders_per_day = options['orders_per_day']
        
        self.stdout.write(self.style.SUCCESS('Starting advanced analytics data generation...'))
        
        # Generate users and products
        users = self.generate_users(users_count)
        products = self.generate_products(products_count)
        
        # Generate sales data
        self.generate_sales_data(users, products, days, orders_per_day)
        
        # Generate analytics
        self.generate_analytics()
        
        # Test advanced analytics
        self.test_advanced_analytics()
        
        self.stdout.write(self.style.SUCCESS('Advanced analytics data generation completed!'))

    def generate_users(self, count):
        """Generate users for analytics"""
        self.stdout.write('Generating users...')
        
        users = []
        for i in range(count):
            username = f'analytics_user_{i+1}'
            email = f'analytics_user_{i+1}@example.com'
            
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    'email': email,
                    'first_name': f'Analytics User {i+1}',
                    'last_name': 'Test',
                    'is_active': True
                }
            )
            
            if created:
                # Create UserAnalytics for new user
                UserAnalytics.objects.get_or_create(user=user)
            
            users.append(user)
        
        self.stdout.write(self.style.SUCCESS(f'Generated {len(users)} users'))
        return users

    def generate_products(self, count):
        """Generate products for analytics"""
        self.stdout.write('Generating products...')
        
        products = []
        for i in range(count):
            product_id = i + 1
            
            # Create ProductAnalytics
            product_analytics, created = ProductAnalytics.objects.get_or_create(
                product_id=product_id,
                defaults={
                    'total_views': random.randint(0, 1000),
                    'unique_views': random.randint(0, 500),
                    'total_clicks': random.randint(0, 100),
                    'add_to_cart_count': random.randint(0, 50),
                    'total_purchases': random.randint(0, 25),
                    'revenue': random.uniform(0, 5000),
                    'popularity_score': random.uniform(0, 100),
                    'trending_score': random.uniform(0, 100)
                }
            )
            
            products.append(product_analytics)
        
        self.stdout.write(self.style.SUCCESS(f'Generated {len(products)} products'))
        return products

    def generate_sales_data(self, users, products, days, orders_per_day):
        """Generate sales data for analytics"""
        self.stdout.write('Generating sales data...')
        
        start_date = timezone.now() - timedelta(days=days)
        
        total_orders = 0
        for day in range(days):
            current_date = start_date + timedelta(days=day)
            
            # Generate orders for this day
            daily_orders = random.randint(orders_per_day // 2, orders_per_day * 2)
            
            for order in range(daily_orders):
                # Select random user and product
                user = random.choice(users)
                product = random.choice(products)
                
                # Generate order value
                order_value = random.uniform(10, 1000)
                
                # Create purchase event
                UserBehaviorEvent.objects.create(
                    user=user,
                    session_id=f'session_{user.id}_{day}_{order}',
                    event_type='purchase',
                    object_id=product.product_id,
                    event_data={
                        'value': order_value,
                        'currency': 'IRR',
                        'product_id': product.product_id
                    },
                    page_url='https://asoud.com/checkout',
                    referrer_url='https://asoud.com/cart',
                    user_agent=f'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                    ip_address=f'192.168.1.{random.randint(1, 254)}',
                    device_type=random.choice(['desktop', 'mobile', 'tablet']),
                    browser=random.choice(['Chrome', 'Firefox', 'Safari', 'Edge']),
                    os=random.choice(['Windows', 'macOS', 'Linux', 'iOS', 'Android']),
                    country=random.choice(['Iran', 'Turkey', 'UAE', 'Germany', 'USA']),
                    city=random.choice(['Tehran', 'Istanbul', 'Dubai', 'Berlin', 'New York']),
                    latitude=random.uniform(25, 40),
                    longitude=random.uniform(44, 60),
                    timestamp=current_date + timedelta(
                        hours=random.randint(0, 23),
                        minutes=random.randint(0, 59)
                    )
                )
                
                total_orders += 1
                
                if total_orders % 100 == 0:
                    self.stdout.write(f'Generated {total_orders} orders...')
        
        self.stdout.write(self.style.SUCCESS(f'Generated {total_orders} total orders'))

    def generate_analytics(self):
        """Generate analytics for all entities"""
        self.stdout.write('Generating analytics...')
        
        # Calculate user analytics
        for user_analytics in UserAnalytics.objects.all():
            try:
                user_analytics.calculate_metrics()
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Error calculating user analytics: {e}'))
        
        # Calculate product analytics
        for product_analytics in ProductAnalytics.objects.all():
            try:
                product_analytics.calculate_metrics()
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Error calculating product analytics: {e}'))
        
        self.stdout.write(self.style.SUCCESS('Analytics calculated'))

    def test_advanced_analytics(self):
        """Test advanced analytics functionality"""
        self.stdout.write('Testing advanced analytics...')
        
        try:
            # Test Sales Analytics
            sales_analytics = SalesAnalytics()
            
            # Test sales overview
            sales_overview = sales_analytics.get_sales_overview(30)
            self.stdout.write(f'Sales Overview - Total Revenue: {sales_overview["total_revenue"]}')
            
            # Test revenue analytics
            revenue_analytics = sales_analytics.get_revenue_analytics(30)
            self.stdout.write(f'Revenue Analytics - Total Revenue: {revenue_analytics["total_revenue"]}')
            
            # Test customer analytics
            customer_analytics = sales_analytics.get_customer_analytics(30)
            self.stdout.write(f'Customer Analytics - Total Customers: {customer_analytics["total_customers"]}')
            
            # Test product analytics
            product_analytics = sales_analytics.get_product_analytics(30)
            self.stdout.write(f'Product Analytics - Total Products: {product_analytics["total_products"]}')
            
            # Test Business Intelligence
            bi = BusinessIntelligence()
            kpi_dashboard = bi.get_kpi_dashboard(30)
            
            kpis = kpi_dashboard.get('kpis', {})
            insights = kpi_dashboard.get('insights', [])
            
            self.stdout.write(f'KPI Dashboard - Revenue: {kpis.get("revenue", {}).get("current", 0)}')
            self.stdout.write(f'Business Insights - Count: {len(insights)}')
            
            self.stdout.write(self.style.SUCCESS('Advanced analytics testing completed successfully'))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error testing advanced analytics: {e}'))


"""
Management command to generate sample analytics data
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta, datetime
import random
import json

from apps.analytics.models import UserBehaviorEvent, UserSession, ProductAnalytics, UserAnalytics
from apps.analytics.signals import track_user_behavior

User = get_user_model()


class Command(BaseCommand):
    help = 'Generate sample analytics data for testing'

    def add_arguments(self, parser):
        parser.add_argument(
            '--users',
            type=int,
            default=100,
            help='Number of users to generate data for'
        )
        parser.add_argument(
            '--days',
            type=int,
            default=30,
            help='Number of days to generate data for'
        )
        parser.add_argument(
            '--events-per-user',
            type=int,
            default=50,
            help='Average number of events per user per day'
        )

    def handle(self, *args, **options):
        users_count = options['users']
        days = options['days']
        events_per_user = options['events_per_user']
        
        self.stdout.write(self.style.SUCCESS('Starting analytics data generation...'))
        
        # Get or create users
        users = self.get_or_create_users(users_count)
        
        # Generate sessions and events
        self.generate_sessions_and_events(users, days, events_per_user)
        
        # Calculate analytics
        self.calculate_analytics()
        
        self.stdout.write(self.style.SUCCESS('Analytics data generation completed!'))

    def get_or_create_users(self, count):
        """Get or create users for data generation"""
        self.stdout.write('Creating users...')
        
        users = []
        for i in range(count):
            username = f'test_user_{i+1}'
            email = f'test_user_{i+1}@example.com'
            
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    'email': email,
                    'first_name': f'Test User {i+1}',
                    'last_name': 'Analytics',
                    'is_active': True
                }
            )
            
            if created:
                # Create UserAnalytics for new user
                UserAnalytics.objects.get_or_create(user=user)
            
            users.append(user)
        
        self.stdout.write(self.style.SUCCESS(f'Created/retrieved {len(users)} users'))
        return users

    def generate_sessions_and_events(self, users, days, events_per_user):
        """Generate sessions and events for users"""
        self.stdout.write('Generating sessions and events...')
        
        event_types = [
            'page_view', 'product_view', 'add_to_cart', 'remove_from_cart',
            'search', 'filter', 'sort', 'purchase', 'review', 'share'
        ]
        
        device_types = ['desktop', 'mobile', 'tablet']
        browsers = ['Chrome', 'Firefox', 'Safari', 'Edge']
        operating_systems = ['Windows', 'macOS', 'Linux', 'iOS', 'Android']
        countries = ['Iran', 'Turkey', 'UAE', 'Germany', 'USA']
        cities = ['Tehran', 'Istanbul', 'Dubai', 'Berlin', 'New York']
        
        start_date = timezone.now() - timedelta(days=days)
        
        for user in users:
            # Generate sessions for this user
            sessions_count = random.randint(1, days // 2)  # 1-15 sessions
            
            for session_num in range(sessions_count):
                # Generate session start time
                session_start = start_date + timedelta(
                    days=random.randint(0, days-1),
                    hours=random.randint(0, 23),
                    minutes=random.randint(0, 59)
                )
                
                # Generate session duration (5 minutes to 2 hours)
                session_duration = timedelta(
                    minutes=random.randint(5, 120)
                )
                session_end = session_start + session_duration
                
                # Create session
                session = UserSession.objects.create(
                    user=user,
                    session_id=f'session_{user.id}_{session_num}_{int(session_start.timestamp())}',
                    ip_address=f'192.168.1.{random.randint(1, 254)}',
                    device_type=random.choice(device_types),
                    browser=random.choice(browsers),
                    os=random.choice(operating_systems),
                    country=random.choice(countries),
                    city=random.choice(cities),
                    start_time=session_start,
                    end_time=session_end,
                    page_views=random.randint(1, 20),
                    events_count=0,
                    converted=random.random() < 0.1,  # 10% conversion rate
                    conversion_value=random.uniform(10, 1000) if random.random() < 0.1 else 0
                )
                
                # Generate events for this session
                events_in_session = random.randint(1, events_per_user // sessions_count)
                
                for event_num in range(events_in_session):
                    event_time = session_start + timedelta(
                        minutes=random.randint(0, int(session_duration.total_seconds() // 60))
                    )
                    
                    event_type = random.choice(event_types)
                    
                    # Generate event data
                    event_data = {}
                    if event_type == 'purchase':
                        event_data = {
                            'value': random.uniform(10, 1000),
                            'currency': 'IRR',
                            'product_id': random.randint(1, 1000)
                        }
                    elif event_type == 'search':
                        event_data = {
                            'query': random.choice(['laptop', 'phone', 'book', 'clothes', 'shoes']),
                            'results_count': random.randint(0, 100)
                        }
                    elif event_type == 'product_view':
                        event_data = {
                            'product_id': random.randint(1, 1000),
                            'category': random.choice(['electronics', 'books', 'clothing', 'home'])
                        }
                    
                    # Create event
                    UserBehaviorEvent.objects.create(
                        user=user,
                        session_id=session.session_id,
                        event_type=event_type,
                        page_url=f'https://asoud.com/{random.choice(["home", "products", "cart", "checkout"])}',
                        referrer_url=f'https://google.com/search?q={random.choice(["asoud", "online shop", "products"])}',
                        event_data=event_data,
                        user_agent=f'Mozilla/5.0 ({random.choice(operating_systems)}) AppleWebKit/537.36',
                        ip_address=session.ip_address,
                        device_type=session.device_type,
                        browser=session.browser,
                        os=session.os,
                        country=session.country,
                        city=session.city,
                        latitude=random.uniform(25, 40),
                        longitude=random.uniform(44, 60),
                        timestamp=event_time
                    )
                
                # Update session events count
                session.events_count = UserBehaviorEvent.objects.filter(
                    session_id=session.session_id
                ).count()
                session.save()
        
        self.stdout.write(self.style.SUCCESS('Generated sessions and events'))

    def calculate_analytics(self):
        """Calculate analytics for all entities"""
        self.stdout.write('Calculating analytics...')
        
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


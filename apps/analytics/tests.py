"""
Analytics Tests for ASOUD Platform
"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
import json

from .models import (
    UserBehaviorEvent, UserSession, ProductAnalytics, 
    MarketAnalytics, UserAnalytics, AnalyticsAggregation
)
from .services import AnalyticsService, MLService, RealTimeAnalyticsService
from .ml_models import (
    CollaborativeFilteringModel, ContentBasedFilteringModel, 
    PriceOptimizationModel, DemandForecastingModel
)

User = get_user_model()


class AnalyticsModelsTestCase(TestCase):
    """Test cases for analytics models"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            mobile_number='09123456789',
            email='test@example.com',
            password='testpass123'
        )
        
        self.user_analytics, created = UserAnalytics.objects.get_or_create(
            user=self.user,
            defaults={
                'total_sessions': 10,
                'total_page_views': 100,
                'total_orders': 5,
                'total_spent': 500.0
            }
        )
    
    def test_user_behavior_event_creation(self):
        """Test UserBehaviorEvent creation"""
        event = UserBehaviorEvent.objects.create(
            user=self.user,
            session_id='test_session_123',
            event_type='page_view',
            page_url='https://asoud.com/products',
            event_data={'product_id': 1, 'category': 'electronics'}
        )
        
        self.assertEqual(event.user, self.user)
        self.assertEqual(event.event_type, 'page_view')
        self.assertEqual(event.session_id, 'test_session_123')
        self.assertIsNotNone(event.timestamp)
    
    def test_user_session_creation(self):
        """Test UserSession creation"""
        start_time = timezone.now()
        end_time = start_time + timedelta(minutes=30)
        
        session = UserSession.objects.create(
            user=self.user,
            session_id='test_session_123',
            ip_address='192.168.1.1',
            device_type='desktop',
            browser='Chrome',
            os='Windows',
            country='Iran',
            city='Tehran',
            start_time=start_time,
            end_time=end_time,
            page_views=10,
            events_count=25,
            converted=True,
            conversion_value=100.0
        )
        
        self.assertEqual(session.user, self.user)
        self.assertEqual(session.device_type, 'desktop')
        self.assertTrue(session.converted)
        self.assertIsNotNone(session.duration)
    
    def test_user_analytics_calculation(self):
        """Test UserAnalytics metrics calculation"""
        # Create some test events
        UserBehaviorEvent.objects.create(
            user=self.user,
            session_id='session1',
            event_type='page_view',
            page_url='https://asoud.com/products'
        )
        
        UserBehaviorEvent.objects.create(
            user=self.user,
            session_id='session1',
            event_type='purchase',
            event_data={'value': 100.0}
        )
        
        # Calculate metrics
        self.user_analytics.calculate_metrics()
        
        # Refresh from database
        self.user_analytics.refresh_from_db()
        
        # Check that metrics were updated
        self.assertGreater(self.user_analytics.total_page_views, 0)
        self.assertGreater(self.user_analytics.total_orders, 0)


class AnalyticsServicesTestCase(TestCase):
    """Test cases for analytics services"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            mobile_number='09123456789',
            email='test@example.com',
            password='testpass123'
        )
        
        self.analytics_service = AnalyticsService()
        self.ml_service = MLService()
        self.real_time_service = RealTimeAnalyticsService()
    
    def test_analytics_service_dashboard_data(self):
        """Test AnalyticsService dashboard data"""
        # Create test data
        UserAnalytics.objects.create(
            user=self.user,
            total_sessions=5,
            total_page_views=50,
            total_orders=2,
            total_spent=200.0
        )
        
        # Get dashboard data
        dashboard_data = self.analytics_service.get_dashboard_data(self.user)
        
        # Check that dashboard data contains expected keys
        expected_keys = [
            'total_users', 'total_sessions', 'total_page_views', 
            'total_orders', 'total_revenue', 'conversion_rate'
        ]
        
        for key in expected_keys:
            self.assertIn(key, dashboard_data)
    
    def test_analytics_service_time_series_data(self):
        """Test AnalyticsService time series data"""
        # Get time series data
        time_series_data = self.analytics_service.get_time_series_data(days=7, metric='revenue')
        
        # Check that we get data for 7 days
        self.assertEqual(len(time_series_data), 7)
        
        # Check that each day has expected structure
        for day_data in time_series_data:
            self.assertIn('date', day_data)
            self.assertIn('value', day_data)
    
    def test_ml_service_product_recommendations(self):
        """Test MLService product recommendations"""
        # Get product recommendations
        recommendations = self.ml_service.get_product_recommendations(self.user.id, 5)
        
        # Check that we get a list
        self.assertIsInstance(recommendations, list)
        
        # Check that recommendations don't exceed limit
        self.assertLessEqual(len(recommendations), 5)
    
    def test_real_time_service_metrics(self):
        """Test RealTimeAnalyticsService metrics"""
        # Get real-time metrics
        real_time_data = self.real_time_service.get_real_time_metrics()
        
        # Check that real-time data contains expected keys
        expected_keys = [
            'timestamp', 'active_users', 'active_sessions', 
            'current_orders', 'current_revenue'
        ]
        
        for key in expected_keys:
            self.assertIn(key, real_time_data)


class MLModelsTestCase(TestCase):
    """Test cases for ML models"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            mobile_number='09123456789',
            email='test@example.com',
            password='testpass123'
        )
        
        # Create test events
        self.events = []
        for i in range(10):
            event = UserBehaviorEvent.objects.create(
                user=self.user,
                session_id=f'session_{i}',
                event_type='purchase',
                object_id=i + 1,
                event_data={'value': 100.0 + i * 10}
            )
            self.events.append(event)
    
    def test_collaborative_filtering_model(self):
        """Test CollaborativeFilteringModel"""
        model = CollaborativeFilteringModel()
        
        # Fit the model
        model.fit(self.events)
        
        # Test prediction
        prediction = model.predict(self.user.id, 1)
        self.assertIsInstance(prediction, float)
        
        # Test recommendations
        recommendations = model.get_recommendations(self.user.id, 5)
        self.assertIsInstance(recommendations, list)
        self.assertLessEqual(len(recommendations), 5)
    
    def test_content_based_filtering_model(self):
        """Test ContentBasedFilteringModel"""
        model = ContentBasedFilteringModel()
        
        # Prepare test data
        products_data = [
            {
                'product_id': 1,
                'category_id': 1,
                'price': 100.0,
                'rating': 4.5,
                'popularity_score': 80.0
            },
            {
                'product_id': 2,
                'category_id': 1,
                'price': 150.0,
                'rating': 4.0,
                'popularity_score': 70.0
            }
        ]
        
        # Fit the model
        model.fit(products_data)
        
        # Test similar products
        similar_products = model.get_similar_products(1, 5)
        self.assertIsInstance(similar_products, list)
    
    def test_price_optimization_model(self):
        """Test PriceOptimizationModel"""
        model = PriceOptimizationModel()
        
        # Prepare test data
        historical_data = [
            {
                'price': 100.0,
                'category_id': 1,
                'competitor_price': 95.0,
                'demand_score': 0.8,
                'seasonality': 1.0,
                'promotion_active': False,
                'stock_level': 100,
                'demand': 50
            }
        ]
        
        # Fit the model
        model.fit(historical_data)
        
        # Test price optimization
        product_features = {
            'price': 100.0,
            'category_id': 1,
            'competitor_price': 95.0,
            'demand_score': 0.8,
            'seasonality': 1.0,
            'promotion_active': False,
            'stock_level': 100
        }
        
        optimization = model.predict_optimal_price(product_features)
        self.assertIn('optimal_price', optimization)
        self.assertIn('confidence', optimization)
    
    def test_demand_forecasting_model(self):
        """Test DemandForecastingModel"""
        model = DemandForecastingModel()
        
        # Prepare test data
        time_series_data = [
            {'date': '2024-01-01', 'demand': 50},
            {'date': '2024-01-02', 'demand': 55},
            {'date': '2024-01-03', 'demand': 60},
            {'date': '2024-01-04', 'demand': 45},
            {'date': '2024-01-05', 'demand': 70}
        ]
        
        # Fit the model
        model.fit(time_series_data)
        
        # Test forecasting
        forecast = model.forecast(7)
        self.assertIsInstance(forecast, list)
        self.assertEqual(len(forecast), 7)
        
        # Check forecast structure
        for day_forecast in forecast:
            self.assertIn('date', day_forecast)
            self.assertIn('predicted_demand', day_forecast)
            self.assertIn('confidence', day_forecast)


class AnalyticsIntegrationTestCase(TestCase):
    """Integration test cases for analytics"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            mobile_number='09123456789',
            email='test@example.com',
            password='testpass123'
        )
        
        # Create user analytics
        self.user_analytics, created = UserAnalytics.objects.get_or_create(
            user=self.user,
            defaults={
                'total_sessions': 10,
                'total_page_views': 100,
                'total_orders': 5,
                'total_spent': 500.0
            }
        )
    
    def test_end_to_end_analytics_flow(self):
        """Test end-to-end analytics flow"""
        # Create a session
        session = UserSession.objects.create(
            user=self.user,
            session_id='test_session',
            ip_address='192.168.1.1',
            device_type='desktop',
            browser='Chrome',
            os='Windows',
            country='Iran',
            city='Tehran',
            start_time=timezone.now(),
            end_time=timezone.now() + timedelta(minutes=30),
            page_views=10,
            events_count=25,
            converted=True,
            conversion_value=100.0
        )
        
        # Create some events
        UserBehaviorEvent.objects.create(
            user=self.user,
            session_id=session.session_id,
            event_type='page_view',
            page_url='https://asoud.com/products'
        )
        
        UserBehaviorEvent.objects.create(
            user=self.user,
            session_id=session.session_id,
            event_type='purchase',
            event_data={'value': 100.0}
        )
        
        # Update analytics
        self.user_analytics.calculate_metrics()
        
        # Get dashboard data
        analytics_service = AnalyticsService()
        dashboard_data = analytics_service.get_dashboard_data(self.user)
        
        # Verify that analytics were updated
        self.assertGreater(dashboard_data['total_sessions'], 0)
        self.assertGreater(dashboard_data['total_page_views'], 0)
        self.assertGreater(dashboard_data['total_orders'], 0)
    
    def test_ml_recommendations_integration(self):
        """Test ML recommendations integration"""
        # Create some test events
        for i in range(5):
            UserBehaviorEvent.objects.create(
                user=self.user,
                session_id=f'session_{i}',
                event_type='purchase',
                object_id=i + 1,
                event_data={'value': 100.0 + i * 10}
            )
        
        # Get ML service
        ml_service = MLService()
        
        # Get recommendations
        recommendations = ml_service.get_user_recommendations(self.user)
        
        # Check that we get recommendations
        self.assertIn('products', recommendations)
        self.assertIn('categories', recommendations)
        self.assertIn('markets', recommendations)
        
        # Check that recommendations are lists
        self.assertIsInstance(recommendations['products'], list)
        self.assertIsInstance(recommendations['categories'], list)
        self.assertIsInstance(recommendations['markets'], list)


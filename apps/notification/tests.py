"""
Tests for notification app
"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.test import APITestCase
from rest_framework import status

from .models import Notification, NotificationTemplate, NotificationPreference

User = get_user_model()


class NotificationModelTests(TestCase):
    """Test notification models"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            mobile_number='09123456789',
            email='test@example.com',
            password='testpass123'
        )
    
    def test_notification_creation(self):
        """Test notification creation"""
        notification = Notification.objects.create(
            user=self.user,
            notification_type='order_confirmed',
            channel='push',
            title='Test Notification',
            body='This is a test notification',
            priority='high'
        )
        
        self.assertEqual(notification.user, self.user)
        self.assertEqual(notification.notification_type, 'order_confirmed')
        self.assertEqual(notification.channel, 'push')
        self.assertEqual(notification.status, 'pending')
        self.assertEqual(notification.priority, 'high')
    
    def test_notification_mark_as_sent(self):
        """Test marking notification as sent"""
        notification = Notification.objects.create(
            user=self.user,
            notification_type='order_confirmed',
            channel='push',
            title='Test Notification',
            body='This is a test notification'
        )
        
        notification.mark_as_sent()
        
        self.assertEqual(notification.status, 'sent')
        self.assertIsNotNone(notification.sent_at)


class NotificationAPITests(APITestCase):
    """Test notification API endpoints"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            mobile_number='09123456789',
            email='test@example.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
    
    def test_notification_list(self):
        """Test notification list endpoint"""
        # Create test notifications
        Notification.objects.create(
            user=self.user,
            notification_type='order_confirmed',
            channel='push',
            title='Test Notification 1',
            body='This is test notification 1'
        )
        
        response = self.client.get('/api/v1/notifications/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Check if response is paginated or not
        if isinstance(response.data, dict) and 'results' in response.data:
            self.assertEqual(len(response.data['results']), 1)
        else:
            self.assertEqual(len(response.data), 1)
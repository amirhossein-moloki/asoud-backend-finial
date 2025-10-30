"""
Test Cases for IDOR Fixes - Day 1
Week 1 Security Patch Implementation
"""

import uuid
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from apps.users.models import User
from apps.cart.models import Order, OrderItem
from apps.users.models import UserBankInfo, BankInfo
from apps.product.models import Product, Market


class OrderIDORTestCase(TestCase):
    """
    Test IDOR vulnerabilities in Order views
    
    Security: Verify that users cannot access/modify orders that don't belong to them
    """
    
    def setUp(self):
        """Set up test data"""
        self.client = APIClient()
        
        # Create users
        self.user1 = User.objects.create_user(
            mobile_number='09121234567',
            password='testpass123'
        )
        self.user2 = User.objects.create_user(
            mobile_number='09121234568',
            password='testpass123'
        )
        
        # Create orders
        self.order_user1 = Order.objects.create(
            user=self.user1,
            status=Order.PENDING,
            description="User 1 Order"
        )
        self.order_user2 = Order.objects.create(
            user=self.user2,
            status=Order.PENDING,
            description="User 2 Order"
        )
    
    def test_user_cannot_view_other_users_order(self):
        """
        Test: User 1 tries to view User 2's order
        
        Expected: 404 Not Found (not 403 to avoid information disclosure)
        """
        self.client.force_authenticate(user=self.user1)
        
        url = reverse('order-detail', kwargs={'pk': self.order_user2.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn('error', response.data)
    
    def test_user_can_view_own_order(self):
        """
        Test: User 1 views their own order
        
        Expected: 200 OK with order data
        """
        self.client.force_authenticate(user=self.user1)
        
        url = reverse('order-detail', kwargs={'pk': self.order_user1.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['data']['id'], str(self.order_user1.id))
    
    def test_user_cannot_update_other_users_order(self):
        """
        Test: User 1 tries to update User 2's order
        
        Expected: 404 Not Found
        """
        self.client.force_authenticate(user=self.user1)
        
        url = reverse('order-update', kwargs={'pk': self.order_user2.id})
        response = self.client.put(url, {
            'description': 'Hacked!',
            'type': 'online'
        }, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        
        # Verify order was NOT modified
        self.order_user2.refresh_from_db()
        self.assertEqual(self.order_user2.description, "User 2 Order")
    
    def test_user_can_update_own_pending_order(self):
        """
        Test: User 1 updates their own pending order
        
        Expected: 200 OK
        """
        self.client.force_authenticate(user=self.user1)
        
        url = reverse('order-update', kwargs={'pk': self.order_user1.id})
        response = self.client.put(url, {
            'description': 'Updated description',
            'type': 'online'
        }, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify order was modified
        self.order_user1.refresh_from_db()
        self.assertEqual(self.order_user1.description, 'Updated description')
    
    def test_user_cannot_update_confirmed_order(self):
        """
        Test: User tries to update a confirmed order
        
        Expected: 400 Bad Request
        """
        self.order_user1.status = Order.CONFIRMED
        self.order_user1.save()
        
        self.client.force_authenticate(user=self.user1)
        
        url = reverse('order-update', kwargs={'pk': self.order_user1.id})
        response = self.client.put(url, {
            'description': 'Try to update',
            'type': 'online'
        }, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('cannot be modified', response.data['error'].lower())
    
    def test_user_cannot_delete_other_users_order(self):
        """
        Test: User 1 tries to delete User 2's order
        
        Expected: 404 Not Found
        """
        self.client.force_authenticate(user=self.user1)
        
        url = reverse('order-delete', kwargs={'pk': self.order_user2.id})
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        
        # Verify order still exists
        self.assertTrue(Order.objects.filter(id=self.order_user2.id).exists())
    
    def test_user_can_delete_own_draft_order(self):
        """
        Test: User deletes their own draft order
        
        Expected: 204 No Content
        """
        self.order_user1.status = Order.DRAFT
        self.order_user1.save()
        
        self.client.force_authenticate(user=self.user1)
        
        url = reverse('order-delete', kwargs={'pk': self.order_user1.id})
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        
        # Verify order was deleted
        self.assertFalse(Order.objects.filter(id=self.order_user1.id).exists())
    
    def test_user_cannot_delete_non_draft_order(self):
        """
        Test: User tries to delete their own pending order
        
        Expected: 400 Bad Request
        """
        self.client.force_authenticate(user=self.user1)
        
        url = reverse('order-delete', kwargs={'pk': self.order_user1.id})
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('draft', response.data['error'].lower())
    
    def test_unauthenticated_cannot_access_orders(self):
        """
        Test: Unauthenticated user tries to access order
        
        Expected: 401 Unauthorized
        """
        url = reverse('order-detail', kwargs={'pk': self.order_user1.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class BankInfoIDORTestCase(TestCase):
    """
    Test IDOR vulnerabilities in BankInfo views
    
    Security: Verify that users cannot access/modify bank info that doesn't belong to them
    """
    
    def setUp(self):
        """Set up test data"""
        self.client = APIClient()
        
        # Create users
        self.user1 = User.objects.create_user(
            mobile_number='09121234567',
            password='testpass123'
        )
        self.user2 = User.objects.create_user(
            mobile_number='09121234568',
            password='testpass123'
        )
        
        # Create bank
        self.bank = BankInfo.objects.create(
            name='Test Bank',
            code='123'
        )
        
        # Create bank info
        self.bank_info_user1 = UserBankInfo.objects.create(
            user=self.user1,
            bank=self.bank,
            shaba='IR123456789012345678901234',
            account_number='1234567890'
        )
        self.bank_info_user2 = UserBankInfo.objects.create(
            user=self.user2,
            bank=self.bank,
            shaba='IR987654321098765432109876',
            account_number='0987654321'
        )
    
    def test_user_cannot_view_other_users_bank_info(self):
        """
        Test: User 1 tries to view User 2's bank info
        
        Expected: 404 Not Found
        """
        self.client.force_authenticate(user=self.user1)
        
        url = reverse('bankinfo-detail', kwargs={'pk': self.bank_info_user2.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn('error', response.data)
    
    def test_user_can_view_own_bank_info(self):
        """
        Test: User 1 views their own bank info
        
        Expected: 200 OK with bank info data
        """
        self.client.force_authenticate(user=self.user1)
        
        url = reverse('bankinfo-detail', kwargs={'pk': self.bank_info_user1.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['data']['shaba'], self.bank_info_user1.shaba)
    
    def test_user_cannot_update_other_users_bank_info(self):
        """
        Test: User 1 tries to update User 2's bank info
        
        Expected: 404 Not Found
        """
        self.client.force_authenticate(user=self.user1)
        
        url = reverse('bankinfo-update', kwargs={'pk': self.bank_info_user2.id})
        response = self.client.put(url, {
            'shaba': 'IR111111111111111111111111'
        }, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        
        # Verify bank info was NOT modified
        self.bank_info_user2.refresh_from_db()
        self.assertEqual(self.bank_info_user2.shaba, 'IR987654321098765432109876')
    
    def test_user_can_update_own_bank_info(self):
        """
        Test: User 1 updates their own bank info
        
        Expected: 200 OK
        """
        self.client.force_authenticate(user=self.user1)
        
        new_shaba = 'IR111111111111111111111111'
        url = reverse('bankinfo-update', kwargs={'pk': self.bank_info_user1.id})
        response = self.client.put(url, {
            'shaba': new_shaba
        }, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify bank info was modified
        self.bank_info_user1.refresh_from_db()
        self.assertEqual(self.bank_info_user1.shaba, new_shaba)
    
    def test_user_cannot_delete_other_users_bank_info(self):
        """
        Test: User 1 tries to delete User 2's bank info
        
        Expected: 404 Not Found
        """
        self.client.force_authenticate(user=self.user1)
        
        url = reverse('bankinfo-delete', kwargs={'pk': self.bank_info_user2.id})
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        
        # Verify bank info still exists
        self.assertTrue(UserBankInfo.objects.filter(id=self.bank_info_user2.id).exists())
    
    def test_user_can_delete_own_bank_info(self):
        """
        Test: User deletes their own bank info
        
        Expected: 204 No Content
        """
        self.client.force_authenticate(user=self.user1)
        
        url = reverse('bankinfo-delete', kwargs={'pk': self.bank_info_user1.id})
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        
        # Verify bank info was deleted
        self.assertFalse(UserBankInfo.objects.filter(id=self.bank_info_user1.id).exists())
    
    def test_unauthenticated_cannot_access_bank_info(self):
        """
        Test: Unauthenticated user tries to access bank info
        
        Expected: 401 Unauthorized
        """
        url = reverse('bankinfo-detail', kwargs={'pk': self.bank_info_user1.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class SecurityTestCase(TestCase):
    """
    Additional security tests
    """
    
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            mobile_number='09121234567',
            password='testpass123'
        )
    
    def test_invalid_uuid_returns_404(self):
        """
        Test: Invalid UUID in URL
        
        Expected: 404 Not Found (not 500)
        """
        self.client.force_authenticate(user=self.user)
        
        url = f'/api/v1/order/{uuid.uuid4()}/'
        response = self.client.get(url)
        
        self.assertIn(response.status_code, [status.HTTP_404_NOT_FOUND, status.HTTP_400_BAD_REQUEST])
    
    def test_no_information_disclosure_in_errors(self):
        """
        Test: Error messages don't disclose sensitive information
        
        Expected: Generic error messages
        """
        self.client.force_authenticate(user=self.user)
        
        # Try to access non-existent order
        url = f'/api/v1/order/{uuid.uuid4()}/'
        response = self.client.get(url)
        
        if 'error' in response.data:
            error_msg = str(response.data['error']).lower()
            # Should not contain database details, stack traces, etc.
            self.assertNotIn('exception', error_msg)
            self.assertNotIn('traceback', error_msg)
            self.assertNotIn('database', error_msg)
            self.assertNotIn('query', error_msg)


# Run tests:
# python manage.py test apps.cart.tests.test_idor_fixes -v 2



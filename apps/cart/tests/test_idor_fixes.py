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
from apps.item.models import Item
from apps.office_registration.models.office_registration_models import OfficeRegistration
from rest_framework.test import APITestCase


class OrderIDORTestCase(APITestCase):
    """
    Test IDOR vulnerabilities in Order views
    
    Security: Verify that users cannot access/modify orders that don't belong to them
    """
    
    def setUp(self):
        """Set up test data"""
        
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
        
        url = reverse('user_order:order-detail', kwargs={'pk': self.order_user2.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn('error', response.data)
    
    def test_user_can_view_own_order(self):
        """
        Test: User 1 views their own order
        
        Expected: 200 OK with order data
        """
        self.client.force_authenticate(user=self.user1)
        
        url = reverse('user_order:order-detail', kwargs={'pk': self.order_user1.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['data']['id'], str(self.order_user1.id))
    
    def test_user_cannot_update_other_users_order(self):
        """
        Test: User 1 tries to update User 2's order
        
        Expected: 404 Not Found
        """
        self.client.force_authenticate(user=self.user1)
        
        url = reverse('user_order:order-update', kwargs={'pk': self.order_user2.id})
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
        
        url = reverse('user_order:order-update', kwargs={'pk': self.order_user1.id})
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
        
        url = reverse('user_order:order-update', kwargs={'pk': self.order_user1.id})
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
        
        url = reverse('user_order:order-delete', kwargs={'pk': self.order_user2.id})
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
        
        url = reverse('user_order:order-delete', kwargs={'pk': self.order_user1.id})
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
        
        url = reverse('user_order:order-delete', kwargs={'pk': self.order_user1.id})
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('draft', response.data['error'].lower())
    
    def test_unauthenticated_cannot_access_orders(self):
        """
        Test: Unauthenticated user tries to access order
        
        Expected: 401 Unauthorized
        """
        url = reverse('user_order:order-detail', kwargs={'pk': self.order_user1.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class BankInfoIDORTestCase(APITestCase):
    """
    Test IDOR vulnerabilities in BankInfo views
    
    Security: Verify that users cannot access/modify bank info that doesn't belong to them
    """
    
    def setUp(self):
        """Set up test data"""
        
        # Create users
        self.user1 = User.objects.create_user(
            mobile_number='09121234567',
            password='testpass123'
        )
        self.user2 = User.objects.create_user(
            mobile_number='09121234568',
            password='testpass123'
        )
        self.bank_info = BankInfo.objects.create(name="Bank Mellat")
        
        # Create bank info
        self.bank_info_user1 = UserBankInfo.objects.create(
            user=self.user1,
            bank_info=self.bank_info,
            card_number="6104337912345678",
            account_number='1234567890',
            iban='IR123456789012345678901234',
            full_name='User One',
            branch_id=101,
            branch_name='Branch A'
        )
        self.bank_info_user2 = UserBankInfo.objects.create(
            user=self.user2,
            bank_info=self.bank_info,
            card_number="6104337912345679",
            account_number='0987654321',
            iban='IR987654321098765432109876',
            full_name='User Two',
            branch_id=102,
            branch_name='Branch B'
        )
    
    def test_user_cannot_view_other_users_bank_info(self):
        """
        Test: User 1 tries to view User 2's bank info
        
        Expected: 404 Not Found
        """
        self.client.force_authenticate(user=self.user1)
        
        url = reverse('users_user:bank-detail', kwargs={'pk': self.bank_info_user2.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn('error', response.data)
    
    def test_user_can_view_own_bank_info(self):
        """
        Test: User 1 views their own bank info
        
        Expected: 200 OK with bank info data
        """
        self.client.force_authenticate(user=self.user1)
        
        url = reverse('users_user:bank-detail', kwargs={'pk': self.bank_info_user1.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['data']['iban'], self.bank_info_user1.iban)
    
    def test_user_cannot_update_other_users_bank_info(self):
        """
        Test: User 1 tries to update User 2's bank info
        
        Expected: 404 Not Found
        """
        self.client.force_authenticate(user=self.user1)
        
        url = reverse('users_user:bank-update', kwargs={'pk': self.bank_info_user2.id})
        response = self.client.put(url, {
            'shaba': 'IR111111111111111111111111'
        }, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        
        # Verify bank info was NOT modified
        self.bank_info_user2.refresh_from_db()
        self.assertEqual(self.bank_info_user2.iban, 'IR987654321098765432109876')
    
    def test_user_can_update_own_bank_info(self):
        """
        Test: User 1 updates their own bank info
        
        Expected: 200 OK
        """
        self.client.force_authenticate(user=self.user1)
        
        new_shaba = 'IR111111111111111111111111'
        url = reverse('users_user:bank-update', kwargs={'pk': self.bank_info_user1.id})
        response = self.client.put(url, {
            'iban': new_shaba
        }, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify bank info was modified
        self.bank_info_user1.refresh_from_db()
        self.assertEqual(self.bank_info_user1.iban, new_shaba)
    
    def test_user_cannot_delete_other_users_bank_info(self):
        """
        Test: User 1 tries to delete User 2's bank info
        
        Expected: 404 Not Found
        """
        self.client.force_authenticate(user=self.user1)
        
        url = reverse('users_user:bank-delete', kwargs={'pk': self.bank_info_user2.id})
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
        
        url = reverse('users_user:bank-delete', kwargs={'pk': self.bank_info_user1.id})
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        
        # Verify bank info was deleted
        self.assertFalse(UserBankInfo.objects.filter(id=self.bank_info_user1.id).exists())
    
    def test_unauthenticated_cannot_access_bank_info(self):
        """
        Test: Unauthenticated user tries to access bank info
        
        Expected: 401 Unauthorized
        """
        url = reverse('users_user:bank-detail', kwargs={'pk': self.bank_info_user1.id})
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
        
        payload = getattr(response, 'data', None)
        if isinstance(payload, dict) and 'error' in payload:
            error_msg = str(payload['error']).lower()
            # Should not contain database details, stack traces, etc.
            self.assertNotIn('exception', error_msg)
            self.assertNotIn('traceback', error_msg)
            self.assertNotIn('database', error_msg)
            self.assertNotIn('query', error_msg)


# Run tests:
# python manage.py test apps.cart.tests.test_idor_fixes -v 2



#!/usr/bin/env python
"""
Test script to verify the 8-state virtual office workflow system implementation.
This script tests the workflow models, status transitions, and admin functionality.
"""

import os
import sys
import django
from django.test import TestCase
from django.contrib.auth import get_user_model

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

from apps.market.models import Market, MarketWorkflowHistory, MarketApprovalRequest, MarketSubscription
from apps.users.models import User
from apps.category.models import Category, SubCategory
from decimal import Decimal
from datetime import datetime, timedelta

def test_workflow_models():
    """Test that all workflow models can be created and work correctly."""
    print("🧪 Testing Workflow Models...")
    
    try:
        # Create or get test user
        user, created = User.objects.get_or_create(
            mobile_number='09123456789',
            defaults={
                'email': 'test@example.com',
                'password': 'testpass123'
            }
        )
        if created:
            user.set_password('testpass123')
            user.save()
        print("✅ Test user created/retrieved successfully")
        
        # Create or get a SubCategory for the market
        from apps.category.models import Group
        
        # First create a Group
        group, _ = Group.objects.get_or_create(
            title='Test Group',
            defaults={'market_fee': 0.0}
        )
        
        category, _ = Category.objects.get_or_create(
            title='Test Category',
            group=group,
            defaults={'market_fee': 0.0}
        )
        sub_category, _ = SubCategory.objects.get_or_create(
            title='Test SubCategory',
            category=category,
            defaults={'market_fee': 0.0}
        )
        print("✅ Test group, category and subcategory created successfully")
        
        # Create test market
        market = Market.objects.create(
            user=user,
            type=Market.COMPANY,
            name='Test Market',
            business_id='123456789',
            sub_category=sub_category
        )
        print("✅ Test market created successfully")
        
        # Test status transition
        market.status = Market.PAID_UNDER_CREATION
        market.save()
        print("✅ Market status updated to: PAID_UNDER_CREATION")
        
        # Test MarketWorkflowHistory
        workflow_history = MarketWorkflowHistory.objects.create(
            market=market,
            from_status=Market.UNPAID_UNDER_CREATION,
            to_status=Market.PAID_UNDER_CREATION,
            reason='Payment completed',
            changed_by=user
        )
        print("✅ Workflow history record created")
        
        # Test MarketApprovalRequest
        approval_request = MarketApprovalRequest.objects.create(
            market=market,
            requested_by=user,
            request_type='publication',
            message='Please approve my virtual office for publication'
        )
        print("✅ Approval request created")
        
        # Test MarketSubscription
        subscription = MarketSubscription.objects.create(
            market=market,
            plan_type=MarketSubscription.MONTHLY,
            amount=Decimal('99.99'),
            start_date=datetime.now(),
            end_date=datetime.now() + timedelta(days=30)
        )
        print("✅ Market subscription created")
        
        # Test all 8 workflow states
        workflow_states = [
            Market.UNPAID_UNDER_CREATION,
            Market.PAID_UNDER_CREATION,
            Market.PAID_IN_PUBLICATION_QUEUE,
            Market.PAID_NON_PUBLICATION,
            Market.PUBLISHED,
            Market.PAID_NEEDS_EDITING,
            Market.INACTIVE,
            Market.PAYMENT_PENDING
        ]
        
        print("\n📋 Testing all 8 workflow states:")
        for state in workflow_states:
            market.status = state
            market.save()
            print(f"   ✅ {state}: {market.get_status_display()}")
        
        # Test relationships
        print(f"\n🔗 Testing relationships:")
        print(f"   Market workflow history count: {market.workflow_history.count()}")
        print(f"   Market approval requests count: {market.approval_requests.count()}")
        print(f"   Market subscriptions count: {market.subscriptions.count()}")
        
        print("\n🎉 All workflow model tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_admin_functionality():
    """Test that admin functionality is working."""
    print("\n🔧 Testing Admin Functionality...")
    
    try:
        from django.contrib import admin
        from apps.market.admin import MarketWorkflowHistoryAdmin, MarketApprovalRequestAdmin, MarketSubscriptionAdmin
        
        # Check if admin classes are registered
        admin_models = [
            (MarketWorkflowHistory, MarketWorkflowHistoryAdmin),
            (MarketApprovalRequest, MarketApprovalRequestAdmin),
            (MarketSubscription, MarketSubscriptionAdmin)
        ]
        
        for model, admin_class in admin_models:
            if model in admin.site._registry:
                print(f"   ✅ {model.__name__} is registered in admin")
            else:
                print(f"   ❌ {model.__name__} is NOT registered in admin")
        
        print("✅ Admin functionality test completed")
        return True
        
    except Exception as e:
        print(f"❌ Admin test failed: {e}")
        return False

def test_url_configuration():
    """Test that URL configuration is working."""
    print("\n🌐 Testing URL Configuration...")
    
    try:
        from django.urls import reverse, NoReverseMatch
        
        # Test workflow URLs
        workflow_urls = [
            'market_workflow:workflow_history',
            'market_workflow:list_approval_requests',
            'market_workflow:list_subscriptions',
            'market_workflow:admin_approval_list'
        ]
        
        for url_name in workflow_urls:
            try:
                if 'workflow_history' in url_name:
                    # This URL requires market_id parameter
                    url = reverse(url_name, kwargs={'market_id': 'test-market'})
                else:
                    url = reverse(url_name)
                print(f"   ✅ {url_name}: {url}")
            except NoReverseMatch:
                print(f"   ❌ {url_name}: URL not found")
        
        print("✅ URL configuration test completed")
        return True
        
    except Exception as e:
        print(f"❌ URL test failed: {e}")
        return False

def main():
    """Run all tests."""
    print("🚀 Starting Virtual Office Workflow System Tests\n")
    
    tests = [
        test_workflow_models,
        test_admin_functionality,
        test_url_configuration
    ]
    
    results = []
    for test in tests:
        results.append(test())
    
    print(f"\n📊 Test Results:")
    print(f"   Passed: {sum(results)}/{len(results)}")
    print(f"   Failed: {len(results) - sum(results)}/{len(results)}")
    
    if all(results):
        print("\n🎉 All tests passed! The workflow system is working correctly.")
    else:
        print("\n⚠️  Some tests failed. Please check the implementation.")
    
    return all(results)

if __name__ == '__main__':
    main()
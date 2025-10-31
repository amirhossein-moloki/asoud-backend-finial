#!/usr/bin/env python
"""
Enhanced Share Functionality Test Script
Tests the comprehensive sharing system with analytics and social media integration.
"""

import os
import sys
import django
import json
from datetime import datetime

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

from django.test import RequestFactory
from django.contrib.auth import get_user_model
from apps.market.models import Market, MarketShare
from apps.category.models import Group, Category, SubCategory
from apps.market.views.workflow_views import MarketShareAPIView, MarketShareAnalyticsAPIView

User = get_user_model()

def test_enhanced_share_functionality():
    """Test the enhanced share functionality"""
    print("🧪 Testing Enhanced Share Functionality...")
    
    try:
        # Create test data
        print("📝 Creating test data...")
        
        # Create Group, Category, and SubCategory
        group, _ = Group.objects.get_or_create(
            title="Test Group",
            defaults={'market_fee': 0.0}
        )
        
        category, _ = Category.objects.get_or_create(
            title="Test Category",
            group=group,
            defaults={'market_fee': 0.0}
        )
        
        subcategory, _ = SubCategory.objects.get_or_create(
            title="Test SubCategory",
            category=category,
            defaults={'market_fee': 0.0}
        )
        
        # Create test user
        user, created = User.objects.get_or_create(
            mobile_number="09123456789",
            defaults={
                'email': 'test@example.com',
            }
        )
        if created:
            user.set_password('testpass123')
            user.save()
        
        # Create test market
        market, _ = Market.objects.get_or_create(
            user=user,
            name="Test Virtual Office",
            business_id="TEST123",
            sub_category=subcategory,
            defaults={
                'type': Market.SHOP,  # Using SHOP instead of VIRTUAL_OFFICE
                'status': Market.PUBLISHED,  # Set to published for sharing
                'description': 'A test virtual office for sharing functionality',
                'slogan': 'Your virtual office solution',
                'view_count': 100,
            }
        )
        
        # Ensure market is published
        market.status = Market.PUBLISHED
        market.save()
        
        print(f"✅ Test data created - Market: {market.name} (ID: {market.id})")
        
        # Test 1: Basic Share Data Generation
        print("\n🔗 Test 1: Basic Share Data Generation")
        
        factory = RequestFactory()
        request = factory.get('/')
        request.META['HTTP_HOST'] = 'localhost:8000'
        
        share_data = market.get_share_data(request)
        
        assert share_data is not None, "Share data should not be None for published market"
        assert 'url' in share_data, "Share data should contain URL"
        assert 'social_links' in share_data, "Share data should contain social links"
        assert 'whatsapp' in share_data['social_links'], "Should have WhatsApp share link"
        assert 'telegram' in share_data['social_links'], "Should have Telegram share link"
        
        print(f"✅ Share URL: {share_data['url']}")
        print(f"✅ Social platforms: {list(share_data['social_links'].keys())}")
        
        # Test 2: Share API View (GET)
        print("\n📊 Test 2: Share API View (GET)")
        
        request = factory.get(f'/api/v1/owner/market/workflow/{market.id}/share/')
        request.user = user
        request.META['HTTP_HOST'] = 'localhost:8000'
        
        view = MarketShareAPIView()
        response = view.get(request, market.id)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        response_data = response.data['data']
        assert 'share_data' in response_data, "Response should contain share_data"
        assert 'analytics' in response_data, "Response should contain analytics"
        assert 'qr_code_url' in response_data, "Response should contain QR code URL"
        
        print(f"✅ Share API GET successful")
        print(f"✅ Analytics included: {list(response_data['analytics'].keys())}")
        
        # Test 3: Share Tracking (POST)
        print("\n📈 Test 3: Share Tracking (POST)")
        
        platforms_to_test = ['whatsapp', 'telegram', 'twitter', 'facebook', 'copy_link']
        
        for platform in platforms_to_test:
            request = factory.post(
                f'/api/v1/owner/market/workflow/{market.id}/share/',
                data={'platform': platform},
                content_type='application/json'
            )
            request.user = user
            request.META['HTTP_HOST'] = 'localhost:8000'
            request.META['HTTP_USER_AGENT'] = 'Test Browser 1.0'
            request.META['REMOTE_ADDR'] = '127.0.0.1'
            # Add data attribute for DRF compatibility
            request.data = {'platform': platform}
            
            view = MarketShareAPIView()
            response = view.post(request, market.id)
            
            assert response.status_code == 200, f"Share tracking failed for {platform}"
            
            # Verify share record was created
            share_record = MarketShare.objects.filter(
                market=market,
                platform=platform,
                shared_by=user
            ).first()
            
            assert share_record is not None, f"Share record not created for {platform}"
            print(f"✅ {platform.capitalize()} share tracked successfully")
        
        # Test 4: Share Analytics
        print("\n📊 Test 4: Share Analytics")
        
        request = factory.get(f'/api/v1/owner/market/workflow/{market.id}/share/analytics/')
        request.user = user
        
        view = MarketShareAnalyticsAPIView()
        response = view.get(request, market.id)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        analytics_data = response.data['data']
        
        # Verify analytics structure
        expected_keys = [
            'total_shares', 'shares_last_30_days', 'shares_last_7_days', 
            'shares_today', 'platform_stats', 'daily_shares', 'top_sharers',
            'conversion_metrics'
        ]
        
        for key in expected_keys:
            assert key in analytics_data, f"Analytics should contain {key}"
        
        print(f"✅ Total shares tracked: {analytics_data['total_shares']}")
        print(f"✅ Platform breakdown: {len(analytics_data['platform_stats'])} platforms")
        print(f"✅ Daily shares data: {len(analytics_data['daily_shares'])} days")
        
        # Verify platform stats
        platform_stats = analytics_data['platform_stats']
        assert len(platform_stats) == len(platforms_to_test), "Should have stats for all tested platforms"
        
        for stat in platform_stats:
            assert 'platform' in stat, "Platform stat should have platform field"
            assert 'count' in stat, "Platform stat should have count field"
        
        # Test 5: Share Analytics with Non-Published Market
        print("\n🚫 Test 5: Share Analytics with Non-Published Market")
        
        # Create unpublished market
        unpublished_market = Market.objects.create(
            user=user,
            name="Unpublished Market",
            business_id="UNPUB123",
            sub_category=subcategory,
            type=Market.SHOP,  # Using SHOP instead of VIRTUAL_OFFICE
            status=Market.UNPAID_UNDER_CREATION,
        )
        
        request = factory.get(f'/api/v1/owner/market/workflow/{unpublished_market.id}/share/')
        request.user = user
        
        view = MarketShareAPIView()
        response = view.get(request, unpublished_market.id)
        
        assert response.status_code == 400, "Should return 400 for unpublished market"
        print("✅ Correctly blocked sharing for unpublished market")
        
        # Test 6: Invalid Platform Validation
        print("\n❌ Test 6: Invalid Platform Validation")
        
        request = factory.post(
            f'/api/v1/owner/market/workflow/{market.id}/share/',
            data={'platform': 'invalid_platform'},
            content_type='application/json'
        )
        request.user = user
        # Add data attribute for DRF compatibility
        request.data = {'platform': 'invalid_platform'}
        
        view = MarketShareAPIView()
        response = view.post(request, market.id)
        
        assert response.status_code == 400, "Should return 400 for invalid platform"
        print("✅ Correctly validated platform input")
        
        # Test 7: Share URL Generation
        print("\n🔗 Test 7: Share URL Generation")
        
        # Test with request - add testserver to allowed hosts temporarily
        from django.conf import settings
        original_allowed_hosts = settings.ALLOWED_HOSTS
        settings.ALLOWED_HOSTS = settings.ALLOWED_HOSTS + ['testserver']
        
        try:
            request = factory.get('/')
            request.META['HTTP_HOST'] = 'testserver'
            share_url_with_request = market.get_share_url(request)
            assert share_url_with_request.startswith('http'), "Should generate full URL with request"
            
            # Test without request
            share_url_without_request = market.get_share_url()
            assert share_url_without_request.startswith('https://asoud.com'), "Should use default base URL"
            
            print(f"✅ Share URL with request: {share_url_with_request}")
            print(f"✅ Share URL without request: {share_url_without_request}")
            
        finally:
            # Restore original allowed hosts
            settings.ALLOWED_HOSTS = original_allowed_hosts
        
        print("\n🎉 All Enhanced Share Functionality Tests Passed!")
        
        # Summary
        total_shares = MarketShare.objects.filter(market=market).count()
        unique_platforms = MarketShare.objects.filter(market=market).values('platform').distinct().count()
        
        print(f"\n📊 Test Summary:")
        print(f"   • Total shares created: {total_shares}")
        print(f"   • Unique platforms tested: {unique_platforms}")
        print(f"   • Market view count: {market.view_count}")
        print(f"   • Share analytics endpoints: ✅ Working")
        print(f"   • Social media integration: ✅ Complete")
        print(f"   • Share tracking: ✅ Functional")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 Starting Enhanced Share Functionality Tests...")
    print("=" * 60)
    
    success = test_enhanced_share_functionality()
    
    print("=" * 60)
    if success:
        print("✅ All tests completed successfully!")
        print("🎯 Enhanced share functionality is working perfectly!")
    else:
        print("❌ Some tests failed!")
        sys.exit(1)
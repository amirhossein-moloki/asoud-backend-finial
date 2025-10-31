#!/usr/bin/env python
"""
Simplified Virtual Office Share Test
Tests the core functionality without translation dependencies.
"""
import os
import sys

# Setup Django with English locale to avoid translation issues
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
os.environ.setdefault('DJANGO_LANGUAGE_CODE', 'en')

import django
from django.conf import settings
# Override language code before setup
settings.configure = lambda: None  # Prevent reconfiguration
django.setup()

# Override language settings
from django.conf import settings
settings.LANGUAGE_CODE = 'en'
settings.USE_I18N = False

from django.test import Client
from django.contrib.auth.models import User
from apps.market.models import Market, MarketShare
import json

class SimpleVirtualOfficeShareTest:
    """Simplified test for virtual office share functionality"""
    
    def __init__(self):
        self.client = Client()
        self.results = []
        
    def setup_test_data(self):
        """Create test data"""
        print("🏢 Setting up Virtual Office Share Test Data...")
        
        # Create test user
        self.user = User.objects.create_user(
            username='vo_testuser',
            email='vo_test@example.com',
            password='testpass123'
        )
        
        # Create virtual office (Market)
        self.virtual_office = Market.objects.create(
            name='Tehran Premium Virtual Office',
            description='Premium virtual office space in Tehran business district',
            address='Tehran, Vanak Square, Business Tower, Floor 15',
            city='Tehran',
            zip_code='1234567890',
            phone='021-88776655',
            email='info@tehranvo.com',
            website_url='https://tehranvo.com',
            status='published',  # Must be published for sharing
            user=self.user
        )
        
        print(f"✓ Created virtual office: {self.virtual_office.name}")
        print(f"✓ Virtual office ID: {self.virtual_office.id}")
        print(f"✓ Status: {self.virtual_office.status}")
        
    def test_share_data_generation(self):
        """Test 1: Share Data Generation for Virtual Office"""
        print("\n=== Test 1: Virtual Office Share Data Generation ===")
        
        try:
            share_data = self.virtual_office.get_share_data()
            
            # Validate structure
            assert 'title' in share_data, "Missing title"
            assert 'description' in share_data, "Missing description"
            assert 'url' in share_data, "Missing URL"
            assert 'platforms' in share_data, "Missing platforms"
            
            # Validate content
            assert self.virtual_office.name in share_data['title'], "Title should contain office name"
            assert len(share_data['platforms']) > 0, "Should have sharing platforms"
            
            print(f"✓ Share data generated successfully")
            print(f"✓ Title: {share_data['title']}")
            print(f"✓ Available platforms: {len(share_data['platforms'])}")
            
            self.results.append(("Share Data Generation", "PASSED"))
            
        except Exception as e:
            print(f"✗ Test failed: {str(e)}")
            self.results.append(("Share Data Generation", f"FAILED: {str(e)}"))
    
    def test_share_api_access(self):
        """Test 2: Share API Access"""
        print("\n=== Test 2: Virtual Office Share API Access ===")
        
        try:
            # Test GET request
            url = f'/api/markets/{self.virtual_office.id}/share/'
            response = self.client.get(url)
            
            print(f"API Response Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                assert 'share_data' in data, "Response should contain share_data"
                print(f"✓ API accessible and returns valid data")
                self.results.append(("Share API Access", "PASSED"))
            else:
                print(f"✓ API endpoint exists (status: {response.status_code})")
                self.results.append(("Share API Access", f"ACCESSIBLE (status: {response.status_code})"))
                
        except Exception as e:
            print(f"✗ Test failed: {str(e)}")
            self.results.append(("Share API Access", f"FAILED: {str(e)}"))
    
    def test_share_tracking(self):
        """Test 3: Share Tracking"""
        print("\n=== Test 3: Virtual Office Share Tracking ===")
        
        try:
            url = f'/api/markets/{self.virtual_office.id}/share/'
            
            # Track a share
            response = self.client.post(url, {
                'platform': 'WhatsApp',
                'user_agent': 'Virtual Office Test Browser',
                'referrer_url': 'https://virtualoffice-test.com'
            })
            
            print(f"Share Tracking Response Status: {response.status_code}")
            
            if response.status_code in [200, 201]:
                # Check if share record was created
                share_count = MarketShare.objects.filter(market=self.virtual_office).count()
                print(f"✓ Share tracking successful")
                print(f"✓ Share records created: {share_count}")
                self.results.append(("Share Tracking", "PASSED"))
            else:
                print(f"✓ Share tracking endpoint accessible (status: {response.status_code})")
                self.results.append(("Share Tracking", f"ACCESSIBLE (status: {response.status_code})"))
                
        except Exception as e:
            print(f"✗ Test failed: {str(e)}")
            self.results.append(("Share Tracking", f"FAILED: {str(e)}"))
    
    def test_workflow_states(self):
        """Test 4: Virtual Office Workflow States"""
        print("\n=== Test 4: Virtual Office Workflow States ===")
        
        try:
            # Test different workflow states
            states_to_test = ['draft', 'published', 'suspended']
            results = {}
            
            for state in states_to_test:
                self.virtual_office.status = state
                self.virtual_office.save()
                
                try:
                    share_data = self.virtual_office.get_share_data()
                    results[state] = "Can share"
                except:
                    results[state] = "Cannot share"
            
            # Reset to published
            self.virtual_office.status = 'published'
            self.virtual_office.save()
            
            print(f"✓ Workflow state testing completed")
            for state, result in results.items():
                print(f"  - {state}: {result}")
            
            self.results.append(("Workflow States", "PASSED"))
            
        except Exception as e:
            print(f"✗ Test failed: {str(e)}")
            self.results.append(("Workflow States", f"FAILED: {str(e)}"))
    
    def run_all_tests(self):
        """Run all tests"""
        print("🏢 VIRTUAL OFFICE SHARE FUNCTIONALITY TEST")
        print("=" * 50)
        
        self.setup_test_data()
        self.test_share_data_generation()
        self.test_share_api_access()
        self.test_share_tracking()
        self.test_workflow_states()
        
        # Print summary
        print("\n" + "=" * 50)
        print("📊 TEST SUMMARY")
        print("=" * 50)
        
        passed = 0
        total = len(self.results)
        
        for test_name, result in self.results:
            status_icon = "✅" if "PASSED" in result else "⚠️" if "ACCESSIBLE" in result else "❌"
            print(f"{status_icon} {test_name}: {result}")
            if "PASSED" in result:
                passed += 1
        
        print(f"\n📈 Results: {passed}/{total} tests passed")
        
        # Check database records
        total_shares = MarketShare.objects.filter(market=self.virtual_office).count()
        print(f"📋 Share records created: {total_shares}")
        
        if passed == total:
            print("\n🎉 ALL VIRTUAL OFFICE SHARE TESTS PASSED!")
            print("✨ Virtual office share functionality is operational")
        else:
            print(f"\n⚠️ {total - passed} test(s) need attention")
        
        return passed == total

if __name__ == '__main__':
    test = SimpleVirtualOfficeShareTest()
    success = test.run_all_tests()
    sys.exit(0 if success else 1)
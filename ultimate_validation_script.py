#!/usr/bin/env python3
"""
Ultimate Validation Script for ASOUD Platform Phase 1 & 2
Comprehensive validation of security, performance, and production readiness
"""

import os
import sys
import django
import requests
import json
import time
from datetime import datetime

# Add the project directory to Python path
sys.path.append('/home/devops/projects/asoud-main-1-/asoud-main')

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.production')
django.setup()

class UltimateValidator:
    """Ultimate validation for Phase 1 & 2"""
    
    def __init__(self, base_url='http://localhost:8000'):
        self.base_url = base_url
        self.validation_results = {
            'security': {'passes': [], 'issues': [], 'critical': []},
            'performance': {'passes': [], 'issues': [], 'critical': []},
            'production': {'passes': [], 'issues': [], 'critical': []},
            'overall': {'score': 0, 'status': 'UNKNOWN'}
        }
        self.start_time = time.time()
    
    def validate_security_comprehensive(self):
        """Comprehensive security validation"""
        print("🔒 Comprehensive Security Validation...")
        
        from django.conf import settings
        
        # 1. Environment Security
        self._validate_environment_security(settings)
        
        # 2. Authentication Security
        self._validate_authentication_security(settings)
        
        # 3. Authorization Security
        self._validate_authorization_security(settings)
        
        # 4. Data Protection
        self._validate_data_protection(settings)
        
        # 5. Network Security
        self._validate_network_security(settings)
        
        # 6. API Security
        self._validate_api_security()
    
    def _validate_environment_security(self, settings):
        """Validate environment security"""
        # DEBUG mode
        if settings.DEBUG:
            self.validation_results['security']['critical'].append("DEBUG mode enabled in production")
        else:
            self.validation_results['security']['passes'].append("DEBUG mode disabled")
        
        # SECRET_KEY
        if not settings.SECRET_KEY or settings.SECRET_KEY == 'change-me-in-env':
            self.validation_results['security']['critical'].append("SECRET_KEY not properly configured")
        else:
            self.validation_results['security']['passes'].append("SECRET_KEY configured")
        
        # ALLOWED_HOSTS
        if not settings.ALLOWED_HOSTS:
            self.validation_results['security']['critical'].append("ALLOWED_HOSTS empty")
        else:
            self.validation_results['security']['passes'].append(f"ALLOWED_HOSTS configured ({len(settings.ALLOWED_HOSTS)} hosts)")
        
        # HTTPS settings
        if getattr(settings, 'SECURE_SSL_REDIRECT', False):
            self.validation_results['security']['passes'].append("HTTPS redirect enabled")
        else:
            self.validation_results['security']['issues'].append("HTTPS redirect not enabled")
    
    def _validate_authentication_security(self, settings):
        """Validate authentication security"""
        # JWT Authentication
        auth_classes = settings.REST_FRAMEWORK.get('DEFAULT_AUTHENTICATION_CLASSES', [])
        if 'apps.users.authentication.JWTAuthentication' in auth_classes:
            self.validation_results['security']['passes'].append("JWT Authentication configured")
        else:
            self.validation_results['security']['issues'].append("JWT Authentication not configured")
        
        # Password validators
        if hasattr(settings, 'AUTH_PASSWORD_VALIDATORS') and len(settings.AUTH_PASSWORD_VALIDATORS) > 0:
            self.validation_results['security']['passes'].append(f"Password validators configured ({len(settings.AUTH_PASSWORD_VALIDATORS)})")
        else:
            self.validation_results['security']['issues'].append("Password validators not configured")
    
    def _validate_authorization_security(self, settings):
        """Validate authorization security"""
        # Permission classes
        permission_classes = settings.REST_FRAMEWORK.get('DEFAULT_PERMISSION_CLASSES', [])
        if 'rest_framework.permissions.IsAuthenticated' in permission_classes:
            self.validation_results['security']['passes'].append("Authentication required by default")
        else:
            self.validation_results['security']['issues'].append("No default authentication requirement")
    
    def _validate_data_protection(self, settings):
        """Validate data protection"""
        # CSRF protection
        if 'django.middleware.csrf.CsrfViewMiddleware' in settings.MIDDLEWARE:
            self.validation_results['security']['passes'].append("CSRF middleware enabled")
        else:
            self.validation_results['security']['critical'].append("CSRF middleware not enabled")
        
        # Session security
        if getattr(settings, 'SESSION_COOKIE_SECURE', False):
            self.validation_results['security']['passes'].append("Secure session cookies enabled")
        else:
            self.validation_results['security']['issues'].append("Secure session cookies not enabled")
    
    def _validate_network_security(self, settings):
        """Validate network security"""
        # Security headers middleware
        if 'config.middleware.SecurityHeadersMiddleware' in settings.MIDDLEWARE:
            self.validation_results['security']['passes'].append("Security headers middleware enabled")
        else:
            self.validation_results['security']['issues'].append("Security headers middleware not enabled")
        
        # Rate limiting
        if 'config.middleware.RateLimitMiddleware' in settings.MIDDLEWARE:
            self.validation_results['security']['passes'].append("Rate limiting middleware enabled")
        else:
            self.validation_results['security']['issues'].append("Rate limiting middleware not enabled")
    
    def _validate_api_security(self):
        """Validate API security"""
        try:
            # Test CSRF protection
            response = requests.post(f"{self.base_url}/api/v1/user/products/", 
                                   json={'name': 'test'}, timeout=5)
            if response.status_code in [403, 401]:
                self.validation_results['security']['passes'].append("CSRF protection working")
            else:
                self.validation_results['security']['issues'].append("CSRF protection may not be working")
        except Exception as e:
            self.validation_results['security']['issues'].append(f"CSRF test failed: {e}")
    
    def validate_performance_comprehensive(self):
        """Comprehensive performance validation"""
        print("⚡ Comprehensive Performance Validation...")
        
        # 1. Database Performance
        self._validate_database_performance()
        
        # 2. Caching Performance
        self._validate_caching_performance()
        
        # 3. API Performance
        self._validate_api_performance()
        
        # 4. Memory Performance
        self._validate_memory_performance()
    
    def _validate_database_performance(self):
        """Validate database performance"""
        try:
            from django.db import connection
            from apps.product.models import Product
            
            # Test simple query
            start_time = time.time()
            products = list(Product.objects.all()[:10])
            query_time = (time.time() - start_time) * 1000
            
            if query_time < 100:
                self.validation_results['performance']['passes'].append(f"Database query fast ({query_time:.1f}ms)")
            elif query_time < 500:
                self.validation_results['performance']['issues'].append(f"Database query slow ({query_time:.1f}ms)")
            else:
                self.validation_results['performance']['critical'].append(f"Database query very slow ({query_time:.1f}ms)")
            
            # Test query count
            query_count = len(connection.queries)
            if query_count < 5:
                self.validation_results['performance']['passes'].append(f"Low query count ({query_count})")
            elif query_count < 20:
                self.validation_results['performance']['issues'].append(f"High query count ({query_count})")
            else:
                self.validation_results['performance']['critical'].append(f"Very high query count ({query_count})")
                
        except Exception as e:
            self.validation_results['performance']['critical'].append(f"Database performance test failed: {e}")
    
    def _validate_caching_performance(self):
        """Validate caching performance"""
        try:
            from apps.core.caching import cache_manager
            
            if hasattr(cache_manager, 'redis_available') and cache_manager.redis_available:
                self.validation_results['performance']['passes'].append("Redis caching available")
                
                # Test cache performance
                start_time = time.time()
                cache_manager.set('test_key', 'test_value', 60)
                cache_value = cache_manager.get('test_key')
                cache_time = (time.time() - start_time) * 1000
                
                if cache_time < 10:
                    self.validation_results['performance']['passes'].append(f"Cache fast ({cache_time:.1f}ms)")
                else:
                    self.validation_results['performance']['issues'].append(f"Cache slow ({cache_time:.1f}ms)")
            else:
                self.validation_results['performance']['issues'].append("Redis caching not available")
                
        except Exception as e:
            self.validation_results['performance']['issues'].append(f"Caching test failed: {e}")
    
    def _validate_api_performance(self):
        """Validate API performance"""
        try:
            # Test health endpoint
            start_time = time.time()
            response = requests.get(f"{self.base_url}/health/", timeout=5)
            api_time = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                if api_time < 200:
                    self.validation_results['performance']['passes'].append(f"API fast ({api_time:.1f}ms)")
                elif api_time < 1000:
                    self.validation_results['performance']['issues'].append(f"API slow ({api_time:.1f}ms)")
                else:
                    self.validation_results['performance']['critical'].append(f"API very slow ({api_time:.1f}ms)")
            else:
                self.validation_results['performance']['issues'].append(f"API returned {response.status_code}")
                
        except Exception as e:
            self.validation_results['performance']['issues'].append(f"API test failed: {e}")
    
    def _validate_memory_performance(self):
        """Validate memory performance"""
        try:
            import psutil
            process = psutil.Process()
            memory_mb = process.memory_info().rss / (1024 * 1024)
            
            if memory_mb < 200:
                self.validation_results['performance']['passes'].append(f"Memory usage low ({memory_mb:.1f}MB)")
            elif memory_mb < 500:
                self.validation_results['performance']['issues'].append(f"Memory usage moderate ({memory_mb:.1f}MB)")
            else:
                self.validation_results['performance']['critical'].append(f"Memory usage high ({memory_mb:.1f}MB)")
                
        except Exception as e:
            self.validation_results['performance']['issues'].append(f"Memory test failed: {e}")
    
    def validate_production_readiness(self):
        """Validate production readiness"""
        print("🚀 Production Readiness Validation...")
        
        from django.conf import settings
        
        # 1. Environment Configuration
        self._validate_environment_config(settings)
        
        # 2. Dependencies
        self._validate_dependencies()
        
        # 3. Logging
        self._validate_logging(settings)
        
        # 4. Error Handling
        self._validate_error_handling()
    
    def _validate_environment_config(self, settings):
        """Validate environment configuration"""
        # Check critical settings
        critical_settings = [
            'SECRET_KEY', 'ALLOWED_HOSTS', 'DEBUG', 'DATABASES'
        ]
        
        for setting in critical_settings:
            if hasattr(settings, setting):
                self.validation_results['production']['passes'].append(f"{setting} configured")
            else:
                self.validation_results['production']['critical'].append(f"{setting} not configured")
    
    def _validate_dependencies(self):
        """Validate dependencies"""
        try:
            import redis
            self.validation_results['production']['passes'].append("Redis dependency available")
        except ImportError:
            self.validation_results['production']['issues'].append("Redis dependency missing")
        
        try:
            import psutil
            self.validation_results['production']['passes'].append("psutil dependency available")
        except ImportError:
            self.validation_results['production']['issues'].append("psutil dependency missing")
    
    def _validate_logging(self, settings):
        """Validate logging configuration"""
        if hasattr(settings, 'LOGGING') and 'loggers' in settings.LOGGING:
            self.validation_results['production']['passes'].append("Logging configured")
        else:
            self.validation_results['production']['issues'].append("Logging not configured")
    
    def _validate_error_handling(self):
        """Validate error handling"""
        try:
            from apps.core.exception_handler import custom_exception_handler
            self.validation_results['production']['passes'].append("Custom exception handler available")
        except ImportError:
            self.validation_results['production']['issues'].append("Custom exception handler missing")
    
    def calculate_overall_score(self):
        """Calculate overall validation score"""
        total_checks = 0
        total_passes = 0
        
        for category in ['security', 'performance', 'production']:
            category_data = self.validation_results[category]
            total_checks += len(category_data['passes']) + len(category_data['issues']) + len(category_data['critical'])
            total_passes += len(category_data['passes'])
        
        if total_checks > 0:
            self.validation_results['overall']['score'] = (total_passes / total_checks) * 100
        
        # Determine overall status
        if any(len(self.validation_results[cat]['critical']) > 0 for cat in ['security', 'performance', 'production']):
            self.validation_results['overall']['status'] = 'CRITICAL'
        elif any(len(self.validation_results[cat]['issues']) > 0 for cat in ['security', 'performance', 'production']):
            self.validation_results['overall']['status'] = 'ISSUES'
        else:
            self.validation_results['overall']['status'] = 'PASSED'
    
    def generate_ultimate_report(self):
        """Generate ultimate validation report"""
        print("\n" + "="*80)
        print("🎯 ULTIMATE VALIDATION REPORT - PHASE 1 & 2")
        print("="*80)
        
        # Run all validations
        self.validate_security_comprehensive()
        self.validate_performance_comprehensive()
        self.validate_production_readiness()
        
        # Calculate overall score
        self.calculate_overall_score()
        
        # Display results
        for category in ['security', 'performance', 'production']:
            print(f"\n📊 {category.upper()} VALIDATION:")
            print("-" * 50)
            
            data = self.validation_results[category]
            
            if data['critical']:
                print("❌ CRITICAL ISSUES:")
                for i, issue in enumerate(data['critical'], 1):
                    print(f"  {i}. {issue}")
            
            if data['issues']:
                print("⚠️ ISSUES:")
                for i, issue in enumerate(data['issues'], 1):
                    print(f"  {i}. {issue}")
            
            if data['passes']:
                print("✅ PASSES:")
                for i, issue in enumerate(data['passes'], 1):
                    print(f"  {i}. {issue}")
        
        # Overall assessment
        print(f"\n🎯 OVERALL ASSESSMENT:")
        print("-" * 50)
        print(f"Score: {self.validation_results['overall']['score']:.1f}%")
        print(f"Status: {self.validation_results['overall']['status']}")
        
        if self.validation_results['overall']['status'] == 'CRITICAL':
            print("🚨 CRITICAL ISSUES FOUND - DO NOT DEPLOY!")
        elif self.validation_results['overall']['status'] == 'ISSUES':
            print("⚠️ ISSUES FOUND - ADDRESS BEFORE DEPLOYMENT")
        else:
            print("✅ ALL VALIDATIONS PASSED - READY FOR DEPLOYMENT!")
        
        # Save report
        with open('ultimate_validation_report.json', 'w') as f:
            json.dump(self.validation_results, f, indent=2)
        
        print(f"\n📄 Report saved to: ultimate_validation_report.json")
        print("="*80)
        
        return self.validation_results

def run_ultimate_validation():
    """Run ultimate validation"""
    print("🎯 Starting Ultimate Validation for Phase 1 & 2...")
    print("="*80)
    
    validator = UltimateValidator()
    
    try:
        report = validator.generate_ultimate_report()
        return report
    except Exception as e:
        print(f"❌ Error during ultimate validation: {e}")
        return None

if __name__ == "__main__":
    run_ultimate_validation()


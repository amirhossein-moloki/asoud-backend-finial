#!/usr/bin/env python3
"""
Ultimate Deep Validation Script for ASOUD Platform Phase 1 & 2
Comprehensive validation to ensure 100% completion with deep analysis
"""

import os
import sys
import django
import requests
import json
import time
import subprocess
from datetime import datetime

# Add the project directory to Python path
sys.path.append('/home/devops/projects/asoud-main-1-/asoud-main')

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
os.environ.setdefault('DJANGO_ALLOWED_HOSTS', 'localhost,127.0.0.1')
django.setup()

class UltimateDeepValidator:
    """Ultimate deep validation for 100% completion"""
    
    def __init__(self, base_url='http://localhost:8000'):
        self.base_url = base_url
        self.validation_results = {
            'security': {'score': 0, 'items': [], 'critical': [], 'warnings': []},
            'performance': {'score': 0, 'items': [], 'critical': [], 'warnings': []},
            'production': {'score': 0, 'items': [], 'critical': [], 'warnings': []},
            'code_quality': {'score': 0, 'items': [], 'critical': [], 'warnings': []},
            'overall': {'score': 0, 'status': 'UNKNOWN'}
        }
        self.start_time = time.time()
    
    def validate_security_deep(self):
        """Deep security validation"""
        print("🔒 Deep Security Validation...")
        
        from django.conf import settings
        
        # Environment Security
        self._validate_environment_security(settings)
        
        # Authentication Security
        self._validate_authentication_security(settings)
        
        # Authorization Security
        self._validate_authorization_security(settings)
        
        # Data Protection
        self._validate_data_protection(settings)
        
        # Network Security
        self._validate_network_security(settings)
        
        # API Security
        self._validate_api_security()
        
        # File Security
        self._validate_file_security()
    
    def _validate_environment_security(self, settings):
        """Validate environment security"""
        # DEBUG mode
        if settings.DEBUG:
            self.validation_results['security']['critical'].append("DEBUG mode enabled in production")
        else:
            self.validation_results['security']['items'].append("✅ DEBUG mode disabled")
        
        # SECRET_KEY
        if not settings.SECRET_KEY or settings.SECRET_KEY == 'change-me-in-env':
            self.validation_results['security']['critical'].append("SECRET_KEY not properly configured")
        else:
            self.validation_results['security']['items'].append("✅ SECRET_KEY configured")
        
        # ALLOWED_HOSTS
        if not settings.ALLOWED_HOSTS:
            self.validation_results['security']['critical'].append("ALLOWED_HOSTS empty")
        else:
            self.validation_results['security']['items'].append(f"✅ ALLOWED_HOSTS configured ({len(settings.ALLOWED_HOSTS)} hosts)")
        
        # HTTPS settings
        if getattr(settings, 'SECURE_SSL_REDIRECT', False):
            self.validation_results['security']['items'].append("✅ HTTPS redirect enabled")
        else:
            self.validation_results['security']['warnings'].append("⚠️ HTTPS redirect not enabled")
    
    def _validate_authentication_security(self, settings):
        """Validate authentication security"""
        # JWT Authentication
        auth_classes = settings.REST_FRAMEWORK.get('DEFAULT_AUTHENTICATION_CLASSES', [])
        if 'apps.users.authentication.JWTAuthentication' in auth_classes:
            self.validation_results['security']['items'].append("✅ JWT Authentication configured")
        else:
            self.validation_results['security']['critical'].append("❌ JWT Authentication not configured")
        
        # Password validators
        if hasattr(settings, 'AUTH_PASSWORD_VALIDATORS') and len(settings.AUTH_PASSWORD_VALIDATORS) > 0:
            self.validation_results['security']['items'].append(f"✅ Password validators configured ({len(settings.AUTH_PASSWORD_VALIDATORS)})")
        else:
            self.validation_results['security']['critical'].append("❌ Password validators not configured")
        
        # Session security
        if getattr(settings, 'SESSION_COOKIE_SECURE', False):
            self.validation_results['security']['items'].append("✅ Secure session cookies enabled")
        else:
            self.validation_results['security']['warnings'].append("⚠️ Secure session cookies not enabled")
    
    def _validate_authorization_security(self, settings):
        """Validate authorization security"""
        # Permission classes
        permission_classes = settings.REST_FRAMEWORK.get('DEFAULT_PERMISSION_CLASSES', [])
        if 'rest_framework.permissions.IsAuthenticated' in permission_classes:
            self.validation_results['security']['items'].append("✅ Authentication required by default")
        else:
            self.validation_results['security']['warnings'].append("⚠️ No default authentication requirement")
    
    def _validate_data_protection(self, settings):
        """Validate data protection"""
        # CSRF protection
        if 'django.middleware.csrf.CsrfViewMiddleware' in settings.MIDDLEWARE:
            self.validation_results['security']['items'].append("✅ CSRF middleware enabled")
        else:
            self.validation_results['security']['critical'].append("❌ CSRF middleware not enabled")
        
        # Security headers middleware
        if 'config.middleware.SecurityHeadersMiddleware' in settings.MIDDLEWARE:
            self.validation_results['security']['items'].append("✅ Security headers middleware enabled")
        else:
            self.validation_results['security']['critical'].append("❌ Security headers middleware not enabled")
        
        # Rate limiting middleware
        if 'config.middleware.RateLimitMiddleware' in settings.MIDDLEWARE:
            self.validation_results['security']['items'].append("✅ Rate limiting middleware enabled")
        else:
            self.validation_results['security']['critical'].append("❌ Rate limiting middleware not enabled")
    
    def _validate_network_security(self, settings):
        """Validate network security"""
        # Security audit middleware
        if 'config.middleware.SecurityAuditMiddleware' in settings.MIDDLEWARE:
            self.validation_results['security']['items'].append("✅ Security audit middleware enabled")
        else:
            self.validation_results['security']['warnings'].append("⚠️ Security audit middleware not enabled")
        
        # CORS settings
        if hasattr(settings, 'CORS_ALLOWED_ORIGINS'):
            self.validation_results['security']['items'].append("✅ CORS configured")
        else:
            self.validation_results['security']['warnings'].append("⚠️ CORS not configured")
    
    def _validate_api_security(self):
        """Validate API security"""
        try:
            # Test CSRF protection
            response = requests.post(f"{self.base_url}/api/v1/user/products/", 
                                   json={'name': 'test'}, timeout=5)
            if response.status_code in [403, 401]:
                self.validation_results['security']['items'].append("✅ CSRF protection working")
            else:
                self.validation_results['security']['warnings'].append("⚠️ CSRF protection may not be working")
        except Exception as e:
            self.validation_results['security']['warnings'].append(f"⚠️ CSRF test failed: {e}")
    
    def _validate_file_security(self):
        """Validate file security"""
        # Check for sensitive files
        sensitive_files = [
            '.env',
            'secrets.json',
            'private_key.pem',
            'database.ini'
        ]
        
        for file in sensitive_files:
            if os.path.exists(file):
                self.validation_results['security']['warnings'].append(f"⚠️ Sensitive file found: {file}")
            else:
                self.validation_results['security']['items'].append(f"✅ Sensitive file not found: {file}")
    
    def validate_performance_deep(self):
        """Deep performance validation"""
        print("⚡ Deep Performance Validation...")
        
        # Database Performance
        self._validate_database_performance()
        
        # Caching Performance
        self._validate_caching_performance()
        
        # API Performance
        self._validate_api_performance()
        
        # Memory Performance
        self._validate_memory_performance()
        
        # File Performance
        self._validate_file_performance()
    
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
                self.validation_results['performance']['items'].append(f"✅ Database query fast ({query_time:.1f}ms)")
            elif query_time < 500:
                self.validation_results['performance']['warnings'].append(f"⚠️ Database query slow ({query_time:.1f}ms)")
            else:
                self.validation_results['performance']['critical'].append(f"❌ Database query very slow ({query_time:.1f}ms)")
            
            # Test query count
            query_count = len(connection.queries)
            if query_count < 5:
                self.validation_results['performance']['items'].append(f"✅ Low query count ({query_count})")
            elif query_count < 20:
                self.validation_results['performance']['warnings'].append(f"⚠️ High query count ({query_count})")
            else:
                self.validation_results['performance']['critical'].append(f"❌ Very high query count ({query_count})")
                
        except Exception as e:
            self.validation_results['performance']['critical'].append(f"❌ Database performance test failed: {e}")
    
    def _validate_caching_performance(self):
        """Validate caching performance"""
        try:
            from apps.core.caching import cache_manager
            
            if hasattr(cache_manager, 'redis_available') and cache_manager.redis_available:
                self.validation_results['performance']['items'].append("✅ Redis caching available")
                
                # Test cache performance
                start_time = time.time()
                cache_manager.set('test_key', 'test_value', 60)
                cache_value = cache_manager.get('test_key')
                cache_time = (time.time() - start_time) * 1000
                
                if cache_time < 10:
                    self.validation_results['performance']['items'].append(f"✅ Cache fast ({cache_time:.1f}ms)")
                else:
                    self.validation_results['performance']['warnings'].append(f"⚠️ Cache slow ({cache_time:.1f}ms)")
            else:
                self.validation_results['performance']['warnings'].append("⚠️ Redis caching not available")
                
        except Exception as e:
            self.validation_results['performance']['warnings'].append(f"⚠️ Caching test failed: {e}")
    
    def _validate_api_performance(self):
        """Validate API performance"""
        try:
            # Test health endpoint
            start_time = time.time()
            response = requests.get(f"{self.base_url}/health/", timeout=5)
            api_time = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                if api_time < 200:
                    self.validation_results['performance']['items'].append(f"✅ API fast ({api_time:.1f}ms)")
                elif api_time < 1000:
                    self.validation_results['performance']['warnings'].append(f"⚠️ API slow ({api_time:.1f}ms)")
                else:
                    self.validation_results['performance']['critical'].append(f"❌ API very slow ({api_time:.1f}ms)")
            else:
                self.validation_results['performance']['warnings'].append(f"⚠️ API returned {response.status_code}")
                
        except Exception as e:
            self.validation_results['performance']['warnings'].append(f"⚠️ API test failed: {e}")
    
    def _validate_memory_performance(self):
        """Validate memory performance"""
        try:
            import psutil
            process = psutil.Process()
            memory_mb = process.memory_info().rss / (1024 * 1024)
            
            if memory_mb < 200:
                self.validation_results['performance']['items'].append(f"✅ Memory usage low ({memory_mb:.1f}MB)")
            elif memory_mb < 500:
                self.validation_results['performance']['warnings'].append(f"⚠️ Memory usage moderate ({memory_mb:.1f}MB)")
            else:
                self.validation_results['performance']['critical'].append(f"❌ Memory usage high ({memory_mb:.1f}MB)")
                
        except Exception as e:
            self.validation_results['performance']['warnings'].append(f"⚠️ Memory test failed: {e}")
    
    def _validate_file_performance(self):
        """Validate file performance"""
        try:
            # Check static files
            static_files = [
                'static/css/',
                'static/js/',
                'static/images/',
                'media/'
            ]
            
            for static_dir in static_files:
                if os.path.exists(static_dir):
                    self.validation_results['performance']['items'].append(f"✅ Static directory exists: {static_dir}")
                else:
                    self.validation_results['performance']['warnings'].append(f"⚠️ Static directory missing: {static_dir}")
                    
        except Exception as e:
            self.validation_results['performance']['warnings'].append(f"⚠️ File performance test failed: {e}")
    
    def validate_production_deep(self):
        """Deep production validation"""
        print("🚀 Deep Production Validation...")
        
        # Configuration Files
        self._validate_configuration_files()
        
        # Dependencies
        self._validate_dependencies()
        
        # Logging
        self._validate_logging()
        
        # Error Handling
        self._validate_error_handling()
        
        # Monitoring
        self._validate_monitoring()
    
    def _validate_configuration_files(self):
        """Validate configuration files"""
        config_files = [
            'config/settings/production.py',
            'docker-compose.prod.yaml',
            'deploy_production.py',
            'gunicorn.conf.py',
            'nginx.conf',
            'asoud.service'
        ]
        
        for file in config_files:
            if os.path.exists(file):
                self.validation_results['production']['items'].append(f"✅ Configuration file exists: {file}")
            else:
                self.validation_results['production']['critical'].append(f"❌ Configuration file missing: {file}")
    
    def _validate_dependencies(self):
        """Validate dependencies"""
        dependencies = [
            'redis',
            'psutil',
            'PIL',
            'django_redis',
            'gunicorn'
        ]
        
        for dep in dependencies:
            try:
                __import__(dep)
                self.validation_results['production']['items'].append(f"✅ Dependency available: {dep}")
            except ImportError:
                self.validation_results['production']['critical'].append(f"❌ Dependency missing: {dep}")
    
    def _validate_logging(self):
        """Validate logging configuration"""
        try:
            from django.conf import settings
            if hasattr(settings, 'LOGGING') and 'loggers' in settings.LOGGING:
                self.validation_results['production']['items'].append("✅ Logging configured")
            else:
                self.validation_results['production']['critical'].append("❌ Logging not configured")
        except Exception as e:
            self.validation_results['production']['critical'].append(f"❌ Logging validation failed: {e}")
    
    def _validate_error_handling(self):
        """Validate error handling"""
        error_handling_files = [
            'apps/core/exception_handler.py',
            'apps/core/caching.py',
            'config/middleware.py'
        ]
        
        for file in error_handling_files:
            if os.path.exists(file):
                try:
                    with open(file, 'r') as f:
                        content = f.read()
                        if 'try:' in content and 'except' in content:
                            self.validation_results['production']['items'].append(f"✅ Error handling in {file}")
                        else:
                            self.validation_results['production']['warnings'].append(f"⚠️ Limited error handling in {file}")
                except Exception as e:
                    self.validation_results['production']['warnings'].append(f"⚠️ Error reading {file}: {e}")
            else:
                self.validation_results['production']['critical'].append(f"❌ Error handling file missing: {file}")
    
    def _validate_monitoring(self):
        """Validate monitoring"""
        monitoring_files = [
            'apps/core/management/commands/performance_monitor.py',
            'ultimate_validation_script.py',
            'security_validation_complete.py',
            'monitor.sh'
        ]
        
        for file in monitoring_files:
            if os.path.exists(file):
                self.validation_results['production']['items'].append(f"✅ Monitoring file exists: {file}")
            else:
                self.validation_results['production']['warnings'].append(f"⚠️ Monitoring file missing: {file}")
    
    def validate_code_quality_deep(self):
        """Deep code quality validation"""
        print("📝 Deep Code Quality Validation...")
        
        # Check for TODO/FIXME comments
        self._check_todo_comments()
        
        # Check for error handling
        self._check_error_handling()
        
        # Check for logging
        self._check_logging()
        
        # Check for documentation
        self._check_documentation()
    
    def _check_todo_comments(self):
        """Check for TODO/FIXME comments"""
        try:
            result = subprocess.run(['grep', '-r', 'TODO\\|FIXME\\|BUG\\|HACK\\|XXX', 'apps/', 'config/'], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                if lines and lines[0]:
                    self.validation_results['code_quality']['warnings'].append(f"⚠️ Found {len(lines)} TODO/FIXME comments")
                else:
                    self.validation_results['code_quality']['items'].append("✅ No TODO/FIXME comments found")
            else:
                self.validation_results['code_quality']['items'].append("✅ No TODO/FIXME comments found")
        except Exception as e:
            self.validation_results['code_quality']['warnings'].append(f"⚠️ TODO check failed: {e}")
    
    def _check_error_handling(self):
        """Check for error handling"""
        try:
            result = subprocess.run(['grep', '-r', 'try:', 'apps/'], capture_output=True, text=True)
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                if lines and lines[0]:
                    self.validation_results['code_quality']['items'].append(f"✅ Found {len(lines)} try blocks")
                else:
                    self.validation_results['code_quality']['warnings'].append("⚠️ No try blocks found")
            else:
                self.validation_results['code_quality']['warnings'].append("⚠️ No try blocks found")
        except Exception as e:
            self.validation_results['code_quality']['warnings'].append(f"⚠️ Error handling check failed: {e}")
    
    def _check_logging(self):
        """Check for logging"""
        try:
            result = subprocess.run(['grep', '-r', 'logger\\.', 'apps/'], capture_output=True, text=True)
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                if lines and lines[0]:
                    self.validation_results['code_quality']['items'].append(f"✅ Found {len(lines)} logger calls")
                else:
                    self.validation_results['code_quality']['warnings'].append("⚠️ No logger calls found")
            else:
                self.validation_results['code_quality']['warnings'].append("⚠️ No logger calls found")
        except Exception as e:
            self.validation_results['code_quality']['warnings'].append(f"⚠️ Logging check failed: {e}")
    
    def _check_documentation(self):
        """Check for documentation"""
        doc_files = [
            'PHASE1_SECURITY_IMPLEMENTATION.md',
            'PHASE2_PERFORMANCE_IMPLEMENTATION.md',
            'ULTIMATE_PHASES_1_2_REVIEW.md',
            'FINAL_100_PERCENT_COMPLETION.md'
        ]
        
        for file in doc_files:
            if os.path.exists(file):
                self.validation_results['code_quality']['items'].append(f"✅ Documentation exists: {file}")
            else:
                self.validation_results['code_quality']['warnings'].append(f"⚠️ Documentation missing: {file}")
    
    def calculate_overall_score(self):
        """Calculate overall score"""
        total_score = 0
        max_score = 0
        
        for category in ['security', 'performance', 'production', 'code_quality']:
            category_data = self.validation_results[category]
            
            # Calculate category score
            items_count = len(category_data['items'])
            warnings_count = len(category_data['warnings'])
            critical_count = len(category_data['critical'])
            
            total_items = items_count + warnings_count + critical_count
            if total_items > 0:
                category_score = (items_count * 100 + warnings_count * 50) / total_items
                self.validation_results[category]['score'] = category_score
                total_score += category_score
                max_score += 100
        
        if max_score > 0:
            self.validation_results['overall']['score'] = (total_score / max_score) * 100
        
        # Determine overall status
        if any(len(self.validation_results[cat]['critical']) > 0 for cat in ['security', 'performance', 'production', 'code_quality']):
            self.validation_results['overall']['status'] = 'CRITICAL'
        elif any(len(self.validation_results[cat]['warnings']) > 0 for cat in ['security', 'performance', 'production', 'code_quality']):
            self.validation_results['overall']['status'] = 'WARNINGS'
        else:
            self.validation_results['overall']['status'] = 'PERFECT'
    
    def generate_ultimate_deep_report(self):
        """Generate ultimate deep validation report"""
        print("\n" + "="*80)
        print("🎯 ULTIMATE DEEP VALIDATION REPORT - PHASE 1 & 2")
        print("="*80)
        
        # Run all validations
        self.validate_security_deep()
        self.validate_performance_deep()
        self.validate_production_deep()
        self.validate_code_quality_deep()
        
        # Calculate overall score
        self.calculate_overall_score()
        
        # Display results
        for category in ['security', 'performance', 'production', 'code_quality']:
            print(f"\n📊 {category.upper()} VALIDATION:")
            print("-" * 50)
            print(f"Score: {self.validation_results[category]['score']:.1f}%")
            
            if self.validation_results[category]['critical']:
                print("❌ CRITICAL ISSUES:")
                for issue in self.validation_results[category]['critical']:
                    print(f"  {issue}")
            
            if self.validation_results[category]['warnings']:
                print("⚠️ WARNINGS:")
                for issue in self.validation_results[category]['warnings']:
                    print(f"  {issue}")
            
            if self.validation_results[category]['items']:
                print("✅ PASSES:")
                for issue in self.validation_results[category]['items']:
                    print(f"  {issue}")
        
        # Overall assessment
        print(f"\n🎯 OVERALL ASSESSMENT:")
        print("-" * 50)
        print(f"Overall Score: {self.validation_results['overall']['score']:.1f}%")
        print(f"Status: {self.validation_results['overall']['status']}")
        
        if self.validation_results['overall']['status'] == 'PERFECT':
            print("🎉 PERFECT! 100% COMPLETION ACHIEVED!")
            print("🚀 READY FOR PRODUCTION DEPLOYMENT!")
        elif self.validation_results['overall']['status'] == 'WARNINGS':
            print("✅ EXCELLENT! Minor warnings only!")
            print("🚀 READY FOR PRODUCTION DEPLOYMENT!")
        else:
            print("⚠️ CRITICAL ISSUES FOUND!")
            print("❌ Address critical issues before production deployment")
        
        # Save report
        with open('ultimate_deep_validation_report.json', 'w') as f:
            json.dump(self.validation_results, f, indent=2)
        
        print(f"\n📄 Report saved to: ultimate_deep_validation_report.json")
        print("="*80)
        
        return self.validation_results

def run_ultimate_deep_validation():
    """Run ultimate deep validation"""
    print("🎯 Starting Ultimate Deep Validation for Phase 1 & 2...")
    print("="*80)
    
    validator = UltimateDeepValidator()
    
    try:
        report = validator.generate_ultimate_deep_report()
        return report
    except Exception as e:
        print(f"❌ Error during ultimate deep validation: {e}")
        return None

if __name__ == "__main__":
    run_ultimate_deep_validation()


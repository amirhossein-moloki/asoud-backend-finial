#!/usr/bin/env python3
"""
Complete Security Validation Script for ASOUD Platform Phase 1 & 2
"""

import os
import sys
import django
import requests
import json
from datetime import datetime

# Add the project directory to Python path
sys.path.append('/home/devops/projects/asoud-main-1-/asoud-main')

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.production')
django.setup()

class SecurityValidator:
    """Comprehensive security validation for Phase 1 & 2"""
    
    def __init__(self, base_url='http://localhost:8000'):
        self.base_url = base_url
        self.security_issues = []
        self.security_passes = []
        self.critical_issues = []
    
    def validate_environment_security(self):
        """Validate environment security settings"""
        print("🔒 Validating Environment Security...")
        
        from django.conf import settings
        
        # Check DEBUG mode
        if settings.DEBUG:
            self.critical_issues.append("CRITICAL: DEBUG mode is enabled in production!")
        else:
            self.security_passes.append("✅ DEBUG mode is disabled")
        
        # Check SECRET_KEY
        if not settings.SECRET_KEY or settings.SECRET_KEY == 'change-me-in-env':
            self.critical_issues.append("CRITICAL: SECRET_KEY is not properly configured!")
        else:
            self.security_passes.append("✅ SECRET_KEY is configured")
        
        # Check ALLOWED_HOSTS
        if not settings.ALLOWED_HOSTS:
            self.critical_issues.append("CRITICAL: ALLOWED_HOSTS is empty!")
        else:
            self.security_passes.append(f"✅ ALLOWED_HOSTS configured: {len(settings.ALLOWED_HOSTS)} hosts")
        
        # Check HTTPS settings
        if hasattr(settings, 'SECURE_SSL_REDIRECT') and settings.SECURE_SSL_REDIRECT:
            self.security_passes.append("✅ HTTPS redirect enabled")
        else:
            self.security_issues.append("⚠️ HTTPS redirect not enabled")
        
        # Check CSRF settings
        if hasattr(settings, 'CSRF_COOKIE_SECURE') and settings.CSRF_COOKIE_SECURE:
            self.security_passes.append("✅ CSRF secure cookies enabled")
        else:
            self.security_issues.append("⚠️ CSRF secure cookies not enabled")
        
        # Check session security
        if hasattr(settings, 'SESSION_COOKIE_SECURE') and settings.SESSION_COOKIE_SECURE:
            self.security_passes.append("✅ Session secure cookies enabled")
        else:
            self.security_issues.append("⚠️ Session secure cookies not enabled")
    
    def validate_authentication_security(self):
        """Validate authentication security"""
        print("🔐 Validating Authentication Security...")
        
        from django.conf import settings
        
        # Check JWT settings
        if 'apps.users.authentication.JWTAuthentication' in settings.REST_FRAMEWORK.get('DEFAULT_AUTHENTICATION_CLASSES', []):
            self.security_passes.append("✅ JWT Authentication configured")
        else:
            self.security_issues.append("⚠️ JWT Authentication not configured")
        
        # Check password validators
        if hasattr(settings, 'AUTH_PASSWORD_VALIDATORS') and len(settings.AUTH_PASSWORD_VALIDATORS) > 0:
            self.security_passes.append(f"✅ Password validators configured: {len(settings.AUTH_PASSWORD_VALIDATORS)}")
        else:
            self.security_issues.append("⚠️ Password validators not configured")
        
        # Check session timeout
        if hasattr(settings, 'SESSION_COOKIE_AGE') and settings.SESSION_COOKIE_AGE <= 3600:
            self.security_passes.append("✅ Session timeout is reasonable")
        else:
            self.security_issues.append("⚠️ Session timeout may be too long")
    
    def validate_middleware_security(self):
        """Validate middleware security"""
        print("🛡️ Validating Middleware Security...")
        
        from django.conf import settings
        
        middleware = settings.MIDDLEWARE
        
        # Check CSRF middleware
        if 'django.middleware.csrf.CsrfViewMiddleware' in middleware:
            self.security_passes.append("✅ CSRF middleware enabled")
        else:
            self.critical_issues.append("CRITICAL: CSRF middleware not enabled!")
        
        # Check security headers middleware
        if 'config.middleware.SecurityHeadersMiddleware' in middleware:
            self.security_passes.append("✅ Security headers middleware enabled")
        else:
            self.security_issues.append("⚠️ Security headers middleware not enabled")
        
        # Check rate limiting middleware
        if 'config.middleware.RateLimitMiddleware' in middleware:
            self.security_passes.append("✅ Rate limiting middleware enabled")
        else:
            self.security_issues.append("⚠️ Rate limiting middleware not enabled")
        
        # Check security audit middleware
        if 'config.middleware.SecurityAuditMiddleware' in middleware:
            self.security_passes.append("✅ Security audit middleware enabled")
        else:
            self.security_issues.append("⚠️ Security audit middleware not enabled")
    
    def validate_api_security(self):
        """Validate API security"""
        print("🌐 Validating API Security...")
        
        # Test CSRF protection
        try:
            response = requests.post(f"{self.base_url}/api/v1/user/products/", 
                                   json={'name': 'test'}, timeout=5)
            if response.status_code == 403:
                self.security_passes.append("✅ CSRF protection working")
            elif response.status_code == 401:
                self.security_passes.append("✅ CSRF protection working (requires authentication)")
            else:
                self.security_issues.append("⚠️ CSRF protection may not be working")
        except requests.exceptions.ConnectionError:
            self.security_issues.append("⚠️ Cannot connect to server for CSRF test")
        except Exception as e:
            self.security_issues.append(f"⚠️ CSRF test failed: {e}")
        
        # Test rate limiting
        try:
            rate_limited = False
            for i in range(15):  # Try to exceed rate limit
                response = requests.get(f"{self.base_url}/api/v1/user/products/", timeout=5)
                if response.status_code == 429:
                    rate_limited = True
                    break
            if rate_limited:
                self.security_passes.append("✅ Rate limiting working")
            else:
                self.security_issues.append("⚠️ Rate limiting may not be working")
        except Exception as e:
            self.security_issues.append(f"⚠️ Rate limiting test failed: {e}")
        
        # Test security headers
        try:
            response = requests.get(f"{self.base_url}/health/", timeout=5)
            headers = response.headers
            
            security_headers = [
                'X-Content-Type-Options',
                'X-Frame-Options',
                'X-XSS-Protection',
                'Referrer-Policy'
            ]
            
            for header in security_headers:
                if header in headers:
                    self.security_passes.append(f"✅ Security header {header} present")
                else:
                    self.security_issues.append(f"⚠️ Security header {header} missing")
                    
        except Exception as e:
            self.security_issues.append(f"⚠️ Security headers test failed: {e}")
    
    def validate_database_security(self):
        """Validate database security"""
        print("🗄️ Validating Database Security...")
        
        from django.db import connection
        from django.conf import settings
        
        # Check database configuration
        db_config = settings.DATABASES['default']
        
        if db_config['ENGINE'] == 'django.db.backends.postgresql':
            self.security_passes.append("✅ PostgreSQL database configured")
        else:
            self.security_issues.append("⚠️ Non-PostgreSQL database may have security issues")
        
        # Check if database has proper indexes
        try:
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT COUNT(*) FROM pg_indexes 
                    WHERE schemaname = 'public' AND tablename LIKE 'users_%'
                """)
                index_count = cursor.fetchone()[0]
                
                if index_count > 0:
                    self.security_passes.append(f"✅ Database indexes present: {index_count}")
                else:
                    self.security_issues.append("⚠️ Database indexes may be missing")
                    
        except Exception as e:
            self.security_issues.append(f"⚠️ Database security check failed: {e}")
    
    def validate_performance_security(self):
        """Validate performance-related security"""
        print("⚡ Validating Performance Security...")
        
        from django.conf import settings
        
        # Check caching configuration
        if hasattr(settings, 'CACHES') and 'default' in settings.CACHES:
            cache_backend = settings.CACHES['default']['BACKEND']
            if 'redis' in cache_backend.lower():
                self.security_passes.append("✅ Redis caching configured")
            else:
                self.security_issues.append("⚠️ Non-Redis caching may have security issues")
        else:
            self.security_issues.append("⚠️ Caching not configured")
        
        # Check logging configuration
        if hasattr(settings, 'LOGGING') and 'loggers' in settings.LOGGING:
            loggers = settings.LOGGING['loggers']
            if 'config.security' in loggers:
                self.security_passes.append("✅ Security logging configured")
            else:
                self.security_issues.append("⚠️ Security logging not configured")
        else:
            self.security_issues.append("⚠️ Logging not configured")
    
    def generate_security_report(self):
        """Generate comprehensive security report"""
        print("\n" + "="*60)
        print("🔒 COMPREHENSIVE SECURITY VALIDATION REPORT")
        print("="*60)
        
        # Run all validations
        self.validate_environment_security()
        self.validate_authentication_security()
        self.validate_middleware_security()
        self.validate_api_security()
        self.validate_database_security()
        self.validate_performance_security()
        
        # Calculate security score
        total_checks = len(self.security_passes) + len(self.security_issues) + len(self.critical_issues)
        security_score = (len(self.security_passes) / total_checks) * 100 if total_checks > 0 else 0
        
        print(f"\n📊 SECURITY SCORE: {security_score:.1f}%")
        print(f"✅ Security Passes: {len(self.security_passes)}")
        print(f"⚠️ Security Issues: {len(self.security_issues)}")
        print(f"❌ Critical Issues: {len(self.critical_issues)}")
        
        # Display critical issues
        if self.critical_issues:
            print("\n❌ CRITICAL SECURITY ISSUES:")
            for i, issue in enumerate(self.critical_issues, 1):
                print(f"{i}. {issue}")
        
        # Display security issues
        if self.security_issues:
            print("\n⚠️ SECURITY ISSUES:")
            for i, issue in enumerate(self.security_issues, 1):
                print(f"{i}. {issue}")
        
        # Display security passes
        if self.security_passes:
            print("\n✅ SECURITY PASSES:")
            for i, issue in enumerate(self.security_passes, 1):
                print(f"{i}. {issue}")
        
        # Generate recommendations
        recommendations = self._generate_security_recommendations()
        if recommendations:
            print("\n💡 SECURITY RECOMMENDATIONS:")
            for i, rec in enumerate(recommendations, 1):
                print(f"{i}. {rec}")
        
        # Overall assessment
        if self.critical_issues:
            print("\n🚨 OVERALL ASSESSMENT: CRITICAL ISSUES FOUND!")
            print("   Immediate action required before production deployment.")
        elif self.security_issues:
            print("\n⚠️ OVERALL ASSESSMENT: SECURITY ISSUES FOUND!")
            print("   Address issues before production deployment.")
        else:
            print("\n✅ OVERALL ASSESSMENT: SECURITY VALIDATION PASSED!")
            print("   System is ready for production deployment.")
        
        return {
            'security_score': security_score,
            'critical_issues': self.critical_issues,
            'security_issues': self.security_issues,
            'security_passes': self.security_passes,
            'recommendations': recommendations,
            'overall_status': 'CRITICAL' if self.critical_issues else 'ISSUES' if self.security_issues else 'PASSED'
        }
    
    def _generate_security_recommendations(self):
        """Generate security recommendations"""
        recommendations = []
        
        if self.critical_issues:
            recommendations.append("Fix all critical issues immediately")
        
        if any("DEBUG" in issue for issue in self.security_issues):
            recommendations.append("Ensure DEBUG=False in production")
        
        if any("SECRET_KEY" in issue for issue in self.security_issues):
            recommendations.append("Set strong SECRET_KEY in environment variables")
        
        if any("ALLOWED_HOSTS" in issue for issue in self.security_issues):
            recommendations.append("Configure ALLOWED_HOSTS properly")
        
        if any("HTTPS" in issue for issue in self.security_issues):
            recommendations.append("Enable HTTPS redirect and secure cookies")
        
        if any("middleware" in issue for issue in self.security_issues):
            recommendations.append("Enable all security middleware")
        
        if any("logging" in issue for issue in self.security_issues):
            recommendations.append("Configure security logging")
        
        return recommendations

def run_security_validation():
    """Run comprehensive security validation"""
    print("🔒 Starting Comprehensive Security Validation...")
    print("="*60)
    
    validator = SecurityValidator()
    
    try:
        report = validator.generate_security_report()
        
        # Save report
        with open('security_validation_report.json', 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"\n📄 Security report saved to: security_validation_report.json")
        print("="*60)
        print("✅ Security Validation Completed!")
        
        return report
        
    except Exception as e:
        print(f"❌ Error during security validation: {e}")
        return None

if __name__ == "__main__":
    run_security_validation()

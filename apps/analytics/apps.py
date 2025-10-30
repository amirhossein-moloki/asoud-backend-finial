"""
Analytics App Configuration
"""

from django.apps import AppConfig


class AnalyticsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.analytics'
    verbose_name = 'Analytics & Machine Learning'
    
    def ready(self):
        """Import signal handlers when the app is ready"""
        try:
            import apps.analytics.signals
        except ImportError:
            pass


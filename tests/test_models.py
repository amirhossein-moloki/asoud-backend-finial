
from django.test import TestCase
from apps.analytics.models import UserBehaviorEvent

class AnalyticsTestCase(TestCase):
    def test_create_user_behavior_event(self):
        UserBehaviorEvent.objects.create(
            session_id='test_session',
            event_type='page_view',
            page_url='https://example.com',
        )
        self.assertEqual(UserBehaviorEvent.objects.count(), 1)

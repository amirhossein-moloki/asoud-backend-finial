import json
import os
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
from apps.market.models import Market

@receiver(post_save, sender=Market)
def add_market_url_to_allowed_hosts(sender, instance, created, **kwargs):
    if created:
        pass
    elif not created and instance.status == 'published':
        if not instance.business_id:
            return
        domain = (instance.business_id).lower() + '.' + 'asoud.ir'
        if domain in settings.ALLOWED_HOSTS:
            return
        
        new_allowed_hosts = settings.ALLOWED_HOSTS + [domain]
        
        settings.ALLOWED_HOSTS = new_allowed_hosts
        ALLOWED_HOSTS_FILE = os.path.join(settings.BASE_DIR, 'allowed_hosts.json')
        with open(ALLOWED_HOSTS_FILE, 'w') as f:
            json.dump(new_allowed_hosts, f)

import json
import os
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.conf import settings
from apps.market.models import Market

@receiver(pre_save, sender=Market)
def generate_subdomain_on_save(sender, instance, **kwargs):
    """Generate subdomain automatically when market is saved"""
    if not instance.subdomain:
        instance.generate_subdomain()

@receiver(post_save, sender=Market)
def add_market_url_to_allowed_hosts(sender, instance, created, **kwargs):
    """Add market subdomain to allowed hosts when published"""
    if created:
        pass
    elif not created and instance.status == 'published':
        # Handle both business_id and subdomain
        domains_to_add = []
        
        if instance.business_id:
            domain = (instance.business_id).lower() + '.' + 'asoud.ir'
            domains_to_add.append(domain)
        
        if instance.subdomain:
            subdomain = instance.subdomain.lower() + '.' + 'asoud.ir'
            domains_to_add.append(subdomain)
            # Also add .com version
            subdomain_com = instance.subdomain.lower() + '.' + 'asoud.com'
            domains_to_add.append(subdomain_com)
        
        # Add new domains to ALLOWED_HOSTS
        new_allowed_hosts = list(settings.ALLOWED_HOSTS)
        for domain in domains_to_add:
            if domain not in new_allowed_hosts:
                new_allowed_hosts.append(domain)
        
        if new_allowed_hosts != settings.ALLOWED_HOSTS:
            settings.ALLOWED_HOSTS = new_allowed_hosts
            ALLOWED_HOSTS_FILE = os.path.join(settings.BASE_DIR, 'allowed_hosts.json')
            with open(ALLOWED_HOSTS_FILE, 'w') as f:
                json.dump(new_allowed_hosts, f)

#!/usr/bin/env python
"""
Endpoint Analysis Script for ASOUD Platform
Compares Django URL patterns with Postman collection endpoints
"""

import os
import sys
import django
import json
from django.conf import settings
from django.urls import get_resolver
from django.urls.resolvers import URLPattern, URLResolver

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
sys.path.append('.')
django.setup()

def extract_all_patterns(urlpatterns, prefix=''):
    """Recursively extract all URL patterns"""
    patterns = []
    for pattern in urlpatterns:
        if isinstance(pattern, URLResolver):
            new_prefix = prefix + str(pattern.pattern)
            patterns.extend(extract_all_patterns(pattern.url_patterns, new_prefix))
        elif isinstance(pattern, URLPattern):
            full_path = prefix + str(pattern.pattern)
            patterns.append({
                'path': full_path,
                'name': pattern.name,
                'callback': str(pattern.callback)
            })
    return patterns

def load_postman_collection():
    """Load and parse Postman collection"""
    try:
        with open('ASOUD_Complete_Postman_Collection_252_Endpoints_FINAL.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print("Postman collection file not found!")
        return None

def extract_postman_endpoints(collection, endpoints=None, prefix=''):
    """Extract endpoints from Postman collection recursively"""
    if endpoints is None:
        endpoints = []
    
    if isinstance(collection, dict):
        if 'item' in collection:
            for item in collection['item']:
                extract_postman_endpoints(item, endpoints, prefix)
        elif 'request' in collection:
            # This is an endpoint
            request = collection['request']
            if 'url' in request:
                url = request['url']
                if isinstance(url, dict) and 'path' in url:
                    path = '/'.join(url['path'])
                    method = request.get('method', 'GET')
                    name = collection.get('name', 'Unknown')
                    endpoints.append({
                        'name': name,
                        'method': method,
                        'path': path,
                        'full_url': f"/{path}"
                    })
    elif isinstance(collection, list):
        for item in collection:
            extract_postman_endpoints(item, endpoints, prefix)
    
    return endpoints

def main():
    print('=== ASOUD ENDPOINT ANALYSIS ===')
    print()
    
    # Get Django URL patterns
    resolver = get_resolver()
    django_patterns = extract_all_patterns(resolver.url_patterns)
    
    print(f'Django patterns found: {len(django_patterns)}')
    
    # Group Django patterns
    api_v1_patterns = [p for p in django_patterns if 'api/v1/' in p['path']]
    other_patterns = [p for p in django_patterns if 'api/v1/' not in p['path']]
    
    print(f'API v1 patterns: {len(api_v1_patterns)}')
    print(f'Other patterns: {len(other_patterns)}')
    print()
    
    # Load Postman collection
    postman_collection = load_postman_collection()
    if postman_collection:
        postman_endpoints = extract_postman_endpoints(postman_collection)
        print(f'Postman endpoints found: {len(postman_endpoints)}')
        print()
        
        # Print API v1 endpoints comparison
        print('=== API V1 DJANGO ENDPOINTS ===')
        for pattern in sorted(api_v1_patterns, key=lambda x: x['path']):
            clean_path = pattern['path'].replace('^', '').replace('$', '')
            print(f'{clean_path}')
        
        print()
        print('=== POSTMAN ENDPOINTS (API V1) ===')
        api_v1_postman = [e for e in postman_endpoints if 'api/v1/' in e['path']]
        for endpoint in sorted(api_v1_postman, key=lambda x: x['path']):
            print(f"{endpoint['method']} /{endpoint['path']} - {endpoint['name']}")
        
        print()
        print(f'Django API v1 endpoints: {len(api_v1_patterns)}')
        print(f'Postman API v1 endpoints: {len(api_v1_postman)}')
        
        # Save detailed analysis
        analysis = {
            'django_patterns': len(django_patterns),
            'django_api_v1': len(api_v1_patterns),
            'postman_endpoints': len(postman_endpoints),
            'postman_api_v1': len(api_v1_postman),
            'django_endpoints': [p['path'] for p in api_v1_patterns],
            'postman_paths': [f"{e['method']} /{e['path']}" for e in api_v1_postman]
        }
        
        with open('endpoint_analysis_results.json', 'w', encoding='utf-8') as f:
            json.dump(analysis, f, indent=2, ensure_ascii=False)
        
        print()
        print('Analysis saved to endpoint_analysis_results.json')
    
    else:
        print('Could not load Postman collection for comparison')

if __name__ == '__main__':
    main()
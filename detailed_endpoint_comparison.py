#!/usr/bin/env python
"""
Detailed Endpoint Comparison Script
Compares Django URL patterns with Postman collection endpoints
and identifies specific discrepancies, missing endpoints, and implementation gaps.
"""

import json
import re
from pathlib import Path
from collections import defaultdict

def load_analysis_results():
    """Load the previous analysis results"""
    with open('simple_endpoint_analysis.json', 'r', encoding='utf-8') as f:
        return json.load(f)

def normalize_endpoint(endpoint):
    """Normalize endpoint for comparison"""
    # Remove leading/trailing slashes and normalize parameter patterns
    normalized = endpoint.strip('/')
    # Convert Django parameter patterns to Postman format
    normalized = re.sub(r'<str:(\w+)>', r'{{\1}}', normalized)
    normalized = re.sub(r'<int:(\w+)>', r'{{\1}}', normalized)
    normalized = re.sub(r'<slug:(\w+)>', r'{{\1}}', normalized)
    normalized = re.sub(r'<uuid:(\w+)>', r'{{\1}}', normalized)
    return normalized

def categorize_endpoints(endpoints):
    """Categorize endpoints by functionality"""
    categories = {
        'auth': [],
        'user_management': [],
        'market_management': [],
        'product_management': [],
        'order_management': [],
        'payment': [],
        'analytics': [],
        'notification': [],
        'chat': [],
        'category': [],
        'region': [],
        'discount': [],
        'reservation': [],
        'sms': [],
        'wallet': [],
        'affiliate': [],
        'other': []
    }
    
    for endpoint in endpoints:
        path = endpoint.get('path', '').lower()
        
        if any(x in path for x in ['pin', 'auth', 'login', 'register']):
            categories['auth'].append(endpoint)
        elif 'user' in path and any(x in path for x in ['bank', 'profile']):
            categories['user_management'].append(endpoint)
        elif 'market' in path:
            categories['market_management'].append(endpoint)
        elif 'product' in path:
            categories['product_management'].append(endpoint)
        elif any(x in path for x in ['order', 'cart']):
            categories['order_management'].append(endpoint)
        elif any(x in path for x in ['payment', 'wallet']):
            categories['payment'].append(endpoint)
        elif 'analytics' in path:
            categories['analytics'].append(endpoint)
        elif 'notification' in path:
            categories['notification'].append(endpoint)
        elif 'chat' in path:
            categories['chat'].append(endpoint)
        elif 'category' in path:
            categories['category'].append(endpoint)
        elif 'region' in path:
            categories['region'].append(endpoint)
        elif 'discount' in path:
            categories['discount'].append(endpoint)
        elif any(x in path for x in ['reservation', 'reserve']):
            categories['reservation'].append(endpoint)
        elif 'sms' in path:
            categories['sms'].append(endpoint)
        elif 'wallet' in path:
            categories['wallet'].append(endpoint)
        elif 'affiliate' in path:
            categories['affiliate'].append(endpoint)
        else:
            categories['other'].append(endpoint)
    
    return categories

def find_missing_endpoints(django_patterns, postman_endpoints):
    """Find endpoints that exist in Postman but not in Django"""
    django_normalized = set()
    for pattern in django_patterns:
        if isinstance(pattern, str) and pattern.startswith('api/v1/'):
            normalized = normalize_endpoint(pattern)
            django_normalized.add(normalized)
    
    missing_endpoints = []
    for endpoint in postman_endpoints:
        path = endpoint.get('path', '')
        if path.startswith('api/v1/'):
            normalized = normalize_endpoint(path)
            if normalized not in django_normalized:
                missing_endpoints.append({
                    'method': endpoint.get('method', 'GET'),
                    'path': path,
                    'normalized': normalized,
                    'name': endpoint.get('name', 'Unknown')
                })
    
    return missing_endpoints

def find_extra_endpoints(django_patterns, postman_endpoints):
    """Find endpoints that exist in Django but not in Postman"""
    postman_normalized = set()
    for endpoint in postman_endpoints:
        path = endpoint.get('path', '')
        if path.startswith('api/v1/'):
            normalized = normalize_endpoint(path)
            postman_normalized.add(normalized)
    
    extra_endpoints = []
    for pattern in django_patterns:
        if isinstance(pattern, str) and pattern.startswith('api/v1/'):
            normalized = normalize_endpoint(pattern)
            if normalized not in postman_normalized:
                extra_endpoints.append({
                    'pattern': pattern,
                    'normalized': normalized
                })
    
    return extra_endpoints

def analyze_method_coverage(django_patterns, postman_endpoints):
    """Analyze HTTP method coverage for each endpoint"""
    # Group Postman endpoints by normalized path
    postman_by_path = defaultdict(list)
    for endpoint in postman_endpoints:
        path = endpoint.get('path', '')
        if path.startswith('api/v1/'):
            normalized = normalize_endpoint(path)
            postman_by_path[normalized].append(endpoint.get('method', 'GET'))
    
    # Django patterns don't include method info, so we'll note this limitation
    method_analysis = {
        'postman_methods_by_path': dict(postman_by_path),
        'note': 'Django URL patterns do not specify HTTP methods - methods are defined in views'
    }
    
    return method_analysis

def generate_implementation_recommendations(missing_endpoints):
    """Generate recommendations for implementing missing endpoints"""
    recommendations = []
    
    # Group missing endpoints by app/module
    by_module = defaultdict(list)
    for endpoint in missing_endpoints:
        path_parts = endpoint['path'].split('/')
        if len(path_parts) >= 4:  # api/v1/module/...
            module = path_parts[3]
            by_module[module].append(endpoint)
    
    for module, endpoints in by_module.items():
        recommendations.append({
            'module': module,
            'missing_count': len(endpoints),
            'endpoints': endpoints,
            'suggested_actions': [
                f"Review {module} app views and URL patterns",
                f"Implement missing {len(endpoints)} endpoints",
                f"Add proper serializers and permissions",
                f"Update URL routing in apps/{module}/urls/"
            ]
        })
    
    return recommendations

def main():
    print("Loading analysis results...")
    data = load_analysis_results()
    
    django_patterns = data.get('django_patterns', [])
    postman_endpoints = data.get('postman_endpoints', [])
    
    print(f"Django patterns: {len(django_patterns)}")
    print(f"Postman endpoints: {len(postman_endpoints)}")
    
    # Extract pattern strings from django_patterns (they are dicts with 'pattern' key)
    django_pattern_strings = []
    for pattern_dict in django_patterns:
        if isinstance(pattern_dict, dict) and 'pattern' in pattern_dict:
            django_pattern_strings.append(pattern_dict['pattern'])
        elif isinstance(pattern_dict, str):
            django_pattern_strings.append(pattern_dict)
    
    # Filter API v1 endpoints
    django_api_patterns = [p for p in django_pattern_strings if p.startswith('api/v1/')]
    postman_api_endpoints = [e for e in postman_endpoints if e.get('path', '').startswith('api/v1/')]
    
    print(f"Django API v1 patterns: {len(django_api_patterns)}")
    print(f"Postman API v1 endpoints: {len(postman_api_endpoints)}")
    
    # Detailed comparison
    print("\n=== DETAILED ENDPOINT COMPARISON ===")
    
    # Find missing endpoints
    missing_endpoints = find_missing_endpoints(django_api_patterns, postman_api_endpoints)
    print(f"\nMissing endpoints (in Postman but not Django): {len(missing_endpoints)}")
    
    # Find extra endpoints
    extra_endpoints = find_extra_endpoints(django_api_patterns, postman_api_endpoints)
    print(f"Extra endpoints (in Django but not Postman): {len(extra_endpoints)}")
    
    # Categorize endpoints
    postman_categories = categorize_endpoints(postman_api_endpoints)
    
    # Method analysis
    method_analysis = analyze_method_coverage(django_api_patterns, postman_api_endpoints)
    
    # Generate recommendations
    recommendations = generate_implementation_recommendations(missing_endpoints)
    
    # Prepare detailed report
    detailed_report = {
        'summary': {
            'django_api_patterns': len(django_api_patterns),
            'postman_api_endpoints': len(postman_api_endpoints),
            'missing_endpoints_count': len(missing_endpoints),
            'extra_endpoints_count': len(extra_endpoints),
            'coverage_percentage': round((len(django_api_patterns) / len(postman_api_endpoints)) * 100, 2) if postman_api_endpoints else 0
        },
        'missing_endpoints': missing_endpoints,
        'extra_endpoints': extra_endpoints,
        'postman_categories': {k: len(v) for k, v in postman_categories.items()},
        'postman_categories_detailed': postman_categories,
        'method_analysis': method_analysis,
        'implementation_recommendations': recommendations,
        'critical_missing_endpoints': [
            ep for ep in missing_endpoints 
            if any(critical in ep['path'].lower() for critical in [
                'create', 'update', 'delete', 'list', 'detail', 'auth', 'payment'
            ])
        ]
    }
    
    # Save detailed report
    with open('detailed_endpoint_comparison.json', 'w', encoding='utf-8') as f:
        json.dump(detailed_report, f, indent=2, ensure_ascii=False)
    
    print(f"\n=== SUMMARY ===")
    print(f"Coverage: {detailed_report['summary']['coverage_percentage']}%")
    print(f"Missing endpoints: {len(missing_endpoints)}")
    print(f"Critical missing endpoints: {len(detailed_report['critical_missing_endpoints'])}")
    
    print(f"\n=== TOP MISSING ENDPOINTS ===")
    for i, endpoint in enumerate(missing_endpoints[:10]):
        print(f"{i+1}. {endpoint['method']} {endpoint['path']} - {endpoint['name']}")
    
    print(f"\n=== RECOMMENDATIONS BY MODULE ===")
    for rec in recommendations[:5]:
        print(f"- {rec['module']}: {rec['missing_count']} missing endpoints")
    
    print(f"\nDetailed report saved to: detailed_endpoint_comparison.json")

if __name__ == "__main__":
    main()
#!/usr/bin/env python
"""
Simple Endpoint Analysis Script for ASOUD Platform
Analyzes URL patterns from files and compares with Postman collection
"""

import os
import json
import re
from pathlib import Path

def find_url_files():
    """Find all urls.py files in the project"""
    url_files = []
    for root, dirs, files in os.walk('.'):
        for file in files:
            if file == 'urls.py' or file.endswith('_urls.py'):
                url_files.append(os.path.join(root, file))
    return url_files

def extract_url_patterns_from_file(file_path):
    """Extract URL patterns from a urls.py file"""
    patterns = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Find path() calls
        path_pattern = r"path\(\s*['\"]([^'\"]+)['\"]"
        matches = re.findall(path_pattern, content)
        
        for match in matches:
            patterns.append({
                'file': file_path,
                'pattern': match,
                'raw_pattern': match
            })
            
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
    
    return patterns

def load_postman_collection():
    """Load and parse Postman collection"""
    try:
        with open('ASOUD_Complete_Postman_Collection_252_Endpoints_FINAL.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print("Postman collection file not found!")
        return None

def extract_postman_endpoints(collection, endpoints=None):
    """Extract endpoints from Postman collection recursively"""
    if endpoints is None:
        endpoints = []
    
    if isinstance(collection, dict):
        if 'item' in collection:
            for item in collection['item']:
                extract_postman_endpoints(item, endpoints)
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
            extract_postman_endpoints(item, endpoints)
    
    return endpoints

def analyze_main_urls():
    """Analyze the main config/urls.py file"""
    main_urls_file = 'config/urls.py'
    if not os.path.exists(main_urls_file):
        return []
    
    with open(main_urls_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Extract include patterns
    include_pattern = r"path\(\s*['\"]([^'\"]*)['\"],\s*include\(['\"]([^'\"]+)['\"]"
    includes = re.findall(include_pattern, content)
    
    # Extract direct path patterns
    path_pattern = r"path\(\s*['\"]([^'\"]+)['\"]"
    direct_paths = re.findall(path_pattern, content)
    
    return {
        'includes': includes,
        'direct_paths': direct_paths,
        'content': content
    }

def main():
    print('=== ASOUD SIMPLE ENDPOINT ANALYSIS ===')
    print()
    
    # Find all URL files
    url_files = find_url_files()
    print(f'Found {len(url_files)} URL files:')
    for file in url_files:
        print(f'  - {file}')
    print()
    
    # Analyze main URLs
    main_analysis = analyze_main_urls()
    print('=== MAIN URL CONFIGURATION ===')
    print(f'Include patterns: {len(main_analysis["includes"])}')
    for prefix, include_path in main_analysis['includes']:
        print(f'  {prefix} -> {include_path}')
    print()
    
    # Extract all patterns
    all_patterns = []
    for file_path in url_files:
        patterns = extract_url_patterns_from_file(file_path)
        all_patterns.extend(patterns)
    
    print(f'Total URL patterns found: {len(all_patterns)}')
    
    # Filter API v1 patterns
    api_v1_patterns = []
    for pattern in all_patterns:
        if 'api/v1/' in pattern['file'] or 'api/v1/' in pattern['pattern']:
            api_v1_patterns.append(pattern)
    
    print(f'API v1 related patterns: {len(api_v1_patterns)}')
    print()
    
    # Load Postman collection
    postman_collection = load_postman_collection()
    if postman_collection:
        postman_endpoints = extract_postman_endpoints(postman_collection)
        print(f'Postman endpoints found: {len(postman_endpoints)}')
        
        # Filter API v1 Postman endpoints
        api_v1_postman = [e for e in postman_endpoints if 'api' in e['path'] and 'v1' in e['path']]
        print(f'Postman API v1 endpoints: {len(api_v1_postman)}')
        print()
        
        # Show some examples
        print('=== SAMPLE DJANGO URL PATTERNS ===')
        for i, pattern in enumerate(all_patterns[:20]):
            print(f'{i+1:2d}. {pattern["pattern"]} (from {pattern["file"]})')
        
        print()
        print('=== SAMPLE POSTMAN ENDPOINTS ===')
        for i, endpoint in enumerate(api_v1_postman[:20]):
            print(f'{i+1:2d}. {endpoint["method"]} /{endpoint["path"]} - {endpoint["name"]}')
        
        # Save analysis
        analysis_result = {
            'summary': {
                'django_url_files': len(url_files),
                'django_patterns': len(all_patterns),
                'django_api_v1_patterns': len(api_v1_patterns),
                'postman_total_endpoints': len(postman_endpoints),
                'postman_api_v1_endpoints': len(api_v1_postman)
            },
            'django_patterns': [{'file': p['file'], 'pattern': p['pattern']} for p in all_patterns],
            'postman_endpoints': [{'method': e['method'], 'path': e['path'], 'name': e['name']} for e in postman_endpoints],
            'main_url_includes': main_analysis['includes']
        }
        
        with open('simple_endpoint_analysis.json', 'w', encoding='utf-8') as f:
            json.dump(analysis_result, f, indent=2, ensure_ascii=False)
        
        print()
        print('=== ANALYSIS SUMMARY ===')
        print(f'Django URL files: {len(url_files)}')
        print(f'Django patterns: {len(all_patterns)}')
        print(f'Django API v1 patterns: {len(api_v1_patterns)}')
        print(f'Postman total endpoints: {len(postman_endpoints)}')
        print(f'Postman API v1 endpoints: {len(api_v1_postman)}')
        print()
        print('Detailed analysis saved to simple_endpoint_analysis.json')
    
    else:
        print('Could not load Postman collection for comparison')

if __name__ == '__main__':
    main()
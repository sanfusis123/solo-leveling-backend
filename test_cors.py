#!/usr/bin/env python3
"""
Test script to verify CORS configuration is working properly.
"""

import requests
import sys

def test_cors(base_url):
    """Test CORS configuration by making requests from different origins."""
    
    print(f"Testing CORS for: {base_url}")
    print("-" * 50)
    
    # Test basic endpoint
    try:
        response = requests.get(f"{base_url}/")
        print(f"✅ Root endpoint: {response.status_code}")
        print(f"   Response: {response.json()}")
    except Exception as e:
        print(f"❌ Root endpoint failed: {e}")
    
    # Test health endpoint
    try:
        response = requests.get(f"{base_url}/health")
        print(f"✅ Health endpoint: {response.status_code}")
        print(f"   Response: {response.json()}")
    except Exception as e:
        print(f"❌ Health endpoint failed: {e}")
    
    # Test API endpoint
    try:
        response = requests.get(f"{base_url}/api/v1/")
        print(f"✅ API endpoint: {response.status_code}")
    except Exception as e:
        print(f"❌ API endpoint failed: {e}")
    
    # Test CORS headers with a preflight request
    try:
        headers = {
            'Origin': 'https://solo-leveling-frontend.vercel.app',
            'Access-Control-Request-Method': 'POST',
            'Access-Control-Request-Headers': 'Content-Type,Authorization'
        }
        response = requests.options(f"{base_url}/api/v1/auth/login", headers=headers)
        print(f"✅ CORS preflight: {response.status_code}")
        
        cors_headers = {k: v for k, v in response.headers.items() if 'access-control' in k.lower()}
        print(f"   CORS headers: {cors_headers}")
        
    except Exception as e:
        print(f"❌ CORS preflight failed: {e}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        base_url = sys.argv[1].rstrip('/')
    else:
        base_url = "https://your-backend-url.com"  # Replace with your actual backend URL
    
    test_cors(base_url)
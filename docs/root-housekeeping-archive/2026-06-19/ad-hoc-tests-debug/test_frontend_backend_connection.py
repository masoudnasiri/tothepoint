#!/usr/bin/env python3
"""
Test Frontend-Backend Connection
"""

import requests
import json

print("\n" + "="*60)
print("  Test Frontend-Backend Connection")
print("="*60)

# Test if backend is accessible from frontend perspective
print("\n[1] Test Backend Health")
try:
    response = requests.get("http://localhost:8000/health", timeout=5)
    print(f"    Status: {response.status_code}")
    if response.status_code == 200:
        print("    [OK] Backend is accessible")
    else:
        print("    [FAIL] Backend health check failed")
except Exception as e:
    print(f"    [FAIL] Backend not accessible: {e}")

# Test if frontend can reach backend through proxy
print("\n[2] Test Frontend Proxy Connection")
try:
    # Simulate frontend request to backend
    response = requests.get("http://localhost:3000/api/health", timeout=5)
    print(f"    Status: {response.status_code}")
    if response.status_code == 200:
        print("    [OK] Frontend proxy working")
    else:
        print("    [FAIL] Frontend proxy not working")
except Exception as e:
    print(f"    [FAIL] Frontend proxy error: {e}")

# Test optimization endpoint directly
print("\n[3] Test Optimization Endpoint")
try:
    # Login first
    login_response = requests.post("http://localhost:8000/auth/login", json={
        "username": "finance1",
        "password": "finance123"
    })
    
    if login_response.status_code == 200:
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Test optimization
        optimization_request = {
            "max_time_slots": 24,
            "time_limit_seconds": 300
        }
        
        response = requests.post("http://localhost:8000/finance/optimize", 
                                json=optimization_request, 
                                headers=headers, 
                                timeout=30)
        
        print(f"    Status: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"    [OK] Optimization successful")
            print(f"        Status: {result.get('status')}")
            print(f"        Total Cost: {result.get('total_cost')}")
            print(f"        Items Optimized: {result.get('items_optimized')}")
        else:
            print(f"    [FAIL] Optimization failed: {response.text[:200]}")
    else:
        print(f"    [FAIL] Login failed: {login_response.status_code}")
        
except Exception as e:
    print(f"    [FAIL] Optimization test error: {e}")

print("\n" + "="*60)
print("  CONNECTION TEST COMPLETE")
print("="*60)

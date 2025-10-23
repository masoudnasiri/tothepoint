#!/usr/bin/env python3
"""
Test Optimization Results Endpoint
Check what the optimization results API returns
"""

import requests
import json
from datetime import datetime, date, timedelta

BASE_URL = "http://localhost:8000"

print("\n" + "="*60)
print("  Test Optimization Results Endpoint")
print("="*60)

# Login as Finance
print("\n[1] Login as Finance")
response = requests.post(f"{BASE_URL}/auth/login", json={"username": "finance1", "password": "finance123"})
finance_token = response.json()["access_token"]
headers_finance = {"Authorization": f"Bearer {finance_token}"}
print("    [OK] Logged in")

# Get Optimization Results
print("\n[2] Get Optimization Results")
response = requests.get(f"{BASE_URL}/finance/optimization-results", headers=headers_finance)
if response.status_code == 200:
    results = response.json()
    print(f"    [OK] Results retrieved")
    print(f"        Status Code: {response.status_code}")
    print(f"        Results Type: {type(results)}")
    print(f"        Results Length: {len(results) if isinstance(results, list) else 'Not a list'}")
    
    if isinstance(results, list) and len(results) > 0:
        print(f"        First Result Keys: {list(results[0].keys()) if results[0] else 'No results'}")
        print(f"        Sample Result: {json.dumps(results[0], indent=2, default=str) if results[0] else 'No results'}")
    else:
        print(f"        Results: {results}")
    
else:
    print(f"    [FAIL] Failed to get results: {response.status_code}")
    print(f"        Response: {response.text[:200]}")

# Get Latest Optimization Run
print("\n[3] Get Latest Optimization Run")
response = requests.get(f"{BASE_URL}/finance/latest-optimization", headers=headers_finance)
if response.status_code == 200:
    latest_run = response.json()
    print(f"    [OK] Latest run retrieved")
    print(f"        Status Code: {response.status_code}")
    print(f"        Latest Run: {json.dumps(latest_run, indent=2, default=str)}")
else:
    print(f"    [FAIL] Failed to get latest run: {response.status_code}")
    print(f"        Response: {response.text[:200]}")

print("\n" + "="*60)
print("  RESULTS TEST COMPLETE")
print("="*60)

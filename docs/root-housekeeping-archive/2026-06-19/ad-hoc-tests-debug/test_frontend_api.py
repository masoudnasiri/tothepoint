#!/usr/bin/env python3
"""
Test Frontend API Calls
Check what the frontend API endpoints return
"""

import requests
import json
from datetime import datetime, date, timedelta

BASE_URL = "http://localhost:8000"

print("\n" + "="*60)
print("  Test Frontend API Calls")
print("="*60)

# Login as Finance
print("\n[1] Login as Finance")
response = requests.post(f"{BASE_URL}/auth/login", json={"username": "finance1", "password": "finance123"})
finance_token = response.json()["access_token"]
headers_finance = {"Authorization": f"Bearer {finance_token}"}
print("    [OK] Logged in")

# Test listResults API (what frontend calls)
print("\n[2] Test listResults API")
response = requests.get(f"{BASE_URL}/finance/optimization-results", headers=headers_finance)
if response.status_code == 200:
    results = response.json()
    print(f"    [OK] listResults API working")
    print(f"        Status Code: {response.status_code}")
    print(f"        Results Type: {type(results)}")
    print(f"        Results Length: {len(results) if isinstance(results, list) else 'Not a list'}")
    
    if isinstance(results, list) and len(results) > 0:
        print(f"        First Result: {json.dumps(results[0], indent=2, default=str)}")
        print(f"        Run IDs: {list(set([r.get('run_id') for r in results]))}")
    else:
        print(f"        Results: {results}")
else:
    print(f"    [FAIL] listResults API failed: {response.status_code}")
    print(f"        Response: {response.text[:200]}")

# Test getLatestRun API (what frontend calls)
print("\n[3] Test getLatestRun API")
response = requests.get(f"{BASE_URL}/finance/latest-optimization", headers=headers_finance)
if response.status_code == 200:
    latest_run = response.json()
    print(f"    [OK] getLatestRun API working")
    print(f"        Status Code: {response.status_code}")
    print(f"        Latest Run: {json.dumps(latest_run, indent=2, default=str)}")
else:
    print(f"    [FAIL] getLatestRun API failed: {response.status_code}")
    print(f"        Response: {response.text[:200]}")

# Test optimization-runs API (alternative)
print("\n[4] Test optimization-runs API")
response = requests.get(f"{BASE_URL}/finance/optimization-runs", headers=headers_finance)
if response.status_code == 200:
    runs = response.json()
    print(f"    [OK] optimization-runs API working")
    print(f"        Status Code: {response.status_code}")
    print(f"        Runs: {json.dumps(runs, indent=2, default=str)}")
else:
    print(f"    [FAIL] optimization-runs API failed: {response.status_code}")
    print(f"        Response: {response.text[:200]}")

print("\n" + "="*60)
print("  FRONTEND API TEST COMPLETE")
print("="*60)

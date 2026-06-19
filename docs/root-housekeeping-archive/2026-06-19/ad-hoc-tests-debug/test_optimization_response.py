#!/usr/bin/env python3
"""
Test Optimization Response
Check what the optimization API actually returns
"""

import requests
import json
from datetime import datetime, date, timedelta

BASE_URL = "http://localhost:8000"

print("\n" + "="*60)
print("  Test Optimization Response")
print("="*60)

# Login as Finance
print("\n[1] Login as Finance")
response = requests.post(f"{BASE_URL}/auth/login", json={"username": "finance1", "password": "finance123"})
finance_token = response.json()["access_token"]
headers_finance = {"Authorization": f"Bearer {finance_token}"}
print("    [OK] Logged in")

# Run Optimization
print("\n[2] Run Optimization")
optimization_request = {
    "max_time_slots": 5,
    "include_budget_constraints": True,
    "include_priority_weights": True
}

response = requests.post(f"{BASE_URL}/finance/optimize", json=optimization_request, headers=headers_finance)
if response.status_code == 200:
    result = response.json()
    print(f"    [OK] Optimization completed")
    print(f"        Status Code: {response.status_code}")
    print(f"        Response Keys: {list(result.keys())}")
    print(f"        Status: {result.get('status', 'Unknown')}")
    print(f"        Total Cost: {result.get('total_cost', 'N/A')}")
    print(f"        Items Optimized: {result.get('items_optimized', 'N/A')}")
    print(f"        Execution Time: {result.get('execution_time_seconds', 'N/A')}")
    print(f"        Proposals Count: {len(result.get('proposals', []))}")
    print(f"        Message: {result.get('message', 'No message')}")
    
    # Show full response structure
    print(f"\n    Full Response Structure:")
    print(json.dumps(result, indent=2, default=str))
    
else:
    print(f"    [FAIL] Optimization failed: {response.status_code}")
    print(f"        Response: {response.text[:200]}")

print("\n" + "="*60)
print("  RESPONSE TEST COMPLETE")
print("="*60)

#!/usr/bin/env python3
"""
Debug Optimization Issue
"""

import requests
from datetime import datetime, date, timedelta

BASE_URL = "http://localhost:8000"

print("\n" + "="*50)
print("  Debug Optimization Issue")
print("="*50)

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
    print(f"        Status: {result.get('status', 'Unknown')}")
    print(f"        Total Cost: {result.get('total_cost', 'N/A')}")
    print(f"        Items Selected: {len(result.get('selected_items', []))}")
    message = result.get('message', 'No message')
    print(f"        Message: {message.encode('ascii', 'ignore').decode('ascii')}")
    
    # Show selected items
    selected_items = result.get('selected_items', [])
    print(f"\n    Selected Items:")
    for item in selected_items:
        print(f"        - {item.get('item_code', 'Unknown')}: {item.get('supplier_name', 'Unknown')}")
else:
    print(f"    [FAIL] Optimization failed: {response.text[:200]}")

print("\n" + "="*50)
print("  DEBUG COMPLETE")
print("="*50)

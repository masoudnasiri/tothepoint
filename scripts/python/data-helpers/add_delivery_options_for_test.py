#!/usr/bin/env python3
"""
Add Delivery Options for Test Items
"""

import requests
from datetime import datetime, date, timedelta

BASE_URL = "http://localhost:8000"

print("\n" + "="*50)
print("  Add Delivery Options for Test Items")
print("="*50)

# Login as Admin
print("\n[1] Login as Admin")
response = requests.post(f"{BASE_URL}/auth/login", json={"username": "admin", "password": "admin123"})
admin_token = response.json()["access_token"]
headers_admin = {"Authorization": f"Bearer {admin_token}"}
print("    [OK] Logged in")

# Get Project Items from Project 1 (which has delivery options)
print("\n[2] Get Project Items from Project 1")
response = requests.get(f"{BASE_URL}/items/project/1", headers=headers_admin)
items = response.json().get("items", [])
test_items = items[:2]  # Test with 2 items
print(f"    [OK] Testing with {len(test_items)} items from Project 1")

# Add Delivery Options for Each Item
print("\n[3] Add Multiple Delivery Options")
delivery_templates = [
    {"days": 20, "slot": 1, "name": "Fast (20 days)"},
    {"days": 35, "slot": 2, "name": "Standard (35 days)"},
    {"days": 50, "slot": 3, "name": "Slow (50 days)"}
]

for item in test_items:
    print(f"\n    {item['item_code']}:")
    for opt in delivery_templates:
        delivery_date = (datetime.now() + timedelta(days=opt["days"])).strftime("%Y-%m-%d")
        data = {
            "project_item_id": item["id"],
            "delivery_date": delivery_date,
            "delivery_slot": opt["slot"],
            "invoice_timing_type": "ABSOLUTE",
            "invoice_issue_date": delivery_date,
            "invoice_days_after_delivery": 0,
            "invoice_amount_per_unit": 1000.0,
            "preference_rank": opt["slot"]
        }
        response = requests.post(f"{BASE_URL}/delivery-options", json=data, headers=headers_admin)
        if response.status_code == 200:
            delivery_id = response.json()["id"]
            print(f"        [OK] {opt['name']}: {delivery_date} (ID: {delivery_id})")
        else:
            print(f"        [FAIL] {opt['name']}: {response.text[:80]}")

# Finalize Items
print("\n[4] Finalize Items")
for item in test_items:
    response = requests.put(
        f"{BASE_URL}/items/{item['id']}/finalize",
        json={"is_finalized": True},
        headers=headers_admin
    )
    print(f"    {item['item_code']}: {'[OK]' if response.status_code == 200 else '[FAIL]'}")

print("\n" + "="*50)
print("  DELIVERY OPTIONS ADDED")
print("="*50)
print("\nItems now have:")
print("  - Multiple delivery options (Fast, Standard, Slow)")
print("  - Items are finalized and visible in procurement")
print("  - Ready for optimization testing")

#!/usr/bin/env python3
"""
Check procurement status for all finalized items
"""

import requests

BASE_URL = "http://localhost:8000"

print("\n" + "="*80)
print("  Check Procurement Status for All Finalized Items")
print("="*80)

# Login as Finance (has admin access)
print("\n[1] Login as Finance")
response = requests.post(f"{BASE_URL}/auth/login", json={"username": "finance1", "password": "finance123"})
if response.status_code != 200:
    print(f"    [ERROR] Login failed: {response.status_code} - {response.text}")
    exit(1)
admin_token = response.json()["access_token"]
headers_admin = {"Authorization": f"Bearer {admin_token}"}
print("    [OK] Logged in")

# Get all finalized items
print("\n[2] Get all finalized project items")
response = requests.get(f"{BASE_URL}/items/finalized", headers=headers_admin)
finalized_items = response.json()
print(f"    Total finalized items: {len(finalized_items)}")

# For each item, check:
# 1. Has delivery options
# 2. Has finalized procurement options
print("\n[3] Check each item's status")
print("-" * 80)

items_with_all_data = []
items_missing_delivery = []
items_missing_procurement = []

for item in finalized_items:
    item_code = item["item_code"]
    project_item_id = item["id"]
    
    # Check delivery options
    try:
        delivery_response = requests.get(
            f"{BASE_URL}/delivery-options/by-item-code/{item_code}",
            headers=headers_admin
        )
        delivery_options_count = len(delivery_response.json()) if delivery_response.status_code == 200 else 0
    except:
        delivery_options_count = 0
    
    # Check finalized procurement options
    try:
        proc_response = requests.get(f"{BASE_URL}/procurement/options", headers=headers_admin)
        all_proc_options = proc_response.json()
        finalized_proc_options = [
            opt for opt in all_proc_options 
            if opt.get("item_code") == item_code and opt.get("is_finalized") == True
        ]
        finalized_proc_count = len(finalized_proc_options)
    except Exception as e:
        finalized_proc_count = 0
    
    # Categorize
    if delivery_options_count > 0 and finalized_proc_count > 0:
        items_with_all_data.append(item_code)
        status = "[OK]"
    elif delivery_options_count == 0:
        items_missing_delivery.append(item_code)
        status = "[MISSING DELIVERY]"
    elif finalized_proc_count == 0:
        items_missing_procurement.append(item_code)
        status = "[MISSING FINALIZED PROCUREMENT]"
    else:
        status = "[UNKNOWN]"
    
    print(f"    {status:30} {item_code:20} Delivery: {delivery_options_count:2}   Procurement(Finalized): {finalized_proc_count:2}")

print("-" * 80)
print(f"\n[4] Summary")
print(f"    Items with all data (ready for optimization): {len(items_with_all_data)}")
print(f"    Items missing delivery options:               {len(items_missing_delivery)}")
print(f"    Items missing finalized procurement options:  {len(items_missing_procurement)}")

if items_missing_delivery:
    print(f"\n    Items missing delivery options:")
    for item in items_missing_delivery:
        print(f"      - {item}")

if items_missing_procurement:
    print(f"\n    Items missing finalized procurement options:")
    for item in items_missing_procurement:
        print(f"      - {item}")

if items_with_all_data:
    print(f"\n    Items ready for optimization ({len(items_with_all_data)} items):")
    for item in items_with_all_data:
        print(f"      - {item}")

print("\n" + "="*80)
print("  PROCUREMENT STATUS CHECK COMPLETE")
print("="*80)

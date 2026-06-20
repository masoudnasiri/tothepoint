#!/usr/bin/env python3
"""
Add delivery options to all finalized project items
"""

import requests
from datetime import datetime, timedelta

BASE_URL = "http://localhost:8000"

print("\n" + "="*60)
print("  Add Delivery Options to All Finalized Items")
print("="*60)

# Login as Admin
print("\n[1] Login as Admin")
response = requests.post(f"{BASE_URL}/auth/login", json={"username": "admin", "password": "admin123"})
admin_token = response.json()["access_token"]
headers_admin = {"Authorization": f"Bearer {admin_token}"}
print("    [OK] Logged in as admin")

# Get all finalized items
print("\n[2] Get all finalized project items")
response = requests.get(f"{BASE_URL}/items/finalized", headers=headers_admin)
finalized_items = response.json()
print(f"    Found {len(finalized_items)} finalized items")

# Add delivery options to each item
print("\n[3] Add delivery options to each item")
base_date = datetime.now()

# Delivery options template: 4 options per item at different dates
delivery_options_template = [
    {"days_offset": 15, "slot": 1, "invoice_timing": "ABSOLUTE"},
    {"days_offset": 30, "slot": 2, "invoice_timing": "RELATIVE", "days_after": 15},
    {"days_offset": 45, "slot": 3, "invoice_timing": "RELATIVE", "days_after": 30},
    {"days_offset": 60, "slot": 4, "invoice_timing": "ABSOLUTE"},
]

added_count = 0
skipped_count = 0

for item in finalized_items:
    item_code = item["item_code"]
    project_item_id = item["id"]
    
    # Check if item already has delivery options
    try:
        response = requests.get(
            f"{BASE_URL}/delivery-options/by-item-code/{item_code}",
            headers=headers_admin
        )
        if response.status_code == 200 and len(response.json()) > 0:
            print(f"    [SKIP] {item_code} already has delivery options")
            skipped_count += 1
            continue
    except:
        pass
    
    # Add 4 delivery options for this item
    for option in delivery_options_template:
        delivery_date = (base_date + timedelta(days=option["days_offset"])).strftime("%Y-%m-%d")
        
        if option["invoice_timing"] == "ABSOLUTE":
            invoice_date = delivery_date
        else:
            invoice_date = (base_date + timedelta(days=option["days_offset"] + option["days_after"])).strftime("%Y-%m-%d")
        
        delivery_option_data = {
            "project_item_id": project_item_id,
            "delivery_date": delivery_date,
            "delivery_slot": option["slot"],
            "invoice_timing_type": option["invoice_timing"],
            "invoice_date": invoice_date,
            "invoice_amount_per_unit": item.get("unit_cost", 0) if item.get("unit_cost") else 100.0,
        }
        
        try:
            response = requests.post(
                f"{BASE_URL}/delivery-options",
                json=delivery_option_data,
                headers=headers_admin
            )
            if response.status_code == 200:
                added_count += 1
            else:
                print(f"    [ERROR] Failed to add delivery option for {item_code}: {response.text[:100]}")
        except Exception as e:
            print(f"    [ERROR] Exception adding delivery option for {item_code}: {e}")

print(f"\n[4] Summary")
print(f"    Total items: {len(finalized_items)}")
print(f"    Delivery options added: {added_count}")
print(f"    Items skipped (already had options): {skipped_count}")
print(f"    Expected total options: {len(finalized_items) * 4}")
print(f"    Actual options added: {added_count}")

print("\n" + "="*60)
print("  DELIVERY OPTIONS ADDED TO ALL ITEMS")
print("="*60)

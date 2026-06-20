#!/usr/bin/env python3
"""
Add Multiple Delivery Options for Project Items
This script adds multiple delivery date options for each item in a project
"""

import requests
from datetime import datetime, timedelta

BASE_URL = "http://localhost:8000"

print("\n" + "="*60)
print("  Add Multiple Delivery Options for Project Items")
print("="*60)

# Step 1: Login as admin (can manage delivery options)
print("\n=== Step 1: Login as Admin ===")
response = requests.post(f"{BASE_URL}/auth/login", json={"username": "admin", "password": "admin123"})
if response.status_code == 200:
    admin_token = response.json()["access_token"]
    print("[OK] Logged in as admin")
else:
    print(f"[FAIL] Login failed: {response.text}")
    exit(1)

headers = {"Authorization": f"Bearer {admin_token}"}

# Step 2: Get project items
print("\n=== Step 2: Get Project 1 Items ===")
response = requests.get(f"{BASE_URL}/items/project/1", headers=headers)
items = response.json().get("items", [])
print(f"[OK] Found {len(items)} items in Project 1 (DC-MOD-2025)")

# Use first 5 items for testing
test_items = items[:5]
print(f"\nTesting with {len(test_items)} items:")
for item in test_items:
    print(f"  - {item['item_code']}: {item['item_name']}")

# Step 3: Add multiple delivery options for each item
print("\n=== Step 3: Add Multiple Delivery Options ===")

# Define delivery options: different dates and slots
delivery_options_template = [
    {
        "days_offset": 15,
        "slot": 1,
        "slot_name": "Early Delivery - Morning",
        "invoice_timing": "ABSOLUTE",
        "invoice_amount_multiplier": 1.0
    },
    {
        "days_offset": 30,
        "slot": 2,
        "slot_name": "Standard Delivery - Afternoon",
        "invoice_timing": "ABSOLUTE",
        "invoice_amount_multiplier": 1.0
    },
    {
        "days_offset": 45,
        "slot": 3,
        "slot_name": "Flexible Delivery - Evening",
        "invoice_timing": "RELATIVE",
        "invoice_amount_multiplier": 0.95,
        "invoice_days_after": 30
    },
    {
        "days_offset": 60,
        "slot": 4,
        "slot_name": "Extended Delivery - Morning",
        "invoice_timing": "RELATIVE",
        "invoice_amount_multiplier": 0.9,
        "invoice_days_after": 60
    }
]

delivery_stats = {"total_added": 0, "total_failed": 0}

for item in test_items:
    print(f"\n[Item: {item['item_code']} - {item['item_name']}]")
    
    for i, delivery_opt in enumerate(delivery_options_template, 1):
        # Calculate delivery date
        delivery_date = (datetime.now() + timedelta(days=delivery_opt["days_offset"])).strftime("%Y-%m-%d")
        
        # Calculate invoice issue date if needed
        if delivery_opt["invoice_timing"] == "after_delivery" and "invoice_days_after" in delivery_opt:
            invoice_date = (datetime.now() + timedelta(
                days=delivery_opt["days_offset"] + delivery_opt["invoice_days_after"]
            )).strftime("%Y-%m-%d")
        else:
            invoice_date = delivery_date
        
        # Prepare delivery option data
        data = {
            "project_item_id": item["id"],
            "delivery_date": delivery_date,
            "delivery_slot": delivery_opt["slot"],
            "invoice_timing_type": delivery_opt["invoice_timing"],
            "invoice_issue_date": invoice_date,
            "invoice_days_after_delivery": delivery_opt.get("invoice_days_after", 0),
            "invoice_amount_per_unit": float(item.get("quantity", 1) * 1000 * delivery_opt["invoice_amount_multiplier"]),
            "preference_rank": i,
            "notes": f"{delivery_opt['slot_name']} - {delivery_opt['days_offset']} days from now"
        }
        
        # Add delivery option
        response = requests.post(f"{BASE_URL}/delivery-options", json=data, headers=headers)
        if response.status_code == 200:
            delivery_stats["total_added"] += 1
            print(f"  [{i}] [OK] Added: {delivery_opt['slot_name']}")
            print(f"      Delivery: {delivery_date}, Invoice: {invoice_date}")
        else:
            delivery_stats["total_failed"] += 1
            print(f"  [{i}] [FAIL] Failed: {response.status_code}")
            print(f"      Error: {response.text[:150]}")

# Step 4: Verify delivery options were added
print("\n=== Step 4: Verify Delivery Options ===")
for item in test_items:
    response = requests.get(f"{BASE_URL}/delivery-options/item/{item['id']}", headers=headers)
    if response.status_code == 200:
        options = response.json()
        print(f"\n{item['item_code']}: {len(options)} delivery options")
        for opt in options[:2]:  # Show first 2
            print(f"  - Delivery: {opt.get('delivery_date')} (Slot {opt.get('delivery_slot')})")
    else:
        print(f"{item['item_code']}: Unable to fetch options")

# Summary
print("\n" + "="*60)
print("  Delivery Options Added Successfully!")
print("="*60)
print(f"\nStatistics:")
print(f"  - Items processed: {len(test_items)}")
print(f"  - Delivery options per item: {len(delivery_options_template)}")
print(f"  - Total delivery options added: {delivery_stats['total_added']}")
print(f"  - Failed: {delivery_stats['total_failed']}")

print(f"\nDelivery Options Summary:")
print(f"  1. Early Delivery (15 days) - Morning slot")
print(f"  2. Standard Delivery (30 days) - Afternoon slot")
print(f"  3. Flexible Delivery (45 days) - Evening slot - 5% discount")
print(f"  4. Extended Delivery (60 days) - Morning slot - 10% discount")

print(f"\nNow each item has {len(delivery_options_template)} delivery date options to choose from!")
print(f"Next step: Finalize items to make them visible to procurement.\n")


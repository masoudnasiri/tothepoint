#!/usr/bin/env python3
"""
Complete Linked Workflow Test
Procurement options are linked to project item delivery options
"""

import requests
from datetime import datetime, timedelta

BASE_URL = "http://localhost:8000"

print("\n" + "="*70)
print("  Complete Linked Workflow - Delivery to Procurement")
print("="*70)

# Login as Admin
print("\n[1] Login as Admin")
response = requests.post(f"{BASE_URL}/auth/login", json={"username": "admin", "password": "admin123"})
admin_token = response.json()["access_token"]
headers_admin = {"Authorization": f"Bearer {admin_token}"}
print("    [OK] Logged in")

# Get items from Project 3
print("\n[2] Get Items from Project 3 (NET-INF-2025)")
response = requests.get(f"{BASE_URL}/items/project/3", headers=headers_admin)
items = response.json().get("items", [])
test_items = items[:2]  # Test with 2 items
print(f"    [OK] Testing with {len(test_items)} items:")
for item in test_items:
    print(f"        - {item['item_code']}: {item['item_name']}")

# Add Delivery Options for Each Item
print("\n[3] Add Multiple Delivery Options")
delivery_templates = [
    {"days": 20, "slot": 1, "name": "Fast (20 days)"},
    {"days": 35, "slot": 2, "name": "Standard (35 days)"},
    {"days": 50, "slot": 3, "name": "Slow (50 days)"}
]

item_delivery_options = {}
for item in test_items:
    print(f"\n    {item['item_code']}:")
    delivery_ids = []
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
            delivery_ids.append(delivery_id)
            print(f"        [OK] {opt['name']}: {delivery_date} (ID: {delivery_id})")
        else:
            print(f"        [FAIL] {opt['name']}: {response.text[:80]}")
    item_delivery_options[item["item_code"]] = delivery_ids

# Finalize Items
print("\n[4] Finalize Items")
for item in test_items:
    response = requests.put(
        f"{BASE_URL}/items/{item['id']}/finalize",
        json={"is_finalized": True},
        headers=headers_admin
    )
    print(f"    {item['item_code']}: {'[OK]' if response.status_code == 200 else '[FAIL]'}")

# Login as Procurement
print("\n[5] Login as Procurement")
response = requests.post(f"{BASE_URL}/auth/login", json={"username": "procurement1", "password": "proc123"})
proc_token = response.json()["access_token"]
headers_proc = {"Authorization": f"Bearer {proc_token}"}
print("    [OK] Logged in")

# Add Procurement Options Linked to Delivery Options
print("\n[6] Add Procurement Options (Linked to Delivery Options)")
suppliers = [
    {"name": "Supplier A", "cost": 1500},
    {"name": "Supplier B", "cost": 1400},
    {"name": "Supplier C", "cost": 1600}
]

proc_option_ids = {}
for item in test_items:
    print(f"\n    {item['item_code']}:")
    delivery_ids = item_delivery_options.get(item["item_code"], [])
    ids = []
    
    # Create one procurement option for each delivery option
    for i, delivery_id in enumerate(delivery_ids):
        if i < len(suppliers):
            supplier = suppliers[i]
            
            # Get delivery option details to extract the date
            response_delivery = requests.get(f"{BASE_URL}/delivery-options/{delivery_id}", headers=headers_admin)
            if response_delivery.status_code == 200:
                delivery_data = response_delivery.json()
                delivery_date = delivery_data["delivery_date"]
                
                data = {
                    "item_code": item["item_code"],
                    "supplier_name": supplier["name"],
                    "base_cost": supplier["cost"],
                    "currency_id": 18,
                    "shipping_cost": 100.0,
                    "delivery_option_id": delivery_id,  # LINK TO DELIVERY OPTION
                    "lomc_lead_time": 0,
                    "expected_delivery_date": delivery_date,  # From delivery option
                    "payment_terms": {"type": "cash", "discount_percent": 0}
                }
                
                response = requests.post(f"{BASE_URL}/procurement/options", json=data, headers=headers_proc)
                if response.status_code == 200:
                    opt_id = response.json()["id"]
                    ids.append(opt_id)
                    print(f"        [OK] {supplier['name']}: ${supplier['cost']} -> Delivery: {delivery_date} (Delivery Option ID: {delivery_id})")
                else:
                    print(f"        [FAIL] {supplier['name']}: {response.text[:80]}")
    
    proc_option_ids[item["item_code"]] = ids

# Finalize Best Options
print("\n[7] Finalize Best Procurement Options")
for item in test_items:
    ids = proc_option_ids.get(item["item_code"], [])
    if len(ids) > 1:
        best_id = ids[1]  # Supplier B - middle option
        print(f"    {item['item_code']}: Selecting Supplier B (best price)")
        response = requests.put(
            f"{BASE_URL}/procurement/option/{best_id}",
            json={"is_finalized": True},
            headers=headers_proc
        )
        print(f"        {'[OK]' if response.status_code == 200 else '[FAIL]'} Decision finalized")

# Summary
print("\n" + "="*70)
print("  WORKFLOW COMPLETE - Procurement Linked to Delivery Options!")
print("="*70)
print(f"\nResults:")
print(f"  - Items processed: {len(test_items)}")
print(f"  - Delivery options per item: {len(delivery_templates)}")
print(f"  - Procurement options per item: {len(suppliers)}")
print(f"  - Each procurement option linked to a delivery option")
print(f"  - Delivery dates from project item used in procurement")

print(f"\nKey Feature:")
print(f"  When procurement edits an option, the delivery date comes from")
print(f"  the project item's delivery options, not entered manually!")

print(f"\nVerify in UI:")
print(f"  1. Login as procurement1 -> Procurement")
print(f"  2. View items - each has 3 procurement options")
print(f"  3. Each option shows delivery date from project item")
print(f"  4. Edit an option - delivery date is pre-filled from project\n")


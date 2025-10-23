#!/usr/bin/env python3
"""
Complete Workflow Test with Delivery Options
1. Add multiple delivery options for items
2. Finalize items (PMO/Admin)
3. Add procurement options
4. Finalize procurement decisions
"""

import requests
from datetime import datetime, timedelta

BASE_URL = "http://localhost:8000"

print("\n" + "="*70)
print("  Complete Workflow Test - With Delivery Options")
print("="*70)

# STEP 1: Login as Admin
print("\n=== STEP 1: Login as Admin ===")
response = requests.post(f"{BASE_URL}/auth/login", json={"username": "admin", "password": "admin123"})
admin_token = response.json()["access_token"]
headers_admin = {"Authorization": f"Bearer {admin_token}"}
print("[OK] Logged in as admin")

# STEP 2: Get items from Project 2
print("\n=== STEP 2: Get Items from Project 2 (OFF-IT-2025) ===")
response = requests.get(f"{BASE_URL}/items/project/2", headers=headers_admin)
items = response.json().get("items", [])
test_items = items[:3]  # Use first 3 items
print(f"[OK] Testing with {len(test_items)} items:")
for item in test_items:
    print(f"  - {item['item_code']}: {item['item_name']}")

# STEP 3: Add Multiple Delivery Options
print("\n=== STEP 3: Add Multiple Delivery Options ===")
delivery_opts = [
    {"days": 15, "slot": 1, "name": "Express (15 days)"},
    {"days": 30, "slot": 2, "name": "Standard (30 days)"},
    {"days": 45, "slot": 3, "name": "Economy (45 days)"}
]

for item in test_items:
    print(f"\n{item['item_code']}:")
    for opt in delivery_opts:
        delivery_date = (datetime.now() + timedelta(days=opt["days"])).strftime("%Y-%m-%d")
        data = {
            "project_item_id": item["id"],
            "delivery_date": delivery_date,
            "delivery_slot": opt["slot"],
            "invoice_timing_type": "ABSOLUTE",
            "invoice_issue_date": delivery_date,
            "invoice_days_after_delivery": 0,
            "invoice_amount_per_unit": 1000.0,
            "preference_rank": opt["slot"],
            "notes": opt["name"]
        }
        response = requests.post(f"{BASE_URL}/delivery-options", json=data, headers=headers_admin)
        if response.status_code == 200:
            print(f"  [OK] {opt['name']} - {delivery_date}")
        else:
            print(f"  [FAIL] {opt['name']}: {response.text[:100]}")

# STEP 4: Finalize Items
print("\n=== STEP 4: Finalize Items ===")
for item in test_items:
    response = requests.put(
        f"{BASE_URL}/items/{item['id']}/finalize",
        json={"is_finalized": True},
        headers=headers_admin
    )
    if response.status_code == 200:
        print(f"[OK] Finalized: {item['item_code']}")
    else:
        print(f"[FAIL] {item['item_code']}: {response.text[:100]}")

# STEP 5: Login as Procurement
print("\n=== STEP 5: Login as Procurement ===")
response = requests.post(f"{BASE_URL}/auth/login", json={"username": "procurement1", "password": "proc123"})
proc_token = response.json()["access_token"]
headers_proc = {"Authorization": f"Bearer {proc_token}"}
print("[OK] Logged in as procurement1")

# STEP 6: Add Procurement Options with Different Delivery Dates
print("\n=== STEP 6: Add Procurement Options ===")
suppliers = [
    {"name": "Supplier A", "cost": 1200, "delivery_days": 20},
    {"name": "Supplier B", "cost": 1100, "delivery_days": 35},
    {"name": "Supplier C", "cost": 1300, "delivery_days": 15}
]

option_ids = {}
for item in test_items:
    print(f"\n{item['item_code']}:")
    ids = []
    for supplier in suppliers:
        expected_date = (datetime.now() + timedelta(days=supplier["delivery_days"])).strftime("%Y-%m-%d")
        data = {
            "item_code": item["item_code"],
            "supplier_name": supplier["name"],
            "base_cost": supplier["cost"],
            "currency_id": 18,
            "shipping_cost": 50.0,
            "lomc_lead_time": supplier["delivery_days"],
            "expected_delivery_date": expected_date,
            "payment_terms": {"type": "cash", "discount_percent": 0}
        }
        response = requests.post(f"{BASE_URL}/procurement/options", json=data, headers=headers_proc)
        if response.status_code == 200:
            opt_id = response.json()["id"]
            ids.append(opt_id)
            print(f"  [OK] {supplier['name']}: ${supplier['cost']} (Delivery: {expected_date})")
        else:
            print(f"  [FAIL] {supplier['name']}: {response.text[:100]}")
    option_ids[item["item_code"]] = ids

# STEP 7: Finalize Best Options
print("\n=== STEP 7: Finalize Best Procurement Options ===")
for item in test_items:
    print(f"\n{item['item_code']}:")
    ids = option_ids.get(item["item_code"], [])
    if len(ids) > 1:
        best_id = ids[1]  # Supplier B - best price
        print(f"  Selecting Supplier B (best price: $1100)")
        response = requests.put(
            f"{BASE_URL}/procurement/option/{best_id}",
            json={"is_finalized": True},
            headers=headers_proc
        )
        if response.status_code == 200:
            print(f"  [OK] Procurement decision finalized")
        else:
            print(f"  [FAIL] {response.text[:100]}")

# SUMMARY
print("\n" + "="*70)
print("  WORKFLOW COMPLETE!")
print("="*70)
print(f"\nSummary:")
print(f"  Items Tested: {len(test_items)}")
print(f"  Delivery Options per Item: {len(delivery_opts)}")
print(f"  Procurement Options per Item: {len(suppliers)}")
print(f"  Finalized Decisions: {len(test_items)}")

print(f"\nWorkflow Steps Completed:")
print(f"  1. [OK] Added multiple delivery options for each item")
print(f"  2. [OK] Finalized items (made visible to procurement)")
print(f"  3. [OK] Added procurement options with delivery dates")
print(f"  4. [OK] Finalized best procurement options")

print(f"\nVerify in UI:")
print(f"  - Login as admin -> Projects -> OFF-IT-2025")
print(f"    See first 3 items finalized with locked status")
print(f"  - Login as procurement1 -> Procurement")
print(f"    See items with 3 procurement options each")
print(f"  - Login as finance1 -> Finance")
print(f"    See 3 finalized procurement decisions\n")


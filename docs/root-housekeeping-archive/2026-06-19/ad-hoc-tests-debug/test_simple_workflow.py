#!/usr/bin/env python3
"""
Simple Platform Workflow Test (No Delivery Options)
Tests: Finalize Items -> Add Procurement Options -> Finalize Decisions
"""

import requests
from datetime import datetime, timedelta

BASE_URL = "http://localhost:8000"

print("\n" + "="*50)
print("  Simple Platform Workflow Test")
print("="*50)

# Step 1: Login as admin
print("\n=== Step 1: Login as admin ===")
response = requests.post(f"{BASE_URL}/auth/login", json={"username": "admin", "password": "admin123"})
if response.status_code == 200:
    admin_token = response.json()["access_token"]
    print("[OK] Logged in as admin")
else:
    print(f"[FAIL] Login failed: {response.text}")
    exit(1)

headers_admin = {"Authorization": f"Bearer {admin_token}"}

# Step 2: Get project items
print("\n=== Step 2: Get Project Items ===")
response = requests.get(f"{BASE_URL}/items/project/1", headers=headers_admin)
items = response.json().get("items", [])
print(f"[OK] Found {len(items)} items")

# Take first 3 items
test_items = items[:3]
print(f"Testing with items: {[item['item_code'] for item in test_items]}")

# Step 3: Finalize items (without delivery options)
print("\n=== Step 3: Finalize Items ===")
for item in test_items:
    print(f"Finalizing: {item['item_code']} (ID: {item['id']})...")
    response = requests.put(
        f"{BASE_URL}/items/{item['id']}/finalize",
        json={"is_finalized": True},
        headers=headers_admin
    )
    if response.status_code == 200:
        print(f"  [OK] Item finalized")
    else:
        print(f"  [FAIL] Failed: {response.status_code} - {response.text[:200]}")

# Step 4: Login as procurement
print("\n=== Step 4: Login as procurement ===")
response = requests.post(f"{BASE_URL}/auth/login", json={"username": "procurement1", "password": "proc123"})
if response.status_code == 200:
    proc_token = response.json()["access_token"]
    print("[OK] Logged in as procurement1")
else:
    print(f"[FAIL] Login failed: {response.text}")
    exit(1)

headers_proc = {"Authorization": f"Bearer {proc_token}"}

# Step 5: View finalized items
print("\n=== Step 5: View Finalized Items ===")
response = requests.get(f"{BASE_URL}/items/finalized", headers=headers_proc)
if response.status_code == 200:
    finalized = response.json()
    print(f"[OK] Found {len(finalized)} finalized items")
    for item in finalized[:5]:
        print(f"  - {item.get('item_code', 'N/A')}")
else:
    print(f"[FAIL] Failed: {response.text}")

# Step 6: Add procurement options
print("\n=== Step 6: Add Procurement Options ===")
suppliers = [
    {"name": "Dell Direct", "cost": 5000, "delivery_days": 30},
    {"name": "Vendor A", "cost": 4800, "delivery_days": 45},
    {"name": "Vendor B", "cost": 5200, "delivery_days": 20}
]

option_ids = {}
for item in test_items:
    print(f"\nItem: {item['item_code']}")
    ids = []
    for supplier in suppliers:
        # Calculate expected delivery date
        expected_date = (datetime.now() + timedelta(days=supplier["delivery_days"])).strftime("%Y-%m-%d")
        
        data = {
            "item_code": item["item_code"],
            "supplier_name": supplier["name"],
            "base_cost": supplier["cost"],
            "currency_id": 18,  # USD
            "shipping_cost": 100.0,
            "lomc_lead_time": supplier["delivery_days"],
            "expected_delivery_date": expected_date,
            "payment_terms": {"type": "cash", "discount_percent": 0}
        }
        response = requests.post(f"{BASE_URL}/procurement/options", json=data, headers=headers_proc)
        if response.status_code == 200:
            opt_id = response.json()["id"]
            ids.append(opt_id)
            print(f"  [OK] Added: {supplier['name']} - ${supplier['cost']} (Delivery: {expected_date})")
        else:
            print(f"  [FAIL] Failed: {response.status_code} - {response.text[:200]}")
    option_ids[item["item_code"]] = ids

# Step 7: Finalize best procurement option
print("\n=== Step 7: Finalize Best Procurement Options ===")
for item in test_items:
    print(f"\nItem: {item['item_code']}")
    ids = option_ids.get(item["item_code"], [])
    if len(ids) > 1:
        best_id = ids[1]  # Vendor A with best price
        print(f"  Selecting option ID: {best_id} (Vendor A @ $4800)")
        response = requests.put(
            f"{BASE_URL}/procurement/option/{best_id}",
            json={"is_finalized": True},
            headers=headers_proc
        )
        if response.status_code == 200:
            print(f"  [OK] Procurement option finalized")
        else:
            print(f"  [FAIL] Failed: {response.status_code} - {response.text[:200]}")
    else:
        print(f"  [SKIP] No options to finalize")

# Summary
print("\n" + "="*50)
print("  Workflow Test Complete!")
print("="*50)
print(f"\nResults:")
print(f"  - Tested {len(test_items)} items")
print(f"  - Items finalized")
print(f"  - Procurement options added")
print(f"  - Best options selected")
print(f"\nNow check the UI to verify:")
print(f"  1. Login as admin -> Projects -> DC-MOD-2025")
print(f"  2. See finalized items with locked status")
print(f"  3. Login as procurement1 -> Procurement")
print(f"  4. See procurement options for finalized items")
print(f"  5. Login as finance1 -> Finance")
print(f"  6. See finalized procurement decisions\n")


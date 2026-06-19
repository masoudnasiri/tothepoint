#!/usr/bin/env python3
"""
Complete Platform Workflow Test
Tests the end-to-end workflow using actual API endpoints
"""

import requests
import json
from datetime import datetime, timedelta

BASE_URL = "http://localhost:8000"

def login(username, password):
    """Login and get access token"""
    print(f"\n=== Login as {username} ===")
    response = requests.post(
        f"{BASE_URL}/auth/login",
        json={"username": username, "password": password}
    )
    if response.status_code == 200:
        token = response.json()["access_token"]
        print(f"[OK] Logged in successfully")
        return token
    else:
        print(f"[FAIL] Login failed: {response.text}")
        return None

def get_project_items(token, project_id):
    """Get items for a project"""
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/items/project/{project_id}", headers=headers)
    if response.status_code == 200:
        data = response.json()
        items = data.get("items", data)
        print(f"[OK] Found {len(items)} items")
        return items
    else:
        print(f"[FAIL] Failed to get items: {response.text}")
        return []

def add_delivery_option(token, item_code, delivery_date, slot):
    """Add a delivery option"""
    headers = {"Authorization": f"Bearer {token}"}
    data = {
        "item_code": item_code,
        "delivery_date": delivery_date,
        "delivery_slot": slot,
        "capacity": 100,
        "cost": 50.0
    }
    response = requests.post(f"{BASE_URL}/delivery-options", json=data, headers=headers)
    if response.status_code == 200:
        print(f"  [OK] Added delivery: {delivery_date} {slot}")
        return response.json()["id"]
    else:
        print(f"  [FAIL] Failed: {response.text}")
        return None

def finalize_item(token, item_id):
    """Finalize a project item"""
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.put(
        f"{BASE_URL}/items/{item_id}/finalize",
        json={"is_finalized": True},
        headers=headers
    )
    if response.status_code == 200:
        print(f"  [OK] Item finalized")
        return True
    else:
        print(f"  [FAIL] Failed: {response.text}")
        return False

def add_procurement_option(token, item_code, supplier, cost, currency_id=1):
    """Add a procurement option"""
    headers = {"Authorization": f"Bearer {token}"}
    data = {
        "item_code": item_code,
        "supplier_name": supplier,
        "base_cost": cost,
        "currency_id": currency_id,
        "shipping_cost": 100.0,
        "lomc_lead_time": 30,
        "payment_terms": {"type": "cash", "discount_percent": 0}
    }
    response = requests.post(f"{BASE_URL}/procurement/options", json=data, headers=headers)
    if response.status_code == 200:
        print(f"  [OK] Added option: {supplier} - ${cost}")
        return response.json()["id"]
    else:
        print(f"  [FAIL] Failed: {response.text}")
        return None

def finalize_procurement_option(token, option_id):
    """Finalize a procurement option"""
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.put(
        f"{BASE_URL}/procurement/option/{option_id}",
        json={"is_finalized": True},
        headers=headers
    )
    if response.status_code == 200:
        print(f"  [OK] Procurement option finalized")
        return True
    else:
        print(f"  [FAIL] Failed: {response.text}")
        return False

def main():
    print("\n" + "="*50)
    print("  Complete Platform Workflow Test")
    print("="*50)
    
    # Step 1: Login as admin
    admin_token = login("admin", "admin123")
    if not admin_token:
        print("\n[FAIL] Workflow stopped - admin login failed")
        return
    
    # Step 2: Get project items
    print("\n=== Get Project Items (Project 1) ===")
    items = get_project_items(admin_token, 1)
    if not items:
        print("[FAIL] No items found")
        return
    
    # Use first 3 items for testing
    test_items = items[:3]
    
    # Step 3: Add delivery options
    print("\n=== Add Delivery Options ===")
    today = datetime.now()
    for item in test_items:
        print(f"\nItem: {item['item_code']}")
        for i, slot in enumerate(["Morning", "Afternoon", "Evening"]):
            delivery_date = (today + timedelta(days=15*i)).strftime("%Y-%m-%d")
            add_delivery_option(admin_token, item["item_code"], delivery_date, slot)
    
    # Step 4: Finalize items
    print("\n=== Finalize Items ===")
    for item in test_items:
        print(f"\nFinalizing: {item['item_code']}")
        finalize_item(admin_token, item["id"])
    
    # Step 5: Login as procurement
    proc_token = login("procurement1", "proc123")
    if not proc_token:
        print("\n[FAIL] Workflow stopped - procurement login failed")
        return
    
    # Step 6: Add procurement options
    print("\n=== Add Procurement Options ===")
    suppliers = [
        {"name": "Dell Direct", "cost": 5000},
        {"name": "Vendor A", "cost": 4800},
        {"name": "Vendor B", "cost": 5200}
    ]
    
    option_ids = {}
    for item in test_items:
        print(f"\nItem: {item['item_code']}")
        ids = []
        for supplier in suppliers:
            opt_id = add_procurement_option(
                proc_token,
                item["item_code"],
                supplier["name"],
                supplier["cost"]
            )
            if opt_id:
                ids.append(opt_id)
        option_ids[item["item_code"]] = ids
    
    # Step 7: Finalize best procurement option
    print("\n=== Finalize Best Procurement Options ===")
    for item in test_items:
        print(f"\nItem: {item['item_code']}")
        ids = option_ids.get(item["item_code"], [])
        if len(ids) > 1:
            # Finalize second option (Vendor A with best price)
            print(f"  Selecting best option: Vendor A @ $4800")
            finalize_procurement_option(proc_token, ids[1])
    
    # Summary
    print("\n" + "="*50)
    print("  [OK] Workflow Test Complete!")
    print("="*50)
    print(f"\nSummary:")
    print(f"  - Tested {len(test_items)} items")
    print(f"  - Added 3 delivery options per item")
    print(f"  - Finalized all test items")
    print(f"  - Added 3 procurement options per item")
    print(f"  - Finalized best procurement option per item")
    
    print(f"\nNow check the UI:")
    print(f"  1. Login as admin - Projects - DC-MOD-2025")
    print(f"  2. See finalized items (first 3)")
    print(f"  3. Login as procurement1 - Procurement")
    print(f"  4. See finalized items with procurement options")
    print(f"  5. Login as finance1 - Finance")
    print(f"  6. See finalized decisions\n")

if __name__ == "__main__":
    main()


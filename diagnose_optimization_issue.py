#!/usr/bin/env python3
"""
Comprehensive diagnostic for optimization issue
"""

import requests
from datetime import datetime, date

BASE_URL = "http://localhost:8000"

print("\n" + "="*80)
print("  COMPREHENSIVE OPTIMIZATION DIAGNOSTIC")
print("="*80)

# Login
print("\n[1] Login as Finance")
response = requests.post(f"{BASE_URL}/auth/login", json={"username": "finance1", "password": "finance123"})
token = response.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}
print("    [OK] Logged in")

# Check finalized items
print("\n[2] Check Finalized Items")
response = requests.get(f"{BASE_URL}/items/finalized?limit=100", headers=headers)
if response.status_code == 200:
    finalized_items = response.json()
    print(f"    Total finalized items: {len(finalized_items)}")
else:
    print(f"    [ERROR] Failed to get finalized items: {response.status_code}")
    finalized_items = []

# Check finalized procurement options
print("\n[3] Check Finalized Procurement Options")
response = requests.get(f"{BASE_URL}/procurement/options", headers=headers)
if response.status_code == 200:
    all_options = response.json()
    finalized_options = [opt for opt in all_options if opt.get("is_finalized") == True]
    print(f"    Total procurement options: {len(all_options)}")
    print(f"    Finalized procurement options: {len(finalized_options)}")
    
    # Group by item
    by_item = {}
    for opt in finalized_options:
        item_code = opt.get("item_code")
        if item_code not in by_item:
            by_item[item_code] = []
        by_item[item_code].append(opt)
    
    print(f"    Items with finalized options: {len(by_item)}")
    for item_code, opts in sorted(by_item.items()):
        print(f"        {item_code}: {len(opts)} options")
else:
    print(f"    [ERROR] Failed to get procurement options: {response.status_code}")
    finalized_options = []

# Check budget data
print("\n[4] Check Budget Data")
response = requests.get(f"{BASE_URL}/finance/budget", headers=headers)
if response.status_code == 200:
    budgets = response.json()
    print(f"    Total budget entries: {len(budgets)}")
    if budgets:
        try:
            total_budget = sum(float(b.get("available_budget", 0)) for b in budgets if b.get("available_budget"))
            print(f"    Total budget amount: {total_budget:,.2f}")
        except:
            print(f"    Could not calculate total budget")
        print(f"    Budget entries:")
        for b in budgets:
            print(f"        Date: {b.get('budget_date')} Amount: {b.get('available_budget')} Currency: {b.get('currency', 'N/A')}")
    else:
        print("    [WARNING] NO BUDGET DATA FOUND!")
        print("    This is why optimization returns 0 items - no budget available!")
else:
    print(f"    [ERROR] Failed to get budget data: {response.status_code}")

# Check delivery options
print("\n[5] Check Delivery Options for Items")
items_with_delivery = 0
items_without_delivery = 0
for item in finalized_items[:10]:  # Check first 10
    item_code = item.get("item_code")
    response = requests.get(f"{BASE_URL}/delivery-options/by-item-code/{item_code}", headers=headers)
    if response.status_code == 200 and len(response.json()) > 0:
        items_with_delivery += 1
        print(f"    {item_code}: {len(response.json())} delivery options")
    else:
        items_without_delivery += 1
        print(f"    {item_code}: NO delivery options")

print(f"\n    Items with delivery options: {items_with_delivery}")
print(f"    Items without delivery options: {items_without_delivery}")

# Summary
print("\n" + "="*80)
print("  DIAGNOSTIC SUMMARY")
print("="*80)
print(f"  Finalized Items:                {len(finalized_items)}")
print(f"  Items with Finalized Proc Opts: {len(by_item) if 'by_item' in locals() else 0}")
print(f"  Items with Delivery Options:    {items_with_delivery}")
print(f"  Budget Entries:                 {len(budgets) if 'budgets' in locals() else 0}")

if 'budgets' in locals() and len(budgets) == 0:
    print("\n  ⚠️  ISSUE IDENTIFIED: NO BUDGET DATA!")
    print("  Solution: Add budget data in Finance → Budget Management")
    print("  Without budget, the optimization cannot select any items.")
elif items_with_delivery < len(finalized_items):
    print(f"\n  ⚠️  ISSUE: {len(finalized_items) - items_with_delivery} items missing delivery options")
    print("  Solution: Add delivery options to all finalized items")
else:
    print("\n  ✅ All prerequisites met - optimization should work!")

print("="*80)

#!/usr/bin/env python3
"""
Debug optimization variables to understand the constraint issue
"""

import requests
from datetime import datetime, date

BASE_URL = "http://localhost:8000"

print("\n" + "="*80)
print("  OPTIMIZATION VARIABLES DEBUG")
print("="*80)

# Login
print("\n[1] Login as Finance")
response = requests.post(f"{BASE_URL}/auth/login", json={"username": "finance1", "password": "finance123"})
token = response.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}
print("    [OK] Logged in")

# Get finalized items with delivery options
print("\n[2] Check Finalized Items with Delivery Options")
response = requests.get(f"{BASE_URL}/items/finalized", headers=headers)
if response.status_code == 200:
    items = response.json()
    print(f"    Total finalized items: {len(items)}")
    
    # Check delivery options for each item
    items_with_delivery = 0
    for item in items[:5]:  # Check first 5
        item_code = item.get("item_code")
        response = requests.get(f"{BASE_URL}/delivery-options/by-item-code/{item_code}", headers=headers)
        if response.status_code == 200:
            delivery_options = response.json()
            if delivery_options:
                items_with_delivery += 1
                print(f"    {item_code}: {len(delivery_options)} delivery options")
                for do in delivery_options[:2]:  # Show first 2
                    delivery_date = do.get('delivery_date')
                    if delivery_date:
                        # Calculate days from today
                        today = date.today()
                        delivery_date_obj = datetime.strptime(delivery_date, '%Y-%m-%d').date()
                        days_from_today = (delivery_date_obj - today).days
                        print(f"        Delivery: {delivery_date} (day {days_from_today})")
            else:
                print(f"    {item_code}: NO delivery options")
        else:
            print(f"    {item_code}: ERROR getting delivery options")
    
    print(f"    Items with delivery options: {items_with_delivery}")
else:
    print(f"    [ERROR] Failed to get finalized items: {response.status_code}")

# Get procurement options with lead times
print("\n[3] Check Procurement Options with Lead Times")
response = requests.get(f"{BASE_URL}/procurement/options", headers=headers)
if response.status_code == 200:
    options = response.json()
    finalized_options = [opt for opt in options if opt.get("is_finalized") == True]
    
    print(f"    Total finalized options: {len(finalized_options)}")
    
    # Group by item and show lead times
    by_item = {}
    for opt in finalized_options:
        item_code = opt.get("item_code")
        if item_code not in by_item:
            by_item[item_code] = []
        by_item[item_code].append(opt)
    
    print(f"    Items with finalized options: {len(by_item)}")
    for item_code, opts in sorted(by_item.items())[:5]:  # First 5 items
        print(f"        {item_code}: {len(opts)} options")
        for opt in opts[:2]:  # First 2 options
            lead_time = opt.get('lomc_lead_time', 0)
            supplier = opt.get('supplier_name', 'Unknown')
            cost = opt.get('base_cost', 0)
            print(f"            {supplier}: lead_time={lead_time} days, cost=${cost}")

# Simulate variable creation logic
print("\n[4] Simulate Variable Creation")
print("    Simulating the optimization engine logic...")

# Get a sample item with delivery options
sample_item_code = None
sample_delivery_options = []
sample_procurement_options = []

for item_code in by_item.keys():
    response = requests.get(f"{BASE_URL}/delivery-options/by-item-code/{item_code}", headers=headers)
    if response.status_code == 200:
        delivery_options = response.json()
        if delivery_options:
            sample_item_code = item_code
            sample_delivery_options = delivery_options
            sample_procurement_options = by_item[item_code]
            break

if sample_item_code:
    print(f"    Sample item: {sample_item_code}")
    print(f"    Delivery options: {len(sample_delivery_options)}")
    print(f"    Procurement options: {len(sample_procurement_options)}")
    
    # Calculate valid times (days from today)
    today = date.today()
    valid_times = []
    for delivery_option in sample_delivery_options:
        delivery_date = delivery_option.get('delivery_date')
        if delivery_date:
            delivery_date_obj = datetime.strptime(delivery_date, '%Y-%m-%d').date()
            days_from_today = (delivery_date_obj - today).days
            if days_from_today > 0:
                valid_times.append(days_from_today)
    
    print(f"    Valid delivery times: {valid_times}")
    
    # Simulate variable creation
    variables_created = 0
    for option in sample_procurement_options:
        lead_time = option.get('lomc_lead_time', 0)
        print(f"    Option {option.get('supplier_name')} (lead_time={lead_time}):")
        
        for delivery_time in valid_times:
            purchase_time = delivery_time - lead_time
            if purchase_time < 1:
                print(f"        SKIP: delivery_time={delivery_time}, lead_time={lead_time}, purchase_time={purchase_time}")
            else:
                print(f"        CREATE: delivery_time={delivery_time}, lead_time={lead_time}, purchase_time={purchase_time}")
                variables_created += 1
    
    print(f"    Total variables that would be created: {variables_created}")
else:
    print("    [ERROR] Could not find sample item with delivery options")

print("\n" + "="*80)
print("  ANALYSIS")
print("="*80)
print("  The issue might be:")
print("  1. Delivery dates are too far in the future")
print("  2. Lead times are too long relative to delivery dates")
print("  3. Budget constraints are misaligned with time slots")
print("  4. Constraint logic has bugs")
print("="*80)

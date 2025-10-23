#!/usr/bin/env python3
"""
Test Currency Conversion in Optimization
Verify that optimization correctly converts currencies using time-variant exchange rates
"""

import requests
from datetime import datetime, date, timedelta

BASE_URL = "http://localhost:8000"

print("\n" + "="*70)
print("  Test Currency Conversion in Optimization")
print("="*70)

# Login as Finance
print("\n[1] Login as Finance")
response = requests.post(f"{BASE_URL}/auth/login", json={"username": "finance1", "password": "finance123"})
finance_token = response.json()["access_token"]
headers_finance = {"Authorization": f"Bearer {finance_token}"}
print("    [OK] Logged in")

# Add Exchange Rates for Different Dates
print("\n[2] Add Exchange Rates for Different Dates")
exchange_rates = [
    # Today - USD to IRR
    {"from_currency": "USD", "to_currency": "IRR", "date": date.today().strftime("%Y-%m-%d"), "rate": 120.0},
    # Tomorrow - USD to IRR (higher rate)
    {"from_currency": "USD", "to_currency": "IRR", "date": (date.today() + timedelta(days=1)).strftime("%Y-%m-%d"), "rate": 180.0},
    # Day after tomorrow - USD to IRR (even higher)
    {"from_currency": "USD", "to_currency": "IRR", "date": (date.today() + timedelta(days=2)).strftime("%Y-%m-%d"), "rate": 200.0},
    # EUR to IRR rates
    {"from_currency": "EUR", "to_currency": "IRR", "date": date.today().strftime("%Y-%m-%d"), "rate": 130.0},
    {"from_currency": "EUR", "to_currency": "IRR", "date": (date.today() + timedelta(days=1)).strftime("%Y-%m-%d"), "rate": 190.0},
    {"from_currency": "EUR", "to_currency": "IRR", "date": (date.today() + timedelta(days=2)).strftime("%Y-%m-%d"), "rate": 210.0},
]

for rate_data in exchange_rates:
    # Use the correct endpoint format
    response = requests.post(
        f"{BASE_URL}/currencies/rates/add",
        params={
            "date_str": rate_data["date"],
            "from_currency": rate_data["from_currency"],
            "to_currency": rate_data["to_currency"],
            "rate": rate_data["rate"]
        },
        headers=headers_finance
    )
    if response.status_code == 200:
        print(f"    [OK] Added rate: {rate_data['from_currency']} -> {rate_data['to_currency']} = {rate_data['rate']} on {rate_data['date']}")
    else:
        print(f"    [FAIL] Failed to add rate: {response.text[:80]}")

# Add Budget Data
print("\n[3] Add Budget Data")
budget_data = [
    {"budget_date": date.today().strftime("%Y-%m-%d"), "available_budget": 1000000, "currency_id": 20},  # IRR
    {"budget_date": (date.today() + timedelta(days=1)).strftime("%Y-%m-%d"), "available_budget": 2000000, "currency_id": 20},  # IRR
    {"budget_date": (date.today() + timedelta(days=2)).strftime("%Y-%m-%d"), "available_budget": 3000000, "currency_id": 20},  # IRR
]

for budget in budget_data:
    response = requests.post(f"{BASE_URL}/finance/budget", json=budget, headers=headers_finance)
    if response.status_code == 200:
        print(f"    [OK] Added budget: {budget['available_budget']} IRR on {budget['budget_date']}")
    else:
        print(f"    [FAIL] Failed to add budget: {response.text[:80]}")

# Get Project Items to Test
print("\n[4] Get Project Items")
response = requests.get(f"{BASE_URL}/items/project/1", headers=headers_finance)
items = response.json().get("items", [])
test_items = items[:2]  # Test with 2 items
print(f"    [OK] Testing with {len(test_items)} items")

# Add Procurement Options with Different Currencies and Lead Times
print("\n[5] Add Procurement Options with Multi-Currency Pricing")
procurement_options = []

# Item 1: Same item, different suppliers, different currencies, different lead times
for i, item in enumerate(test_items):
    print(f"\n    {item['item_code']}:")
    
    # Supplier A: USD pricing, 1 day lead time (purchase today, deliver tomorrow)
    data_a = {
        "item_code": item["item_code"],
        "supplier_name": f"Supplier A (USD)",
        "base_cost": 900.0,
        "currency_id": 18,  # USD
        "shipping_cost": 50.0,
        "lomc_lead_time": 1,  # 1 day lead time
        "payment_terms": {"type": "cash", "discount_percent": 0}
    }
    response = requests.post(f"{BASE_URL}/procurement/options", json=data_a, headers=headers_finance)
    if response.status_code == 200:
        opt_id_a = response.json()["id"]
        procurement_options.append(opt_id_a)
        print(f"        [OK] Supplier A: $900 USD, 1 day lead time (ID: {opt_id_a})")
    else:
        print(f"        [FAIL] Supplier A: {response.text[:80]}")
    
    # Supplier B: USD pricing, 2 day lead time (purchase today, deliver day after tomorrow)
    data_b = {
        "item_code": item["item_code"],
        "supplier_name": f"Supplier B (USD)",
        "base_cost": 850.0,
        "currency_id": 18,  # USD
        "shipping_cost": 50.0,
        "lomc_lead_time": 2,  # 2 day lead time
        "payment_terms": {"type": "cash", "discount_percent": 0}
    }
    response = requests.post(f"{BASE_URL}/procurement/options", json=data_b, headers=headers_finance)
    if response.status_code == 200:
        opt_id_b = response.json()["id"]
        procurement_options.append(opt_id_b)
        print(f"        [OK] Supplier B: $850 USD, 2 day lead time (ID: {opt_id_b})")
    else:
        print(f"        [FAIL] Supplier B: {response.text[:80]}")
    
    # Supplier C: EUR pricing, 1 day lead time
    data_c = {
        "item_code": item["item_code"],
        "supplier_name": f"Supplier C (EUR)",
        "base_cost": 800.0,
        "currency_id": 19,  # EUR
        "shipping_cost": 30.0,
        "lomc_lead_time": 1,  # 1 day lead time
        "payment_terms": {"type": "cash", "discount_percent": 0}
    }
    response = requests.post(f"{BASE_URL}/procurement/options", json=data_c, headers=headers_finance)
    if response.status_code == 200:
        opt_id_c = response.json()["id"]
        procurement_options.append(opt_id_c)
        print(f"        [OK] Supplier C: €800 EUR, 1 day lead time (ID: {opt_id_c})")
    else:
        print(f"        [FAIL] Supplier C: {response.text[:80]}")

# Run Optimization
print("\n[6] Run Optimization")
optimization_request = {
    "max_time_slots": 5,
    "include_budget_constraints": True,
    "include_priority_weights": True
}

response = requests.post(f"{BASE_URL}/finance/optimize", json=optimization_request, headers=headers_finance)
if response.status_code == 200:
    result = response.json()
    print(f"    [OK] Optimization completed")
    print(f"        Status: {result.get('status', 'Unknown')}")
    print(f"        Total Cost: {result.get('total_cost', 'N/A')}")
    print(f"        Items Selected: {len(result.get('selected_items', []))}")
    
    # Show selected items with currency conversion details
    selected_items = result.get('selected_items', [])
    print(f"\n    Selected Items:")
    for item in selected_items:
        print(f"        - {item.get('item_code', 'Unknown')}: {item.get('supplier_name', 'Unknown')}")
        print(f"          Cost: {item.get('cost_per_unit', 'N/A')} {item.get('currency', 'N/A')}")
        print(f"          Lead Time: {item.get('lead_time', 'N/A')} days")
        print(f"          Purchase Date: {item.get('purchase_date', 'N/A')}")
        print(f"          Delivery Date: {item.get('delivery_date', 'N/A')}")
else:
    print(f"    [FAIL] Optimization failed: {response.text[:200]}")

# Calculate Expected Results
print("\n[7] Expected Currency Conversion Results")
print("    Based on exchange rates:")
print(f"    - Today: USD=120 IRR, EUR=130 IRR")
print(f"    - Tomorrow: USD=180 IRR, EUR=190 IRR")
print(f"    - Day After: USD=200 IRR, EUR=210 IRR")
print("\n    Expected costs in IRR:")
print("    - Supplier A (USD $900, 1 day): $900 * 120 = 108,000 IRR (purchase today)")
print("    - Supplier B (USD $850, 2 days): $850 * 200 = 170,000 IRR (purchase today, deliver day after)")
print("    - Supplier C (EUR €800, 1 day): €800 * 130 = 104,000 IRR (purchase today)")
print("\n    Expected selection: Supplier C (lowest cost in IRR)")

print("\n" + "="*70)
print("  CURRENCY CONVERSION TEST COMPLETE")
print("="*70)
print("\nKey Points:")
print("  - Exchange rates set for different dates")
print("  - Procurement options with different currencies and lead times")
print("  - Optimization should select based on IRR cost after conversion")
print("  - Lead time affects purchase date, which affects exchange rate")
print("\nExpected Result:")
print("  Supplier C (EUR) should be selected as cheapest in IRR")
print("  despite Supplier B having lower USD price")

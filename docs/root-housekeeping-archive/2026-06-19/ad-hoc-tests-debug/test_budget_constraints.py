#!/usr/bin/env python3
"""
Test budget constraints to see if they're preventing optimization
"""

import requests
from datetime import datetime, date

BASE_URL = "http://localhost:8000"

print("\n" + "="*80)
print("  BUDGET CONSTRAINT ANALYSIS")
print("="*80)

# Login
print("\n[1] Login as Finance")
response = requests.post(f"{BASE_URL}/auth/login", json={"username": "finance1", "password": "finance123"})
token = response.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}
print("    [OK] Logged in")

# Get budget data
print("\n[2] Check Budget Data")
response = requests.get(f"{BASE_URL}/finance/budget", headers=headers)
if response.status_code == 200:
    budgets = response.json()
    print(f"    Total budget entries: {len(budgets)}")
    
    # Calculate total budget by month
    budget_by_month = {}
    for budget in budgets:
        month = budget.get('budget_date', '')[:7]  # YYYY-MM
        amount = float(budget.get('available_budget', 0))
        if month not in budget_by_month:
            budget_by_month[month] = 0
        budget_by_month[month] += amount
    
    print(f"    Budget by month:")
    for month, amount in sorted(budget_by_month.items()):
        print(f"        {month}: ${amount:,.2f}")
    
    total_budget = sum(budget_by_month.values())
    print(f"    Total budget: ${total_budget:,.2f}")
else:
    print(f"    [ERROR] Failed to get budget data: {response.status_code}")

# Get procurement options and calculate total costs
print("\n[3] Check Procurement Option Costs")
response = requests.get(f"{BASE_URL}/procurement/options", headers=headers)
if response.status_code == 200:
    options = response.json()
    finalized_options = [opt for opt in options if opt.get("is_finalized") == True]
    
    print(f"    Total finalized options: {len(finalized_options)}")
    
    # Calculate total cost if all options were selected
    total_cost = 0
    for opt in finalized_options:
        base_cost = float(opt.get('base_cost', 0))
        shipping_cost = float(opt.get('shipping_cost', 0))
        quantity = int(opt.get('quantity', 1))
        total_option_cost = (base_cost + shipping_cost) * quantity
        total_cost += total_option_cost
    
    print(f"    Total cost if ALL options selected: ${total_cost:,.2f}")
    print(f"    Budget vs Total Cost: ${total_budget:,.2f} vs ${total_cost:,.2f}")
    
    if total_cost > total_budget:
        print(f"    ⚠️  WARNING: Total cost (${total_cost:,.2f}) exceeds total budget (${total_budget:,.2f})")
        print(f"    This might be why optimization selects 0 items!")
    else:
        print(f"    ✅ Budget is sufficient for all options")
        
    # Check costs by month (if we can determine delivery months)
    print(f"\n    Sample option costs:")
    for i, opt in enumerate(finalized_options[:10]):
        base_cost = float(opt.get('base_cost', 0))
        shipping_cost = float(opt.get('shipping_cost', 0))
        quantity = int(opt.get('quantity', 1))
        total_option_cost = (base_cost + shipping_cost) * quantity
        print(f"        {opt.get('item_code')} - {opt.get('supplier_name')}: ${total_option_cost:,.2f}")
else:
    print(f"    [ERROR] Failed to get procurement options: {response.status_code}")

# Check if there are any budget constraints that might be too restrictive
print("\n[4] Budget Constraint Analysis")
print("    The optimization might be failing because:")
print("    1. Budget constraints are too tight for the time periods")
print("    2. Currency conversion issues")
print("    3. Time-based budget allocation problems")
print("    4. Constraint logic errors")

print("\n" + "="*80)
print("  RECOMMENDATION")
print("="*80)
if 'total_cost' in locals() and 'total_budget' in locals():
    if total_cost > total_budget:
        print("  ⚠️  ISSUE: Total procurement cost exceeds available budget")
        print("  Solution: Increase budget or reduce procurement options")
    else:
        print("  ✅ Budget appears sufficient")
        print("  Issue might be in constraint logic or currency conversion")
        print("  Check optimization engine budget constraint implementation")
else:
    print("  ❌ Could not analyze budget constraints")

print("="*80)

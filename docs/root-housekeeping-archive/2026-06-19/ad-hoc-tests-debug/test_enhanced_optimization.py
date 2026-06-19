#!/usr/bin/env python3
"""
Test Enhanced Optimization Endpoint
"""

import requests
import json

BASE_URL = "http://localhost:8000"

print("\n" + "="*60)
print("  Test Enhanced Optimization Endpoint")
print("="*60)

# Login as Finance
print("\n[1] Login as Finance")
response = requests.post(f"{BASE_URL}/auth/login", json={"username": "finance1", "password": "finance123"})
finance_token = response.json()["access_token"]
headers_finance = {"Authorization": f"Bearer {finance_token}"}
print("    [OK] Logged in")

# Test enhanced optimization (what frontend is calling)
print("\n[2] Test Enhanced Optimization")
params = "solver_type=CP_SAT&generate_multiple_proposals=true"
request_body = {
    "max_time_slots": 60,  # Increased to accommodate all delivery dates
    "time_limit_seconds": 300
}

print(f"    URL: {BASE_URL}/finance/optimize-enhanced?{params}")
print(f"    Body: {json.dumps(request_body, indent=2)}")

response = requests.post(
    f"{BASE_URL}/finance/optimize-enhanced?{params}", 
    json=request_body, 
    headers=headers_finance,
    timeout=60
)

print(f"    Status Code: {response.status_code}")

if response.status_code == 200:
    result = response.json()
    print(f"    [OK] Enhanced optimization completed")
    print(f"        Run ID: {result.get('run_id')}")
    print(f"        Status: {result.get('status')}")
    print(f"        Total Cost: {result.get('total_cost')}")
    print(f"        Proposals Count: {len(result.get('proposals', []))}")
    print(f"        Items Optimized: {result.get('items_optimized', 'N/A')}")
    print(f"        Message: {result.get('message', 'No message')}")
    
    # Check each proposal
    for i, proposal in enumerate(result.get('proposals', [])):
        print(f"\n        Proposal {i+1}:")
        print(f"            Strategy: {proposal.get('strategy', 'N/A')}")
        print(f"            Total Cost: {proposal.get('total_cost', 0)}")
        print(f"            Items Count: {len(proposal.get('items', []))}")
        if len(proposal.get('items', [])) > 0:
            print(f"            First 3 items: {proposal.get('items', [])[:3]}")
        else:
            print(f"            NO ITEMS SELECTED!")
else:
    print(f"    [FAIL] Enhanced optimization failed: {response.status_code}")
    print(f"        Response: {response.text[:500]}")

print("\n" + "="*60)
print("  ENHANCED OPTIMIZATION TEST COMPLETE")
print("="*60)

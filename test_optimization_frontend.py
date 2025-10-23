#!/usr/bin/env python3
"""
Test Optimization from Frontend Perspective
"""

import requests
import json
from datetime import datetime, date, timedelta

BASE_URL = "http://localhost:8000"

print("\n" + "="*60)
print("  Test Optimization from Frontend Perspective")
print("="*60)

# Login as Finance
print("\n[1] Login as Finance")
response = requests.post(f"{BASE_URL}/auth/login", json={"username": "finance1", "password": "finance123"})
finance_token = response.json()["access_token"]
headers_finance = {"Authorization": f"Bearer {finance_token}"}
print("    [OK] Logged in")

# Test optimization with frontend config
print("\n[2] Test Optimization with Frontend Config")
optimization_request = {
    "max_time_slots": 24,  # Frontend default
    "time_limit_seconds": 300,
}

print(f"    Request: {json.dumps(optimization_request, indent=2)}")

response = requests.post(f"{BASE_URL}/finance/optimize", json=optimization_request, headers=headers_finance)
print(f"    Status Code: {response.status_code}")

if response.status_code == 200:
    result = response.json()
    print(f"    [OK] Optimization completed")
    print(f"        Status: {result.get('status', 'Unknown')}")
    print(f"        Total Cost: {result.get('total_cost', 'N/A')}")
    print(f"        Items Optimized: {result.get('items_optimized', 'N/A')}")
    print(f"        Message: {result.get('message', 'No message')}")
    
    # Check if frontend should show alert
    if result.get('status') in ['OPTIMAL', 'FEASIBLE']:
        print(f"    [SUCCESS] Frontend should show alert: 'Optimization completed successfully!'")
        print(f"        Total Cost: ${result.get('total_cost', 0)}")
        print(f"        Items Optimized: {result.get('items_optimized', 0)}")
    else:
        print(f"    [FAIL] Frontend should show alert: 'Optimization failed: {result.get('message', 'Unknown error')}'")
        
else:
    print(f"    [FAIL] Optimization failed: {response.status_code}")
    print(f"        Response: {response.text[:500]}")

# Test results after optimization
print("\n[3] Test Results After Optimization")
response = requests.get(f"{BASE_URL}/finance/optimization-results", headers=headers_finance)
if response.status_code == 200:
    results = response.json()
    print(f"    [OK] Results retrieved")
    print(f"        Results Count: {len(results)}")
    
    if len(results) > 0:
        # Group by run_id like frontend does
        grouped_results = {}
        for result in results:
            run_id = result['run_id']
            if run_id not in grouped_results:
                grouped_results[run_id] = {
                    'run_id': run_id,
                    'run_timestamp': result['run_timestamp'],
                    'results': [],
                    'total_cost': 0
                }
            grouped_results[run_id]['results'].append(result)
            grouped_results[run_id]['total_cost'] += float(result.get('final_cost', 0))
        
        run_ids = list(grouped_results.keys())
        print(f"        Run IDs: {len(run_ids)}")
        print(f"        Run IDs: {run_ids[:3]}...")  # Show first 3
        
        # Show latest run
        if run_ids:
            latest_run_id = run_ids[0]
            latest_run = grouped_results[latest_run_id]
            print(f"        Latest Run: {latest_run_id}")
            print(f"        Latest Run Results: {len(latest_run['results'])}")
            print(f"        Latest Run Cost: {latest_run['total_cost']}")
    else:
        print(f"        No results found")
else:
    print(f"    [FAIL] Failed to get results: {response.status_code}")

print("\n" + "="*60)
print("  FRONTEND OPTIMIZATION TEST COMPLETE")
print("="*60)

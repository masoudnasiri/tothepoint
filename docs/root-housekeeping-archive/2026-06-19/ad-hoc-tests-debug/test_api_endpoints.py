#!/usr/bin/env python3
"""
Test script to verify procurement API endpoints
"""
import asyncio
import asyncpg
import json

async def test_api_endpoints():
    # Connect to database
    conn = await asyncpg.connect(
        host="localhost",
        port=5432,
        user="postgres",
        password="postgres",
        database="procurement_dss"
    )
    
    try:
        # Test 1: Simulate /procurement/items-with-details
        print("=== SIMULATING /procurement/items-with-details ===")
        items_query = """
        SELECT pi.item_code, pi.item_name, pi.description, pi.project_id, pi.id as project_item_id
        FROM project_items pi 
        WHERE pi.project_id IN (SELECT id FROM projects WHERE is_active = true)
        ORDER BY pi.item_code
        """
        items = await conn.fetch(items_query)
        print(f"Items API would return {len(items)} items")
        
        # Test 2: Simulate /procurement/options
        print("\n=== SIMULATING /procurement/options ===")
        options_query = """
        SELECT item_code, COUNT(*) as count
        FROM procurement_options 
        WHERE is_active = true
        GROUP BY item_code
        ORDER BY item_code
        """
        options = await conn.fetch(options_query)
        print(f"Options API would return {len(options)} items with options")
        
        # Test 3: Check for mismatches
        print("\n=== CHECKING FOR MISMATCHES ===")
        items_codes = {item['item_code'] for item in items}
        options_codes = {option['item_code'] for option in options}
        
        items_without_options = items_codes - options_codes
        options_without_items = options_codes - items_codes
        
        print(f"Items without options: {len(items_without_options)}")
        if items_without_options:
            print(f"  {list(items_without_options)}")
            
        print(f"Options without items: {len(options_without_items)}")
        if options_without_items:
            print(f"  {list(options_without_items)}")
            
        # Test 4: Check specific items from screenshot
        print("\n=== CHECKING SPECIFIC ITEMS FROM SCREENSHOT ===")
        screenshot_items = ['ROOF002', 'CONC002', 'FURN002', 'EQUIP002', 'ELEC001', 'LAND001']
        for item_code in screenshot_items:
            item_count = sum(1 for item in items if item['item_code'] == item_code)
            option_count = sum(1 for option in options if option['item_code'] == item_code)
            print(f"  {item_code}: {item_count} items, {option_count} options")
            
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(test_api_endpoints())

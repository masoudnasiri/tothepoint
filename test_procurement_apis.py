#!/usr/bin/env python3
"""
Test script to verify procurement API responses
"""
import asyncio
import asyncpg
import json

async def test_procurement_apis():
    # Connect to database
    conn = await asyncpg.connect(
        host="localhost",
        port=5432,
        user="postgres",
        password="postgres",
        database="procurement_dss"
    )
    
    try:
        # Test 1: Check items with details
        print("=== ITEMS WITH DETAILS ===")
        items_query = """
        SELECT pi.item_code, pi.description, pi.project_id
        FROM project_items pi 
        WHERE pi.project_id IN (SELECT id FROM projects WHERE is_active = true)
        ORDER BY pi.item_code
        LIMIT 10
        """
        items = await conn.fetch(items_query)
        print(f"Found {len(items)} items")
        for item in items:
            print(f"  {item['item_code']}: {item['description']}")
        
        # Test 2: Check procurement options
        print("\n=== PROCUREMENT OPTIONS ===")
        options_query = """
        SELECT item_code, COUNT(*) as count
        FROM procurement_options 
        WHERE is_active = true
        GROUP BY item_code
        ORDER BY item_code
        LIMIT 10
        """
        options = await conn.fetch(options_query)
        print(f"Found {len(options)} items with options")
        for option in options:
            print(f"  {option['item_code']}: {option['count']} options")
        
        # Test 3: Check for items with 0 options
        print("\n=== ITEMS WITH 0 OPTIONS ===")
        zero_options_query = """
        SELECT pi.item_code, pi.description
        FROM project_items pi 
        LEFT JOIN procurement_options po ON pi.item_code = po.item_code AND po.is_active = true
        WHERE pi.project_id IN (SELECT id FROM projects WHERE is_active = true)
        GROUP BY pi.item_code, pi.description
        HAVING COUNT(po.id) = 0
        ORDER BY pi.item_code
        """
        zero_options = await conn.fetch(zero_options_query)
        print(f"Found {len(zero_options)} items with 0 options")
        for item in zero_options:
            print(f"  {item['item_code']}: {item['description']}")
            
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(test_procurement_apis())

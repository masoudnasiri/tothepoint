# Frontend Option Counting Issue

## Problem
- Frontend shows items with 0 options (ROOF002, CONC002, FURN002, etc.)
- Database shows all items have active options (3-75 options each)
- This is a frontend display bug

## Root Cause Analysis
1. **Items Source**: Frontend gets items from `/procurement/items-with-details`
2. **Options Source**: Frontend gets options from `/procurement/options` 
3. **Counting Logic**: `itemOptions.length` where `itemOptions = procurementOptions.filter(opt => opt.item_code === itemCode)`

## Possible Issues
1. **API Response Mismatch**: Items API returns more items than Options API
2. **Filtering Issue**: Options API might be filtering out some options
3. **Frontend State Issue**: `procurementOptions` state might be empty or incomplete
4. **Async Loading Issue**: Options might not be loaded when items are displayed

## Debug Steps
1. Check browser console for API calls
2. Verify both API endpoints return expected data
3. Check if `procurementOptions` state is properly populated
4. Verify the filtering logic in the frontend

## Expected Fix
Either:
- Fix the frontend to only show items that have options
- Fix the option counting logic to handle missing options
- Ensure both APIs return consistent data

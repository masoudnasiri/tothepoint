# Shipping Cost Feature Implementation

## Overview
Added shipping cost support to procurement options. Users can now specify shipping costs for each procurement option, and the total cost will automatically include it in all calculations and optimizations.

## Changes Made

### 1. Database Schema
- **Added Column**: `shipping_cost` (NUMERIC(15, 2), nullable, default 0) to `procurement_options` table
- **Migration**: `add_shipping_cost_migration.sql` - safely adds the column with default value

### 2. Backend Models (`backend/app/models.py`)
- Added `shipping_cost` field to `ProcurementOption` model
- Field stores shipping cost in the same currency as `cost_amount`

### 3. Backend Schemas (`backend/app/schemas.py`)
- Added `shipping_cost` to `ProcurementOptionBase` schema (optional, default 0)
- Added `shipping_cost` to `ProcurementOptionUpdate` schema
- Includes validation: `ge=0` (must be non-negative)

### 4. Cost Calculation Logic

#### Regular Optimization Engine (`backend/app/optimization_engine.py`)
- Updated `_calculate_effective_cost()` method
- **Calculation Order**:
  1. Base cost + Shipping cost
  2. Apply cash discount (if applicable)
  3. Apply bundle discount (if applicable)
  4. Convert to base currency (IRR)

#### Enhanced Optimization Engine (`backend/app/optimization_engine_enhanced.py`)
- Updated `_calculate_effective_cost()` method
- Same calculation order as regular engine

### 5. Frontend Forms (`frontend/src/pages/ProcurementPage.tsx`)
- Added "Shipping Cost (Optional)" field to:
  - **Add Procurement Option** dialog
  - **Edit Procurement Option** dialog
- Field includes helper text: "Shipping cost in the same currency as base cost"
- Default value: 0
- Properly initialized in form state

## Usage

### For Procurement Specialists:

1. **Adding a New Procurement Option**:
   - Navigate to Procurement Plan page
   - Click "Add Option for [ITEM_CODE]"
   - Fill in Base Cost
   - Optionally add Shipping Cost (in same currency)
   - Select Currency
   - Complete other fields
   - Save

2. **Editing an Existing Option**:
   - Click Edit icon on any procurement option
   - Update Shipping Cost field as needed
   - Save changes

### Cost Calculation Example:
```
Base Cost: $1,000
Shipping Cost: $150
Cash Discount: 5%
Bundle Discount: 10% (if threshold met)

Calculation:
1. Total before discounts: $1,000 + $150 = $1,150
2. After cash discount: $1,150 × 0.95 = $1,092.50
3. After bundle discount: $1,092.50 × 0.90 = $983.25
4. Convert to IRR (if needed)
```

## Benefits

1. **Accurate Costing**: Total procurement cost now includes shipping
2. **Better Optimization**: Optimization engine considers shipping when selecting best options
3. **Transparent Pricing**: Users can see breakdown of costs
4. **Flexible**: Shipping cost is optional (defaults to 0)
5. **Multi-Currency Support**: Shipping cost uses same currency as base cost

## Testing

### Manual Testing Steps:
1. ✅ Add a new procurement option with shipping cost
2. ✅ Edit an existing option to add/modify shipping cost
3. ✅ Run optimization - verify shipping cost is included in total cost
4. ✅ Check finalized decisions - verify shipping cost is reflected
5. ✅ Verify multi-currency: shipping cost in USD/IRR

### Database Verification:
```sql
-- Check shipping_cost column exists
SELECT column_name, data_type, column_default 
FROM information_schema.columns 
WHERE table_name = 'procurement_options' 
AND column_name = 'shipping_cost';

-- View procurement options with shipping costs
SELECT id, item_code, supplier_name, cost_amount, shipping_cost, cost_currency
FROM procurement_options
WHERE shipping_cost > 0;
```

## Migration Notes

- **Backward Compatible**: Existing procurement options automatically get `shipping_cost = 0`
- **No Data Loss**: All existing data is preserved
- **Safe Rollback**: Column can be dropped if needed (though not recommended)

## Future Enhancements (Optional)

- [ ] Add shipping cost breakdown in reports
- [ ] Support different shipping costs for different delivery options
- [ ] Add shipping cost trends/analytics
- [ ] Bulk update shipping costs by supplier

## Files Modified

### Backend:
- `backend/app/models.py` - Added shipping_cost field
- `backend/app/schemas.py` - Added shipping_cost to schemas
- `backend/app/optimization_engine.py` - Updated cost calculation
- `backend/app/optimization_engine_enhanced.py` - Updated cost calculation

### Frontend:
- `frontend/src/pages/ProcurementPage.tsx` - Added shipping cost input fields

### Database:
- `add_shipping_cost_migration.sql` - Migration script

### Documentation:
- `SHIPPING_COST_FEATURE.md` - This file

---

**Implementation Date**: October 12, 2025  
**Status**: ✅ Complete and Tested


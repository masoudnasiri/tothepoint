-- ============================================
-- Link Procurement Options to Delivery Options
-- ============================================
-- Add delivery_option_id to procurement_options
-- This links each procurement option to a specific delivery option from the project item
-- ============================================

BEGIN;

-- Add delivery_option_id column to procurement_options
ALTER TABLE procurement_options 
ADD COLUMN IF NOT EXISTS delivery_option_id INTEGER REFERENCES delivery_options(id);

-- Add index for faster lookups
CREATE INDEX IF NOT EXISTS idx_procurement_options_delivery_option 
ON procurement_options(delivery_option_id);

-- Comment
COMMENT ON COLUMN procurement_options.delivery_option_id IS 
'Links to the delivery option from project item - determines actual delivery date and invoice timing';

-- Show result
SELECT 'Schema updated successfully' as status;
SELECT 'Procurement options table now linked to delivery options' as info;

COMMIT;

-- ============================================
-- USAGE:
-- ============================================
-- When adding a procurement option, also specify which delivery option it uses:
-- 
-- POST /procurement/options
-- {
--   "item_code": "DELL-LAP-001",
--   "supplier_name": "Dell Direct",
--   "base_cost": 1200,
--   "currency_id": 18,
--   "delivery_option_id": 123,  // <-- Links to project item's delivery option
--   ...
-- }
--
-- The delivery option determines:
-- - Actual delivery date
-- - Invoice timing (ABSOLUTE vs RELATIVE)
-- - Invoice issue date
-- - Invoice amount per unit
-- ============================================


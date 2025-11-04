-- ============================================
-- Update Lead Time and Delivery Dates Schema
-- ============================================
-- Change lomc_lead_time from integer (days) to date (expected delivery date)
-- Add expected_delivery_date column
-- ============================================

BEGIN;

-- Add new column for expected delivery date
ALTER TABLE procurement_options 
ADD COLUMN IF NOT EXISTS expected_delivery_date DATE;

-- Comment on columns
COMMENT ON COLUMN procurement_options.lomc_lead_time IS 'Lead time in days (deprecated - use expected_delivery_date)';
COMMENT ON COLUMN procurement_options.expected_delivery_date IS 'Expected delivery date from supplier';

-- For existing records, calculate expected delivery date from lead time
-- (Current date + lead time days)
UPDATE procurement_options 
SET expected_delivery_date = CURRENT_DATE + (COALESCE(lomc_lead_time, 30) || ' days')::INTERVAL
WHERE expected_delivery_date IS NULL AND lomc_lead_time IS NOT NULL;

-- Set default for records without lead time
UPDATE procurement_options 
SET expected_delivery_date = CURRENT_DATE + INTERVAL '30 days'
WHERE expected_delivery_date IS NULL;

SELECT 'Schema updated successfully' as status;
SELECT 'Procurement options with dates:' as info, COUNT(*) as count 
FROM procurement_options 
WHERE expected_delivery_date IS NOT NULL;

COMMIT;

-- ============================================
-- NEXT STEPS:
-- ============================================
-- 1. Update backend schemas.py to include expected_delivery_date
-- 2. Update frontend to show expected_delivery_date
-- 3. Update test scripts to use dates instead of integers
-- ============================================


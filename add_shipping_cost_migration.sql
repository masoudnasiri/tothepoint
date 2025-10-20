-- Migration: Add shipping_cost column to procurement_options table
-- Date: 2025-10-12
-- Description: Adds shipping_cost field to support shipping costs in procurement options

-- Add shipping_cost column (nullable, defaults to 0)
ALTER TABLE procurement_options 
ADD COLUMN IF NOT EXISTS shipping_cost NUMERIC(15, 2) DEFAULT 0;

-- Update existing records to have shipping_cost = 0
UPDATE procurement_options 
SET shipping_cost = 0 
WHERE shipping_cost IS NULL;

-- Add comment to document the column
COMMENT ON COLUMN procurement_options.shipping_cost IS 'Shipping cost in the same currency as cost_amount';

-- Verify the migration
SELECT 
    'Migration completed successfully' AS status,
    COUNT(*) AS total_records,
    COUNT(shipping_cost) AS records_with_shipping_cost
FROM procurement_options;


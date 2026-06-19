-- Migration: Increase invoice_amount_per_unit precision in delivery_options table
-- This allows larger invoice amounts to be stored (from Numeric(12,2) to Numeric(18,2))
-- Maximum value increases from 9,999,999,999.99 to 999,999,999,999,999,999.99

BEGIN;

-- Alter the column to increase precision
ALTER TABLE delivery_options 
ALTER COLUMN invoice_amount_per_unit TYPE NUMERIC(18, 2);

-- Verify the change
COMMENT ON COLUMN delivery_options.invoice_amount_per_unit IS 
'Invoice amount per unit. Precision increased from Numeric(12,2) to Numeric(18,2) to support larger values (max: 999,999,999,999,999,999.99)';

COMMIT;

-- Note: This migration is safe to run on existing databases
-- All existing values will be preserved, and the column will accept larger values going forward


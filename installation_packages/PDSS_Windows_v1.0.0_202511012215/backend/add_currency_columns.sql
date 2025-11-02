-- Simplified migration to add currency columns
-- Run this if columns don't exist yet

BEGIN;

-- Step 1: Add currency columns to projects
ALTER TABLE projects ADD COLUMN IF NOT EXISTS budget_amount NUMERIC(15, 2);
ALTER TABLE projects ADD COLUMN IF NOT EXISTS budget_currency VARCHAR(3) DEFAULT 'IRR';

-- Step 2: Add currency columns to procurement_options
ALTER TABLE procurement_options ADD COLUMN IF NOT EXISTS cost_amount NUMERIC(15, 2);
ALTER TABLE procurement_options ADD COLUMN IF NOT EXISTS cost_currency VARCHAR(3) DEFAULT 'IRR';

-- Migrate existing data
UPDATE procurement_options 
SET cost_amount = base_cost, cost_currency = 'IRR'
WHERE cost_amount IS NULL AND base_cost IS NOT NULL;

-- Step 3: Add currency columns to finalized_decisions
ALTER TABLE finalized_decisions ADD COLUMN IF NOT EXISTS final_cost_amount NUMERIC(15, 2);
ALTER TABLE finalized_decisions ADD COLUMN IF NOT EXISTS final_cost_currency VARCHAR(3) DEFAULT 'IRR';
ALTER TABLE finalized_decisions ADD COLUMN IF NOT EXISTS forecast_invoice_amount_value NUMERIC(15, 2);
ALTER TABLE finalized_decisions ADD COLUMN IF NOT EXISTS forecast_invoice_amount_currency VARCHAR(3) DEFAULT 'IRR';
ALTER TABLE finalized_decisions ADD COLUMN IF NOT EXISTS actual_invoice_amount_value NUMERIC(15, 2);
ALTER TABLE finalized_decisions ADD COLUMN IF NOT EXISTS actual_invoice_amount_currency VARCHAR(3) DEFAULT 'IRR';
ALTER TABLE finalized_decisions ADD COLUMN IF NOT EXISTS actual_payment_amount_value NUMERIC(15, 2);
ALTER TABLE finalized_decisions ADD COLUMN IF NOT EXISTS actual_payment_amount_currency VARCHAR(3) DEFAULT 'IRR';

-- Migrate existing data
UPDATE finalized_decisions 
SET final_cost_amount = final_cost, final_cost_currency = 'IRR'
WHERE final_cost_amount IS NULL AND final_cost IS NOT NULL;

UPDATE finalized_decisions 
SET forecast_invoice_amount_value = forecast_invoice_amount, forecast_invoice_amount_currency = 'IRR'
WHERE forecast_invoice_amount_value IS NULL AND forecast_invoice_amount IS NOT NULL;

UPDATE finalized_decisions 
SET actual_invoice_amount_value = actual_invoice_amount, actual_invoice_amount_currency = 'IRR'
WHERE actual_invoice_amount_value IS NULL AND actual_invoice_amount IS NOT NULL;

UPDATE finalized_decisions 
SET actual_payment_amount_value = actual_payment_amount, actual_payment_amount_currency = 'IRR'
WHERE actual_payment_amount_value IS NULL AND actual_payment_amount IS NOT NULL;

-- Step 4: Add currency columns to cashflow_events
ALTER TABLE cashflow_events ADD COLUMN IF NOT EXISTS amount_value NUMERIC(15, 2);
ALTER TABLE cashflow_events ADD COLUMN IF NOT EXISTS amount_currency VARCHAR(3) DEFAULT 'IRR';

-- Migrate existing data
UPDATE cashflow_events 
SET amount_value = amount, amount_currency = 'IRR'
WHERE amount_value IS NULL AND amount IS NOT NULL;

COMMIT;

-- Verify the changes
SELECT 'Projects with budget_amount' as table_check, COUNT(*) FROM projects WHERE budget_amount IS NOT NULL;
SELECT 'Procurement options with cost_amount' as table_check, COUNT(*) FROM procurement_options WHERE cost_amount IS NOT NULL;
SELECT 'Finalized decisions with final_cost_amount' as table_check, COUNT(*) FROM finalized_decisions WHERE final_cost_amount IS NOT NULL;
SELECT 'Cashflow events with amount_value' as table_check, COUNT(*) FROM cashflow_events WHERE amount_value IS NOT NULL;

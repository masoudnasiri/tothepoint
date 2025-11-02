-- Multi-Currency Architecture Migration Script
-- This script migrates the existing database to support proper multi-currency architecture
-- Run this script after updating the models to add new currency fields

BEGIN;

-- Step 1: Drop existing exchange_rates table and recreate with new structure
DROP TABLE IF EXISTS exchange_rates CASCADE;

CREATE TABLE exchange_rates (
    id SERIAL PRIMARY KEY,
    date DATE NOT NULL,
    from_currency VARCHAR(3) NOT NULL,
    to_currency VARCHAR(3) NOT NULL,
    rate NUMERIC(15, 6) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE,
    created_by_id INTEGER REFERENCES users(id),
    
    -- Constraints
    CONSTRAINT check_different_currencies CHECK (from_currency != to_currency),
    CONSTRAINT check_positive_rate CHECK (rate > 0)
);

-- Create indexes for efficient lookups
CREATE INDEX idx_exchange_rates_date ON exchange_rates(date);
CREATE INDEX idx_exchange_rates_from_currency ON exchange_rates(from_currency);
CREATE INDEX idx_exchange_rates_to_currency ON exchange_rates(to_currency);
CREATE INDEX idx_exchange_rates_from_to_date ON exchange_rates(from_currency, to_currency, date);
CREATE INDEX idx_exchange_rates_active ON exchange_rates(is_active);

-- Step 2: Add new currency fields to projects table
ALTER TABLE projects ADD COLUMN IF NOT EXISTS budget_amount NUMERIC(15, 2);
ALTER TABLE projects ADD COLUMN IF NOT EXISTS budget_currency VARCHAR(3) DEFAULT 'IRR';

-- Add constraints
ALTER TABLE projects ADD CONSTRAINT IF NOT EXISTS check_positive_budget 
    CHECK (budget_amount IS NULL OR budget_amount >= 0);

-- Step 3: Add new currency fields to procurement_options table
ALTER TABLE procurement_options ADD COLUMN IF NOT EXISTS cost_amount NUMERIC(15, 2);
ALTER TABLE procurement_options ADD COLUMN IF NOT EXISTS cost_currency VARCHAR(3) DEFAULT 'IRR';

-- Add constraints
ALTER TABLE procurement_options ADD CONSTRAINT IF NOT EXISTS check_positive_cost 
    CHECK (cost_amount > 0);

-- Migrate existing base_cost data to new fields
UPDATE procurement_options 
SET cost_amount = base_cost, cost_currency = 'IRR'
WHERE cost_amount IS NULL AND base_cost IS NOT NULL;

-- Step 4: Add new currency fields to finalized_decisions table
ALTER TABLE finalized_decisions ADD COLUMN IF NOT EXISTS final_cost_amount NUMERIC(15, 2);
ALTER TABLE finalized_decisions ADD COLUMN IF NOT EXISTS final_cost_currency VARCHAR(3) DEFAULT 'IRR';

ALTER TABLE finalized_decisions ADD COLUMN IF NOT EXISTS forecast_invoice_amount_value NUMERIC(15, 2);
ALTER TABLE finalized_decisions ADD COLUMN IF NOT EXISTS forecast_invoice_amount_currency VARCHAR(3) DEFAULT 'IRR';

ALTER TABLE finalized_decisions ADD COLUMN IF NOT EXISTS actual_invoice_amount_value NUMERIC(15, 2);
ALTER TABLE finalized_decisions ADD COLUMN IF NOT EXISTS actual_invoice_amount_currency VARCHAR(3) DEFAULT 'IRR';

ALTER TABLE finalized_decisions ADD COLUMN IF NOT EXISTS actual_payment_amount_value NUMERIC(15, 2);
ALTER TABLE finalized_decisions ADD COLUMN IF NOT EXISTS actual_payment_amount_currency VARCHAR(3) DEFAULT 'IRR';

-- Migrate existing data to new fields
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

-- Step 5: Add new currency fields to cashflow_events table
ALTER TABLE cashflow_events ADD COLUMN IF NOT EXISTS amount_value NUMERIC(15, 2);
ALTER TABLE cashflow_events ADD COLUMN IF NOT EXISTS amount_currency VARCHAR(3) DEFAULT 'IRR';

-- Migrate existing amount data to new fields
UPDATE cashflow_events 
SET amount_value = amount, amount_currency = 'IRR'
WHERE amount_value IS NULL AND amount IS NOT NULL;

-- Step 6: Insert sample exchange rates for testing
-- USD to IRR rates (historical sample data)
INSERT INTO exchange_rates (date, from_currency, to_currency, rate, is_active, created_by_id) VALUES
('2024-01-01', 'USD', 'IRR', 42000.00, TRUE, 1),
('2024-01-02', 'USD', 'IRR', 42100.00, TRUE, 1),
('2024-01-03', 'USD', 'IRR', 42050.00, TRUE, 1),
('2024-01-04', 'USD', 'IRR', 42200.00, TRUE, 1),
('2024-01-05', 'USD', 'IRR', 42150.00, TRUE, 1),
('2024-02-01', 'USD', 'IRR', 42500.00, TRUE, 1),
('2024-02-02', 'USD', 'IRR', 42600.00, TRUE, 1),
('2024-02-03', 'USD', 'IRR', 42550.00, TRUE, 1),
('2024-03-01', 'USD', 'IRR', 42800.00, TRUE, 1),
('2024-03-02', 'USD', 'IRR', 42900.00, TRUE, 1),
('2024-04-01', 'USD', 'IRR', 43000.00, TRUE, 1),
('2024-05-01', 'USD', 'IRR', 43200.00, TRUE, 1),
('2024-06-01', 'USD', 'IRR', 43500.00, TRUE, 1),
('2024-07-01', 'USD', 'IRR', 43800.00, TRUE, 1),
('2024-08-01', 'USD', 'IRR', 44000.00, TRUE, 1),
('2024-09-01', 'USD', 'IRR', 44200.00, TRUE, 1),
('2024-10-01', 'USD', 'IRR', 44500.00, TRUE, 1),
('2024-11-01', 'USD', 'IRR', 44800.00, TRUE, 1),
('2024-12-01', 'USD', 'IRR', 45000.00, TRUE, 1),
('2025-01-01', 'USD', 'IRR', 45200.00, TRUE, 1),
('2025-02-01', 'USD', 'IRR', 45500.00, TRUE, 1),
('2025-03-01', 'USD', 'IRR', 45800.00, TRUE, 1),
('2025-04-01', 'USD', 'IRR', 46000.00, TRUE, 1),
('2025-05-01', 'USD', 'IRR', 46200.00, TRUE, 1),
('2025-06-01', 'USD', 'IRR', 46500.00, TRUE, 1),
('2025-07-01', 'USD', 'IRR', 46800.00, TRUE, 1),
('2025-08-01', 'USD', 'IRR', 47000.00, TRUE, 1),
('2025-09-01', 'USD', 'IRR', 47200.00, TRUE, 1),
('2025-10-01', 'USD', 'IRR', 47500.00, TRUE, 1),
('2025-10-11', 'USD', 'IRR', 47600.00, TRUE, 1);

-- EUR to IRR rates (historical sample data)
INSERT INTO exchange_rates (date, from_currency, to_currency, rate, is_active, created_by_id) VALUES
('2024-01-01', 'EUR', 'IRR', 46000.00, TRUE, 1),
('2024-02-01', 'EUR', 'IRR', 46500.00, TRUE, 1),
('2024-03-01', 'EUR', 'IRR', 47000.00, TRUE, 1),
('2024-04-01', 'EUR', 'IRR', 47500.00, TRUE, 1),
('2024-05-01', 'EUR', 'IRR', 48000.00, TRUE, 1),
('2024-06-01', 'EUR', 'IRR', 48500.00, TRUE, 1),
('2024-07-01', 'EUR', 'IRR', 49000.00, TRUE, 1),
('2024-08-01', 'EUR', 'IRR', 49500.00, TRUE, 1),
('2024-09-01', 'EUR', 'IRR', 50000.00, TRUE, 1),
('2024-10-01', 'EUR', 'IRR', 50500.00, TRUE, 1),
('2024-11-01', 'EUR', 'IRR', 51000.00, TRUE, 1),
('2024-12-01', 'EUR', 'IRR', 51500.00, TRUE, 1),
('2025-01-01', 'EUR', 'IRR', 52000.00, TRUE, 1),
('2025-02-01', 'EUR', 'IRR', 52500.00, TRUE, 1),
('2025-03-01', 'EUR', 'IRR', 53000.00, TRUE, 1),
('2025-04-01', 'EUR', 'IRR', 53500.00, TRUE, 1),
('2025-05-01', 'EUR', 'IRR', 54000.00, TRUE, 1),
('2025-06-01', 'EUR', 'IRR', 54500.00, TRUE, 1),
('2025-07-01', 'EUR', 'IRR', 55000.00, TRUE, 1),
('2025-08-01', 'EUR', 'IRR', 55500.00, TRUE, 1),
('2025-09-01', 'EUR', 'IRR', 56000.00, TRUE, 1),
('2025-10-01', 'EUR', 'IRR', 56500.00, TRUE, 1),
('2025-10-11', 'EUR', 'IRR', 56600.00, TRUE, 1);

-- AED to IRR rates (historical sample data)
INSERT INTO exchange_rates (date, from_currency, to_currency, rate, is_active, created_by_id) VALUES
('2024-01-01', 'AED', 'IRR', 11400.00, TRUE, 1),
('2024-02-01', 'AED', 'IRR', 11500.00, TRUE, 1),
('2024-03-01', 'AED', 'IRR', 11600.00, TRUE, 1),
('2024-04-01', 'AED', 'IRR', 11700.00, TRUE, 1),
('2024-05-01', 'AED', 'IRR', 11800.00, TRUE, 1),
('2024-06-01', 'AED', 'IRR', 11900.00, TRUE, 1),
('2024-07-01', 'AED', 'IRR', 12000.00, TRUE, 1),
('2024-08-01', 'AED', 'IRR', 12100.00, TRUE, 1),
('2024-09-01', 'AED', 'IRR', 12200.00, TRUE, 1),
('2024-10-01', 'AED', 'IRR', 12300.00, TRUE, 1),
('2024-11-01', 'AED', 'IRR', 12400.00, TRUE, 1),
('2024-12-01', 'AED', 'IRR', 12500.00, TRUE, 1),
('2025-01-01', 'AED', 'IRR', 12600.00, TRUE, 1),
('2025-02-01', 'AED', 'IRR', 12700.00, TRUE, 1),
('2025-03-01', 'AED', 'IRR', 12800.00, TRUE, 1),
('2025-04-01', 'AED', 'IRR', 12900.00, TRUE, 1),
('2025-05-01', 'AED', 'IRR', 13000.00, TRUE, 1),
('2025-06-01', 'AED', 'IRR', 13100.00, TRUE, 1),
('2025-07-01', 'AED', 'IRR', 13200.00, TRUE, 1),
('2025-08-01', 'AED', 'IRR', 13300.00, TRUE, 1),
('2025-09-01', 'AED', 'IRR', 13400.00, TRUE, 1),
('2025-10-01', 'AED', 'IRR', 13500.00, TRUE, 1),
('2025-10-11', 'AED', 'IRR', 13550.00, TRUE, 1);

-- Step 7: Update some existing records to have mixed currencies for testing
-- Update some procurement options to have USD costs
UPDATE procurement_options 
SET cost_amount = base_cost * 0.000021, cost_currency = 'USD'  -- Convert IRR to USD equivalent
WHERE id IN (SELECT id FROM procurement_options ORDER BY RANDOM() LIMIT 5);

-- Update some finalized decisions to have mixed currencies
UPDATE finalized_decisions 
SET final_cost_amount = final_cost * 0.000021, final_cost_currency = 'USD'
WHERE id IN (SELECT id FROM finalized_decisions ORDER BY RANDOM() LIMIT 3);

UPDATE finalized_decisions 
SET actual_invoice_amount_value = actual_invoice_amount * 0.000021, actual_invoice_amount_currency = 'USD'
WHERE id IN (SELECT id FROM finalized_decisions ORDER BY RANDOM() LIMIT 2);

-- Update some cashflow events to have mixed currencies
UPDATE cashflow_events 
SET amount_value = amount * 0.000021, amount_currency = 'USD'
WHERE id IN (SELECT id FROM cashflow_events ORDER BY RANDOM() LIMIT 4);

-- Step 8: Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_projects_budget_currency ON projects(budget_currency);
CREATE INDEX IF NOT EXISTS idx_procurement_options_cost_currency ON procurement_options(cost_currency);
CREATE INDEX IF NOT EXISTS idx_finalized_decisions_final_cost_currency ON finalized_decisions(final_cost_currency);
CREATE INDEX IF NOT EXISTS idx_finalized_decisions_invoice_currency ON finalized_decisions(actual_invoice_amount_currency);
CREATE INDEX IF NOT EXISTS idx_finalized_decisions_payment_currency ON finalized_decisions(actual_payment_amount_currency);
CREATE INDEX IF NOT EXISTS idx_cashflow_events_amount_currency ON cashflow_events(amount_currency);

COMMIT;

-- Verification queries (run these after migration to verify data)
-- SELECT 'Exchange Rates' as table_name, COUNT(*) as record_count FROM exchange_rates
-- UNION ALL
-- SELECT 'Projects with Budget', COUNT(*) FROM projects WHERE budget_amount IS NOT NULL
-- UNION ALL
-- SELECT 'Procurement Options with Cost', COUNT(*) FROM procurement_options WHERE cost_amount IS NOT NULL
-- UNION ALL
-- SELECT 'Finalized Decisions with Cost', COUNT(*) FROM finalized_decisions WHERE final_cost_amount IS NOT NULL
-- UNION ALL
-- SELECT 'Cashflow Events with Amount', COUNT(*) FROM cashflow_events WHERE amount_value IS NOT NULL;

-- Show sample of mixed currencies
-- SELECT 'USD Procurement Options' as type, COUNT(*) as count FROM procurement_options WHERE cost_currency = 'USD'
-- UNION ALL
-- SELECT 'USD Finalized Decisions', COUNT(*) FROM finalized_decisions WHERE final_cost_currency = 'USD'
-- UNION ALL
-- SELECT 'USD Cashflow Events', COUNT(*) FROM cashflow_events WHERE amount_currency = 'USD';

-- Create test multi-currency data for dashboard testing
-- This will create projects, decisions, and cashflow events in different currencies

-- First, let's create some test projects
INSERT INTO projects (name, description, status, budget_amount, budget_currency, start_date, end_date, created_at, updated_at) VALUES
('Test Project USD', 'Test project with USD budget', 'active', 100000.00, 'USD', '2025-10-01', '2025-12-31', NOW(), NOW()),
('Test Project EUR', 'Test project with EUR budget', 'active', 80000.00, 'EUR', '2025-10-01', '2025-12-31', NOW(), NOW()),
('Test Project IRR', 'Test project with IRR budget', 'active', 5000000000.00, 'IRR', '2025-10-01', '2025-12-31', NOW(), NOW());

-- Get the project IDs we just created
-- Create some finalized decisions with different currencies
INSERT INTO finalized_decisions (
    project_id, project_item_id, procurement_option_id, 
    supplier_name, item_code, item_name, description,
    final_cost_amount, final_cost_currency,
    forecast_invoice_amount_value, forecast_invoice_amount_currency,
    actual_invoice_amount_value, actual_invoice_amount_currency,
    status, created_at, updated_at
) VALUES
(1, NULL, NULL, 'USD Supplier', 'ITEM001', 'USD Item', 'Item in USD', 50000.00, 'USD', 50000.00, 'USD', 50000.00, 'USD', 'LOCKED', NOW(), NOW()),
(2, NULL, NULL, 'EUR Supplier', 'ITEM002', 'EUR Item', 'Item in EUR', 40000.00, 'EUR', 40000.00, 'EUR', 40000.00, 'EUR', 'LOCKED', NOW(), NOW()),
(3, NULL, NULL, 'IRR Supplier', 'ITEM003', 'IRR Item', 'Item in IRR', 2500000000.00, 'IRR', 2500000000.00, 'IRR', 2500000000.00, 'IRR', 'LOCKED', NOW(), NOW());

-- Create cashflow events with different currencies
INSERT INTO cashflow_events (
    related_decision_id, event_type, forecast_type, event_date,
    amount_value, amount_currency,
    description, is_cancelled, created_at, updated_at
) VALUES
-- USD events
(1, 'OUTFLOW', 'FORECAST', '2025-10-15', 50000.00, 'USD', 'USD Payment Forecast', false, NOW(), NOW()),
(1, 'OUTFLOW', 'ACTUAL', '2025-10-20', 50000.00, 'USD', 'USD Payment Actual', false, NOW(), NOW()),
-- EUR events  
(2, 'OUTFLOW', 'FORECAST', '2025-10-15', 40000.00, 'EUR', 'EUR Payment Forecast', false, NOW(), NOW()),
(2, 'OUTFLOW', 'ACTUAL', '2025-10-20', 40000.00, 'EUR', 'EUR Payment Actual', false, NOW(), NOW()),
-- IRR events
(3, 'OUTFLOW', 'FORECAST', '2025-10-15', 2500000000.00, 'IRR', 'IRR Payment Forecast', false, NOW(), NOW()),
(3, 'OUTFLOW', 'ACTUAL', '2025-10-20', 2500000000.00, 'IRR', 'IRR Payment Actual', false, NOW(), NOW());

-- Update budget data to have multi-currency amounts
UPDATE budget_data SET 
    multi_currency_budget = '{"USD": 100000, "EUR": 80000}'::jsonb
WHERE budget_date = '2025-10-01';

UPDATE budget_data SET 
    multi_currency_budget = '{"USD": 120000, "EUR": 90000}'::jsonb  
WHERE budget_date = '2025-11-01';

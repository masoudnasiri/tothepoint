-- Create test multi-currency data for dashboard testing
-- Using correct column names from the actual database schema

-- First, let's create some test projects
INSERT INTO projects (project_code, name, priority_weight, budget_amount, budget_currency, is_active) VALUES
('TEST-USD-001', 'Test Project USD', 5, 100000.00, 'USD', true),
('TEST-EUR-002', 'Test Project EUR', 5, 80000.00, 'EUR', true),
('TEST-IRR-003', 'Test Project IRR', 5, 5000000000.00, 'IRR', true);

-- Create some finalized decisions with different currencies
INSERT INTO finalized_decisions (
    project_id, procurement_option_id, 
    item_code, item_name,
    final_cost_amount, final_cost_currency,
    forecast_invoice_amount_value, forecast_invoice_amount_currency,
    actual_invoice_amount_value, actual_invoice_amount_currency,
    status
) VALUES
(1, NULL, 'ITEM001', 'USD Item', 50000.00, 'USD', 50000.00, 'USD', 50000.00, 'USD', 'LOCKED'),
(2, NULL, 'ITEM002', 'EUR Item', 40000.00, 'EUR', 40000.00, 'EUR', 40000.00, 'EUR', 'LOCKED'),
(3, NULL, 'ITEM003', 'IRR Item', 2500000000.00, 'IRR', 2500000000.00, 'IRR', 2500000000.00, 'IRR', 'LOCKED');

-- Create cashflow events with different currencies
INSERT INTO cashflow_events (
    related_decision_id, event_type, forecast_type, event_date,
    amount_value, amount_currency,
    description, is_cancelled
) VALUES
-- USD events
(1, 'OUTFLOW', 'FORECAST', '2025-10-15', 50000.00, 'USD', 'USD Payment Forecast', false),
(1, 'OUTFLOW', 'ACTUAL', '2025-10-20', 50000.00, 'USD', 'USD Payment Actual', false),
-- EUR events  
(2, 'OUTFLOW', 'FORECAST', '2025-10-15', 40000.00, 'EUR', 'EUR Payment Forecast', false),
(2, 'OUTFLOW', 'ACTUAL', '2025-10-20', 40000.00, 'EUR', 'EUR Payment Actual', false),
-- IRR events
(3, 'OUTFLOW', 'FORECAST', '2025-10-15', 2500000000.00, 'IRR', 'IRR Payment Forecast', false),
(3, 'OUTFLOW', 'ACTUAL', '2025-10-20', 2500000000.00, 'IRR', 'IRR Payment Actual', false);

-- Update budget data to have multi-currency amounts
UPDATE budget_data SET 
    multi_currency_budget = '{"USD": 100000, "EUR": 80000}'::jsonb
WHERE budget_date = '2025-10-01';

UPDATE budget_data SET 
    multi_currency_budget = '{"USD": 120000, "EUR": 90000}'::jsonb  
WHERE budget_date = '2025-11-01';

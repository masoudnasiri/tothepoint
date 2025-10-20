-- Create simple multi-currency cashflow events for dashboard testing
-- This will create events directly without requiring complex finalized_decisions

-- First, let's create some test projects (we need these for the foreign key)
INSERT INTO projects (project_code, name, priority_weight, budget_amount, budget_currency, is_active) VALUES
('TEST-USD-001', 'Test Project USD', 5, 100000.00, 'USD', true),
('TEST-EUR-002', 'Test Project EUR', 5, 80000.00, 'EUR', true),
('TEST-IRR-003', 'Test Project IRR', 5, 5000000000.00, 'IRR', true);

-- Create cashflow events with different currencies (without related_decision_id for now)
INSERT INTO cashflow_events (
    event_type, forecast_type, event_date,
    amount, amount_value, amount_currency,
    description, is_cancelled
) VALUES
-- USD events
('OUTFLOW', 'FORECAST', '2025-10-15', 50000.00, 50000.00, 'USD', 'USD Payment Forecast', false),
('OUTFLOW', 'ACTUAL', '2025-10-20', 50000.00, 50000.00, 'USD', 'USD Payment Actual', false),
-- EUR events  
('OUTFLOW', 'FORECAST', '2025-10-15', 40000.00, 40000.00, 'EUR', 'EUR Payment Forecast', false),
('OUTFLOW', 'ACTUAL', '2025-10-20', 40000.00, 40000.00, 'EUR', 'EUR Payment Actual', false),
-- IRR events
('OUTFLOW', 'FORECAST', '2025-10-15', 2500000000.00, 2500000000.00, 'IRR', 'IRR Payment Forecast', false),
('OUTFLOW', 'ACTUAL', '2025-10-20', 2500000000.00, 2500000000.00, 'IRR', 'IRR Payment Actual', false);

-- Update budget data to have multi-currency amounts
UPDATE budget_data SET 
    multi_currency_budget = '{"USD": 100000, "EUR": 80000}'::jsonb
WHERE budget_date = '2025-10-01';

UPDATE budget_data SET 
    multi_currency_budget = '{"USD": 120000, "EUR": 90000}'::jsonb  
WHERE budget_date = '2025-11-01';

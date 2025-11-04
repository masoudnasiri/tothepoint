-- Simple Reset - No transaction, clear errors
-- Delete data
DELETE FROM optimization_results;
DELETE FROM optimization_runs;
DELETE FROM finalized_decisions;
DELETE FROM cashflow_events;
DELETE FROM budget_data;
DELETE FROM delivery_options;
DELETE FROM procurement_options;
DELETE FROM project_assignments;
DELETE FROM project_phases;
DELETE FROM project_items;
DELETE FROM projects;
DELETE FROM items_master;
DELETE FROM exchange_rates;
DELETE FROM currencies;
DELETE FROM users WHERE username != 'admin';

-- Currencies
INSERT INTO currencies (code, name, symbol, is_base_currency, is_active, decimal_places)
VALUES 
    ('USD', 'US Dollar', '$', true, true, 2),
    ('IRR', 'Iranian Rial', '﷼', false, true, 0)
ON CONFLICT (code) DO UPDATE 
SET is_base_currency = EXCLUDED.is_base_currency;

-- Exchange rates
INSERT INTO exchange_rates (from_currency, to_currency, rate, date, is_active)
VALUES 
    ('USD', 'IRR', 42000.00, CURRENT_DATE, true),
    ('IRR', 'USD', 0.000024, CURRENT_DATE, true);

-- Users  
INSERT INTO users (username, password_hash, role, is_active)
VALUES 
    ('pmo_user', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5aX7V5mXq5Xc2', 'pmo', true),
    ('pm1', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5aX7V5mXq5Xc2', 'pm', true),
    ('procurement1', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5aX7V5mXq5Xc2', 'procurement', true),
    ('finance1', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5aX7V5mXq5Xc2', 'finance', true)
ON CONFLICT (username) DO NOTHING;

-- Items Master
INSERT INTO items_master (item_code, company, item_name, model, category, unit, description)
VALUES
    ('DELL-LAT5540', 'Dell', 'Latitude 5540 Laptop', '2024 Model', 'Laptops', 'piece', 'Dell Latitude 5540 - Core i7, 16GB, 512GB SSD'),
    ('DELL-R750', 'Dell', 'PowerEdge R750 Server', 'Rack Mount', 'Servers', 'piece', 'Dell PowerEdge R750 - Dual Xeon, 128GB'),
    ('HP-EB840', 'HP', 'EliteBook 840 G10', 'Business', 'Laptops', 'piece', 'HP EliteBook 840 - Core i7, 16GB'),
    ('HP-DL380', 'HP', 'ProLiant DL380 Gen11', 'Server', 'Servers', 'piece', 'HP ProLiant DL380 - Dual EPYC'),
    ('CISCO-C9300', 'Cisco', 'Catalyst 9300 Switch', '48-Port', 'Networking', 'piece', 'Cisco 48-Port Gigabit Switch');

-- Projects
INSERT INTO projects (name, description, start_date, end_date)
VALUES
    ('IT Infrastructure Upgrade 2025', 'IT infrastructure upgrade', '2025-01-01', '2025-12-31'),
    ('Office Equipment', 'Office equipment procurement', '2025-02-01', '2025-08-31');

-- Project Items (Finalized)
INSERT INTO project_items (project_id, item_code, item_name, quantity, delivery_options, description, status, external_purchase, is_finalized, finalized_by, finalized_at)
VALUES
    ((SELECT id FROM projects WHERE name LIKE 'IT%' LIMIT 1), 'DELL-LAT5540', 'Latitude 5540', 25, '["2025-04-15"]', 'Dev team', 'PENDING', false, true, (SELECT id FROM users WHERE username='pmo_user'), NOW() - INTERVAL '5 days'),
    ((SELECT id FROM projects WHERE name LIKE 'IT%' LIMIT 1), 'DELL-R750', 'R750 Server', 3, '["2025-03-30"]', 'App servers', 'PENDING', false, true, (SELECT id FROM users WHERE username='pmo_user'), NOW() - INTERVAL '5 days'),
    ((SELECT id FROM projects WHERE name LIKE 'IT%' LIMIT 1), 'CISCO-C9300', 'C9300 Switch', 5, '["2025-03-15"]', 'Network', 'PENDING', false, true, (SELECT id FROM users WHERE username='pmo_user'), NOW() - INTERVAL '5 days'),
    ((SELECT id FROM projects WHERE name LIKE 'Office%' LIMIT 1), 'HP-EB840', 'EliteBook 840', 30, '["2025-04-01"]', 'Management', 'PENDING', false, true, (SELECT id FROM users WHERE username='pmo_user'), NOW() - INTERVAL '5 days'),
    ((SELECT id FROM projects WHERE name LIKE 'Office%' LIMIT 1), 'HP-DL380', 'DL380 Server', 8, '["2025-06-01"]', 'Database', 'PENDING', false, true, (SELECT id FROM users WHERE username='pmo_user'), NOW() - INTERVAL '5 days');

-- Procurement Options (USD)
INSERT INTO procurement_options (item_code, supplier_name, base_cost, currency_id, shipping_cost, lomc_lead_time, payment_terms, is_finalized)
VALUES
    ('DELL-LAT5540', 'Dell Direct USA', 1200.00, (SELECT id FROM currencies WHERE code='USD'), 60.00, 15, '{"type": "cash", "discount_percent": 2.0}', false),
    ('DELL-R750', 'Dell Enterprise', 8500.00, (SELECT id FROM currencies WHERE code='USD'), 425.00, 30, '{"type": "cash", "discount_percent": 2.0}', false),
    ('CISCO-C9300', 'Cisco Authorized', 12000.00, (SELECT id FROM currencies WHERE code='USD'), 600.00, 20, '{"type": "cash", "discount_percent": 2.0}', false),
    ('HP-EB840', 'HP Store', 1300.00, (SELECT id FROM currencies WHERE code='USD'), 65.00, 15, '{"type": "cash", "discount_percent": 2.0}', false),
    ('HP-DL380', 'HP Enterprise', 15000.00, (SELECT id FROM currencies WHERE code='USD'), 750.00, 35, '{"type": "cash", "discount_percent": 2.0}', false);

-- Procurement Options (IRR)
INSERT INTO procurement_options (item_code, supplier_name, base_cost, currency_id, shipping_cost, lomc_lead_time, payment_terms, is_finalized)
VALUES
    ('DELL-LAT5540', 'IT Distributor Tehran', 52000000.00, (SELECT id FROM currencies WHERE code='IRR'), 2600000.00, 20, '{"type": "cash", "discount_percent": 0}', false),
    ('DELL-R750', 'Server Solutions Iran', 370000000.00, (SELECT id FROM currencies WHERE code='IRR'), 18500000.00, 45, '{"type": "cash", "discount_percent": 0}', false),
    ('CISCO-C9300', 'Network Equipment Co', 520000000.00, (SELECT id FROM currencies WHERE code='IRR'), 26000000.00, 30, '{"type": "cash", "discount_percent": 0}', false),
    ('HP-EB840', 'Tehran Computer', 56000000.00, (SELECT id FROM currencies WHERE code='IRR'), 2800000.00, 10, '{"type": "cash", "discount_percent": 0}', false),
    ('HP-DL380', 'Data Center Iran', 650000000.00, (SELECT id FROM currencies WHERE code='IRR'), 32500000.00, 50, '{"type": "cash", "discount_percent": 0}', false);

-- Summary
SELECT '=== DATA RESET COMPLETE ===' as status;
SELECT 'Finalized Items: ' || COUNT(*)::text FROM project_items WHERE is_finalized = true;
SELECT 'Procurement Options: ' || COUNT(*)::text FROM procurement_options;
SELECT 'USD Options: ' || COUNT(*)::text FROM procurement_options WHERE currency_id = (SELECT id FROM currencies WHERE code='USD');
SELECT 'IRR Options: ' || COUNT(*)::text FROM procurement_options WHERE currency_id = (SELECT id FROM currencies WHERE code='IRR');


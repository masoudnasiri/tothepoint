-- PDSS Complete Data Reset and Reseed
-- Handles all foreign keys and creates fresh USD/IRR data

BEGIN;

-- Step 1: Delete all operational data in correct order
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

SELECT '✅ Step 1: Old data deleted' as status;

-- Step 2: Create currencies
INSERT INTO currencies (code, name, symbol, is_base, active, decimal_places)
VALUES ('USD', 'US Dollar', '$', true, true, 2)
ON CONFLICT (code) DO UPDATE SET is_base = true, active = true;

INSERT INTO currencies (code, name, symbol, is_base, active, decimal_places)
VALUES ('IRR', 'Iranian Rial', '﷼', false, true, 0)
ON CONFLICT (code) DO UPDATE SET is_base = false, active = true;

SELECT '✅ Step 2: Currencies created' as status;

-- Step 3: Exchange rates (1 USD = 42,000 IRR)
INSERT INTO exchange_rates (from_currency, to_currency, rate, date, source)
SELECT 
    (SELECT id FROM currencies WHERE code = 'IRR'),
    (SELECT id FROM currencies WHERE code = 'USD'),
    0.0000238,  -- 1 IRR = 0.0000238 USD
    CURRENT_DATE,
    'Manual'
WHERE EXISTS (SELECT 1 FROM currencies WHERE code = 'IRR');

INSERT INTO exchange_rates (from_currency, to_currency, rate, date, source)
SELECT 
    (SELECT id FROM currencies WHERE code = 'USD'),
    (SELECT id FROM currencies WHERE code = 'IRR'),
    42000.0,  -- 1 USD = 42,000 IRR
    CURRENT_DATE,
    'Manual'
WHERE EXISTS (SELECT 1 FROM currencies WHERE code = 'USD');

SELECT '✅ Step 3: Exchange rates set' as status;

-- Step 4: Create users
-- Password hash for all test users (password123)
INSERT INTO users (username, password_hash, role, is_active)
VALUES 
    ('pmo_user', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5aX7V5mXq5Xc2', 'pmo', true),
    ('pm1', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5aX7V5mXq5Xc2', 'pm', true),
    ('procurement1', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5aX7V5mXq5Xc2', 'procurement', true),
    ('finance1', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5aX7V5mXq5Xc2', 'finance', true)
ON CONFLICT (username) DO NOTHING;

SELECT '✅ Step 4: Users created' as status;

-- Step 5: Create items master
INSERT INTO items_master (item_code, company, item_name, model, category, unit, description)
VALUES
    ('DELL-L5540', 'Dell', 'Latitude 5540 Laptop', 'Latest Model', 'Laptops', 'piece', 'Dell Latitude 5540 Business Laptop'),
    ('DELL-R750', 'Dell', 'PowerEdge R750 Server', 'Rack Server', 'Servers', 'piece', 'Dell PowerEdge R750 Rack Server'),
    ('CISCO-C9300', 'Cisco', 'Catalyst 9300 Switch', '48 Port', 'Networking', 'piece', 'Cisco Catalyst 9300 48-Port Switch'),
    ('HP-EB840', 'HP', 'EliteBook 840 G10', 'Business Laptop', 'Laptops', 'piece', 'HP EliteBook 840 G10'),
    ('HP-DL380', 'HP', 'ProLiant DL380 Gen11', 'Rack Server', 'Servers', 'piece', 'HP ProLiant DL380 Gen11 Server')
ON CONFLICT (item_code) DO NOTHING;

SELECT '✅ Step 5: Items master created' as status;

-- Step 6: Create projects
INSERT INTO projects (name, description, start_date, end_date)
VALUES
    ('IT Infrastructure Upgrade 2025', 'Complete IT infrastructure upgrade including servers and networking', '2025-01-01', '2025-12-31'),
    ('Office Equipment Procurement', 'New office equipment for headquarters expansion', '2025-02-01', '2025-08-31')
RETURNING id, name;

SELECT '✅ Step 6: Projects created' as status;

-- Step 7: Create finalized project items
WITH pmo AS (SELECT id FROM users WHERE username = 'pmo_user' LIMIT 1)
INSERT INTO project_items (project_id, item_code, item_name, quantity, delivery_options, description, status, is_finalized, finalized_by, finalized_at, external_purchase)
VALUES
    ((SELECT id FROM projects WHERE name LIKE 'IT Infrastructure%' LIMIT 1), 'DELL-L5540', 'Latitude 5540 Laptop', 25, '["2025-04-15"]', 'For development team', 'PENDING', true, (SELECT id FROM pmo), NOW() - INTERVAL '5 days', false),
    ((SELECT id FROM projects WHERE name LIKE 'IT Infrastructure%' LIMIT 1), 'DELL-R750', 'PowerEdge R750 Server', 3, '["2025-03-30"]', 'Application servers', 'PENDING', true, (SELECT id FROM pmo), NOW() - INTERVAL '5 days', false),
    ((SELECT id FROM projects WHERE name LIKE 'IT Infrastructure%' LIMIT 1), 'CISCO-C9300', 'Catalyst 9300 Switch', 5, '["2025-03-15"]', 'Core network switches', 'PENDING', true, (SELECT id FROM pmo), NOW() - INTERVAL '5 days', false),
    ((SELECT id FROM projects WHERE name LIKE 'Office%' LIMIT 1), 'HP-EB840', 'EliteBook 840 G10', 30, '["2025-04-01"]', 'For management team', 'PENDING', true, (SELECT id FROM pmo), NOW() - INTERVAL '5 days', false),
    ((SELECT id FROM projects WHERE name LIKE 'Office%' LIMIT 1), 'HP-DL380', 'ProLiant DL380 Gen11', 8, '["2025-06-01"]', 'Database servers', 'PENDING', true, (SELECT id FROM pmo), NOW() - INTERVAL '5 days', false);

SELECT '✅ Step 7: Project items created and finalized' as status;

-- Step 8: Create procurement options with mixed USD/IRR pricing
WITH usd AS (SELECT id FROM currencies WHERE code = 'USD' LIMIT 1),
     irr AS (SELECT id FROM currencies WHERE code = 'IRR' LIMIT 1)
INSERT INTO procurement_options (item_id, item_code, supplier_name, base_cost, currency_id, shipping_cost, lead_time_days, payment_terms, finalized)
-- Dell Laptop: 2 options (USD and IRR)
SELECT pi.id, pi.item_code, 'Dell Direct USA', 1200.00, usd.id, 60.00, 15, '{"type": "cash", "discount_percent": 0.02}', false
FROM project_items pi, usd WHERE pi.item_code = 'DELL-L5540'
UNION ALL
SELECT pi.id, pi.item_code, 'Local IT Distributor', 52000000.00, irr.id, 2600000.00, 20, '{"type": "cash", "discount_percent": 0}', false
FROM project_items pi, irr WHERE pi.item_code = 'DELL-L5540'
UNION ALL
-- Dell Server: 2 options
SELECT pi.id, pi.item_code, 'Dell Enterprise', 8500.00, usd.id, 425.00, 30, '{"type": "cash", "discount_percent": 0.02}', false
FROM project_items pi, usd WHERE pi.item_code = 'DELL-R750'
UNION ALL
SELECT pi.id, pi.item_code, 'Server Solutions Iran', 370000000.00, irr.id, 18500000.00, 45, '{"type": "cash", "discount_percent": 0}', false
FROM project_items pi, irr WHERE pi.item_code = 'DELL-R750'
UNION ALL
-- Cisco Switch: 2 options
SELECT pi.id, pi.item_code, 'Cisco Authorized', 12000.00, usd.id, 600.00, 20, '{"type": "cash", "discount_percent": 0.02}', false
FROM project_items pi, usd WHERE pi.item_code = 'CISCO-C9300'
UNION ALL
SELECT pi.id, pi.item_code, 'Network Equipment Co', 520000000.00, irr.id, 26000000.00, 30, '{"type": "cash", "discount_percent": 0}', false
FROM project_items pi, irr WHERE pi.item_code = 'CISCO-C9300'
UNION ALL
-- HP Laptop: 2 options
SELECT pi.id, pi.item_code, 'HP Store', 1300.00, usd.id, 65.00, 15, '{"type": "cash", "discount_percent": 0.02}', false
FROM project_items pi, usd WHERE pi.item_code = 'HP-EB840'
UNION ALL
SELECT pi.id, pi.item_code, 'Tehran Computer Market', 56000000.00, irr.id, 2800000.00, 10, '{"type": "cash", "discount_percent": 0}', false
FROM project_items pi, irr WHERE pi.item_code = 'HP-EB840'
UNION ALL
-- HP Server: 2 options
SELECT pi.id, pi.item_code, 'HP Enterprise', 15000.00, usd.id, 750.00, 35, '{"type": "cash", "discount_percent": 0.02}', false
FROM project_items pi, usd WHERE pi.item_code = 'HP-DL380'
UNION ALL
SELECT pi.id, pi.item_code, 'Data Center Equipment', 650000000.00, irr.id, 32500000.00, 50, '{"type": "cash", "discount_percent": 0}', false
FROM project_items pi, irr WHERE pi.item_code = 'HP-DL380';

SELECT '✅ Step 8: Procurement options created with USD/IRR pricing' as status;

COMMIT;

-- Show summary
SELECT '========== DATA RESET COMPLETE ==========' as "Status";
SELECT 'Table Counts:' as "Summary";
SELECT 'Currencies' as table_name, COUNT(*) as count FROM currencies
UNION ALL SELECT 'Users', COUNT(*) FROM users
UNION ALL SELECT 'Items Master', COUNT(*) FROM items_master
UNION ALL SELECT 'Projects', COUNT(*) FROM projects
UNION ALL SELECT 'Project Items', COUNT(*) FROM project_items
UNION ALL SELECT 'Finalized Items', COUNT(*) FROM project_items WHERE is_finalized = true
UNION ALL SELECT 'Procurement Options', COUNT(*) FROM procurement_options;

SELECT 'Currency Breakdown:' as "Options by Currency";
SELECT c.code as currency, COUNT(*) as options_count
FROM procurement_options po
JOIN currencies c ON c.id = po.currency_id
GROUP BY c.code
ORDER BY c.code;

SELECT '===========================================' as "Status";
SELECT 'Login Credentials:' as "Info";
SELECT 'Admin: admin / admin123' as credentials
UNION ALL SELECT 'PMO: pmo_user / pmo123'
UNION ALL SELECT 'PM: pm1 / pm123'
UNION ALL SELECT 'Procurement: procurement1 / proc123'
UNION ALL SELECT 'Finance: finance1 / finance123';

SELECT 'Refresh your browser to see the new data!' as "Next Step";


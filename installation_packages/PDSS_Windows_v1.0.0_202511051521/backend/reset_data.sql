-- PDSS Data Reset and Reseed SQL Script
-- Run this to wipe data and create fresh test data with USD/IRR pricing

-- Step 1: Delete operational data
DELETE FROM decisions;
DELETE FROM delivery_options;
DELETE FROM procurement_options;
DELETE FROM project_items;
DELETE FROM projects;
DELETE FROM items_master;
DELETE FROM exchange_rates;
DELETE FROM currencies;
DELETE FROM users WHERE username != 'admin';

-- Step 2: Create currencies
INSERT INTO currencies (code, name, symbol, is_base_currency, is_active, decimal_places)
VALUES ('USD', 'US Dollar', '$', true, true, 2)
ON CONFLICT (code) DO NOTHING;

INSERT INTO currencies (code, name, symbol, is_base_currency, is_active, decimal_places)
VALUES ('IRR', 'Iranian Rial', '﷼', false, true, 0)
ON CONFLICT (code) DO NOTHING;

-- Step 3: Create exchange rates
INSERT INTO exchange_rates (currency_id, rate, effective_date, is_active)
SELECT id, 42000.0, NOW(), true
FROM currencies WHERE code = 'IRR';

-- Step 4: Create users (password: pmo123, pm123, etc.)
-- Note: These are bcrypt hashes of the passwords
INSERT INTO users (username, password_hash, role, is_active)
VALUES 
  ('pmo_user', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5aX7V5mXq5Xc2', 'pmo', true),
  ('pm1', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5aX7V5mXq5Xc2', 'pm', true),
  ('procurement1', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5aX7V5mXq5Xc2', 'procurement', true),
  ('finance1', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5aX7V5mXq5Xc2', 'finance', true)
ON CONFLICT (username) DO NOTHING;

-- Step 5: Create items master
INSERT INTO items_master (company, item_name, model, category, unit, description)
VALUES
  ('Dell', 'Latitude 5540 Laptop', 'Latest Model', 'Laptops', 'piece', 'Dell Latitude 5540 Laptop'),
  ('Dell', 'PowerEdge R750 Server', 'Rack Server', 'Servers', 'piece', 'Dell PowerEdge R750 Server'),
  ('Cisco', 'Catalyst 9300 Switch', '48 Port', 'Networking', 'piece', 'Cisco Catalyst 9300 Switch'),
  ('HP', 'EliteBook 840 G10', 'Business Laptop', 'Laptops', 'piece', 'HP EliteBook 840 G10'),
  ('HP', 'ProLiant DL380 Gen11', 'Rack Server', 'Servers', 'piece', 'HP ProLiant DL380 Gen11');

-- Step 6: Create projects
INSERT INTO projects (name, budget, description, start_date, end_date)
VALUES
  ('IT Infrastructure Upgrade 2025', 250000.00, 'Complete IT infrastructure upgrade', '2025-01-01', '2025-12-31'),
  ('Office Equipment Procurement', 150000.00, 'New office equipment for headquarters', '2025-02-01', '2025-08-31');

-- Step 7: Create project items (finalized)
WITH pmo AS (SELECT id FROM users WHERE username = 'pmo_user' LIMIT 1),
     proj1 AS (SELECT id FROM projects WHERE name = 'IT Infrastructure Upgrade 2025' LIMIT 1),
     proj2 AS (SELECT id FROM projects WHERE name = 'Office Equipment Procurement' LIMIT 1),
     item1 AS (SELECT id FROM items_master WHERE company = 'Dell' AND item_name = 'Latitude 5540 Laptop' LIMIT 1),
     item2 AS (SELECT id FROM items_master WHERE company = 'Dell' AND item_name = 'PowerEdge R750 Server' LIMIT 1),
     item3 AS (SELECT id FROM items_master WHERE company = 'Cisco' AND item_name = 'Catalyst 9300 Switch' LIMIT 1),
     item4 AS (SELECT id FROM items_master WHERE company = 'HP' AND item_name = 'EliteBook 840 G10' LIMIT 1),
     item5 AS (SELECT id FROM items_master WHERE company = 'HP' AND item_name = 'ProLiant DL380 Gen11' LIMIT 1)
INSERT INTO project_items (project_id, master_item_id, item_code, item_name, quantity, delivery_options, description, status, is_finalized, finalized_by, finalized_at, external_purchase)
SELECT proj1.id, item1.id, 'Dell-Latitude 5540 Laptop', 'Latitude 5540 Laptop', 25, '["2025-04-15"]'::jsonb, 'For development team', 'PENDING', true, pmo.id, NOW() - INTERVAL '5 days', false FROM proj1, item1, pmo
UNION ALL
SELECT proj1.id, item2.id, 'Dell-PowerEdge R750 Server', 'PowerEdge R750 Server', 3, '["2025-03-30"]'::jsonb, 'Application servers', 'PENDING', true, pmo.id, NOW() - INTERVAL '5 days', false FROM proj1, item2, pmo
UNION ALL
SELECT proj1.id, item3.id, 'Cisco-Catalyst 9300 Switch', 'Catalyst 9300 Switch', 5, '["2025-03-15"]'::jsonb, 'Core network switches', 'PENDING', true, pmo.id, NOW() - INTERVAL '5 days', false FROM proj1, item3, pmo
UNION ALL
SELECT proj2.id, item4.id, 'HP-EliteBook 840 G10', 'EliteBook 840 G10', 30, '["2025-04-01"]'::jsonb, 'For management team', 'PENDING', true, pmo.id, NOW() - INTERVAL '5 days', false FROM proj2, item4, pmo
UNION ALL
SELECT proj2.id, item5.id, 'HP-ProLiant DL380 Gen11', 'ProLiant DL380 Gen11', 8, '["2025-06-01"]'::jsonb, 'Database servers', 'PENDING', true, pmo.id, NOW() - INTERVAL '5 days', false FROM proj2, item5, pmo;

-- Step 8: Create procurement options with mixed USD/IRR pricing
WITH usd AS (SELECT id FROM currencies WHERE code = 'USD' LIMIT 1),
     irr AS (SELECT id FROM currencies WHERE code = 'IRR' LIMIT 1)
INSERT INTO procurement_options (project_item_id, item_code, supplier_name, base_cost, currency_id, shipping_cost, lomc_lead_time, payment_terms, is_finalized)
-- Dell Laptop options
SELECT pi.id, pi.item_code, 'Dell Direct USA', 1200.00, usd.id, 60.00, 15, '{"type": "cash", "discount_percent": 0.02}'::jsonb, false
FROM project_items pi, usd WHERE pi.item_code = 'Dell-Latitude 5540 Laptop'
UNION ALL
SELECT pi.id, pi.item_code, 'Local IT Distributor', 52000000.00, irr.id, 2600000.00, 20, '{"type": "cash", "discount_percent": 0}'::jsonb, false
FROM project_items pi, irr WHERE pi.item_code = 'Dell-Latitude 5540 Laptop'
UNION ALL
-- Dell Server options
SELECT pi.id, pi.item_code, 'Dell Enterprise', 8500.00, usd.id, 425.00, 30, '{"type": "cash", "discount_percent": 0.02}'::jsonb, false
FROM project_items pi, usd WHERE pi.item_code = 'Dell-PowerEdge R750 Server'
UNION ALL
SELECT pi.id, pi.item_code, 'Server Solutions Iran', 370000000.00, irr.id, 18500000.00, 45, '{"type": "cash", "discount_percent": 0}'::jsonb, false
FROM project_items pi, irr WHERE pi.item_code = 'Dell-PowerEdge R750 Server'
UNION ALL
-- Cisco Switch options
SELECT pi.id, pi.item_code, 'Cisco Authorized', 12000.00, usd.id, 600.00, 20, '{"type": "cash", "discount_percent": 0.02}'::jsonb, false
FROM project_items pi, usd WHERE pi.item_code = 'Cisco-Catalyst 9300 Switch'
UNION ALL
SELECT pi.id, pi.item_code, 'Network Equipment Co', 520000000.00, irr.id, 26000000.00, 30, '{"type": "cash", "discount_percent": 0}'::jsonb, false
FROM project_items pi, irr WHERE pi.item_code = 'Cisco-Catalyst 9300 Switch'
UNION ALL
-- HP Laptop options
SELECT pi.id, pi.item_code, 'HP Store', 1300.00, usd.id, 65.00, 15, '{"type": "cash", "discount_percent": 0.02}'::jsonb, false
FROM project_items pi, usd WHERE pi.item_code = 'HP-EliteBook 840 G10'
UNION ALL
SELECT pi.id, pi.item_code, 'Tehran Computer Market', 56000000.00, irr.id, 2800000.00, 10, '{"type": "cash", "discount_percent": 0}'::jsonb, false
FROM project_items pi, irr WHERE pi.item_code = 'HP-EliteBook 840 G10'
UNION ALL
-- HP Server options
SELECT pi.id, pi.item_code, 'HP Enterprise', 15000.00, usd.id, 750.00, 35, '{"type": "cash", "discount_percent": 0.02}'::jsonb, false
FROM project_items pi, usd WHERE pi.item_code = 'HP-ProLiant DL380 Gen11'
UNION ALL
SELECT pi.id, pi.item_code, 'Data Center Equipment', 650000000.00, irr.id, 32500000.00, 50, '{"type": "cash", "discount_percent": 0}'::jsonb, false
FROM project_items pi, irr WHERE pi.item_code = 'HP-ProLiant DL380 Gen11';

-- Step 9: Show summary
SELECT '✅ Data Reset Complete!' as status;
SELECT 'Currencies' as table_name, COUNT(*) as count FROM currencies
UNION ALL SELECT 'Users', COUNT(*) FROM users
UNION ALL SELECT 'Items Master', COUNT(*) FROM items_master
UNION ALL SELECT 'Projects', COUNT(*) FROM projects
UNION ALL SELECT 'Project Items', COUNT(*) FROM project_items
UNION ALL SELECT 'Finalized Items', COUNT(*) FROM project_items WHERE is_finalized = true
UNION ALL SELECT 'Procurement Options', COUNT(*) FROM procurement_options;

SELECT 'Options by Currency' as breakdown;
SELECT c.code as currency, COUNT(*) as options_count
FROM procurement_options po
JOIN currencies c ON c.id = po.currency_id
GROUP BY c.code;


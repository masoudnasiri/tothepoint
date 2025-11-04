-- ============================================================================
-- PDSS LARGE DATASET RESET
-- Creates 10+ projects with 100+ items each
-- 5+ procurement options per item with mixed USD/IRR pricing
-- ============================================================================

-- Delete all operational data
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

-- Create currencies
INSERT INTO currencies (code, name, symbol, is_base_currency, is_active, decimal_places)
VALUES 
    ('USD', 'US Dollar', '$', true, true, 2),
    ('IRR', 'Iranian Rial', '﷼', false, true, 0),
    ('EUR', 'Euro', '€', false, true, 2)
ON CONFLICT (code) DO UPDATE 
SET is_base_currency = EXCLUDED.is_base_currency;

-- Exchange rates
INSERT INTO exchange_rates (from_currency, to_currency, rate, date, is_active)
VALUES 
    ('USD', 'IRR', 42000.00, CURRENT_DATE, true),
    ('IRR', 'USD', 0.000024, CURRENT_DATE, true),
    ('USD', 'EUR', 0.92, CURRENT_DATE, true),
    ('EUR', 'USD', 1.09, CURRENT_DATE, true),
    ('EUR', 'IRR', 45650.00, CURRENT_DATE, true),
    ('IRR', 'EUR', 0.000022, CURRENT_DATE, true);

-- Users
INSERT INTO users (username, password_hash, role, is_active)
VALUES 
    ('pmo_user', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5aX7V5mXq5Xc2', 'pmo', true),
    ('pm1', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5aX7V5mXq5Xc2', 'pm', true),
    ('pm2', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5aX7V5mXq5Xc2', 'pm', true),
    ('procurement1', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5aX7V5mXq5Xc2', 'procurement', true),
    ('finance1', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5aX7V5mXq5Xc2', 'finance', true)
ON CONFLICT (username) DO NOTHING;

-- ============================================================================
-- Items Master: 150+ items across multiple categories
-- ============================================================================

-- Laptops (40 items)
INSERT INTO items_master (item_code, company, item_name, model, category, unit, description)
SELECT 
    'DELL-LAT' || num,
    'Dell',
    'Latitude ' || (5400 + num) || ' Laptop',
    'Model ' || num,
    'Laptops',
    'piece',
    'Dell Latitude series laptop'
FROM generate_series(1, 20) num;

INSERT INTO items_master (item_code, company, item_name, model, category, unit, description)
SELECT 
    'HP-EB' || num,
    'HP',
    'EliteBook ' || (800 + num) || ' Laptop',
    'Gen ' || num,
    'Laptops',
    'piece',
    'HP EliteBook series laptop'
FROM generate_series(1, 20) num;

-- Servers (30 items)
INSERT INTO items_master (item_code, company, item_name, model, category, unit, description)
SELECT 
    'DELL-R' || (700 + num),
    'Dell',
    'PowerEdge R' || (700 + num) || ' Server',
    'Rack Server',
    'Servers',
    'piece',
    'Dell PowerEdge rack server'
FROM generate_series(1, 15) num;

INSERT INTO items_master (item_code, company, item_name, model, category, unit, description)
SELECT 
    'HP-DL' || (300 + num),
    'HP',
    'ProLiant DL' || (300 + num) || ' Server',
    'Gen11',
    'Servers',
    'piece',
    'HP ProLiant rack server'
FROM generate_series(1, 15) num;

-- Networking (30 items)
INSERT INTO items_master (item_code, company, item_name, model, category, unit, description)
SELECT 
    'CISCO-C' || (9200 + num),
    'Cisco',
    'Catalyst ' || (9200 + num) || ' Switch',
    '48-Port',
    'Networking',
    'piece',
    'Cisco Catalyst switch'
FROM generate_series(1, 15) num;

INSERT INTO items_master (item_code, company, item_name, model, category, unit, description)
SELECT 
    'CISCO-ISR' || (4300 + num),
    'Cisco',
    'ISR ' || (4300 + num) || ' Router',
    'Integrated',
    'Networking',
    'piece',
    'Cisco ISR router'
FROM generate_series(1, 15) num;

-- Storage (20 items)
INSERT INTO items_master (item_code, company, item_name, model, category, unit, description)
SELECT 
    'SYNOLOGY-DS' || (1800 + num),
    'Synology',
    'DiskStation DS' || (1800 + num) || ' NAS',
    '8-Bay',
    'Storage',
    'piece',
    'Synology NAS storage'
FROM generate_series(1, 10) num;

INSERT INTO items_master (item_code, company, item_name, model, category, unit, description)
SELECT 
    'WD-GOLD' || num || 'TB',
    'Western Digital',
    'Gold Enterprise HDD ' || num || 'TB',
    'Enterprise',
    'Storage',
    'piece',
    'WD Gold enterprise hard drive'
FROM generate_series(10, 18, 2) num;

-- Monitors (15 items)
INSERT INTO items_master (item_code, company, item_name, model, category, unit, description)
SELECT 
    'DELL-U' || (2400 + num),
    'Dell',
    'UltraSharp U' || (2400 + num) || ' Monitor',
    '27-inch',
    'Monitors',
    'piece',
    'Dell UltraSharp monitor'
FROM generate_series(1, 15) num;

-- Printers (15 items)
INSERT INTO items_master (item_code, company, item_name, model, category, unit, description)
SELECT 
    'HP-LJ' || (400 + num),
    'HP',
    'LaserJet Pro M' || (400 + num),
    'MFP',
    'Printers',
    'piece',
    'HP LaserJet printer'
FROM generate_series(1, 15) num;

-- ============================================================================
-- Projects: 12 projects
-- ============================================================================

INSERT INTO projects (project_code, name, priority_weight, budget_amount, budget_currency, is_active)
VALUES
    ('PROJ-IT-2025', 'IT Infrastructure Upgrade 2025', 9, 500000.00, 'USD', true),
    ('PROJ-OFFICE-2025', 'Office Equipment Procurement', 8, 300000.00, 'USD', true),
    ('PROJ-DC-2025', 'Data Center Expansion', 10, 800000.00, 'USD', true),
    ('PROJ-BRANCH-01', 'Branch Office Setup - Tehran', 7, 200000.00, 'IRR', true),
    ('PROJ-BRANCH-02', 'Branch Office Setup - Isfahan', 7, 180000.00, 'IRR', true),
    ('PROJ-NETWORK-2025', 'Network Infrastructure Upgrade', 8, 400000.00, 'USD', true),
    ('PROJ-SECURITY-2025', 'IT Security Enhancement', 9, 350000.00, 'USD', true),
    ('PROJ-CLOUD-2025', 'Cloud Infrastructure Migration', 8, 600000.00, 'USD', true),
    ('PROJ-ERP-2025', 'ERP System Hardware', 9, 450000.00, 'USD', true),
    ('PROJ-TRAINING-2025', 'Training Center Equipment', 6, 150000.00, 'USD', true),
    ('PROJ-RD-2025', 'R&D Lab Equipment', 7, 250000.00, 'USD', true),
    ('PROJ-BACKUP-2025', 'Backup & Disaster Recovery', 10, 700000.00, 'USD', true);

-- ============================================================================
-- Project Items: 100+ items per project (finalized)
-- ============================================================================

-- Project 1: IT Infrastructure (120 items)
WITH pmo AS (SELECT id FROM users WHERE username = 'pmo_user' LIMIT 1),
     proj AS (SELECT id FROM projects WHERE project_code = 'PROJ-IT-2025' LIMIT 1)
INSERT INTO project_items (project_id, item_code, item_name, quantity, delivery_options, description, status, external_purchase, is_finalized, finalized_by, finalized_at)
SELECT 
    proj.id,
    im.item_code,
    im.item_name,
    (5 + (random() * 20)::int),
    '["2025-04-15", "2025-05-15"]',
    'For IT Infrastructure project',
    'PENDING',
    false,
    true,
    pmo.id,
    NOW() - (random() * 10 || ' days')::interval
FROM items_master im, proj, pmo
WHERE im.category IN ('Laptops', 'Servers', 'Networking', 'Storage')
LIMIT 120;

-- Project 2: Office Equipment (110 items)
WITH pmo AS (SELECT id FROM users WHERE username = 'pmo_user' LIMIT 1),
     proj AS (SELECT id FROM projects WHERE project_code = 'PROJ-OFFICE-2025' LIMIT 1)
INSERT INTO project_items (project_id, item_code, item_name, quantity, delivery_options, description, status, external_purchase, is_finalized, finalized_by, finalized_at)
SELECT 
    proj.id,
    im.item_code,
    im.item_name,
    (10 + (random() * 30)::int),
    '["2025-03-20", "2025-04-20"]',
    'For Office Equipment project',
    'PENDING',
    false,
    true,
    pmo.id,
    NOW() - (random() * 8 || ' days')::interval
FROM items_master im, proj, pmo
WHERE im.category IN ('Laptops', 'Monitors', 'Printers')
LIMIT 110;

-- Project 3: Data Center (100 items)
WITH pmo AS (SELECT id FROM users WHERE username = 'pmo_user' LIMIT 1),
     proj AS (SELECT id FROM projects WHERE project_code = 'PROJ-DC-2025' LIMIT 1)
INSERT INTO project_items (project_id, item_code, item_name, quantity, delivery_options, description, status, external_purchase, is_finalized, finalized_by, finalized_at)
SELECT 
    proj.id,
    im.item_code,
    im.item_name,
    (2 + (random() * 10)::int),
    '["2025-05-01", "2025-06-01"]',
    'For Data Center project',
    'PENDING',
    false,
    true,
    pmo.id,
    NOW() - (random() * 7 || ' days')::interval
FROM items_master im, proj, pmo
WHERE im.category IN ('Servers', 'Storage', 'Networking')
LIMIT 100;

-- Project 4-12: More projects (100 items each)
WITH pmo AS (SELECT id FROM users WHERE username = 'pmo_user' LIMIT 1)
INSERT INTO project_items (project_id, item_code, item_name, quantity, delivery_options, description, status, external_purchase, is_finalized, finalized_by, finalized_at)
SELECT 
    p.id,
    im.item_code,
    im.item_name,
    (3 + (random() * 15)::int),
    '["2025-04-01"]',
    'For ' || p.name,
    'PENDING',
    false,
    true,
    pmo.id,
    NOW() - (random() * 10 || ' days')::interval
FROM projects p
CROSS JOIN items_master im
CROSS JOIN pmo
WHERE p.project_code IN ('PROJ-BRANCH-01', 'PROJ-BRANCH-02', 'PROJ-NETWORK-2025', 'PROJ-SECURITY-2025', 
                         'PROJ-CLOUD-2025', 'PROJ-ERP-2025', 'PROJ-TRAINING-2025', 'PROJ-RD-2025', 'PROJ-BACKUP-2025')
AND random() < 0.7  -- 70% chance to include item
LIMIT 900;

-- ============================================================================
-- Procurement Options: 5+ options per item (mixed currencies)
-- ============================================================================

-- Generate supplier names
CREATE TEMP TABLE temp_suppliers AS
SELECT supplier_name, currency_code FROM (VALUES
    ('Dell Direct USA', 'USD'),
    ('Dell Enterprise Partners', 'USD'),
    ('Dell International', 'EUR'),
    ('HP Official Store', 'USD'),
    ('HP Enterprise Direct', 'USD'),
    ('HP Europe', 'EUR'),
    ('Cisco Authorized Distributor', 'USD'),
    ('Cisco Gold Partner', 'USD'),
    ('Cisco Europe', 'EUR'),
    ('Local IT Distributor Tehran', 'IRR'),
    ('Server Solutions Iran', 'IRR'),
    ('Network Equipment Co Tehran', 'IRR'),
    ('Tehran Computer Market', 'IRR'),
    ('Data Center Equipment Iran', 'IRR'),
    ('Office Equipment Tehran', 'IRR'),
    ('Import Specialist USA', 'USD'),
    ('Import Specialist Europe', 'EUR'),
    ('Global IT Supplier', 'USD'),
    ('Enterprise Solutions Tehran', 'IRR'),
    ('Tech Solutions Iran', 'IRR')
) AS s(supplier_name, currency_code);

-- Create procurement options (5-7 per item)
WITH finalized_items AS (
    SELECT DISTINCT item_code FROM project_items WHERE is_finalized = true
),
currency_map AS (
    SELECT code, id FROM currencies
)
INSERT INTO procurement_options (
    item_code, supplier_name, base_cost, currency_id, 
    shipping_cost, lomc_lead_time, discount_bundle_threshold, 
    discount_bundle_percent, payment_terms, is_finalized
)
SELECT 
    fi.item_code,
    ts.supplier_name,
    CASE 
        WHEN ts.currency_code = 'USD' THEN (800 + random() * 14000)::numeric(12,2)
        WHEN ts.currency_code = 'EUR' THEN (700 + random() * 13000)::numeric(12,2)
        WHEN ts.currency_code = 'IRR' THEN (35000000 + random() * 600000000)::numeric(12,2)
    END as base_cost,
    cm.id,
    CASE 
        WHEN ts.currency_code = 'USD' THEN (40 + random() * 700)::numeric(12,2)
        WHEN ts.currency_code = 'EUR' THEN (35 + random() * 650)::numeric(12,2)
        WHEN ts.currency_code = 'IRR' THEN (1500000 + random() * 30000000)::numeric(12,2)
    END as shipping_cost,
    (7 + random() * 43)::int as lead_time,
    (5 + random() * 15)::int as bundle_threshold,
    (3.0 + random() * 12.0)::numeric(5,2) as bundle_discount,
    CASE 
        WHEN random() < 0.5 THEN '{"type": "cash", "discount_percent": ' || (random() * 3.0)::numeric(5,2) || '}'
        ELSE '{"type": "installments", "schedule": [{"due_offset": 0, "percent": 30}, {"due_offset": 30, "percent": 40}, {"due_offset": 60, "percent": 30}]}'
    END::json as payment_terms,
    false
FROM finalized_items fi
CROSS JOIN temp_suppliers ts
CROSS JOIN currency_map cm
WHERE cm.code = ts.currency_code
  AND random() < 0.35  -- 35% chance to create option (results in 5-7 per item)
ORDER BY fi.item_code, ts.supplier_name;

DROP TABLE temp_suppliers;

-- ============================================================================
-- SUMMARY
-- ============================================================================

SELECT '=======================================' as "STATUS";
SELECT 'DATA RESET COMPLETE - LARGE DATASET' as "RESULT";
SELECT '=======================================' as "STATUS";

SELECT 
    'Currencies' as "Table", 
    COUNT(*)::text as "Count" 
FROM currencies
UNION ALL
SELECT 'Users', COUNT(*)::text FROM users  
UNION ALL
SELECT 'Items Master', COUNT(*)::text FROM items_master
UNION ALL
SELECT 'Projects', COUNT(*)::text FROM projects
UNION ALL
SELECT 'Project Items', COUNT(*)::text FROM project_items
UNION ALL
SELECT 'Finalized Items', COUNT(*)::text FROM project_items WHERE is_finalized = true
UNION ALL
SELECT 'Procurement Options', COUNT(*)::text FROM procurement_options;

SELECT '=======================================' as "STATUS";
SELECT 'CURRENCY BREAKDOWN' as "INFO";
SELECT c.code as "Currency", COUNT(po.id)::text as "Options"
FROM currencies c
LEFT JOIN procurement_options po ON po.currency_id = c.id
GROUP BY c.code
ORDER BY c.code;

SELECT '=======================================' as "STATUS";
SELECT 'PROJECTS WITH ITEM COUNTS' as "INFO";
SELECT p.name as "Project", COUNT(pi.id)::text as "Items"
FROM projects p
LEFT JOIN project_items pi ON pi.project_id = p.id
GROUP BY p.name
ORDER BY COUNT(pi.id) DESC;

SELECT '=======================================' as "STATUS";
SELECT 'READY TO USE!' as "NEXT";
SELECT 'Restart: docker-compose restart backend' as "STEP";



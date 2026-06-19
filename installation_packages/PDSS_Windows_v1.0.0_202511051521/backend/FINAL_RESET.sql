-- ============================================================================
-- PDSS FINAL DATA RESET AND RESEED
-- Based on complete schema review and all implemented changes
-- Includes: Item Finalization Workflow + USD/IRR Currency Support
-- ============================================================================

-- Start transaction
BEGIN;

RAISE NOTICE '============================================================================';
RAISE NOTICE 'PDSS DATA RESET - Wiping operational data...';
RAISE NOTICE '============================================================================';

-- Step 1: Delete all operational data in correct dependency order
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

RAISE NOTICE '✅ Step 1 Complete: All operational data deleted';

-- ============================================================================
-- Step 2: Create Currencies (USD as base, IRR as secondary)
-- ============================================================================
RAISE NOTICE '💰 Step 2: Creating currencies...';

INSERT INTO currencies (code, name, symbol, is_base_currency, is_active, decimal_places)
VALUES 
    ('USD', 'US Dollar', '$', true, true, 2),
    ('IRR', 'Iranian Rial', '﷼', false, true, 0)
ON CONFLICT (code) DO UPDATE 
SET is_base_currency = EXCLUDED.is_base_currency,
    is_active = EXCLUDED.is_active,
    decimal_places = EXCLUDED.decimal_places;

RAISE NOTICE '✅ Currencies created: USD (base) and IRR';

-- ============================================================================
-- Step 3: Create Exchange Rates (1 USD = 42,000 IRR)
-- ============================================================================
RAISE NOTICE '💱 Step 3: Setting exchange rates...';

INSERT INTO exchange_rates (from_currency, to_currency, rate, date, is_active)
VALUES 
    ('USD', 'IRR', 42000.00, CURRENT_DATE, true),
    ('IRR', 'USD', 0.000024, CURRENT_DATE, true)
ON CONFLICT DO NOTHING;

RAISE NOTICE '✅ Exchange rates set: 1 USD = 42,000 IRR';

-- ============================================================================
-- Step 4: Create Users (preserving admin, creating test users)
-- ============================================================================
RAISE NOTICE '👥 Step 4: Creating users...';

-- Password hash for 'password123' (bcrypt)
INSERT INTO users (username, password_hash, role, is_active)
VALUES 
    ('pmo_user', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5aX7V5mXq5Xc2', 'pmo', true),
    ('pm1', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5aX7V5mXq5Xc2', 'pm', true),
    ('pm2', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5aX7V5mXq5Xc2', 'pm', true),
    ('procurement1', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5aX7V5mXq5Xc2', 'procurement', true),
    ('finance1', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5aX7V5mXq5Xc2', 'finance', true)
ON CONFLICT (username) DO NOTHING;

RAISE NOTICE '✅ Users created: admin, pmo_user, pm1, pm2, procurement1, finance1';

-- ============================================================================
-- Step 5: Create Items Master Catalog (IT Equipment)
-- ============================================================================
RAISE NOTICE '📦 Step 5: Creating items master catalog...';

INSERT INTO items_master (item_code, company, item_name, model, category, unit, description)
VALUES
    -- Dell Items
    ('DELL-LAT5540', 'Dell', 'Latitude 5540 Laptop', '2024 Model', 'Laptops', 'piece', 'Dell Latitude 5540 Business Laptop - Intel Core i7, 16GB RAM, 512GB SSD'),
    ('DELL-R750', 'Dell', 'PowerEdge R750 Server', 'Rack Mount', 'Servers', 'piece', 'Dell PowerEdge R750 Rack Server - Dual Xeon, 128GB RAM, 8TB Storage'),
    ('DELL-U2723DE', 'Dell', 'UltraSharp U2723DE Monitor', '27 inch', 'Monitors', 'piece', 'Dell UltraSharp 27" QHD Monitor with USB-C Hub'),
    
    -- HP Items
    ('HP-EB840', 'HP', 'EliteBook 840 G10', 'Business Series', 'Laptops', 'piece', 'HP EliteBook 840 G10 - Intel Core i7, 16GB RAM, 512GB SSD'),
    ('HP-DL380', 'HP', 'ProLiant DL380 Gen11', 'Rack Server', 'Servers', 'piece', 'HP ProLiant DL380 Gen11 - Dual AMD EPYC, 256GB RAM'),
    ('HP-M479FDW', 'HP', 'LaserJet Pro M479fdw', 'Color MFP', 'Printers', 'piece', 'HP LaserJet Pro Color MFP - Print/Scan/Copy/Fax'),
    
    -- Cisco Networking
    ('CISCO-C9300', 'Cisco', 'Catalyst 9300 Switch', '48-Port', 'Networking', 'piece', 'Cisco Catalyst 9300 48-Port Gigabit Switch with PoE+'),
    ('CISCO-ISR4331', 'Cisco', 'ISR 4331 Router', 'Integrated Services', 'Networking', 'piece', 'Cisco ISR 4331 Integrated Services Router'),
    
    -- Storage & Accessories
    ('SYNOLOGY-DS1823', 'Synology', 'DS1823xs+ NAS', '8-Bay', 'Storage', 'piece', 'Synology DiskStation DS1823xs+ 8-Bay NAS - AMD Ryzen'),
    ('WD-GOLD18TB', 'Western Digital', 'Gold Enterprise HDD', '18TB', 'Storage', 'piece', 'WD Gold 18TB Enterprise Hard Drive - 7200 RPM'),
    ('APC-UPS1500', 'APC', 'Smart-UPS 1500VA', 'LCD 120V', 'Power', 'piece', 'APC Smart-UPS 1500VA Battery Backup')
ON CONFLICT (item_code) DO NOTHING;

RAISE NOTICE '✅ Items master created: 11 IT equipment items';

-- ============================================================================
-- Step 6: Create Projects
-- ============================================================================
RAISE NOTICE '🏢 Step 6: Creating projects...';

INSERT INTO projects (name, description, start_date, end_date)
VALUES
    ('IT Infrastructure Upgrade 2025', 'Complete IT infrastructure upgrade including servers, networking equipment, and end-user devices', '2025-01-01', '2025-12-31'),
    ('Office Equipment Procurement', 'New office equipment for headquarters expansion and remote offices', '2025-02-01', '2025-08-31'),
    ('Data Center Expansion', 'Data center expansion with enterprise-grade servers and storage systems', '2025-03-01', '2025-11-30')
RETURNING id, name;

RAISE NOTICE '✅ Projects created: 3 projects';

-- ============================================================================
-- Step 7: Create Project Items (ALL FINALIZED for immediate procurement)
-- ============================================================================
RAISE NOTICE '📋 Step 7: Creating finalized project items...';

WITH pmo_user AS (
    SELECT id FROM users WHERE username = 'pmo_user' LIMIT 1
)
INSERT INTO project_items (
    project_id, item_code, item_name, quantity, delivery_options, 
    description, status, external_purchase,
    is_finalized, finalized_by, finalized_at
)
SELECT 
    p.id,
    items.item_code,
    items.item_name,
    items.quantity,
    items.delivery_options::jsonb,
    items.description,
    'PENDING'::projectitemstatus,
    false,
    true,
    pmo_user.id,
    NOW() - (items.days_ago || ' days')::interval
FROM pmo_user,
(VALUES
    -- Project 1: IT Infrastructure Upgrade
    ((SELECT id FROM projects WHERE name LIKE 'IT Infrastructure%' LIMIT 1), 'DELL-LAT5540', 'Latitude 5540 Laptop', 25, '["2025-04-15", "2025-05-15"]', 'For software development team', 5),
    ((SELECT id FROM projects WHERE name LIKE 'IT Infrastructure%' LIMIT 1), 'DELL-R750', 'PowerEdge R750 Server', 3, '["2025-03-30"]', 'Primary application servers', 7),
    ((SELECT id FROM projects WHERE name LIKE 'IT Infrastructure%' LIMIT 1), 'CISCO-C9300', 'Catalyst 9300 Switch', 5, '["2025-03-15", "2025-04-15"]', 'Core network switches', 8),
    ((SELECT id FROM projects WHERE name LIKE 'IT Infrastructure%' LIMIT 1), 'APC-UPS1500', 'Smart-UPS 1500VA', 10, '["2025-03-20"]', 'UPS for critical equipment', 6),
    
    -- Project 2: Office Equipment
    ((SELECT id FROM projects WHERE name LIKE 'Office Equipment%' LIMIT 1), 'HP-EB840', 'EliteBook 840 G10', 30, '["2025-04-01", "2025-05-01"]', 'For management and sales team', 4),
    ((SELECT id FROM projects WHERE name LIKE 'Office Equipment%' LIMIT 1), 'DELL-U2723DE', 'UltraSharp U2723DE Monitor', 50, '["2025-04-15"]', 'Dual monitor setup for employees', 5),
    ((SELECT id FROM projects WHERE name LIKE 'Office Equipment%' LIMIT 1), 'HP-M479FDW', 'LaserJet Pro M479fdw', 8, '["2025-03-25"]', 'Department printers', 6),
    
    -- Project 3: Data Center Expansion
    ((SELECT id FROM projects WHERE name LIKE 'Data Center%' LIMIT 1), 'HP-DL380', 'ProLiant DL380 Gen11', 8, '["2025-06-01", "2025-07-01"]', 'Enterprise database servers', 3),
    ((SELECT id FROM projects WHERE name LIKE 'Data Center%' LIMIT 1), 'SYNOLOGY-DS1823', 'DS1823xs+ NAS', 2, '["2025-05-15"]', 'Backup and file storage', 4),
    ((SELECT id FROM projects WHERE name LIKE 'Data Center%' LIMIT 1), 'WD-GOLD18TB', 'Gold Enterprise HDD', 40, '["2025-05-20"]', 'Storage expansion drives', 5),
    ((SELECT id FROM projects WHERE name LIKE 'Data Center%' LIMIT 1), 'CISCO-ISR4331', 'ISR 4331 Router', 4, '["2025-05-15"]', 'Data center routers', 4)
) AS items(project_id, item_code, item_name, quantity, delivery_options, description, days_ago)
JOIN projects p ON p.id = items.project_id;

RAISE NOTICE '✅ Project items created: 11 items, all finalized and ready for procurement';

-- ============================================================================
-- Step 8: Create Procurement Options with Mixed USD/IRR Pricing
-- ============================================================================
RAISE NOTICE '💰 Step 8: Creating procurement options with USD/IRR pricing...';

WITH currency_ids AS (
    SELECT 
        MAX(CASE WHEN code = 'USD' THEN id END) as usd_id,
        MAX(CASE WHEN code = 'IRR' THEN id END) as irr_id
    FROM currencies
)
INSERT INTO procurement_options (
    item_code, supplier_name, base_cost, currency_id, 
    shipping_cost, lomc_lead_time, discount_bundle_threshold, 
    discount_bundle_percent, payment_terms, is_finalized
)
SELECT 
    pi.item_code,
    options.supplier_name,
    options.base_cost,
    CASE 
        WHEN options.currency = 'USD' THEN currency_ids.usd_id
        WHEN options.currency = 'IRR' THEN currency_ids.irr_id
    END,
    options.shipping_cost,
    options.lead_time,
    options.bundle_threshold,
    options.bundle_discount,
    options.payment_terms::json,
    false
FROM project_items pi
CROSS JOIN currency_ids
CROSS JOIN LATERAL (
    VALUES
        -- Dell Laptop (2 options: USD and IRR)
        ('Dell Direct USA', 1200.00, 'USD', 60.00, 15, 10, 5.0, '{"type": "cash", "discount_percent": 2.0}'),
        ('Local IT Distributor Tehran', 52000000.00, 'IRR', 2600000.00, 20, 10, 5.0, '{"type": "cash", "discount_percent": 0}'),
        
        -- Dell Server (2 options)
        ('Dell Enterprise Partners', 8500.00, 'USD', 425.00, 30, 2, 10.0, '{"type": "installments", "schedule": [{"due_offset": 0, "percent": 30}, {"due_offset": 30, "percent": 40}, {"due_offset": 60, "percent": 30}]}'),
        ('Server Solutions Iran', 370000000.00, 'IRR', 18500000.00, 45, 2, 10.0, '{"type": "cash", "discount_percent": 0}'),
        
        -- Cisco Switch (2 options)
        ('Cisco Authorized Distributor', 12000.00, 'USD', 600.00, 20, 3, 7.5, '{"type": "cash", "discount_percent": 2.0}'),
        ('Network Equipment Co', 520000000.00, 'IRR', 26000000.00, 30, 3, 7.5, '{"type": "cash", "discount_percent": 0}'),
        
        -- HP Laptop (2 options)
        ('HP Official Store', 1300.00, 'USD', 65.00, 15, 10, 5.0, '{"type": "cash", "discount_percent": 2.0}'),
        ('Tehran Computer Market', 56000000.00, 'IRR', 2800000.00, 10, 10, 5.0, '{"type": "cash", "discount_percent": 0}'),
        
        -- HP Server (2 options)
        ('HP Enterprise Direct', 15000.00, 'USD', 750.00, 35, 3, 10.0, '{"type": "cash", "discount_percent": 2.0}'),
        ('Data Center Equipment Iran', 650000000.00, 'IRR', 32500000.00, 50, 3, 10.0, '{"type": "cash", "discount_percent": 0}'),
        
        -- Dell Monitor (2 options)
        ('Dell Display Solutions', 450.00, 'USD', 22.50, 10, 20, 5.0, '{"type": "cash", "discount_percent": 2.0}'),
        ('Monitor Supplier Iran', 19500000.00, 'IRR', 975000.00, 15, 20, 5.0, '{"type": "cash", "discount_percent": 0}'),
        
        -- HP Printer (2 options)
        ('HP Printer Division', 650.00, 'USD', 32.50, 10, 5, 5.0, '{"type": "cash", "discount_percent": 2.0}'),
        ('Office Equipment Tehran', 28000000.00, 'IRR', 1400000.00, 12, 5, 5.0, '{"type": "cash", "discount_percent": 0}'),
        
        -- Synology NAS (2 options)
        ('Synology Direct', 3500.00, 'USD', 175.00, 20, 1, 10.0, '{"type": "cash", "discount_percent": 2.0}'),
        ('Storage Solutions Iran', 152000000.00, 'IRR', 7600000.00, 25, 1, 10.0, '{"type": "cash", "discount_percent": 0}'),
        
        -- WD HDD (2 options)
        ('Western Digital Authorized', 420.00, 'USD', 21.00, 10, 20, 5.0, '{"type": "cash", "discount_percent": 2.0}'),
        ('Storage Depot Tehran', 18200000.00, 'IRR', 910000.00, 15, 20, 5.0, '{"type": "cash", "discount_percent": 0}'),
        
        -- Cisco Router (2 options)
        ('Cisco Network Partners', 4500.00, 'USD', 225.00, 25, 2, 10.0, '{"type": "cash", "discount_percent": 2.0}'),
        ('Network Pro Iran', 195000000.00, 'IRR', 9750000.00, 30, 2, 10.0, '{"type": "cash", "discount_percent": 0}'),
        
        -- APC UPS (2 options)
        ('APC by Schneider Electric', 850.00, 'USD', 42.50, 15, 5, 5.0, '{"type": "cash", "discount_percent": 2.0}'),
        ('Power Solutions Iran', 37000000.00, 'IRR', 1850000.00, 20, 5, 5.0, '{"type": "cash", "discount_percent": 0}')
) AS options(supplier_name, base_cost, currency, shipping_cost, lead_time, bundle_threshold, bundle_discount, payment_terms)
WHERE 
    (pi.item_code = 'DELL-LAT5540' AND options.supplier_name IN ('Dell Direct USA', 'Local IT Distributor Tehran'))
    OR (pi.item_code = 'DELL-R750' AND options.supplier_name IN ('Dell Enterprise Partners', 'Server Solutions Iran'))
    OR (pi.item_code = 'CISCO-C9300' AND options.supplier_name IN ('Cisco Authorized Distributor', 'Network Equipment Co'))
    OR (pi.item_code = 'HP-EB840' AND options.supplier_name IN ('HP Official Store', 'Tehran Computer Market'))
    OR (pi.item_code = 'HP-DL380' AND options.supplier_name IN ('HP Enterprise Direct', 'Data Center Equipment Iran'))
    OR (pi.item_code = 'DELL-U2723DE' AND options.supplier_name IN ('Dell Display Solutions', 'Monitor Supplier Iran'))
    OR (pi.item_code = 'HP-M479FDW' AND options.supplier_name IN ('HP Printer Division', 'Office Equipment Tehran'))
    OR (pi.item_code = 'SYNOLOGY-DS1823' AND options.supplier_name IN ('Synology Direct', 'Storage Solutions Iran'))
    OR (pi.item_code = 'WD-GOLD18TB' AND options.supplier_name IN ('Western Digital Authorized', 'Storage Depot Tehran'))
    OR (pi.item_code = 'CISCO-ISR4331' AND options.supplier_name IN ('Cisco Network Partners', 'Network Pro Iran'))
    OR (pi.item_code = 'APC-UPS1500' AND options.supplier_name IN ('APC by Schneider Electric', 'Power Solutions Iran'));

RAISE NOTICE '✅ Procurement options created: ~22 options with mixed USD/IRR pricing';

-- Commit all changes
COMMIT;

-- ============================================================================
-- SUMMARY
-- ============================================================================
RAISE NOTICE '============================================================================';
RAISE NOTICE 'DATA RESET COMPLETE!';
RAISE NOTICE '============================================================================';

-- Show table counts
SELECT 'TABLE COUNTS' as "═══════════════════════════";
SELECT 'Currencies' as "Table", COUNT(*)::text as "Count" FROM currencies
UNION ALL SELECT 'Exchange Rates', COUNT(*)::text FROM exchange_rates
UNION ALL SELECT 'Users', COUNT(*)::text FROM users
UNION ALL SELECT 'Items Master', COUNT(*)::text FROM items_master
UNION ALL SELECT 'Projects', COUNT(*)::text FROM projects
UNION ALL SELECT 'Project Items', COUNT(*)::text FROM project_items
UNION ALL SELECT 'Finalized Items', COUNT(*)::text FROM project_items WHERE is_finalized = true
UNION ALL SELECT 'Procurement Options', COUNT(*)::text FROM procurement_options
ORDER BY "Table";

-- Show currency breakdown
SELECT 'CURRENCY BREAKDOWN' as "═══════════════════════════";
SELECT c.code as "Currency", c.name as "Name", COUNT(po.id)::text as "Options"
FROM currencies c
LEFT JOIN procurement_options po ON po.currency_id = c.id
GROUP BY c.code, c.name
ORDER BY c.code;

-- Show login credentials
SELECT 'LOGIN CREDENTIALS' as "═══════════════════════════";
SELECT 
    CASE 
        WHEN username = 'admin' THEN '👑 Admin'
        WHEN username = 'pmo_user' THEN '🎯 PMO'
        WHEN username = 'pm1' THEN '📋 PM1'
        WHEN username = 'pm2' THEN '📋 PM2'
        WHEN username = 'procurement1' THEN '🛒 Procurement'
        WHEN username = 'finance1' THEN '💰 Finance'
    END as "Role",
    username || ' / ' || 
    CASE 
        WHEN username = 'admin' THEN 'admin123'
        WHEN username = 'pmo_user' THEN 'pmo123'
        ELSE 'password123'
    END as "Credentials"
FROM users
ORDER BY role;

-- Final message
SELECT '✅ READY TO USE!' as "═══════════════════════════";
SELECT 'Restart backend: docker-compose restart backend' as "Next Step";
SELECT 'Refresh browser to see new data' as "Action Required";


-- ================================================================
-- WIPE ALL OPERATIONAL DATA AND CREATE 3 PROJECTS WITH 3 ITEMS EACH
-- Preserves: users, currencies, exchange_rates, items_master
-- ================================================================

BEGIN;

-- ================================================================
-- STEP 1: DELETE ALL OPERATIONAL DATA (in correct order)
-- ================================================================

-- Delete cash flow events first
DELETE FROM cashflow_events;

-- Delete finalized decisions
DELETE FROM finalized_decisions;

-- Delete optimization results
DELETE FROM optimization_results;

-- Delete optimization runs
DELETE FROM optimization_runs;

-- Delete procurement options (must come before delivery_options due to FK)
DELETE FROM procurement_options;

-- Delete delivery options
DELETE FROM delivery_options;

-- Delete project items
DELETE FROM project_items;

-- Delete budget data
DELETE FROM budget_data;

-- Delete project phases
DELETE FROM project_phases;

-- Delete project assignments
DELETE FROM project_assignments;

-- Delete projects
DELETE FROM projects;

-- ================================================================
-- STEP 2: CREATE 3 PROJECTS
-- ================================================================

INSERT INTO projects (project_code, name, priority_weight, budget_amount, budget_currency, is_active)
VALUES
    ('PROJ-2025-001', 'Data Center Infrastructure Upgrade', 8, 500000, 'IRR', true),
    ('PROJ-2025-002', 'Network Security Enhancement', 7, 300000, 'USD', true),
    ('PROJ-2025-003', 'Enterprise Software Deployment', 6, 200000, 'EUR', true);

-- ================================================================
-- STEP 3: ASSIGN PM1 TO ALL 3 PROJECTS
-- ================================================================

INSERT INTO project_assignments (user_id, project_id)
SELECT 
    u.id,
    p.id
FROM users u
CROSS JOIN projects p
WHERE u.username = 'pm1';

-- ================================================================
-- STEP 4: CREATE 3 PROJECT ITEMS FOR EACH PROJECT (9 items total)
-- ================================================================

-- Project 1 Items (Data Center Infrastructure)
INSERT INTO project_items (
    project_id, master_item_id, item_code, item_name, quantity,
    delivery_options, status, external_purchase, is_finalized
)
SELECT 
    p.id,
    im.id,
    im.item_code,
    im.item_name,
    CASE 
        WHEN im.item_code = 'DELL-SRV-001' THEN 5
        WHEN im.item_code = 'DELL-STR-001' THEN 2
        WHEN im.item_code = 'CISCO-SW-001' THEN 10
    END as quantity,
    '[]'::json,
    'PENDING',
    false,
    false
FROM projects p
CROSS JOIN items_master im
WHERE p.project_code = 'PROJ-2025-001'
  AND im.item_code IN ('DELL-SRV-001', 'DELL-STR-001', 'CISCO-SW-001')
LIMIT 3;

-- Project 2 Items (Network Security)
INSERT INTO project_items (
    project_id, master_item_id, item_code, item_name, quantity,
    delivery_options, status, external_purchase, is_finalized
)
SELECT 
    p.id,
    im.id,
    im.item_code,
    im.item_name,
    CASE 
        WHEN im.item_code = 'CISCO-FW-001' THEN 3
        WHEN im.item_code = 'CISCO-RTR-001' THEN 4
        WHEN im.item_code = 'APC-UPS-001' THEN 6
    END as quantity,
    '[]'::json,
    'PENDING',
    false,
    false
FROM projects p
CROSS JOIN items_master im
WHERE p.project_code = 'PROJ-2025-002'
  AND im.item_code IN ('CISCO-FW-001', 'CISCO-RTR-001', 'APC-UPS-001')
LIMIT 3;

-- Project 3 Items (Enterprise Software)
INSERT INTO project_items (
    project_id, master_item_id, item_code, item_name, quantity,
    delivery_options, status, external_purchase, is_finalized
)
SELECT 
    p.id,
    im.id,
    im.item_code,
    im.item_name,
    CASE 
        WHEN im.item_code = 'VMWARE-SW-001' THEN 20
        WHEN im.item_code = 'ARUBA-SW-001' THEN 10
        WHEN im.item_code = 'DELL-DSK-001' THEN 50
    END as quantity,
    '[]'::json,
    'PENDING',
    false,
    false
FROM projects p
CROSS JOIN items_master im
WHERE p.project_code = 'PROJ-2025-003'
  AND im.item_code IN ('VMWARE-SW-001', 'ARUBA-SW-001', 'DELL-DSK-001')
LIMIT 3;

-- ================================================================
-- VERIFICATION QUERIES
-- ================================================================

-- Show created projects
SELECT 
    id, 
    project_code, 
    name, 
    priority_weight,
    budget_amount,
    budget_currency
FROM projects
ORDER BY id;

-- Show created project items
SELECT 
    pi.id,
    p.project_code,
    pi.item_code,
    pi.item_name,
    pi.quantity,
    pi.is_finalized
FROM project_items pi
JOIN projects p ON pi.project_id = p.id
ORDER BY p.id, pi.id;

-- Show project assignments
SELECT 
    u.username,
    p.project_code
FROM project_assignments pa
JOIN users u ON pa.user_id = u.id
JOIN projects p ON pa.project_id = p.id
ORDER BY p.id;

-- Summary
SELECT 
    'Projects' as entity,
    COUNT(*) as count
FROM projects
UNION ALL
SELECT 
    'Project Items',
    COUNT(*)
FROM project_items
UNION ALL
SELECT 
    'Project Assignments',
    COUNT(*)
FROM project_assignments;

COMMIT;

-- ================================================================
-- SUMMARY
-- ================================================================
-- Created:
--   - 3 Projects
--   - 9 Project Items (3 per project, all unfinalized)
--   - 3 Project Assignments (pm1 assigned to all projects)
-- 
-- Preserved:
--   - users table (all users intact)
--   - currencies table (IRR, USD, EUR)
--   - exchange_rates table (all rates preserved)
--   - items_master table (all master items preserved)
-- ================================================================

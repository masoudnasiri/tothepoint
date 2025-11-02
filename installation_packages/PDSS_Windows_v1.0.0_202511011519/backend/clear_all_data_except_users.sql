-- Clear all data from the platform except users
-- This will delete all projects, items, procurement options, decisions, cashflow, etc.
-- but preserve user accounts

BEGIN;

-- Disable triggers temporarily for faster deletion
SET session_replication_role = 'replica';

-- Step 1: Clear optimization and decision data
TRUNCATE TABLE optimization_results CASCADE;
TRUNCATE TABLE finalized_decisions CASCADE;
TRUNCATE TABLE optimization_runs CASCADE;

-- Step 2: Clear cashflow data
TRUNCATE TABLE cashflow_events CASCADE;

-- Step 3: Clear budget data
TRUNCATE TABLE budget_data CASCADE;

-- Step 4: Clear procurement and delivery data
TRUNCATE TABLE procurement_options CASCADE;
TRUNCATE TABLE delivery_options CASCADE;

-- Step 5: Clear project-related data
TRUNCATE TABLE project_items CASCADE;
TRUNCATE TABLE project_phases CASCADE;
TRUNCATE TABLE project_assignments CASCADE;
TRUNCATE TABLE projects CASCADE;

-- Step 6: Clear items master data
TRUNCATE TABLE items_master CASCADE;

-- Step 7: Clear currency-related data (optional - uncomment if you want to clear these)
-- TRUNCATE TABLE exchange_rates CASCADE;
-- DELETE FROM currencies WHERE code != 'IRR'; -- Keep base currency

-- Re-enable triggers
SET session_replication_role = 'origin';

COMMIT;

-- Verify what's left
SELECT 'Users remaining' as table_name, COUNT(*) as count FROM users
UNION ALL
SELECT 'Projects remaining', COUNT(*) FROM projects
UNION ALL
SELECT 'Items remaining', COUNT(*) FROM items_master
UNION ALL
SELECT 'Procurement options remaining', COUNT(*) FROM procurement_options
UNION ALL
SELECT 'Decisions remaining', COUNT(*) FROM finalized_decisions
UNION ALL
SELECT 'Cashflow events remaining', COUNT(*) FROM cashflow_events
UNION ALL
SELECT 'Budget data remaining', COUNT(*) FROM budget_data;

-- Show remaining users
SELECT id, username, email, role, is_active FROM users ORDER BY id;

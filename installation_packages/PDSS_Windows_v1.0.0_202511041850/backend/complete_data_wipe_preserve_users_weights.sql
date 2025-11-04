-- Complete Data Wipe Script - Preserve Users and Decision Factor Weights Only
-- This script removes all operational data while preserving system configuration
-- 
-- Tables to PRESERVE:
-- - users (system users)
-- - decision_factor_weights (system configuration)
--
-- Tables to WIPE:
-- - All other tables with operational data
--
-- Execution Order: Delete in reverse dependency order to avoid foreign key violations

BEGIN;

-- Disable foreign key checks temporarily for faster execution
SET session_replication_role = replica;

-- 1. Delete dependent tables first (those with foreign keys pointing to others)
DELETE FROM cashflow_events;
DELETE FROM supplier_payments;
DELETE FROM finalized_decisions;
DELETE FROM optimization_results;
DELETE FROM optimization_runs;
DELETE FROM procurement_options;
DELETE FROM delivery_options;
DELETE FROM project_items;
DELETE FROM project_assignments;
DELETE FROM project_phases;
DELETE FROM projects;
DELETE FROM supplier_contacts;
DELETE FROM supplier_documents;
DELETE FROM suppliers;
DELETE FROM items_master;
DELETE FROM exchange_rates;
DELETE FROM currencies;
DELETE FROM budget_data;

-- 2. Reset sequences to start from 1 for clean data
-- This ensures new data starts with clean IDs
ALTER SEQUENCE IF EXISTS projects_id_seq RESTART WITH 1;
ALTER SEQUENCE IF EXISTS project_items_id_seq RESTART WITH 1;
ALTER SEQUENCE IF EXISTS procurement_options_id_seq RESTART WITH 1;
ALTER SEQUENCE IF EXISTS finalized_decisions_id_seq RESTART WITH 1;
ALTER SEQUENCE IF EXISTS optimization_runs_run_id_seq RESTART WITH 1;
ALTER SEQUENCE IF EXISTS optimization_results_id_seq RESTART WITH 1;
ALTER SEQUENCE IF EXISTS delivery_options_id_seq RESTART WITH 1;
ALTER SEQUENCE IF EXISTS suppliers_id_seq RESTART WITH 1;
ALTER SEQUENCE IF EXISTS supplier_contacts_id_seq RESTART WITH 1;
ALTER SEQUENCE IF EXISTS supplier_documents_id_seq RESTART WITH 1;
ALTER SEQUENCE IF EXISTS supplier_payments_id_seq RESTART WITH 1;
ALTER SEQUENCE IF EXISTS items_master_id_seq RESTART WITH 1;
ALTER SEQUENCE IF EXISTS currencies_id_seq RESTART WITH 1;
ALTER SEQUENCE IF EXISTS exchange_rates_id_seq RESTART WITH 1;
ALTER SEQUENCE IF EXISTS cashflow_events_id_seq RESTART WITH 1;
ALTER SEQUENCE IF EXISTS budget_data_id_seq RESTART WITH 1;

-- 3. Re-enable foreign key checks
SET session_replication_role = DEFAULT;

-- 4. Verify preservation of critical data
DO $$
DECLARE
    user_count INTEGER;
    weight_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO user_count FROM users;
    SELECT COUNT(*) INTO weight_count FROM decision_factor_weights;
    
    RAISE NOTICE 'Data wipe completed successfully!';
    RAISE NOTICE 'Users preserved: %', user_count;
    RAISE NOTICE 'Decision factor weights preserved: %', weight_count;
    RAISE NOTICE 'All operational data has been removed.';
    RAISE NOTICE 'Platform is ready for fresh data entry.';
END $$;

COMMIT;

-- Final verification query
SELECT 
    'users' as preserved_table, 
    count(*) as record_count 
FROM users 
UNION ALL 
SELECT 
    'decision_factor_weights' as preserved_table, 
    count(*) as record_count 
FROM decision_factor_weights
UNION ALL
SELECT 
    'projects' as wiped_table, 
    count(*) as record_count 
FROM projects
UNION ALL
SELECT 
    'procurement_options' as wiped_table, 
    count(*) as record_count 
FROM procurement_options
UNION ALL
SELECT 
    'finalized_decisions' as wiped_table, 
    count(*) as record_count 
FROM finalized_decisions
ORDER BY preserved_table, wiped_table;

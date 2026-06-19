-- COMPREHENSIVE DATA WIPE SCRIPT
-- Preserves: users, items_master, suppliers
-- Removes: All other operational data

-- Disable foreign key checks temporarily for safe deletion
SET session_replication_role = replica;

-- ==============================================
-- 1. DELETE CASH FLOW AND FINANCIAL DATA
-- ==============================================

-- Delete cash flow events (depends on finalized_decisions)
DELETE FROM cashflow_events;

-- Delete supplier payments (depends on finalized_decisions, projects, suppliers)
DELETE FROM supplier_payments;

-- Delete budget data (standalone)
DELETE FROM budget_data;

-- ==============================================
-- 2. DELETE DECISION AND OPTIMIZATION DATA
-- ==============================================

-- Delete finalized decisions (central table with many dependencies)
DELETE FROM finalized_decisions;

-- Delete optimization results (depends on projects, procurement_options)
DELETE FROM optimization_results;

-- Delete optimization runs (referenced by finalized_decisions)
DELETE FROM optimization_runs;

-- ==============================================
-- 3. DELETE PROCUREMENT AND PROJECT DATA
-- ==============================================

-- Delete procurement options (depends on suppliers, currencies, delivery_options)
DELETE FROM procurement_options;

-- Delete delivery options (depends on project_items)
DELETE FROM delivery_options;

-- Delete project items (depends on projects, items_master)
DELETE FROM project_items;

-- Delete project assignments (depends on projects, users)
DELETE FROM project_assignments;

-- Delete project phases (depends on projects)
DELETE FROM project_phases;

-- Delete projects (depends on users)
DELETE FROM projects;

-- ==============================================
-- 4. DELETE SUPPORTING DATA
-- ==============================================

-- Delete exchange rates (depends on users)
DELETE FROM exchange_rates;

-- Delete decision factor weights (standalone)
DELETE FROM decision_factor_weights;

-- ==============================================
-- 5. DELETE SUPPLIER-RELATED DATA (EXCEPT SUPPLIERS TABLE)
-- ==============================================

-- Delete supplier contacts (depends on suppliers, users)
DELETE FROM supplier_contacts;

-- Delete supplier documents (depends on suppliers, users)
DELETE FROM supplier_documents;

-- ==============================================
-- 6. RESET SEQUENCES FOR CLEAN STATE
-- ==============================================

-- Reset sequences for deleted tables
ALTER SEQUENCE projects_id_seq RESTART WITH 1;
ALTER SEQUENCE project_items_id_seq RESTART WITH 1;
ALTER SEQUENCE procurement_options_id_seq RESTART WITH 1;
ALTER SEQUENCE delivery_options_id_seq RESTART WITH 1;
ALTER SEQUENCE finalized_decisions_id_seq RESTART WITH 1;
ALTER SEQUENCE optimization_results_id_seq RESTART WITH 1;
ALTER SEQUENCE budget_data_id_seq RESTART WITH 1;
ALTER SEQUENCE cashflow_events_id_seq RESTART WITH 1;
ALTER SEQUENCE exchange_rates_id_seq RESTART WITH 1;
ALTER SEQUENCE decision_factor_weights_id_seq RESTART WITH 1;
ALTER SEQUENCE project_assignments_id_seq RESTART WITH 1;
ALTER SEQUENCE project_phases_id_seq RESTART WITH 1;
ALTER SEQUENCE supplier_contacts_id_seq RESTART WITH 1;
ALTER SEQUENCE supplier_documents_id_seq RESTART WITH 1;
ALTER SEQUENCE supplier_payments_id_seq RESTART WITH 1;

-- Re-enable foreign key checks
SET session_replication_role = DEFAULT;

-- ==============================================
-- 7. VERIFICATION QUERIES
-- ==============================================

-- Verify preserved data
SELECT 'USERS' as table_name, COUNT(*) as count FROM users
UNION ALL
SELECT 'ITEMS_MASTER' as table_name, COUNT(*) as count FROM items_master
UNION ALL
SELECT 'SUPPLIERS' as table_name, COUNT(*) as count FROM suppliers
UNION ALL
SELECT 'CURRENCIES' as table_name, COUNT(*) as count FROM currencies;

-- Verify deleted data (should all be 0)
SELECT 'PROJECTS' as table_name, COUNT(*) as count FROM projects
UNION ALL
SELECT 'PROJECT_ITEMS' as table_name, COUNT(*) as count FROM project_items
UNION ALL
SELECT 'PROCUREMENT_OPTIONS' as table_name, COUNT(*) as count FROM procurement_options
UNION ALL
SELECT 'DELIVERY_OPTIONS' as table_name, COUNT(*) as count FROM delivery_options
UNION ALL
SELECT 'FINALIZED_DECISIONS' as table_name, COUNT(*) as count FROM finalized_decisions
UNION ALL
SELECT 'BUDGET_DATA' as table_name, COUNT(*) as count FROM budget_data
UNION ALL
SELECT 'CASHFLOW_EVENTS' as table_name, COUNT(*) as count FROM cashflow_events
UNION ALL
SELECT 'SUPPLIER_PAYMENTS' as table_name, COUNT(*) as count FROM supplier_payments
UNION ALL
SELECT 'SUPPLIER_CONTACTS' as table_name, COUNT(*) as count FROM supplier_contacts
UNION ALL
SELECT 'SUPPLIER_DOCUMENTS' as table_name, COUNT(*) as count FROM supplier_documents;

-- ==============================================
-- COMPLETION MESSAGE
-- ==============================================

SELECT 'DATA WIPE COMPLETED SUCCESSFULLY' as status,
       'Preserved: users, items_master, suppliers, currencies' as preserved,
       'Removed: All operational data (projects, decisions, payments, etc.)' as removed;

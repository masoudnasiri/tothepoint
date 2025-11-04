-- ============================================
-- CLEAN RESET: Projects Only (No Operational Data)
-- ============================================
-- This script wipes all operational data and creates clean projects
-- Then we can test the platform flow manually using the UI/API
-- ============================================

BEGIN;

-- ============================================
-- STEP 1: Delete all operational data (respect foreign keys)
-- ============================================

DELETE FROM finalized_decisions;
DELETE FROM budget_data;
DELETE FROM optimization_results;
DELETE FROM project_phases;
DELETE FROM procurement_options;
DELETE FROM delivery_options;
DELETE FROM project_items;
DELETE FROM project_assignments;
DELETE FROM projects;

-- Reset sequences
ALTER SEQUENCE projects_id_seq RESTART WITH 1;
ALTER SEQUENCE project_items_id_seq RESTART WITH 1;
ALTER SEQUENCE procurement_options_id_seq RESTART WITH 1;
ALTER SEQUENCE delivery_options_id_seq RESTART WITH 1;
ALTER SEQUENCE finalized_decisions_id_seq RESTART WITH 1;
ALTER SEQUENCE budget_data_id_seq RESTART WITH 1;

-- ============================================
-- STEP 2: Insert Clean Projects (No Items)
-- ============================================

INSERT INTO projects (project_code, name, priority_weight, budget_amount, budget_currency, is_active) VALUES
('DC-MOD-2025', 'Data Center Modernization', 9, 5000000.00, 'USD', true),
('OFF-IT-2025', 'Office IT Refresh', 7, 1500000.00, 'USD', true),
('NET-INF-2025', 'Network Infrastructure Upgrade', 8, 3000000.00, 'USD', true),
('SRV-VIRT-2025', 'Server Virtualization Project', 6, 2500000.00, 'USD', true),
('STR-EXP-2025', 'Storage Expansion Initiative', 7, 1800000.00, 'USD', true),
('SEC-SYS-2025', 'Security Systems Upgrade', 9, 2200000.00, 'USD', true),
('BKP-DR-2025', 'Backup and Disaster Recovery', 8, 1200000.00, 'USD', true),
('WLAN-EXP-2025', 'Wireless Network Expansion', 6, 800000.00, 'USD', true),
('VID-CONF-2025', 'Video Conferencing Upgrade', 5, 600000.00, 'USD', true),
('PRT-INF-2025', 'Printing Infrastructure Renewal', 4, 400000.00, 'USD', true);

-- ============================================
-- STEP 3: Assign Project Managers
-- ============================================

-- Get actual user IDs
DO $$
DECLARE
    pm1_id INTEGER;
    pm2_id INTEGER;
BEGIN
    -- Get PM user IDs
    SELECT id INTO pm1_id FROM users WHERE username = 'pm1' LIMIT 1;
    SELECT id INTO pm2_id FROM users WHERE username = 'pm2' LIMIT 1;
    
    -- Assign PM1 to first 5 projects
    IF pm1_id IS NOT NULL THEN
        INSERT INTO project_assignments (user_id, project_id)
        SELECT pm1_id, id FROM projects WHERE project_code IN 
            ('DC-MOD-2025', 'OFF-IT-2025', 'NET-INF-2025', 'SRV-VIRT-2025', 'STR-EXP-2025');
    END IF;
    
    -- Assign PM2 to last 5 projects
    IF pm2_id IS NOT NULL THEN
        INSERT INTO project_assignments (user_id, project_id)
        SELECT pm2_id, id FROM projects WHERE project_code IN 
            ('SEC-SYS-2025', 'BKP-DR-2025', 'WLAN-EXP-2025', 'VID-CONF-2025', 'PRT-INF-2025');
    END IF;
END $$;

-- ============================================
-- VERIFICATION
-- ============================================

SELECT '======================================' as "CLEAN RESET SUMMARY";
SELECT 'Projects Created:' as metric, COUNT(*)::text as value FROM projects
UNION ALL
SELECT 'Project Assignments:', COUNT(*)::text FROM project_assignments
UNION ALL
SELECT 'Project Items (should be 0):', COUNT(*)::text FROM project_items
UNION ALL
SELECT 'Procurement Options (should be 0):', COUNT(*)::text FROM procurement_options
UNION ALL
SELECT 'Finalized Decisions (should be 0):', COUNT(*)::text FROM finalized_decisions;

SELECT '';
SELECT '======================================' as "PROJECTS LIST";
SELECT id, project_code, name, priority_weight, 
       budget_amount || ' ' || budget_currency as budget 
FROM projects ORDER BY id;

SELECT '';
SELECT '======================================' as "PROJECT ASSIGNMENTS";
SELECT pa.project_id, p.project_code, u.username as assigned_pm
FROM project_assignments pa
JOIN projects p ON pa.project_id = p.id
JOIN users u ON pa.user_id = u.id
ORDER BY pa.project_id;

COMMIT;

SELECT '';
SELECT '======================================' as "NEXT STEPS";
SELECT '1. Login as PM (pm1 or pm2)' as step
UNION ALL SELECT '2. Go to Projects → Select a project'
UNION ALL SELECT '3. Add project items from master items'
UNION ALL SELECT '4. Login as PMO (pmo_user) or Admin (admin)'
UNION ALL SELECT '5. Go to Projects → Finalize items'
UNION ALL SELECT '6. Login as Procurement (procurement1)'
UNION ALL SELECT '7. View finalized items in Procurement'
UNION ALL SELECT '8. Add procurement options'
UNION ALL SELECT '9. Finalize procurement decision'
UNION ALL SELECT '10. Login as Finance (finance1)'
UNION ALL SELECT '11. View finalized decisions';


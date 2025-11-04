-- ============================================
-- Complete Seed: Add Master Items + Project Items
-- ============================================
-- This script:
-- 1. Adds items to items_master
-- 2. Creates project items from master items (unfinalized)
-- 3. No procurement options, no delivery data
-- Then test workflow using endpoints
-- ============================================

BEGIN;

-- ============================================
-- STEP 1: Add Master Items to items_master
-- ============================================

-- Dell Products
INSERT INTO items_master (item_code, company, item_name, model, category, unit, is_active, description) VALUES
('DELL-SRV-001', 'Dell', 'PowerEdge R750 Server', 'R750', 'Servers', 'Unit', true, 'Enterprise server with dual processors'),
('DELL-SRV-002', 'Dell', 'PowerEdge R640 Server', 'R640', 'Servers', 'Unit', true, 'Rack server for virtualization'),
('DELL-LAP-001', 'Dell', 'Latitude 5420 Laptop', '5420', 'Laptops', 'Unit', true, 'Business laptop with i5 processor'),
('DELL-LAP-002', 'Dell', 'Latitude 7420 Laptop', '7420', 'Laptops', 'Unit', true, 'Premium business laptop'),
('DELL-DSK-001', 'Dell', 'OptiPlex 7090 Desktop', '7090', 'Desktops', 'Unit', true, 'Business desktop computer'),
('DELL-MON-001', 'Dell', '24" Monitor P2422H', 'P2422H', 'Monitors', 'Unit', true, 'Full HD business monitor'),
('DELL-STR-001', 'Dell', 'PowerVault Storage', 'ME4024', 'Storage', 'Unit', true, 'Enterprise storage system'),
('DELL-NET-001', 'Dell', '10GbE Network Switch', 'N3224P', 'Networking', 'Unit', true, '24-port managed switch'),

-- HP Products
('HP-SRV-001', 'HP', 'ProLiant DL380 Gen10', 'DL380', 'Servers', 'Unit', true, 'Enterprise server platform'),
('HP-LAP-001', 'HP', 'EliteBook 840 G8', '840 G8', 'Laptops', 'Unit', true, 'Business laptop'),
('HP-LAP-002', 'HP', 'EliteBook 850 G8', '850 G8', 'Laptops', 'Unit', true, 'Premium business laptop'),
('HP-PRN-001', 'HP', 'LaserJet Pro M404dn', 'M404dn', 'Printers', 'Unit', true, 'Network laser printer'),
('HP-PRN-002', 'HP', 'LaserJet Pro MFP M428', 'M428', 'Printers', 'Unit', true, 'Multifunction printer'),
('HP-DOCK-001', 'HP', 'USB-C Docking Station', 'G5', 'Accessories', 'Unit', true, 'Universal docking station'),

-- Cisco Products
('CISCO-SW-001', 'Cisco', 'Catalyst 9300 48-Port', 'C9300-48P', 'Networking', 'Unit', true, 'Enterprise switch'),
('CISCO-SW-002', 'Cisco', 'Catalyst 9200 24-Port', 'C9200-24P', 'Networking', 'Unit', true, 'Access switch'),
('CISCO-RTR-001', 'Cisco', 'ISR 4331 Router', '4331', 'Networking', 'Unit', true, 'Enterprise router'),
('CISCO-RTR-002', 'Cisco', 'ISR 4351 Router', '4351', 'Networking', 'Unit', true, 'High-performance router'),
('CISCO-AP-001', 'Cisco', 'Aironet 3800 Access Point', '3800', 'Networking', 'Unit', true, 'Wireless access point'),
('CISCO-AP-002', 'Cisco', 'Aironet 2800 Access Point', '2800', 'Networking', 'Unit', true, 'Standard access point'),
('CISCO-FW-001', 'Cisco', 'Firepower 2130 Firewall', 'FPR2130', 'Security', 'Unit', true, 'Next-gen firewall'),
('CISCO-WLC-001', 'Cisco', 'Wireless LAN Controller', 'WLC3504', 'Networking', 'Unit', true, 'Wireless controller'),

-- Storage Products
('WD-HDD-001', 'Western Digital', 'Gold 10TB Enterprise HDD', 'WD102KRYZ', 'Storage', 'Unit', true, '10TB enterprise hard drive'),
('WD-HDD-002', 'Western Digital', 'Gold 18TB Enterprise HDD', 'WD181KRYZ', 'Storage', 'Unit', true, '18TB enterprise hard drive'),
('SAMSUNG-SSD-001', 'Samsung', '870 EVO 4TB SSD', '870 EVO', 'Storage', 'Unit', true, '4TB solid state drive'),
('SAMSUNG-SSD-002', 'Samsung', '980 PRO 2TB NVMe', '980 PRO', 'Storage', 'Unit', true, '2TB NVMe SSD'),

-- Networking & Security
('UBIQUITI-AP-001', 'Ubiquiti', 'UniFi AP AC Pro', 'UAP-AC-PRO', 'Networking', 'Unit', true, 'Wireless access point'),
('FORTINET-FW-001', 'FortiNet', 'FortiGate 60F', '60F', 'Security', 'Unit', true, 'Firewall appliance'),
('ARUBA-SW-001', 'Aruba', '2930F 48-Port Switch', '2930F', 'Networking', 'Unit', true, 'Managed switch'),

-- Accessories
('LOGITECH-KB-001', 'Logitech', 'MK850 Keyboard/Mouse', 'MK850', 'Accessories', 'Set', true, 'Wireless keyboard and mouse'),
('APC-UPS-001', 'APC', 'Smart-UPS 3000VA', 'SMX3000', 'Power', 'Unit', true, 'Uninterruptible power supply'),

-- Software
('VMWARE-SW-001', 'VMware', 'vSphere Enterprise Plus', 'v7', 'Software', 'License', true, 'Virtualization platform'),
('VMWARE-SW-002', 'VMware', 'vSAN Enterprise', 'v7', 'Software', 'License', true, 'Virtual SAN software'),
('VEEAM-SW-001', 'Veeam', 'Backup & Replication', 'v11', 'Software', 'License', true, 'Backup software');

-- ============================================
-- STEP 2: Add Project Items (Unfinalized)
-- ============================================

-- Project 1: Data Center Modernization (10 items)
INSERT INTO project_items (project_id, master_item_id, item_code, item_name, quantity, delivery_options, status, external_purchase, is_finalized)
SELECT 1, id, item_code, item_name, 
    CASE 
        WHEN item_code LIKE '%SRV%' THEN 5
        WHEN item_code LIKE '%SW%' THEN 4
        WHEN item_code LIKE '%HDD%' THEN 20
        ELSE 3
    END as quantity,
    '[]'::json, 'PENDING', false, false
FROM items_master 
WHERE item_code IN ('DELL-SRV-001', 'CISCO-SW-001', 'WD-HDD-002', 'CISCO-RTR-001', 'APC-UPS-001', 
                    'HP-SRV-001', 'DELL-NET-001', 'CISCO-FW-001', 'DELL-STR-001', 'VMWARE-SW-001');

-- Project 2: Office IT Refresh (10 items)
INSERT INTO project_items (project_id, master_item_id, item_code, item_name, quantity, delivery_options, status, external_purchase, is_finalized)
SELECT 2, id, item_code, item_name,
    CASE 
        WHEN item_code LIKE '%LAP%' THEN 30
        WHEN item_code LIKE '%DSK%' THEN 25
        WHEN item_code LIKE '%MON%' THEN 50
        WHEN item_code LIKE '%PRN%' THEN 10
        ELSE 40
    END as quantity,
    '[]'::json, 'PENDING', false, false
FROM items_master 
WHERE item_code IN ('DELL-LAP-001', 'HP-LAP-001', 'DELL-DSK-001', 'HP-PRN-001', 'DELL-MON-001',
                    'LOGITECH-KB-001', 'HP-DOCK-001', 'DELL-LAP-002', 'HP-LAP-002', 'HP-PRN-002');

-- Project 3: Network Infrastructure (10 items)
INSERT INTO project_items (project_id, master_item_id, item_code, item_name, quantity, delivery_options, status, external_purchase, is_finalized)
SELECT 3, id, item_code, item_name, 
    CASE 
        WHEN item_code LIKE '%SW%' THEN 8
        WHEN item_code LIKE '%RTR%' THEN 3
        WHEN item_code LIKE '%AP%' THEN 25
        ELSE 5
    END as quantity,
    '[]'::json, 'PENDING', false, false
FROM items_master 
WHERE item_code IN ('CISCO-SW-002', 'CISCO-SW-001', 'CISCO-RTR-001', 'CISCO-AP-001', 'UBIQUITI-AP-001',
                    'CISCO-FW-001', 'DELL-NET-001', 'ARUBA-SW-001', 'FORTINET-FW-001', 'CISCO-WLC-001');

-- Project 4: Server Virtualization (8 items)
INSERT INTO project_items (project_id, master_item_id, item_code, item_name, quantity, delivery_options, status, external_purchase, is_finalized)
SELECT 4, id, item_code, item_name,
    CASE 
        WHEN item_code LIKE '%SRV%' THEN 6
        WHEN item_code LIKE '%SW%' THEN 10
        WHEN item_code LIKE '%HDD%' THEN 40
        ELSE 8
    END as quantity,
    '[]'::json, 'PENDING', false, false
FROM items_master 
WHERE item_code IN ('DELL-SRV-001', 'HP-SRV-001', 'VMWARE-SW-001', 'VMWARE-SW-002',
                    'WD-HDD-001', 'DELL-NET-001', 'DELL-SRV-002', 'SAMSUNG-SSD-002');

-- Project 5: Storage Expansion (6 items)
INSERT INTO project_items (project_id, master_item_id, item_code, item_name, quantity, delivery_options, status, external_purchase, is_finalized)
SELECT 5, id, item_code, item_name,
    CASE 
        WHEN item_code LIKE '%HDD%' THEN 50
        WHEN item_code LIKE '%SSD%' THEN 30
        ELSE 2
    END as quantity,
    '[]'::json, 'PENDING', false, false
FROM items_master 
WHERE item_code IN ('DELL-STR-001', 'WD-HDD-002', 'SAMSUNG-SSD-001', 'WD-HDD-001', 'SAMSUNG-SSD-002', 'DELL-SRV-002');

-- Project 6: Security Systems (6 items)
INSERT INTO project_items (project_id, master_item_id, item_code, item_name, quantity, delivery_options, status, external_purchase, is_finalized)
SELECT 6, id, item_code, item_name, 4,
    '[]'::json, 'PENDING', false, false
FROM items_master 
WHERE item_code IN ('CISCO-FW-001', 'FORTINET-FW-001', 'CISCO-SW-001', 'ARUBA-SW-001', 'APC-UPS-001', 'DELL-NET-001');

-- Project 7: Backup and DR (5 items)
INSERT INTO project_items (project_id, master_item_id, item_code, item_name, quantity, delivery_options, status, external_purchase, is_finalized)
SELECT 7, id, item_code, item_name,
    CASE 
        WHEN item_code LIKE '%SW%' THEN 1
        WHEN item_code LIKE '%HDD%' THEN 35
        ELSE 3
    END as quantity,
    '[]'::json, 'PENDING', false, false
FROM items_master 
WHERE item_code IN ('VEEAM-SW-001', 'DELL-SRV-001', 'WD-HDD-002', 'DELL-STR-001', 'HP-SRV-001');

-- Project 8: Wireless Expansion (4 items)
INSERT INTO project_items (project_id, master_item_id, item_code, item_name, quantity, delivery_options, status, external_purchase, is_finalized)
SELECT 8, id, item_code, item_name,
    CASE 
        WHEN item_code LIKE '%AP%' THEN 40
        ELSE 3
    END as quantity,
    '[]'::json, 'PENDING', false, false
FROM items_master 
WHERE item_code IN ('CISCO-AP-001', 'UBIQUITI-AP-001', 'CISCO-WLC-001', 'CISCO-AP-002');

-- Project 9: Video Conferencing (4 items)
INSERT INTO project_items (project_id, master_item_id, item_code, item_name, quantity, delivery_options, status, external_purchase, is_finalized)
SELECT 9, id, item_code, item_name, 10,
    '[]'::json, 'PENDING', false, false
FROM items_master 
WHERE item_code IN ('DELL-MON-001', 'HP-LAP-001', 'LOGITECH-KB-001', 'HP-DOCK-001');

-- Project 10: Printing Infrastructure (3 items)
INSERT INTO project_items (project_id, master_item_id, item_code, item_name, quantity, delivery_options, status, external_purchase, is_finalized)
SELECT 10, id, item_code, item_name,
    CASE 
        WHEN item_code LIKE '%PRN%' THEN 15
        ELSE 10
    END as quantity,
    '[]'::json, 'PENDING', false, false
FROM items_master 
WHERE item_code IN ('HP-PRN-001', 'HP-PRN-002', 'DELL-DSK-001');

-- ============================================
-- VERIFICATION
-- ============================================

SELECT '======================================' as "SEED COMPLETE";
SELECT 'Master Items Added:' as metric, COUNT(*)::text as value FROM items_master WHERE created_at > (NOW() - INTERVAL '1 minute')
UNION ALL
SELECT 'Total Project Items:', COUNT(*)::text FROM project_items
UNION ALL
SELECT 'Finalized Items (should be 0):', COUNT(*)::text FROM project_items WHERE is_finalized = true
UNION ALL
SELECT 'Items with Delivery Data (should be 0):', COUNT(*)::text FROM project_items WHERE delivery_options::text != '[]';

SELECT '';
SELECT '======================================' as "ITEMS PER PROJECT";
SELECT p.id, p.project_code, p.name, COUNT(pi.id) as items
FROM projects p
LEFT JOIN project_items pi ON p.id = pi.project_id
GROUP BY p.id, p.project_code, p.name
ORDER BY p.id;

COMMIT;

-- ============================================
-- TESTING WORKFLOW
-- ============================================
-- Now test the complete workflow:
--
-- 1. LOGIN AS PM (pm1 or pm2)
--    - View projects and their items
--    - Items are not finalized yet
--
-- 2. LOGIN AS ADMIN or PMO (admin or pmo_user)
--    - Go to Projects → Select "DC-MOD-2025"
--    - Click "Finalize" button on an item
--    - This calls: PUT /items/{item_id}/finalize
--
-- 3. LOGIN AS PROCUREMENT (procurement1)
--    - Go to Procurement page
--    - See the finalized item appear
--    - Click to add procurement options
--    - This calls: POST /procurement/options
--    - Add supplier, cost, currency, etc.
--
-- 4. FINALIZE PROCUREMENT DECISION
--    - Select best option
--    - Click finalize
--    - This calls: PUT /procurement/option/{id} (is_finalized=true)
--
-- 5. LOGIN AS FINANCE (finance1)
--    - View finalized decisions
--    - See costs and budgets
--
-- This tests the COMPLETE end-to-end workflow!
-- ============================================

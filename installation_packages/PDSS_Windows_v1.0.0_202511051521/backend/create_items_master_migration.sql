-- Migration: Create Items Master catalog and update project_items
-- Date: 2025-01-10
-- Description: Creates centralized items catalog with auto-generated codes

-- ============================================
-- STEP 1: Create items_master table
-- ============================================

CREATE TABLE IF NOT EXISTS items_master (
    id SERIAL PRIMARY KEY,
    item_code VARCHAR(100) UNIQUE NOT NULL,
    company VARCHAR(100) NOT NULL,
    item_name VARCHAR(200) NOT NULL,
    model VARCHAR(100),
    specifications JSONB,
    category VARCHAR(100),
    unit VARCHAR(50) DEFAULT 'piece',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE,
    created_by_id INT REFERENCES users(id) ON DELETE SET NULL,
    is_active BOOLEAN DEFAULT TRUE
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_items_master_code ON items_master(item_code);
CREATE INDEX IF NOT EXISTS idx_items_master_company ON items_master(company);
CREATE INDEX IF NOT EXISTS idx_items_master_category ON items_master(category);
CREATE INDEX IF NOT EXISTS idx_items_master_active ON items_master(is_active);
CREATE INDEX IF NOT EXISTS idx_items_master_name ON items_master(item_name);

-- ============================================
-- STEP 2: Migrate existing items to master
-- ============================================

-- Insert unique items from project_items into items_master
-- Uses "LEGACY" as company for existing items
INSERT INTO items_master (item_code, company, item_name, model, unit, is_active, created_at)
SELECT DISTINCT ON (item_code)
    item_code,
    'LEGACY' as company,
    COALESCE(item_name, item_code) as item_name,
    '' as model,
    'piece' as unit,  -- Set default unit
    true as is_active,
    MIN(created_at) as created_at
FROM project_items
WHERE item_code IS NOT NULL
  AND item_code != ''
  AND item_code NOT IN (SELECT item_code FROM items_master WHERE item_code IS NOT NULL)
GROUP BY item_code, item_name
ON CONFLICT (item_code) DO NOTHING;

-- Ensure all items have a unit (fix any NULL values)
UPDATE items_master SET unit = 'piece' WHERE unit IS NULL;

-- ============================================
-- STEP 3: Add master_item_id to project_items
-- ============================================

ALTER TABLE project_items
ADD COLUMN IF NOT EXISTS master_item_id INT REFERENCES items_master(id) ON DELETE RESTRICT;

-- Create index for foreign key
CREATE INDEX IF NOT EXISTS idx_project_items_master_item_id ON project_items(master_item_id);

-- ============================================
-- STEP 4: Link existing project items to master
-- ============================================

-- Update project_items to reference master items
UPDATE project_items pi
SET master_item_id = (
    SELECT id FROM items_master im
    WHERE im.item_code = pi.item_code
    LIMIT 1
)
WHERE pi.master_item_id IS NULL
  AND pi.item_code IS NOT NULL
  AND pi.item_code != '';

-- ============================================
-- VERIFICATION
-- ============================================

-- Show migration results
SELECT 
    'Items Master Created' as status,
    COUNT(*) as count
FROM items_master

UNION ALL

SELECT 
    'Project Items Linked' as status,
    COUNT(*) as count
FROM project_items
WHERE master_item_id IS NOT NULL

UNION ALL

SELECT 
    'Project Items Unlinked' as status,
    COUNT(*) as count
FROM project_items
WHERE master_item_id IS NULL;

-- Show sample master items
SELECT id, item_code, company, item_name, model
FROM items_master
ORDER BY created_at DESC
LIMIT 10;


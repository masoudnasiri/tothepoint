-- Migration: Create procurement_packages table
-- Phase: 1.1 - Additive Changes
-- Strategy: Online (no downtime)
-- Dependencies: None (base table, must run first)
--
-- This table groups sub-items into procurement units (packages).
-- Supports FULL (entire project item), PARTIAL (subset), and CUSTOM packages.

BEGIN;

CREATE TABLE IF NOT EXISTS procurement_packages (
    id SERIAL PRIMARY KEY,
    project_item_id INTEGER NOT NULL REFERENCES project_items(id) ON DELETE CASCADE,
    package_name TEXT,
    package_type VARCHAR(20) NOT NULL CHECK (package_type IN ('FULL', 'PARTIAL', 'CUSTOM')),
    supplier_id INTEGER REFERENCES suppliers(id) ON DELETE SET NULL,
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE,
    created_by_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    
    -- Constraints
    CONSTRAINT check_package_type CHECK (package_type IN ('FULL', 'PARTIAL', 'CUSTOM'))
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_procurement_packages_project_item_id 
    ON procurement_packages(project_item_id);
CREATE INDEX IF NOT EXISTS idx_procurement_packages_supplier_id 
    ON procurement_packages(supplier_id);
CREATE INDEX IF NOT EXISTS idx_procurement_packages_package_type 
    ON procurement_packages(package_type);
CREATE INDEX IF NOT EXISTS idx_procurement_packages_is_active 
    ON procurement_packages(is_active);

-- Unique constraint: package_name per project_item (or allow NULL)
CREATE UNIQUE INDEX IF NOT EXISTS idx_procurement_packages_unique_name 
    ON procurement_packages(project_item_id, package_name) 
    WHERE package_name IS NOT NULL;

-- Comments for documentation
COMMENT ON TABLE procurement_packages IS 'Groups sub-items into procurement units (packages). Supports FULL (entire project item), PARTIAL (subset of sub-items), and CUSTOM (user-defined) packages.';
COMMENT ON COLUMN procurement_packages.package_type IS 'FULL: all sub-items of project item, PARTIAL: subset of sub-items, CUSTOM: user-defined package with specific sub-item mix';
COMMENT ON COLUMN procurement_packages.project_item_id IS 'Foreign key to project_items - every package belongs to one project item';
COMMENT ON COLUMN procurement_packages.supplier_id IS 'Optional pre-assigned supplier for this package';
COMMENT ON COLUMN procurement_packages.package_name IS 'Human-readable name for the package (e.g., "Network Package", "Full Package"). Must be unique per project_item_id if not NULL.';

COMMIT;


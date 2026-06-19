-- Migration: Create package_subitems table
-- Phase: 1.2 - Additive Changes
-- Strategy: Online (no downtime)
-- Dependencies: Requires procurement_packages table (1.1)
--
-- This table maps sub-items to packages with coverage details (quantities, percentages).

BEGIN;

CREATE TABLE IF NOT EXISTS package_subitems (
    id SERIAL PRIMARY KEY,
    package_id INTEGER NOT NULL REFERENCES procurement_packages(id) ON DELETE CASCADE,
    project_item_subitem_id INTEGER NOT NULL REFERENCES project_item_subitems(id) ON DELETE CASCADE,
    quantity_covered INTEGER NOT NULL CHECK (quantity_covered >= 0),
    is_fully_covered BOOLEAN DEFAULT FALSE,
    coverage_percentage NUMERIC(5,2) CHECK (coverage_percentage >= 0 AND coverage_percentage <= 100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Prevent duplicate mappings
    CONSTRAINT unique_package_subitem UNIQUE (package_id, project_item_subitem_id)
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_package_subitems_package_id 
    ON package_subitems(package_id);
CREATE INDEX IF NOT EXISTS idx_package_subitems_subitem_id 
    ON package_subitems(project_item_subitem_id);

-- Comments for documentation
COMMENT ON TABLE package_subitems IS 'Maps sub-items to packages with coverage details (quantities, percentages). Defines which sub-items are included in each package and how much of each sub-item requirement is covered.';
COMMENT ON COLUMN package_subitems.package_id IS 'Foreign key to procurement_packages - the package containing this sub-item';
COMMENT ON COLUMN package_subitems.project_item_subitem_id IS 'Foreign key to project_item_subitems - the sub-item being covered';
COMMENT ON COLUMN package_subitems.quantity_covered IS 'How many units of this sub-item are covered by this package';
COMMENT ON COLUMN package_subitems.is_fully_covered IS 'Whether this package fully satisfies the sub-item requirement';
COMMENT ON COLUMN package_subitems.coverage_percentage IS 'Percentage of required quantity covered (0-100). NULL allowed for flexibility.';

COMMIT;


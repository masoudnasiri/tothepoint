-- Migration: Add CHECK constraint to procurement_options
-- Phase: 1.8 - Additive Changes
-- Dependencies: Requires package_id column in procurement_options (1.4)
--
-- Ensures at least one of package_id, project_item_id, or item_code is present.
-- This allows backward compatibility during transition while enforcing data integrity.

BEGIN;

-- Add CHECK constraint: at least one reference must be present
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints 
        WHERE table_name = 'procurement_options' 
        AND constraint_name = 'check_procurement_option_reference'
    ) THEN
        ALTER TABLE procurement_options 
        ADD CONSTRAINT check_procurement_option_reference 
            CHECK (
                (package_id IS NOT NULL) OR 
                (project_item_id IS NOT NULL) OR 
                (item_code IS NOT NULL)
            );
    END IF;
END $$;

-- Comments for documentation
COMMENT ON CONSTRAINT check_procurement_option_reference ON procurement_options IS 
    'Ensures procurement option references package_id (new), project_item_id (legacy), or item_code (legacy). At least one must be present.';
COMMENT ON COLUMN procurement_options.package_id IS 'Foreign key to procurement_packages (new). Preferred for new records.';
COMMENT ON COLUMN procurement_options.project_item_id IS 'Foreign key to project_items (legacy). Deprecated in favor of package_id.';
COMMENT ON COLUMN procurement_options.item_code IS 'Item code string (legacy). Deprecated in favor of package_id.';

COMMIT;


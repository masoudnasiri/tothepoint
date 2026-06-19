-- Migration: Make project_item_id nullable in delivery_options
-- Phase: 1.5 - Additive Changes
-- Strategy: Online (requires CHECK constraint update)
-- Dependencies: Requires package_id column in delivery_options (1.4)
--
-- Allows delivery_options to reference either project_item_id (legacy) or package_id (new).
-- Adds CHECK constraint to ensure at least one is present.

BEGIN;

-- First, add CHECK constraint to ensure at least one of project_item_id OR package_id is present
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints 
        WHERE table_name = 'delivery_options' 
        AND constraint_name = 'check_delivery_option_reference'
    ) THEN
        ALTER TABLE delivery_options 
        ADD CONSTRAINT check_delivery_option_reference 
            CHECK (project_item_id IS NOT NULL OR package_id IS NOT NULL);
    END IF;
END $$;

-- Then make project_item_id nullable (if not already nullable)
DO $$
BEGIN
    -- Check if column is currently NOT NULL
    IF EXISTS (
        SELECT 1 
        FROM information_schema.columns 
        WHERE table_name = 'delivery_options' 
        AND column_name = 'project_item_id' 
        AND is_nullable = 'NO'
    ) THEN
        ALTER TABLE delivery_options 
        ALTER COLUMN project_item_id DROP NOT NULL;
    END IF;
END $$;

-- Comments for documentation
COMMENT ON CONSTRAINT check_delivery_option_reference ON delivery_options IS 
    'Ensures delivery option references either project_item_id (legacy) or package_id (new). At least one must be present.';
COMMENT ON COLUMN delivery_options.project_item_id IS 'Foreign key to project_items (legacy). Nullable to support package-level delivery options.';
COMMENT ON COLUMN delivery_options.package_id IS 'Foreign key to procurement_packages (new). Allows package-level delivery timing configuration.';

COMMIT;


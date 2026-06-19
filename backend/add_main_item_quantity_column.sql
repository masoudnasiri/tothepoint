-- Migration: Add main_item_quantity column to procurement_packages table
-- This column tracks the quantity of the main item covered by the package

BEGIN;

-- Check if column already exists before adding
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 
        FROM information_schema.columns 
        WHERE table_name = 'procurement_packages' 
        AND column_name = 'main_item_quantity'
    ) THEN
        ALTER TABLE procurement_packages 
        ADD COLUMN main_item_quantity INTEGER NULL DEFAULT 0;
        
        COMMENT ON COLUMN procurement_packages.main_item_quantity IS 'Quantity of main item covered by this package';
    END IF;
END $$;

COMMIT;


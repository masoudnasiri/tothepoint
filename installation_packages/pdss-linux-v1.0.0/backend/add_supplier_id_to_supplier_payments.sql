-- Migration: Add supplier_id FK to supplier_payments
-- Phase: 1.6 - Additive Changes
-- Strategy: Online (no downtime)
-- Dependencies: Requires suppliers table to exist
--
-- Adds supplier_id foreign key column to supplier_payments for normalized supplier references.
-- Supplier_id is nullable during transition, but CHECK constraint ensures supplier_id OR supplier_name is present.

BEGIN;

-- Add supplier_id column (nullable during transition)
ALTER TABLE supplier_payments 
ADD COLUMN IF NOT EXISTS supplier_id INTEGER REFERENCES suppliers(id) ON DELETE SET NULL;

CREATE INDEX IF NOT EXISTS idx_supplier_payments_supplier_id 
    ON supplier_payments(supplier_id);

-- Add CHECK constraint: at least one of supplier_id OR supplier_name must be present
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints 
        WHERE table_name = 'supplier_payments' 
        AND constraint_name = 'check_supplier_reference'
    ) THEN
        ALTER TABLE supplier_payments 
        ADD CONSTRAINT check_supplier_reference 
            CHECK (supplier_id IS NOT NULL OR supplier_name IS NOT NULL);
    END IF;
END $$;

-- Comments for documentation
COMMENT ON COLUMN supplier_payments.supplier_id IS 'Foreign key to suppliers table. Required for new records, nullable during transition to support legacy supplier_name field.';
COMMENT ON COLUMN supplier_payments.supplier_name IS 'Legacy field - will be deprecated in favor of supplier_id FK. Required during transition if supplier_id is NULL.';
COMMENT ON CONSTRAINT check_supplier_reference ON supplier_payments IS 
    'Ensures at least one of supplier_id (FK) or supplier_name (legacy) is present. Required for data integrity during transition period.';

COMMIT;


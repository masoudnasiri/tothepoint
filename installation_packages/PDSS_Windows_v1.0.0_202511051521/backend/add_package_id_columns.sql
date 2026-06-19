-- Migration: Add package_id columns to existing tables
-- Phase: 1.4 - Additive Changes
-- Strategy: Online (no downtime, columns nullable)
-- Dependencies: Requires procurement_packages table (1.1)
--
-- Adds package_id foreign key column to multiple tables to enable package-level tracking.
-- All columns are nullable to maintain backward compatibility.

BEGIN;

-- Add package_id to procurement_options
ALTER TABLE procurement_options 
ADD COLUMN IF NOT EXISTS package_id INTEGER REFERENCES procurement_packages(id) ON DELETE SET NULL;

CREATE INDEX IF NOT EXISTS idx_procurement_options_package_id 
    ON procurement_options(package_id);

COMMENT ON COLUMN procurement_options.package_id IS 'Foreign key to procurement_packages. Links procurement options to packages. Nullable during transition to support legacy project_item_id/item_code references.';

-- Add package_id to finalized_decisions
ALTER TABLE finalized_decisions 
ADD COLUMN IF NOT EXISTS package_id INTEGER REFERENCES procurement_packages(id) ON DELETE SET NULL;

CREATE INDEX IF NOT EXISTS idx_finalized_decisions_package_id 
    ON finalized_decisions(package_id);

COMMENT ON COLUMN finalized_decisions.package_id IS 'Foreign key to procurement_packages. Links finalized decisions to packages for package-level execution tracking. Nullable for legacy decisions.';

-- Add package_id to delivery_options
ALTER TABLE delivery_options 
ADD COLUMN IF NOT EXISTS package_id INTEGER REFERENCES procurement_packages(id) ON DELETE SET NULL;

CREATE INDEX IF NOT EXISTS idx_delivery_options_package_id 
    ON delivery_options(package_id);

COMMENT ON COLUMN delivery_options.package_id IS 'Foreign key to procurement_packages. Allows delivery options to be configured at package level. Nullable for legacy project_item_id references.';

-- Add package_id to invoices (if table exists)
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'invoices') THEN
        ALTER TABLE invoices 
        ADD COLUMN IF NOT EXISTS package_id INTEGER REFERENCES procurement_packages(id) ON DELETE SET NULL;
        
        CREATE INDEX IF NOT EXISTS idx_invoices_package_id 
            ON invoices(package_id);
        
        COMMENT ON COLUMN invoices.package_id IS 'Foreign key to procurement_packages. Links invoices to packages for package-level invoicing. NULL indicates consolidated invoice.';
    END IF;
END $$;

-- Add package_id to payments (if table exists)
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'payments') THEN
        ALTER TABLE payments 
        ADD COLUMN IF NOT EXISTS package_id INTEGER REFERENCES procurement_packages(id) ON DELETE SET NULL;
        
        CREATE INDEX IF NOT EXISTS idx_payments_package_id 
            ON payments(package_id);
        
        COMMENT ON COLUMN payments.package_id IS 'Foreign key to procurement_packages. Links buyer receipts (customer payments) to packages. NULL indicates consolidated payment.';
    END IF;
END $$;

-- Add package_id to supplier_payments (if table exists)
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'supplier_payments') THEN
        ALTER TABLE supplier_payments 
        ADD COLUMN IF NOT EXISTS package_id INTEGER REFERENCES procurement_packages(id) ON DELETE SET NULL;
        
        CREATE INDEX IF NOT EXISTS idx_supplier_payments_package_id 
            ON supplier_payments(package_id);
        
        COMMENT ON COLUMN supplier_payments.package_id IS 'Foreign key to procurement_packages. Links supplier payments to packages for package-level payment tracking. NULL indicates consolidated payment.';
    END IF;
END $$;

COMMIT;


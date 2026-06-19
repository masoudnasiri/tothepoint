-- Migration: Link financial records (invoices, payments, supplier_payments) to packages
-- Phase: 2.7 - Data Migration
-- Strategy: Link via finalized_decisions → FULL package

BEGIN;

-- Step 1: Link invoices to packages
DO $$
DECLARE
    updated_count INTEGER := 0;
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'invoices') THEN
        UPDATE invoices i
        SET package_id = (
            SELECT pp.id
            FROM finalized_decisions fd
            JOIN procurement_packages pp ON pp.project_item_id = fd.project_item_id
            WHERE fd.id = i.decision_id
            AND pp.package_type = 'FULL'
            LIMIT 1
        )
        WHERE i.package_id IS NULL
        AND i.decision_id IS NOT NULL
        AND EXISTS (
            SELECT 1
            FROM finalized_decisions fd
            JOIN procurement_packages pp ON pp.project_item_id = fd.project_item_id
            WHERE fd.id = i.decision_id
            AND pp.package_type = 'FULL'
        );
        
        GET DIAGNOSTICS updated_count = ROW_COUNT;
        RAISE NOTICE 'Linked % invoices to packages', updated_count;
        
        INSERT INTO migration_audit_log (
            migration_step,
            records_processed,
            records_succeeded
        ) VALUES (
            'link_invoices',
            updated_count,
            updated_count
        );
    ELSE
        RAISE NOTICE 'invoices table does not exist. Skipping.';
    END IF;
END $$;

-- Step 2: Link payments to packages
DO $$
DECLARE
    updated_count INTEGER := 0;
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'payments') THEN
        UPDATE payments p
        SET package_id = COALESCE(
            -- Try via invoice first
            (SELECT i.package_id FROM invoices i WHERE i.id = p.invoice_id),
            -- Fallback to decision
            (SELECT pp.id
             FROM finalized_decisions fd
             JOIN procurement_packages pp ON pp.project_item_id = fd.project_item_id
             WHERE fd.id = p.decision_id
             AND pp.package_type = 'FULL'
             LIMIT 1)
        )
        WHERE p.package_id IS NULL
        AND (p.invoice_id IS NOT NULL OR p.decision_id IS NOT NULL);
        
        GET DIAGNOSTICS updated_count = ROW_COUNT;
        RAISE NOTICE 'Linked % payments to packages', updated_count;
        
        INSERT INTO migration_audit_log (
            migration_step,
            records_processed,
            records_succeeded
        ) VALUES (
            'link_payments',
            updated_count,
            updated_count
        );
    ELSE
        RAISE NOTICE 'payments table does not exist. Skipping.';
    END IF;
END $$;

-- Step 3: Link supplier_payments to packages
DO $$
DECLARE
    updated_count INTEGER := 0;
BEGIN
    UPDATE supplier_payments sp
    SET package_id = (
        SELECT pp.id
        FROM finalized_decisions fd
        JOIN procurement_packages pp ON pp.project_item_id = fd.project_item_id
        WHERE fd.id = sp.decision_id
        AND pp.package_type = 'FULL'
        LIMIT 1
    )
    WHERE sp.package_id IS NULL
    AND sp.decision_id IS NOT NULL
    AND EXISTS (
        SELECT 1
        FROM finalized_decisions fd
        JOIN procurement_packages pp ON pp.project_item_id = fd.project_item_id
        WHERE fd.id = sp.decision_id
        AND pp.package_type = 'FULL'
    );
    
    GET DIAGNOSTICS updated_count = ROW_COUNT;
    RAISE NOTICE 'Linked % supplier_payments to packages', updated_count;
    
    INSERT INTO migration_audit_log (
        migration_step,
        records_processed,
        records_succeeded
    ) VALUES (
        'link_supplier_payments',
        updated_count,
        updated_count
    );
END $$;

-- Verification query
DO $$
DECLARE
    invoices_total INTEGER;
    invoices_linked INTEGER;
    payments_total INTEGER;
    payments_linked INTEGER;
    supplier_payments_total INTEGER;
    supplier_payments_linked INTEGER;
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'invoices') THEN
        SELECT COUNT(*) INTO invoices_total FROM invoices;
        SELECT COUNT(*) INTO invoices_linked FROM invoices WHERE package_id IS NOT NULL;
    ELSE
        invoices_total := 0;
        invoices_linked := 0;
    END IF;
    
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'payments') THEN
        SELECT COUNT(*) INTO payments_total FROM payments;
        SELECT COUNT(*) INTO payments_linked FROM payments WHERE package_id IS NOT NULL;
    ELSE
        payments_total := 0;
        payments_linked := 0;
    END IF;
    
    SELECT COUNT(*) INTO supplier_payments_total FROM supplier_payments;
    SELECT COUNT(*) INTO supplier_payments_linked FROM supplier_payments WHERE package_id IS NOT NULL;
    
    RAISE NOTICE '=== Financial Records Linking Verification ===';
    RAISE NOTICE 'Invoices: % total, % linked', invoices_total, invoices_linked;
    RAISE NOTICE 'Payments: % total, % linked', payments_total, payments_linked;
    RAISE NOTICE 'Supplier Payments: % total, % linked', supplier_payments_total, supplier_payments_linked;
END $$;

COMMIT;


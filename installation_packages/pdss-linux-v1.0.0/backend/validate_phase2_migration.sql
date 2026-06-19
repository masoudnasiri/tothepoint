-- Migration: Validation queries for Phase 2 migration
-- Phase: 2.8 - Validation
-- Purpose: Comprehensive data integrity checks and reconciliation

BEGIN;

DO $$
DECLARE
    validation_errors INTEGER := 0;
BEGIN
    RAISE NOTICE '=== Phase 2 Migration Validation ===';
    RAISE NOTICE '';
    
    -- 1. Verify FULL packages created for all items with sub-items
    RAISE NOTICE '1. Checking FULL package coverage...';
    PERFORM
    FROM project_items pi
    WHERE EXISTS (SELECT 1 FROM project_item_subitems WHERE project_item_id = pi.id)
    AND NOT EXISTS (
        SELECT 1 
        FROM procurement_packages pp 
        WHERE pp.project_item_id = pi.id 
        AND pp.package_type = 'FULL'
    );
    
    IF FOUND THEN
        validation_errors := validation_errors + 1;
        RAISE WARNING '  ✗ Found project items with sub-items but no FULL packages';
    ELSE
        RAISE NOTICE '  ✓ All items with sub-items have FULL packages';
    END IF;
    
    -- 2. Verify package_subitems coverage
    RAISE NOTICE '2. Checking package_subitems coverage...';
    PERFORM
    FROM project_item_subitems pis
    WHERE EXISTS (
        SELECT 1 
        FROM procurement_packages pp 
        WHERE pp.project_item_id = pis.project_item_id 
        AND pp.package_type = 'FULL'
    )
    AND NOT EXISTS (
        SELECT 1 
        FROM package_subitems psi 
        WHERE psi.project_item_subitem_id = pis.id
    );
    
    IF FOUND THEN
        validation_errors := validation_errors + 1;
        RAISE WARNING '  ✗ Found sub-items without package_subitems entries';
    ELSE
        RAISE NOTICE '  ✓ All sub-items linked to packages';
    END IF;
    
    -- 3. Verify procurement_options linking
    RAISE NOTICE '3. Checking procurement_options linking...';
    PERFORM
    FROM procurement_options po
    WHERE po.project_item_id IS NOT NULL
    AND po.package_id IS NULL
    AND EXISTS (
        SELECT 1 
        FROM procurement_packages pp 
        WHERE pp.project_item_id = po.project_item_id 
        AND pp.package_type = 'FULL'
    );
    
    IF FOUND THEN
        validation_errors := validation_errors + 1;
        RAISE WARNING '  ✗ Found procurement_options with project_item_id but no package_id';
    ELSE
        RAISE NOTICE '  ✓ All procurement_options linked to packages (where applicable)';
    END IF;
    
    -- 4. Verify finalized_decisions linking
    RAISE NOTICE '4. Checking finalized_decisions linking...';
    PERFORM
    FROM finalized_decisions fd
    WHERE fd.package_id IS NULL
    AND EXISTS (
        SELECT 1 
        FROM procurement_packages pp 
        WHERE pp.project_item_id = fd.project_item_id 
        AND pp.package_type = 'FULL'
    );
    
    IF FOUND THEN
        validation_errors := validation_errors + 1;
        RAISE WARNING '  ✗ Found finalized_decisions without package_id (where FULL package exists)';
    ELSE
        RAISE NOTICE '  ✓ All finalized_decisions linked to packages (where applicable)';
    END IF;
    
    -- 5. Verify supplier normalization
    RAISE NOTICE '5. Checking supplier normalization...';
    PERFORM
    FROM procurement_options po
    WHERE po.supplier_name IS NOT NULL
    AND po.supplier_id IS NULL
    AND NOT EXISTS (
        SELECT 1 
        FROM migration_unmatched_suppliers mus 
        WHERE mus.table_name = 'procurement_options' 
        AND mus.record_id = po.id
        AND mus.resolved = FALSE
    );
    
    IF FOUND THEN
        validation_errors := validation_errors + 1;
        RAISE WARNING '  ✗ Found procurement_options with supplier_name but no supplier_id (and not logged as unmatched)';
    ELSE
        RAISE NOTICE '  ✓ Supplier normalization complete (unmatched logged for review)';
    END IF;
    
    -- 6. Summary statistics
    RAISE NOTICE '';
    RAISE NOTICE '=== Summary Statistics ===';
    
    RAISE NOTICE 'FULL Packages: %', (SELECT COUNT(*) FROM procurement_packages WHERE package_type = 'FULL');
    RAISE NOTICE 'Package Subitems: %', (SELECT COUNT(*) FROM package_subitems);
    RAISE NOTICE 'Procurement Options with package_id: %', (SELECT COUNT(*) FROM procurement_options WHERE package_id IS NOT NULL);
    RAISE NOTICE 'Finalized Decisions with package_id: %', (SELECT COUNT(*) FROM finalized_decisions WHERE package_id IS NOT NULL);
    RAISE NOTICE 'Unmatched Suppliers: %', (SELECT COUNT(*) FROM migration_unmatched_suppliers WHERE resolved = FALSE);
    
    -- Final validation result
    RAISE NOTICE '';
    IF validation_errors = 0 THEN
        RAISE NOTICE '✅ Validation PASSED: All checks passed';
    ELSE
        RAISE WARNING '⚠️  Validation found % issue(s). Review warnings above.', validation_errors;
    END IF;
    
END $$;

COMMIT;

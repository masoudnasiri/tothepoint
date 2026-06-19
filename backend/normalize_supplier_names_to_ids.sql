-- Migration: Normalize supplier_name to supplier_id in procurement_options and supplier_payments
-- Phase: 2.6 - Data Migration
-- Strategy: Deterministic matching using LOWER(TRIM()), log unmatched for manual review

BEGIN;

-- Step 1: Normalize procurement_options
DO $$
DECLARE
    batch_size INTEGER := 1000;
    processed_count INTEGER := 0;
    updated_count INTEGER := 0;
    unmatched_count INTEGER := 0;
    start_time TIMESTAMP;
    batch_start_id INTEGER;
    batch_end_id INTEGER;
    matched_supplier_id INTEGER;
    supplier_name_text TEXT;
BEGIN
    start_time := clock_timestamp();
    
    -- Get min and max procurement_option IDs for batching
    SELECT MIN(id), MAX(id) INTO batch_start_id, batch_end_id
    FROM procurement_options
    WHERE supplier_id IS NULL
    AND supplier_name IS NOT NULL;
    
    IF batch_start_id IS NULL THEN
        RAISE NOTICE 'No procurement options with supplier_name to normalize.';
    ELSE
        -- Process in batches
        DECLARE
            current_batch_start INTEGER;
            current_batch_end INTEGER;
        BEGIN
            current_batch_start := batch_start_id;
            
            WHILE current_batch_start <= batch_end_id LOOP
                current_batch_end := LEAST(current_batch_start + batch_size - 1, (SELECT MAX(id) FROM procurement_options));
                
                -- Process each option in current batch
                FOR supplier_name_text, matched_supplier_id IN 
                    SELECT DISTINCT po.supplier_name, (
                        SELECT s.id
                        FROM suppliers s
                        WHERE LOWER(TRIM(s.company_name)) = LOWER(TRIM(po.supplier_name))
                        LIMIT 1
                    ) as supplier_id
                    FROM procurement_options po
                    WHERE po.id BETWEEN current_batch_start AND current_batch_end
                AND po.supplier_id IS NULL
                AND po.supplier_name IS NOT NULL
            LOOP
                IF matched_supplier_id IS NOT NULL THEN
                    -- Update all options with this supplier_name
                    UPDATE procurement_options
                    SET supplier_id = matched_supplier_id
                    WHERE supplier_id IS NULL
                    AND LOWER(TRIM(supplier_name)) = LOWER(TRIM(supplier_name_text));
                    
                    GET DIAGNOSTICS updated_count = ROW_COUNT;
                    processed_count := processed_count + updated_count;
                ELSE
                    -- Log unmatched supplier
                    INSERT INTO migration_unmatched_suppliers (
                        table_name,
                        record_id,
                        supplier_name,
                        context
                    )
                    SELECT 
                        'procurement_options',
                        po.id,
                        po.supplier_name,
                        jsonb_build_object(
                            'item_code', po.item_code,
                            'project_item_id', po.project_item_id,
                            'package_id', po.package_id
                        )
                    FROM procurement_options po
                    WHERE po.supplier_id IS NULL
                    AND LOWER(TRIM(po.supplier_name)) = LOWER(TRIM(supplier_name_text))
                    AND po.id BETWEEN current_batch_start AND current_batch_end;
                    
                    GET DIAGNOSTICS unmatched_count = ROW_COUNT;
                END IF;
            END LOOP;
            
            -- Log every batch
            IF processed_count % 1000 = 0 THEN
                RAISE NOTICE 'Normalized % procurement options so far...', processed_count;
            END IF;
            
            -- Log batch completion
            INSERT INTO migration_audit_log (
                migration_step,
                batch_number,
                records_processed,
                records_succeeded,
                execution_time_ms
            ) VALUES (
                'normalize_supplier_names_procurement_options',
                ((current_batch_start - batch_start_id) / batch_size) + 1,
                processed_count + unmatched_count,
                processed_count,
                EXTRACT(EPOCH FROM (clock_timestamp() - start_time) * 1000)::INTEGER
            );
            
            COMMIT;  -- Commit batch
            BEGIN;   -- Start new transaction for next batch
            
            current_batch_start := current_batch_start + batch_size;
            
            END LOOP;
        END;
        
        RAISE NOTICE '=== Procurement Options Supplier Normalization Summary ===';
        RAISE NOTICE 'Total matched: %', processed_count;
        RAISE NOTICE 'Unmatched (logged): %', unmatched_count;
    END IF;
END $$;

-- Step 2: Normalize supplier_payments
DO $$
DECLARE
    batch_size INTEGER := 1000;
    processed_count INTEGER := 0;
    updated_count INTEGER := 0;
    unmatched_count INTEGER := 0;
    start_time TIMESTAMP;
    batch_start_id INTEGER;
    batch_end_id INTEGER;
    matched_supplier_id INTEGER;
    supplier_name_text TEXT;
BEGIN
    start_time := clock_timestamp();
    
    -- Get min and max supplier_payment IDs for batching
    SELECT MIN(id), MAX(id) INTO batch_start_id, batch_end_id
    FROM supplier_payments
    WHERE supplier_id IS NULL
    AND supplier_name IS NOT NULL;
    
    IF batch_start_id IS NULL THEN
        RAISE NOTICE 'No supplier_payments with supplier_name to normalize.';
    ELSE
        -- Process in batches
        DECLARE
            current_batch_start INTEGER;
            current_batch_end INTEGER;
        BEGIN
            current_batch_start := batch_start_id;
            
            WHILE current_batch_start <= batch_end_id LOOP
                current_batch_end := LEAST(current_batch_start + batch_size - 1, (SELECT MAX(id) FROM supplier_payments));
                
                -- Process each payment in current batch
                FOR supplier_name_text, matched_supplier_id IN 
                    SELECT DISTINCT sp.supplier_name, (
                        SELECT s.id
                        FROM suppliers s
                        WHERE LOWER(TRIM(s.company_name)) = LOWER(TRIM(sp.supplier_name))
                        LIMIT 1
                    ) as supplier_id
                    FROM supplier_payments sp
                    WHERE sp.id BETWEEN current_batch_start AND current_batch_end
                AND sp.supplier_id IS NULL
                AND sp.supplier_name IS NOT NULL
            LOOP
                IF matched_supplier_id IS NOT NULL THEN
                    -- Update all payments with this supplier_name
                    UPDATE supplier_payments
                    SET supplier_id = matched_supplier_id
                    WHERE supplier_id IS NULL
                    AND LOWER(TRIM(supplier_name)) = LOWER(TRIM(supplier_name_text));
                    
                    GET DIAGNOSTICS updated_count = ROW_COUNT;
                    processed_count := processed_count + updated_count;
                ELSE
                    -- Log unmatched supplier
                    INSERT INTO migration_unmatched_suppliers (
                        table_name,
                        record_id,
                        supplier_name,
                        context
                    )
                    SELECT 
                        'supplier_payments',
                        sp.id,
                        sp.supplier_name,
                        jsonb_build_object(
                            'decision_id', sp.decision_id,
                            'item_code', sp.item_code,
                            'package_id', sp.package_id
                        )
                    FROM supplier_payments sp
                    WHERE sp.supplier_id IS NULL
                    AND LOWER(TRIM(sp.supplier_name)) = LOWER(TRIM(supplier_name_text))
                    AND sp.id BETWEEN current_batch_start AND current_batch_end;
                    
                    GET DIAGNOSTICS unmatched_count = ROW_COUNT;
                END IF;
            END LOOP;
            
            -- Log every batch
            IF processed_count % 1000 = 0 THEN
                RAISE NOTICE 'Normalized % supplier payments so far...', processed_count;
            END IF;
            
            -- Log batch completion
            INSERT INTO migration_audit_log (
                migration_step,
                batch_number,
                records_processed,
                records_succeeded,
                execution_time_ms
            ) VALUES (
                'normalize_supplier_names_supplier_payments',
                ((current_batch_start - batch_start_id) / batch_size) + 1,
                processed_count + unmatched_count,
                processed_count,
                EXTRACT(EPOCH FROM (clock_timestamp() - start_time) * 1000)::INTEGER
            );
            
            COMMIT;  -- Commit batch
            BEGIN;   -- Start new transaction for next batch
            
            current_batch_start := current_batch_start + batch_size;
            
            END LOOP;
        END;
        
        RAISE NOTICE '=== Supplier Payments Supplier Normalization Summary ===';
        RAISE NOTICE 'Total matched: %', processed_count;
        RAISE NOTICE 'Unmatched (logged): %', unmatched_count;
    END IF;
END $$;

-- Verification query
DO $$
DECLARE
    total_options INTEGER;
    options_with_supplier_id INTEGER;
    unmatched_suppliers_count INTEGER;
    total_payments INTEGER;
    payments_with_supplier_id INTEGER;
    unmatched_payments_count INTEGER;
BEGIN
    -- Procurement options
    SELECT COUNT(*) INTO total_options FROM procurement_options WHERE supplier_name IS NOT NULL;
    SELECT COUNT(*) INTO options_with_supplier_id FROM procurement_options WHERE supplier_name IS NOT NULL AND supplier_id IS NOT NULL;
    SELECT COUNT(*) INTO unmatched_suppliers_count FROM migration_unmatched_suppliers WHERE table_name = 'procurement_options' AND resolved = FALSE;
    
    -- Supplier payments
    SELECT COUNT(*) INTO total_payments FROM supplier_payments WHERE supplier_name IS NOT NULL;
    SELECT COUNT(*) INTO payments_with_supplier_id FROM supplier_payments WHERE supplier_name IS NOT NULL AND supplier_id IS NOT NULL;
    SELECT COUNT(*) INTO unmatched_payments_count FROM migration_unmatched_suppliers WHERE table_name = 'supplier_payments' AND resolved = FALSE;
    
    RAISE NOTICE '=== Supplier Normalization Verification ===';
    RAISE NOTICE 'Procurement Options:';
    RAISE NOTICE '  Total with supplier_name: %', total_options;
    RAISE NOTICE '  Matched to supplier_id: %', options_with_supplier_id;
    RAISE NOTICE '  Unmatched (require review): %', unmatched_suppliers_count;
    RAISE NOTICE 'Supplier Payments:';
    RAISE NOTICE '  Total with supplier_name: %', total_payments;
    RAISE NOTICE '  Matched to supplier_id: %', payments_with_supplier_id;
    RAISE NOTICE '  Unmatched (require review): %', unmatched_payments_count;
    
    IF unmatched_suppliers_count > 0 OR unmatched_payments_count > 0 THEN
        RAISE WARNING 'Found unmatched suppliers. Review migration_unmatched_suppliers table and resolve manually.';
    END IF;
END $$;

COMMIT;


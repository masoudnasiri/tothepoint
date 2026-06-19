-- Migration: Populate package_subitems from project_item_subitems
-- Phase: 2.2 - Data Migration
-- Strategy: Link all sub-items to their FULL packages with 100% coverage

BEGIN;

DO $$
DECLARE
    batch_size INTEGER := 1000;
    processed_count INTEGER := 0;
    created_count INTEGER := 0;
    skipped_count INTEGER := 0;
    error_count INTEGER := 0;
    start_time TIMESTAMP;
    batch_start_id INTEGER;
    batch_end_id INTEGER;
    subitem_rec RECORD;
BEGIN
    start_time := clock_timestamp();
    
    -- Get min and max subitem IDs for batching
    SELECT MIN(id), MAX(id) INTO batch_start_id, batch_end_id
    FROM project_item_subitems;
    
    IF batch_start_id IS NULL THEN
        RAISE NOTICE 'No project item sub-items found. Skipping package_subitems creation.';
        RETURN;
    END IF;
    
    -- Process in batches
    DECLARE
        current_batch_start INTEGER;
        current_batch_end INTEGER;
    BEGIN
        current_batch_start := batch_start_id;
        
        WHILE current_batch_start <= batch_end_id LOOP
            current_batch_end := LEAST(current_batch_start + batch_size - 1, batch_end_id);
            
            -- Process each sub-item in current batch
            FOR subitem_rec IN 
                SELECT 
                    pis.id as subitem_id,
                    pis.project_item_id,
                    pis.quantity,
                    pp.id as package_id
                FROM project_item_subitems pis
                INNER JOIN procurement_packages pp 
                    ON pp.project_item_id = pis.project_item_id 
                    AND pp.package_type = 'FULL'
                WHERE pis.id BETWEEN current_batch_start AND current_batch_end
            AND NOT EXISTS (
                SELECT 1 
                FROM package_subitems psi 
                WHERE psi.project_item_subitem_id = pis.id
            )
        LOOP
            BEGIN
                -- Create package_subitem entry
                INSERT INTO package_subitems (
                    package_id,
                    project_item_subitem_id,
                    quantity_covered,
                    is_fully_covered,
                    coverage_percentage,
                    created_at
                ) VALUES (
                    subitem_rec.package_id,
                    subitem_rec.subitem_id,
                    subitem_rec.quantity,
                    TRUE,
                    100.0,
                    NOW()
                );
                
                created_count := created_count + 1;
                processed_count := processed_count + 1;
                
                -- Log every 100 records
                IF created_count % 100 = 0 THEN
                    RAISE NOTICE 'Created % package_subitems so far...', created_count;
                END IF;
                
            EXCEPTION WHEN OTHERS THEN
                error_count := error_count + 1;
                -- Log error but continue
                INSERT INTO migration_audit_log (
                    migration_step, 
                    records_failed, 
                    error_message, 
                    metadata
                ) VALUES (
                    'populate_package_subitems',
                    1,
                    SQLERRM,
                    jsonb_build_object(
                        'subitem_id', subitem_rec.subitem_id,
                        'project_item_id', subitem_rec.project_item_id,
                        'package_id', subitem_rec.package_id
                    )
                );
            END;
        END LOOP;
        
        -- Log batch completion
        INSERT INTO migration_audit_log (
            migration_step,
            batch_number,
            records_processed,
            records_succeeded,
            records_failed,
            execution_time_ms
        ) VALUES (
            'populate_package_subitems',
            ((current_batch_start - batch_start_id) / batch_size) + 1,
            processed_count,
            created_count,
            error_count,
            EXTRACT(EPOCH FROM (clock_timestamp() - start_time) * 1000)::INTEGER
        );
        
        COMMIT;  -- Commit batch
        BEGIN;   -- Start new transaction for next batch
        
        current_batch_start := current_batch_start + batch_size;
        
        END LOOP;
    END;
    
    -- Final summary
    RAISE NOTICE '=== Package Subitems Creation Summary ===';
    RAISE NOTICE 'Total processed: %', processed_count;
    RAISE NOTICE 'Package subitems created: %', created_count;
    RAISE NOTICE 'Already existed (skipped): %', skipped_count;
    RAISE NOTICE 'Errors: %', error_count;
    RAISE NOTICE 'Execution time: % ms', EXTRACT(EPOCH FROM (clock_timestamp() - start_time) * 1000)::INTEGER;
    
END $$;

-- Verification query
DO $$
DECLARE
    total_subitems INTEGER;
    linked_subitems INTEGER;
    orphaned_subitems INTEGER;
    coverage_percentage NUMERIC;
BEGIN
    SELECT COUNT(*) INTO total_subitems
    FROM project_item_subitems;
    
    SELECT COUNT(*) INTO linked_subitems
    FROM package_subitems;
    
    -- Find orphaned sub-items (no corresponding FULL package)
    SELECT COUNT(*) INTO orphaned_subitems
    FROM project_item_subitems pis
    WHERE NOT EXISTS (
        SELECT 1 
        FROM procurement_packages pp 
        WHERE pp.project_item_id = pis.project_item_id 
        AND pp.package_type = 'FULL'
    );
    
    coverage_percentage := CASE 
        WHEN total_subitems > 0 
        THEN (linked_subitems::NUMERIC / total_subitems::NUMERIC * 100)
        ELSE 0
    END;
    
    RAISE NOTICE '=== Verification Results ===';
    RAISE NOTICE 'Total sub-items: %', total_subitems;
    RAISE NOTICE 'Linked to packages: %', linked_subitems;
    RAISE NOTICE 'Orphaned (no FULL package): %', orphaned_subitems;
    RAISE NOTICE 'Coverage: %%', ROUND(coverage_percentage, 2);
    
    IF orphaned_subitems > 0 THEN
        RAISE WARNING 'Found % orphaned sub-items without FULL packages. These may be from items without sub-items (expected) or require manual review.', orphaned_subitems;
    END IF;
END $$;

COMMIT;


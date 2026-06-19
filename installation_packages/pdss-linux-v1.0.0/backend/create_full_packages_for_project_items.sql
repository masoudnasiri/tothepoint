-- Migration: Create FULL packages for all project items with sub-items
-- Phase: 2.1 - Data Migration
-- Strategy: One FULL package per project_item that has sub-items
-- Edge cases: Skip items without sub-items, handle inactive projects

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
    project_item_rec RECORD;
    full_package_id INTEGER;
BEGIN
    start_time := clock_timestamp();
    
    -- Get min and max project_item IDs for batching
    SELECT MIN(id), MAX(id) INTO batch_start_id, batch_end_id
    FROM project_items;
    
    IF batch_start_id IS NULL THEN
        RAISE NOTICE 'No project items found. Skipping FULL package creation.';
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
            
            -- Process each project item in current batch
            FOR project_item_rec IN 
                SELECT DISTINCT pi.id, pi.item_code, pi.project_id
                FROM project_items pi
                WHERE pi.id BETWEEN current_batch_start AND current_batch_end
            AND EXISTS (
                SELECT 1 
                FROM project_item_subitems pis 
                WHERE pis.project_item_id = pi.id
            )
            AND NOT EXISTS (
                SELECT 1 
                FROM procurement_packages pp 
                WHERE pp.project_item_id = pi.id 
                AND pp.package_type = 'FULL'
            )
        LOOP
            BEGIN
                -- Create FULL package
                INSERT INTO procurement_packages (
                    project_item_id,
                    package_name,
                    package_type,
                    is_active,
                    created_at
                ) VALUES (
                    project_item_rec.id,
                    COALESCE(project_item_rec.item_code, 'ITEM-' || project_item_rec.id) || ' - Full Package',
                    'FULL',
                    TRUE,
                    NOW()
                )
                RETURNING id INTO full_package_id;
                
                created_count := created_count + 1;
                processed_count := processed_count + 1;
                
                -- Log every 100 records
                IF created_count % 100 = 0 THEN
                    RAISE NOTICE 'Created % FULL packages so far...', created_count;
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
                    'create_full_packages',
                    1,
                    SQLERRM,
                    jsonb_build_object(
                        'project_item_id', project_item_rec.id,
                        'item_code', project_item_rec.item_code
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
            'create_full_packages',
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
    RAISE NOTICE '=== FULL Package Creation Summary ===';
    RAISE NOTICE 'Total processed: %', processed_count;
    RAISE NOTICE 'Packages created: %', created_count;
    RAISE NOTICE 'Already existed (skipped): %', skipped_count;
    RAISE NOTICE 'Errors: %', error_count;
    RAISE NOTICE 'Execution time: % ms', EXTRACT(EPOCH FROM (clock_timestamp() - start_time) * 1000)::INTEGER;
    
END $$;

-- Verification query (run after migration)
DO $$
DECLARE
    items_with_subitems INTEGER;
    items_with_full_packages INTEGER;
    coverage_percentage NUMERIC;
BEGIN
    SELECT COUNT(DISTINCT pi.id) INTO items_with_subitems
    FROM project_items pi
    WHERE EXISTS (SELECT 1 FROM project_item_subitems WHERE project_item_id = pi.id);
    
    SELECT COUNT(DISTINCT pp.project_item_id) INTO items_with_full_packages
    FROM procurement_packages pp
    WHERE pp.package_type = 'FULL';
    
    coverage_percentage := CASE 
        WHEN items_with_subitems > 0 
        THEN (items_with_full_packages::NUMERIC / items_with_subitems::NUMERIC * 100)
        ELSE 0
    END;
    
    RAISE NOTICE '=== Verification Results ===';
    RAISE NOTICE 'Project items with sub-items: %', items_with_subitems;
    RAISE NOTICE 'Items with FULL packages: %', items_with_full_packages;
    RAISE NOTICE 'Coverage: %%', ROUND(coverage_percentage, 2);
    
    IF items_with_subitems > 0 AND items_with_full_packages < items_with_subitems THEN
        RAISE WARNING 'Not all items with sub-items have FULL packages. Review required.';
    END IF;
END $$;

COMMIT;


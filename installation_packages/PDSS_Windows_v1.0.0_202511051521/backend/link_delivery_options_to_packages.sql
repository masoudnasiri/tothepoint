-- Migration: Link delivery_options to FULL packages
-- Phase: 2.5 - Data Migration
-- Strategy: Update package_id where project_item_id exists and FULL package exists

BEGIN;

DO $$
DECLARE
    batch_size INTEGER := 1000;
    processed_count INTEGER := 0;
    updated_count INTEGER := 0;
    start_time TIMESTAMP;
    batch_start_id INTEGER;
    batch_end_id INTEGER;
BEGIN
    start_time := clock_timestamp();
    
    -- Get min and max delivery_option IDs for batching
    SELECT MIN(id), MAX(id) INTO batch_start_id, batch_end_id
    FROM delivery_options
    WHERE package_id IS NULL
    AND project_item_id IS NOT NULL;
    
    IF batch_start_id IS NULL THEN
        RAISE NOTICE 'No delivery options to link. All options already have package_id or no project_item_id.';
        RETURN;
    END IF;
    
    -- Process in batches
    DECLARE
        current_batch_start INTEGER;
        current_batch_end INTEGER;
    BEGIN
        current_batch_start := batch_start_id;
        
        WHILE current_batch_start <= batch_end_id LOOP
            current_batch_end := LEAST(current_batch_start + batch_size - 1, (SELECT MAX(id) FROM delivery_options));
            
            -- Update batch
            UPDATE delivery_options do
            SET package_id = (
                SELECT pp.id
                FROM procurement_packages pp
                WHERE pp.project_item_id = do.project_item_id
                AND pp.package_type = 'FULL'
                LIMIT 1
            )
            WHERE do.id BETWEEN current_batch_start AND current_batch_end
        AND do.package_id IS NULL
        AND do.project_item_id IS NOT NULL
        AND EXISTS (
            SELECT 1
            FROM procurement_packages pp
            WHERE pp.project_item_id = do.project_item_id
            AND pp.package_type = 'FULL'
        );
        
        GET DIAGNOSTICS updated_count = ROW_COUNT;
        processed_count := processed_count + updated_count;
        
        -- Log every batch
        IF processed_count % 1000 = 0 THEN
            RAISE NOTICE 'Linked % delivery options so far...', processed_count;
        END IF;
        
        -- Log batch completion
        INSERT INTO migration_audit_log (
            migration_step,
            batch_number,
            records_processed,
            records_succeeded,
            execution_time_ms
        ) VALUES (
            'link_delivery_options',
            ((current_batch_start - batch_start_id) / batch_size) + 1,
            updated_count,
            updated_count,
            EXTRACT(EPOCH FROM (clock_timestamp() - start_time) * 1000)::INTEGER
        );
        
        COMMIT;  -- Commit batch
        BEGIN;   -- Start new transaction for next batch
        
        current_batch_start := current_batch_start + batch_size;
        
        END LOOP;
    END;
    
    -- Final summary
    RAISE NOTICE '=== Delivery Options Linking Summary ===';
    RAISE NOTICE 'Total linked: %', processed_count;
    RAISE NOTICE 'Execution time: % ms', EXTRACT(EPOCH FROM (clock_timestamp() - start_time) * 1000)::INTEGER;
    
END $$;

-- Verification query
DO $$
DECLARE
    total_delivery_options INTEGER;
    options_with_package_id INTEGER;
    options_without_package_id INTEGER;
BEGIN
    SELECT COUNT(*) INTO total_delivery_options FROM delivery_options;
    SELECT COUNT(*) INTO options_with_package_id FROM delivery_options WHERE package_id IS NOT NULL;
    SELECT COUNT(*) INTO options_without_package_id FROM delivery_options WHERE package_id IS NULL AND project_item_id IS NOT NULL;
    
    RAISE NOTICE '=== Verification Results ===';
    RAISE NOTICE 'Total delivery options: %', total_delivery_options;
    RAISE NOTICE 'Linked to packages: %', options_with_package_id;
    RAISE NOTICE 'Unlinked (have project_item_id): %', options_without_package_id;
    
    IF options_without_package_id > 0 THEN
        RAISE WARNING 'Found % delivery options with project_item_id but no package_id. These may be from items without FULL packages (expected) or require manual review.', options_without_package_id;
    END IF;
END $$;

COMMIT;


-- Migration: Link finalized_decisions to FULL packages
-- Phase: 2.4 - Data Migration
-- Strategy: Update package_id via project_item_id → FULL package

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
    
    -- Get min and max decision IDs for batching
    SELECT MIN(id), MAX(id) INTO batch_start_id, batch_end_id
    FROM finalized_decisions
    WHERE package_id IS NULL;
    
    IF batch_start_id IS NULL THEN
        RAISE NOTICE 'No finalized decisions to link. All decisions already have package_id.';
        RETURN;
    END IF;
    
    -- Process in batches
    DECLARE
        current_batch_start INTEGER;
        current_batch_end INTEGER;
    BEGIN
        current_batch_start := batch_start_id;
        
        WHILE current_batch_start <= batch_end_id LOOP
            current_batch_end := LEAST(current_batch_start + batch_size - 1, (SELECT MAX(id) FROM finalized_decisions));
            
            -- Update batch
            UPDATE finalized_decisions fd
            SET package_id = (
                SELECT pp.id
                FROM procurement_packages pp
                WHERE pp.project_item_id = fd.project_item_id
                AND pp.package_type = 'FULL'
                LIMIT 1
            )
            WHERE fd.id BETWEEN current_batch_start AND current_batch_end
        AND fd.package_id IS NULL
        AND EXISTS (
            SELECT 1
            FROM procurement_packages pp
            WHERE pp.project_item_id = fd.project_item_id
            AND pp.package_type = 'FULL'
        );
        
        GET DIAGNOSTICS updated_count = ROW_COUNT;
        processed_count := processed_count + updated_count;
        
        -- Log every batch
        IF processed_count % 1000 = 0 THEN
            RAISE NOTICE 'Linked % finalized decisions so far...', processed_count;
        END IF;
        
        -- Log batch completion
        INSERT INTO migration_audit_log (
            migration_step,
            batch_number,
            records_processed,
            records_succeeded,
            execution_time_ms
        ) VALUES (
            'link_finalized_decisions',
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
    RAISE NOTICE '=== Finalized Decisions Linking Summary ===';
    RAISE NOTICE 'Total linked: %', processed_count;
    RAISE NOTICE 'Execution time: % ms', EXTRACT(EPOCH FROM (clock_timestamp() - start_time) * 1000)::INTEGER;
    
END $$;

-- Verification query
DO $$
DECLARE
    total_decisions INTEGER;
    decisions_with_package_id INTEGER;
    decisions_without_package_id INTEGER;
BEGIN
    SELECT COUNT(*) INTO total_decisions FROM finalized_decisions;
    SELECT COUNT(*) INTO decisions_with_package_id FROM finalized_decisions WHERE package_id IS NOT NULL;
    SELECT COUNT(*) INTO decisions_without_package_id FROM finalized_decisions WHERE package_id IS NULL;
    
    RAISE NOTICE '=== Verification Results ===';
    RAISE NOTICE 'Total finalized decisions: %', total_decisions;
    RAISE NOTICE 'Linked to packages: %', decisions_with_package_id;
    RAISE NOTICE 'Unlinked: %', decisions_without_package_id;
    
    IF decisions_without_package_id > 0 THEN
        RAISE WARNING 'Found % decisions without package_id. These may be from items without FULL packages (expected) or require manual review.', decisions_without_package_id;
    END IF;
END $$;

COMMIT;


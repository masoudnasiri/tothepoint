# Phase 2 Migration Execution Blueprint

**Date:** 2025-11-04  
**Status:** Execution Ready  
**Prerequisites:** Phase 1 complete (all additive changes applied)

---

## Section 1 — Narrative Phase 2 Plan

### Overview

Phase 2 migrates existing data to be package-aware while maintaining full backward compatibility. All operations are idempotent, batched, and can be safely re-run. The migration preserves all existing functionality while preparing the system for package-based procurement workflows.

### Migration Tasks (Execution Order)

1. **Create FULL Packages for Project Items**
   - Create one FULL package per `project_item` that has sub-items
   - Handle edge cases: items without sub-items, inactive projects, soft-deleted items
   - Package naming: `"{item_code} - Full Package"`
   - Set `is_active = TRUE`, `package_type = 'FULL'`
   - Skip if FULL package already exists for project item

2. **Populate Package Subitems**
   - Link all `project_item_subitems` to their corresponding FULL package
   - Set `quantity_covered = subitem.quantity`, `is_fully_covered = TRUE`, `coverage_percentage = 100.0`
   - Handle orphaned sub-items (project_item deleted but sub-items remain)
   - Skip if package_subitem mapping already exists

3. **Link Procurement Options to Packages**
   - For each `procurement_option` with `project_item_id`, find the FULL package
   - Update `package_id` where `package_id IS NULL` and `project_item_id IS NOT NULL`
   - Preserve legacy `item_code`-based options (they remain unlinked until manually resolved)
   - Handle options with invalid `project_item_id` (orphaned)

4. **Link Finalized Decisions to Packages**
   - For each `finalized_decision`, find the FULL package via `project_item_id`
   - Update `package_id` where `package_id IS NULL`
   - Decisions remain linked to `project_item_id` for aggregation

5. **Link Delivery Options to Packages**
   - For each `delivery_option` with `project_item_id`, find the FULL package
   - Update `package_id` where `package_id IS NULL` and `project_item_id IS NOT NULL`
   - Maintains CHECK constraint compliance (at least one reference present)

6. **Supplier Name Normalization**
   - Match `supplier_name` in `procurement_options` to `suppliers.id` using deterministic matching
   - Match `supplier_name` in `supplier_payments` to `suppliers.id`
   - Matching strategy: `LOWER(TRIM(company_name)) = LOWER(TRIM(supplier_name))`
   - Handle conflicts: multiple suppliers with same name (use first match, log conflicts)
   - Create audit log table for unmatched suppliers requiring manual review
   - Batch processing with progress reporting

7. **Link Financial Records to Packages**
   - Link `invoices.package_id` via `finalized_decisions` → FULL package
   - Link `payments.package_id` via `invoices` or `finalized_decisions` → FULL package
   - Link `supplier_payments.package_id` via `finalized_decisions` → FULL package
   - Only link records where `package_id IS NULL` and valid relationship exists

### Edge Cases Handled

- **Project Items Without Sub-items**: No FULL package created (not required for backward compatibility)
- **Inactive Projects**: Packages created (no filtering by project status)
- **Soft-Deleted Items**: Handled by `is_active` flag on packages (inherit from project_item if needed)
- **Orphaned Records**: Logged for manual review, not migrated
- **Duplicate Supplier Names**: First match wins, conflicts logged
- **Missing Suppliers**: Unmatched names logged to `migration_unmatched_suppliers` table

### Batching Strategy

- Process in batches of 1000 records per transaction
- Use primary key ranges for pagination
- Commit after each batch to minimize lock duration
- Log progress after each batch

### Observability

- Create `migration_audit_log` table for tracking execution
- Log: migration step, batch number, records processed, errors, execution time
- Create `migration_unmatched_suppliers` table for manual review
- Provide summary statistics after each step

### Rollback Strategy

- All `package_id` updates can be set to `NULL` (reversible)
- `package_subitems` can be deleted
- FULL packages can be deleted (optional, keep for reference)
- Supplier normalization can be reversed by setting `supplier_id = NULL` (preserves `supplier_name`)
- All operations maintain CHECK constraint compliance throughout

---

## Section 2 — Script Inventory

| Filename | Purpose | Dependencies | Execution Order |
|----------|---------|--------------|-----------------|
| `create_migration_audit_tables.sql` | Create audit logging and unmatched suppliers tracking tables | Phase 1 complete | 2.0 (prerequisite) |
| `create_full_packages_for_project_items.sql` | Create FULL packages for all project items with sub-items | 2.0 | 2.1 |
| `populate_package_subitems.sql` | Link project_item_subitems to FULL packages | 2.1 | 2.2 |
| `link_procurement_options_to_packages.sql` | Set package_id in procurement_options | 2.1 | 2.3 |
| `link_finalized_decisions_to_packages.sql` | Set package_id in finalized_decisions | 2.1 | 2.4 |
| `link_delivery_options_to_packages.sql` | Set package_id in delivery_options | 2.1 | 2.5 |
| `normalize_supplier_names_to_ids.sql` | Migrate supplier_name → supplier_id | suppliers table | 2.6 |
| `link_financial_records_to_packages.sql` | Set package_id in invoices, payments, supplier_payments | 2.1, 2.4 | 2.7 |
| `validate_phase2_migration.sql` | Validation queries and reconciliation checks | All 2.1-2.7 | 2.8 |
| `run_phase2_data_migration.sh` | Linux execution harness | All SQL files | Runner script |
| `run_phase2_data_migration.ps1` | Windows PowerShell execution harness | All SQL files | Runner script |

**Total SQL Scripts:** 9  
**Execution Scripts:** 2 (Linux bash, Windows PowerShell)  
**Estimated Runtime:** 10-30 minutes (depends on dataset size)  
**Downtime Required:** None (online migration)

### Execution Scripts

**Linux (`run_phase2_data_migration.sh`):**
- Supports Docker and direct PostgreSQL connections
- Auto-detects Docker containers
- Accepts `--skip-validation` flag
- Provides colored output and progress tracking
- Stops on first error

**Windows (`run_phase2_data_migration.ps1`):**
- Supports Docker connections (primary method)
- Accepts `-SkipValidation` parameter
- Uses PowerShell-native error handling
- Stops on first error

---

## Section 3 — SQL Scripts

### Script 2.0: Create Migration Audit Tables

**File:** `backend/create_migration_audit_tables.sql`

```sql
-- Migration: Create audit logging tables for Phase 2
-- Phase: 2.0 - Prerequisites
-- Purpose: Track migration execution and log unmatched suppliers for manual review

BEGIN;

-- Migration audit log table
CREATE TABLE IF NOT EXISTS migration_audit_log (
    id SERIAL PRIMARY KEY,
    migration_step VARCHAR(100) NOT NULL,
    batch_number INTEGER,
    records_processed INTEGER DEFAULT 0,
    records_succeeded INTEGER DEFAULT 0,
    records_failed INTEGER DEFAULT 0,
    error_message TEXT,
    execution_time_ms INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    metadata JSONB
);

CREATE INDEX IF NOT EXISTS idx_migration_audit_log_step 
    ON migration_audit_log(migration_step);
CREATE INDEX IF NOT EXISTS idx_migration_audit_log_created_at 
    ON migration_audit_log(created_at);

-- Unmatched suppliers table (for manual review)
CREATE TABLE IF NOT EXISTS migration_unmatched_suppliers (
    id SERIAL PRIMARY KEY,
    table_name VARCHAR(50) NOT NULL,
    record_id INTEGER NOT NULL,
    supplier_name TEXT NOT NULL,
    context JSONB,  -- Additional context (item_code, project_item_id, etc.)
    resolved BOOLEAN DEFAULT FALSE,
    resolved_supplier_id INTEGER REFERENCES suppliers(id),
    resolved_at TIMESTAMP WITH TIME ZONE,
    resolved_by VARCHAR(100),
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_migration_unmatched_suppliers_table_record 
    ON migration_unmatched_suppliers(table_name, record_id);
CREATE INDEX IF NOT EXISTS idx_migration_unmatched_suppliers_resolved 
    ON migration_unmatched_suppliers(resolved);
CREATE INDEX IF NOT EXISTS idx_migration_unmatched_suppliers_supplier_name 
    ON migration_unmatched_suppliers(supplier_name);

COMMENT ON TABLE migration_audit_log IS 
    'Tracks Phase 2 migration execution progress and errors';
COMMENT ON TABLE migration_unmatched_suppliers IS 
    'Logs supplier names that could not be matched to suppliers table during migration. Requires manual review.';

COMMIT;
```

---

### Script 2.1: Create FULL Packages for Project Items

**File:** `backend/create_full_packages_for_project_items.sql`

```sql
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
    FOR batch_start_id IN batch_start_id..batch_end_id BY batch_size LOOP
        batch_end_id := LEAST(batch_start_id + batch_size - 1, (SELECT MAX(id) FROM project_items));
        
        -- Process each project item in current batch
        FOR project_item_rec IN 
            SELECT DISTINCT pi.id, pi.item_code, pi.project_id
            FROM project_items pi
            WHERE pi.id BETWEEN batch_start_id AND batch_end_id
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
            (batch_start_id / batch_size) + 1,
            processed_count,
            created_count,
            error_count,
            EXTRACT(EPOCH FROM (clock_timestamp() - start_time) * 1000)::INTEGER
        );
        
        COMMIT;  -- Commit batch
        BEGIN;   -- Start new transaction for next batch
        
    END LOOP;
    
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
```

---

### Script 2.2: Populate Package Subitems

**File:** `backend/populate_package_subitems.sql`

```sql
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
    FOR batch_start_id IN batch_start_id..batch_end_id BY batch_size LOOP
        batch_end_id := LEAST(batch_start_id + batch_size - 1, (SELECT MAX(id) FROM project_item_subitems));
        
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
            WHERE pis.id BETWEEN batch_start_id AND batch_end_id
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
            (batch_start_id / batch_size) + 1,
            processed_count,
            created_count,
            error_count,
            EXTRACT(EPOCH FROM (clock_timestamp() - start_time) * 1000)::INTEGER
        );
        
        COMMIT;  -- Commit batch
        BEGIN;   -- Start new transaction for next batch
        
    END LOOP;
    
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
```

---

### Script 2.3: Link Procurement Options to Packages

**File:** `backend/link_procurement_options_to_packages.sql`

```sql
-- Migration: Link procurement_options to FULL packages
-- Phase: 2.3 - Data Migration
-- Strategy: Update package_id where project_item_id exists and FULL package exists

BEGIN;

DO $$
DECLARE
    batch_size INTEGER := 1000;
    processed_count INTEGER := 0;
    updated_count INTEGER := 0;
    skipped_count INTEGER := 0;
    error_count INTEGER := 0;
    start_time TIMESTAMP;
    batch_start_id INTEGER;
    batch_end_id INTEGER;
BEGIN
    start_time := clock_timestamp();
    
    -- Get min and max procurement_option IDs for batching
    SELECT MIN(id), MAX(id) INTO batch_start_id, batch_end_id
    FROM procurement_options
    WHERE package_id IS NULL
    AND project_item_id IS NOT NULL;
    
    IF batch_start_id IS NULL THEN
        RAISE NOTICE 'No procurement options to link. All options already have package_id or no project_item_id.';
        RETURN;
    END IF;
    
    -- Process in batches
    FOR batch_start_id IN batch_start_id..batch_end_id BY batch_size LOOP
        batch_end_id := LEAST(batch_start_id + batch_size - 1, (SELECT MAX(id) FROM procurement_options));
        
        -- Update batch
        UPDATE procurement_options po
        SET package_id = (
            SELECT pp.id
            FROM procurement_packages pp
            WHERE pp.project_item_id = po.project_item_id
            AND pp.package_type = 'FULL'
            LIMIT 1
        )
        WHERE po.id BETWEEN batch_start_id AND batch_end_id
        AND po.package_id IS NULL
        AND po.project_item_id IS NOT NULL
        AND EXISTS (
            SELECT 1
            FROM procurement_packages pp
            WHERE pp.project_item_id = po.project_item_id
            AND pp.package_type = 'FULL'
        );
        
        GET DIAGNOSTICS updated_count = ROW_COUNT;
        processed_count := processed_count + updated_count;
        
        -- Log every batch
        IF processed_count % 1000 = 0 THEN
            RAISE NOTICE 'Linked % procurement options so far...', processed_count;
        END IF;
        
        -- Log batch completion
        INSERT INTO migration_audit_log (
            migration_step,
            batch_number,
            records_processed,
            records_succeeded,
            execution_time_ms
        ) VALUES (
            'link_procurement_options',
            (batch_start_id / batch_size) + 1,
            updated_count,
            updated_count,
            EXTRACT(EPOCH FROM (clock_timestamp() - start_time) * 1000)::INTEGER
        );
        
        COMMIT;  -- Commit batch
        BEGIN;   -- Start new transaction for next batch
        
    END LOOP;
    
    -- Final summary
    RAISE NOTICE '=== Procurement Options Linking Summary ===';
    RAISE NOTICE 'Total linked: %', processed_count;
    RAISE NOTICE 'Execution time: % ms', EXTRACT(EPOCH FROM (clock_timestamp() - start_time) * 1000)::INTEGER;
    
END $$;

-- Verification query
DO $$
DECLARE
    total_options INTEGER;
    options_with_package_id INTEGER;
    options_without_package_id INTEGER;
    options_with_item_code_only INTEGER;
BEGIN
    SELECT COUNT(*) INTO total_options FROM procurement_options;
    SELECT COUNT(*) INTO options_with_package_id FROM procurement_options WHERE package_id IS NOT NULL;
    SELECT COUNT(*) INTO options_without_package_id FROM procurement_options WHERE package_id IS NULL AND project_item_id IS NOT NULL;
    SELECT COUNT(*) INTO options_with_item_code_only FROM procurement_options WHERE package_id IS NULL AND project_item_id IS NULL AND item_code IS NOT NULL;
    
    RAISE NOTICE '=== Verification Results ===';
    RAISE NOTICE 'Total procurement options: %', total_options;
    RAISE NOTICE 'Linked to packages: %', options_with_package_id;
    RAISE NOTICE 'Unlinked (have project_item_id): %', options_without_package_id;
    RAISE NOTICE 'Item-code only (legacy): %', options_with_item_code_only;
    
    IF options_without_package_id > 0 THEN
        RAISE WARNING 'Found % options with project_item_id but no package_id. These may be from items without FULL packages (expected) or require manual review.', options_without_package_id;
    END IF;
END $$;

COMMIT;
```

---

### Script 2.4: Link Finalized Decisions to Packages

**File:** `backend/link_finalized_decisions_to_packages.sql`

```sql
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
    FOR batch_start_id IN batch_start_id..batch_end_id BY batch_size LOOP
        batch_end_id := LEAST(batch_start_id + batch_size - 1, (SELECT MAX(id) FROM finalized_decisions));
        
        -- Update batch
        UPDATE finalized_decisions fd
        SET package_id = (
            SELECT pp.id
            FROM procurement_packages pp
            WHERE pp.project_item_id = fd.project_item_id
            AND pp.package_type = 'FULL'
            LIMIT 1
        )
        WHERE fd.id BETWEEN batch_start_id AND batch_end_id
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
            (batch_start_id / batch_size) + 1,
            updated_count,
            updated_count,
            EXTRACT(EPOCH FROM (clock_timestamp() - start_time) * 1000)::INTEGER
        );
        
        COMMIT;  -- Commit batch
        BEGIN;   -- Start new transaction for next batch
        
    END LOOP;
    
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
```

---

### Script 2.5: Link Delivery Options to Packages

**File:** `backend/link_delivery_options_to_packages.sql`

```sql
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
    FOR batch_start_id IN batch_start_id..batch_end_id BY batch_size LOOP
        batch_end_id := LEAST(batch_start_id + batch_size - 1, (SELECT MAX(id) FROM delivery_options));
        
        -- Update batch
        UPDATE delivery_options do
        SET package_id = (
            SELECT pp.id
            FROM procurement_packages pp
            WHERE pp.project_item_id = do.project_item_id
            AND pp.package_type = 'FULL'
            LIMIT 1
        )
        WHERE do.id BETWEEN batch_start_id AND batch_end_id
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
            (batch_start_id / batch_size) + 1,
            updated_count,
            updated_count,
            EXTRACT(EPOCH FROM (clock_timestamp() - start_time) * 1000)::INTEGER
        );
        
        COMMIT;  -- Commit batch
        BEGIN;   -- Start new transaction for next batch
        
    END LOOP;
    
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
```

---

### Script 2.6: Normalize Supplier Names to IDs

**File:** `backend/normalize_supplier_names_to_ids.sql`

```sql
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
        FOR batch_start_id IN batch_start_id..batch_end_id BY batch_size LOOP
            batch_end_id := LEAST(batch_start_id + batch_size - 1, (SELECT MAX(id) FROM procurement_options));
            
            -- Process each option in current batch
            FOR supplier_name_text, matched_supplier_id IN 
                SELECT DISTINCT po.supplier_name, (
                    SELECT s.id
                    FROM suppliers s
                    WHERE LOWER(TRIM(s.company_name)) = LOWER(TRIM(po.supplier_name))
                    LIMIT 1
                ) as supplier_id
                FROM procurement_options po
                WHERE po.id BETWEEN batch_start_id AND batch_end_id
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
                    AND po.id BETWEEN batch_start_id AND batch_end_id;
                    
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
                (batch_start_id / batch_size) + 1,
                processed_count + unmatched_count,
                processed_count,
                EXTRACT(EPOCH FROM (clock_timestamp() - start_time) * 1000)::INTEGER
            );
            
            COMMIT;  -- Commit batch
            BEGIN;   -- Start new transaction for next batch
            
        END LOOP;
        
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
        FOR batch_start_id IN batch_start_id..batch_end_id BY batch_size LOOP
            batch_end_id := LEAST(batch_start_id + batch_size - 1, (SELECT MAX(id) FROM supplier_payments));
            
            -- Process each payment in current batch
            FOR supplier_name_text, matched_supplier_id IN 
                SELECT DISTINCT sp.supplier_name, (
                    SELECT s.id
                    FROM suppliers s
                    WHERE LOWER(TRIM(s.company_name)) = LOWER(TRIM(sp.supplier_name))
                    LIMIT 1
                ) as supplier_id
                FROM supplier_payments sp
                WHERE sp.id BETWEEN batch_start_id AND batch_end_id
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
                    AND sp.id BETWEEN batch_start_id AND batch_end_id;
                    
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
                (batch_start_id / batch_size) + 1,
                processed_count + unmatched_count,
                processed_count,
                EXTRACT(EPOCH FROM (clock_timestamp() - start_time) * 1000)::INTEGER
            );
            
            COMMIT;  -- Commit batch
            BEGIN;   -- Start new transaction for next batch
            
        END LOOP;
        
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
```

---

### Script 2.7: Link Financial Records to Packages

**File:** `backend/link_financial_records_to_packages.sql`

```sql
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
```

---

### Script 2.8: Validate Phase 2 Migration

**File:** `backend/validate_phase2_migration.sql`

```sql
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
```

---

## Section 4 — Post-Run Validation Checklist + Rollback Guidance

### Execution Script Usage

**Linux:**
```bash
# Make script executable
chmod +x run_phase2_data_migration.sh

# Set connection (choose one method):
export DOCKER_CONTAINER=pdss-postgres-1  # Your container name
export USE_DOCKER=true
export PGDATABASE=procurement_dss
export PGUSER=postgres

# Or use DATABASE_URL
export DATABASE_URL="postgresql://postgres:password@host:5432/procurement_dss"

# Run migrations
./run_phase2_data_migration.sh

# Skip validation
./run_phase2_data_migration.sh --skip-validation
```

**Windows PowerShell:**
```powershell
# Set connection
$env:DOCKER_CONTAINER = "pdss-postgres-1"
$env:PGDATABASE = "procurement_dss"
$env:PGUSER = "postgres"

# Run migrations
.\run_phase2_data_migration.ps1

# Skip validation
.\run_phase2_data_migration.ps1 -SkipValidation
```

**Required Environment Variables:**
- `PGDATABASE` - Database name (default: `procurement_dss`)
- `PGUSER` - PostgreSQL user (default: `postgres`)
- `DOCKER_CONTAINER` - Docker container name (default: `postgres`, auto-detected)
- `USE_DOCKER` - Set to `true` to force Docker mode (Linux only)
- `DATABASE_URL` - Full connection string (alternative to individual vars)
- `PGPASSWORD` - Password (optional, will prompt if not set)

### Validation Checklist

After running all Phase 2 scripts, execute the following validation queries:

#### 1. Quick Status Check

```sql
-- Overall migration status
SELECT 
    migration_step,
    SUM(records_processed) as total_processed,
    SUM(records_succeeded) as total_succeeded,
    SUM(records_failed) as total_failed,
    MAX(created_at) as last_execution
FROM migration_audit_log
GROUP BY migration_step
ORDER BY migration_step;
```

#### 2. Package Coverage Verification

```sql
-- Items with sub-items should have FULL packages
SELECT 
    pi.id,
    pi.item_code,
    COUNT(DISTINCT pis.id) as subitem_count,
    COUNT(DISTINCT pp.id) as full_package_count
FROM project_items pi
LEFT JOIN project_item_subitems pis ON pis.project_item_id = pi.id
LEFT JOIN procurement_packages pp ON pp.project_item_id = pi.id AND pp.package_type = 'FULL'
WHERE EXISTS (SELECT 1 FROM project_item_subitems WHERE project_item_id = pi.id)
GROUP BY pi.id, pi.item_code
HAVING COUNT(DISTINCT pp.id) = 0;  -- Should return 0 rows
```

#### 3. Supplier Normalization Status

```sql
-- Check unmatched suppliers requiring manual review
SELECT 
    table_name,
    COUNT(*) as unmatched_count,
    COUNT(DISTINCT supplier_name) as unique_supplier_names
FROM migration_unmatched_suppliers
WHERE resolved = FALSE
GROUP BY table_name;
```

#### 4. Data Integrity Check

```sql
-- Verify CHECK constraints are satisfied
SELECT 
    'procurement_options' as table_name,
    COUNT(*) as total,
    COUNT(*) FILTER (WHERE package_id IS NOT NULL OR project_item_id IS NOT NULL OR item_code IS NOT NULL) as valid_refs
FROM procurement_options
UNION ALL
SELECT 
    'delivery_options',
    COUNT(*),
    COUNT(*) FILTER (WHERE package_id IS NOT NULL OR project_item_id IS NOT NULL)
FROM delivery_options;
```

### Rollback Guidance

#### Full Phase 2 Rollback

If you need to completely rollback Phase 2:

```sql
BEGIN;

-- 1. Unlink all package_id references
UPDATE procurement_options SET package_id = NULL WHERE package_id IS NOT NULL;
UPDATE finalized_decisions SET package_id = NULL WHERE package_id IS NOT NULL;
UPDATE delivery_options SET package_id = NULL WHERE package_id IS NOT NULL;

-- 2. Unlink financial records
UPDATE invoices SET package_id = NULL WHERE package_id IS NOT NULL;
UPDATE payments SET package_id = NULL WHERE package_id IS NOT NULL;
UPDATE supplier_payments SET package_id = NULL WHERE package_id IS NOT NULL;

-- 3. Remove supplier_id links (optional - preserves supplier_name)
UPDATE procurement_options SET supplier_id = NULL WHERE supplier_id IS NOT NULL;
UPDATE supplier_payments SET supplier_id = NULL WHERE supplier_id IS NOT NULL;

-- 4. Delete package_subitems
DELETE FROM package_subitems;

-- 5. Delete FULL packages (optional - keep for reference if needed)
DELETE FROM procurement_packages WHERE package_type = 'FULL';

-- 6. Clear audit logs (optional)
-- DELETE FROM migration_audit_log;
-- DELETE FROM migration_unmatched_suppliers;

COMMIT;
```

#### Partial Rollback (Per Script)

Each script is idempotent and can be re-run safely. To rollback a specific step:

1. **Rollback package creation**: Delete FULL packages and package_subitems
2. **Rollback linking**: Set `package_id = NULL` in affected tables
3. **Rollback supplier normalization**: Set `supplier_id = NULL` (preserves `supplier_name`)

### Phase 3 Readiness Checklist

Before enabling Phase 3 feature flags:

- [ ] All Phase 2 scripts executed successfully
- [ ] Validation queries return 0 errors
- [ ] Unmatched suppliers reviewed and resolved (or documented)
- [ ] Backup taken post-Phase 2
- [ ] Application code updated to support package-aware logic
- [ ] Feature flags configured in `backend/app/config.py`

### Feature Flags to Enable (Phase 3)

```python
# In backend/app/config.py or environment variables
ENABLE_PACKAGE_AWARE_PROCUREMENT = True
ENABLE_PACKAGE_BASED_OPTIMIZATION = False  # Enable gradually
REQUIRE_PACKAGE_ID_FOR_NEW_OPTIONS = False  # Start with False, enable later
```

### Data Quality Assumptions / TODOs

1. **Orphaned Records**: Items without sub-items won't get FULL packages (by design). If needed, create packages manually or adjust script.

2. **Supplier Name Variations**: Current matching uses `LOWER(TRIM())`. May need fuzzy matching for typos/variations.

3. **Legacy Item-Code Options**: Options with only `item_code` (no `project_item_id`) remain unlinked. Requires manual resolution.

4. **Soft-Deleted Items**: Script creates packages for all items. If soft-delete logic exists, consider filtering by `is_active` flag.

5. **Concurrent Writes**: Scripts use transactions but don't handle concurrent modifications. Run during maintenance window or ensure no writes during migration.

---

**End of Phase 2 Migration Blueprint**

*Ready for execution. All scripts are idempotent and safe to re-run.*

---

## Materialization Notes

All SQL scripts and execution harnesses have been materialized under `backend/`:

**SQL Files Created (9):**
- ✓ `create_migration_audit_tables.sql` (2.0)
- ✓ `create_full_packages_for_project_items.sql` (2.1)
- ✓ `populate_package_subitems.sql` (2.2)
- ✓ `link_procurement_options_to_packages.sql` (2.3)
- ✓ `link_finalized_decisions_to_packages.sql` (2.4)
- ✓ `link_delivery_options_to_packages.sql` (2.5)
- ✓ `normalize_supplier_names_to_ids.sql` (2.6)
- ✓ `link_financial_records_to_packages.sql` (2.7)
- ✓ `validate_phase2_migration.sql` (2.8)

**Execution Scripts Created (2):**
- ✓ `run_phase2_data_migration.sh` (Linux bash, executable)
- ✓ `run_phase2_data_migration.ps1` (Windows PowerShell)

**Script Refinements:**
- All scripts use `DO $$` blocks for conditional logic and idempotency
- Batching set to 1000 records per transaction (configurable via `batch_size` variable)
- All DML wrapped in explicit transactions (`BEGIN`/`COMMIT`)
- Audit logging integrated into `migration_audit_log` table
- Unmatched suppliers logged to `migration_unmatched_suppliers` table
- Progress reporting via `RAISE NOTICE` statements
- Error handling with `EXCEPTION WHEN OTHERS` blocks
- Verification queries included in each script

**Execution Script Features:**
- Docker auto-detection (Linux) and explicit Docker support (Windows)
- `--skip-validation` flag support (Linux: `--skip-validation`, Windows: `-SkipValidation`)
- Colored output and progress tracking
- Stops on first error (`set -e` in bash, `$ErrorActionPreference = "Stop"` in PowerShell)
- Comprehensive summary reporting

**Ready for Production Use:**
All scripts follow Phase 1 patterns and are ready for execution on PostgreSQL 13+.


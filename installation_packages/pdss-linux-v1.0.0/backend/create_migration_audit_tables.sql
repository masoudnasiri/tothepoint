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


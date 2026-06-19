-- Migration: Add bunch management columns to finalized_decisions table
-- This allows phased finalization of procurement decisions
-- Run this in Docker: docker-compose exec postgres psql -U postgres -d procurement_dss -f /app/add_bunch_columns_migration.sql

-- Add bunch_id column (indexed for performance)
ALTER TABLE finalized_decisions 
ADD COLUMN IF NOT EXISTS bunch_id VARCHAR(50);

-- Add bunch_name column
ALTER TABLE finalized_decisions 
ADD COLUMN IF NOT EXISTS bunch_name VARCHAR(200);

-- Create index on bunch_id for faster queries
CREATE INDEX IF NOT EXISTS idx_finalized_decisions_bunch_id 
ON finalized_decisions(bunch_id);

-- Add comments for documentation
COMMENT ON COLUMN finalized_decisions.bunch_id IS 'Bunch identifier for phased finalization (e.g., BUNCH_1, BUNCH_2)';
COMMENT ON COLUMN finalized_decisions.bunch_name IS 'Human-readable bunch name (e.g., High Priority - Month 1)';

-- Verify columns added
\d finalized_decisions

-- Success message
SELECT 'Migration completed successfully! bunch_id and bunch_name columns added.' AS status;


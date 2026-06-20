-- Migration: Add is_finalized column to procurement_options
-- This allows procurement team to mark options as finalized for optimization

-- Add the column with default value FALSE
ALTER TABLE procurement_options
ADD COLUMN is_finalized BOOLEAN DEFAULT FALSE;

-- Update existing active options to be finalized (backward compatibility)
UPDATE procurement_options
SET is_finalized = TRUE
WHERE is_active = TRUE;

-- Add comment
COMMENT ON COLUMN procurement_options.is_finalized IS 'Whether this procurement option has been finalized by procurement team for use in optimization';

-- Verify migration
SELECT 
    'Migration completed successfully' as status,
    (SELECT COUNT(*) FROM procurement_options) as total_options,
    (SELECT COUNT(*) FROM procurement_options WHERE is_finalized = TRUE) as finalized_options,
    (SELECT COUNT(*) FROM procurement_options WHERE is_finalized = FALSE) as not_finalized_options;


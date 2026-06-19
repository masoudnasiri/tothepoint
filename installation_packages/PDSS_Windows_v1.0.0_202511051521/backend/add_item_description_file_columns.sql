-- Migration: Add description and file attachment columns to project_items
-- Date: 2025-01-10
-- Description: Adds description, file_path, and file_name columns to project_items table

-- Add description column (for item details)
ALTER TABLE project_items 
ADD COLUMN IF NOT EXISTS description TEXT;

-- Add file_path column (stores file path)
ALTER TABLE project_items 
ADD COLUMN IF NOT EXISTS file_path VARCHAR(500);

-- Add file_name column (stores original file name)
ALTER TABLE project_items 
ADD COLUMN IF NOT EXISTS file_name VARCHAR(255);

-- Add index for better query performance (optional)
CREATE INDEX IF NOT EXISTS idx_project_items_file_path 
ON project_items(file_path);

-- Verify columns were added
SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_name = 'project_items' 
AND column_name IN ('description', 'file_path', 'file_name')
ORDER BY column_name;


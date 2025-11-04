-- Migration: Add is_finalized field to project_items table
-- This allows PMO users to finalize items, making them visible in procurement

-- Add is_finalized column to project_items table
ALTER TABLE project_items 
ADD COLUMN is_finalized BOOLEAN DEFAULT FALSE NOT NULL;

-- Add finalized_by column to track who finalized the item
ALTER TABLE project_items 
ADD COLUMN finalized_by INTEGER REFERENCES users(id);

-- Add finalized_at column to track when the item was finalized
ALTER TABLE project_items 
ADD COLUMN finalized_at TIMESTAMP WITH TIME ZONE;

-- Create index for better performance when filtering finalized items
CREATE INDEX idx_project_items_is_finalized ON project_items(is_finalized);

-- Create index for finalized_by for audit purposes
CREATE INDEX idx_project_items_finalized_by ON project_items(finalized_by);

-- Update existing items to be not finalized by default
UPDATE project_items SET is_finalized = FALSE WHERE is_finalized IS NULL;

-- Add comment to the table
COMMENT ON COLUMN project_items.is_finalized IS 'Indicates if the item has been finalized by PMO and is ready for procurement';
COMMENT ON COLUMN project_items.finalized_by IS 'User ID of the PMO user who finalized this item';
COMMENT ON COLUMN project_items.finalized_at IS 'Timestamp when the item was finalized';

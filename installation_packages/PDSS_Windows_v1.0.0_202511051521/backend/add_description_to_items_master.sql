-- Add description column to items_master table

ALTER TABLE items_master 
ADD COLUMN IF NOT EXISTS description TEXT;

-- Add comment to the column
COMMENT ON COLUMN items_master.description IS 'General description of the item';


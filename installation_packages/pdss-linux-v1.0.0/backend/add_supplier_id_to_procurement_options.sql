-- Add supplier_id foreign key to procurement_options table
-- This will link procurement options to the centralized suppliers table

-- First, add the supplier_id column as nullable
ALTER TABLE procurement_options 
ADD COLUMN supplier_id INTEGER REFERENCES suppliers(id);

-- Create an index on the new foreign key
CREATE INDEX idx_procurement_options_supplier_id ON procurement_options(supplier_id);

-- Update existing procurement options to link to suppliers based on supplier_name
-- This is a best-effort mapping - some suppliers might not exist
UPDATE procurement_options 
SET supplier_id = s.id 
FROM suppliers s 
WHERE LOWER(TRIM(procurement_options.supplier_name)) = LOWER(TRIM(s.company_name));

-- For any procurement options that couldn't be matched, we'll leave supplier_id as NULL
-- Users can manually link them later through the UI

-- Add a comment to the table
COMMENT ON COLUMN procurement_options.supplier_id IS 'Foreign key to suppliers table - centralized supplier data';
COMMENT ON COLUMN procurement_options.supplier_name IS 'Legacy field - will be deprecated in favor of supplier_id relationship';

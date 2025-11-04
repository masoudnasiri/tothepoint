-- Add is_final_invoice field to finalized_decisions table
ALTER TABLE finalized_decisions 
ADD COLUMN is_final_invoice BOOLEAN NOT NULL DEFAULT FALSE;

-- Add comment to explain the field
COMMENT ON COLUMN finalized_decisions.is_final_invoice IS 'Indicates if this is the final invoice for this item. When true, no additional invoices can be created.';

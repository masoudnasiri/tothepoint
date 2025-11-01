-- Add supplier_payments table
CREATE TABLE IF NOT EXISTS supplier_payments (
    id SERIAL PRIMARY KEY,
    decision_id INTEGER NOT NULL REFERENCES finalized_decisions(id) ON DELETE CASCADE,
    supplier_name VARCHAR(200) NOT NULL,
    item_code VARCHAR(100) NOT NULL,
    project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    payment_date DATE NOT NULL,
    payment_amount NUMERIC(12, 2) NOT NULL CHECK (payment_amount > 0),
    currency VARCHAR(10) NOT NULL DEFAULT 'IRR',
    payment_method VARCHAR(50) NOT NULL CHECK (payment_method IN ('cash', 'bank_transfer', 'check', 'credit_card')),
    reference_number VARCHAR(100),
    notes TEXT,
    status VARCHAR(20) NOT NULL DEFAULT 'completed' CHECK (status IN ('pending', 'completed', 'failed', 'cancelled')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE,
    created_by_id INTEGER REFERENCES users(id)
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_supplier_payments_decision_id ON supplier_payments(decision_id);
CREATE INDEX IF NOT EXISTS idx_supplier_payments_item_code ON supplier_payments(item_code);
CREATE INDEX IF NOT EXISTS idx_supplier_payments_project_id ON supplier_payments(project_id);
CREATE INDEX IF NOT EXISTS idx_supplier_payments_payment_date ON supplier_payments(payment_date);
CREATE INDEX IF NOT EXISTS idx_supplier_payments_status ON supplier_payments(status);
CREATE INDEX IF NOT EXISTS idx_supplier_payments_supplier_name ON supplier_payments(supplier_name);

-- Add comments for documentation
COMMENT ON TABLE supplier_payments IS 'Tracks payments made to suppliers for procurement items';
COMMENT ON COLUMN supplier_payments.decision_id IS 'Reference to the finalized decision';
COMMENT ON COLUMN supplier_payments.supplier_name IS 'Name of the supplier being paid';
COMMENT ON COLUMN supplier_payments.item_code IS 'Item code for the procurement';
COMMENT ON COLUMN supplier_payments.project_id IS 'Project ID for the procurement';
COMMENT ON COLUMN supplier_payments.payment_date IS 'Date when payment was made';
COMMENT ON COLUMN supplier_payments.payment_amount IS 'Amount paid to supplier';
COMMENT ON COLUMN supplier_payments.currency IS 'Currency of the payment';
COMMENT ON COLUMN supplier_payments.payment_method IS 'Method used for payment';
COMMENT ON COLUMN supplier_payments.reference_number IS 'Reference number for the payment';
COMMENT ON COLUMN supplier_payments.notes IS 'Additional notes about the payment';
COMMENT ON COLUMN supplier_payments.status IS 'Current status of the payment';

-- Create Invoice and Payment Management Tables
-- This script creates the necessary tables for invoice and payment management

-- Create Invoice table
CREATE TABLE IF NOT EXISTS invoices (
    id SERIAL PRIMARY KEY,
    decision_id INTEGER NOT NULL REFERENCES finalized_decisions(id),
    invoice_number VARCHAR(100) UNIQUE NOT NULL,
    invoice_date TIMESTAMP WITH TIME ZONE NOT NULL,
    invoice_amount NUMERIC(15,2) NOT NULL,
    currency VARCHAR(3) NOT NULL DEFAULT 'IRR',
    due_date TIMESTAMP WITH TIME ZONE NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'draft',
    payment_terms VARCHAR(100),
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create Payment table
CREATE TABLE IF NOT EXISTS payments (
    id SERIAL PRIMARY KEY,
    invoice_id INTEGER NOT NULL REFERENCES invoices(id),
    decision_id INTEGER NOT NULL REFERENCES finalized_decisions(id),
    payment_date TIMESTAMP WITH TIME ZONE NOT NULL,
    payment_amount NUMERIC(15,2) NOT NULL,
    currency VARCHAR(3) NOT NULL DEFAULT 'IRR',
    payment_method VARCHAR(20) NOT NULL,
    reference_number VARCHAR(100),
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_invoices_decision_id ON invoices(decision_id);
CREATE INDEX IF NOT EXISTS idx_invoices_status ON invoices(status);
CREATE INDEX IF NOT EXISTS idx_invoices_invoice_date ON invoices(invoice_date);
CREATE INDEX IF NOT EXISTS idx_invoices_due_date ON invoices(due_date);

CREATE INDEX IF NOT EXISTS idx_payments_invoice_id ON payments(invoice_id);
CREATE INDEX IF NOT EXISTS idx_payments_decision_id ON payments(decision_id);
CREATE INDEX IF NOT EXISTS idx_payments_status ON payments(status);
CREATE INDEX IF NOT EXISTS idx_payments_payment_date ON payments(payment_date);

-- Add constraints
ALTER TABLE invoices ADD CONSTRAINT chk_invoice_status 
    CHECK (status IN ('draft', 'sent', 'paid', 'overdue', 'cancelled'));

ALTER TABLE payments ADD CONSTRAINT chk_payment_method 
    CHECK (payment_method IN ('cash', 'bank_transfer', 'check', 'credit_card'));

ALTER TABLE payments ADD CONSTRAINT chk_payment_status 
    CHECK (status IN ('pending', 'completed', 'failed', 'cancelled'));

-- Add triggers for updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_invoices_updated_at 
    BEFORE UPDATE ON invoices 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_payments_updated_at 
    BEFORE UPDATE ON payments 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Insert sample data (optional)
-- INSERT INTO invoices (decision_id, invoice_number, invoice_date, invoice_amount, currency, due_date, status, payment_terms)
-- VALUES 
--     (1, 'INV-2025-001', '2025-01-15', 10000.00, 'IRR', '2025-02-15', 'sent', 'Net 30'),
--     (2, 'INV-2025-002', '2025-01-16', 5000.00, 'USD', '2025-02-16', 'draft', 'Net 15');

-- INSERT INTO payments (invoice_id, decision_id, payment_date, payment_amount, currency, payment_method, reference_number, status)
-- VALUES 
--     (1, 1, '2025-02-10', 10000.00, 'IRR', 'bank_transfer', 'TXN-001', 'completed'),
--     (2, 2, '2025-02-20', 5000.00, 'USD', 'check', 'CHK-001', 'pending');

COMMIT;

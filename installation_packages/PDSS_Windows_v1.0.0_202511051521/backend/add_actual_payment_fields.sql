-- Add actual payment fields to finalized_decisions table

ALTER TABLE finalized_decisions 
ADD COLUMN IF NOT EXISTS actual_payment_amount NUMERIC(12, 2);

ALTER TABLE finalized_decisions 
ADD COLUMN IF NOT EXISTS actual_payment_date DATE;

ALTER TABLE finalized_decisions 
ADD COLUMN IF NOT EXISTS actual_payment_installments JSON;

ALTER TABLE finalized_decisions 
ADD COLUMN IF NOT EXISTS payment_entered_by_id INTEGER REFERENCES users(id);

ALTER TABLE finalized_decisions 
ADD COLUMN IF NOT EXISTS payment_entered_at TIMESTAMP WITH TIME ZONE;

-- Add comments
COMMENT ON COLUMN finalized_decisions.actual_payment_amount IS 'Total amount actually paid to supplier';
COMMENT ON COLUMN finalized_decisions.actual_payment_date IS 'Date of first/single payment to supplier';
COMMENT ON COLUMN finalized_decisions.actual_payment_installments IS 'Array of installment payments: [{"date": "2026-01-15", "amount": 10000}, ...]';
COMMENT ON COLUMN finalized_decisions.payment_entered_by_id IS 'User who entered the payment data';
COMMENT ON COLUMN finalized_decisions.payment_entered_at IS 'When payment data was entered';


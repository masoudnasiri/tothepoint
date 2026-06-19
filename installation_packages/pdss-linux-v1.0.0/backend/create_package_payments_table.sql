-- Migration: Create package_payments table
-- Phase: 1.3 - Additive Changes
-- Strategy: Online (no downtime)
-- Dependencies: Requires procurement_packages table (1.1) and finalized_decisions table
--
-- This table tracks payments at package level (more granular than supplier_payments).
-- Supports package-level payment tracking for split procurement scenarios.

BEGIN;

CREATE TABLE IF NOT EXISTS package_payments (
    id SERIAL PRIMARY KEY,
    decision_id INTEGER NOT NULL REFERENCES finalized_decisions(id) ON DELETE CASCADE,
    package_id INTEGER NOT NULL REFERENCES procurement_packages(id) ON DELETE CASCADE,
    supplier_id INTEGER NOT NULL REFERENCES suppliers(id) ON DELETE RESTRICT,
    payment_amount NUMERIC(12,2) NOT NULL CHECK (payment_amount > 0),
    currency VARCHAR(10) NOT NULL DEFAULT 'IRR',
    payment_date DATE NOT NULL,
    payment_method VARCHAR(50) NOT NULL CHECK (payment_method IN ('cash', 'bank_transfer', 'check', 'credit_card')),
    reference_number TEXT,
    status VARCHAR(20) NOT NULL DEFAULT 'completed' CHECK (status IN ('pending', 'completed', 'failed', 'cancelled')),
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE,
    created_by_id INTEGER REFERENCES users(id) ON DELETE SET NULL
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_package_payments_decision_id 
    ON package_payments(decision_id);
CREATE INDEX IF NOT EXISTS idx_package_payments_package_id 
    ON package_payments(package_id);
CREATE INDEX IF NOT EXISTS idx_package_payments_supplier_id 
    ON package_payments(supplier_id);
CREATE INDEX IF NOT EXISTS idx_package_payments_payment_date 
    ON package_payments(payment_date);
CREATE INDEX IF NOT EXISTS idx_package_payments_status 
    ON package_payments(status);

-- Comments for documentation
COMMENT ON TABLE package_payments IS 'Payment tracking at package level. Enables granular payment tracking for split procurement scenarios where different packages are sourced from different suppliers.';
COMMENT ON COLUMN package_payments.decision_id IS 'Foreign key to finalized_decisions - the procurement decision this payment is for';
COMMENT ON COLUMN package_payments.package_id IS 'Foreign key to procurement_packages - the specific package this payment covers';
COMMENT ON COLUMN package_payments.supplier_id IS 'Foreign key to suppliers - the supplier being paid (required, NOT NULL)';
COMMENT ON COLUMN package_payments.payment_amount IS 'Amount paid to supplier (must be > 0)';
COMMENT ON COLUMN package_payments.status IS 'Payment status: pending, completed, failed, or cancelled';

COMMIT;


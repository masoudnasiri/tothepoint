-- Migration: Add Delivery Tracking fields to finalized_decisions table
-- Date: 2025-10-10
-- Purpose: Support Procurement Plan & Delivery Tracking feature

-- Add delivery tracking fields
ALTER TABLE finalized_decisions
ADD COLUMN IF NOT EXISTS delivery_status VARCHAR(50) NOT NULL DEFAULT 'AWAITING_DELIVERY',
ADD COLUMN IF NOT EXISTS actual_delivery_date DATE,
ADD COLUMN IF NOT EXISTS procurement_confirmed_at TIMESTAMP WITH TIME ZONE,
ADD COLUMN IF NOT EXISTS procurement_confirmed_by_id INTEGER REFERENCES users(id),
ADD COLUMN IF NOT EXISTS is_correct_item_confirmed BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS serial_number VARCHAR(200),
ADD COLUMN IF NOT EXISTS procurement_delivery_notes TEXT,
ADD COLUMN IF NOT EXISTS pm_accepted_at TIMESTAMP WITH TIME ZONE,
ADD COLUMN IF NOT EXISTS pm_accepted_by_id INTEGER REFERENCES users(id),
ADD COLUMN IF NOT EXISTS is_accepted_by_pm BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS pm_acceptance_notes TEXT,
ADD COLUMN IF NOT EXISTS customer_delivery_date DATE;

-- Create index on delivery_status for faster filtering
CREATE INDEX IF NOT EXISTS idx_finalized_decisions_delivery_status ON finalized_decisions(delivery_status);

-- Update existing records to have default delivery status
UPDATE finalized_decisions 
SET delivery_status = 'AWAITING_DELIVERY' 
WHERE delivery_status IS NULL;

COMMIT;


-- Sprint 3A-R3
-- Add component-level payment metadata storage for procurement cost components.

ALTER TABLE procurement_cost_components
ADD COLUMN IF NOT EXISTS payment_metadata JSON;


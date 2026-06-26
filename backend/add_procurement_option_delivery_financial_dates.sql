-- Sprint 2C additive migration:
-- Procurement option delivery source + customer invoice/receipt forecast defaults.
-- Safe for repeated execution on PostgreSQL.

ALTER TABLE procurement_options
    ADD COLUMN IF NOT EXISTS project_requested_delivery_date DATE NULL,
    ADD COLUMN IF NOT EXISTS supplier_actual_delivery_date DATE NULL,
    ADD COLUMN IF NOT EXISTS selected_delivery_date DATE NULL,
    ADD COLUMN IF NOT EXISTS delivery_date_source VARCHAR(20) NULL,
    ADD COLUMN IF NOT EXISTS delivery_date_variance_days INTEGER NULL,
    ADD COLUMN IF NOT EXISTS forecast_customer_invoice_date DATE NULL,
    ADD COLUMN IF NOT EXISTS forecast_customer_invoice_date_source VARCHAR(20) NULL,
    ADD COLUMN IF NOT EXISTS forecast_customer_receipt_date DATE NULL,
    ADD COLUMN IF NOT EXISTS forecast_customer_receipt_date_source VARCHAR(20) NULL,
    ADD COLUMN IF NOT EXISTS forecast_customer_receipt_delay_days INTEGER NULL,
    ADD COLUMN IF NOT EXISTS date_calculation_trace JSON NULL;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'check_procurement_option_delivery_date_source'
    ) THEN
        ALTER TABLE procurement_options
            ADD CONSTRAINT check_procurement_option_delivery_date_source
            CHECK (
                delivery_date_source IS NULL
                OR delivery_date_source IN ('PROJECT_OPTION', 'SUPPLIER_ACTUAL', 'MANUAL')
            );
    END IF;
END $$;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'check_procurement_option_invoice_date_source'
    ) THEN
        ALTER TABLE procurement_options
            ADD CONSTRAINT check_procurement_option_invoice_date_source
            CHECK (
                forecast_customer_invoice_date_source IS NULL
                OR forecast_customer_invoice_date_source IN ('SYSTEM_DEFAULT', 'MANUAL_OVERRIDE')
            );
    END IF;
END $$;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'check_procurement_option_receipt_date_source'
    ) THEN
        ALTER TABLE procurement_options
            ADD CONSTRAINT check_procurement_option_receipt_date_source
            CHECK (
                forecast_customer_receipt_date_source IS NULL
                OR forecast_customer_receipt_date_source IN ('SYSTEM_DEFAULT', 'MANUAL_OVERRIDE')
            );
    END IF;
END $$;


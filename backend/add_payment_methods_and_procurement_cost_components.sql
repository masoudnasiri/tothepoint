-- Sprint 2A additive migration:
-- Payment methods master data + procurement option cost components
-- Safe for repeated execution on PostgreSQL.

CREATE TABLE IF NOT EXISTS payment_methods (
    id SERIAL PRIMARY KEY,
    code VARCHAR(50) NOT NULL UNIQUE,
    name_en VARCHAR(200) NOT NULL,
    name_fa VARCHAR(200) NOT NULL,
    description TEXT NULL,
    settlement_delay_days INTEGER NOT NULL DEFAULT 0,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NULL,
    CONSTRAINT check_payment_method_settlement_delay_non_negative
        CHECK (settlement_delay_days >= 0)
);

CREATE INDEX IF NOT EXISTS idx_payment_methods_code ON payment_methods (code);
CREATE INDEX IF NOT EXISTS idx_payment_methods_is_active ON payment_methods (is_active);

CREATE TABLE IF NOT EXISTS procurement_cost_components (
    id SERIAL PRIMARY KEY,
    procurement_option_id INTEGER NOT NULL REFERENCES procurement_options(id) ON DELETE CASCADE,
    component_type VARCHAR(30) NOT NULL,
    description TEXT NULL,
    amount_value NUMERIC(18, 2) NOT NULL,
    amount_currency VARCHAR(3) NOT NULL,
    amount_irr NUMERIC(18, 2) NULL,
    exchange_rate_date DATE NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NULL,
    CONSTRAINT check_procurement_cost_component_positive_amount
        CHECK (amount_value > 0),
    CONSTRAINT check_procurement_cost_component_type
        CHECK (
            component_type IN (
                'BASE_PRICE',
                'SHIPPING',
                'VAT',
                'CUSTOMS',
                'CLEARANCE',
                'INSURANCE',
                'BANK_FEE',
                'OTHER'
            )
        )
);

CREATE INDEX IF NOT EXISTS idx_procurement_cost_components_option_id
    ON procurement_cost_components (procurement_option_id);
CREATE INDEX IF NOT EXISTS idx_procurement_cost_components_component_type
    ON procurement_cost_components (component_type);
CREATE INDEX IF NOT EXISTS idx_procurement_cost_components_is_active
    ON procurement_cost_components (is_active);

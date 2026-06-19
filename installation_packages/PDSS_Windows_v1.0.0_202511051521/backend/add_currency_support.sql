-- Add Currency and Exchange Rate support
-- This migration adds multi-currency support with Iranian Rials as base currency

-- Create currencies table
CREATE TABLE IF NOT EXISTS currencies (
    id SERIAL PRIMARY KEY,
    code VARCHAR(3) UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    symbol VARCHAR(10) NOT NULL,
    is_base_currency BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    decimal_places INTEGER DEFAULT 2,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE,
    created_by_id INTEGER REFERENCES users(id)
);

-- Create exchange_rates table
CREATE TABLE IF NOT EXISTS exchange_rates (
    id SERIAL PRIMARY KEY,
    currency_id INTEGER NOT NULL REFERENCES currencies(id),
    rate_date DATE NOT NULL,
    rate_to_base NUMERIC(15,6) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE,
    created_by_id INTEGER REFERENCES users(id)
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_currencies_code ON currencies(code);
CREATE INDEX IF NOT EXISTS idx_currencies_is_base ON currencies(is_base_currency);
CREATE INDEX IF NOT EXISTS idx_currencies_is_active ON currencies(is_active);
CREATE INDEX IF NOT EXISTS idx_exchange_rates_currency_id ON exchange_rates(currency_id);
CREATE INDEX IF NOT EXISTS idx_exchange_rates_rate_date ON exchange_rates(rate_date);
CREATE INDEX IF NOT EXISTS idx_exchange_rates_is_active ON exchange_rates(is_active);

-- Add currency_id to procurement_options table
ALTER TABLE procurement_options ADD COLUMN IF NOT EXISTS currency_id INTEGER REFERENCES currencies(id);

-- Add currency_id to finalized_decisions table
ALTER TABLE finalized_decisions ADD COLUMN IF NOT EXISTS currency_id INTEGER REFERENCES currencies(id);

-- Insert default currencies
INSERT INTO currencies (code, name, symbol, is_base_currency, is_active, decimal_places) VALUES
('IRR', 'Iranian Rial', '﷼', TRUE, TRUE, 0),
('USD', 'US Dollar', '$', FALSE, TRUE, 2),
('EUR', 'Euro', '€', FALSE, TRUE, 2),
('GBP', 'British Pound', '£', FALSE, TRUE, 2),
('JPY', 'Japanese Yen', '¥', FALSE, TRUE, 0),
('CNY', 'Chinese Yuan', '¥', FALSE, TRUE, 2),
('AED', 'UAE Dirham', 'د.إ', FALSE, TRUE, 2),
('SAR', 'Saudi Riyal', 'ر.س', FALSE, TRUE, 2),
('TRY', 'Turkish Lira', '₺', FALSE, TRUE, 2),
('INR', 'Indian Rupee', '₹', FALSE, TRUE, 2)
ON CONFLICT (code) DO NOTHING;

-- Insert sample exchange rates (example rates - should be updated with real rates)
INSERT INTO exchange_rates (currency_id, rate_date, rate_to_base, is_active) VALUES
-- USD to IRR (example: 1 USD = 420,000 IRR)
((SELECT id FROM currencies WHERE code = 'USD'), CURRENT_DATE, 420000.000000, TRUE),
-- EUR to IRR (example: 1 EUR = 450,000 IRR)
((SELECT id FROM currencies WHERE code = 'EUR'), CURRENT_DATE, 450000.000000, TRUE),
-- GBP to IRR (example: 1 GBP = 520,000 IRR)
((SELECT id FROM currencies WHERE code = 'GBP'), CURRENT_DATE, 520000.000000, TRUE),
-- JPY to IRR (example: 1 JPY = 2,800 IRR)
((SELECT id FROM currencies WHERE code = 'JPY'), CURRENT_DATE, 2800.000000, TRUE),
-- CNY to IRR (example: 1 CNY = 58,000 IRR)
((SELECT id FROM currencies WHERE code = 'CNY'), CURRENT_DATE, 58000.000000, TRUE),
-- AED to IRR (example: 1 AED = 114,000 IRR)
((SELECT id FROM currencies WHERE code = 'AED'), CURRENT_DATE, 114000.000000, TRUE),
-- SAR to IRR (example: 1 SAR = 112,000 IRR)
((SELECT id FROM currencies WHERE code = 'SAR'), CURRENT_DATE, 112000.000000, TRUE),
-- TRY to IRR (example: 1 TRY = 14,000 IRR)
((SELECT id FROM currencies WHERE code = 'TRY'), CURRENT_DATE, 14000.000000, TRUE),
-- INR to IRR (example: 1 INR = 5,000 IRR)
((SELECT id FROM currencies WHERE code = 'INR'), CURRENT_DATE, 5000.000000, TRUE)
ON CONFLICT DO NOTHING;

-- Update existing procurement_options to use IRR as default currency
UPDATE procurement_options 
SET currency_id = (SELECT id FROM currencies WHERE code = 'IRR' AND is_base_currency = TRUE)
WHERE currency_id IS NULL;

-- Update existing finalized_decisions to use IRR as default currency
UPDATE finalized_decisions 
SET currency_id = (SELECT id FROM currencies WHERE code = 'IRR' AND is_base_currency = TRUE)
WHERE currency_id IS NULL;

-- Make currency_id NOT NULL after setting defaults
ALTER TABLE procurement_options ALTER COLUMN currency_id SET NOT NULL;
ALTER TABLE finalized_decisions ALTER COLUMN currency_id SET NOT NULL;

-- Add comments
COMMENT ON TABLE currencies IS 'Master table for supported currencies';
COMMENT ON TABLE exchange_rates IS 'Exchange rates for currencies to base currency (IRR)';
COMMENT ON COLUMN currencies.is_base_currency IS 'Only one currency should be marked as base currency';
COMMENT ON COLUMN exchange_rates.rate_to_base IS 'Rate to convert to base currency (IRR)';
COMMENT ON COLUMN currencies.decimal_places IS 'Number of decimal places for display formatting';

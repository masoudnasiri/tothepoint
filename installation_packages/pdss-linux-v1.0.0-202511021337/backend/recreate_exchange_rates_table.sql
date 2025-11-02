-- Drop and recreate exchange_rates table with new structure

BEGIN;

-- Drop the old exchange_rates table
DROP TABLE IF EXISTS exchange_rates CASCADE;

-- Create new exchange_rates table with proper structure
CREATE TABLE exchange_rates (
    id SERIAL PRIMARY KEY,
    date DATE NOT NULL,
    from_currency VARCHAR(3) NOT NULL,
    to_currency VARCHAR(3) NOT NULL,
    rate NUMERIC(15, 6) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE,
    created_by_id INTEGER REFERENCES users(id)
);

-- Create indexes for efficient lookups
CREATE INDEX idx_exchange_rates_date ON exchange_rates(date);
CREATE INDEX idx_exchange_rates_from_currency ON exchange_rates(from_currency);
CREATE INDEX idx_exchange_rates_to_currency ON exchange_rates(to_currency);
CREATE INDEX idx_exchange_rates_from_to_date ON exchange_rates(from_currency, to_currency, date);
CREATE INDEX idx_exchange_rates_active ON exchange_rates(is_active);

-- Insert sample exchange rates for testing
-- USD to IRR rates
INSERT INTO exchange_rates (date, from_currency, to_currency, rate, is_active, created_by_id) VALUES
('2025-10-11', 'USD', 'IRR', 47600.00, TRUE, 297),  -- Using admin user id
('2025-10-10', 'USD', 'IRR', 47500.00, TRUE, 297),
('2025-10-09', 'USD', 'IRR', 47400.00, TRUE, 297),
('2025-10-08', 'USD', 'IRR', 47300.00, TRUE, 297),
('2025-10-07', 'USD', 'IRR', 47200.00, TRUE, 297);

-- EUR to IRR rates
INSERT INTO exchange_rates (date, from_currency, to_currency, rate, is_active, created_by_id) VALUES
('2025-10-11', 'EUR', 'IRR', 56600.00, TRUE, 297),
('2025-10-10', 'EUR', 'IRR', 56500.00, TRUE, 297),
('2025-10-09', 'EUR', 'IRR', 56400.00, TRUE, 297);

-- AED to IRR rates
INSERT INTO exchange_rates (date, from_currency, to_currency, rate, is_active, created_by_id) VALUES
('2025-10-11', 'AED', 'IRR', 13550.00, TRUE, 297),
('2025-10-10', 'AED', 'IRR', 13500.00, TRUE, 297);

-- GBP to IRR rates
INSERT INTO exchange_rates (date, from_currency, to_currency, rate, is_active, created_by_id) VALUES
('2025-10-11', 'GBP', 'IRR', 64000.00, TRUE, 297);

COMMIT;

-- Verify the new structure
\d exchange_rates

-- Show sample data
SELECT * FROM exchange_rates ORDER BY date DESC, from_currency LIMIT 10;

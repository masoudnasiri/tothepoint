-- Add multi-currency support to budget_data table

-- Add the multi_currency_budget column
ALTER TABLE budget_data ADD COLUMN IF NOT EXISTS multi_currency_budget JSONB;

-- Add comment
COMMENT ON COLUMN budget_data.multi_currency_budget IS 'Multi-currency budget allocation as JSON: {"USD": 1000000, "IRR": 1000000000000, "AED": 12000000000}';

-- Update existing records to have multi_currency_budget with IRR
UPDATE budget_data 
SET multi_currency_budget = jsonb_build_object('IRR', available_budget)
WHERE multi_currency_budget IS NULL;

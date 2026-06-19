# Dual Cash Flow System Implementation

## Overview
Implemented a comprehensive dual cash flow tracking system that separates **Forecasted** cash flow (based on planning) from **Actual** cash flow (based on real data from finance team).

## Key Features

### 1. Forecasted Cash Flow
- **Source**: Delivery Options configured during project planning phase
- **Purpose**: Financial forecasting and planning
- **Data**: Predicted invoice timing, amounts, and dates
- **When Created**: Automatically when decisions are finalized (LOCKED)

### 2. Actual Cash Flow  
- **Source**: Real invoice data entered by finance team
- **Purpose**: Track actual financial performance
- **Data**: Real invoice issue dates, amounts, and payment received dates
- **When Created**: When finance team enters actual invoice data

## Database Schema Changes

### FinalizedDecision Model
**New Fields for Forecasted Invoice:**
- `delivery_option_id` - Links to the DeliveryOption used for forecasting
- `forecast_invoice_timing_type` - 'ABSOLUTE' or 'RELATIVE'
- `forecast_invoice_issue_date` - Predicted invoice date (for ABSOLUTE)
- `forecast_invoice_days_after_delivery` - Days after delivery (for RELATIVE)
- `forecast_invoice_amount` - Expected invoice amount

**New Fields for Actual Invoice:**
- `actual_invoice_issue_date` - Real invoice issue date
- `actual_invoice_amount` - Real invoice amount
- `actual_invoice_received_date` - When payment was actually received
- `invoice_entered_by_id` - Finance user who entered the data
- `invoice_entered_at` - Timestamp when data was entered

### CashflowEvent Model
**New Field:**
- `forecast_type` - Values: 'FORECAST' or 'ACTUAL'
  - `FORECAST`: Events based on predicted data
  - `ACTUAL`: Events based on real data from finance

## API Endpoints

### 1. POST `/decisions/batch`
- **Purpose**: Save optimization results as finalized decisions
- **Enhancement**: Now automatically populates forecast invoice fields from DeliveryOption
- **Access**: PM, Admin

### 2. POST `/decisions/finalize`
- **Purpose**: Lock decisions and create FORECAST cashflow events
- **Enhancement**: Creates events marked as 'FORECAST' type
- **Events Created**:
  - OUTFLOW events (based on payment terms)
  - INFLOW events (based on forecast invoice timing)
- **Access**: PM, Admin

### 3. POST `/decisions/{decision_id}/actual-invoice` (NEW)
- **Purpose**: Finance team enters actual invoice data
- **Request Body**:
  ```json
  {
    "actual_invoice_issue_date": "2025-10-15",
    "actual_invoice_amount": 12500.00,
    "actual_invoice_received_date": "2025-10-20",
    "notes": "Invoice #INV-2025-001"
  }
  ```
- **Creates**: ACTUAL INFLOW cashflow event
- **Access**: Finance, Admin

## Workflow

### Phase 1: Planning (PM)
1. PM creates project items
2. PM configures Delivery Options with:
   - Delivery dates
   - Invoice timing (ABSOLUTE or RELATIVE)
   - Expected invoice amounts per unit

### Phase 2: Optimization (Finance/PM)
1. Run optimization
2. Review and edit optimization results
3. Save plan as finalized decisions
   - System automatically loads forecast data from DeliveryOptions

### Phase 3: Finalization (PM)
1. Lock finalized decisions
2. System creates FORECAST cashflow events:
   - OUTFLOW: Based on procurement payment terms
   - INFLOW: Based on forecast invoice timing from DeliveryOptions

### Phase 4: Actual Data Entry (Finance)
1. Finance team enters real invoice data when invoices are issued
2. System creates ACTUAL cashflow events:
   - INFLOW: Based on actual invoice received date and amount

### Phase 5: Analysis (All)
1. View Forecasted Cash Flow dashboard (predicted)
2. View Actual Cash Flow dashboard (real data)
3. Compare forecast vs actual for variance analysis

## Dashboard Views

### Forecasted Cash Flow Dashboard
- Shows predicted cash flow based on DeliveryOptions
- Helps with financial planning
- Filter: `forecast_type = 'FORECAST'`
- Available immediately after decisions are locked

### Actual Cash Flow Dashboard
- Shows real cash flow based on finance team data
- Tracks actual financial performance
- Filter: `forecast_type = 'ACTUAL'`
- Populated as finance enters actual invoice data

### Variance Analysis (Future Enhancement)
- Compare forecast vs actual
- Show differences in timing and amounts
- Help improve future forecasting accuracy

## Benefits

1. **Better Planning**: Forecast cash flow during project planning phase
2. **Accurate Tracking**: Record actual financial data separately
3. **Performance Analysis**: Compare forecasts vs actuals
4. **Audit Trail**: Complete history of both predicted and actual data
5. **Role Separation**: PM handles forecasts, Finance handles actuals
6. **Improved Forecasting**: Learn from variances to improve future predictions

## Next Steps (Frontend Implementation)

1. ✅ Update database models
2. ✅ Update Pydantic schemas
3. ✅ Update finalize endpoint for FORECAST events
4. ✅ Create actual invoice data entry endpoint
5. ⏳ Update dashboard to show FORECAST vs ACTUAL views
6. ⏳ Create UI for finance to enter actual invoice data
7. ⏳ Add variance analysis view

## Technical Notes

- All FORECAST events are created automatically when decisions are locked
- ACTUAL events are created only when finance enters real data
- Both types of events are stored in the same `cashflow_events` table
- The `forecast_type` field distinguishes between them
- Cancelled events (`is_cancelled=True`) are excluded from both views
- DeliveryOptions provide the source data for forecasts
- Finance team has exclusive access to enter actual invoice data

# Phase 12B Cashflow Semantics Audit

## Scope

Audit target:

- `backend/app/routers/dashboard.py`
- `backend/app/routers/reports.py`
- `backend/app/routers/analytics.py`
- `backend/app/routers/finance.py`
- `backend/app/cashflow_sync_service.py`
- `backend/app/models.py`
- `backend/app/models_invoice_payment.py`
- `backend/app/routers/invoice_payment_simple.py`
- `backend/app/routers/supplier_payments.py`
- `backend/app/routers/procurement_plan.py`
- `frontend/src/pages/DashboardPage.tsx`
- `frontend/src/pages/ReportsPage.tsx`
- `frontend/src/pages/AnalyticsDashboardPage.tsx`
- `frontend/src/pages/FinancePage.tsx`

## Endpoint and Source Map

### `GET /dashboard/cashflow`

- Source models/tables: `cashflow_events`, `finalized_decisions`, `budget_data`, `exchange_rates`
- Domain buckets:
  - Budget: `budget_data`
  - Forecast/Actual: `cashflow_events` with `forecast_type`
- Previous lifecycle filter issue:
  - `FORECAST` rows were not restricted to `finalized_decisions.status = LOCKED`
  - Candidate/pre-decision forecast rows could leak into dashboard
- Previous currency issue:
  - Unified conversion fallback silently used original amount when rate lookup failed
- Fix applied:
  - Enforced lifecycle scope: forecast only from locked decisions
  - Kept budget separate from inflow totals
  - Added conversion warnings and excluded unconvertible rows from unified totals

### `GET /dashboard/summary`

- Source models/tables: `cashflow_events`, `finalized_decisions`, `budget_data`
- Previous semantic issue:
  - Summary mixed budget into net position and did not enforce committed forecast scope
- Fix applied:
  - Added lifecycle scope condition (ACTUAL + LOCKED FORECAST)
  - `net_position` now reflects inflow-outflow; `net_with_budget` exposed separately

### `GET /dashboard/cashflow/export`

- Source models/tables: `cashflow_events`, `finalized_decisions`
- Previous issue:
  - Export could include pre-decision forecast rows
- Fix applied:
  - Same lifecycle scope as dashboard views

### `GET /analytics/cashflow-forecast/{project_id}`
### `GET /analytics/portfolio/cashflow-forecast`

- Source models/tables: `cashflow_events`, `finalized_decisions`, `projects`, `exchange_rates`
- Previous lifecycle issue:
  - Forecast rows were not restricted to locked decisions
- Previous currency issue:
  - Unified mode did not convert consistently from original currency
- Fix applied:
  - Added lifecycle scope (ACTUAL + LOCKED FORECAST)
  - Added unified IRR conversion and conversion warnings

### `GET /reports/`

- Source models/tables: `finalized_decisions`, `cashflow_events`, `budget_data`, `exchange_rates`
- Previous semantic issue:
  - Financial summary cash flow did not include monthly budget line
  - Currency conversion was incomplete for unified reporting aggregates
  - ACTUAL event aggregation was not explicitly bound to locked decisions
- Fix applied:
  - Added budget series in financial summary cash flow
  - Added unified conversion to IRR for events/planned cost
  - Added conversion warning reporting
  - Bound ACTUAL cashflow aggregation to locked decisions

### `GET /finance/dashboard`

- Source: `app.crud.get_dashboard_stats()`
- Status:
  - Uses project-level budget field and high-level counts
  - Not used as core cashflow semantics endpoint for forecast/actual split
  - No Phase 12B logic change applied here

## Operational Event Creation Map (Actuals)

- `backend/app/routers/invoice_payment_simple.py`
  - Creates `ACTUAL INFLOW` cashflow on payment-in
- `backend/app/routers/supplier_payments.py`
  - Creates `ACTUAL OUTFLOW` cashflow via sync service
- `backend/app/cashflow_sync_service.py`
  - Syncs payment/invoice records into `cashflow_events` with `forecast_type = ACTUAL`
- `backend/app/routers/procurement_plan.py`
  - On invoice entry, writes ACTUAL inflow

These are the operational sources treated as actual cashflow records.

## Suspected Incorrect Inclusions Found

- Pre-decision candidate forecast values (`status=PROPOSED`) in dashboard/analytics/export.
- Budget being interpreted as inflow in summary totals and comparison metrics.
- Silent inclusion risk for foreign amounts with missing exchange rate in unified mode.
- Reports financial summary missing explicit budget capacity series.

## Correction Plan Executed

1. Enforce lifecycle filter for forecast visibility:
   - only `LOCKED`-bound forecast rows included.
2. Keep budget separate from inflow:
   - budget remains visible as capacity, not revenue inflow.
3. Protect unified currency totals:
   - if conversion rate missing, emit warning and skip value from unified sum.
4. Align frontend display mapping:
   - dashboard cards and comparison mapping updated to avoid budget-as-revenue.
5. Add focused regression tests:
   - `backend/tests/test_phase12b_cashflow_semantics.py`.

## Reproduction Notes

- Prior UAT symptom (reported): project/dashboard financial mismatch and pre-decision leakage concern.
- Server-first replay executed against `http://193.162.129.58:18010` using current UAT data (no reset).
- Runtime state before fix:
  - `budget_data`: 9 rows
  - `project_items`: 500 rows
  - `procurement_options` (active): 327 rows
  - `finalized_decisions`: 0 rows
  - `cashflow_events` active: 0 rows
- Bug reproduced before fix:
  - `GET /dashboard/cashflow?forecast_type=FORECAST` returned non-zero `summary.total_inflow` and non-zero `net_flow` despite no forecast/actual events.
  - Root cause was budget mixed into inflow/net computations in dashboard aggregation.
- Post-fix server verification:
  - `summary.total_inflow = 0`, `summary.total_outflow = 0`
  - `summary.total_budget > 0` (as capacity only)
  - monthly `net_flow = 0` while `capacity_flow` carries budget effect
  - `ACTUAL` remains zero when no actual events exist
  - reports and analytics cashflow endpoints remain zero for forecast/actual streams with budget separated.

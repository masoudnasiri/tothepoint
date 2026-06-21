# Phase 12E-4 — Optimization Financial Traceability Audit

## Scope

This audit focuses only on financial traceability and number reconciliation between:

- pre-run budget analysis
- optimization result totals
- selected-result financial analysis
- Budget Analysis `selected_result` scenario
- currency cards / period rows / narrative totals

## Root Cause Summary

1. **Selected-result path used non-canonical arithmetic**
   - `analyze_optimization_run_financial` previously rebuilt totals from procurement option base fields and did not reliably carry selected-result execution totals through a trace model.
   - Quantity/final-cost semantics were inconsistent between optimizer outputs and financial analysis.

2. **Mixed semantics in UI labels**
   - UI presented `Total Cost` and `Weighted Cost` without explicit semantic distinction.
   - Weighted objective values could be interpreted as procurement cash requirement.

3. **Run binding gap in Budget Analysis tab**
   - Budget tab selected-result analysis could resolve without explicit `run_id`, causing mismatch with the active run context in optimization view.

4. **Budget shortage modal localization gap**
   - Pre-run shortage decision dialog labels were hardcoded in English.

## Canonical Financial Semantics (Phase 12E-4)

- `total_purchase_cost_irr`:
  - Sum of selected decision payment allocations converted to IRR.
  - Used as canonical procurement/cash requirement reference.
- `weighted_objective_cost_irr`:
  - Objective-weighted solver metric (not a cash budget amount).
  - Exposed separately.
- `budget_required_irr`:
  - Required execution budget in IRR for selected decisions.
  - Reconciled against trace lines and period totals.
- `budget_required_by_currency`:
  - Grouped original-currency payment amounts from selected trace lines.
  - Not an IRR-labeled field.

## Canonical Trace Model

`OptimizationFinancialAnalysis` now includes:

- `trace_lines`: selected-result financial line trace (item/candidate/currency/rate/period allocation/inclusion flags)
- `reconciliation`: aggregate reconciliation object
- `total_purchase_cost_irr`
- `weighted_objective_cost_irr`

Reconciliation checks:

- trace sum vs required budget
- period sum vs required budget
- optimizer total vs required budget
- warning capture in `differences`

## Payment Schedule and Period Allocation

For selected/proposal analysis:

- if installment schedule exists, amount is split by schedule percentages
- each split is assigned to its due-date period
- each split is converted to IRR once
- period totals are computed from split amounts only (no duplicate full-amount allocation)

Fallback without schedule:

- full amount allocated to purchase-date period

## Currency Conversion/Scaling Fixes

- Conversion is performed from original currency to IRR using date-valid rate.
- Trace carries original amount and IRR amount separately.
- Currency cards are grouped from original amounts; IRR equivalent stays in IRR fields.
- Exchange rate is explicit in trace lines.

## UI and Localization Fixes

- Budget Analysis selected-result now passes active `run_id`.
- Optimization cards now distinguish:
  - `Total Purchase Cost (IRR)`
  - `Weighted Objective Cost (IRR)`
- Financial reconciliation warning is shown when differences exist.
- Budget shortage decision modal is localized using i18n keys.
- Persian required labels added:
  - `کسری بودجه شناسایی شد`
  - `کسری بودجه باید به‌عنوان هشدار و نقطه تصمیم‌گیری نمایش داده شود. روش ادامه را انتخاب کنید.`
  - `سناریو`
  - `وضعیت بودجه`
  - `بودجه مورد نیاز`
  - `بودجه موجود`
  - `کسری بودجه`
  - `ادامه با بودجه موجود`
  - `بهینه‌سازی همه اقلام با نمایش تحلیل کسری بودجه`
  - `لغو و بازگشت به مدیریت بودجه`

## Before/After Reconciliation Example (Conceptual)

- Before:
  - selected-result panel and budget tab could show divergent required budget totals for the same run context.
- After:
  - both selected-result views consume the same run-scoped canonical analysis payload and expose trace/reconciliation totals from one computation path.

## Test Coverage Added

`backend/tests/test_phase12e4_financial_traceability_reconciliation.py`

- A: selected result views match and exclude unselected candidate
- B: weighted objective cost separated from purchase cost
- C: USD conversion labeled and converted once
- D: period allocation uses schedule split without duplication
- E: minimum feasible uses one chosen candidate trace
- F: Persian localization labels exist in i18n payload

## Verification Notes

- Frontend build: successful (warnings are pre-existing and unrelated).
- Python compile check on changed backend files: successful.
- Docker-based local test execution remains blocked by local Docker engine API error (same environmental blocker as prior phase).

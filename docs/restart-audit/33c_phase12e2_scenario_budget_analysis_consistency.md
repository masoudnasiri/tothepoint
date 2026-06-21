# 33c — Phase 12E-2 Scenario Budget Analysis Consistency

## Incident summary

UAT reported that scenario selection only changed top explanatory text while the report body remained unchanged.

Impacted elements:

- currency summary cards
- required/available/gap by currency
- critical periods
- charts
- period details
- recommendations
- narrative report

## Reproduction

1. Open Budget Analysis.
2. Switch scenario between `minimum_feasible`, `average_candidate`, `worst_case`.
3. Observe header text changes.
4. Observe body totals/charts/report remained fixed in prior build.

## Root cause (technical)

`BudgetAnalysis.tsx` consumed `decisionsAPI.getBudgetAnalysis()` which returned a mixed payload:

- legacy budget report fields from `BudgetAnalysisService` (default/static context)
- scenario metadata in `optimization_semantics` from `build_optimization_budget_analysis`

The UI rendered body from legacy fields and header from scenario metadata.

## Corrective changes

### Backend

- Enriched canonical schema `OptimizationFinancialAnalysis` with:
  - `analysis_scope`
  - `optimization_result_id`
  - `selected_scenario_candidates`
  - `surplus_shortage_by_currency`
  - `critical_periods`
  - `charts`
- Added scenario aliases:
  - `worst_case`
  - `selected_optimization_result`
- Result-model narrative explicitly marked:
  - `تحلیل مالی مدل انتخابی`

### Frontend

- Switched `BudgetAnalysis.tsx` to consume only:
  - `financeAPI.getOptimizationBudgetAnalysis`
- Rebound all UI sections to canonical response object.
- Period chart/table now derived from canonical `periods`.
- Critical periods derived from canonical `critical_periods`.

## Numeric consistency controls

Regression checks assert:

- `budget_required_irr == sum(period.required_irr)`
- `budget_required_irr == sum(selected_scenario_candidates.required_irr)`
- `budget_required_irr == sum(charts.periods.required_irr)`
- narrative required number uses same canonical required total

## Non-blocking shortage messaging

Narrative keeps warning semantics and avoids blocker wording.

## Date/currency notes

- Persian UI keeps Jalali period labels in Budget Analysis.
- Narrative is no longer mixed with old Gregorian month report text from legacy source.
- Currency symbols/labels remain normalized by shared utilities.

## Validation assets

- New test suite:
  - `backend/tests/test_phase12e2_scenario_budget_analysis_consistency.py`
- Release audit:
  - `docs/release/phase12e2_scenario_budget_analysis_consistency_audit.md`

## Status

- Phase 12E-2 implementation complete in code.
- Awaiting full UAT visual walkthrough and sign-off.

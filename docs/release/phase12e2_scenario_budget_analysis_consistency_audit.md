# Phase 12E-2 — Scenario-Based Budget Analysis End-to-End Consistency Audit

## User-reported issue

In UAT, changing scenario only changed the header text while the rest of Budget Analysis (cards, charts, period details, recommendations, long narrative) remained from the legacy default analysis.

The reported numeric mismatch was:

- Scenario text: `4,136,519,213,927,500,664.23 IRR`
- Summary/report cards: `41,360,651,837,528 IRR`

## Root cause

Two different data sources were combined in one screen:

1. `decisions /budget-analysis` returned legacy `BudgetAnalysisService` sections (`total_needed_by_currency`, charts, critical months, legacy recommendations).
2. `optimization_semantics` in the same response came from scenario-aware `build_optimization_budget_analysis`.

So the header used scenario semantics, but cards/charts/tables/report used legacy baseline data.

## Backend fix

- Extended canonical `OptimizationFinancialAnalysis` to carry full scenario report data:
  - `analysis_scope`
  - `optimization_result_id`
  - `selected_scenario_candidates`
  - `surplus_shortage_by_currency`
  - `critical_periods`
  - `charts`
- Added scenario aliases:
  - `worst_case -> conservative`
  - `selected_optimization_result -> selected_result`
- Ensured all totals are derived from one selected candidate set per scenario.
- Added `selected result` narrative with explicit model wording:
  - `تحلیل مالی مدل انتخابی`

## Frontend fix

- `BudgetAnalysis` now calls canonical endpoint:
  - `GET /finance/optimization-budget-analysis`
- The whole page now renders from one response object:
  - status card
  - currency summary cards
  - charts
  - critical periods
  - period details
  - recommendations
  - narrative
- Removed mixed rendering path that used legacy default fields with scenario header metadata.

## Canonical scenario analysis behavior

- `minimum_feasible`: lowest eligible candidate per item, counted once.
- `average_candidate`: per-item average candidate cost, counted once.
- `worst_case` (alias of conservative): highest eligible candidate per item, counted once.
- `selected_optimization_result`: only candidates selected in the chosen optimization run.

## Numeric consistency fix

Consistency now enforced using one canonical object and Decimal-based totals:

- header totals
- summary totals
- narrative required budget
- period totals
- chart totals

Any order-of-magnitude drift now fails tests.

## Narrative/report behavior

- Shortage language is warning-only (non-blocking).
- Recommendations continue to allow:
  - constrained mode
  - allow-shortage mode
  - budget update path
- For result-specific analysis, narrative explicitly references selected model context.

## Date and currency display consistency

- Period labels continue to be formatted in Jalali on Persian UI in `BudgetAnalysis`.
- Narrative no longer leaks Gregorian month tokens from mixed legacy report payloads.
- Currency formatting remains centralized via `formatCurrencyAmount` and backend symbol map.

## Tests added

`backend/tests/test_phase12e2_scenario_budget_analysis_consistency.py`:

- Test A: scenario drives full response
- Test B: no double counting in all sections
- Test C: numeric consistency across sections
- Test D: selected result analysis uses selected candidates only
- Test E: non-blocking shortage language
- Test F: no Gregorian period leakage in narrative
- Test G: currency symbol consistency

## Before / After

- Before: header changed by scenario, but body remained legacy/default.
- After: all sections are recomputed and rendered from a single scenario-specific analysis response.

## Remaining limitations

- `decisions /budget-analysis` endpoint still includes legacy budget-analysis fields for backward compatibility.
- Canonical scenario view is now enforced in Budget Analysis UI through finance endpoint.

## Phase 12E-2 status

- Code fix complete.
- Automated tests added for regression coverage.
- UAT manual walkthrough still required for final business sign-off.

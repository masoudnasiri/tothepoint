# 33g — Phase 12E-4C Financial UI Clarity and Narrative Restoration

## Scope

Phase 12E-4C focuses on business-readable financial presentation in Optimization UI while preserving canonical backend traceability from 12E-4/12E-4B.

## User-Reported Issues Addressed

- Mixed English/Persian UI labels and runtime messages in Persian mode.
- Ambiguous cost semantics between purchase cost, required budget, weighted objective, and legacy solver cost.
- Selected items table not clearly showing original currency versus IRR equivalent.
- Technical reconciliation warning shown as primary business message.
- Executive narrative report degraded to short/technical output.

## Implemented Fixes

### 1) Localization and label cleanup

- Replaced hardcoded English strings in `OptimizationPage_enhanced` result cards, dialogs, actions, and notices with i18n keys.
- Added missing Persian/English i18n keys for optimization financial semantics and UI actions.
- Localized previous-runs dialog and solver/help dialogs.

### 2) Financial semantics clarity in UI

- Main business cost now prioritizes canonical `total_purchase_cost_irr`.
- Weighted objective cost remains separated and includes explicit explanatory hint.
- Added explanatory note for potential differences between required budget and purchase cost (schedule/FX/rounding basis).

### 3) Selected items table currency semantics

- Added business-facing columns for currency transparency:
  - Currency
  - Unit cost (original)
  - Total cost (original)
  - Exchange rate
  - IRR equivalent
  - Payment (plus periods where available)
- Added table-level IRR-equivalent sum for reconciliation with canonical purchase-cost card.

### 4) Reconciliation and trace display behavior

- Business-facing warning kept concise and non-technical.
- Added collapsible technical section containing:
  - reconciliation reasons
  - raw differences
  - trace lines sample table
- Technical trace is no longer primary report content.

### 5) Persian narrative restoration

- Enhanced selected-result backend narrative generation in `optimization_budget_service`:
  - starts with `📊 تحلیل مالی مدل انتخابی`
  - includes result id, selected item count, purchase cost, required/available budget, shortage/surplus, currency summary, critical periods, and recommended actions.

## Backend/API Semantics

- Canonical payload fields preserved and consumed:
  - `trace_lines`
  - `reconciliation` (+ `reasons`)
  - `total_purchase_cost_irr`
  - `weighted_objective_cost_irr`
  - `budget_required_irr`
  - `budget_required_by_currency`
  - `budget_available_by_currency`
  - `surplus_shortage_by_currency`
  - `periods`
  - `narrative_report`

## Tests and Build

- Added backend test file:
  - `backend/tests/test_phase12e4c_financial_ui_payload_semantics.py`
  - validates selected-result semantic fields and Persian narrative presence
  - validates reconciliation includes human-readable reason(s) when weighted objective differs

### UAT verification commands and results

- DB backup before rebuild:
  - `/root/pdss_backups/procurement_dss_pre_phase12e4c_20260621_144705.sql`
  - size: `1298642` bytes (verified non-empty)
- `docker compose ps` (UAT `/root/pdss_demo`): **PASS**
- `curl -sS http://127.0.0.1:18010/health`: **PASS** (`Rivar / Corbit / 1.0.0-rc1`)
- `docker compose run --rm backend python -m pytest tests -q`: **PASS** (`95 passed, 5 skipped`)
- `docker compose run --rm backend python -m pytest tests/test_phase8_release_candidate_smoke.py -q`: **PASS** (`3 passed`)
- `docker compose run --rm backend python -m pytest tests/test_phase12e4c_financial_ui_payload_semantics.py -q`: **PASS** (`2 passed`)
- `docker compose run --rm frontend npm run build`: **PASS** (compiled with pre-existing unrelated lint warnings)

## Manual UI Verification

- Manual browser walkthrough remains required for business sign-off (hard refresh/incognito).
- This phase run verified deploy, build, and tests on UAT server; it did **not** include full visual click-through automation.
- Validate all requested checkpoints (labels, semantics, table, narrative, trace collapsibility, consistency).

## Remaining Risks

- Any residual mixed-language text outside touched components may remain and should be caught in manual UAT.
- Historical runs with legacy stored totals may still surface old semantics in some meta-fields unless re-run.

## Closure

- **Phase 12E-4C status:** not closed (manual UI sign-off pending)

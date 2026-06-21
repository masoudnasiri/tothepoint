# 33e — Phase 12E-4 Financial Traceability Reconciliation

## User-reported inconsistencies at start

- Persian UI showed English shortage-decision modal labels.
- `minimum_feasible` pre-run required budget looked non-reconcilable vs optimization totals.
- selected-result financial panel and Budget Analysis `selected_result` tab reported inconsistent totals.
- currency totals (especially USD) looked suspicious in scale/label semantics.

## Implemented reconciliation model

### Canonical selected-result payload

`OptimizationFinancialAnalysis` extended with:

- `trace_lines`
- `reconciliation`
- `total_purchase_cost_irr`
- `weighted_objective_cost_irr`

### Canonical computation path

- selected-result analysis derives line-level amounts from selected result rows/decisions
- payment schedule splits are allocated by due-offset
- conversion to IRR is explicit and date-based
- period and currency totals are derived from the same trace

### Single-source behavior alignment

- Budget Analysis selected-result now receives `run_id` from optimization page context.
- Proposal financial panel and budget tab both expose canonical selected-result semantics and reconciliation warnings.

## Cost semantics clarified

- `Total Purchase Cost (IRR)` = execution/purchase cost reference.
- `Weighted Objective Cost (IRR)` = optimization objective metric, shown separately.
- Weighted objective value is not presented as purchase budget.

## Localization fix

Budget shortage decision dialog moved to i18n keys and Persian labels were added per business-required wording.

## Tests added

`backend/tests/test_phase12e4_financial_traceability_reconciliation.py`

- selected-result consistency
- weighted-vs-purchase distinction
- conversion correctness (USD to IRR)
- period split no-duplication
- minimum-feasible candidate trace
- Persian localization key validation

## Verification status

- `python -m py_compile` on changed backend modules/tests: ✅
- `frontend npm run build`: ✅ (pre-existing unrelated lint warnings remain)
- Docker-based local backend test commands: ❌ blocked by local Docker API/engine 500 error
- local `pytest` without docker: ❌ unavailable in current python env

## Risks / limits

- UAT server runtime checks and manual click-through validation are still required.
- Existing unrelated warnings in frontend are outside this phase scope.
- Legacy `total_cost` consumers should prefer `total_purchase_cost_irr` where financial correctness is required.

## Phase 12E-4 status

- **Not closed** (implementation complete locally; UAT deploy + server test run + manual business verification pending).

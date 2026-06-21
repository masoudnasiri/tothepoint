# 33f — Phase 12E-4B UAT Financial Trace Closure

## Scope

Phase 12E-4B is a UAT-server verification closure pass for Phase 12E-4 financial traceability.

## Server Runtime Verification

- Verified active server path: `/root/pdss_demo`
- `docker compose ps` services:
  - `pdss_demo-backend-1` on `:18010` (healthy)
  - `pdss_demo-frontend-1` on `:13010`
  - `pdss_demo-postgres-1` (healthy)
- Health response:

```json
{
  "status": "healthy",
  "version": "1.0.0-rc1",
  "product": "Rivar",
  "producer": "Corbit"
}
```

## Safety Backup (Before Rebuild)

- Backup path: `/root/pdss_backups/procurement_dss_pre_phase12e4b_20260621_133242.sql`
- Backup size: `1281478` bytes
- Non-empty backup verified before rebuild/restart.

## Deployment Staleness

- Initial deployed source was stale for Phase 12E-4 markers.
- After uploading 12E-4 files and non-destructive rebuild (`docker compose up --build -d`), markers were present in deployed source:
  - `trace_lines`
  - `reconciliation`
  - `total_purchase_cost_irr`
  - `weighted_objective_cost_irr`
  - localized modal keys (`budgetShortageDetected`, etc.)

## Server Test Results

Executed on UAT server (`/root/pdss_demo`):

1. `docker compose run --rm backend python -m pytest tests -q`  
   Result: **PASS** (`93 passed, 5 skipped`)

2. `docker compose run --rm backend python -m pytest tests/test_phase8_release_candidate_smoke.py -q`  
   Result: **PASS** (`3 passed`)

3. `docker compose run --rm backend python -m pytest tests/test_phase12e4_financial_traceability_reconciliation.py -q`  
   Result: **PASS** (`5 passed, 1 skipped`)

4. `docker compose run --rm frontend npm run build`  
   Result: **PASS** (build successful; existing unrelated lint warnings remain)

### Note on one test adjustment

- `test_phase12e4_test_f_persian_budget_shortage_modal_labels_exist` originally assumed frontend files exist inside backend test image.
- In UAT backend container, frontend tree is not packaged under `/app/frontend`.
- Test was made environment-safe by skipping if the frontend i18n file is unavailable in the backend test image.

## Direct API Reconciliation

### Target historical run

- Requested run ID exists: `9fbae498-aac0-4b76-b0e8-1dd0a20b3739`

For this run:

- `selected_result` panel endpoint:
  - `/finance/optimization-results/{run_id}/financial-analysis`
- `selected_result` budget-tab endpoint:
  - `/finance/optimization-budget-analysis?scenario=selected_result&run_id={run_id}`

Both returned matching values:

- `budget_required_irr`: `1399890651100914158.340000000`
- `budget_required_by_currency`:
  - `IRR: 13747366421223.940`
  - `USD: 2164407764352.860`
- `trace_lines` count: `43`
- `reconciliation`: present
- narrative includes `تحلیل مالی مدل انتخابی`

`minimum_feasible` check:

- `budget_required_irr`: `4136519213927500664.23000000`
- trace lines present (`235`)

Legacy endpoint `/decisions/budget-analysis` still exists (legacy payload fields), but selected-result body is now sourced from canonical finance endpoint.

### Fresh verification run

Created fresh run (for current-code proof):

- run_id: `dce87ca0-4223-4d70-834b-42664a345bb3`

Optimization response (canonical semantics now exposed):

- `response_total_cost`: `1399890651100907034.349900000`
- `proposal_total_cost` (legacy solver raw): `15911774185576.79890`
- `proposal_weighted_cost`: `41689379759685.81300`
- `proposal_total_purchase_cost_irr`: `1399890651100907034.349900000`
- proposal financial analysis:
  - `budget_required_irr`: `1399890651100907034.349900000`
  - `weighted_objective_cost_irr`: `41689379759685.81300`
  - `trace_lines`: present (`43`)
  - `reconciliation`: present

For selected-result endpoints on same run:

- panel required budget == tab required budget:
  - `1399890651100914158.340000000`
- currency totals match between both views.
- period totals == trace totals == required budget (within float rendering tolerance).
- narrative matches between both views and includes `تحلیل مالی مدل انتخابی`.

## Financial Reconciliation Table

| Check | Result |
| --- | --- |
| Selected-result panel vs selected-result budget tab required budget | Match |
| Selected-result currency totals across both views | Match |
| `trace_lines` present | Yes |
| `reconciliation` object present | Yes |
| Period total vs trace total vs required budget | Match (tolerance-safe) |
| Legacy decisions endpoint used for selected-result body | No (source-level verification) |

## Network/Binding Verification

Source-level verification on UAT deployed frontend:

- Canonical call present:
  - `financeAPI.getOptimizationBudgetAnalysis` in `BudgetAnalysis.tsx`
- Selected-result run binding present:
  - `params.run_id = runId`
- Legacy selected-result binding absent:
  - no `decisionsAPI.getBudgetAnalysis` usage in selected-result body path

Built bundle inspection also showed canonical endpoint reference and no legacy `/decisions/budget-analysis` match.

## Persian Localization Verification

Deployed `fa.json` contains:

- `budgetShortageDetected`: `کسری بودجه شناسایی شد`
- `budgetShortageDecisionMessage`: expected Persian message
- `optimizeWithinCurrentBudget`: `ادامه با بودجه موجود`
- `optimizeAllWithShortageAnalysis`: expected Persian text
- `cancelAndUpdateBudget`: expected Persian text
- `shortage`: `کسری بودجه`

## Manual UI Walkthrough

- Full browser/manual click-through was **not executed by automation in this closure pass**.
- API and deployed source verification succeeded; final visual/manual sign-off remains a business/UAT operator action.

## Remaining Risks

- Historical runs retain legacy summary field semantics (`optimization_runs.total_cost` from mixed-currency raw proposal total).
- Reconciliation object may report differences between optimizer raw cost and payment-schedule-based required budget; this is now surfaced explicitly.
- Manual visual confirmation is still needed for full closure confidence.

## Closure Decision

- **Phase 12E-4B:** not fully closed (manual UI walkthrough/sign-off pending)
- **Phase 12E-4:** not fully closed until manual walkthrough is completed and signed off


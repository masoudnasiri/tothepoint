# 33d — Phase 12E-3 Budget Analysis Deployment and Optimizer Diagnostics

## User-reported state at start

- UAT still showed legacy/default budget analysis body.
- Only top scenario text changed.
- Financial analysis for selected optimization result looked non-specific.
- User also observed same optimization outputs across modes and unchanged cost after item removal.

## Deployment verification findings

### Server path and runtime

- Active runtime path: `/root/pdss_demo`
- Services healthy:
  - `backend` on `:18010`
  - `frontend` on `:13010`
  - `postgres` healthy
- Health endpoint matched product identity:
  - `status=healthy`
  - `version=1.0.0-rc1`
  - `product=Rivar`
  - `producer=Corbit`

### Git/commit state on server

- `/root/pdss_demo` is **not a git checkout** (tar-style deployment layout).
- `git rev-parse` for commit `6f336df` was not available on server.
- Therefore commit-level verification had to be done by source-marker inspection.

### Pre-deploy backup

- Backup created before rebuild:
  - `/root/pdss_backups/procurement_dss_pre_phase12e3_20260621_062142.sql`
  - size: `1248549` bytes (non-empty, verified)

## Root cause of unchanged analysis

### Confirmed stale deployment + legacy endpoint usage

Before redeploy, deployed frontend source contained:

- `decisionsAPI.getBudgetAnalysis` ✅
- `financeAPI.getOptimizationBudgetAnalysis` ❌

This reproduces the exact mixed-source bug:

- Legacy endpoint `/decisions/budget-analysis` returned:
  - old body fields like `total_needed_by_currency` (e.g. `41360651837527.77 IRR`)
  - plus `optimization_semantics` narrative (`4,136,519,213,927,500,664.23 IRR`)
- This caused the headline/body mismatch seen by UAT.

## What was deployed/fixed in this phase

- Deployed canonical scenario-binding files to UAT backend/frontend.
- Rebuilt services non-destructively via:
  - `docker compose up --build -d`

After deploy, frontend source markers show:

- `decisionsAPI.getBudgetAnalysis` ❌
- `financeAPI.getOptimizationBudgetAnalysis` ✅

and backend canonical schema/service markers are present (`analysis_scope`, `selected_scenario_candidates`, `surplus_shortage_by_currency`, etc.).

## Backend scenario endpoint behavior after deploy

Direct authenticated endpoint checks on:

- `GET /finance/optimization-budget-analysis?scenario=minimum_feasible`
- `...average_candidate`
- `...worst_case`

showed:

- canonical fields present (`selected_scenario_candidates`, `surplus_shortage_by_currency`, `critical_periods`, `charts`)
- body not from legacy endpoint
- numeric consistency across canonical sections:
  - `budget_required_irr ~= sum(period.required_irr) ~= sum(charts.period.required_irr) ~= sum(selected_scenario_candidates.required_irr)` (rounding-level variance only)

In current UAT dataset, min/avg/worst totals were equal because candidate alternatives collapsed to effectively identical scenario totals for analyzed items (data-dependent outcome).

## Numeric consistency result

- Legacy endpoint mismatch reproduced (expected old bug behavior).
- Canonical endpoint after deploy is internally consistent across summary/period/chart/selected-candidate totals.

## Selected result financial analysis behavior

`scenario=selected_optimization_result&run_id=<id>` now returns:

- `analysis_scope=optimization_result`
- `optimization_result_id=<run_id>`
- model-specific narrative prefix:
  - `تحلیل مالی مدل انتخابی`

Observed one run with `0` required budget also emitted explicit “No selected optimization result exists yet.” narrative (valid for empty-result run).

## Optimizer objective diagnostics (no solver rewrite)

### What was verified

Controlled API diagnostics were executed for `CP_SAT` and `GLOP` with multiple strategies.

Findings:

- Solver/mode propagation works (backend receives solver and strategies).
- `GLOP` produced **different** decision sets/costs for some strategies.
- `CP_SAT` produced identical decision sets for all tested strategies on this dataset.

Interpretation:

- “all modes same output” is **not universally true**; objective propagation exists.
- For CP-SAT + current constraints/data, equal outputs appear data/constraint-driven (not yet proven engine bug).

## Item removal / total-cost behavior

Confirmed UI issue:

- removing/editing items in proposal was local-only
- displayed proposal `Total Cost` and item count were not recomputed immediately

Fix applied (frontend, minimal):

- proposal summary cost and item count now recompute from effective local decisions (edited/removed/added)
- informational note clarifies financial analysis card updates after saving proposal

## Tests added

- `backend/tests/test_phase12e3_budget_analysis_runtime_binding.py`
  - A: scenario-driven full-body behavior (when data supports)
  - B: canonical payload without legacy field leakage
  - C: selected-result uses selected candidates only
  - D: numeric consistency across summary/period/chart/narrative

- `backend/tests/test_phase12e3_optimizer_objective_diagnostics.py`
  - E: strategy/objective list accepted and reflected in optimizer response path
  - F: financial summary recomputes when decision set changes

## Test execution on UAT server

- `docker compose run --rm backend python -m pytest tests -q` ✅
- `docker compose run --rm backend python -m pytest tests/test_phase8_release_candidate_smoke.py -q` ✅
- `docker compose run --rm backend python -m pytest tests/test_phase12e3_budget_analysis_runtime_binding.py -q` ✅
- `docker compose run --rm backend python -m pytest tests/test_phase12e3_optimizer_objective_diagnostics.py -q` ✅
- `docker compose run --rm frontend npm run build` ✅ (with pre-existing lint warnings unrelated to Phase 12E-3)

## Manual UAT verification status

- API/runtime verification completed.
- Full click-through UI manual verification still pending business/user walkthrough.

## Remaining limitations / risks

- Server deployment is not git-native; commit hash verification on server cannot be direct.
- CP-SAT strategy-equivalence on this dataset may still be perceived as “same mode result”; currently not proven incorrect.
- Local proposal financial-analysis card still reflects persisted snapshot until save/recompute flow (explicitly labeled now).

## Phase 12E-3 status

- **Not closed** pending final manual business UI verification in UAT.

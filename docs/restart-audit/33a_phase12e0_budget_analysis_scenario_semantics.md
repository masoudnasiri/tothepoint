# Phase 12E-0 — Optimization Budget Analysis Scenario Semantics and Budget-Shortage Flow

## User concern

Business feedback indicated that optimization budget analysis semantics were not explicit enough for decision support:

- risk of alternative-candidate double counting
- shortage acting as practical blocker without explicit user decision flow
- missing constrained/allow-shortage mode distinction
- inconsistent currency symbol formatting

## Root cause (confirmed)

1. No dedicated scenario-based optimization budget-analysis service for pre-run decision flow.
2. Optimization run UX lacked explicit shortage decision dialog with actionable mode choices.
3. Budget mode intent was not captured explicitly in optimization request model.
4. Currency formatting in optimization/budget UI was not centralized.

## Corrected semantics

Implemented in `app/services/optimization_budget_service.py`:

- `minimum_feasible`
- `average_candidate`
- `conservative`
- `selected_result`

Each scenario enforces:

- one counted contribution per project item
- alternatives treated as alternatives (not summed)
- base aggregate in IRR with FX warnings on missing rates

## Coverage eligibility rule used

Budget scenario analysis now follows optimization-eligible inputs aligned with current flow:

- active projects
- finalized project items (`is_finalized=true`)
- active + finalized procurement options
- excludes already decided items (`LOCKED`/`PROPOSED`)
- package combinations are considered through package-combination analysis where available

## Double-count prevention

- `double_count_prevented=true` in scenario response metadata
- candidate/combo alternatives are grouped per project item
- scenario picks one representative candidate per item

## Non-blocking shortage behavior

Scenario response now includes:

- `is_blocking=false`
- `can_continue_with_warning=true`
- `allowed_actions`:
  - `optimize_within_available_budget`
  - `optimize_all_with_shortage_analysis`
  - `cancel_and_update_budget`

## Optimization mode behavior

### 1) Constrained mode (`budget_mode=constrained`)

- execution path now enforces within-budget final selection
- deferred/excluded items are returned in proposal metadata
- proposal includes used/remaining budget summary
- safe fallback heuristic (greedy by IRR) is applied when needed

### 2) Allow-shortage mode (`budget_mode=allow_shortage`)

- optimization continues despite shortage
- proposal financial analysis is attached for warning/critical visibility

## Per-result financial analysis

Added:

- `GET /finance/optimization-results/{run_id}/financial-analysis`
- `POST /finance/proposal-financial-analysis`

Each analysis includes:

- required/available/shortage in IRR
- required and available by currency
- period gaps
- contributors
- recommendations + narrative

## Frontend changes

- `OptimizationPage_enhanced.tsx` now performs pre-run budget precheck.
- If shortage exists, user gets 3 explicit choices:
  - optimize within current budget
  - optimize all items and show shortage analysis
  - cancel and update budget
- Proposal-level financial analysis panel added.
- Budget analysis component shows scenario selector and anti-double-count note.

## Currency symbol fix

Added centralized frontend utility:

- `frontend/src/utils/currencyFormat.ts`
  - `getCurrencySymbol(currency)`
  - `formatCurrencyAmount(amount, currency, locale)`

Applied to optimization and budget analysis UI paths to avoid blanket `$` formatting.

## Tests added

- `backend/tests/test_phase12e0_budget_analysis_semantics.py`
  - A: multiple candidates not summed
  - B: package combinations not summed
  - C: multiple items counted once each
  - D: missing candidate warning path
  - E: FX conversion correctness
  - F: missing FX warning path
  - G: shortage is non-blocking
  - H: constrained selection stays within budget
  - I: allow-shortage analysis keeps full shortage visibility
  - J: currency symbol mapping

## Before/after (illustrative)

- Before: alternatives could be interpreted cumulatively in pre-run decision semantics.
- After: scenario-driven single-count per item, explicit warning workflow, explicit execution modes.

## Remaining limitations

- Constrained mode final enforcement includes a greedy fallback; full exact multi-objective constrained selection remains an optimization-engine enhancement path.

## Phase status

- **Implementation complete in code and tests; pending business UAT confirmation on live dataset.**


# Phase 12E-1 — Optimization Feasibility Diagnostics and Allow-Shortage Execution Fix

## User-reported failure

In UAT, both optimization paths failed with generic infeasible messaging:

- `budget_mode=constrained`
- `budget_mode=allow_shortage`

This was incorrect for allow-shortage because budget shortage must be warning-only in that mode.

## Root cause found

Two core issues were confirmed:

1. **Variable-key parsing bug** in enhanced optimizer:
   - decision-variable names embedded `item_code`
   - parser split on `_`
   - item codes containing `_` broke parser assumptions and caused strategy failures (`None` proposals)
2. **Legacy candidate gating** still depended on delivery-option structures in solver build path, which could silently remove otherwise valid finalized procurement candidates.

## Frontend budget-mode propagation

Verified and preserved:

- `OptimizationPage_enhanced` sends explicit mode:
  - `budget_mode=constrained`
  - `budget_mode=allow_shortage`

No propagation bug found in the enhanced page path.

## Backend budget-mode handling

Corrected and verified:

- `allow_shortage` keeps budget constraints disabled (`budget_constraints_enabled=false`)
- `constrained` keeps budget-aware restriction behavior, with budget-filter diagnostics exposed

## Candidate pipeline diagnostics added

Structured diagnostics are now attached in optimization response, including:

- item/candidate counts
- missing-candidate and missing-coverage lists
- status/budget/lead-time filter counters
- constraint summary and solver status
- budget constraint toggle visibility

Also added `error_code` for machine-readable failure semantics (e.g. `NO_ELIGIBLE_CANDIDATES`).

## Partial feasible behavior

Added request flag:

- `require_all_items` (default `false` for UAT)

With default behavior:

- optimizer can return feasible partial results when at least one item has valid candidates
- skipped/infeasible causes remain visible through diagnostics

## Error-message behavior after fix

Replaced budget-only generic failure pattern with diagnostics-aware messaging:

- allow-shortage failures explicitly state budget was not the blocker
- no-candidate and filtered-candidate cases report non-budget causes

## Allow-shortage behavior after fix

- budget shortage does not hard-block execution in solver path
- runs can complete with candidate-driven decisions even when budget is below required cost
- shortage analysis remains available via financial analysis flow

## Constrained behavior after fix

- constrained flow still supports budget-limited outcomes
- diagnostics now include `items_filtered_by_budget` to explain exclusions

## Tests added

`backend/tests/test_phase12e1_optimization_feasibility_modes.py`:

- A: allow-shortage ignores budget as hard blocker
- B: constrained mode respects budget and reports budget filtering
- C: frontend/backend mode propagation path (API handling)
- D: no-candidate path returns specific error code and diagnostics
- E: partial feasible result with `require_all_items=false`
- F: diagnostic counters include dropped-reason visibility

## Before/after behavior

- **Before:** allow-shortage could still end with generic infeasible due parser/filter pipeline errors, often blamed on budget.
- **After:** parser-safe variable mapping + diagnostics clarify real non-budget causes; allow-shortage does not use budget as hard blocker.

## Remaining limitations

- Detailed per-stage drop reasons for every package-combination path still depend on deeper package-engine instrumentation.
- Legacy optimization page (`/finance/optimize`) remains separate from enhanced diagnostics flow.

## Phase 12E-1 status

- Implementation complete in code + automated tests.
- Manual UAT walkthrough still required for business sign-off.

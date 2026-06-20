# Phase 12E-0 Budget Analysis Semantics Audit

## Scope

- Product: `Rivar`
- Producer: `Corbit`
- Version: `1.0.0-rc1`
- Focus: Optimization budget-analysis correctness and budget-shortage execution flow.

## Current endpoint/component map (post-fix)

- Backend pre-check endpoint: `GET /finance/optimization-budget-analysis`
- Backend optimization execution endpoints: `POST /finance/optimize-enhanced` (+ `budget_mode`)
- Backend per-run financial analysis: `GET /finance/optimization-results/{run_id}/financial-analysis`
- Backend per-proposal financial analysis: `POST /finance/proposal-financial-analysis`
- Existing budget screen endpoint (kept compatible): `GET /decisions/budget-analysis`
- Frontend optimization page: `frontend/src/pages/OptimizationPage_enhanced.tsx`
- Frontend budget analysis component: `frontend/src/components/BudgetAnalysis.tsx`

## Data sources used

- `Project`, `ProjectItem` (eligible finalized items)
- `ProcurementOption` (active + finalized candidates)
- `ProcurementPackage` + package-combination analysis service for package alternatives
- `BudgetData` (monthly available budget, including multi-currency payload)
- `OptimizationResult` (selected-result scenario and run-level analysis)
- `ExchangeRate` via `CurrencyConversionService` (IRR aggregation)

## Root-cause findings

1. Budget analysis and optimization pre-check semantics were not explicitly scenario-based for optimization decisions.
2. Optimization flow had no mandatory warning decision point with explicit user choices when shortage exists.
3. Currency display was inconsistent in optimization/budget UI and defaulted to USD formatting (`$`) in multiple places.
4. Constrained-vs-allow-shortage execution behavior was not explicit in request/response contracts.

## Confirmed corrections

- Added scenario-based optimization budget analysis:
  - `minimum_feasible`
  - `average_candidate`
  - `conservative`
  - `selected_result`
- Enforced single-count semantics per project item per scenario (`double_count_prevented=true`).
- Added explicit non-blocking shortage metadata:
  - `is_blocking=false`
  - `can_continue_with_warning=true`
  - `allowed_actions=[constrained, allow_shortage, cancel]`
- Added explicit optimization execution mode:
  - `budget_mode=constrained`
  - `budget_mode=allow_shortage`
- Added per-proposal and per-run financial analysis outputs.
- Added centralized frontend currency symbol/label formatting utility and applied it to optimization/budget flows.

## Double-count prevention semantics

- Each project item contributes at most one candidate/combination per scenario.
- Alternatives are evaluated as alternatives, not summed together.
- Scenario selection chooses one representative per item (min/avg/max/selected).

## Budget-shortage behavior

- Shortage is now a warning decision point, not a hard blocker.
- UI now prompts user to choose:
  1. Optimize within current budget (`constrained`)
  2. Optimize all items with shortage analysis (`allow_shortage`)
  3. Cancel and update budget

## Optimization mode behavior

- **Constrained mode**
  - Budget treated as hard execution cap.
  - Response includes excluded/deferred item summaries.
  - Used/remaining budget fields returned in proposal budget summary.
  - Note: a safe greedy fallback is used to enforce final within-budget selection when needed.

- **Allow-shortage mode**
  - Optimization can proceed despite shortage.
  - Financial shortage analysis is attached per proposal/result.

## Currency behavior

- Unified IRR base for aggregate shortage/surplus.
- Original currency totals are preserved in analysis structures.
- Missing exchange rates generate warnings and are not silently included in IRR aggregates.
- Frontend symbol behavior corrected:
  - `IRR: ریال`
  - `USD: $`
  - `EUR: €`
  - `AED: د.إ`
  - `CNY: ¥`
  - `TRY: ₺`

## Before/after example

- Before (incorrect interpretation): all alternatives could be interpreted as cumulative exposure.
- After (scenario-based): one candidate per item per scenario; same item alternatives are not summed together.

## Remaining limitations

- The constrained fallback selection is heuristic (greedy by IRR) when strict solver-level constraints do not fully enforce desired budget behavior.
- Legacy optimization page (`OptimizationPage.tsx`) remains simpler than enhanced flow, but now uses corrected currency formatting and default non-blocking mode input.

## Phase status

- Phase 12E-0 implementation status: **implemented in code + tests + docs**, pending final UAT sign-off.


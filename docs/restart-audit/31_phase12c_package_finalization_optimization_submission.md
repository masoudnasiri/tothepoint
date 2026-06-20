# Phase 12C - Package Finalization and Optimization Submission Gate

## Scope

- Phase: `12C`
- Product: `Rivar`
- Producer: `Corbit`
- Version: `1.0.0-rc1`
- Context: UAT post-redesign workflow fixes for procurement package finalization and optimization submission.

## User-Reported Issues

- Finalized packages were not clearly represented in list status and optimization eligibility gates.
- Partial package sets needed deterministic combination analysis before optimization submission.
- Incomplete coverage could be submitted without explicit confirmation.
- Bulk submission flow needed to apply the same confirmation and eligibility rules as single-item flow.
- Items sent to optimization needed backend-enforced package edit/create/delete locks.
- Procurement users needed optimization-state and coverage-state filters.
- Coverage labels needed clearer semantics (current package vs aggregate vs optimization-eligible) and explicit surplus wording.

## Business Rules Implemented

- Only finalized packages are eligible for optimization submission.
- Draft/non-finalized packages are excluded by backend logic regardless of UI state.
- Partial combinations are generated deterministically with a configurable cap (`max_combinations`, default `128`, max `512`).
- Dominated combinations are removed when they are clearly inferior (coverage/cost/delivery criteria).
- Incomplete coverage requires explicit user confirmation (`include_incomplete_with_confirmation` + item list).
- Sending an item to optimization locks package and procurement option write operations for that item.
- Rollback is blocked when dependent decisions are in `PROPOSED` or `LOCKED` state.

## Backend Changes

- Added `OptimizationSubmission` persistence model and constraints.
- Added `backend/app/services/package_combination_service.py` with:
  - finalized package extraction,
  - combination generation and pruning,
  - coverage/cost/delivery analysis,
  - submission marking and rollback safety checks,
  - optimization/coverage state helpers.
- Extended package schemas with runtime status and locking metadata.
- Added optimization submission and rollback endpoints in package router:
  - `POST /packages/optimization-submission`
  - `POST /packages/optimization-submission/{project_item_id}/rollback`
- Enforced sent-to-optimization lock in:
  - package create/update/delete,
  - package subitem create/update/delete,
  - procurement option create/update/delete.
- Extended finalized item listing with:
  - optimization state,
  - coverage state,
  - rollback capability metadata,
  - finalized/active package counts.

## Frontend Changes

- Package Wizard:
  - persisted `is_finalized`,
  - clarified coverage semantics and surplus messaging,
  - kept redesigned UI layout intact.
- Package List:
  - explicit status chip (`DRAFT`, `FINALIZED`, `SENT_TO_OPTIMIZATION`, `INACTIVE`),
  - disabled edit/delete when item is optimization-locked.
- Procurement Page:
  - single and bulk send-to-optimization flow with incomplete confirmation gate,
  - rollback action when safe,
  - optimization state filter,
  - coverage state filter,
  - sent/rolled-back visual tags and action gating.
- Coverage modal/calculations:
  - over-coverage warning representation,
  - surplus-aware display,
  - consistent wording for coverage context.

## API Behavior

### Submit packages to optimization

- Request supports one item, multiple items, or all eligible finalized items.
- Response structure includes:
  - `submitted_items`
  - `skipped_items`
  - `warnings`
  - `incomplete_items_requiring_confirmation`
  - `generated_combinations`
  - `errors`

### Rollback optimization submission

- Marks item submission state as `ROLLED_BACK` when safe.
- Rejects rollback when dependent decisions are already `PROPOSED` or `LOCKED`.

## Combination Logic and Threshold

- Subsets are generated deterministically from finalized package candidates.
- Combination count is capped by `max_combinations` to avoid combinatorial explosion.
- If cap is reached, response includes warnings and analyzed deterministic subset only.
- Over-coverage is treated as warning-state (`OVER_COVERED`) and surfaced to UI.

## Incomplete Coverage Confirmation

- Incomplete items are returned in `incomplete_items_requiring_confirmation`.
- They are not submitted unless explicitly confirmed by user.
- Confirmed incomplete submissions are tracked with `partial_coverage_acknowledged=true`.

## Sent-to-Optimization Locking

- Once submitted:
  - create/edit/delete package is rejected,
  - package subitem edits are rejected,
  - procurement option edits are rejected.
- Rollback re-enables write operations only when dependency safety checks pass.

## Filters Added

- Optimization filter: `all`, `not_sent`, `sent`, `rolled_back`.
- Coverage filter: `all`, `no_package`, `partial`, `full`, `over_covered`, `missing_components`.

## Tests Added

- `backend/tests/test_phase12c_package_optimization_submission.py`
  - finalized eligibility gate,
  - full coverage from partial combinations,
  - multiple full combination candidates,
  - incomplete confirmation gate,
  - optimization lock + rollback safety,
  - coverage overage state consistency.

## Verification Status

- Local Python compile check for modified backend modules: passed.
- Frontend build (`npm run build`): passed (existing non-blocking lint warnings remain outside Phase 12C scope).
- Containerized backend test execution in this workstation was blocked by local Docker engine/image API issue and must be executed on UAT server.

## Remaining Limitations / Risks

- Full backend regression and UAT smoke verification remain pending on target UAT server runtime.
- Bulk confirmation UX currently uses browser confirm prompt; future enhancement can replace with richer dialog without changing backend contract.

## Phase 12C Status

- Implementation: complete in code.
- UAT server verification and final acceptance: pending.

# Rivar Restart Audit - Phase 5 Increment Report (Decision Lock Coverage Enforcement)

## Scope

This increment enforces package/sub-item coverage checks at the decision lock boundary.

Focus:

- prevent locking package decisions when required component coverage is incomplete
- keep rollout safe via a dedicated feature flag
- preserve legacy behavior when package flow or enforcement is disabled

## Changes Implemented

### 1) New feature flag

Updated:

- `backend/app/config.py`
- `backend/app/routers/config.py`
- `.env.example`
- `backend/.env.example`

Added:

- `ENFORCE_PACKAGE_COVERAGE_ON_LOCK` (default `false`)

Feature flag response (`GET /config/feature-flags`) now includes:

- `enforce_package_coverage_on_lock`

### 2) Service-layer lock guard

Updated:

- `backend/app/services/package_service.py`
- `backend/app/services/__init__.py`

Added:

- `validate_package_coverage_for_lock(db, decision_ids)`
- internal `_validate_project_item_subitem_coverage_for_packages(...)`

Behavior:

1. Guard is active only when:
   - `ENABLE_PACKAGE_PROCUREMENT=true`
   - `ENFORCE_PACKAGE_COVERAGE_ON_LOCK=true`
2. For each locking decision with `package_id`, service validates per `project_item_id`:
   - union of package IDs from:
     - existing `LOCKED` package decisions
     - currently locking decisions
   - validates aggregate `PackageSubItem.quantity_covered` against required `ProjectItemSubItem.quantity`
3. If any required sub-item remains uncovered, lock is blocked with HTTP 400.
4. If a project item has no sub-item requirements, enforcement is skipped for that item.

### 3) Decision boundary enforcement on lock

Updated:

- `backend/app/routers/decisions.py`

Applied guard in:

1. `POST /decisions/finalize`
   - resolves eligible decisions first
   - executes coverage guard before status update
   - keeps existing cashflow reactivation behavior for re-finalized decisions
2. `PUT /decisions/{decision_id}/status` when target status is `LOCKED`
   - runs coverage guard before updating status

Also improved error semantics in finalize flow:

- `HTTPException` from coverage validation now propagates correctly (not wrapped as 500).

## Tests Added

New test file:

- `backend/tests/test_phase5_decision_lock_coverage.py`

Coverage:

1. enforcement disabled => no-op
2. enforcement enabled + incomplete coverage => blocks lock (HTTP 400)
3. enforcement enabled + existing LOCKED package plus target package together satisfy coverage => allows lock

## Verification

Executed:

- `python -m py_compile app/config.py app/services/package_service.py app/services/__init__.py app/routers/config.py app/routers/decisions.py tests/test_phase5_decision_lock_coverage.py tests/test_phase5_package_optimization_boundary.py`
  - result: **passed**

Note:

- Runtime pytest execution remains blocked in this workstation due missing host `pytest` package and Docker engine API failures; syntax and lint checks for changed files pass.

## Outcome

This increment closes a major decision-boundary safety gap for package rollout: finance lock/finalize operations can now be configured to reject incomplete component coverage, preventing partially covered package decisions from becoming locked commitments.

# Rivar Restart Audit - Phase 5 Increment Report (Package-Aware Optimization + Decision Boundary)

## Scope

This increment implements package-aware decision boundaries in optimization and decision persistence flow.

Focus:

- avoid over-blocking optimization when only one package is already decided
- treat package-level decisions as first-class optimization boundaries
- align decision deduplication/supersede logic with package boundaries
- propagate `package_id` through enhanced optimization proposal decisions

## Changes Implemented

### 1) Optimization boundary integration

Updated:

- `backend/app/optimization_engine.py`
- `backend/app/optimization_engine_enhanced.py`

Key behavior:

1. Added package-boundary mode gating via `ENABLE_PACKAGE_BASED_OPTIMIZATION`.
2. In package-boundary mode:
   - decided records with `package_id` block only matching package options
   - legacy decided records without `package_id` still block by `project_item_id`
3. In legacy mode:
   - existing coarse exclusion behavior remains (item-level/project-item level depending on engine).
4. Enhanced optimizer now includes `package_id` in output decision objects.

### 2) Decision-save boundary integration

Updated:

- `backend/app/routers/decisions.py`

Key behavior:

1. Added internal boundary helper `_decision_boundary_conditions(...)`:
   - package-first boundary in package optimization mode
   - fallback to legacy (`project_item_id + item_code`) boundary
2. `POST /decisions/save-proposal` now:
   - resolves package from payload -> procurement option -> project item fallback
   - checks duplicate decisions per run using package-aware boundary
   - marks superseded reverted decisions using same boundary
   - prefers package-scoped delivery options when package boundary mode is enabled
3. `POST /decisions/batch` now:
   - uses package-aware deduplication boundary
   - prefers package-scoped delivery options for invoice derivation

### 3) Schema update

Updated:

- `backend/app/schemas.py`

Added `package_id` to `OptimizationDecision` response schema so optimizer outputs can carry package boundary context into decision save flows.

### 4) Tests added

New file:

- `backend/tests/test_phase5_package_optimization_boundary.py`

Coverage:

1. boundary helper chooses package boundary when package mode is enabled
2. boundary helper falls back to legacy keys when package mode is disabled
3. optimizer in package mode blocks decided package option while keeping sibling package option available

## Verification

Executed:

- `python -m py_compile app/optimization_engine.py app/optimization_engine_enhanced.py app/routers/decisions.py app/schemas.py tests/test_phase5_package_optimization_boundary.py`
  - result: **passed** (syntax validation)

Attempted:

- `python -m pytest tests/test_phase5_package_optimization_boundary.py tests/test_package_validation_phase5.py -q`
  - result: **failed** (`No module named pytest` in host interpreter)
- `docker compose run --rm backend python -m pytest backend/tests/test_phase5_package_optimization_boundary.py backend/tests/test_package_validation_phase5.py -q`
  - result: **failed** (Docker engine API error on this workstation at runtime)

## Outcome

This increment closes a key Phase 5 integration gap: optimization and decision persistence now share a package-aware boundary model, reducing false exclusions and duplicate decision conflicts in package procurement rollout mode while preserving legacy fallback behavior.

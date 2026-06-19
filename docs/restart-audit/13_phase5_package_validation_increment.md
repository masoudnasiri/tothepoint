# Rivar Restart Audit - Phase 5 Increment Report (Package Coverage Guardrails)

## Scope

This Phase 5 increment hardens package/sub-item business rules in the procurement package flow.

Focus:

- prevent invalid package-to-subitem mappings
- prevent over-coverage of sub-item demand across active packages
- normalize coverage fields (`is_fully_covered`, `coverage_percentage`) at write time
- enforce safe package main-item quantity limits

## Changes Implemented

### Backend service-layer rules

Updated `backend/app/services/package_service.py`:

1. `validate_main_item_quantity(...)`
   - blocks negative values
   - blocks `main_item_quantity` greater than project item required quantity

2. `validate_and_compute_subitem_coverage(...)`
   - verifies package exists
   - verifies project sub-item exists
   - enforces package and sub-item belong to the same `project_item_id`
   - blocks per-row overflow (`quantity_covered > required_quantity`)
   - blocks aggregate overflow across active packages for the same sub-item
   - computes normalized:
     - `is_fully_covered`
     - `coverage_percentage`

### API endpoint enforcement

Updated `backend/app/routers/packages.py`:

- `POST /packages/`
  - validates `main_item_quantity` via service rule
- `PUT /packages/{package_id}`
  - validates duplicate package names when renamed
  - validates `main_item_quantity` if updated
- `POST /packages/subitems/`
  - runs coverage validation helper
  - stores computed `is_fully_covered` and `coverage_percentage`
- `PUT /packages/subitems/{subitem_id}`
  - validates update against aggregate active coverage (excluding current row)
  - recomputes/stores normalized coverage fields

### Service exports

Updated `backend/app/services/__init__.py` to export the new validation helpers.

## Tests Added

New test file: `backend/tests/test_package_validation_phase5.py`

Coverage:

1. rejects `main_item_quantity` above project demand
2. rejects sub-item mapped to package from a different project item
3. rejects aggregate sub-item over-coverage across active packages
4. verifies computed coverage fields for valid input

## Verification

Executed:

- `docker compose run --rm backend python -m pytest tests/test_package_validation_phase5.py -q`
  - result: **4 passed**

- `docker compose run --rm backend python -m pytest tests/test_crud_phase3.py tests/test_validators.py tests/test_audit_service.py tests/test_package_validation_phase5.py -q`
  - result: **27 passed**

Note:

- a full `pytest tests -q` run intermittently hit container memory limits during test discovery on this workstation; targeted backend suites passed.

## Outcome

This increment closes a major Phase 5 gap: packages can no longer silently produce inconsistent or over-allocated sub-item coverage in active planning data, and the API now enforces parent-child integrity for package composition.

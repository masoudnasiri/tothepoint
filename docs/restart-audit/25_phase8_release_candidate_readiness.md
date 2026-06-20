# Phase 8 - Release Candidate, Demo Data and Delivery Readiness

## Scope

Phase 8 focused on release readiness and demonstration readiness only:

- deterministic demo dataset tooling
- release/demo documentation artifacts
- minimal automated RC smoke regression tests
- baseline verification commands in healthy runtime environment
- targeted documentation consistency pass

No new major product module was introduced.

## Demo Dataset Artifacts

Added:

- `backend/scripts/create_demo_dataset.py`

Key behavior:

- deterministic `DEMO_RC8_` tagged data creation
- cleanup mode that removes only `DEMO_RC8_` tagged records
- includes:
  - 2 projects (`DEMO_RC8_PRJ_DC`, `DEMO_RC8_PRJ_SEC`)
  - decomposed `Server` item with required components
  - simple non-decomposed item
  - 3 suppliers with differing package/payment-term profile
  - incomplete and complete package lock scenarios
  - execution finance records (invoice/payment-in/supplier-payment/cashflow)
  - demo audit row

Server evidence:

- create command:
  - `docker compose run --rm -e PYTHONPATH=/app backend python scripts/create_demo_dataset.py --mode create`
- returned lock validation:
  - `fail_lock_error_contains_incomplete: true`
  - `pass_lock_ok: true`
- cleanup command:
  - `docker compose run --rm -e PYTHONPATH=/app backend python scripts/create_demo_dataset.py --mode cleanup`
- cleanup verification query:
  - `projects_demo_count=0`
  - `project_items_demo_count=0`
  - `suppliers_demo_count=0`

## Demo/Release Documents Added

Added:

- `docs/release/demo_script_phase8.md`
- `docs/release/product_smoke_test_checklist.md`
- `docs/release/release_candidate_checklist.md`

These cover:

- non-developer end-to-end demo walkthrough
- manual smoke checklist across login/procurement/finance/cashflow/audit/update-safety gates
- release gate checklist for branch/test/build/health/backup/rehearsal/demo status

## Automated RC Smoke Tests Added

Added:

- `backend/tests/test_phase8_release_candidate_smoke.py`

Coverage:

- package coverage fail/pass validation
- locked decision visibility in procurement plan
- invoice metadata package/supplier traceability
- supplier-payment decision endpoint behavior
- cashflow reflection after finance action
- audit log creation for supplier payment lifecycle action

## Verification Commands and Results (Linux Server)

Environment used: `/root/pdss` on `193.162.129.58`

1) Docker status

- Command: `docker compose ps`
- Result:
  - `backend`: Up (healthy)
  - `postgres`: Up (healthy)
  - `frontend`: Up

2) Health endpoint

- Command: `curl -sS http://127.0.0.1:8000/health`
- Result: `{"status":"healthy","version":"1.0.0"}`

3) Full backend tests

- Command: `docker compose run --rm backend python -m pytest tests -q`
- Result: `39 passed, 4 skipped, 38 warnings`

4) Phase 8 smoke tests

- Command: `docker compose run --rm backend python -m pytest tests/test_phase8_release_candidate_smoke.py -q`
- Result: `3 passed, 20 warnings`

5) Frontend build

- Command: `docker compose run --rm frontend npm run build`
- Result: success (`Compiled with warnings`)

## Frontend Warning Budget (Critical Only)

- No new frontend source changes were introduced in Phase 8 implementation.
- Existing eslint warnings remain in previously changed areas from earlier phases.
- Build remains green; warning cleanup was intentionally not expanded to avoid non-scope refactors.

## Documentation Consistency Pass

Updated for consistency:

- `docs/restart-audit/18_user_manual.md`
- `docs/restart-audit/19_developer_manual.md`
- `docs/restart-audit/20_feature_list.md`
- `docs/restart-audit/21_full_application_overview_and_description.md`
- `docs/restart-audit/22_admin_guide.md`
- `docs/restart-audit/23_deployment_guide.md`

Focus:

- package/sub-item and operational finance traceability wording
- canonical test commands including Phase 8 smoke test
- service-name-safe backup command usage
- release/demo readiness references

## Known Limitations

- Frontend build still reports pre-existing eslint warnings in several files.
- Backend test output still includes existing deprecation warnings.
- One SQLAlchemy cartesian-product warning appears in procurement-plan path during tests (non-blocking in current suite).
- Full manual UI walkthrough checklist should still be executed by business reviewers before final sign-off.

## Phase 8 Status

Status: **CLOSED** (code + docs + automated verification complete, demo dataset create/cleanup validated).

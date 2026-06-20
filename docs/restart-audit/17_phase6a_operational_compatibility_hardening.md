# Phase 6A - Operational Compatibility Hardening

## Scope

Implemented the targeted stabilization items identified in `docs/restart-audit/14_existing_operational_modules_regression_audit.md`:

1. Fix supplier payment decision endpoint runtime error.
2. Reconcile procurement-plan payment-in status for decision-field invoice/payment flow.
3. Propagate package/supplier metadata in operational APIs.
4. Add audit logging on key decision/finance/delivery lifecycle actions.
5. Add regression coverage for key package-aware operational paths.

## Implemented Changes

### 1) Supplier payment decision endpoint fix

- File: `backend/app/routers/supplier_payments.py`
- Fixed ORM/schema mix-up by replacing `select(SupplierPayment)` with `select(SupplierPaymentModel)` in:
  - `get_decision_supplier_payments`
  - `update_supplier_payment`
- This removes the SQLAlchemy `ArgumentError` caused by passing a Pydantic schema to `select(...)`.

### 2) Payment-in status reconciliation in procurement plan

- File: `backend/app/routers/procurement_plan.py`
- Added fallback logic so payment-in status can be derived from `finalized_decisions.actual_invoice_*` and `actual_payment_*` fields when invoice/payment table rows are absent.
- Kept table-based status calculation and merged both sources safely (strongest status wins).
- This aligns procurement-plan status with current `invoice_payment_simple` write path.

### 3) Package/supplier metadata propagation

- Files:
  - `backend/app/schemas.py`
  - `backend/app/routers/decisions.py`
  - `backend/app/routers/procurement_plan.py`
  - `backend/app/routers/invoice_payment_simple.py`
  - `backend/app/routers/supplier_payments.py`
- Added/propagated:
  - `package_id`, `package_name`, `package_type`
  - `supplier_id`, `supplier_name`
- Responses now preserve traceability for package-based decisions through operational finance/procurement endpoints.

### 4) Audit writes for key operational actions

- Files:
  - `backend/app/routers/decisions.py`
  - `backend/app/routers/procurement_plan.py`
  - `backend/app/routers/invoice_payment_simple.py`
  - `backend/app/routers/supplier_payments.py`
- Added `log_audit(...)` calls for:
  - decision finalization and status transitions,
  - procurement delivery confirm/accept and invoice entry in procurement-plan flow,
  - invoice create/delete and payment-in create/delete (simple invoice/payment flow),
  - supplier payment create/update/delete.
- Audit calls are non-blocking (errors are swallowed) to avoid operational interruption.

### 5) Regression tests

- New file: `backend/tests/test_phase6a_operational_compat.py`
- Added tests for:
  - supplier-payment decision endpoint retrieval path,
  - procurement-plan payment-in fallback status from decision fields,
  - invoice list metadata propagation (`package_*`, `supplier_*`).
- Updated pre-existing tests:
  - `backend/tests/test_audit_service.py`: feature-flag assertion now aligns with runtime settings.
  - `backend/tests/test_crud_phase3.py`: fixture alignment for package auto-resolution assertions.

## Verification

### Local syntax gate (Windows workspace)

- `python -m compileall app/routers/supplier_payments.py app/routers/procurement_plan.py app/routers/invoice_payment_simple.py app/routers/decisions.py app/schemas.py tests/test_phase6a_operational_compat.py tests/test_audit_service.py tests/test_crud_phase3.py`
  - Result: success (all modified files compile).

### Runtime verification on Linux server (`/root/pdss`)

After syncing the Phase 6A files to the server and rebuilding containers:

1. `docker compose ps`
   - Result: `backend`, `frontend`, `postgres` all up; backend and postgres healthy.
2. `curl -sS http://127.0.0.1:8000/health`
   - Result: `{"status":"healthy","version":"1.0.0"}`
3. `docker compose run --rm backend python -m pytest tests -q`
   - Result: `36 passed, 4 skipped, 37 warnings`
4. `docker compose run --rm frontend npm run build`
   - Result: build succeeded (compiled with existing eslint warnings; no build failure).

### Regression test adjustment during verification

- The first server test run exposed a test harness issue in `test_phase6a_operational_compat.py`:
  - direct function call to `list_invoices(...)` used FastAPI `Query` defaults implicitly.
- Fix applied:
  - explicit parameter values passed in the test call.
- Re-run result:
  - full backend test suite passed (`36 passed, 4 skipped`).

## Phase 6A Status

- Targeted compatibility fixes implemented.
- Full verification set executed successfully on the Linux server with runtime evidence.
- **Phase 6A is closed.**

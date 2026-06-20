# Existing Operational Modules Regression Audit (Post-Phase 5)

## Scope and Baseline

- **Audit intent:** Verify whether Phase 5 package/sub-item work broke or bypassed pre-existing operational modules.
- **Phase 5 baseline commit:** `cc4a9f5`
- **Branch:** `restart/baseline-before-github-push`
- **Validation target:** running server at `193.162.129.58`
- **Important constraint followed:** discovery and regression verification only (no new finance/accounting module build).

## Verification Commands and Results

### Required safe command set

1. `docker compose ps`  
   - **Result:** backend, frontend, postgres containers all up; backend and postgres healthy.
2. `curl http://127.0.0.1:8000/health`  
   - **Result:** `{"status":"healthy","version":"1.0.0"}`
3. `docker compose run --rm backend python -m pytest tests -q`  
   - **Result:** **failed** (`3 failed, 30 passed, 4 skipped`)  
   - **Failing tests:** `test_audit_service`, `test_crud_phase3` package auto-resolution assertions.
4. `docker compose run --rm frontend npm run build`  
   - **Result:** build succeeded with existing lint warnings.

### Runtime regression workflow replay (package path)

Executed a focused smoke flow with temporary fixture data:
- Created package-based fixture decisions (fail + pass lock cases).
- Verified lock behavior:
  - fail case: HTTP 400 (incomplete sub-item coverage)
  - pass case: lock successful.
- Entered invoice, supplier payment, and customer payment for package-based locked decision.
- Verified dashboard/reports reflected inserted payment/invoice data.
- Cleaned fixture data after verification.

## Capability Map (Evidence-Based)

## 1) Purchase / Procurement Plan Tracking

- **Backend model/table:** `finalized_decisions`, `project_items`, `delivery_options`
- **Router/API:** `backend/app/routers/procurement_plan.py` (`/procurement-plan/*`)
- **CRUD/service path:** router-local query logic + payment status helpers
- **Frontend:** `frontend/src/pages/ProcurementPlanPage.tsx`
- **Workflow status:** operational for listing, delivery confirmation, PM acceptance.
- **Post-Phase5 status:** still operational for locked package-based decisions.
- **Package-awareness:** **partial** (package-based decisions appear, but package metadata is not exposed in procurement-plan response).

## 2) Proforma Purchase Records

- **Implementation evidence:** no explicit `proforma` entity/endpoint found.
- **Nearest functional equivalent:** forecast invoice fields on `finalized_decisions` (`forecast_invoice_*`) and delivery-option invoice timing.
- **Status:** concept exists as forecast timing/amount, not as dedicated proforma module.
- **Package-awareness:** inherited through `finalized_decisions.package_id`, not a separate package-aware proforma API.

## 3) Purchase Invoice Records

- **Backend model/table:** `invoices` table exists (`backend/app/models_invoice_payment.py`), plus legacy invoice fields on `finalized_decisions`.
- **Router/API:** `backend/app/routers/invoice_payment_simple.py` (`/api/invoice-payment/invoices`)
- **CRUD/service path:** router updates `finalized_decisions` directly (not full table-centric invoice flow)
- **Frontend:** `frontend/src/components/InvoicePaymentManagement.tsx` (Invoices tab), `frontend/src/pages/FinancePage.tsx`
- **Workflow status:** create/list/delete operational.
- **Post-Phase5 status:** operational in smoke test.
- **Package-awareness:** **limited** (no package metadata in invoice API response).

## 4) Sales Invoice Records (if present)

- **Evidence:** no separate sales-invoice module/table naming found.
- **Functional mapping:** invoice/payment-in flow behaves as customer inflow tracking.
- **Status:** present as generic invoice/payment flow tied to decisions.

## 5) Supplier Payment Tracking

- **Backend model/table:** `supplier_payments` (includes `package_id` and `supplier_id` columns)
- **Router/API:** `backend/app/routers/supplier_payments.py` (`/supplier-payments/*`)
- **CRUD/service path:** router + `CashflowSyncService.sync_payment_out`
- **Frontend:** `frontend/src/components/InvoicePaymentManagement.tsx` (Payments Out tab)
- **Workflow status:** list/create/delete work.
- **Post-Phase5 status:** partially working; one endpoint is broken.
- **Package-awareness:** schema supports it, runtime API does not propagate it.

## 6) Customer Receipt / Cash-In Tracking

- **Backend model/table:** `payments` table + `finalized_decisions.actual_payment_*` fields
- **Router/API:** `backend/app/routers/invoice_payment_simple.py` (`/api/invoice-payment/payments`)
- **CRUD/service path:** router writes decision payment fields and creates cashflow INFLOW
- **Frontend:** `InvoicePaymentManagement` (Payments In tab)
- **Workflow status:** create/list/delete works.
- **Post-Phase5 status:** operational, but status integration mismatch exists in procurement plan (see regressions).
- **Package-awareness:** **no explicit package fields** in payment API responses.

## 7) Cashflow Events

- **Backend model/table:** `cashflow_events`
- **Router/API:** `backend/app/routers/dashboard.py`, `analytics.py`, `reports.py`
- **Service:** `backend/app/cashflow_sync_service.py`
- **Frontend:** `DashboardPage`, `ReportsPage`, `AnalyticsDashboardPage`
- **Workflow status:** operational; reflects payment in/out transactions.
- **Post-Phase5 status:** verified with package-based decision smoke flow (inflow/outflow reflected).
- **Package-awareness:** indirect via `related_decision_id`; no package-first reporting dimensions.

## 8) Delivery Confirmation

- **Backend model/table:** delivery fields on `finalized_decisions`
- **Router/API:** `/procurement-plan/{decision_id}/confirm-delivery`
- **Frontend:** `ProcurementPlanPage` confirm action
- **Status:** implemented and routable.
- **Package-awareness:** indirect through decision linkage.

## 9) PM Acceptance / Handover

- **Backend model/table:** PM acceptance fields on `finalized_decisions`
- **Router/API:** `/procurement-plan/{decision_id}/accept-delivery`
- **Frontend:** `ProcurementPlanPage` accept action
- **Status:** implemented and routable.
- **Package-awareness:** indirect through decision linkage.

## 10) Audit Logs

- **Backend model/table:** `audit_logs`
- **Router/API:** `backend/app/routers/audit.py` (`/audit-logs`)
- **Write path:** `crud.log_audit` used by auth/projects/items/items_master/procurement/delivery_options/suppliers
- **Frontend:** `frontend/src/pages/AuditLogsPage.tsx`
- **Status:** audit log module exists and works for covered actions.
- **Post-Phase5 status:** operational but incomplete coverage (finance and decision lifecycle actions missing).
- **Package-awareness:** no dedicated package-action audit enrichment.

## 11) Reports and Dashboards

- **Backend router/API:** `/dashboard/*`, `/reports/*`, `/analytics/*`
- **Frontend:** `DashboardPage`, `ReportsPage`, `AnalyticsDashboardPage`
- **Status:** operational.
- **Post-Phase5 status:** still works; reflects newly created invoice/payment counts and cashflow sums.
- **Package-awareness:** mostly item/decision-centric; package-specific columns/filters are not exposed.

## Phase 5 Impact and Regression Analysis

## Git impact around Phase 5

`cc4a9f5` touched package/decision/optimization/config/test files (for example `backend/app/routers/decisions.py`, `backend/app/services/package_service.py`, optimizers, feature flag config).  
It did **not** directly modify `procurement_plan.py`, `invoice_payment_simple.py`, `supplier_payments.py`, `dashboard.py`, `reports.py`, or `audit.py`.

Interpretation: most operational module issues found are likely pre-existing or surfaced by package-path execution, not newly introduced by direct edits in those modules.

## Confirmed regressions / integration gaps

1. **Broken API:** `GET /supplier-payments/decisions/{decision_id}/payments` returns 500.  
   - **Runtime evidence:** backend log shows SQLAlchemy error using schema class in `select(...)`.
   - **Code evidence:** `backend/app/routers/supplier_payments.py` uses `select(SupplierPayment)` where `SupplierPayment` is schema import, not ORM model.

2. **Payment-In status mismatch in procurement plan:**  
   - After creating invoice + payment-in through `/api/invoice-payment/*`, `procurement-plan/{id}` still shows `payment_in_status = not_paid`.
   - **Root cause:** procurement-plan status calculator reads `Invoice`/`Payment` tables, while `invoice_payment_simple` writes mostly to `finalized_decisions` fields.

3. **Package traceability loss in operational finance APIs/UI:**  
   - Package decision exists (`decision.package_id` set), but procurement-plan and invoice/payment/supplier-payment responses do not expose package context.
   - `supplier_payments` create flow does not populate `package_id`/`supplier_id` despite model columns existing.

4. **Audit coverage gap for operational actions:**  
   - No audit rows for decision finalization, invoice creation/payment entry, supplier payment creation, or procurement-plan transitions in this path.

## Package-Based Integration Check (Key Question)

- **Is package-based decision visible in procurement plan?**  
  - Yes, package-backed locked decisions are listed in procurement plan.
- **Can invoice/payment be entered for package-based decision?**  
  - Yes, via decision-driven finance endpoints.
- **Is supplier traceability preserved?**  
  - Partial at best; decision payload can miss supplier context, and supplier payment endpoint by decision is broken.
- **Is package traceability preserved?**  
  - No end-to-end; package context is not propagated in core finance API responses/UI.
- **Does cashflow include package decision/payment data?**  
  - Yes indirectly via `related_decision_id`.
- **Does audit log capture package decision + financial actions?**  
  - Not for the tested decision/finance flow.
- **Are APIs still assuming item-level records?**  
  - Yes in practical behavior for invoice/payment/supplier-payment responses and procurement-plan payload shape.
- **Are frontend pages failing due to item-level assumptions?**  
  - No hard UI crash observed in this audit flow, but package context is absent.

## What Should Not Be Rebuilt

Do **not** rebuild:
- invoice/payment subsystem,
- supplier payment subsystem,
- cashflow dashboard/reporting subsystem,
- audit-log module.

These modules already exist and are broadly operational. The right path is targeted compatibility and regression hardening.

## Small Compatibility Fixes (Recommended)

1. Fix `supplier-payments` decision-specific endpoint to use ORM model consistently.
2. Unify payment-in status logic:
   - either persist true `invoices/payments` rows in simple flow,
   - or make procurement-plan status fallback to `finalized_decisions.actual_*` fields.
3. Add package/supplier metadata propagation in operational responses (procurement-plan, invoice/payment, supplier-payment).
4. Add audit writes for decision finalize/status change, invoice/payment create/delete, supplier payment create/delete, delivery confirm/accept.
5. Add regression tests for package-decision -> invoice/payment/cashflow/procurement-plan path.

## Conclusion: Proceed / Not Proceed

- **Can proceed to next phase?** **Yes, with caution.**  
- Core operational modules exist and still run after Phase 5.
- However, at least two concrete compatibility regressions/gaps should be treated as a short stabilization sub-phase before larger new feature work.

## Suggested Next Phase

**Phase 6A: Operational Compatibility Hardening (small, targeted)**  
Focus only on:
- supplier-payment decision endpoint fix,
- payment status reconciliation fix,
- package metadata propagation and minimal UI display,
- audit coverage for decision/finance lifecycle,
- regression test additions for these paths.

# Phase 9 UAT Defect Log

Environment: isolated demo instance on `193.162.129.58`  
Frontend: `http://193.162.129.58:13010`  
Backend: `http://193.162.129.58:18010`

## Defects

### UAT-05

- ID: `UAT-05`
- Title: Package list endpoint failed with 500
- Module: projects / package listing (`GET /projects/{project_id}/packages`)
- Steps to reproduce:
  1. Login as admin.
  2. Open demo project package list.
  3. Request `GET /projects/{project_id}/packages?active_only=true`.
- Expected behavior: Package list returns 200 with package/supplier/sub-item data.
- Actual behavior: 500 internal server error due response serialization (`MissingGreenlet` lazy-load on `supplier` / `subitems`).
- Severity: `major`
- Business impact: Blocks supplier package review step in business demo flow.
- Recommended action: Eager-load required relationships in endpoint query.
- Status: `Closed - fixed in Phase 9`
- Fix applied: `backend/app/routers/projects.py` now uses `selectinload` for package `supplier` and `subitems`.

### UAT-12

- ID: `UAT-12`
- Title: Invoice/payment step failed in first UAT probe run
- Module: UAT harness path mapping
- Steps to reproduce:
  1. Execute first probe using `/invoice-payments/*` path.
  2. Receive `404 Not Found`.
- Expected behavior: Invoice/payment endpoints resolve and create records.
- Actual behavior: Probe used outdated path; active API prefix is `/api/invoice-payment`.
- Severity: `minor`
- Business impact: Test harness false failure, no production regression.
- Recommended action: Update probe paths to canonical API prefix.
- Status: `Closed - test harness corrected`
- Fix applied: Updated UAT probe to call `/api/invoice-payment/invoices` and `/api/invoice-payment/payments`.

## Open Defects Summary

- Blocker: `0`
- Major: `0`
- Minor: `0`
- Cosmetic: `0`

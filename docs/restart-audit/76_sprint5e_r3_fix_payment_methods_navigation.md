# Sprint 5E-R3-Fix - Payment Methods Navigation Regression and Deployment Provenance Cleanup

**Status:** PASS  
**Date:** 2026-06-27  
**Sprint name:** Sprint 5E-R3-Fix - Payment Methods Navigation Regression and Deployment Provenance Cleanup

## Baseline

| Item | Value |
|------|-------|
| Starting branch | `restart/sprint5e-r3-bulk-remove-procurement-assignments` |
| Starting commit | `378497172a11d0035c16908e4f618067128fe627` |
| New branch | `restart/sprint5e-r3-fix-payment-methods-navigation` |

## User-reported runtime issue

- In `/opt/rivar-demo`, Payment Methods was no longer visible under Base Information / Master Data.
- User expected behavior from accepted 5C-R4-Fix-3 model: authorized users can view/use Payment Methods, unauthorized users remain denied.

## Diagnosis summary

### Root cause

- `PaymentMethodsManager` and backend `/payment-methods` RBAC endpoints were still present.
- Frontend wiring regressed:
  - no Payment Methods child entry in `Layout` Base Information navigation;
  - no `/payment-methods` route in `App.tsx`;
  - Payment Methods manager became effectively orphaned/unreachable from navigation.

### Runtime evidence before fix

- On deployed source in `/opt/rivar-demo`:
  - `frontend/src/components/Layout.tsx` had no Payment Methods nav entry;
  - `frontend/src/App.tsx` had no `/payment-methods` route;
  - `frontend/src/components/finance/PaymentMethodsManager.tsx` existed.
- Deployment provenance markers were contradictory before this sprint:
  - root marker referenced 5E-R3;
  - docs marker referenced 5F.

## Expected RBAC behavior (locked)

1. **admin/system_admin**
   - Payment Methods visible under Base Information.
   - Payment Methods page reachable.
   - `/payment-methods` API allowed.
2. **explicit permission user**
   - `master_data.payment_methods.view` required for visibility and page access.
   - action gating:
     - create: `master_data.payment_methods.create`
     - edit: `master_data.payment_methods.edit`
     - delete/deactivate: `master_data.payment_methods.delete`
3. **unauthorized**
   - access-control-only user must not see/access Payment Methods.
   - procurement assignment view-only user must not see/access Payment Methods.
   - backend denies unauthorized Payment Methods API calls.

## Fix applied (minimal scoped)

- Restored Payment Methods navigation and route:
  - added Base Information child nav item (`/payment-methods`) in `Layout`;
  - added protected route `/payment-methods` in `App.tsx`;
  - added `PaymentMethodsRoute` guard component;
  - added `PaymentMethodsPage` wrapper for header + section content.
- Hardened frontend payment-method permission helpers:
  - removed legacy broad role fallback for Payment Methods;
  - admin bypass preserved;
  - explicit permission checks introduced for view/create/edit/delete.
- Enforced granular UI action gating in `PaymentMethodsManager`:
  - Add button only with create permission;
  - Edit icon only with edit permission;
  - Deactivate icon only with delete permission.
- Added/updated i18n keys for Payment Methods navigation label.
- Added focused tests for nav visibility, route guard, page rendering, and action gating.

## Changed files

- `frontend/src/App.tsx`
- `frontend/src/components/Layout.tsx`
- `frontend/src/components/PaymentMethodsRoute.tsx`
- `frontend/src/components/PaymentMethodsRoute.test.tsx`
- `frontend/src/components/Layout.masterDataNavigation.test.tsx`
- `frontend/src/components/finance/PaymentMethodsManager.tsx`
- `frontend/src/components/finance/PaymentMethodsManager.test.tsx`
- `frontend/src/pages/PaymentMethodsPage.tsx`
- `frontend/src/pages/PaymentMethodsPage.test.tsx`
- `frontend/src/utils/permissions.ts`
- `frontend/src/i18n/en.json`
- `frontend/src/i18n/fa.json`
- `deployment/rivar-installer/deploy_update_5e_r3_fix.sh`

## Focused tests (resource-safe)

Executed without watch mode / coverage / broad loops:

- `src/components/Layout.masterDataNavigation.test.tsx` PASS
- `src/components/PaymentMethodsRoute.test.tsx` PASS
- `src/pages/PaymentMethodsPage.test.tsx` PASS
- `src/components/finance/PaymentMethodsManager.test.tsx` PASS
- `src/pages/ProcurementPage.workbenchUx.test.ts` PASS
- `src/pages/ProcurementPage.secureAssignedItems.test.ts` PASS
- `src/components/PackageWizard/PackageWizardStep3.test.tsx` PASS

## Runtime deploy and smoke (/opt/rivar-demo)

### Deploy target and constraints

- Official host: `193.162.129.58`
- Path: `/opt/rivar-demo`
- Compose project: `rivar-demo`
- Forbidden path not used: `/root/pdss_demo`

### Deploy/verify result

- Applied runtime patch and executed:
  - `deployment/rivar-installer/deploy_update_5e_r3_fix.sh`
  - `deployment/rivar-installer/verify.sh`
- `verify.sh`: PASS (after one transient frontend connection-reset during immediate startup; rerun passed clean).

### Runtime checks

- `/health`: 200
- `/openapi.json`: 200
- Admin login: 200
- Backend Payment Methods RBAC:
  - admin `GET /payment-methods`: 200
  - payment_methods.view user `GET /payment-methods`: 200
  - access-control-only user `GET /payment-methods`: 403
  - procurement assignment view-only user `GET /payment-methods`: 403
- Regression checks:
  - procurement assigned-items safe endpoint (`/procurement-assignments/my-assigned-items`) for view-only user: 200
  - direct project items endpoint (`/items/project/{project_id}`) for same user: 403
  - procurement assignment smoke in deploy script (create/list/cancel): PASS
- Deployed frontend source now includes:
  - Payment Methods nav entry in `Layout`;
  - `/payment-methods` route guarded by `PaymentMethodsRoute` in `App.tsx`.

## Deployment provenance cleanup

- **Authoritative marker:** `/opt/rivar-demo/DEPLOYED_COMMIT.txt`
- Transitional compatibility marker retained and mirrored:
  - `/opt/rivar-demo/docs/restart-audit/DEPLOYED_COMMIT.txt`
- During this sprint deploy, both markers are synchronized and non-contradictory.
- Marker format used:
  - `branch=restart/sprint5e-r3-fix-payment-methods-navigation`
  - `commit=<full commit>`
  - `deployed_at=<UTC timestamp>`
  - `sprint=5E-R3-Fix`

## Scope exclusions honored

- No Sprint 5F procurement scope enforcement started.
- No Package Wizard behavior changes.
- No optimization/cashflow/decision logic changes.
- No procurement assignment logic changes beyond regression checks.
- No Master Data RBAC weakening.

## Remaining risks

1. Frontend route curl checks for SPA deep links may report unauthenticated backend status when called without browser session context; route wiring is validated via source + focused tests.
2. Runtime provenance commit field must be finalized with the sprint closure commit hash after git closure.

## Compile hotfix: ProcurementPage Permission Helper Compile Fix

### Error

- Runtime frontend compile blocker after refresh:
  - `export 'isAssignedOnlyProcurementScopeUser' was not found in '../utils/permissions.ts'`
  - `export 'isGlobalProcurementScopeUser' was not found in '../utils/permissions.ts'`

### Root cause

- On deployed source under `/opt/rivar-demo`:
  - `frontend/src/pages/ProcurementPage.tsx` imported `isAssignedOnlyProcurementScopeUser` and `isGlobalProcurementScopeUser`.
  - `frontend/src/utils/permissions.ts` did not export these helpers.
- This mismatch was introduced by earlier scope-enforcement branch history and caused webpack compile failure in runtime.

### Minimal fix

- Added back exports in `frontend/src/utils/permissions.ts` only:
  - `isGlobalProcurementScopeUser(user)`
  - `isAssignedOnlyProcurementScopeUser(user)`
  - `GLOBAL_PROCUREMENT_SCOPE_PERMISSION_KEYS` constant
  - corresponding `usePermissions()` accessors
- Semantics preserved:
  - admin bypass remains;
  - global scope requires assignment-management/project-items grants;
  - assigned-only requires `procurement.assignments.view` and not global;
  - access-control-only users remain non-procurement-scope by default.
- No package wizard / optimization / cashflow / decisions / master-data behavior changes in this hotfix.

### Compile hotfix verification

- Focused local tests:
  - `src/utils/procurementAssignmentPermissions.test.ts` PASS
  - `src/pages/ProcurementPage.workbenchUx.test.ts` PASS
  - `src/pages/ProcurementPage.secureAssignedItems.test.ts` PASS
  - `src/components/Layout.masterDataNavigation.test.tsx` PASS
  - `src/components/PackageWizard/PackageWizardStep3.test.tsx` PASS
- Local build:
  - `npm run build` PASS (with existing pre-existing lint warnings; no missing-export compile errors)
- Runtime deploy:
  - frontend rebuilt on `/opt/rivar-demo` using installer deploy flow
  - `verify.sh` PASS
- Runtime smoke:
  - `/health` 200, `/openapi.json` 200
  - helper mismatch resolved on deployed source (`ProcurementPage` imports present and `permissions.ts` exports present)
  - `/#/procurement` 200
  - payment-method RBAC checks unchanged (admin/view user 200, AC-only/proc-view-only 403)
  - safe assigned item endpoint 200 and direct project-items denial 403 for procurement view-only account
  - Package Wizard readiness endpoint `/procurement-options/81/readiness` 200

## Git provenance

- Branch: `restart/sprint5e-r3-fix-payment-methods-navigation`
- Commit/push provenance: recorded in sprint closure commands and final QA report.

## Recommendation

**Proceed to Sprint 5F - Procurement Assignment Scope Enforcement and Procurement Workflow Filtering**

# Sprint 5E-R4 — Finalized-Only Procurement Assignment Item Visibility

**Status:** PASS  
**Date:** 2026-06-27  
**Sprint name:** Sprint 5E-R4 — Finalized-Only Procurement Assignment Item Visibility

## Baseline

| Item | Value |
|------|-------|
| Starting branch | `restart/sprint5e-r3-fix-payment-methods-navigation` |
| Starting commit | `5d4874a0010010ed34b37c526c0c1abf1b656949` |
| New branch | `restart/sprint5e-r4-finalized-only-assignment-items` |
| Working-tree cleanup | stashed as `pre-5e-r4-cleanup-backup` before branch creation |

## Product-owner rule implemented

- Project-level procurement assignment remains allowed even when no project items are finalized.
- Item-level visibility, picker selection, and item-level assignment creation now require finalized project items only.
- Newly finalized items become visible for existing project-level assignees without creating synthetic item-level assignments.
- Non-finalized items are not exposed in assignment-oriented item views.

## Finalization field/status discovered

- Canonical finalization signal: `project_items.is_finalized` (`ProjectItem.is_finalized` in SQLAlchemy model and API schemas).
- Finalization lifecycle endpoints remain unchanged (`/items/{id}/finalize`, `/items/{id}/unfinalize`, `/items/project/{id}/finalize-all`).
- Sprint scope only consumed the existing finalization flag for filtering and validation.

## Backend behavior changes

### 1) Item-level assignment validation

File: `backend/app/services/procurement_assignment_service.py`

- Added finalized-state validation in `_ensure_project_item_belongs(..., require_finalized=True)`.
- `POST /procurement-assignments` now rejects non-finalized `project_item_id` with 400 and clear message.
- `POST /procurement-assignments/bulk` now rejects payload when any selected item is non-finalized (safe fail-fast behavior).
- Project-level assignment path is unchanged and still allowed with no finalized items.

### 2) Safe assigned-items finalized filtering

File: `backend/app/services/procurement_assigned_items_service.py`

- Project-level expansion now loads only finalized `ProjectItem` rows.
- Item-level hydration now returns only finalized `ProjectItem` rows.
- Applied to:
  - `GET /procurement-assignments/my-assigned-items`
  - `GET /procurement-assignments/assigned-items`
  - `GET /procurement-assignments/projects/{project_id}/assigned-items`
- Sensitive-field allowlist from Sprint 5E-R2-Fix remained unchanged.

## Frontend behavior changes

### 1) Workbench item loading and visibility

File: `frontend/src/components/procurement/ProcurementAssignmentManagementPanel.tsx`

- Project item loading now requests finalized-only rows (`is_finalized: true`) and persists finalized-only item maps.
- Item-level workbench assignments are filtered so non-finalized item-level rows do not render in assignment views.
- Added finalized-only helper alerts and project-level future-finalized guidance in assignment dialog.
- Added no-finalized-items message for item-level assignment context.

### 2) View by Project UI

File: `frontend/src/components/procurement/ProcurementAssignmentProjectView.tsx`

- Assignment table renders finalized items only.
- Added explicit empty-state message when no finalized items exist for item-level assignment.
- Updated assign-all label to finalized-specific wording.

### 3) My Assignments non-finalized suppression

File: `frontend/src/components/procurement/MyProcurementAssignmentsPanel.tsx`

- Panel now uses safe assigned-items endpoint results to determine visible item-level chips.
- Item-level chips for non-finalized items are suppressed for procurement view users.

### 4) UX wording updates (EN/FA)

Files:
- `frontend/src/i18n/en.json`
- `frontend/src/i18n/fa.json`

Added/updated:
- EN: `Assign all finalized project items`
- FA: `تخصیص همه اقلام نهایی‌شده پروژه`
- EN helper: `Only finalized project items are available for item-level procurement assignment.`
- FA helper: `فقط اقلام نهایی‌شده پروژه برای تخصیص آیتمی تأمین نمایش داده می‌شوند.`
- EN empty-state: `No finalized items are available for item-level assignment yet.`
- FA empty-state: `هنوز هیچ قلم نهایی‌شده‌ای برای تخصیص آیتمی وجود ندارد.`
- Project-level guidance text in both locales for future-finalized item visibility.

## Security/permission preservation

- Procurement assignment RBAC permissions preserved.
- Direct Project Items deny for procurement view-only users preserved (`project_items.view` guard unchanged).
- Sensitive-field minimization for safe assigned-item APIs preserved.
- Master Data RBAC behavior preserved (admin allowed, access-control-only denied).
- Package Wizard behavior unchanged.

## Tests run (focused/resource-safe)

### Backend focused tests

Command:

`python -m pytest tests/test_phase15d_procurement_assignment_backend.py tests/test_phase15e_r2_fix_secure_assigned_item_visibility.py -q`

Result:

- **23 passed**
- Added validation and finalized-filter coverage:
  - project-level allowed before finalization
  - item-level non-finalized rejection
  - bulk non-finalized rejection
  - project-level assigned-items finalized-only expansion
  - newly finalized item visibility under project-level assignment

### Frontend focused tests

Command:

`npm test -- --watchAll=false --runInBand src/pages/ProcurementPage.workbenchUx.test.ts src/pages/ProcurementPage.secureAssignedItems.test.ts src/components/Layout.masterDataNavigation.test.tsx src/components/PackageWizard/PackageWizardStep3.test.tsx`

Result:

- **4 suites passed, 26 tests passed**

### Frontend compile check

Command:

`npm run build`

Result:

- Build succeeded (existing workspace-wide lint warnings remain outside sprint scope).

## Runtime deployment and smoke (`/opt/rivar-demo`)

### Deployment path and compose safety

- Official path used: `/opt/rivar-demo`
- Compose project: `rivar-demo`
- Forbidden path `/root/pdss_demo` was not used.

### Deploy actions

- Added and executed `deployment/rivar-installer/deploy_update_5e_r4.sh`.
- Rebuilt backend + frontend containers and restarted stack.
- Ran `deployment/rivar-installer/run_sprint5d_smoke.sh` inside deploy script.
- Ran `deployment/rivar-installer/verify.sh` (second retry after transient frontend reset) -> PASS.

### Runtime smoke checks (5E-R4 specific)

Script: `backend/scripts/sprint5e_r4_runtime_smoke.py`

All required checks passed:

- `/health` 200
- `/openapi.json` 200
- Frontend and procurement route load 200 (no compile blocker)
- Project-level assignment allowed before any finalized item
- Item-level assignment to non-finalized item denied (400)
- Bulk item assignment containing non-finalized item denied (400)
- Non-finalized items hidden from `my-assigned-items` and assigned-items project/flat endpoints
- Newly finalized item appears for existing project-level assignee
- Safe assigned-item response remained sanitized (no sensitive financial/customer/revenue/margin keys)
- Direct Project Items denied for procurement view-only user (403)
- Bulk remove/cancel assignment path still operational
- Payment Methods regression remained fixed (admin 200, AC-only 403)
- Package Wizard Step 3 readiness endpoint remained healthy
- 5F enforcement not started (`/items/finalized` still reachable for procurement view user)

## verify.sh result

- `deployment/rivar-installer/verify.sh` -> **PASS**

## Scope exclusions honored

- Sprint 5F broad procurement scope enforcement not started.
- No optimization/cashflow/decision workflow behavior changes.
- No Package Wizard behavior changes.
- No project item finalization business process changes (only consumed existing finalization flag).
- No Master Data RBAC model changes.

## Remaining risks / notes

1. Finalize endpoint eligibility rules can block finalization until procurement-eligibility prerequisites are satisfied (expected behavior).  
   Runtime smoke used SQL fallback strictly to validate post-finalization assignment visibility after API-level eligibility rejection.
2. Frontend workspace has broad pre-existing lint warnings unrelated to this sprint.

## Git provenance

- Commit hash: `c956e503d8151b5ab008d5319695d2d32da512f9`
- Pushed branch: `origin/restart/sprint5e-r4-finalized-only-assignment-items`
- Remote branch verification: `git ls-remote origin refs/heads/restart/sprint5e-r4-finalized-only-assignment-items` -> match

## Recommendation

**Proceed to Sprint 5F — Procurement Assignment Scope Enforcement and Procurement Workflow Filtering**

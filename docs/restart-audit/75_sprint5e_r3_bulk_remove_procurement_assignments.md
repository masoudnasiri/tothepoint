# Sprint 5E-R3 - Bulk Remove Procurement Assignments

**Status:** PASS  
**Date:** 2026-06-27  
**Sprint name:** Sprint 5E-R3 - Bulk Remove Procurement Assignments

## Baseline

| Item | Value |
|------|-------|
| Starting branch | `restart/sprint5e-r2-fix-r1-secure-item-runtime-closure` |
| Starting commit | `e9dc5b4ee513da3a51f142264bd02614fe617d29` |
| New branch | `restart/sprint5e-r3-bulk-remove-procurement-assignments` |
| Implementation commit | `7176f27090c1513675c58a103ba1a70b18d51c71` |

## Product-owner feedback captured

- Procurement Assignment workbench already supported grouped assignment.
- Group removal of existing active assignments was missing in practice for mixed project/item scenarios.
- Assignment action semantics must stay as **remove/cancel responsibility**, not **complete procurement workflow**.

## Selection behavior and UX clarification

- Added explicit split between:
  - selected assignable items
  - selected removable assignments
- Assignable rows are now strictly rows without active assignment:
  - no active item-level assignment on that item
  - no active project-level assignment covering the project
- Removable rows are active assignments only.
- Completed and cancelled assignments are excluded from removal selection.
- Assign checkboxes are disabled for non-assignable rows to reduce ambiguity.

## Bulk remove behavior

- Bulk remove action label remains:
  - EN: `Remove selected assignments`
  - FA: `حذف تخصیص‌های انتخاب‌شده`
- Action appears only when at least one removable active assignment is selected and cancel permission exists.
- Confirmation dialog now includes assignment count and keeps cancellation reason required.
- Bulk remove executes real backend cancel endpoint per assignment (sequential API calls).
- Partial-failure summary includes success/failure counts and failed assignment IDs.
- After action:
  - list refreshes
  - selection clears
  - cancelled records leave active filter and appear in cancelled/history filter

## Project-level and item-level removal support

- View by Project now includes active project-level assignments in removal selection.
- View by Item keeps active-only row selection for cancellation.
- Single-row remove keeps same wording and same cancel endpoint semantics.

## Permissions and RBAC enforcement

- Remove action remains gated by `canCancelProcurementAssignments`.
- View-only procurement users cannot remove/cancel assignments.
- Access-control admin users without assignment permissions cannot remove/cancel assignments.
- Legacy non-admin roles do not bypass procurement assignment RBAC checks.

## Explicit exclusions honored

- No reintroduction of "Complete assignment" as a primary workbench action.
- No Sprint 5F scope enforcement started in this sprint.
- No assignment management move back to Project Items.
- No Package Wizard, optimization send workflow, or master-data behavior changes beyond regression checks.

## Changed files

- `frontend/src/components/procurement/ProcurementAssignmentManagementPanel.tsx`
- `frontend/src/components/procurement/ProcurementAssignmentProjectView.tsx`
- `frontend/src/utils/procurementAssignmentWorkbenchUtils.ts`
- `frontend/src/i18n/en.json`
- `frontend/src/i18n/fa.json`
- `frontend/src/utils/procurementAssignmentWorkbenchUtils.test.ts`
- `frontend/src/utils/procurementAssignmentPermissions.test.ts`
- `frontend/src/pages/ProcurementPage.workbenchUx.test.ts`
- `deployment/rivar-installer/deploy_update_5e_r3.sh`

## Focused tests (resource-safe)

| Test | Result |
|------|--------|
| `procurementAssignmentWorkbenchUtils.test.ts` | PASS (6/6) |
| `procurementAssignmentPermissions.test.ts` | PASS (5/5) |
| `ProcurementPage.workbenchUx.test.ts` | PASS (6/6) |
| `ProcurementPage.secureAssignedItems.test.ts` | PASS (4/4) |

Notes:
- No watch mode.
- No coverage run.
- No broad/repeated Jest loops.

## Runtime deployment and smoke (/opt/rivar-demo)

### Deployment identity

- Target path: `/opt/rivar-demo`
- Compose project: `rivar-demo`
- Forbidden path usage: none (`/root/pdss_demo` not used)
- Deployed branch: `restart/sprint5e-r3-bulk-remove-procurement-assignments`
- Deployed commit: `7176f27090c1513675c58a103ba1a70b18d51c71`
- Root marker updated: `/opt/rivar-demo/DEPLOYED_COMMIT.txt`
- Audit marker updated: `/opt/rivar-demo/docs/restart-audit/DEPLOYED_COMMIT.txt`

### Deployment steps

1. Built tarball from exact commit `7176f27090c1513675c58a103ba1a70b18d51c71`.
2. Uploaded tarball to server with deploy key `id_rivar_deploy_temp`.
3. Extracted into `/opt/rivar-demo`.
4. Normalized installer scripts to LF on server.
5. Executed `deployment/rivar-installer/deploy_update_5e_r3.sh` (frontend rebuild, backend reused).
6. Executed `deployment/rivar-installer/verify.sh`.

### Runtime smoke results

- `/health`: 200
- `/openapi.json`: 200
- Admin login: PASS
- `/auth/me`: PASS
- Frontend root app load: 200
- Procurement Assignments API load: PASS
- View by Project filter API: PASS
- View by Item filter API: PASS
- Assign selected items (bulk create): PASS (201)
- Multiple active assignment selection and sequential cancel simulation: PASS
- Cancelled assignments removed from active filter: PASS
- Cancelled assignments present in cancelled/history filter: PASS
- View-only procurement user cancel attempt: denied (403)
- Access-control admin cancel attempt: denied (403)
- Safe assigned-items view endpoint: PASS (200, sanitized keys only)
- Direct Project Items for procurement view-only user: denied (403)
- Master Data RBAC checks (AC-only denied, admin allowed): PASS
- Package Wizard Step 3 proxy check (`/procurement-options/{id}/readiness`): PASS (200)
- 5F enforcement not started (`/items/finalized` still reachable for procurement view user): confirmed

## Safe assigned-item visibility regression

- Sprint 5E-R2-Fix protections preserved.
- Procurement view-only user remains blocked from direct Project Items APIs/routes.
- Sanitized assigned-items API remains active and excludes sensitive fields.

## verify.sh result

- `verify.sh`: PASS
- Includes compose health checks, fixture reseed, and Sprint 3A-R3 runtime verification path.

## Git provenance

- Local branch: `restart/sprint5e-r3-bulk-remove-procurement-assignments`
- Committed implementation hash: `7176f27090c1513675c58a103ba1a70b18d51c71`
- Pushed to origin branch: yes
- Remote branch verification: completed in sprint closure commands

## Remaining risks / follow-up

1. `/items/finalized` data minimization/enforcement is still intentionally deferred to Sprint 5F.
2. Existing historical fixture accounts may still include broader legacy grants; runtime checks used strict role construction for authoritative deny tests.

## Recommendation

**Proceed to Sprint 5F - Procurement Assignment Scope Enforcement and Procurement Workflow Filtering**

# Sprint 5E-R1 — Procurement Assignment UX Relocation to Procurement Module

**Status:** PASS WITH MINOR ISSUES  
**Date:** 2026-06-26  
**Sprint name:** Sprint 5E-R1 — Procurement Assignment UX Relocation to Procurement Module

## Baseline

| Item | Value |
|------|-------|
| Starting branch | `restart/sprint5e-procurement-assignment-frontend-scoped-ux` |
| Starting commit | `c3ae9baf72ed5e5fbea4bde932e9405be88d788b` |
| New branch | `restart/sprint5e-r1-procurement-assignment-ux-relocation` |

## Product-owner feedback

Sprint 5E placed procurement assignment management primarily inside **Project Items**, which does not match the intended product flow. Assignment management should live in the **Procurement module**, similar to how PMO/project workflows stay in their domain.

## Old placement issue

- Full assignment tab on `/projects/:projectId/items`
- Bulk assign from item checkboxes
- Create/complete/cancel primarily from project context

## New Procurement-module placement

| Surface | Location | Role |
|---------|----------|------|
| **Primary management** | `/procurement` → tab **Procurement Assignments** / **تخصیص تأمین** | PMO/PM/admin with assignment permissions |
| **My Assignments** | Same tab for view-only procurement users | Procurement specialists |
| **Operations** | `/procurement` → tab **Procurement Operations** | Existing package/procurement work (unchanged) |

Component: `ProcurementAssignmentManagementPanel` — global assignment board with filters (project, assignee, status, scope), create dialog (project + scope + items + users), complete/cancel, history.

Deep link from project summary: `/procurement?tab=assignments&projectId={id}`

## Project / Project Items remaining behavior

**Read-only summary only** via `ProjectAssignmentSummaryPanel`:

- Active assignment chips (project-level and item-level)
- Per-item assignee chips in items table
- **Manage in Procurement** link — no create/complete/cancel on project page

Removed: assignment tab, bulk assign checkboxes, `ProcurementAssignmentsPanel` (deleted).

## API usage

Unchanged Sprint 5D APIs via `procurementAssignmentsAPI`:

- `list` with filters for management board
- `create`, `bulkCreate`, `complete`, `cancel`
- `listByProject` for read-only project summary

No fake frontend assignments. No production mocks.

## Permissions

Existing helpers unchanged:

- Management tab content: `canCreateProcurementAssignments` OR `canViewAllProcurementAssignments`
- View-only tab content: `MyProcurementAssignmentsPanel` when user has `procurement.assignments.view` only
- `access_control_admin` excluded (backend + frontend unchanged)
- Legacy admin bypass only

## i18n

Added keys: `managementTitle`, `manageInProcurement`, `assignmentScope`, `projectAssignment`, `itemAssignment`, `selectProject`, `selectProjectItems`, `selectProcurementUsers`, `assignedWork`, `procurement.operationsTab`, etc. (EN + FA).

## Tests

| Test | Result |
|------|--------|
| `procurementAssignmentPermissions.test.ts` | PASS |
| `procurementAssigneeUtils.test.ts` | PASS |
| `ProcurementPage.assignmentsRelocation.test.ts` | PASS (source placement checks) |
| `npm run build` | PASS |

## Runtime smoke (2026-06-26)

| Check | Result |
|-------|--------|
| Deploy | `/opt/rivar-demo` @ `551d2fc`, sprint=5E-R1 |
| `run_sprint5d_smoke.sh` | PASS (13 checks, 0 failures) |
| `verify.sh` | PASS |
| `/health` | 200 |
| Frontend `:3000` | 200 |

## Deployment

- Script: `deployment/rivar-installer/deploy_update_5e_r1.sh`
- Target: `/opt/rivar-demo`, compose `rivar-demo`
- Backend unchanged (frontend-only)

## Out of scope

- Sprint 5F backend scope enforcement
- Package Wizard Step 3
- Master Data RBAC changes
- Optimization/cashflow/decision

## Remaining risks

- Item labels in global board show `#id` until project filter loads items
- No browser E2E for full dialog walkthrough (API smoke + build used)

## Recommendation

**Proceed to Sprint 5F — Procurement Assignment Scope Enforcement and Procurement Workflow Filtering**

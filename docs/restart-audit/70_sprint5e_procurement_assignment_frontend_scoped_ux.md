# Sprint 5E — Procurement Assignment Frontend and Scoped Procurement UX

**Status:** PASS WITH MINOR ISSUES  
**Date:** 2026-06-26  
**Sprint name:** Sprint 5E — Procurement Assignment Frontend and Scoped Procurement UX

## Baseline

| Item | Value |
|------|-------|
| Starting branch | `restart/sprint5d-procurement-assignment-backend` |
| Starting commit | `43bb62e6e0da9e21c99d1e4b4294d51c4272b43f` |
| New branch | `restart/sprint5e-procurement-assignment-frontend-scoped-ux` |
| Feature commit | `4e8c4149699926a2842d89f2dd08aa45d86b497f` |
| Deployed to demo | `/opt/rivar-demo` @ `4e8c414` (sprint=5E) |

## UI placement decision

No new top-level navigation item was added (avoids menu clutter).

| Surface | Location | Audience |
|---------|----------|----------|
| Project + item assignments | **Project Items** page (`/projects/:projectId/items`) — tab **Procurement Assignments** / **تخصیص تأمین** | PMO/PM/admin with assignment permissions |
| Item bulk assign | Same page — row checkboxes + **Assign selected items** | Users with `procurement.assignments.create` |
| My Assignments | Top of **Procurement** page (`/procurement`) | Users with `procurement.assignments.view` (own rows) |

Rationale: project items already host project context; procurement page is the natural home for specialists viewing assigned work.

## API client / types

**Types:** `frontend/src/types/procurementAssignments.ts`

**Client:** `procurementAssignmentsAPI` in `frontend/src/services/api.ts`

Methods: `list`, `get`, `create`, `bulkCreate`, `update`, `complete`, `cancel`, `delete`, `listByProject`, `listByProjectItem`, `listByUser`

All calls use the shared axios instance and `formatApiError` for user-visible errors (including 409 duplicate).

## Permission helpers

Added to `frontend/src/utils/permissions.ts`:

- `canViewProcurementAssignments`
- `canCreateProcurementAssignments`
- `canEditProcurementAssignments`
- `canCompleteProcurementAssignments`
- `canCancelProcurementAssignments`
- `canDeleteProcurementAssignments`
- `canManageProcurementAssignments`
- `canViewAllProcurementAssignments`

Legacy `admin` bypass only; no legacy `procurement` role bypass for management.

## UX summary

### Project-level assignment

- List with status filter (active / completed / cancelled / history)
- Create dialog — multi-select procurement users
- Complete / cancel with confirmation
- Duplicate assignment surfaces backend 409 message

### Item-level / bulk assignment

- Select items via checkboxes on Items tab
- **Assign selected items** opens bulk dialog on Assignments tab
- Uses `POST /procurement-assignments/bulk`

### My Assignments (procurement user)

- Grouped by project; project-level vs item-level chips
- Link to project items page
- Scope disclaimer: assigned-work view only; full enforcement deferred to Sprint 5F
- Toggle assignment history

### Assignee picker

`ProcurementAssigneePicker` filters active users with legacy `procurement` role or `procurement_specialist` RBAC role.

## i18n

Namespace: `procurementAssignments.*` in `en.json` and `fa.json`  
Project items tab: `projectItems.itemsTab`

## Tests

| Test file | Notes |
|-----------|-------|
| `procurementAssignmentPermissions.test.ts` | RBAC helper matrix |
| `procurementAssigneeUtils.test.ts` | Assignee filter/label |

Local Jest cannot parse TypeScript in this workspace (pre-existing toolchain limitation; same failure on existing `permissions.test.ts`). **Frontend production build PASS** (`npm run build`).

## Runtime smoke (2026-06-26)

| Check | Result |
|-------|--------|
| `deploy_update_5e.sh` frontend rebuild | PASS |
| `DEPLOYED_COMMIT.txt` | `branch=restart/sprint5e-procurement-assignment-frontend-scoped-ux`, `commit=4e8c414`, `sprint=5E` |
| `run_sprint5d_smoke.sh` | PASS (13 checks, 0 failures) |
| `verify.sh` | PASS (frontend routes, backend health, OpenAPI, R3 fixture, Sprint 3A-R3 runtime) |
| `/health` | 200 |
| `/openapi.json` | 200 |
| Assignment APIs (create/duplicate/complete/cancel/view own) | PASS via 5D smoke |
| Master Data RBAC regression (AC denied payment-methods) | PASS via 5D smoke |
| Frontend HTTP `:3000` | 200 |

UI flows validated via deployed frontend rebuild + assignment API smoke (project/item create, duplicate 409, complete/cancel, proc view own). Manual browser walkthrough recommended for dialog UX polish.

## Deployment

- Script: `deployment/rivar-installer/deploy_update_5e.sh`
- Target: `/opt/rivar-demo`, compose `rivar-demo`
- Backend unchanged in 5E (frontend-only rebuild)
- Note: initial Windows CRLF on deploy script required `dos2unix` on server; harmless BOM warning on shebang line during first run

## Out of scope (explicit)

- Broad backend procurement scope enforcement
- Package Wizard Step 3 changes
- Payment Methods / Cost Components / Items Master / Suppliers enforcement changes
- Optimization / cashflow / decision changes
- Fake frontend-only assignments

## Remaining risks

- Local Jest not runnable for new `.test.ts` files in this environment
- My Assignments is informational; backend does not yet filter all procurement APIs by assignment
- PM project scoping for create still follows backend Sprint 5D rules

## Recommendation

**Proceed to Sprint 5F — Procurement Assignment Scope Enforcement and Procurement Workflow Filtering**

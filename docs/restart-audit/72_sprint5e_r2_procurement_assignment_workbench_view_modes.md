# Sprint 5E-R2 — Procurement Assignment Workbench View Modes and Remove Assignment UX

**Status:** PASS WITH MINOR ISSUES  
**Date:** 2026-06-26  
**Sprint name:** Sprint 5E-R2 — Procurement Assignment Workbench View Modes and Remove Assignment UX

## Baseline

| Item | Value |
|------|-------|
| Starting branch | `restart/sprint5e-r1-procurement-assignment-ux-relocation` |
| Starting commit | `ddfe4d5b545b141ce8f0aaaa43b898730be37463` |
| New branch | `restart/sprint5e-r2-procurement-assignment-workbench-view-modes` |

## Product-owner feedback

Assignment is responsibility allocation, not finalization of procurement work. Finalization belongs to optimization/decision workflow. "Complete assignment" was confusing. Managers need View by Project / View by Item, item-level removal, and bulk remove — without faking partial removal from project-level assignments.

## Complete action removed/de-emphasized

- Primary management UI no longer shows **Complete assignment**
- `procurementAssignmentsAPI.complete` not called from management views
- Completed status remains in filters/history for backend compatibility
- Helper text explains finalization vs assignment responsibility (EN + FA)

## View modes

| Mode | Behavior |
|------|----------|
| **View by Project** | Expandable project rows, coverage summary, item table, assign all/selected items, remove item/project assignments |
| **View by Item** | Flat assignment list with search, multi-select remove |

Default: View by Project for managers.

## Project-level vs item-level

- **Project-level responsibility** — clearly labeled; warning that per-item exclusion is not supported
- **Item-level assignment** — bulk create via `POST /procurement-assignments/bulk`
- **Assign all current project items** — bulk item-level assignments for full per-item control later

## Remove/cancel behavior

- Wording: **Remove assignment** / **Remove selected assignments**
- Uses backend `cancel` with `cancelled_reason`
- Bulk remove with success/failure summary
- Active-only selection; completed/cancelled not selectable

## Permissions

Unchanged Sprint 5E helpers: view/create/cancel gated; admin bypass only.

## Tests

| Test | Result |
|------|--------|
| `procurementAssignmentWorkbenchUtils.test.ts` | PASS |
| `ProcurementPage.workbenchUx.test.ts` | PASS |
| `ProcurementPage.assignmentsRelocation.test.ts` | PASS |
| `npm run build` | PASS |

## Deployment

- Script: `deployment/rivar-installer/deploy_update_5e_r2.sh`
- Target: `/opt/rivar-demo`, frontend-only

## Out of scope

- Sprint 5F scope enforcement
- Optimization send workflow
- Package Wizard / master data RBAC changes

## Recommendation

**Proceed to Sprint 5F — Procurement Assignment Scope Enforcement and Procurement Workflow Filtering**

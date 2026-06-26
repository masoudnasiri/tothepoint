# Sprint 5E-R2-Fix — Secure Procurement Assigned Item Visibility

**Status:** PASS WITH MINOR ISSUES  
**Date:** 2026-06-26  
**Sprint name:** Sprint 5E-R2-Fix — Secure Procurement Assignment Item Visibility

## Baseline

| Item | Value |
|------|-------|
| Starting branch | `restart/sprint5e-r2-procurement-assignment-workbench-view-modes` |
| Starting commit | `8bfd36374f8e3296f601baeee9160714f746db9a` |
| New branch | `restart/sprint5e-r2-fix-secure-assigned-item-visibility` |

## User-reported security issue

In **Procurement → My Procurement Assignments**, the **Open project items** link routed procurement users without project-management permission to the full **Project Items** page, exposing add/edit/delete/finalize actions and lifecycle/financial fields.

## Unsafe old behavior

- `MyProcurementAssignmentsPanel` linked unconditionally to `/projects/{id}/items`
- `ProjectItemsPage` was login-only (`ProtectedRoute`) with no `project_items.view` guard
- `GET /items/project/{id}` allowed any authenticated user except restricted PM rows — procurement users received full `ProjectItem` payloads including invoice/payment/cash-in dates

## Safe assigned-items view design

| Item | Detail |
|------|--------|
| UI location | `AssignedProcurementItemsDialog` opened from My Assignments when user lacks `canViewProjectItems` |
| EN label | View assigned items |
| FA label | مشاهده اقلام تخصیص‌یافته |
| Interaction | Read-only dialog inside Procurement module; no route change |

### Allowed fields

- `project_id`, `project_code`, `project_name`
- `project_item_id`, `item_code`, `item_name`, `description`
- `quantity`, `delivery_options`, `item_status`, `external_purchase`, `is_finalized`
- Assignment context: `assignment_scope`, `assignment_status`, assignee username/id
- `covered_by_project_assignment` marker for project-level responsibility

### Sensitive fields excluded

- `decision_date`, `procurement_date`, `payment_date`
- `invoice_submission_date`, `expected_cash_in_date`, `actual_cash_in_date`
- `finalized_by`, `finalized_at`, `file_path`, `file_name`
- Sale/customer/revenue/margin fields (not present on model; excluded by allowlist serializer)
- All project-management actions (add/edit/delete/finalize/send-to-optimizer)

## Backend data minimization

| Endpoint | Purpose |
|----------|---------|
| `GET /procurement-assignments/my-assigned-items` | Current user's sanitized rows |
| `GET /procurement-assignments/assigned-items` | Manager-filtered sanitized rows |
| `GET /procurement-assignments/projects/{project_id}/assigned-items` | Per-project sanitized rows |

- Service: `backend/app/services/procurement_assigned_items_service.py`
- Schema: `ProcurementAssignedItemSummary` in `schemas.py`
- Scope: view-only users see only own assignments; managers with assignment create/edit/cancel see broader lists
- Project-level assignments expand to all project items (sanitized)

### Project Items API guard

- `require_project_items_permission("project_items.view")` on read endpoints in `items.py`
- Legacy fallback: PMO/PM without explicit RBAC retain access; procurement view-only denied

## Route / permission guards

| Surface | Guard |
|---------|-------|
| `/projects/:projectId/items` | `ProjectItemsRoute` + `canViewProjectItems` |
| My Assignments link | Ternary: full link only when `canViewProjectItems`; else safe dialog |
| Backend `/items/project/*` | `project_items.view` RBAC dependency |

Admin/PMO/PM with `project_items.view` (or legacy PMO/PM role) unchanged.

## Assignment workbench regression

5E-R2 behavior preserved: View by Project/Item, assign all, remove selected, no Complete primary, Project Items summary-only.

## Tests

| Test | Result |
|------|--------|
| `test_phase15e_r2_fix_secure_assigned_item_visibility.py` | 6/6 PASS |
| `ProcurementPage.secureAssignedItems.test.ts` | 4/4 PASS |

## Runtime smoke

| Check | Result |
|-------|--------|
| Deploy script | `deployment/rivar-installer/deploy_update_5e_r2_fix.sh` |
| Target | `/opt/rivar-demo`, compose `rivar-demo` |
| Rebuild | frontend + backend |

## Scope exclusions

- Sprint 5F broad procurement enforcement
- Package Wizard changes
- Optimization send workflow
- Master Data RBAC changes
- Assignment management relocation back to Project Items

## Remaining risks

- `GET /items/finalized` still serves procurement-role users full item payloads for legacy procurement workflow (intentionally unchanged; address in Sprint 5F)
- Assignment workbench managers still load full project items via `itemsAPI` when expanding projects (requires `project_items.view` in normal RBAC roles)

## Recommendation

**Proceed to Sprint 5F — Procurement Assignment Scope Enforcement and Procurement Workflow Filtering**

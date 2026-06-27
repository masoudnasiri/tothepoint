# Sprint 5E-R2-Fix-R1 — Secure Assigned Item Visibility Runtime Deployment Closure

**Status:** PASS WITH MINOR ISSUES  
**Date:** 2026-06-27  
**Sprint name:** Sprint 5E-R2-Fix-R1 — Secure Assigned Item Visibility Runtime Deployment Closure

## Baseline

| Item | Value |
|------|-------|
| Source branch | `restart/sprint5e-r2-fix-secure-assigned-item-visibility` |
| Source commit | `3057651a7a65af8e4f6650ebd15d454e4bffe184` |
| Closure branch | `restart/sprint5e-r2-fix-r1-secure-item-runtime-closure` |
| Official demo path | `/opt/rivar-demo` |
| Forbidden path used | **No** (`/root/pdss_demo` not used) |

## Server access gate

- SSH to `root@193.162.129.58` succeeded using deploy key `id_rivar_deploy_temp`.
- Official path `/opt/rivar-demo` confirmed accessible.

## Before-deploy evidence

### Deployed commit evidence (before)

- `/opt/rivar-demo/DEPLOYED_COMMIT.txt`: missing (before)
- `/opt/rivar-demo/docs/restart-audit/DEPLOYED_COMMIT.txt`:
  - `branch=restart/sprint5e-r2-procurement-assignment-workbench-view-modes`
  - `commit=d3a1760`
  - `sprint=5E-R2`

### Runtime and container state (before)

- `/health` = 200
- `/openapi.json` = 200
- Assigned-items paths in OpenAPI:
  - `/procurement-assignments/my-assigned-items` = **NO**
  - `/procurement-assignments/assigned-items` = **NO**
  - `/procurement-assignments/projects/{project_id}/assigned-items` = **NO**
- `procurement-assignments` path count before = 8
- Running containers before:
  - backend `16822133dbc8` (healthy)
  - frontend `384753d6fe55`
  - postgres `63338664b8a6` (healthy)

### Frontend behavior evidence (before)

`/opt/rivar-demo/frontend/src/components/procurement/MyProcurementAssignmentsPanel.tsx` showed unsafe direct link:

- `<Link component={RouterLink} to={`/projects/${projectId}/items`} ...>`
- `openProjectItems` present
- `canViewProjectItems` absent
- `AssignedProcurementItemsDialog` absent
- `ProjectItemsRoute` component file absent

## Deployment steps

1. Built exact tarball from commit `3057651a7a65af8e4f6650ebd15d454e4bffe184`.
2. Uploaded tarball to server with `scp` using `id_rivar_deploy_temp`.
3. Extracted into `/opt/rivar-demo`.
4. Normalized installer shell line endings (`CRLF -> LF`) on server for `deployment/rivar-installer/*.sh`.
5. Ran:
   - `bash deployment/rivar-installer/deploy_update_5e_r2_fix.sh 3057651a7a65af8e4f6650ebd15d454e4bffe184 restart/sprint5e-r2-fix-secure-assigned-item-visibility`
   - `bash deployment/rivar-installer/verify.sh`
   - `bash deployment/rivar-installer/run_sprint5d_smoke.sh`
6. Wrote required file:
   - `/opt/rivar-demo/DEPLOYED_COMMIT.txt`
   - `sprint=5E-R2-Fix-R1`

## Exact deployed identity

- Branch deployed: `restart/sprint5e-r2-fix-secure-assigned-item-visibility`
- Commit deployed: `3057651a7a65af8e4f6650ebd15d454e4bffe184`
- `/opt/rivar-demo/DEPLOYED_COMMIT.txt`:
  - `branch=restart/sprint5e-r2-fix-secure-assigned-item-visibility`
  - `commit=3057651a7a65af8e4f6650ebd15d454e4bffe184`
  - `deployed_at=2026-06-27T07:01:07Z`
  - `sprint=5E-R2-Fix-R1`

## After-deploy evidence

### Container refresh (after)

- backend `6c663a4bf18b` created `2026-06-27T06:56:20Z` (healthy)
- frontend `601270c98e30` created `2026-06-27T06:56:22Z`
- postgres unchanged `63338664b8a6` (healthy)

### OpenAPI / backend evidence (after)

- `/health` = 200
- `/openapi.json` = 200
- Assigned-items paths in OpenAPI:
  - `/procurement-assignments/my-assigned-items` = **YES**
  - `/procurement-assignments/assigned-items` = **YES**
  - `/procurement-assignments/projects/{project_id}/assigned-items` = **YES**
- `procurement-assignments` path count after = 11
- Runtime backend source evidence (inside container):
  - `ProcurementAssignedItemSummary` present
  - assigned-items router paths present
  - assigned-items service `list_assigned_item_summaries` present
  - `items.py` contains `require_project_items_permission(...)` and `project_items.view`

### Frontend evidence (after)

`/opt/rivar-demo/frontend/src/...` shows:

- `ProjectItemsRoute.tsx` exists
- `MyProcurementAssignmentsPanel.tsx` has `canViewProjectItems(user)` gate
- safe `AssignedProcurementItemsDialog` integration present
- `viewAssignedItems` i18n key present
- `openProjectItems` still present only for privileged users
- `App.tsx` wraps `/projects/:projectId/items` with `ProjectItemsRoute`

## Runtime security smoke

### Procurement assignment view-only user

Validated with `sprint5d_proc_view_user`:

- `/auth/me` includes `procurement.assignments.view`
- `/auth/me` does **not** include `project_items.view`
- `/procurement-assignments/my-assigned-items` = 200
- Response keys are sanitized allowlist:
  - `project_id`, `project_code`, `project_name`, `project_item_id`
  - `item_code`, `item_name`, `description`, `quantity`
  - `delivery_options`, `item_status`, `external_purchase`, `is_finalized`
  - `covered_by_project_assignment`, `assignments`
- Sensitive keys absent:
  - no `sale_price`, `customer_price`, `revenue`, `margin`
  - no invoice/cashflow fields
  - no file-path/finalization-actor fields
- Unassigned project query:
  - `/procurement-assignments/projects/{unassigned}/assigned-items` = 200 with `[]`
- Full project-items API denied:
  - `/items/project/{project_id}` = 403

### Access-control-only and admin/PMO

- Created runtime AC-only user with only `access_control_admin` role:
  - has access-control manage permissions
  - lacks `project_items.view`
  - `/items/project/{project_id}` = 403
- Admin:
  - `/items/project/{project_id}` = 200
- Temporary PMO user:
  - `/items/project/{project_id}` = 200

## Regression smoke

- `verify.sh` = PASS
  - health/openapi checks passed
  - fixture reseed passed
  - Sprint 3A-R3 runtime verification passed
  - readiness checks passed
- `run_sprint5d_smoke.sh` = PASS (`failures: 0`)
- Assignment backend operations confirmed live:
  - project view filter = 200
  - item view filter = 200
  - bulk create ("assign all") = 201
  - cancel ("remove selected") = 200
- Users + Access Control endpoints = 200
- Master Data RBAC spot checks:
  - AC-only payment methods = 403
  - AC-only items master = 403
  - AC-only suppliers = 403
  - Admin payment methods = 200
  - Cost-component RBAC verified via `/procurement-options/59/cost-components`:
    - admin = 200
    - AC-only = 403

## Scope control

- No Sprint 5F enforcement started.
- No Package Wizard behavior change.
- No optimization/cashflow/decision behavior change.
- No broad procurement enforcement changes beyond accepted 5E-R2-Fix behavior.
- `/root/pdss_demo` not used.

## Remaining risks / follow-ups

1. **Known residual**: `/items/finalized` still returns rich payload fields for legacy procurement-role access.  
   - Confirmed runtime: view-only procurement user receives fields including cashflow/invoice/finalization metadata.
   - Track under Sprint 5F data minimization/enforcement scope.
2. Legacy fixture user `sprint5c_r4_fix3_ac_only_user` is not truly AC-only (has PM base role and broad grants); closure smoke used a freshly created true AC-only user for authoritative RBAC checks.

## Git provenance

- Deployment source branch: `restart/sprint5e-r2-fix-secure-assigned-item-visibility`
- Deployment source commit: `3057651a7a65af8e4f6650ebd15d454e4bffe184`
- Closure branch: `restart/sprint5e-r2-fix-r1-secure-item-runtime-closure`

## Recommendation

**Proceed to Sprint 5F — Procurement Assignment Scope Enforcement and Procurement Workflow Filtering**, with explicit carry-over items:

- `/items/finalized` data minimization/enforcement
- cleanup or replacement of legacy AC-only runtime fixture accounts

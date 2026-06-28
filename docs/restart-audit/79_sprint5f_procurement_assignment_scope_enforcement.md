# Sprint 5F - Procurement Assignment Scope Enforcement and Procurement Workflow Filtering

## Sprint metadata

- Sprint: `Sprint 5F — Procurement Assignment Scope Enforcement and Procurement Workflow Filtering`
- Starting branch: `restart/sprint5e-r4-finalized-only-assignment-items`
- Starting commit: `b492ee1eceb4fd8b409a1b9d86255becfb987897`
- Working branch: `restart/sprint5f-procurement-assignment-scope-enforcement`
- Status: `PASS WITH MINOR ISSUES`

## Endpoint inventory (Phase A)

### Frontend views inspected

- `frontend/src/pages/ProcurementPage.tsx`
- `frontend/src/components/packages/PackageList.tsx`
- `frontend/src/components/PackageWizard/PackageWizard.tsx`
- `frontend/src/components/procurement/MyProcurementAssignmentsPanel.tsx`
- `frontend/src/components/procurement/ProcurementAssignmentManagementPanel.tsx`
- `frontend/src/components/procurement/AssignedProcurementItemsDialog.tsx`
- `frontend/src/services/api.ts`
- `frontend/src/utils/permissions.ts`

### Backend endpoints inspected

- Finalized items:
  - `GET /items/finalized`
- Procurement options:
  - `GET /procurement/item-codes`
  - `GET /procurement/items-with-details`
  - `GET /procurement/options`
  - `GET /procurement/options/{item_code}`
  - `GET /procurement/options/by-project-item/{project_item_id}`
  - `GET /procurement/option/{option_id}`
  - `POST /procurement/options`
  - `PUT /procurement/option/{option_id}`
  - `DELETE /procurement/option/{option_id}`
- Packages:
  - `POST /packages/`
  - `PUT /packages/{package_id}`
  - `DELETE /packages/{package_id}`
  - `GET /packages/by-project-item/{project_item_id}`
  - `GET /packages/{package_id}`
  - `POST /packages/subitems/`
  - `PUT /packages/subitems/{subitem_id}`
  - `DELETE /packages/subitems/{subitem_id}`
  - `GET /packages/coverage/{project_item_id}`
  - `POST /packages/optimization-submission`
  - `POST /packages/optimization-submission/{project_item_id}/rollback`
  - `POST /packages/optimization-rollback-preview`
  - `POST /packages/optimization-rollback`
- Project package/coverage views:
  - `GET /projects/{project_id}/packages`
  - `GET /projects/{project_id}/coverage-summary`

### Endpoints scope-filtered in 5F

- `GET /items/finalized`
- All procurement options endpoints above
- All package endpoints above except unchanged list below
- `GET /projects/{project_id}/packages`
- `GET /projects/{project_id}/coverage-summary`

### Endpoints explicitly unchanged in 5F

- Assignment workbench CRUD endpoints in `procurement_assignments` router (5E-R3/R4 behavior preserved)
- Package wizard internals and optimization/cashflow/decision algorithms
- Master Data RBAC routes (payment methods, cost components) except regression verification

### Assigned-only frontend action changes

- Hide global send-all action: `Send all finalized packages to optimization`
- Hide global bulk rollback dialog/action
- Keep per-item actions visible only when effective permissions allow mutation/submit
- Show assigned-only scope banner in Procurement Operations view

## Scope model implemented

- Global scope users:
  - `admin`/system admin bypass
  - users with any global procurement scope permissions (`procurement.assignments.create|edit|delete|complete|cancel`, `project_items.view`)
- Assigned-only users:
  - have procurement/assignment permissions but no global scope marker
  - access limited to active assignment scope (`status=active`) and finalized project items only
- Unauthorized users:
  - denied from procurement scope endpoints

Assignment union logic:

- Project-level active assignment -> all finalized items under assigned project
- Item-level active assignment -> assigned finalized item only
- Union of both sets is allowed scope
- `completed`/`cancelled` assignments are excluded

## `/items/finalized` carry-over fix (5E-R4 -> 5F)

`GET /items/finalized` now resolves procurement scope access and applies:

- assigned-only filtering to `active_scope.finalized_project_item_ids`
- finalized-only enforcement
- deny unauthorized callers
- global/admin behavior preserved

Assigned-only field allowlist:

- `id`
- `project_id`
- `master_item_id`
- `item_code`
- `item_name`
- `quantity`
- `delivery_options`
- `status`
- `external_purchase`
- `description`
- `is_finalized`
- `created_at`
- `updated_at`
- `sub_items`
- `coverage_state`
- `coverage_percentage`
- `optimization_state`
- `is_sent_to_optimization`
- `active_package_count`
- `finalized_package_count`
- `can_rollback_optimization_submission`

Sensitive finance/cash-in/payment fields are omitted for assigned-only users.

## Procurement options/packages enforcement

### Procurement options

- List/get endpoints filter to assigned finalized scope for assigned-only users
- Create:
  - requires procurement create permissions
  - rejects non-finalized project item
  - rejects project item outside active assignment scope for assigned-only users
- Update/delete:
  - require edit/delete permissions
  - denied for options outside active assignment scope for assigned-only users

### Packages

- Package list/get/subitem/coverage endpoints enforce assigned item scope for assigned-only users
- Package create/update/delete/subitem mutations require mutation permissions and scoped finalized item
- Optimization submission:
  - global users keep broad behavior
  - assigned-only users are scoped to assigned finalized items
  - `send_all_finalized` is converted to assigned finalized set for assigned-only users
- Bulk rollback preview/execute:
  - denied for assigned-only users (unsafe to expose global rollback surface)
  - preserved for global/admin users

## Frontend filtering / UX

- `ProcurementPage` now derives assigned-only scope from RBAC helper and shows:
  - EN: `"This view is limited to procurement work assigned to you."`
  - FA: `"این نما فقط کارهای تأمینی را نشان می‌دهد که به شما تخصیص داده شده‌اند."`
- Global send-all and global bulk rollback actions are hidden for assigned-only users
- Procurement package mutation/send controls are permission-gated instead of role-only gating
- My Assignments / workbench views remain available and unchanged

## Permission behavior

- `access_control_admin` role alone is denied procurement workflow scope endpoints
- Assigned-only procurement users can view/act only inside active assignment scope
- Admin/system-admin preserved
- Legacy procurement role is no longer sufficient to bypass scoped RBAC checks on covered endpoints

## Tests and evidence

### Backend focused tests

- Added: `backend/tests/test_phase15f_procurement_scope_enforcement.py`
  - assigned-only `/items/finalized` scoped + sanitized
  - cancelled assignment removes active scope
  - procurement option list/create/update/delete enforcement by assignment scope/finalized state
  - `access_control_admin` denial checks
- Ran:
  - `python -m pytest backend/tests/test_phase15f_procurement_scope_enforcement.py backend/tests/test_phase15e_r2_fix_secure_assigned_item_visibility.py backend/tests/test_phase15d_procurement_assignment_backend.py -q`
  - Result: `27 passed`

### Frontend focused tests

- Added: `frontend/src/pages/ProcurementPage.scopeEnforcement.test.ts`
- Ran:
  - `npm test -- --watch=false --runTestsByPath src/pages/ProcurementPage.scopeEnforcement.test.ts src/pages/ProcurementPage.secureAssignedItems.test.ts src/pages/ProcurementPage.workbenchUx.test.ts`
  - Result: `3 passed`

## Carry-over cleanups included

- `docs/restart-audit/78_sprint5e_r4_finalized_only_assignment_item_visibility.md`
  - fixed stale provenance commit from `c956...` to `b492ee1eceb4fd8b409a1b9d86255becfb987897`
- `backend/scripts/sprint5e_r4_runtime_smoke.py`
  - removed hardcoded readiness option id `83`
  - readiness check now resolves a live option id dynamically (or records a safe skip when no option exists)

## Runtime deployment and smoke

- Official target path: `/opt/rivar-demo`
- `verify.sh`: **pending in this local change set**
- Runtime smoke script: **pending in this local change set**

## Scope exclusions respected

- No optimization algorithm redesign
- No cashflow or decision engine logic changes
- No package wizard Step 3 workflow redesign
- No Master Data RBAC behavior change (only regression verification intent)
- Assignment management remains inside Procurement module

## Remaining risks / minor issues

- Bulk rollback preview/execute is intentionally denied (not scoped) for assigned-only users; if product requires scoped bulk rollback UX, this needs a follow-up implementation (`5F-Fix`)
- Runtime deploy/verify evidence should be captured on `/opt/rivar-demo` after branch push

## Git provenance

- Commit hash: _pending_
- Pushed branch: `restart/sprint5f-procurement-assignment-scope-enforcement`

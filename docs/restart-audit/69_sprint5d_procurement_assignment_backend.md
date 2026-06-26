# Sprint 5D — Procurement Assignment Backend

**Status:** PASS WITH MINOR ISSUES  
**Date:** 2026-06-26  
**Sprint name:** Sprint 5D — Procurement Assignment Backend  
**Final commit:** `5289efe6022005a289b06d0a65c9660d8e788a97` (includes smoke 409 fix)

## Baseline

| Item | Value |
|------|-------|
| Starting branch | `restart/sprint5c-r4-fix3-masterdata-backend-enforcement` |
| Starting commit | `61048fb43e6ae3eb5e7b27ccad00495cd778cbf4` |
| New branch | `restart/sprint5d-procurement-assignment-backend` |

## Business purpose

Provide backend foundation for assigning procurement specialists to projects and/or selected project items. PMO/PM/admin users can allocate procurement work before future scoped procurement UX (Sprint 5E) and workflow enforcement (Sprint 5F).

## Data model

**Table:** `procurement_assignments`

| Field | Type | Notes |
|-------|------|-------|
| id | SERIAL PK | |
| project_id | INTEGER NOT NULL FK → projects | |
| project_item_id | INTEGER NULL FK → project_items | NULL for project scope |
| assignee_user_id | INTEGER NOT NULL FK → users | |
| assigned_by_user_id | INTEGER NOT NULL FK → users | |
| status | VARCHAR(32) | `active`, `completed`, `cancelled` |
| assignment_scope | VARCHAR(32) | `project`, `project_item` |
| note | TEXT NULL | max 2000 in API |
| created_at / updated_at | TIMESTAMPTZ | |
| completed_at | TIMESTAMPTZ NULL | |
| cancelled_at | TIMESTAMPTZ NULL | |
| cancelled_reason | TEXT NULL | required on cancel |

**Constraints:**

- Scope/item consistency CHECK
- Partial unique indexes on active project-level and item-level rows (Postgres)
- Service-level duplicate prevention for SQLite tests

**Indexes:** project_id, project_item_id, assignee_user_id, status, assignment_scope

## Migration

- File: `backend/add_procurement_assignments_table.sql` (idempotent)
- Wired into `deployment/rivar-installer/apply_r3_schema_migrations.sh`
- SQLAlchemy model also created via `init_db()` create_all for dev/test

## Permission keys

| Key | Description |
|-----|-------------|
| procurement.assignments.view | List/read assignments |
| procurement.assignments.create | Create / bulk create |
| procurement.assignments.edit | Update note on active rows |
| procurement.assignments.delete | Soft-delete (cancel active) |
| procurement.assignments.complete | Mark active → completed |
| procurement.assignments.cancel | Cancel with reason |

### System role grants

| Role | Grants |
|------|--------|
| system_admin | All keys (via ALL_PERMISSION_KEYS) |
| pmo | All assignment keys |
| project_manager | view, create, edit, cancel |
| procurement_specialist | view only (own rows when listing) |
| finance_analyst | none |
| access_control_admin | none |

Seed is idempotent via `ensure_rbac_seeded`.

## API endpoints

| Method | Path | Permission |
|--------|------|------------|
| GET | `/procurement-assignments` | view |
| POST | `/procurement-assignments` | create |
| POST | `/procurement-assignments/bulk` | create |
| GET | `/procurement-assignments/{id}` | view |
| PUT | `/procurement-assignments/{id}` | edit |
| POST | `/procurement-assignments/{id}/complete` | complete |
| POST | `/procurement-assignments/{id}/cancel` | cancel |
| DELETE | `/procurement-assignments/{id}` | delete |
| GET | `/projects/{project_id}/procurement-assignments` | view |
| GET | `/project-items/{item_id}/procurement-assignments` | view |
| GET | `/users/{user_id}/procurement-assignments` | view |

RBAC enforced via `require_procurement_assignment_permission` (always on, like Users/Master Data pilot).

## Assignment scope helpers (future 5E/5F)

Module: `backend/app/services/procurement_assignment_scope_service.py`

- `get_assigned_project_ids_for_user`
- `get_assigned_project_item_ids_for_user`
- `get_user_procurement_assignment_scope`
- `user_has_active_procurement_assignment`
- `can_user_access_procurement_assignment`
- `user_can_view_all_assignments`

**Not enforced** on existing procurement package/option routes in 5D.

## Audit events

- PROCUREMENT_ASSIGNMENT_CREATE
- PROCUREMENT_ASSIGNMENT_BULK_CREATE
- PROCUREMENT_ASSIGNMENT_UPDATE
- PROCUREMENT_ASSIGNMENT_COMPLETE
- PROCUREMENT_ASSIGNMENT_CANCEL
- PROCUREMENT_ASSIGNMENT_DELETE_OR_DEACTIVATE
- PROCUREMENT_ASSIGNMENT_DUPLICATE_BLOCKED
- PROCUREMENT_ASSIGNMENT_PERMISSION_DENIED

## Tests

**File:** `backend/tests/test_phase15d_procurement_assignment_backend.py`

- 13 tests: permissions seed, role grants, CRUD, bulk, duplicate block, validation, RBAC, audit, scope helpers, master-data/users regressions
- Local result: **13 passed**

**Regression:** `test_phase15c_r4_fix3_masterdata_backend_enforcement.py` — passed alongside 5D tests

## Deployment

- Script: `deployment/rivar-installer/deploy_update_5d.sh`
- Smoke: `deployment/rivar-installer/run_sprint5d_smoke.sh` → `backend/scripts/sprint5d_procurement_assignment_runtime_smoke.py`
- Target: `/opt/rivar-demo`, compose `rivar-demo`
- Deployed commit: `8549abf` (backend rebuild); smoke hotfix `5289efe`
- `verify.sh`: **PASS** (R3 Step 3 runtime verification included)
- `run_sprint5d_smoke.sh`: **PASS** (0 failures)

## Out of scope (explicit)

- Procurement assignment frontend page
- Broad procurement endpoint scope enforcement
- Package Wizard / Payment Methods / Cost Components changes
- Optimization / cashflow / decision changes

## Remaining risks

- Unauthenticated assignment list returns 401 (Bearer required) not 403 — consistent with other protected routes
- Permission-denied audit rows may not persist on read-only GET failures (flush-only)
- PM project scoping for create uses legacy `ProjectAssignment` + role checks; custom roles with create permission get global create until 5E UX

## Recommendation

**Proceed to Sprint 5E — Procurement Assignment Frontend and Scoped Procurement UX**

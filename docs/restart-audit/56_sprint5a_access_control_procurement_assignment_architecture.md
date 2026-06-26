# Sprint 5A — Access Control and Procurement Assignment Architecture

Date: 2026-06-26  
Status: **PASS**  
Sprint type: **Architecture and readiness only** (no RBAC implementation)

## Baseline

| Item | Value |
|---|---|
| Starting branch | `restart/workspace-organization-after-sprint3a-r3-hotfix` |
| Starting commit | `7ee7ab35ad32a56942f2a0eeb099b757a5cf0252` |
| New branch | `restart/sprint5a-access-control-procurement-assignment-architecture` |
| ADR | `docs/architecture/ADR-011-role-permission-and-procurement-assignment-model.md` |

## Current auth / RBAC findings

### User model (`users` table)

| Field | Notes |
|---|---|
| `id`, `username`, `password_hash` | Standard credentials |
| `role` | Single string: `admin`, `pmo`, `pm`, `procurement`, `finance` |
| `is_active` | Deactivated users get 403 on auth |
| `created_at` | |

Pydantic `UserCreate` / `UserUpdate` enforce role regex — **custom roles not possible** without schema change.

### Role model

**No `roles` table.** Role is a column on `users`. No `UserRole` or `RolePermission` tables.

### Authentication (`backend/app/auth.py`, `routers/auth.py`)

- JWT bearer token; payload `sub` = username.
- `get_current_user` → 401 invalid/missing; 403 if `is_active=false`.
- Login audits `LOGIN` via `log_audit`.
- No refresh-token rotation; `/auth/me` returns user schema with single `role`.

### Authorization dependencies (backend)

| Helper | Allowed roles |
|---|---|
| `require_admin()` | admin |
| `require_pmo()` | pmo, admin |
| `require_pm()` | pm, admin |
| `require_pm_or_pmo()` | pm, pmo, admin |
| `require_procurement()` | procurement, admin |
| `require_finance()` | finance, admin |
| `require_analytics_access()` | admin, finance, pmo, procurement |
| `require_role([...])` | ad hoc per router |

**~15+ routers** use these helpers inconsistently. Many endpoints use only `get_current_user` (any authenticated user).

Notable R3 paths (unchanged this sprint):

- `procurement_financials`: payment-methods list = `get_current_user`; mutations = `require_finance()` or `require_procurement()`.
- Package wizard cost components / readiness follow same router.

### Data scope (partial)

| Mechanism | Scope | Used for |
|---|---|---|
| `project_assignments` | user_id + project_id (PM only) | PM project list filter; procurement plan PM filter |
| `get_user_projects()` | admin/pmo → all; pm → assigned; **procurement/finance → []** | `/projects` list |
| `can_access_project()` | procurement/finance → **always true** | inconsistent with empty project list |

**Gap:** Procurement APIs (`/procurement/items-with-details`, options CRUD) do **not** filter by assignment — any authenticated procurement user sees all items.

### User management APIs (`/users`)

| Endpoint | Guard |
|---|---|
| `POST /users/` | admin |
| `GET /users/` | admin |
| `GET /users/pm-list` | pmo |
| `PUT /users/{id}` | admin |
| `DELETE /users/{id}` | admin — **no last-admin protection** |

### Project assignment APIs (`/projects/assignments`)

| Endpoint | Guard | Purpose |
|---|---|---|
| `POST /projects/assignments` | pmo | Assign user to project |
| `DELETE /projects/assignments/{user_id}/{project_id}` | admin | Remove assignment |
| `GET /projects/assignments/{user_id}` | admin | User's assignments |
| `GET /projects/{id}/assignments` | pmo | Project's assignees |

**PM-only usage today** — no validation that assignee is PM role; no project-item granularity.

### Frontend auth

| Component | Behavior |
|---|---|
| `AuthContext` | Token in localStorage; loads `/auth/me`; exposes `user.role` |
| `ProtectedRoute` | Login required only — **no role/permission guard** |
| `Layout.tsx` | Nav filtered by hardcoded `roles[]` per item |
| Page components | Widespread `user?.role === 'admin'` conditionals |

**Master Data:** Payment Methods UI in `ItemsMasterPage` (admin/pm/pmo/finance edit); nav under Base Information. Finance page does not host Payment Methods (R3 guarantee preserved).

**Package Wizard / Procurement:** `ProcurementPage` — auth only; no assignment filter in UI.

### Audit support

- Model: `audit_logs` (user_id, action, entity_type, entity_id, details JSON, ip, user_agent, created_at).
- Router: `GET /audit-logs/` admin-only.
- Used for LOGIN, PROJECT_*, item master, etc.
- **No** role/permission/assignment audit actions yet.

### Seed / demo users (`seed_data.py`)

| Username | Role |
|---|---|
| admin | admin |
| pmo1 | pmo |
| pm1, pm2 | pm |
| proc1, proc2 | procurement |
| finance1, finance2 | finance |

`create_project_assignments()` distributes projects across PM users only.

### Existing tests

- No dedicated auth/RBAC test module.
- Tests create users inline with `_create_user(..., role)`.
- R3 tests use `procurement` role users without assignment scoping.
- `LoginPage.smoke.test.tsx` mocks AuthContext.

---

## Current procurement assignment gaps

1. No `procurement_assignments` table or API.
2. Procurement users have **global read/write** on procurement endpoints (except explicit `require_procurement()` mutations).
3. PM assignments exist but are unrelated to procurement workload.
4. No “My assigned items” view or filter.
5. `get_user_projects()` returns `[]` for procurement — projects list empty while procurement page shows all items (inconsistent UX).
6. No `assigned_by`, status, or note on assignments.
7. No multi-assignee item-level granularity.

---

## Proposed data model

See ADR-011. Summary tables:

- `roles` — system + custom roles
- `permissions` — seeded registry
- `role_permissions` — M2M
- `user_roles` — M2M (replaces single column long-term)
- `procurement_assignments` — project and optional project_item scope

Legacy `users.role` retained through Sprint 5B–5E transition.

---

## Proposed API endpoints (document only — not implemented in 5A)

### Role management (`/access-control/roles`)

| Method | Path | Permission | Notes |
|---|---|---|---|
| GET | `/access-control/roles` | `access_control.roles.view` | List roles |
| POST | `/access-control/roles` | `access_control.roles.create` | Custom role |
| GET | `/access-control/roles/{role_id}` | `access_control.roles.view` | Detail + permission ids |
| PUT | `/access-control/roles/{role_id}` | `access_control.roles.edit` | Update metadata/active |
| DELETE | `/access-control/roles/{role_id}` | `access_control.roles.delete` | Soft-delete custom only |

### Permission registry

| Method | Path | Permission |
|---|---|---|
| GET | `/access-control/permissions` | `access_control.permissions.view` |
| PUT | `/access-control/roles/{role_id}/permissions` | `access_control.permissions.manage` |

### User roles

| Method | Path | Permission |
|---|---|---|
| GET | `/access-control/users/{user_id}/roles` | `access_control.user_roles.view` |
| PUT | `/access-control/users/{user_id}/roles` | `access_control.user_roles.manage` |

### Procurement assignments (`/procurement-assignments`)

| Method | Path | Permission |
|---|---|---|
| GET | `/procurement-assignments/by-project/{project_id}` | `procurement.assignments.view` |
| GET | `/procurement-assignments/by-user/{user_id}` | `procurement.assignments.view` (self or admin) |
| POST | `/procurement-assignments` | `procurement.assignments.assign` |
| PUT | `/procurement-assignments/{assignment_id}` | `procurement.assignments.edit` |
| DELETE | `/procurement-assignments/{assignment_id}` | `procurement.assignments.delete` |

### Auth extension (future)

`GET /auth/me` → add `permissions: string[]`, `role_codes: string[]`, `has_global_procurement_scope: boolean`.

---

## Proposed frontend pages / components (document only)

| UI | Route (proposed) | Purpose |
|---|---|---|
| Access Control / Roles | `/access-control/roles` | Role list |
| Role editor | `/access-control/roles/:id` | Metadata + permission matrix |
| Permission matrix | component | Feature rows × action columns |
| User role assignment | section on `/users` or `/access-control/users/:id` | Multi-role picker |
| Project procurement panel | `ProjectsPage` drawer | Assign procurement users to project |
| Item procurement panel | `ProjectItemsPage` row action | Item-level assignees |
| My assigned procurement | `/procurement/my-assignments` | Filtered workload view |

All gated by permission keys; menu entries replace hardcoded role arrays in `Layout.tsx` during Sprint 5C–5F.

---

## Proposed permissions registry (initial seed excerpt)

| Feature key | Permissions |
|---|---|
| `access_control` | `.roles.view/create/edit/delete/manage`, `.permissions.view/manage`, `.user_roles.view/manage` |
| `users` | `.view`, `.create`, `.edit`, `.delete` |
| `projects` | `.view`, `.create`, `.edit`, `.delete`, `.scope.all` |
| `project_items` | `.view`, `.create`, `.edit`, `.delete`, `.finalize` |
| `procurement` | `.packages.view/create/edit/delete/submit`, `.options.view/create/edit/delete`, `.scope.global` |
| `procurement.assignments` | `.view`, `.assign`, `.edit`, `.delete` |
| `master_data` | `.items.view/edit`, `.payment_methods.view/create/edit/delete`, `.suppliers.view/edit` |
| `decisions` | `.view`, `.approve`, `.lock`, `.review` |
| `finance` | `.view`, `.edit`, `.export` |
| `optimization` | `.view`, `.run`, `.review` |
| `reports` | `.view`, `.export` |
| `audit` | `.view` |

Full matrix in ADR-011 §2. Default grants per system role mirror current `require_*` behavior.

---

## Migration plan

1. **5B:** DDL + seed + backfill `user_roles` from `users.role`; add `require_permission` wrapping legacy helpers; last-admin guard on user delete.
2. **5C:** Roles UI + `/auth/me` permissions payload.
3. **5D:** `procurement_assignments` CRUD + list endpoint scope filters.
4. **5E:** Assignment UI on projects/items + my-assignments view.
5. **5F:** Enable `ENABLE_PERMISSION_ENFORCEMENT` per module; menu/button gating; `verify_runtime_rbac.py`.

No data loss; demo fixture adds sample assignments in 5D.

---

## Test plan (implementation sprints)

| Sprint | Tests |
|---|---|
| 5B | Permission dependency unit tests; migration backfill; admin lockout |
| 5C | Role matrix UI tests; nav permission snapshots |
| 5D | Assignment CRUD API; scope filter on procurement list |
| 5E | Assignment panel integration |
| 5F | End-to-end deny/allow; R3 regression suite unchanged |

---

## Runtime impact (Sprint 5A)

**None.** No product code changed. R3 hotfix behavior preserved:

- `procurement_financials` router registered
- `/payment-methods`, readiness, Step 3, cost components, payment schedule terminology — unchanged

---

## Out of scope (Sprint 5A)

- RBAC CRUD implementation
- Permission matrix UI
- Procurement assignment UI
- Login/auth behavior changes
- Package Wizard / Payment Methods / Cost Components changes
- Optimization, cashflow, decision, rollback, dashboard, report builder
- Later sprint endpoints (atomic candidate, coverage, projection, scenario preview)

---

## Recommended implementation sequence

| Sprint | Deliverable |
|---|---|
| **5B** | Backend RBAC foundation: tables, seeds, `require_permission`, last-admin guard, dual-read |
| **5C** | Frontend Role Management UI + permission-aware `/auth/me` |
| **5D** | Procurement Assignment backend/API + scope filters |
| **5E** | Procurement Assignment UI (project, item, my-assignments) |
| **5F** | Enforcement on critical routes + menu/action visibility + RBAC runtime verify |

---

## Validation (this sprint)

| Command | Result |
|---|---|
| `git status --short` | Only new ADR + this doc staged; unrelated untracked files present |
| Backend tests | Not run (docs-only sprint) |
| Frontend tests | Not run (docs-only sprint) |

---

## Git provenance

Recorded at push time:

- Branch: `restart/sprint5a-access-control-procurement-assignment-architecture`
- Parent commit: `7ee7ab35ad32a56942f2a0eeb099b757a5cf0252`
- Staged: `docs/architecture/ADR-011-role-permission-and-procurement-assignment-model.md`, `docs/restart-audit/56_sprint5a_access_control_procurement_assignment_architecture.md`, `docs/restart-audit/08_recommended_continuation_plan.md`

---

## Sprint verdict

**PASS** — architecture package complete; no product behavior change.

# ADR-011: Role, Permission, and Procurement Assignment Model

- Status: **Proposed** (architecture sprint — not implemented)
- Date: 2026-06-26
- Decision owners: Platform Architecture, Security, Procurement Domain
- Baseline: `restart/workspace-organization-after-sprint3a-r3-hotfix` @ `7ee7ab35ad32a56942f2a0eeb099b757a5cf0252`

## Context

Rivar currently uses a **single string role per user** (`admin`, `pmo`, `pm`, `procurement`, `finance`) enforced through ad hoc `require_role([...])` dependencies and duplicated frontend `user.role` checks. There is **no permission registry**, **no custom roles**, and **no procurement-specific assignment model** beyond PM-only `project_assignments`.

Business requires:

1. Custom roles with feature/action-level permissions (view/create/edit/delete plus Rivar-specific actions).
2. Procurement responsibility assignment by project and/or project item, with multiple assignees.
3. Backend enforcement as the source of truth (frontend visibility is additive only).
4. Admin lockout prevention.
5. Persian UI dates remain Jalali; API/storage dates remain ISO Gregorian.

This ADR defines the target model without implementing it in Sprint 5A.

## Current state summary (as-is)

| Area | Current behavior |
|---|---|
| `users.role` | Single `String(20)` column; Pydantic regex allows 5 enum values only |
| Authorization | `require_role`, `require_admin`, `require_pmo`, etc. in `backend/app/auth.py` |
| JWT | `sub` = username only; role resolved from DB on each request |
| PM data scope | `project_assignments` (user_id + project_id composite PK); PM list filtered |
| Procurement scope | **No assignment table**; procurement APIs mostly `get_current_user` only → global visibility |
| Frontend | `Layout.tsx` hardcoded `roles: string[]` per nav item; page-level `user?.role ===` checks |
| Audit | `audit_logs` table + `log_audit()`; LOGIN and entity CRUD actions; no role/permission events |
| User admin | `DELETE /users/{id}` with **no last-admin guard** |

## Decision

Introduce a **three-layer access model**:

1. **Functional permissions** — what actions a user may perform (RBAC).
2. **Data scope** — which projects/items they may see or mutate (assignment + optional global scope).
3. **System roles** — seeded, non-deletable templates that map from today's five roles for backward compatibility.

Functional permission and data scope are **orthogonal**: a user may hold `procurement.packages.edit` globally or only on assigned items.

---

## 1. Role model

### 1.1 System roles vs custom roles

| Kind | `is_system` | Deletable | Editable permissions | Notes |
|---|---|---|---|---|
| System role | `true` | No (deactivate only if replacement exists) | Yes, except lockout-sensitive grants | Seeded from current enum roles |
| Custom role | `false` | Soft-delete when unused | Full | Created by admins |

**Seeded system roles** (initial set, names stable):

| `code` | Display name | Maps from legacy `users.role` |
|---|---|---|
| `system_admin` | System Administrator | `admin` |
| `pmo` | PMO | `pmo` |
| `project_manager` | Project Manager | `pm` |
| `procurement_specialist` | Procurement Specialist | `procurement` |
| `finance_analyst` | Finance Analyst | `finance` |

Additional system role recommended:

| `code` | Purpose |
|---|---|
| `access_control_admin` | May be granted to break-glass admins; holds `access_control.*` permissions |

### 1.2 Role fields (`roles` table)

| Field | Type | Notes |
|---|---|---|
| `id` | serial PK | |
| `code` | varchar(64) unique | machine key, e.g. `procurement_lead` |
| `display_name` | varchar(128) | UI label (i18n key optional later) |
| `description` | text nullable | |
| `is_system` | boolean default false | |
| `is_active` | boolean default true | inactive roles cannot be assigned |
| `created_at` | timestamptz | |
| `updated_at` | timestamptz nullable | |
| `created_by_id` | FK users nullable | |

### 1.3 Role lifecycle

- **Create:** admin with `access_control.roles.create`.
- **Update:** rename/description/active flag; system role `code` immutable.
- **Deactivate:** preferred over hard delete; blocked if role is last holder of `access_control.roles.manage` or `access_control.permissions.manage`.
- **Delete:** soft-delete custom roles only when zero active `user_roles` rows.

---

## 2. Permission model

### 2.1 Permission key structure

Canonical key: `{feature}.{action}`

- `feature` — stable domain identifier (snake_case).
- `action` — verb from controlled vocabulary.

**Minimum CRUD actions:** `view`, `create`, `edit`, `delete`

**Rivar-specific actions:** `assign`, `approve`, `finalize`, `lock`, `export`, `run`, `review`, `submit`

**Administrative actions (access control feature):** `manage` (superset for role/permission admin UI)

Examples:

- `projects.view`
- `projects.create`
- `procurement.packages.edit`
- `procurement.options.submit`
- `master_data.payment_methods.edit`
- `decisions.approve`
- `optimization.run`
- `access_control.roles.manage`

### 2.2 Permission registry (`permissions` table)

| Field | Type | Notes |
|---|---|---|
| `id` | serial PK | |
| `permission_key` | varchar(128) unique | e.g. `procurement.packages.edit` |
| `feature_key` | varchar(64) | grouping for matrix UI |
| `action` | varchar(32) | |
| `description` | text | |
| `is_system` | boolean | seeded, not user-deletable |
| `sort_order` | int | matrix ordering |

Permissions are **seeded by migration** and versioned in repo (`backend/app/security/permission_registry.py` or JSON manifest). New product features must register permissions in the same change that exposes APIs.

### 2.3 Union rule (effective permissions)

When a user has multiple roles, **effective permissions = union** of all active role grants. Deny-by-exception is **out of scope** for v1 (no per-user deny overrides).

---

## 3. RolePermission model

`role_permissions` many-to-many:

| Field | Type |
|---|---|
| `role_id` | FK roles PK |
| `permission_id` | FK permissions PK |
| `granted_at` | timestamptz |
| `granted_by_id` | FK users nullable |

Unique constraint: `(role_id, permission_id)`.

---

## 4. UserRole model

`user_roles` many-to-many (replaces single `users.role` over time):

| Field | Type |
|---|---|
| `user_id` | FK users PK |
| `role_id` | FK roles PK |
| `assigned_at` | timestamptz |
| `assigned_by_id` | FK users nullable |

Unique: `(user_id, role_id)`.

**Transition:** retain `users.role` as **legacy mirror** during dual-read phase; nightly or on-write sync from primary system role assignment. JWT unchanged (username only).

---

## 5. Backend authorization

### 5.1 Dependency design

```python
# Target API (Sprint 5B+)
require_permission("procurement.packages.edit")
require_any_permission(["projects.view", "procurement.assignments.view"])
require_permission("access_control.roles.manage")

# Scope-aware (Sprint 5D+)
require_project_scope(project_id_param="project_id")
require_project_item_scope(project_item_id_param="project_item_id")
```

Implementation sketch:

1. `get_current_user` — unchanged (401 if missing/invalid token).
2. `get_effective_permissions(user_id)` — cached per request; loads union from `user_roles` → `role_permissions`.
3. `require_permission(key)` — 403 if key not in effective set.
4. Scope helpers — 403 if functional permission OK but data scope fails.

### 5.2 HTTP semantics

| Condition | Status | Detail |
|---|---|---|
| Missing/invalid token | **401** | `Could not validate credentials` |
| Valid user, inactive account | **403** | `User account is deactivated` |
| Authenticated, missing permission | **403** | `Insufficient permissions: {permission_key}` |
| Authenticated, permission OK, scope fail | **403** | `Access denied to this resource` |

### 5.3 Super-admin bypass

Users with **any** of:

- legacy `users.role == 'admin'` during transition, **or**
- role `system_admin` with full seed grant set

…receive implicit union of all seeded permissions **only if** `settings.enable_super_admin_bypass=true` (default `true` in demo, `false` in hardened production).

Explicit `access_control.roles.manage` remains required to edit roles even for super-admin when bypass disabled.

### 5.4 Admin lockout prevention

Hard rules:

1. Cannot deactivate/delete the **last active user** with `access_control.roles.manage`.
2. Cannot remove `access_control.roles.manage` from the last role that holds it.
3. System role `system_admin` cannot be deactivated.
4. Bootstrap: installer seeds `admin` user + `system_admin` role assignment; env `RIVAR_BOOTSTRAP_ADMIN_USERNAME` documented.
5. Prefer **soft delete** (`is_active=false`) for users and roles.

---

## 6. Frontend authorization

### 6.1 Principles

- **Never rely on UI alone** — all sensitive APIs use backend `require_permission`.
- Frontend uses permission set from `GET /auth/me` extension: `{ permissions: string[], scopes: {...} }`.
- Until Sprint 5C, continue legacy `user.role` checks; add parallel permission hooks without removing role checks until enforcement sprint.

### 6.2 Route guarding

| Layer | v1 (current) | Target |
|---|---|---|
| Auth | `ProtectedRoute` (logged-in only) | unchanged |
| Feature | none | `PermissionRoute permission="..."` |
| Scope | none | optional assignment guard for procurement views |

### 6.3 Menu visibility

Replace `roles: string[]` in `Layout.tsx` with `permissions: string[]` (any-match). Fallback mapping from legacy role → default permission bundle during transition.

### 6.4 Action visibility

Buttons (finalize, lock, export, run optimization) gate on specific permission keys, not role string equality.

---

## 7. Procurement assignment model

Separate from PM `project_assignments`. New table: **`procurement_assignments`**.

| Field | Type | Notes |
|---|---|---|
| `id` | serial PK | |
| `user_id` | FK users | procurement assignee |
| `project_id` | FK projects | required |
| `project_item_id` | FK project_items nullable | null = project-wide assignment |
| `status` | enum | `active`, `completed`, `cancelled` |
| `assigned_by_id` | FK users | |
| `assigned_at` | timestamptz | |
| `updated_at` | timestamptz nullable | |
| `note` | text nullable | |
| `is_active` | boolean default true | soft deactivate |

**Uniqueness:** partial unique index on `(user_id, project_id, project_item_id)` where `is_active` and `status='active'` (NULL `project_item_id` = project-level).

**Multi-user:** multiple rows per project/item allowed.

**Effective scope for procurement users without global scope:**

- Project-level row → all items under project.
- Item-level row → that item only.
- Union across multiple assignments.

Users with `procurement.scope.global` permission bypass assignment filter (PMO/admin-like).

---

## 8. Scope model (functional vs data)

| Concept | Mechanism |
|---|---|
| Functional | permission keys |
| Global data scope | permissions like `projects.scope.all`, `procurement.scope.global` |
| Assigned data scope | `procurement_assignments` (+ legacy PM `project_assignments` for PM role) |
| Read vs write | same scope for v1; future field-level out of scope |

**Query pattern:** list endpoints add `WHERE project_id IN (:visible_project_ids)` computed from assignments unless global scope permission present.

---

## 9. Audit

Extend `audit_logs` actions (no schema change required):

| Action | entity_type | When |
|---|---|---|
| `ROLE_CREATE` / `ROLE_UPDATE` / `ROLE_DEACTIVATE` | `role` | role admin |
| `ROLE_PERMISSION_UPDATE` | `role` | matrix save |
| `USER_ROLE_UPDATE` | `user` | user role assignment |
| `PROCUREMENT_ASSIGNMENT_CREATE` | `procurement_assignment` | assignment CRUD |
| `PROCUREMENT_ASSIGNMENT_UPDATE` | `procurement_assignment` | |
| `PROCUREMENT_ASSIGNMENT_DEACTIVATE` | `procurement_assignment` | |

Include `details` JSON: `{ before, after, permission_keys, project_id, project_item_id }`.

---

## 10. Migration approach

### Phase 0 — Schema (Sprint 5B)

1. Create `roles`, `permissions`, `role_permissions`, `user_roles`, `procurement_assignments`.
2. Seed permissions manifest (~60–80 keys covering existing routers).
3. Seed five system roles + default grants mirroring current `require_*` behavior.
4. Backfill `user_roles` from `users.role`.
5. Keep `users.role` column; trigger or app-level sync on user create/update.

### Phase 1 — Dual read (Sprint 5B–5F)

- New code paths use permissions.
- Legacy `require_role` wrappers delegate to permission checks internally.
- Feature flag `ENABLE_PERMISSION_ENFORCEMENT` default `false`, then `true` per router group.

### Phase 2 — Procurement assignments (Sprint 5D)

- Seed demo assignments for `proc1`/`proc2` on subset of projects in `RIVAR_DEMO_ACCEPTED_BASELINE`.
- Apply scope filters to `/procurement/*` read/list endpoints.

### Phase 3 — Deprecation (future)

- Remove `users.role` column after all clients use `/auth/me` permissions.
- Remove `require_role` helpers.

**Preserve existing users:** no password resets; no deletion of seeded admin.

---

## 11. Testing strategy

| Area | Tests |
|---|---|
| Permission dependencies | unit: grant/deny matrix per endpoint |
| Scope | procurement user sees only assigned items; global scope sees all |
| UserRole union | user with two roles gets combined permissions |
| Admin lockout | cannot delete last `access_control.roles.manage` holder |
| Migration | sqlite + postgres: backfill role mapping counts match user count |
| Frontend | permission-gated nav snapshot tests; assignment panel smoke |
| Regression | R3 hotfix suite unchanged: payment-methods, readiness, Step 3 |

---

## 12. Rollout strategy

1. Deploy schema + seeds with enforcement flag **off**.
2. Verify `GET /auth/me` returns permissions in staging.
3. Enable enforcement on read-only endpoints first (audit, reports export).
4. Enable procurement mutation endpoints after assignment backfill.
5. Demo server `/opt/rivar-demo`: update fixture script with sample assignments; extend `verify_runtime_r3.py` only after R3 checks — add separate `verify_runtime_rbac.py` in Sprint 5F.

**Fallback:** `ENABLE_PERMISSION_ENFORCEMENT=false` restores legacy `require_role` behavior.

---

## 13. Open questions and risks

| # | Question / risk | Recommendation |
|---|---|---|
| 1 | Should PM `project_assignments` merge into unified assignment table? | Keep separate v1; unified view API later |
| 2 | Per-record ownership (created_by) vs explicit assignment? | Both: assignment for workload routing; ownership for edit locks |
| 3 | JWT size if permissions embedded | Keep permissions server-side; `/auth/me` refresh on role change |
| 4 | Custom role explosion | Limit custom role create to `access_control.roles.create`; audit all changes |
| 5 | Current procurement global visibility | **Security gap** — scope enforcement is high priority in 5D |
| 6 | `delete_user` without last-admin check | Fix in 5B before RBAC UI |
| 7 | UsersPage lacks frontend admin guard | Add route guard in 5C; backend already 403 |
| 8 | i18n for permission labels | Feature × action matrix uses `permissions.feature_key` i18n namespace |
| 9 | Finance vs procurement overlap on payment methods | `master_data.payment_methods.edit` → finance; `view` → procurement + wizard |

---

## Consequences

### Positive

- Custom roles without code changes.
- Consistent backend enforcement path.
- Clear procurement workload scoping.
- Auditable access changes.

### Negative

- Migration complexity and dual-read period.
- Every new endpoint must register permissions.
- Performance: permission union per request (mitigate with request-scoped cache).

### Neutral

- Legacy `users.role` remains during transition.
- Optimization/cashflow/decision modules unchanged until enforcement sprint maps their permissions.

---

## Related documents

- `docs/restart-audit/56_sprint5a_access_control_procurement_assignment_architecture.md`
- `docs/architecture/ADR-005-procurement-option-persistence-contract.md` (unchanged)

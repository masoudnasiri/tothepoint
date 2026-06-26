# Sprint 5B — Backend RBAC Foundation

Date: 2026-06-26  
Status: **PASS WITH MINOR ISSUES**  
Sprint type: **Backend implementation** (no Role Management UI; no broad enforcement)

## Baseline

| Item | Value |
|---|---|
| Starting branch | `restart/sprint5a-access-control-procurement-assignment-architecture` |
| Starting commit | `eed35303efdb68be1a680356264908c2ae31558b` |
| New branch | `restart/sprint5b-backend-rbac-foundation` |
| Architecture source | `docs/architecture/ADR-011-role-permission-and-procurement-assignment-model.md` |

## Files changed

| Area | Files |
|---|---|
| Models | `backend/app/models.py` — `Role`, `Permission`, `RolePermission`, `UserRole` |
| Registry | `backend/app/security/permission_registry.py` |
| Service | `backend/app/services/rbac_service.py` |
| Auth | `backend/app/auth.py` — `require_permission`, `require_any_permission`, `require_access_control_manager` |
| Config | `backend/app/config.py` — `ENABLE_SUPER_ADMIN_BYPASS`, `ENABLE_PERMISSION_ENFORCEMENT` (default false) |
| Schemas | `backend/app/schemas.py` — RBAC + `UserMe` |
| APIs | `backend/app/routers/access_control.py` |
| Auth me | `backend/app/routers/auth.py` |
| Users lockout | `backend/app/routers/users.py`, `backend/app/crud.py` |
| Startup | `backend/app/main.py` — RBAC seed on startup |
| Migration SQL | `backend/add_rbac_foundation_tables.sql` |
| Tests | `backend/tests/test_phase15b_rbac_foundation.py`, `backend/tests/conftest.py` |
| Frontend types only | `frontend/src/types/index.ts` — optional `/auth/me` fields |

## Tables added

- `roles`
- `permissions`
- `role_permissions`
- `user_roles`

`users.role` **retained** as legacy mirror. `procurement_assignments` **not** added (deferred to Sprint 5D).

## Permission registry

- File: `backend/app/security/permission_registry.py`
- **59** seeded permissions across features: `access_control`, `users`, `projects`, `project_items`, `procurement`, `master_data`, `audit_logs`, `finance`, `cashflow`, `optimization`, `reports`, `decisions`

## System roles seeded

| Code | Legacy `users.role` |
|---|---|
| `system_admin` | `admin` |
| `access_control_admin` | — |
| `pmo` | `pmo` |
| `project_manager` | `pm` |
| `procurement_specialist` | `procurement` |
| `finance_analyst` | `finance` |

`system_admin` receives all 59 permissions. Other system roles receive grants aligned with current `require_*` behavior.

## Backfill / idempotency

- `ensure_rbac_seeded()` runs on app startup (after `init_db`)
- Upserts permissions and system roles; adds missing `role_permissions`
- Backfills `user_roles` from `users.role` without duplicating rows
- `create_user` / role `update_user` sync `user_roles` for legacy role changes

## API endpoints added

| Method | Path | Guard |
|---|---|---|
| GET | `/access-control/permissions` | access-control manager |
| GET/POST | `/access-control/roles` | access-control manager |
| GET/PUT/DELETE | `/access-control/roles/{role_id}` | access-control manager |
| GET/PUT | `/access-control/roles/{role_id}/permissions` | access-control manager |
| GET/PUT | `/access-control/users/{user_id}/roles` | access-control manager |

Protection: `require_access_control_manager` (legacy `admin` + super-admin bypass, or `access_control.*.manage` permissions).

## `/auth/me` response shape

Extends legacy user fields with:

```json
{
  "id": 1,
  "username": "admin",
  "role": "admin",
  "is_active": true,
  "created_at": "...",
  "permissions": ["projects.view", "..."],
  "roles": [{"code": "system_admin", "display_name": "...", "is_system": true}],
  "permission_enforcement_enabled": false
}
```

No password, token, or hash fields exposed. JWT unchanged (`sub` = username only).

## Lockout protections

- `DELETE /users/{id}` blocked for last access-control manager
- `PUT /users/{id}` with `is_active=false` blocked for last manager
- `PUT /access-control/roles/{id}/permissions` blocked if it would remove last manager capability
- `DELETE /access-control/roles/{id}` blocked for system roles
- `PUT /access-control/roles/{id}` cannot deactivate system roles
- `system_admin` permissions immutable via API

Audit actions: `ROLE_CREATE`, `ROLE_UPDATE`, `ROLE_DEACTIVATE`, `ROLE_PERMISSION_UPDATE`, `USER_ROLE_UPDATE`, `USER_DELETE_BLOCKED_LAST_ADMIN`

## Tests run

| Suite | Result |
|---|---|
| `pytest tests/test_phase15b_rbac_foundation.py -q` | **15 passed** |
| `pytest tests -q` | **182 passed**, 5 skipped |
| R3 focused 13a + 13c | **22 passed** |

## Runtime smoke (`/opt/rivar-demo`)

Recorded after backend redeploy to demo server (compose `rivar-demo`):

| Check | Result |
|---|---|
| `GET /health` | 200 |
| `GET /openapi.json` | 200 (includes `/access-control/*`) |
| `POST /auth/login` | 200 |
| `GET /auth/me` | 200 with `permissions` + `roles` |
| `GET /access-control/permissions` (admin) | 200 |
| `GET /access-control/roles` (admin) | 200 |
| `GET /access-control/roles` (procurement) | 403 |
| `GET /payment-methods` | 200 |
| `GET /procurement-options/19/readiness` | 404 (fixture reseed blocked — see note) |
| R3 `verify_runtime_r3.py` via `verify.sh` | **FAIL** on server — `payment_metadata` column missing on `procurement_cost_components` (pre-existing DB schema drift; unrelated to RBAC) |

**RBAC-specific smoke (admin token):** `me_perms=59`, `me_roles=1`, `ac_perms=200`, `ac_roles=200`, `ac_roles_proc=403` — **PASS**

`/root/pdss_demo` not used.

## Scope control

- No Role Management UI
- No procurement assignment APIs/tables
- No broad `require_permission` on existing routers (`ENABLE_PERMISSION_ENFORCEMENT=false`)
- Package Wizard, Payment Methods, Cost Components unchanged
- `procurement_financials` router still registered

## Known risks

1. ~40 unrelated untracked files remain in working tree — not staged
2. Broad permission enforcement deferred to Sprint 5F
3. Procurement data scope still global until Sprint 5D
4. Demo server requires backend image rebuild for RBAC tables on existing Postgres volume (`create_all` + startup seed)

## Out of scope

- Sprint 5C UI, 5D assignment, 5F enforcement rollout
- Optimization/cashflow/decision changes

## Recommended next sprint

**Sprint 5C — Role Management Frontend**

## Git provenance

Recorded at push time on branch `restart/sprint5b-backend-rbac-foundation`.

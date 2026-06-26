# Sprint 5C-R4 — Full RBAC Inventory E2E Audit

**Sprint:** Sprint 5C-R4 Full Application RBAC Inventory and End-to-End Access Audit  
**Date:** 2026-06-26  
**Status:** PASS WITH MINOR ISSUES  
**Parent branch:** `restart/sprint5c-r3-role-management-usability-delete`  
**Parent commit:** `10fc427dd3b3af796ca8a88202d76b21850ec10c` (short `10fc427`; task spec hash differed by suffix — same commit message)  
**Working branch:** `restart/sprint5c-r4-full-rbac-inventory-e2e-audit`

## Resource preflight

| Check | Result |
|-------|--------|
| Local disk (C:) before | ~46.2 GB free |
| Local disk after | ~46.2 GB free (no heavy builds) |
| Watch mode | Not used |
| Coverage | Not used |
| Full frontend build | Not run |
| Broad Jest suite | Not run (known hang risk) |
| Heavy verification | Demo API via httpx; backend focused pytest |

## Phase A — Inventory (complete)

- Frontend routes/pages extracted from `App.tsx`, `Layout.tsx`, `frontend/src/pages/`.
- Backend endpoints extracted from `backend/app/routers/*.py` (267 endpoints).
- Permission registry from `permission_registry.py` (67 keys).
- Docs reviewed: ADR-011, `56_*`–`63_*`, `08_recommended_continuation_plan.md`.
- Master matrix: `64_sprint5c_r4_full_rbac_inventory_matrix.md`.

## Phase B — Targeted fixes (complete)

### 1. User-reported Users access issue

**Root cause (confirmed):** Frontend already allowed section access via `users.view` (`canAccessUsersAccessControlSection` / `canViewUsersSection`). Backend `/users/*` endpoints used `require_admin()` only, so permissioned non-admin users received **403** when loading the Users list.

**Runtime evidence (demo, pre-deploy):**

```
OK: users.view user has users.view permission  (/auth/me)
FAIL: users.view user list users expected 200 got 403  (GET /users/)
```

**Fix:** Added `require_users_permission()` (always-on, mirrors pilot pattern) and wired `/users` CRUD to `users.view/create/edit/delete`.

**Local tests after fix:** 3/3 PASS in `test_phase15c_r4_users_permission_enforcement.py`.

### 2. Pilot badge / matrix labels

**Before:** `PILOT_ENFORCED_PREFIXES` included `access_control.*` and `users.*`, causing misleading "Pilot enforced" chips on most matrix rows.

**After:**

- **Pilot enforced** chip: `master_data.items.*`, `master_data.suppliers.*` only.
- **Enforced** chip (new): `users.*`, `access_control.*`.

**Tests:** `frontend/src/utils/permissionLabels.test.ts` (unit logic).

### 3. Frontend Users tab gating (verified, no change required)

- Route: `UsersAccessControlRoute` uses `canAccessUsersAccessControlSection` — does **not** require `access_control.roles.manage` for Users tab.
- Tabs: Users tab requires `users.view`; Roles tab requires `canManageAccessControl`; User Roles tab requires `access_control.user_roles.view/edit`.

## Runtime test plan

| ID | Scenario | Method |
|----|----------|--------|
| R4-01 | Health / OpenAPI | GET demo `/health`, `/openapi.json` |
| R4-02 | users.view list users | API as sprint5c_r4_users_view_only_user |
| R4-03 | users.view cannot create | POST /users/ → 403 |
| R4-04 | users.view cannot access AC roles | GET /access-control/roles → 403 |
| R4-05 | Items pilot deny | users.view-only user → GET /items-master → 403 |
| R4-06 | Admin regression | admin payment-methods 200 |
| R4-07 | Local pytest | users permission enforcement |
| R4-08 | Badge logic | permissionLabels unit test |

## Runtime test results

| Test | Pre-deploy demo | Post-fix local |
|------|-----------------|----------------|
| /health | 200 PASS | — |
| /openapi.json | 200 PASS | — |
| /auth/me permissions | PASS | PASS |
| users.view GET /users/ | **403 FAIL** | **200 PASS** |
| users.view POST /users/ | not reached | 403 PASS |
| Items pilot deny | PASS (script) | PASS |
| Backend pytest | — | 3 passed |
| verify.sh on demo | Not run (no SSH) | Pending deploy |

**Temporary audit users on demo:** Created/updated by smoke script (`sprint5c_r4_users_view_only`, `sprint5c_r4_users_view_only_user`, etc.). Passwords not recorded in this document.

## Remaining gaps by severity

### Critical (resolved in branch, pending deploy)

- ~~users.view blocked on backend~~ → fixed in branch

### High

- Most product modules (projects, procurement, finance, optimization) still legacy-role gated despite registered permissions.
- Navigation uses legacy `users.role` arrays; permission grants do not affect menu visibility except Users & Access Control and Items/Suppliers pilot helpers.
- User Roles tab backend still requires full access-control manager, not granular `access_control.user_roles.view`.

### Medium

- Direct routes (e.g. `/optimization`) reachable without nav role check if user knows URL.
- Payment Methods / Cost Components permissions registered but not enforced.

### Low / Future

- 40+ permission keys registered for future sprints per ADR-011.
- CurrencyManagementPage exists but not routed.

## Tests added/updated

| File | Result |
|------|--------|
| `backend/tests/test_phase15c_r4_users_permission_enforcement.py` | 3 passed |
| `frontend/src/utils/permissionLabels.test.ts` | Added (not run locally — Jest hang risk) |
| `backend/scripts/sprint5c_r4_runtime_smoke.py` | Demo pre-deploy: FAIL at users list (expected) |
| `deployment/rivar-installer/run_sprint5c_r4_smoke.sh` | Added for post-deploy |

## Scope control

- Procurement Assignment: **not started**
- Global RBAC rewrite: **not done**
- Package Wizard: **unchanged**
- Payment Methods location: **unchanged**
- Optimization/cashflow/decision logic: **unchanged**

## Git provenance

To be filled after commit/push:

- Commit: (see final report)
- Branch: `restart/sprint5c-r4-full-rbac-inventory-e2e-audit`
- Remote: `origin`

## Recommendation

**Create Sprint 5C-R4-Fix** (or deploy this branch to demo) to close runtime verification on `/opt/rivar-demo`, then proceed toward Sprint 5D only after demo smoke PASS for users.view and badge UX sign-off.

Do **not** start Sprint 5D Procurement Assignment until:

1. This branch is deployed and `run_sprint5c_r4_smoke.sh` PASS on demo.
2. Stakeholders accept remaining High gaps as documented follow-up.

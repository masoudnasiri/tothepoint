# Sprint 5C-R1 — RBAC UX Consolidation and Master Data Permission Pilot

Date: 2026-06-26  
Status: **PASS WITH MINOR ISSUES**  
Sprint type: **Controlled transition** (pilot enforcement for Items Master + Suppliers only)

## Baseline

| Item | Value |
|---|---|
| Starting branch | `restart/sprint5c-role-management-frontend` |
| Starting commit | `95c6a876f699cc8013d79c79625b9c7309a7a693` |
| New branch | `restart/sprint5c-r1-rbac-ux-masterdata-permission-pilot` |

## User-reported issues addressed

1. User create/edit exposed only legacy roles — **fixed** with RBAC role multi-select (create + edit).
2. Users and Access Control were duplicate top-level nav items — **consolidated** to **Users & Access Control** (`/users-access`).
3. Custom roles without master_data permissions still allowed Items/Suppliers write via legacy role — **fixed** with backend `require_pilot_permission` and frontend pilot gating.

## Navigation consolidation

| Item | Detail |
|---|---|
| Unified menu | `navigation.usersAccessControl` — EN: Users & Access Control; FA: کاربران و کنترل دسترسی |
| Route | `/users-access` with tabs: Users, Roles & Permissions, User Role Assignment |
| Redirects | `/users` → `/users-access?tab=users`; `/access-control` → `/users-access?tab=roles` |
| Visibility | `canAccessUsersAccessControlSection` — `users.view`, access-control manage permissions, or legacy `admin` |

## User create/edit RBAC role assignment

- Legacy `users.role` preserved and labeled **Legacy/base role (compatibility)**.
- RBAC roles loaded from `GET /access-control/roles`; assigned via `PUT /access-control/users/{id}/roles`.
- Create flow: user API then role assignment; partial failure surfaced as warning.
- Edit flow: loads and updates RBAC roles; lockout errors from backend shown in UI.

## Permission matrix UX

- Grouped table matrix by feature group (Access Control, Users, Projects, Procurement, Master Data, …).
- Translated feature/action labels via `permissionLabels.ts` + i18n keys.
- Raw `permission_key` shown in checkbox tooltip / secondary feature key text.
- Advisory note for not-yet-globally-enforced permissions (Items Master/Suppliers are pilot-enforced).

## Permission registry / seeds

New keys in `permission_registry.py`:

- `master_data.items.view|create|edit|delete`
- `master_data.suppliers.view|create|edit|delete`

### System role grant mapping (legacy-aligned)

| System role | Items Master | Suppliers |
|---|---|---|
| `system_admin` | all | all |
| `pmo_manager` | view/create/edit | view/create/edit |
| `project_manager` | view/create/edit | view/create/edit |
| `finance_analyst` | view/create/edit | view/create/edit |
| `procurement_specialist` | **view only** | **view only** |

Seed remains idempotent via `ensure_rbac_seeded`.

## Backend pilot enforcement

- `require_pilot_permission()` in `auth.py` — always enforces pilot routes regardless of `ENABLE_PERMISSION_ENFORCEMENT`.
- `user_has_pilot_permission()` — RBAC `user_roles` only; bypass for legacy `admin` and assigned `system_admin`.
- Applied to `items_master.py` and `suppliers.py` list/get/create/update/delete (+ supplier contacts/documents).

## Frontend pilot enforcement

- `hasPilotPermission` / `canView|Create|Edit|Delete*Master|Suppliers` in `permissions.ts`.
- `ItemsMasterPage` and `SuppliersPage` gate actions and show access denied without view permission.
- Payment Methods and Cost Components unchanged.

## Tests run

```text
python -m pytest tests/test_phase15c_r1_master_data_pilot.py tests/test_phase15b_rbac_foundation.py -q
```

**20 passed**

```text
npm test -- --watchAll=false --testPathPattern="Layout.(accessControl|usersAccessControl)|permissions.(test|pilot)|AccessControlPage"
```

**PASS** (navigation, permissions, Access Control page)

## Runtime smoke on `/opt/rivar-demo`

Deferred to deployment window if not executed in this session. Prior 5C demo path remains `/opt/rivar-demo` (not `/root/pdss_demo`).

Recommended manual checks after deploy:

- Unified menu single entry
- Restricted role (`users.view` only) cannot write Items/Suppliers (403)
- Admin and permissioned roles retain expected access
- `/payment-methods`, readiness, Package Wizard Step 3 unchanged

## Known risks

- Users with only legacy `users.role` and no `user_roles` rows lose Items/Suppliers write until RBAC roles are assigned (intended pilot behavior).
- Global `ENABLE_PERMISSION_ENFORCEMENT` still off; other modules remain legacy-gated.
- `UsersPage` RBAC role picker requires access-control list API (admin or role manager).

## Out of scope (confirmed)

- Procurement Assignment backend/frontend
- Broad global permission enforcement
- Package Wizard / Payment Methods / Cost Components changes
- `users.role` removal

## Git provenance

Branch: `restart/sprint5c-r1-rbac-ux-masterdata-permission-pilot`  
Commit: _(filled after push)_

## Recommended next sprint

**Sprint 5D Procurement Assignment Backend**

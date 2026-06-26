# Sprint 5C — Role Management Frontend

Date: 2026-06-26  
Status: **PASS WITH MINOR ISSUES**  
Sprint type: **Frontend implementation** (no procurement assignment; no broad permission enforcement)

## Baseline

| Item | Value |
|---|---|
| Starting branch | `restart/sprint5b-r1-demo-runtime-closure` |
| Starting commit | `fb9336e20d1d461e9db1e6f5ac5c151abf57340f` |
| New branch | `restart/sprint5c-role-management-frontend` |
| Architecture references | ADR-011, `57_*`, `58_*` |

## Frontend pages / components added

| File | Purpose |
|---|---|
| `frontend/src/pages/AccessControlPage.tsx` | Role list, create/edit, permission matrix, user-role assignment |
| `frontend/src/components/AccessControlRoute.tsx` | Route guard for Access Control page only |
| `frontend/src/utils/permissions.ts` | `hasPermission`, `hasAnyPermission`, `usePermissions`, `canManageAccessControl` |

## API client methods added

`accessControlAPI` in `frontend/src/services/api.ts`:

- `GET /access-control/permissions`
- `GET/POST /access-control/roles`
- `GET/PUT/DELETE /access-control/roles/{role_id}`
- `GET/PUT /access-control/roles/{role_id}/permissions`
- `GET/PUT /access-control/users/{user_id}/roles`

## Types added/updated

`frontend/src/types/index.ts`:

- `Permission`, `Role`, `RoleCreate`, `RoleUpdate`
- `RolePermissionsResponse`, `RolePermissionsUpdate`
- `UserRolesResponse`, `UserRolesUpdate`, `UserRoleSummary`
- `User` retains legacy `role`; `/auth/me` RBAC fields remain optional

## Route / menu changes

| Change | Detail |
|---|---|
| Route | `/access-control` wrapped in `AccessControlRoute` |
| Navigation | `navigation.accessControl` item with `accessControlOnly` flag |
| Visibility | `canManageAccessControl(user)` — legacy `admin` fallback or access-control manage permissions |
| Other menus | Unchanged — still use legacy `roles` arrays |

## Permission helper / guard behavior

- `canManageAccessControl`: mirrors backend transition — `admin` role allowed; otherwise requires one of `access_control.roles.manage`, `access_control.permissions.manage`, `access_control.user_roles.edit`
- Unauthorized direct route: access denied alert (no crash, no management UI)
- No broad permission guards added to existing pages

## i18n

New `accessControl.*` keys in `en.json` and `fa.json` (navigation + page strings).  
Persian payment schedule terminology in `procurement.*` untouched.

## Tests run

```text
npm test -- --watchAll=false --testPathPattern="permissions.test|AccessControlRoute.test|Layout.accessControlNavigation.test|AccessControlPage.test|LoginPage.smoke.test|Layout.masterDataNavigation.test|PackageWizardStep3" --forceExit
```

**22 passed** (7 suites)

```text
CI=false npm run build
```

**PASS** (pre-existing eslint warnings only)

Backend tests: **skipped** (no backend files changed)

## Runtime smoke on `/opt/rivar-demo`

Deployed frontend `src/` to `/opt/rivar-demo`; `verify.sh` **PASS**; R3 runtime **PASS**.

| Check | Result |
|---|---|
| `/health` | 200 |
| `/openapi.json` | 200 |
| `/auth/login` | OK |
| `/auth/me` | 59 permissions, 1 role |
| `/access-control/permissions` (admin) | 200 |
| `/access-control/roles` (admin) | 200 |
| `/access-control/roles` (procurement) | 403 |
| `/payment-methods` | 200 |
| `/procurement-options/21/readiness` | 200 |
| Frontend `/` | 200 |
| Frontend `/access-control` | 200 |
| Create temp role `sprint5c_smoke_role` | 201 |
| Update temp role metadata | 200 |
| Save temp role permissions | 200 |
| Deactivate temp role | 200 |
| Delete system role blocked | 403 |
| Package Wizard Step 3 (verify.sh) | PASS |

Fixture option ids after verify: ready **21**, not ready **22**.

## Scope control

| Area | Changed |
|---|---|
| Backend product code | No |
| Package Wizard | No |
| Payment Methods placement | No |
| Cost Components | No |
| Procurement assignment | No |
| Optimization / cashflow / decision | No |
| Broad permission enforcement on routes | No |

## Known risks

1. **Permission matrix loads counts per role** — N+1 API calls on initial load (acceptable for current role count).
2. **Frontend guard is advisory** — backend remains source of truth; `ENABLE_PERMISSION_ENFORCEMENT` still off globally.
3. **Login smoke test** — added i18n mock to stabilize pre-existing flaky assertion.
4. **CI=true local build** — fails on pre-existing eslint warnings; Docker/demo build uses `npm start` path.

## Out of scope (deferred)

- Procurement assignment backend/frontend
- Permission-driven navigation for all menus
- Broad route permission enforcement (Sprint 5F)
- Users page multi-role UI refactor

## Git provenance

| Item | Value |
|---|---|
| Branch | `restart/sprint5c-role-management-frontend` |
| Parent | `fb9336e20d1d461e9db1e6f5ac5c151abf57340f` |
| Commit message | `feat: add role management frontend` |

## Recommended next sprint

**Sprint 5D Procurement Assignment Backend**

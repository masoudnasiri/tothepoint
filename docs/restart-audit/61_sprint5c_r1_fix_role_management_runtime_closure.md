# Sprint 5C-R1-Fix — Role Management Runtime Closure

Date: 2026-06-26  
Status: **PASS WITH MINOR ISSUES**  
Sprint type: **Closure / fix** (runtime evidence + UsersPage RBAC integration tests)

## Baseline

| Item | Value |
|---|---|
| Starting branch | `restart/sprint5c-r1-rbac-ux-masterdata-permission-pilot` |
| Starting commit | `8e0770a45cae3bf243287a8ee298babac88c4dcf` |
| New branch | `restart/sprint5c-r1-fix-role-management-runtime-closure` |

## Original runtime gap

Sprint 5C-R1 was accepted at code level **PASS WITH MINOR ISSUES** because:

1. `/opt/rivar-demo` had not been redeployed with 5C-R1 unified Users & Access Control UX.
2. `UsersPage` RBAC role assignment integration tests were missing.
3. Restricted/permissioned role runtime smoke was not recorded on the official demo path.

## UsersPage integration test added

**File:** `frontend/src/pages/UsersPage.rbac.test.tsx` (6 tests)

| Test | Result |
|---|---|
| Create form includes legacy/base role + RBAC multi-select | PASS |
| Create calls `usersAPI.create` then `accessControlAPI.updateUserRoles` | PASS |
| Edit loads current RBAC roles via `getUserRoles` | PASS |
| Edit updates RBAC roles via `updateUserRoles` | PASS |
| Backend lockout / role assignment error surfaced on edit | PASS |
| Create partial failure (user created, roles fail) shows warning | PASS |

**Bugfix:** `UsersPage.tsx` — on create, role assignment warning was cleared by `resetForm()`; early `return` preserves warning.

## Deployment steps

| Step | Detail |
|---|---|
| Server | `193.162.129.58` |
| Path | `/opt/rivar-demo` |
| Compose project | `rivar-demo` |
| Forbidden path used | **No** (`/root/pdss_demo` not used) |
| Method | Tarball `scp` from accepted parent commit + `bash deployment/rivar-installer/install.sh` |
| CRLF workaround | `sed -i 's/\r$//' /opt/rivar-demo/deployment/rivar-installer/*.sh` (Windows tarball line endings) |
| Branch/commit deployed | Parent `restart/sprint5c-r1-rbac-ux-masterdata-permission-pilot` @ `8e0770a` |

## Frontend bundle verification

Verified inside `rivar-demo-frontend` container source (dev `npm start` image):

| Artifact | Present |
|---|---|
| `/users-access` routes (`App.tsx`) | Yes |
| `usersAccessControl` / `usersAccessControlOnly` nav (`Layout.tsx`) | Yes |
| Access Control / permission matrix (`AccessControlPage.tsx`) | Yes |
| Items/Suppliers pilot gating (`permissions.ts`) | Yes |
| EN/FA `usersAccessControl`, `permissionMatrix` i18n | Yes (source) |

HTTP: `GET /users-access` → **200**; `/users` and `/access-control` redirect to unified section (route definitions in `App.tsx`).

## Backend bundle verification

Verified inside `rivar-demo-backend` container:

| Artifact | Present |
|---|---|
| `require_pilot_permission` (`auth.py`) | Yes |
| `master_data.items.*` checks (`items_master.py`, `permission_registry.py`) | Yes |
| `master_data.suppliers.*` checks (`suppliers.py`) | Yes |

## verify.sh result

```bash
bash /opt/rivar-demo/deployment/rivar-installer/verify.sh
```

| Check | Result |
|---|---|
| Overall | **PASS** |
| Schema migrations | Applied |
| Fixture reseed | OK |
| Readiness (`/procurement-options/{id}/readiness`) | OK |
| R3 runtime (`verify_runtime_r3.py`) | OK |

## RBAC runtime smoke

```bash
bash /opt/rivar-demo/deployment/rivar-installer/run_sprint5c_r1_smoke.sh
```

**Result: PASS** (includes restricted + permissioned roles)

### Restricted role smoke

| Item | Value |
|---|---|
| Role | `sprint5c_r1_smoke_restricted` (permissions: `users.view` only) |
| User | `sprint5c_r1_smoke_user` |
| Items Master list/create API | **403** |
| Suppliers list/create API | **403** |
| Admin items list | **200** |

### Permissioned role smoke

| Item | Value |
|---|---|
| Role | `sprint5c_r1_smoke_permissioned` (`master_data.items.view`, `master_data.suppliers.view`) |
| User | `sprint5c_r1_smoke_perm_user` |
| Items/suppliers list (view) | **200** |
| Items/suppliers create (no create perm) | **403** |

### Smoke cleanup

Temporary smoke roles/users **left active** on demo DB for repeatable verification. Names are prefixed `sprint5c_r1_smoke_*`.

## Runtime UI smoke (admin)

| Check | Result |
|---|---|
| `/health` | 200 |
| `/openapi.json` | 200 |
| `/auth/login` | Works (verify.sh + smoke) |
| `/auth/me` roles + permissions | Confirmed in smoke |
| `/users-access` | 200 |
| Unified menu (single Users & Access Control) | Verified via `Layout.tsx` + nav tests |
| Duplicate Users + Access Control top-level items | Removed (consolidated) |
| Users / Roles & Permissions / User Role Assignment tabs | Implemented in `UsersAccessControlPage` |
| Permission matrix translated labels | `permissionLabels.ts` + i18n; raw keys secondary |
| Enforcement pilot notice | Present in Access Control page |

Restricted-user **UI** denial for Items Master / Suppliers follows frontend pilot gating (`hasPilotPermission`); API denial confirmed by runtime smoke.

## Regression smoke

| Check | Result |
|---|---|
| `/payment-methods` (admin) | 200 (smoke) |
| Readiness after fixture seed | OK (`verify.sh`) |
| Package Wizard Step 3 | PASS (frontend regression tests) |
| BASE_PRICE default non-removable | PASS (Package Wizard tests) |
| Optional cost components | Unchanged |
| Component payment schedule | R3 verify PASS |
| Persian payment schedule terminology | Unchanged (3A-R3 baseline) |
| Payment Methods in Master Data | Unchanged |
| Cost Components source of truth | Unchanged |

## Tests run

```text
python -m pytest tests/test_phase15c_r1_master_data_pilot.py tests/test_phase15b_rbac_foundation.py -q
→ 20 passed

python -m pytest -q
→ 187 passed, 5 skipped

npm test -- --watchAll=false --testPathPattern="(AccessControl|UsersPage.rbac|Layout.usersAccessControl|Layout.accessControl|ItemsMaster.*pilot|PackageWizard)"
→ 33 passed (8 suites)

CI=false npm run build
→ PASS
```

## Files changed (this fix sprint)

| File | Change |
|---|---|
| `frontend/src/pages/UsersPage.rbac.test.tsx` | New RBAC integration tests |
| `frontend/src/pages/UsersPage.tsx` | Preserve role-assign warning on partial create failure |
| `backend/scripts/sprint5c_r1_runtime_smoke.py` | Demo RBAC runtime smoke (restricted + permissioned) |
| `deployment/rivar-installer/run_sprint5c_r1_smoke.sh` | Installer wrapper for smoke inside backend container |
| `docs/restart-audit/61_sprint5c_r1_fix_role_management_runtime_closure.md` | This document |
| `docs/restart-audit/08_recommended_continuation_plan.md` | Sprint pointer update |

## Known risks

- Demo frontend runs dev server (`npm start`); production minified bundle grep not used — source-level verification applied.
- Windows→Linux tarball may introduce CRLF in installer `.sh` scripts; `sed` fix required before `install.sh` / `verify.sh`.
- Smoke users/roles remain on demo Postgres volume by design.
- Global `ENABLE_PERMISSION_ENFORCEMENT` still off outside Items/Suppliers pilot.

## Out of scope (confirmed)

- Sprint 5D Procurement Assignment — **not started**
- Broad RBAC beyond Items Master / Suppliers pilot
- JWT, Package Wizard logic, Payment Methods placement, Cost Components changes
- `users.role` removal

## Git provenance

See sprint closure commit on `restart/sprint5c-r1-fix-role-management-runtime-closure`.

## Recommendation

**Proceed to Sprint 5D Procurement Assignment Backend** — 5C-R1 runtime closure complete on `/opt/rivar-demo`; remaining issues are minor (CRLF deploy hygiene, dev-mode frontend image).

# Sprint 5C-R4-Fix — RBAC Runtime Deployment Closure

Date: 2026-06-26  
Status: **PASS WITH MINOR ISSUES**  
Sprint type: **Deployment / runtime closure** (no new product features)

## Baseline

| Item | Value |
|---|---|
| Starting branch | `restart/sprint5c-r4-full-rbac-inventory-e2e-audit` |
| Starting commit | `7801c5e0e51f254385e1c6fe72fc9b5b2d721b1f` |
| New branch | `restart/sprint5c-r4-fix-rbac-runtime-deployment-closure` |
| Demo server | `193.162.129.58` |
| Demo path | `/opt/rivar-demo` |
| Forbidden path used | **No** (`/root/pdss_demo` not used) |

## Before-deploy evidence

| Check | Result |
|---|---|
| Backend `require_users_permission` in running container | **Missing** (grep count 0) |
| Backend `users.py` guards | `require_admin()` only |
| Frontend `ENFORCED_PREFIXES` in running container | **Missing** (grep count 0) |
| `DEPLOYED_COMMIT.txt` | Missing |
| Demo GET `/users/` as `users.view` user | **403** |
| Demo `/health`, `/openapi.json` | 200 |
| User-visible symptom | Pilot wording still broad; Users page/API denied for permissioned non-admin |

## Deployment

| Step | Detail |
|---|---|
| Method | `git archive` tarball (`backend/`, `frontend/`, `deployment/rivar-installer/`, smoke script) → `scp` → extract to `/opt/rivar-demo` |
| Branch deployed | `restart/sprint5c-r4-full-rbac-inventory-e2e-audit` |
| Commit deployed | `7801c5e0e51f254385e1c6fe72fc9b5b2d721b1f` |
| Backend rebuild | `docker compose build --no-cache backend` |
| Frontend rebuild | `docker compose build --no-cache frontend` |
| Containers | Recreated and healthy |
| Schema | `apply_r3_schema_migrations.sh` (idempotent) |
| CRLF hygiene | Restored installer `.sh` from tarball + `dos2unix` via Alpine container (Windows tarball had corrupted scripts when fixed with naive `perl`) |
| Provenance file | `/opt/rivar-demo/docs/restart-audit/DEPLOYED_COMMIT.txt` |

## After-deploy code evidence

| Check | Result |
|---|---|
| Backend container: `require_users_permission` | **Present** in `/app/app/auth.py` |
| Backend container: `users.py` uses `require_users_permission` | **Yes** |
| Frontend container: `ENFORCED_PREFIXES` | **Present** in `permissionLabels.ts` |
| Frontend container: `getFeatureEnforcementBadge` | **Present** in `RoleManagementPanel.tsx` |
| `DEPLOYED_COMMIT.txt` | Records branch + commit `7801c5e…` |
| Container age | Backend/frontend recreated ~2026-06-26T15:28 UTC |

## verify.sh

```bash
bash /opt/rivar-demo/deployment/rivar-installer/verify.sh
```

| Check | Result |
|---|---|
| Overall | **PASS** |
| Frontend routes | OK |
| `/health`, `/openapi.json` | OK |
| Fixture reseed | OK (`RIVAR_DEMO_ACCEPTED_BASELINE`) |
| R3 runtime (`verify_runtime_r3.py`) | **PASS** (component payment schedule, readiness, BASE_PRICE path) |
| Readiness ready/not-ready | OK |

## Users access runtime test (primary acceptance)

Test roles/users created by `sprint5c_r4_runtime_smoke.py` (passwords not recorded).

| Role | Permissions | User |
|---|---|---|
| `sprint5c_r4_users_view_only` | `users.view` | `sprint5c_r4_users_view_only_user` |
| `sprint5c_r4_users_manager` | `users.view/create/edit/delete` (no `access_control.roles.manage`) | `sprint5c_r4_users_manager_user` |

| Test | Result |
|---|---|
| `/auth/me` includes `users.view` | **PASS** |
| GET `/users/` as view-only user | **200 PASS** (was 403 pre-deploy) |
| POST `/users/` as view-only user | **403 PASS** |
| GET `/access-control/roles` as view-only user | **403 PASS** |
| GET `/users/` as users manager | **200 PASS** |
| `/users-access` HTTP | **200** |
| Roles tab without `access_control.roles.manage` | Restricted by frontend tab gating + API 403 on AC endpoints |

## Permission matrix badge runtime test

Source-level verification in deployed frontend container (dev `npm start` image):

| Check | Result |
|---|---|
| `PILOT_ENFORCED_PREFIXES` | Only `master_data.items.*`, `master_data.suppliers.*` |
| `ENFORCED_PREFIXES` | `users.*`, `access_control.*` |
| `getFeatureEnforcementBadge` used in matrix UI | **Yes** |
| Future groups (projects/procurement/finance/etc.) | No pilot badge in code path |
| Persian i18n | `enforced` / `pilotEnforced` keys present; UI not manually browsed in browser this session |

**Before:** pilot chip prefix included `access_control.*` and `users.*` (misleading).  
**After deploy:** corrected logic live in container source.

## Regression smoke

| Check | Result |
|---|---|
| `/health` | 200 |
| `/openapi.json` | 200 |
| Admin `/auth/login`, `/auth/me` | OK |
| `/payment-methods` (admin) | 200 |
| Readiness after fixture seed | OK (`verify.sh` + R3 verify) |
| `run_sprint5c_r1_smoke.sh` (Items/Suppliers pilot) | **PASS** |
| Package Wizard Step 3 | **PASS** via R3 runtime verify (component payment schedule save/reopen) |
| BASE_PRICE / component schedule | Unchanged (R3 verify PASS) |
| Payment Methods in Master Data | Unchanged |
| Procurement Assignment | **Not started** |
| Optimization/cashflow/decision logic | **Unchanged** in deploy commit |

## Deployment hygiene notes (minor)

1. Windows-origin tarball requires `dos2unix` on installer `.sh` before `verify.sh` — documented in `deploy_update_5c_r4.sh`.
2. Naive `perl -pi -e 's/\r\n/\n/g'` from PowerShell **corrupted** scripts (stripped `r` characters) — **do not repeat**; use tarball restore + `dos2unix`.
3. Demo frontend runs dev server image; badge verification is source-level inside container.

## Scope control

- No new RBAC features beyond 5C-R4 code already in `7801c5e`.
- No Procurement Assignment, Package Wizard, Payment Methods, Cost Components, or optimization changes.
- Closure branch adds deployment script hardening + audit docs only.

## Git provenance

See closure commit on `restart/sprint5c-r4-fix-rbac-runtime-deployment-closure`.

## Recommendation

**Proceed toward Sprint 5D Procurement Assignment Backend** only after product owner accepts documented **High** RBAC gaps (legacy nav vs permissions on projects/procurement/finance). Runtime closure for 5C-R4 user-reported issues is **complete on demo**.

Remaining follow-up (optional, low priority):

- Commit full endpoint extract JSON to audit trail or CI artifact.
- Fix route-extraction regex for multiline `/users-access` in inventory script.
- Complete `65_*` git provenance placeholder from 5C-R4 doc.

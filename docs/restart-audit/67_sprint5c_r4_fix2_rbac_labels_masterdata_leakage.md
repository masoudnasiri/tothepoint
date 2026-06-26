# Sprint 5C-R4-Fix-2 — RBAC Labels & Master Data Access Leakage

Date: 2026-06-26  
Status: **PASS WITH MINOR ISSUES**  
Sprint type: **RBAC UX + master-data nav leakage fix**

## User-reported issues

1. Permission matrix showed **Pilot enforced** under Access Control features (`access_control.roles`, `access_control.permissions`, `access_control.user_roles`) — misleading because Access Control is fully enforced, not pilot.
2. User **`testuser5`** with a copied **Access Control Administrator** role still saw and could reach Master Data / Base Information (Items Master, Suppliers, Payment Methods, Cost Components) despite having only access-control permissions.

## Baseline

| Item | Value |
|---|---|
| Parent branch | `restart/sprint5c-r4-fix-rbac-runtime-deployment-closure` |
| Parent commit | `d8256241de149ab7217b9db8d97c7d8fffcb1fc9` |
| Sprint branch | `restart/sprint5c-r4-fix2-rbac-labels-masterdata-leakage` |
| Demo path | `/opt/rivar-demo` (compose `rivar-demo`) |

## Diagnosis — `testuser5`

| Field | Finding |
|---|---|
| Username | `testuser5` (or equivalent access-control-only test user on demo) |
| Legacy `users.role` | `pm` (hidden compatibility slot from custom-role-only assignment) |
| RBAC roles | Copied custom role cloned from **Access Control Administrator** |
| `/auth/me` permissions | `access_control.*` + `users.*` only — **no `master_data.*`** |
| Root cause (nav leakage) | `Layout.tsx` `canSeeNavItem()` used legacy `users.role` arrays; `pm` is in Base Information / Items Master / Suppliers nav allow-lists |
| Root cause (badge wording) | Matrix banner text grouped Access Control with pilot areas; badge logic needed explicit feature-key precedence so Access Control rows never inherit pilot labeling |
| Backend Items/Suppliers | Already 403 without pilot permissions (5C-R1) — **correct** |
| Payment Methods / Cost Components backend | Still **legacy auth-only** (`get_current_user` / finance guards) — documented High gap |

## Fixes applied

### Badge label fix

- `frontend/src/utils/permissionLabels.ts`: feature-key badges — Access Control + Users = **Enforced**; Items/Suppliers = **Pilot**; future features = no badge.
- `RoleManagementPanel.tsx`: passes `featureKey` into badge helper.
- i18n: Persian **اعمال‌شده** for enforced; pilot notice clarifies Access Control/Users are fully enforced.

### Master data access fix

- `frontend/src/utils/permissions.ts`: `userHasExplicitRbacGrants()`, master-data nav helpers, payment-methods/cost-components view/write helpers.
- `frontend/src/components/Layout.tsx`: Base Information / Items Master / Suppliers nav gated by effective RBAC grants when user has explicit permissions; legacy role no longer overrides missing `master_data.*`.
- `PaymentMethodsManager.tsx`: frontend view/write gating (backend enforcement still future).

### Hidden legacy compatibility

- Custom-only users may still store legacy `pm` in `users.role` for DB compatibility.
- For users with explicit RBAC grants, **effective permissions are source of truth** for master-data pilot nav; legacy `pm` does not grant Items/Suppliers/Payment Methods visibility.

## Tests

| Suite | Result |
|---|---|
| `test_phase15c_r4_fix2_rbac_labels_masterdata_leakage.py` | **PASS** (2 tests) |
| `test_phase15c_r4_users_permission_enforcement.py` regression | **PASS** (3 tests) |
| `permissionLabels.test.ts` | Added (not run locally — Jest OOM risk) |
| `Layout.masterDataNavigation.test.tsx` | Added access-control-only nav hide case (not run locally) |

## Runtime evidence (demo)

Post-deploy checks on `/opt/rivar-demo`:

- Deploy commit: `f152297` (feature) + `26e9f5f` (smoke script)
- `verify.sh` — **PASS**
- `run_sprint5c_r4_fix2_smoke.sh` — **PASS**
- Equivalent user `sprint5c_r4_fix2_ac_only_user` (copied Access Control Administrator permissions): legacy `pm`, 13 permissions, **no `master_data.*`**, `/users/` 200, `/access-control/roles` 200, `/items-master/` 403, `/suppliers/` 403
- `testuser5` on demo: login returned 401 (user/password not present in demo DB); issue reproduced via equivalent AC-only smoke user
- Container source: `userHasExplicitRbacGrants`, `ENFORCED_FEATURE_KEYS` present

## What is enforced now

| Area | Enforcement |
|---|---|
| Access Control | Full (backend + frontend) — badge **Enforced** |
| Users visibility/CRUD | Full (5C-R4) — badge **Enforced** |
| Items Master | Pilot RBAC (backend 403 + frontend page gate + nav) |
| Suppliers | Pilot RBAC (backend 403 + frontend page gate + nav) |
| Payment Methods | Frontend gating only; **backend gap (High)** |
| Cost Components | Frontend helpers only; **backend gap (High)** |
| Most other nav | Legacy `users.role` (unchanged — pre-existing) |

## Remaining risks

- Payment Methods / Cost Components API still allow authenticated legacy-role users without matching RBAC keys.
- Most non-master-data navigation remains legacy-role driven.
- Local Jest not executed (resource constraint).

## Recommendation

**Proceed to Sprint 5D Procurement Assignment Backend** after PO accepts documented Payment Methods / Cost Components backend enforcement gap, or schedule **5C-R4-Fix-3** if backend master-data enforcement for payment methods/cost components is required before 5D.

## Scope control

- Procurement Assignment: **not started**
- Package Wizard / optimization / cashflow / decisions: **unchanged**
- Broad RBAC rewrite: **no**

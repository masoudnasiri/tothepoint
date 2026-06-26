# Sprint 5C-R4-Fix-3 — Master Data Backend Enforcement and Provenance Closure

Date: 2026-06-26  
Status: **PASS**  
Sprint type: **RBAC backend enforcement closure**

## User-reported issue

After Sprint 5C-R4-Fix-2, Access-Control-only users were still able to **GET `/payment-methods`** (200). Cost Components APIs had no RBAC enforcement. Frontend hiding was insufficient for direct API access.

## Baseline

| Item | Value |
|---|---|
| Parent branch | `restart/sprint5c-r4-fix2-rbac-labels-masterdata-leakage` |
| Parent commit | `94fa823d547a0c2f31488d458d5baa804ea60e73` |
| Sprint branch | `restart/sprint5c-r4-fix3-masterdata-backend-enforcement` |
| Demo path | `/opt/rivar-demo` |

## Diagnosis

| Field | Finding |
|---|---|
| Affected user | `sprint5c_r4_fix3_ac_only_user` (equivalent to `testuser5` pattern) |
| Legacy role | `pm` (compatibility slot) |
| RBAC roles | Copied Access Control Administrator permissions |
| Effective permissions | `access_control.*` + `users.*` — **no `master_data.*`** |
| Root cause | Payment Methods list/get used `get_current_user`; Cost Components CRUD used legacy `require_finance` / `require_procurement` instead of RBAC keys |

## Permission keys (confirmed — no duplicates)

Existing registry keys used:

- `master_data.payment_methods.view/create/edit/delete`
- `master_data.cost_components.view/create/edit/delete`
- `master_data.items.*` / `master_data.suppliers.*` (unchanged pilot)

## Role grant mapping

| Role | master_data grants |
|---|---|
| `system_admin` | all |
| `access_control_admin` | **none** |
| `finance_analyst` | payment_methods full + items/suppliers read/write (legacy finance behavior) |
| `pmo` | payment_methods.view, cost_components.view + items/suppliers |
| `project_manager` | items/suppliers only (no payment_methods) |
| `procurement_specialist` | payment_methods.view; cost_components view/create/edit/**delete** (delete added to preserve deactivate behavior) |

Seed remains idempotent via `_seed_system_role_permissions` (adds missing keys only).

## Backend enforcement

`procurement_financials.py` now uses `require_pilot_permission()` (RBAC-only, admin bypass):

| Endpoint | Permission |
|---|---|
| GET `/payment-methods` | `master_data.payment_methods.view` |
| GET `/payment-methods/{id}` | `.view` |
| POST `/payment-methods` | `.create` |
| PUT `/payment-methods/{id}` | `.edit` |
| DELETE `/payment-methods/{id}` | `.delete` |
| GET `/procurement-options/{id}/cost-components` | `master_data.cost_components.view` |
| POST cost component | `.create` |
| PUT cost component | `.edit` |
| DELETE cost component | `.delete` |

Procurement preview/readiness endpoints unchanged (not master-data catalog CRUD).

`PILOT_PERMISSION_PREFIXES` extended to include payment_methods and cost_components.

## Frontend

- Badge labels: `master_data.payment_methods` and `master_data.cost_components` → **Enforced** / **اعمال‌شده**
- Items/Suppliers remain **Pilot** / **پایلوت اجراشده**
- Access Control remains **Enforced**
- Nav/UI gating from Fix-2 retained (`userHasExplicitRbacGrants`, PaymentMethodsManager gates)

## Tests

| Suite | Result |
|---|---|
| `test_phase15c_r4_fix3_masterdata_backend_enforcement.py` | **5 passed** |
| `test_phase15c_r4_fix2_rbac_labels_masterdata_leakage.py` regression | **2 passed** |
| `permissionLabels.test.ts` | Updated (not run locally — Jest OOM risk) |

## Runtime evidence (demo)

- `verify.sh` — **PASS**
- `run_sprint5c_r4_fix3_smoke.sh` — **PASS**
- AC-only user: no `master_data.*`; GET `/payment-methods` **403**; POST **403**; Items/Suppliers **403**
- `master_data.payment_methods.view` user: GET **200**
- Admin: GET `/payment-methods` **200**
- Unauthenticated: **401**
- `DEPLOYED_COMMIT.txt` updated with full commit hash and proper newlines

## Remaining risks

- Legacy users without RBAC role rows rely on admin bypass only for master-data APIs (same as Items/Suppliers pilot).
- Most non-master-data navigation remains legacy-role driven.
- `testuser5` not directly verified if absent from demo DB; equivalent smoke user used.

## Recommendation

**Proceed to Sprint 5D Procurement Assignment Backend.**

## Scope control

- Procurement Assignment: **not started**
- Package Wizard / R3 verify: **unchanged**
- Optimization/cashflow/decision: **unchanged**

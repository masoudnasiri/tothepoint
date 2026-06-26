# Sprint 5B-R1 — Demo DB Migration and Runtime Closure

Date: 2026-06-26  
Status: **PASS**  
Sprint type: **Demo runtime closure + installer migration path fix** (no RBAC product changes)

## Baseline

| Item | Value |
|---|---|
| Starting branch | `restart/sprint5b-backend-rbac-foundation` |
| Starting commit | `445606edcfd9ec9d27be3e31ebdd2905966552a1` |
| New branch | `restart/sprint5b-r1-demo-runtime-closure` |
| Demo server | `193.162.129.58` |
| Demo install path | `/opt/rivar-demo` |
| Compose project | `rivar-demo` |
| Forbidden path used | **No** (`/root/pdss_demo` not used) |

## Root cause

| Finding | Detail |
|---|---|
| Missing column | `procurement_cost_components.payment_metadata` |
| Canonical migration in repo | **Yes** — `backend/add_procurement_cost_component_payment_metadata.sql` (Sprint 3A-R3) |
| Installer/migration flow issue | **Yes** — `install.sh` / `verify.sh` relied on `init.sql` (fresh volume only) and SQLAlchemy `create_all` (no `ALTER` on existing Postgres volumes) |
| Demo DB drift confirmed | **Yes** — persisted `rivar_demo_postgres_data` volume predated R3 column DDL |
| Sprint 5B RBAC defect | **No** — RBAC smoke passed before and after migration closure |

### Canonical migration (accepted R3 source)

File: `backend/add_procurement_cost_component_payment_metadata.sql`

```sql
ALTER TABLE procurement_cost_components
ADD COLUMN IF NOT EXISTS payment_metadata JSON;
```

Model alignment: `ProcurementCostComponent.payment_metadata` in `backend/app/models.py`.

## Server schema closure

| Step | Result |
|---|---|
| Schema before | `payment_metadata` column **absent** (empty `information_schema` query) |
| Migration applied | `backend/add_procurement_cost_component_payment_metadata.sql` via `docker compose -p rivar-demo exec postgres psql` |
| Schema after | `payment_metadata \| json` |
| Secrets exposed in docs/logs | **No** |

Post-fix fixture reseed (`create_sprint4a_demo_fixture.py --mode recreate`) succeeded. Deterministic readiness option id after reseed: **6** (ready), **7** (not ready).

## Installer fix (scoped)

Added `deployment/rivar-installer/apply_r3_schema_migrations.sh`:

- Runs accepted idempotent R3 DDL against demo Postgres before fixture seed
- Currently whitelists only `add_procurement_cost_component_payment_metadata.sql`

Wired into:

- `deployment/rivar-installer/install.sh` — after backend health, before optional demo seed
- `deployment/rivar-installer/verify.sh` — before fixture reseed

No duplicate migration file created.

## Verification results

### `verify.sh` on `/opt/rivar-demo`

**PASS** — fixture reseed OK, `verify_runtime_r3.py` status `PASS`.

R3 checks included:

- `auth_login`
- `r3_openapi_paths_present`
- `payment_methods_list`
- `readiness_ready_and_not_ready_detected`
- `cost_components_list`
- `component_payment_schedule_save_reopen` (Package Wizard Step 3 backend contract)
- `read_only_side_effects_unchanged`

### RBAC runtime smoke (demo)

| Check | Result |
|---|---|
| `/health` | 200 |
| `/openapi.json` | 200 |
| `/auth/login` | OK |
| `/auth/me` | 59 permissions, 1 role |
| `/access-control/permissions` (admin) | 200 |
| `/access-control/roles` (admin) | 200 |
| `/access-control/roles` (procurement user) | 403 |
| `/payment-methods` | 200 |
| `/procurement-options/6/readiness` | 200 |

### Local tests

```text
pytest tests/test_phase15b_rbac_foundation.py \
       tests/test_phase13a_payment_methods_and_cost_components.py \
       tests/test_phase13c_procurement_option_persistence_readiness.py -q
```

**37 passed**

Skipped: full backend suite (installer-only scoped change; R3 + RBAC focused tests cover affected paths). Frontend tests skipped (no frontend files changed).

## Files changed

| File | Change |
|---|---|
| `deployment/rivar-installer/apply_r3_schema_migrations.sh` | **Added** — idempotent R3 schema apply hook |
| `deployment/rivar-installer/install.sh` | Call `apply_r3_schema_migrations` after backend healthy |
| `deployment/rivar-installer/verify.sh` | Call `apply_r3_schema_migrations` before fixture seed |
| `docs/restart-audit/58_sprint5b_r1_demo_runtime_closure.md` | This document |
| `docs/restart-audit/08_recommended_continuation_plan.md` | Sprint pointer update |

## Scope control

| Area | Changed |
|---|---|
| RBAC product behavior | No |
| Package Wizard UI/logic | No |
| Payment Methods placement | No |
| Cost Components behavior | No |
| Optimization / cashflow / decision / rollback | No |
| Procurement assignment | No (not started) |

## Git provenance

| Item | Value |
|---|---|
| Branch | `restart/sprint5b-r1-demo-runtime-closure` |
| Parent commit | `445606edcfd9ec9d27be3e31ebdd2905966552a1` |
| Commit message | `chore: close sprint 5b demo runtime migration drift` |

## Remaining risks

1. **Other historical DDL** on long-lived demo volumes may still be missing if added after initial volume creation and not covered by `apply_r3_schema_migrations.sh` (currently only `payment_metadata`).
2. **RBAC foundation tables** (`roles`, `permissions`, etc.) rely on backend startup seed + `add_rbac_foundation_tables.sql` for fresh installs; existing volumes need backend restart / manual apply if 5B deployed before table migration — not observed as blocking on current demo after 5B deploy.
3. **Fixture option ids** change on recreate (currently option **6** for readiness smoke); hard-coded id `19` in ad-hoc scripts is stale after reseed.

## Recommendation

**Proceed to Sprint 5C Role Management Frontend** — demo runtime gap closed, `verify.sh` PASS, R3 and RBAC smokes green.

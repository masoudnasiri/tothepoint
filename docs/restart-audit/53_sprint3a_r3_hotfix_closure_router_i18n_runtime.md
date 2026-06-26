# Sprint 3A-R3 Hotfix Closure — Router, i18n, Runtime

Date: 2026-06-26  
Status: **PASS**

## Hotfix purpose

Close the gap between accepted Sprint 3A-R3 code on disk and live `/opt/rivar-demo` behavior after discovery that:

1. Postgres credentials in `.env` did not match the persisted DB volume password.
2. Frontend container and `fa.json` / `en.json` on the demo server were stale.
3. `procurement_financials.router` existed in code but was not registered in `backend/app/main.py`, so Payment Methods, cost components, and readiness HTTP endpoints were unavailable.
4. Schedule-oriented terminology refinement (`743a19b`) existed locally but had not been pushed/deployed before Sprint 4A workspace reset.

## Previous vs new accepted baseline

| Item | Value |
|---|---|
| Previous accepted baseline commit | `23be38619dc9dea072be4b5fe513dd55af998c0f` |
| Hotfix commits | `743a19b` (terminology), `6f9e944` (router registration) |
| Closure commit (verification scripts + provenance) | recorded at push time in git log |
| **Recommended new Sprint 4A baseline** | **`6f9e944` or later closure commit on this branch** |
| Branch | `recovery/sprint3a-r3-cost-level-payment-schedule` |

## Root causes and closure actions

| Root cause | Closure action | Result |
|---|---|---|
| Postgres password mismatch | `ALTER USER postgres` aligned to `.env` on server | Backend DB connectivity restored |
| Stale frontend / i18n | Deployed `fa.json`/`en.json`, rebuilt `rivar-demo-frontend` | Schedule labels live on server |
| Missing `procurement_financials` router | `6f9e944` registers router in `main.py` | `/payment-methods`, cost components, `/readiness` HTTP 200 |
| Lost terminology commit | Restored and pushed `743a19b` | `نوع زمان‌بندی پرداخت`, `تک‌مرحله‌ای`, etc. |
| `verify.sh` SPA 404 on `/login` | Added `Accept: text/html` for SPA route checks | Non-blocking CRA dev-server issue resolved in installer |
| `verify_runtime.py` branch mismatch | Added `backend/scripts/verify_runtime_r3.py`; `verify.sh` calls R3 script | Full installer verify PASS on R3 branch |

## Files changed (hotfix + closure)

### Hotfix commits already pushed

- `743a19b`: `frontend/src/i18n/en.json`, `frontend/src/i18n/fa.json`, `PackageWizardStep3.test.tsx`, docs `50_*`, `08_*`
- `6f9e944`: `backend/app/main.py`

### Closure commit (this document scope)

- `backend/scripts/verify_runtime_r3.py` — R3-only runtime verification
- `deployment/rivar-installer/verify.sh` — SPA Accept header + R3 verifier
- `docs/restart-audit/53_sprint3a_r3_hotfix_closure_router_i18n_runtime.md`
- `docs/restart-audit/08_recommended_continuation_plan.md` (baseline pointer update)

## Server path and security

- Official demo path: `/opt/rivar-demo`
- Compose project: `rivar-demo`
- **`/root/pdss_demo` not used** (confirmed absent on server during closure)
- No secrets, tokens, or DB passwords recorded in this document

## Runtime smoke results (`193.162.129.58`)

| Check | Result |
|---|---|
| `GET /health` | 200 |
| `GET /` | 200 |
| `GET /login` (Accept: text/html) | 200 |
| `GET /procurement` (Accept: text/html) | 200 |
| `POST /auth/login` | 200 (token issued; not logged) |
| `GET /payment-methods` | 200 |
| `GET /procurement-options/{id}/cost-components` | 200 |
| `GET /procurement-options/{id}/readiness` | 200, `is_ready_for_candidate_builder` present |
| `bash deployment/rivar-installer/verify.sh` | **PASS** (fixture reseed + `verify_runtime_r3.py`) |
| Persian schedule terminology on server `fa.json` | `نوع زمان‌بندی پرداخت`, `تک‌مرحله‌ای`, `چندمرحله‌ای` |

## API / verification script evidence

`verify_runtime_r3.py` checks (all PASS on server):

- `auth_login`
- `r3_openapi_paths_present`
- `payment_methods_list`
- `readiness_ready_and_not_ready_detected`
- `cost_components_list`
- `component_payment_schedule_save_reopen`
- `read_only_side_effects_unchanged`

`verify_runtime.py` (full 3C/4A path list) remains in repo for later branches but is **not** used by R3 `verify.sh`.

## Tests run (local, R3 branch)

```text
python -m pytest tests/test_phase13a_payment_methods_and_cost_components.py tests/test_phase13c_procurement_option_persistence_readiness.py -q
→ 22 passed

python -m pytest tests -q
→ 167 passed, 5 skipped

cd frontend && CI=true npm test -- --watch=false --testPathPattern=PackageWizardStep3|PackageWizard.saveBoundary
→ 17 passed

CI=false npm run build
→ PASS
```

Typecheck: no dedicated script in `frontend/package.json`.

## Scope confirmation (unchanged)

- Payment Methods remain in Master Data (not Finance page primary placement)
- Cost Components remain source of truth
- Package Wizard Step 3: Pricing and Costs / Delivery / Payment only
- Component-level payment schedule contract preserved (`payment_metadata`)
- Backend enums `cash` / `installments` unchanged
- No optimization / cashflow / decision / rollback logic changes in hotfix commits

## Remaining known issues

| Issue | Blocking? |
|---|---|
| Frontend Dockerfile uses CRA `npm start` (dev server) while installer README mentions nginx static SPA | **Non-blocking** for R3 hotfix; pre-existing deployment drift |
| `verify_runtime.py` still lists 3C/4A OpenAPI paths (not invoked by R3 `verify.sh`) | **Non-blocking** on R3 branch |
| Local working tree has unrelated untracked files (43+) | **Non-blocking** for hotfix closure; requires future scoped commits |
| Other finance/dashboard i18n keys still use legacy `نقدی` in non-wizard contexts | **Non-blocking**; outside Step 3 procurement scope |

## Recommendation

**Proceed to Sprint 4A Workspace Organization** using:

- Branch: `recovery/sprint3a-r3-cost-level-payment-schedule`
- Baseline commit: latest hotfix closure HEAD (includes `6f9e944` + closure commit)

Do **not** use `23be386` alone as the Sprint 4A baseline — it lacks router registration and terminology restoration.

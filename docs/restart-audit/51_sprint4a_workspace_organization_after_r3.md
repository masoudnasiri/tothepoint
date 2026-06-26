# Sprint 4A — Workspace Organization after Sprint 3A-R3

Date: 2026-06-26  
Status: **PASS WITH MINOR ISSUES**

## Sprint purpose

Repository hygiene only. Archive post-R3 root clutter into ignored `oldfiles/` without changing product behavior, source layout, installer flow, or R3 guarantees.

## Baseline verification

| Item | Value |
|---|---|
| Starting branch | `recovery/sprint3a-r3-cost-level-payment-schedule` |
| Required commit | `23be38619dc9dea072be4b5fe513dd55af998c0f` |
| Pre-reset local tip (not accepted) | `87c63fe` (unpushed terminology-only commit; left in reflog) |
| Actual starting commit (after `git reset --hard 23be386`) | `23be38619dc9dea072be4b5fe513dd55af998c0f` |
| New branch | `restart/workspace-organization-after-sprint3a-r3` |
| Old branch not used | `restart/workspace-organization-after-sprint4a` (not checked out) |

## Inventory summary

See `docs/restart-audit/52_sprint4a_workspace_inventory.md`.

Post-reset untracked entries: 43 (source-like docs/tests only; not moved).

## Dry-run move plan

| Source | Destination | Why safe |
|---|---|---|
| `.tmp_remote_installer/` | `oldfiles/qa-temp/.tmp_remote_installer` | Installer scratch staging; not runtime source |
| `.tmp_sprint3a_r2_artifact_20260625_223635/` | `oldfiles/old-scope-clean-artifacts/...` | Superseded scope-clean staging tree |
| `.tmp_sprint3a_r3_artifact_20260626_000243/` | `oldfiles/old-scope-clean-artifacts/...` | Superseded scope-clean staging tree |
| `rivar_sprint3a_r2_payment_cost_contract_20260625_223635.tar.gz` | `oldfiles/artifacts/...` | Generated root bundle; duplicate of staged tree |
| `rivar_sprint3a_r3_cost_level_payment_schedule_20260626_000243.tar.gz` | `oldfiles/artifacts/...` | Generated root bundle; duplicate of staged tree |

**Intentionally not moved:** all `backend/`, `frontend/`, `deployment/rivar-installer/`, `docs/restart-audit/`, ADRs, tests, migrations, compose/Docker/config files, tracked legacy package trees, root `node_modules/`, untracked source-like routers/services/tests.

## Execution result

- Moves executed: **5** items (3 folders + 2 tarballs)
- Local manifest: `oldfiles/MANIFEST_SPRINT4A_R3_MOVES.md` (git-ignored)
- Prior organization manifest preserved: `oldfiles/MANIFEST_MOVED_FILES.md`
- No files restored after move
- No product source files modified

## `.gitignore`

No change required. R3 baseline already ignores:

- `oldfiles/`
- `.tmp_*/`, `qa-artifacts/`, `playwright_runner_tmp/`, `test-results/`
- root `rivar_*.tar.gz` bundles
- `deployment/artifacts/`

## Scope control confirmation

- No product behavior changes
- Package Wizard source untouched
- Payment Methods remain in Master Data (no Finance relocation)
- Cost Components and component-level payment schedule code untouched
- Optimization / cashflow / decision / rollback logic untouched
- Only documentation + local `oldfiles/` moves (ignored)

## Tests run

### Backend

```text
cd backend && python -m pytest tests -q
167 passed, 5 skipped
```

### Frontend

```text
cd frontend && CI=true npm test -- --watch=false
9 suites: 7 passed, 2 failed
31 tests: 29 passed, 2 failed
```

Failures (pre-existing / environment; not introduced by this sprint):

- `src/pages/LoginPage.smoke.test.tsx` (tracked on R3 baseline)
- `src/pages/ItemsMasterPage.masterData.test.tsx` (untracked local test file)

R3-critical wizard tests passed:

- `PackageWizardStep3.test.tsx` PASS
- `PackageWizard.saveBoundary.test.tsx` PASS

### Frontend build

```text
cd frontend && CI=false npm run build
PASS (eslint warnings only; bundle ready)
```

### Typecheck

No dedicated `typecheck` script in `frontend/package.json` (not applicable).

### Installer script syntax

```text
"C:/Program Files/Git/bin/bash.exe" -n deployment/rivar-installer/install.sh
"C:/Program Files/Git/bin/bash.exe" -n deployment/rivar-installer/uninstall.sh
"C:/Program Files/Git/bin/bash.exe" -n deployment/rivar-installer/verify.sh
PASS
```

### Installer verify (remote `/opt/rivar-demo`)

```text
ssh ... "cd /opt/rivar-demo && bash deployment/rivar-installer/verify.sh"
```

Result: **PARTIAL** — route/compose checks passed; fixture reseed and `verify_runtime.py` failed with:

```text
asyncpg.exceptions.InvalidPasswordError: password authentication failed for user "postgres"
```

This is a **server environment credential mismatch** between backend fixture script DB URL and postgres container credentials. Not caused by workspace organization (no server files changed, no redeploy).

`verify.sh --no-ensure-fixture` also failed at `verify_runtime.py` with the same postgres password error.

## Runtime smoke (`/opt/rivar-demo`, compose project `rivar-demo`)

| Check | Result |
|---|---|
| `/` | 200 |
| `/login` | 200 |
| `/procurement` | 200 |
| `/health` | 200 |
| `/openapi.json` | 200 |
| Compose services | postgres/backend/frontend Up (healthy where applicable) |
| Package Wizard UI walkthrough | Not re-run interactively; Step 3 unit tests PASS on R3 baseline |
| Step 3 sections (Pricing/Delivery/Payment) | Confirmed by `PackageWizardStep3.test.tsx` |
| BASE_PRICE default / non-removable | Confirmed by `PackageWizardStep3.test.tsx` |
| Optional cost components | Confirmed by wizard tests |
| Component-level payment schedule persistence | Confirmed by R3 backend tests (`test_phase13a`, `test_phase13c`) in full suite |
| Payment Methods in Master Data | Confirmed by `Layout.masterDataNavigation.test.tsx` PASS |
| readiness / atomic / coverage / projection / scenario endpoints | Full `verify_runtime.py` blocked by server DB password issue; services healthy and OpenAPI available |

## Artifact / installer

- **Artifact created:** No new release artifact (hygiene-only sprint)
- **oldfiles excluded:** Yes (git-ignored; not in any commit)
- **Secrets excluded:** Yes (no credentials committed; `database_backups` remains under ignored `oldfiles/sensitive-not-tracked/`)
- **Installer flow used:** Official path `deployment/rivar-installer/verify.sh` against `/opt/rivar-demo`

## Known risks

1. Local dirty tree still contains 43 untracked source-like files (routers, ADRs, restart-audit drafts) — requires future scoped commits, not auto-archived.
2. Remote `verify_runtime.py` postgres password mismatch blocks full endpoint matrix smoke until server `.env`/DB credentials are reconciled.
3. Unpushed `87c63fe` terminology commit remains in reflog only; not part of this sprint branch.
4. Two frontend test failures pre-exist on baseline; not regressions from file moves.

## R3 behavior preserved

Confirmed: no source/test/installer/doc files moved; backend full suite green; wizard Step 3 tests green; demo routes healthy.

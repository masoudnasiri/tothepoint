# Sprint 4A — Workspace Organization from Sprint 3A-R3 Hotfix Baseline

Date: 2026-06-26  
Status: **PASS WITH MINOR ISSUES**

## Sprint purpose

Repository hygiene only: archive root-level deploy/verify scratch and QA log clutter into gitignored `oldfiles/`, without changing product behavior or R3 hotfix guarantees.

## Baseline verification

| Item | Value |
|---|---|
| Starting branch | `recovery/sprint3a-r3-cost-level-payment-schedule` |
| Required commit | `07b56f24c66eb4d637e8aa9de1461a5e21932b60` |
| Actual starting commit | `07b56f24c66eb4d637e8aa9de1461a5e21932b60` ✓ |
| New branch | `restart/workspace-organization-after-sprint3a-r3-hotfix` |
| Old workspace branch used | **No** (`restart/workspace-organization-after-sprint4a` not used) |
| Pre-hotfix baseline not used as start | **Yes** (`23be386` not used) |

## Inventory and dry-run

| Document | Path |
|---|---|
| Inventory + dry-run | `docs/restart-audit/55_sprint4a_workspace_inventory_and_dry_run.md` |

### Files/folders moved to `oldfiles/qa-temp/`

16 root scratch items (see `oldfiles/MANIFEST_SPRINT4A_R3_HOTFIX_MOVES.md`):

- `.tmp_check_db.sh`, `.tmp_r3_api_smoke.sh`, `.tmp_r3_hotfix_verify.log`
- `.tmp_server_deploy_output.log`, `.tmp_server_extract_and_deploy.sh`, `.tmp_server_r3_deploy.sh`, `.tmp_server_verify_after_deploy.log`
- `.tmp_sprint4a_*` logs and remote smoke/verify scripts (prior session)
- `.tmp_sprint4a_r3hotfix_pytest.log`, `.tmp_sprint4a_r3hotfix_frontend_test.log`, `.tmp_sprint4a_r3hotfix_frontend_build.log` (this sprint QA)

### Files intentionally not moved

- All tracked `backend/`, `frontend/`, `deployment/`, `docs/` source
- ~43 unrelated untracked files (later-sprint routers, ADRs, tests) — left for separate review
- Legacy package trees: `installation_packages/`, `release_packages/`, etc.
- Prior hotfix artifact archive under `oldfiles/` from first workspace sprint

### Unrelated untracked files

Not staged, not moved, not deleted. Documented in `55_*`.

## Workspace changes

| Change | Detail |
|---|---|
| `.gitignore` | **No change** — `oldfiles/` already ignored (line 164) |
| Documentation | `54_*` (this file), `55_*`, `08_recommended_continuation_plan.md` |
| Installer README | **No change** — CRA/nginx drift documented as known risk below |
| Product code | **None** |

## Scope control confirmation

| Guarantee | Preserved |
|---|---|
| `procurement_financials` router registered | Yes (no `main.py` change) |
| GET `/payment-methods` | Yes (runtime verify PASS) |
| GET `/procurement-options/{id}/readiness` | Yes (runtime verify PASS) |
| Package Wizard Step 3 scope | Yes (17 frontend tests PASS) |
| Cost Components / BASE_PRICE / OTHER description | Yes (R3 runtime verifier PASS) |
| Payment Methods in Master Data | Yes (no frontend nav change) |
| Component-level payment schedule | Yes (`component_payment_schedule_save_reopen` PASS) |
| Schedule-oriented Persian terminology | Yes (hotfix `743a19b` unchanged; server `fa.json` verified in hotfix closure) |
| Optimization / cashflow / decision / rollback | Untouched |
| Sprint 5 not started | Confirmed |
| `/root/pdss_demo` not used | Confirmed |

## Tests run

| Check | Result |
|---|---|
| `pytest tests -q` | **167 passed**, 5 skipped |
| R3 focused (`test_phase13a_*`, `test_phase13c_*`) | **22 passed** |
| Frontend `PackageWizardStep3` + `saveBoundary` | **17 passed** |
| Frontend `npm run build` | **PASS** (without `CI=true`; see minor issue) |
| Typecheck script | N/A (no official typecheck script in `package.json`) |
| Installer `bash -n` (local Windows/WSL) | **Inconclusive** — local `bash -n` hung; scripts validated by successful server `verify.sh` execution |
| Installer `verify.sh` on `/opt/rivar-demo` | **PASS** |
| R3 `verify_runtime_r3.py` | **PASS** (via `verify.sh`) |

### Minor issue: frontend build under `CI=true`

`npm run build` with `CI=true` fails on pre-existing eslint unused-import warnings across unrelated pages. Build succeeds without `CI=true`. This is a pre-existing hygiene debt, not introduced by this sprint.

## Runtime smoke (`/opt/rivar-demo`, compose `rivar-demo`)

Executed via `bash deployment/rivar-installer/verify.sh` on `193.162.129.58` after organization (no redeploy required — hygiene-only local changes).

| Check | Result |
|---|---|
| `GET /health` | 200 (via verify.sh) |
| `GET /` | 200 |
| `GET /login` (Accept: text/html) | 200 |
| `GET /procurement` (Accept: text/html) | 200 |
| `GET /openapi.json` | 200 |
| `POST /auth/login` | 200 (token issued; not logged) |
| `GET /payment-methods` | 200 |
| `GET /procurement-options/{id}/readiness` | 200 |
| `is_ready_for_candidate_builder` present | Yes (`option_id_ready`: 19) |
| Readiness read-only side effects | PASS (`read_only_side_effects_unchanged`) |
| Component payment schedule save/reopen | PASS |
| Persian schedule labels on server | Present per hotfix closure `53_*` |
| Full installer verify | **PASS** |

Package Wizard UI checks are covered by frontend unit tests and R3 runtime script; no browser automation in this hygiene sprint.

## Artifact / installer

| Item | Value |
|---|---|
| Artifact created | **No** |
| `oldfiles/` excluded from artifacts | Yes (gitignored + not packaged) |
| Secrets excluded | Yes |
| Installer flow | Existing R3 `verify.sh` on `/opt/rivar-demo` |

## Git provenance

Recorded at commit time:

- Local branch: `restart/workspace-organization-after-sprint3a-r3-hotfix`
- Staged files: `docs/restart-audit/54_*`, `55_*`, `08_*` only
- Commit message: `chore: organize workspace after sprint 3a r3 hotfix baseline`
- Remote: `origin restart/workspace-organization-after-sprint3a-r3-hotfix`

## Known risks retained for later

1. **Unrelated untracked files** (~43) in working tree from prior sprint work — do not `git add .`
2. **Installer README drift** — documents nginx static SPA and `verify_runtime.py`; live stack uses CRA dev server in `frontend/Dockerfile` and R3 uses `verify_runtime_r3.py`
3. **Legacy non-wizard i18n** — some keys outside Step 3 may still use old payment wording
4. **Frontend CI build** — eslint warnings fail build when `CI=true`

## Sprint verdict

**PASS WITH MINOR ISSUES**

Hygiene goal met: root `.tmp_*` clutter archived to gitignored `oldfiles/`, R3 behavior preserved, tests and `/opt/rivar-demo` verification PASS. Minor issues are pre-existing documentation/CI debt, not regressions from this sprint.

## Recommendation

**Proceed to Sprint 5 Optimization UX Decision Room** — after product owner accepts this branch as the post-R3 hygiene baseline.

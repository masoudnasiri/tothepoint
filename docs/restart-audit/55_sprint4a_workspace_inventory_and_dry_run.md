# Sprint 4A — Workspace Inventory and Dry-Run Plan (from R3 Hotfix Baseline)

Date: 2026-06-26  
Sprint: **Sprint 4A — Workspace Organization from Sprint 3A-R3 Hotfix Baseline**  
Status: **PASS** (inventory + dry-run + safe moves executed)

## Baseline

| Item | Value |
|---|---|
| Starting branch | `recovery/sprint3a-r3-cost-level-payment-schedule` |
| Required commit | `07b56f24c66eb4d637e8aa9de1461a5e21932b60` |
| New branch | `restart/workspace-organization-after-sprint3a-r3-hotfix` |
| Old workspace branch (not used) | `restart/workspace-organization-after-sprint4a` |

## Inventory summary (grouped)

### Official source / runtime files (keep in place)

- `backend/` — accepted R3 hotfix backend including `procurement_financials` router registration
- `frontend/` — accepted R3 hotfix frontend including schedule-oriented Step 3 i18n
- `docker-compose.yml`, `.dockerignore`, `.env.example`, `package.json`, `VERSION`
- `scripts/`, `uploads/` (runtime data path)

### Official tests (keep in place)

- `backend/tests/` — 167 passed at organization time (5 skipped)
- `frontend/src/components/PackageWizard/PackageWizardStep3.test.tsx`
- `frontend/src/components/PackageWizard/PackageWizard.saveBoundary.test.tsx`

### Official installer / deployment files (keep in place)

- `deployment/rivar-installer/` (`install.sh`, `uninstall.sh`, `verify.sh`, compose template)
- `backend/scripts/verify_runtime_r3.py` — R3-compatible runtime verifier

### Official docs / ADR / restart-audit (keep in place)

- `docs/restart-audit/` — sprint evidence chain including `53_sprint3a_r3_hotfix_closure_*`
- `docs/README.md`, design references under `docs/design/`
- Untracked `docs/architecture/ADR-*` and extended restart-audit notes — **not moved** (may belong to later sprints; manual review required before commit)

### Likely temporary files (proposed → `oldfiles/qa-temp/`)

Root-level `.tmp_*` deploy/verify scratch from hotfix closure and prior Sprint 4A QA sessions:

| Source | Why safe |
|---|---|
| `.tmp_check_db.sh` | Ad-hoc server DB credential probe; not runtime source |
| `.tmp_r3_api_smoke.sh` | One-off API smoke script |
| `.tmp_r3_hotfix_verify.log` | Local verify log output |
| `.tmp_server_deploy_output.log` | Deploy session log |
| `.tmp_server_extract_and_deploy.sh` | One-off deploy helper |
| `.tmp_server_r3_deploy.sh` | One-off R3 deploy helper |
| `.tmp_server_verify_after_deploy.log` | Post-deploy verify log |
| `.tmp_sprint4a_frontend_build.log` | Local build log (this sprint) |
| `.tmp_sprint4a_frontend_test.log` | Local frontend test log (this sprint) |
| `.tmp_sprint4a_pytest.log` | Prior session pytest log |
| `.tmp_sprint4a_remote_smoke.sh` | Remote smoke helper |
| `.tmp_sprint4a_remote_verify.log` | Remote verify log |
| `.tmp_sprint4a_remote_verify_nofixture.log` | Remote verify log variant |
| `.tmp_sprint4a_r3hotfix_pytest.log` | This sprint pytest log |
| `.tmp_sprint4a_r3hotfix_frontend_test.log` | This sprint frontend test log |
| `.tmp_sprint4a_r3hotfix_frontend_build.log` | This sprint frontend build log |

### Likely old artifacts (already archived — do not re-move)

Prior Sprint 4A workspace organization (from pre-hotfix `23be386`) already moved to `oldfiles/`:

- `oldfiles/qa-temp/.tmp_remote_installer`
- `oldfiles/old-scope-clean-artifacts/.tmp_sprint3a_r2_*`, `.tmp_sprint3a_r3_*`
- `oldfiles/artifacts/rivar_sprint3a_r2_*.tar.gz`, `rivar_sprint3a_r3_*.tar.gz`

Manifest: `oldfiles/MANIFEST_SPRINT4A_R3_MOVES.md` (prior) + `oldfiles/MANIFEST_SPRINT4A_R3_HOTFIX_MOVES.md` (this sprint).

### Unrelated untracked local files (intentionally not moved)

Approximately 40+ untracked paths including:

- Later-sprint routers/services: `atomic_optimization_candidates`, `candidate_coverage_validation`, `financial_projections`, `optimization_scenario_preview`
- Later-sprint tests: `test_phase13d_*`, `test_phase13e_*`, `test_phase14a_*`, `test_budget_precision.py`
- Architecture ADRs `ADR-001` through `ADR-009`
- Extended restart-audit docs `34a`–`47`
- Frontend test stubs: `Layout.masterDataNavigation.test.tsx`, `FinancePage.uiPresence.test.tsx`, etc.

**Action:** Left in working tree; **not staged** (`git add .` not used). These may be contamination from prior branches and require a separate hygiene decision.

### Suspicious files requiring caution (not moved)

| Path | Reason |
|---|---|
| `installation_packages/`, `release_packages/`, `update_package/`, `pdss-update-v1.0.2-COMPLETE/` | Large tracked legacy trees; moving would alter release history |
| `node_modules/` | Build cache; gitignored |
| `backend/pytest.ini` (untracked) | May be local config; uncertain baseline ownership |
| Any file under `backend/app/` or `frontend/src/` not in R3 commit | Product source — forbidden move target |

## Dry-run move plan

**Policy:** Move only root `.tmp_*` scratch files and local QA logs. No source, tests, migrations, installer, or docs moves.

**Destination:** `oldfiles/qa-temp/` (gitignored via `oldfiles/` in `.gitignore`)

**Rollback:** `Move-Item` back from `oldfiles/qa-temp/` to project root if any test fails.

## Execution result

- **16 items** moved to `oldfiles/qa-temp/` per plan above
- Root directory after move: no `.tmp_*` files remain at project root
- `oldfiles/` remains gitignored (`.gitignore` line `oldfiles/` — unchanged)
- No product source files moved
- Tests after moves: backend 167 passed; R3-focused 22 passed; frontend Step 3 + save boundary 17 passed; frontend build PASS (without `CI=true` strict eslint gate)

## Files intentionally not moved

- All `backend/`, `frontend/`, `deployment/`, `docs/` tracked content
- Untracked later-sprint source and ADR files (manual review queue)
- `installation_packages/` and related legacy package trees
- `node_modules/`, `uploads/`

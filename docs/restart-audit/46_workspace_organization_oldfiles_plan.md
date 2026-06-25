# Sprint 4A-Workspace Organization Oldfiles Plan

Date: 2026-06-25

Status: PASS (plan + safe-move execution)

## Why this organization is needed

The workspace has accumulated large temporary artifacts, runtime QA outputs, and superseded scope-clean bundles in the project root. This creates release risk (accidental packaging of debris), slows local operations, and obscures accepted baseline content.

## Baseline check result

- current branch: `restart/baseline-before-github-push`
- current HEAD: `c10ff4df3a65657b906eb2f18a244b356cd0b3c1`
- expected accepted baseline for Sprint 4A clean flow: `restart/accepted-through-sprint4a-clean-fix` @ `c1ecfd98e5ebf6af0a49257fd800e188fe45fa68`

This mismatch is explicitly recorded as a risk and is preserved in the final report.

## Inventory snapshot

- `git status --short` entries: 286
- `git ls-files --others --exclude-standard` entries: 318
- `git diff --name-only` entries: 23
- largest root items include:
  - `frontend/` (~439 MB)
  - `installation_packages/` (~113 MB)
  - multiple `rivar_*.tar.gz` bundles (~100 MB each)
  - `playwright_runner_tmp/`, `qa-artifacts/`, `.tmp_*` scope folders

## Classification summary

### Must stay in project root (do not move)

- core source and accepted structure:
  - `backend/`, `frontend/`, `docs/`, `scripts/`
  - `docker-compose.yml`, `README*`, `VERSION`, `.env.example`, `.gitignore`
- accepted/possibly-required code under active source paths:
  - untracked backend routers/services/tests under `backend/app` and `backend/tests`
  - untracked frontend source/tests under `frontend/src`
  - architecture and restart-audit docs under `docs/architecture` and `docs/restart-audit`

### Proposed safe move targets (this sprint)

| Source | Destination | Reason | Risk | Tracked/Untracked | Included in older artifacts | Safe to move |
|---|---|---|---|---|---|---|
| `.tmp_frontend_fix/` and root `.tmp_*` sql/json/txt files | `oldfiles/qa-temp/` | temporary debug/runtime scraps | Low | Untracked | Yes (debug/scope outputs) | Yes |
| `.tmp_runtime_closure_3a0_*`, `.tmp_sprint2z_*`, `.tmp_sprint3*_*` folders | `oldfiles/old-scope-clean-artifacts/` | superseded scope-clean staging trees | Low | Untracked | Yes | Yes |
| `rivar_*.tar.gz` root artifact bundles | `oldfiles/artifacts/` | old generated bundles cluttering root | Low | Untracked | N/A (these are artifacts) | Yes |
| `qa-artifacts/`, `playwright_runner_tmp/`, `test-results/` | `oldfiles/qa-temp/` | runtime probe outputs and temporary Playwright data | Low | Untracked | Yes | Yes |
| `qa_runtime_2z.spec.ts`, `qa_runtime_2z_playwright.mjs` | `oldfiles/qa-temp/` | ad-hoc runtime scripts, not accepted baseline tests | Medium | Untracked | Yes | Yes |
| `.repo_hygiene_backups/` | `oldfiles/old-backups/` | local backup metadata no longer needed in root | Low | Untracked | No | Yes |
| `database_backups/` | `oldfiles/sensitive-not-tracked/` | local backup dumps; remove root clutter | Medium | Ignored/local | No | Yes (without exposing contents) |

### Needs manual review (do not move in this pass)

| Path Group | Why manual review is required | Risk |
|---|---|---|
| untracked source-like files in `backend/app/**`, `backend/tests/**`, `frontend/src/**`, `docs/architecture/**`, `docs/restart-audit/**` | may contain accepted Sprint 3A-4A functionality not yet committed in this branch | High |
| tracked legacy package trees with many modifications: `installation_packages/**`, `release_packages/**`, `update_package/**`, `pdss-update-v1.0.2-COMPLETE/**` | moving tracked content would create large deletions/renames and can break historical release workflows | High |
| active modified files in core source (`backend/app/**`, `frontend/src/**`, `docs/restart-audit/08_*`) | belong to active working set; must not be auto-archived | High |

## Future output-location policy (to enforce after moves)

- installer artifacts: `deployment/artifacts/`
- runtime QA outputs: `qa-artifacts/` (or archive/sweep to `oldfiles/qa-temp/` when closed)
- temporary scripts: `.tmp_local/` or `qa-artifacts/tmp/`
- archived local backups: `oldfiles/old-backups/` or `oldfiles/sensitive-not-tracked/`
- server backups remain on server only: `/root/rivar_demo_backups/`
- no new generated bundles directly under project root

## Dry-run decision

Proceed to move only the low-risk/medium-risk safe extras above. Do not move any source-like or tracked baseline-critical paths until manually reviewed.

## Execution result (safe moves only)

Move execution completed after dry-run planning.

- moved item count: 43
- move manifest: `oldfiles/MANIFEST_MOVED_FILES.md`
- root clutter reduced:
  - untracked count before: 318
  - untracked count after: 60
- no source-like manual-review items were moved

High-level moved groups:

- moved to `oldfiles/qa-temp/`:
  - `.tmp_frontend_fix/`, root temporary `.tmp_*` files
  - `qa-artifacts/`, `playwright_runner_tmp/`, `test-results/`
  - `qa_runtime_2z.spec.ts`, `qa_runtime_2z_playwright.mjs`
  - root `.pytest_cache/`, root `__pycache__/`
- moved to `oldfiles/old-scope-clean-artifacts/`:
  - `.tmp_runtime_closure_3a0_*`
  - `.tmp_sprint2z_*`
  - `.tmp_sprint3*_*`
- moved to `oldfiles/artifacts/`:
  - all root `rivar_*.tar.gz` generated artifact bundles
- moved to `oldfiles/old-backups/`:
  - `.repo_hygiene_backups/`
- moved to `oldfiles/sensitive-not-tracked/`:
  - `database_backups/` (moved without exposing contents)

## Files explicitly not moved

- required/active source trees:
  - `backend/`, `frontend/`, `docs/`, `scripts/`
- untracked source-like paths requiring review:
  - `backend/app/**`, `backend/tests/**`, `frontend/src/**`, `docs/architecture/**`, `docs/restart-audit/**`
- tracked legacy package trees with large modifications:
  - `installation_packages/**`, `release_packages/**`, `update_package/**`, `pdss-update-v1.0.2-COMPLETE/**`
- retained runtime directory:
  - `uploads/` (kept in place)

## .gitignore policy updates applied

Added ignore rules for:

- `oldfiles/`
- `.repo_hygiene_backups/`
- `.tmp_*/`, `.tmp_local/`
- `qa-artifacts/`, `playwright_runner_tmp/`, `test-results/`
- root artifact outputs:
  - `rivar_*.tar.gz`
  - `rivar_clean_installer_*.tar.gz`
  - `MANIFEST_INCLUDED_FILES.txt`
  - `MANIFEST_EXCLUDED_FILES.txt`
  - `*.sha256`
- future artifact output path:
  - `deployment/artifacts/`

## Post-move validation

Backend targeted matrix:

- `test_phase14a_optimization_scenario_preview.py` pass
- `test_phase13f_financial_projection_engine.py` pass
- `test_phase13e_candidate_coverage_validation.py` pass
- `test_phase13d_atomic_optimization_candidate_builder.py` pass
- `test_phase13c_procurement_option_persistence_readiness.py` pass
- `test_project_item_procurement_eligibility.py` pass

Backend full suite:

- `163 passed, 5 skipped`

Frontend:

- `npm test -- --watch=false` -> `9` suites pass, `28` tests pass
- `npm run build` -> pass (pre-existing lint warnings only)

Installer script syntax checks:

- `bash -n` pass for:
  - `/opt/rivar-demo/deployment/rivar-installer/install.sh`
  - `/opt/rivar-demo/deployment/rivar-installer/uninstall.sh`
  - `/opt/rivar-demo/deployment/rivar-installer/verify.sh`

No files had to be restored after move.

## Demo verification (no redeploy required)

Demo install remained active at `/opt/rivar-demo`.

- `docker compose ps` healthy for `rivar-demo-postgres`, `rivar-demo-backend`, `rivar-demo-frontend`
- frontend route checks:
  - `/` -> 200
  - `/login` -> 200
  - `/procurement` -> 200
- backend checks:
  - `/health` -> 200
  - `/openapi.json` -> 200
- installer runtime verification (`verify.sh`) PASS, including:
  - financial projection completeness checks
  - scenario preview checks
  - read-only side-effect checks

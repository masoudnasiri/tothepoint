# Sprint 4A — Workspace Inventory (after Sprint 3A-R3 baseline)

Date: 2026-06-26

Baseline branch: `recovery/sprint3a-r3-cost-level-payment-schedule`  
Baseline commit: `23be38619dc9dea072be4b5fe513dd55af998c0f`  
Sprint branch: `restart/workspace-organization-after-sprint3a-r3`

## Inventory counts (post-reset, pre-move)

| Metric | Count |
|---|---|
| `git status --short` untracked entries | 43 |
| Tracked modifications on baseline | 0 (clean after hard reset to R3) |

## 1. Official source / runtime files (must stay)

| Path | Notes |
|---|---|
| `backend/` | Accepted R3 backend source, routers, services, migrations |
| `frontend/` | Accepted R3 frontend source and assets |
| `deployment/` | Official installer under `deployment/rivar-installer/` |
| `docker-compose.yml` | Local compose entry |
| `scripts/` | Operational scripts |
| `uploads/` | Runtime upload directory (retained in place) |
| `package.json`, `package-lock.json` | Root dependency pin (`date-fns-jalali`) |
| `README.md`, `VERSION`, `.env.example` | Project metadata |
| `installation_packages/`, `release_packages/`, `update_package/`, `pdss-update-v1.0.2-COMPLETE/` | Legacy release trees (tracked; not moved) |

## 2. Official tests (must stay)

| Path | Notes |
|---|---|
| `backend/tests/` | Backend pytest suite including R3 payment schedule tests |
| `frontend/src/**/*.test.tsx` | Frontend unit/smoke tests |

## 3. Official installer / deployment files (must stay)

| Path | Notes |
|---|---|
| `deployment/rivar-installer/install.sh` | Official install |
| `deployment/rivar-installer/uninstall.sh` | Official uninstall |
| `deployment/rivar-installer/verify.sh` | Official runtime verification |
| `deployment/rivar-installer/docker-compose.rivar-demo.yml` | Demo compose |

## 4. Official docs / ADR / restart-audit (must stay)

| Path | Notes |
|---|---|
| `docs/restart-audit/` | Sprint provenance and audit trail |
| `docs/architecture/ADR-*.md` | Architecture decision records (untracked but official) |
| `docs/README.md`, design references | Product documentation |

## 5. Likely temporary files (safe to archive to `oldfiles/`)

| Path | Classification | Proposed destination |
|---|---|---|
| `.tmp_remote_installer/` | Installer scratch staging | `oldfiles/qa-temp/` |
| `.tmp_sprint3a_r2_artifact_20260625_223635/` | Superseded scope-clean staging | `oldfiles/old-scope-clean-artifacts/` |
| `.tmp_sprint3a_r3_artifact_20260626_000243/` | Superseded scope-clean staging | `oldfiles/old-scope-clean-artifacts/` |
| `rivar_sprint3a_r2_payment_cost_contract_20260625_223635.tar.gz` | Generated root bundle | `oldfiles/artifacts/` |
| `rivar_sprint3a_r3_cost_level_payment_schedule_20260626_000243.tar.gz` | Generated root bundle | `oldfiles/artifacts/` |

## 6. Likely old artifacts (already archived in prior pass)

| Path | Notes |
|---|---|
| `oldfiles/qa-temp/` | Prior QA/runtime debris from 2026-06-25 organization |
| `oldfiles/old-scope-clean-artifacts/` | Prior scope-clean staging trees |
| `oldfiles/artifacts/` | Prior `rivar_*.tar.gz` bundles |
| `oldfiles/old-backups/` | Local hygiene backups |
| `oldfiles/sensitive-not-tracked/` | Local DB backup folder (contents not exposed) |
| `oldfiles/recovery/` | Sprint recovery evidence snapshots |

## 7. Suspicious / caution — intentionally not moved

| Path | Why not moved |
|---|---|
| Untracked `backend/app/routers/*.py`, `backend/app/services/*.py`, `backend/tests/test_phase13*.py`, `backend/tests/test_phase14*.py` | Source-like; may belong to future sprint commits |
| Untracked `docs/architecture/ADR-*.md`, `docs/restart-audit/34*.md`–`47*.md` | Official documentation awaiting commit; not clutter |
| Untracked `frontend/src/components/finance/`, `*.masterData.test.tsx` | Source-like tests/components |
| Root `node_modules/` | Ignored dependency tree; not archived |
| Tracked legacy package trees with historical modifications | Moving would create large tracked deletions |

## Baseline discrepancy note

Before sprint start, local branch tip was `87c63fe` (unpushed terminology-only commit, malformed message). Sprint instructions require exact R3 commit `23be386`. Local was reset with `git reset --hard 23be386` before branch creation. The `87c63fe` commit remains in reflog only and is not part of this sprint baseline.

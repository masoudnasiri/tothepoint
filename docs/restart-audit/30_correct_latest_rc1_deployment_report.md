# Corrective Latest RC1 Deployment Report

Date (UTC): 2026-08-08  
Host: `193.162.129.58`  
Target path: `/root/pdss`

## 1) Root Cause

- Previous reset/reinstall report referenced deployment flow from branch `restart/sprint5g-procurement-optimization-handoff-ux`, which is not the canonical RC1 release source.
- Corrective action required: redeploy from canonical RC1 branch `restart/baseline-before-github-push`.

## 2) Phase A - Source of Truth Verification

Executed locally:

- `git fetch --all --prune`
- `git branch -a`
- `git log --oneline --decorate -n 20`
- `git status --short`
- `git checkout restart/baseline-before-github-push`
- `git pull --ff-only corbit-rivar restart/baseline-before-github-push`

Verified canonical branch and commit ancestry:

- Checked out branch: `restart/baseline-before-github-push`
- Branch HEAD at deploy time: `c10ff4df3a65657b906eb2f18a244b356cd0b3c1`
- Required commits present in history:
  - `ed6e5d2` (Phase 8 readiness)
  - `ea30aa2` (Phase 9 sign-off)
  - `e811238` (Phase 10 controlled rollout/sign-off)
- `e811238` confirmed reachable from branch HEAD (`merge-base --is-ancestor` success).

## 3) Phase B - Wrong Deployment Inspection Before Correction

Server inspection at `/root/pdss` showed:

- `git status/branch/rev-parse/log` all failed with `not a git repository`.
- Runtime was healthy but source traceability was invalid at path level.
- `docker compose ps` showed all services up.
- Health output before correction:
  - `{"status":"healthy","version":"1.0.0"}`

Interpretation:

- Deployment source in `/root/pdss` was not a canonical git checkout and could not be verified against RC1 branch lineage.

## 4) Phase C - Backup Before Corrective Deploy

Created backup directory:

- `/root/rivar_corrective_deploy_backups`

Database backup:

- DB service detected: `postgres`
- Backup file created:
  - `/root/rivar_corrective_deploy_backups/pre_corrective_deploy_20260808_093533.sql`
- Backup size at capture: `112K`

## 5) Phase D - Corrective Deploy Source Replacement

Safety constraints followed:

- No `docker compose down -v`
- No deletion of fresh DB volumes

Performed actions:

1. Stopped stack with `docker compose down --remove-orphans`.
2. Moved previous deployment tree:
   - `/root/pdss` -> `/root/pdss_wrong_deploy_20260808_093730`
3. Rebuilt `/root/pdss` from canonical source archive created from:
   - branch `restart/baseline-before-github-push`
   - commit `c10ff4df3a65657b906eb2f18a244b356cd0b3c1`
4. Restored `.env` from moved deployment path.

## 6) Phase D/G - RC1/Phase10 Artifact Verification

Verified present in deployed source:

- `docs/restart-audit/27_phase10_controlled_release_rollout_signoff.md`
- `docs/release/release_notes_rc1.md`
- `docs/release/production_signoff_checklist_phase10.md`
- `docs/release/uat_defect_log_phase10.md`
- `docs/release/ui_witness_session_phase10.md`
- `backend/tests/test_phase8_release_candidate_smoke.py`
- `release_packages/corbit-rivar-rc1/manifest.json`
- `release_packages/corbit-rivar-rc1/README_RELEASE.md`
- `release_packages/corbit-rivar-rc1/RELEASE_NOTES.md`
- `release_packages/corbit-rivar-rc1/KNOWN_LIMITATIONS.md`
- `release_packages/corbit-rivar-rc1/POST_DEPLOY_SMOKE_CHECKLIST.md`

## 7) Phase E/F - Rebuild and Validation Results

Rebuild:

- `docker compose down --remove-orphans`
- `docker compose up --build -d`

Runtime status:

- `docker compose ps`: backend/postgres healthy, frontend up.

Health output after correction:

- `{"status":"healthy","version":"1.0.0-rc1","product":"Rivar","producer":"Corbit"}`

Backend logs at startup:

- `Starting up Rivar API...`
- `Database initialized successfully`
- `Database already has data - SKIPPING seeding (data preserved!)`

## 8) Test and Build Results

- Backend full test suite:
  - `docker compose run --rm backend python -m pytest tests -q`
  - Result: `92 passed, 5 skipped`
- Phase 8 smoke:
  - `docker compose run --rm backend python -m pytest tests/test_phase8_release_candidate_smoke.py -q`
  - Result: `3 passed`
- Frontend build:
  - `docker compose run --rm frontend npm run build`
  - Result: success (compiled with warnings)

## 9) Phase H - Demo Dataset and Login Validation

Demo dataset:

- Create command passed (`--mode create`), demo objects created.
- Cleanup command passed (`--mode cleanup`), demo objects removed.
- Post-cleanup counts:
  - `DEMO_RC8_` projects = `0`
  - `DEMO_RC8_` decisions = `0`

Login verification (all returned HTTP `200`):

- `admin/admin123`
- `finance1/finance123`
- `proc1/proc123`
- `pmo1/pmo123`
- `pm1/pm123`

## 10) Phase I - Runtime Identity Status

- Identity mismatch is resolved after corrective deployment.
- Current health includes RC1 identity fields:
  - product: `Rivar`
  - producer: `Corbit`
  - version: `1.0.0-rc1`

No additional Phase 11A branding code changes were needed in this corrective deployment.

## 11) Phase J - Login Stability Probe

Probe output:

- `/root/rivar_reset_evidence/corrective_deploy_login_stability_probe.log`

Probe profile:

- 5 iterations, 2-minute interval.
- Each iteration checked:
  - `/health`
  - `/auth/login` (admin)
  - `/auth/me` using received token
  - backend container memory/cpu snapshot

Result:

- All 5 iterations:
  - `health_code=200`
  - `login_code=200`
  - `auth_me_code=200`
  - `FAILURE_DETECTED=0`
- Backend memory stable around `165.6 MiB`.

## 12) Fresh DB Preservation

- Fresh DB was preserved (`yes`):
  - no volume deletion commands executed
  - no `docker compose down -v`
  - backend confirmed seed skip due existing data

## 13) Remaining Risks

- `/root/pdss` is deployed from an extracted source archive (not a live git checkout), so direct server-side `git rev-parse` provenance remains unavailable unless converted to a git clone workflow.
- Frontend build still contains pre-existing lint warnings.

## 14) Recommended Next Action

1. Keep this corrected deployment as the active baseline.
2. Optionally convert `/root/pdss` to a canonical git checkout workflow for direct on-server commit traceability.
3. Proceed with planned next release activities from `restart/baseline-before-github-push`.

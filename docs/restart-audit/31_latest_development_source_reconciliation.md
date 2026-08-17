# Latest Development Source Reconciliation

Date (UTC): 2026-08-08  
Host: `193.162.129.58`  
Live path: `/root/pdss`

## 1) Why Previous Deployment Was Incomplete

- The live reset had been deployed from the RC baseline line and did not include accepted Sprint 5F-Fix / 5F-Fix-2 commits.
- Mandatory accepted commits missing from the previous live source:
  - `ab7f7131ef67714036cf2cf88a722e78179d2d1c`
  - `ad55a733b6648638a150b7cf6fc9fc1d0251c31a`

## 2) Provenance Audit Results

Commands executed:

- `git fetch --all --prune`
- `git branch -a`
- `git status --short`
- `git log --oneline --decorate --graph --all --max-count=80`
- `git branch -a --contains <commit>`

Commit containment:

- `ab7f713` contained in:
  - `restart/sprint5f-fix-assignment-table-display-closure`
  - `restart/sprint5f-fix2-runtime-ui-closure`
  - `restart/sprint5g-procurement-optimization-handoff-ux`
- `ad55a733` contained in:
  - `restart/sprint5f-fix2-runtime-ui-closure`
  - `restart/sprint5g-procurement-optimization-handoff-ux`
- Release hardening commits (`ed6e5d2`, `ea30aa2`, `e811238`) are reachable from both baseline and Sprint 5F/5G lines.

Branch relationship facts:

- `restart/baseline-before-github-push` does **not** contain `ad55a733`.
- `restart/sprint5f-fix2-runtime-ui-closure` contains baseline head commit `c10ff4d`.
- `restart/sprint5g-procurement-optimization-handoff-ux` differs from Sprint 5F-Fix-2 by one documentation-only commit:
  - `86158c7 chore: document server reset and fresh rc1 reinstall`

Answers to required audit questions:

- Which branch contains Sprint 5F-Fix-2?  
  `restart/sprint5f-fix2-runtime-ui-closure`
- Which branch contains Phase 8/9/10 release hardening?  
  Both baseline and Sprint 5F/Fix2 lines (commit ancestry confirmed).
- Which branch contains Sprint 5G, if any?  
  `restart/sprint5g-procurement-optimization-handoff-ux` exists; only delta over Sprint 5F-Fix-2 here is documentation commit `86158c7`.
- Are release-hardening and Sprint 5F/5G branches diverged?  
  Yes, but Sprint 5F-Fix-2 line already includes release-hardening ancestry.
- Latest branch containing all accepted required work?  
  `restart/sprint5f-fix2-runtime-ui-closure` (accepted QA-passed 5F-Fix-2 + release hardening ancestry).
- Was an integration branch required?  
  No.

## 3) Selected Correct Live Source

Selected branch for live deployment:

- `restart/sprint5f-fix2-runtime-ui-closure`
- deployed commit: `ad55a733b6648638a150b7cf6fc9fc1d0251c31a`

Reason:

- Includes mandatory accepted Sprint 5F-Fix and 5F-Fix-2 commits.
- Includes required Phase 8/9/10 hardening ancestry.
- Avoids introducing uncertain Sprint 5G feature changes (no additional functional commit observed).

## 4) Pre-Deploy Source Evidence Checks

Confirmed present in selected source:

- `docs/restart-audit/81_sprint5f_fix2_runtime_ui_closure.md`
- `docs/restart-audit/80_sprint5f_fix_assignment_table_display_closure.md`
- `docs/restart-audit/27_phase10_controlled_release_rollout_signoff.md`
- `docs/release/release_notes_rc1.md`
- `backend/tests/test_phase8_release_candidate_smoke.py`

Pattern evidence in source:

- `assigned-users` found in `frontend/src/services/api.ts`
- `procurement.actions` found in procurement workbench/UI files
- `Tooltip` usage confirmed in procurement assignment item/project views and related UI components

## 5) Live DB Backup Before Replacement

Backup location:

- `/root/rivar_corrective_backups/pre_latest_source_deploy_20260808_101900.sql`

Details:

- Live DB service detected: `postgres`
- DB preserved; no volume deletion was performed.

## 6) Deployment Actions Performed

1. Stopped current live stack from `/root/pdss` using:
   - `docker compose down --remove-orphans`
2. Moved old live source directory:
   - `/root/pdss` -> `/root/pdss_wrong_source_20260808_102102` (timestamped)
3. Cloned selected branch from uploaded git bundle into `/root/pdss`:
   - branch: `restart/sprint5f-fix2-runtime-ui-closure`
   - commit: `ad55a733b6648638a150b7cf6fc9fc1d0251c31a`
4. Restored runtime `.env` from moved source directory.
5. Rebuilt and restarted live stack:
   - `docker compose up --build -d`

Safety rules followed:

- No `docker compose down -v`
- No DB volume deletion
- No use of demo stacks (`/root/pdss_demo`)

## 7) Post-Deploy Verification

Runtime:

- `docker compose ps`: backend healthy, postgres healthy, frontend up
- `GET /health`: `{"status":"healthy","version":"1.0.0-rc1","product":"Rivar","producer":"Corbit"}`
- `GET /openapi.json`: `OPENAPI_OK`

Live source provenance on server:

- `git branch --show-current` -> `restart/sprint5f-fix2-runtime-ui-closure`
- `git rev-parse HEAD` -> `ad55a733b6648638a150b7cf6fc9fc1d0251c31a`
- `git branch --contains ad55a733...` confirms inclusion
- `5F_FIX2_DEPLOYED_DOC_OK` present on server

## 8) Tests and Build

Backend full tests:

- Command: `docker compose run --rm backend python -m pytest tests -q`
- Result: **FAIL** (collection error)
  - `ImportError: cannot import name 'financial_projections' from 'app.routers'`
  - failing test: `tests/test_phase13f_financial_projection_engine.py`

Phase 8 smoke:

- Command: `docker compose run --rm backend python -m pytest tests/test_phase8_release_candidate_smoke.py -q`
- Result: **PASS** (`3 passed`)

Frontend build:

- Command: `docker compose run --rm frontend npm run build`
- Result: **PASS** (compiled with warnings)

## 9) Login and Runtime Smoke

Login checks (all HTTP `200`):

- `admin/admin123`
- `finance1/finance123`
- `proc1/proc123`
- `pmo1/pmo123`
- `pm1/pm123`

Runtime smoke script path checks:

- `backend/scripts/sprint5e_r4_runtime_smoke.py`: missing in container path context
- `scripts/sprint5e_r4_runtime_smoke.py`: missing

Conclusion: dedicated runtime smoke script not available on this deployed branch layout; login + health + phase8 smoke used as runtime validation.

## 10) Frontend Bundle Freshness

Captured current runtime evidence:

- `HEAD /static/js/bundle.js` -> `200`
- `ETag` present: `W/"b2fb36-C0Z02/NBGau3iSnsxj1m20fvKJ4"`
- `Content-Length`: `11729718`
- index HTML title shows `Rivar | Corbit`
- index references `/static/js/bundle.js`

Result:

- Frontend serves the rebuilt bundle from the reconciled source.
- Because bundle path is non-hashed (`bundle.js`), browser hard refresh can still be required for client cache invalidation.

## 11) Sprint 5G Inclusion Decision

- Sprint 5G branch exists, but observed delta above Sprint 5F-Fix-2 in this repo state is documentation-only commit `86158c7`.
- Deployed source intentionally anchored to accepted QA-passed Sprint 5F-Fix-2 branch.
- Sprint 5G functional inclusion status: not included as additional functional delta in this deployment.

## 12) Remaining Risks

- Backend full test suite currently fails on a Phase 13F import mismatch unrelated to deployment mechanics; requires code-level reconciliation of test/module alignment.
- Non-hashed frontend bundle path may need hard refresh on client browsers.

## 13) Recommended Next Action

1. Open a focused fix task for the Phase 13F import/test mismatch (`financial_projections` router import contract).
2. After fixing, rerun full backend suite and re-verify runtime.
3. If Sprint 5G functional code is expected beyond docs, prepare a separate controlled integration with explicit acceptance criteria and QA gate.

## 14) Re-verification on 2026-08-17

This prompt was re-run after the original 2026-08-08 reconciliation. No second source swap was required.

Live server re-check:

- Path: `/root/pdss`
- Branch: `restart/sprint5f-fix2-runtime-ui-closure`
- HEAD: `ad55a733b6648638a150b7cf6fc9fc1d0251c31a`
- Contains `ab7f713`: yes
- Contains `ad55a733`: yes
- Contains `e811238`: yes
- Sprint 5F-Fix-2 / Phase 10 / Phase 8 artifacts still present
- Health: `{"status":"healthy","version":"1.0.0-rc1","product":"Rivar","producer":"Corbit"}`
- OpenAPI: `200`
- Frontend: `200`
- Bundle still served: `/static/js/bundle.js` `ETag W/"b2fb36-C0Z02/NBGau3iSnsxj1m20fvKJ4"` `Content-Length 11729718`

Login re-check found a runtime-only regression, not a source mismatch:

- Symptom: `/auth/login` returned `500`
- Backend log: `asyncpg.exceptions.InvalidPasswordError: password authentication failed for user "postgres"`
- Action: synced Postgres password from compose values and recreated backend only (`docker compose up -d --no-deps --force-recreate backend`)
- No volumes deleted
- No `docker compose down -v`
- Source commit unchanged
- Login after fix: `admin`, `finance1`, `proc1`, `pmo1`, `pm1` all `200`

No new integration branch was created. Sprint 5G remains excluded because its only extra commit over 5F-Fix-2 is documentation commit `86158c7`.

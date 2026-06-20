# Phase 10 - Controlled Release Rollout and Production Sign-off

## Objective

Convert the accepted release candidate into a controlled rollout package with final sign-off artifacts and verification evidence, without introducing new product modules.

## Phase 10 Deliverables

- UI witness record: `docs/release/ui_witness_session_phase10.md`
- Defect triage log: `docs/release/uat_defect_log_phase10.md`
- Release notes (delivery-facing): `docs/release/release_notes_rc1.md`
- Production gate checklist: `docs/release/production_signoff_checklist_phase10.md`
- Controlled release package: `release_packages/corbit-rivar-rc1/`
  - `manifest.json`
  - `README_RELEASE.md`
  - `RELEASE_NOTES.md`
  - `KNOWN_LIMITATIONS.md`
  - `POST_DEPLOY_SMOKE_CHECKLIST.md`
  - `CHECKSUMS.sha256`
  - `update_package/` snapshot and deployment scripts

## Verification Evidence

Active release environment (`/root/pdss`):

- `docker compose ps`: pass (backend/postgres healthy)
- `curl -sS http://127.0.0.1:8000/health`: pass
- `docker compose run --rm backend python -m pytest tests -q`: `39 passed, 4 skipped, 38 warnings`
- `docker compose run --rm backend python -m pytest tests/test_phase8_release_candidate_smoke.py -q`: `3 passed, 20 warnings`
- `docker compose run --rm frontend npm run build`: success (`Compiled with warnings`)

Demo dataset gate (`/root/pdss`):

- create command: pass
- cleanup command: pass
- cleanup verification query: `demo_projects_count=0`, `demo_decisions_count=0`

Witness flow (`/root/pdss_demo`):

- 12/12 required package wizard and lock-path steps passed
- blocker defects: 0
- major defects: 0

## Release Decision

- Final sign-off status: `APPROVED FOR PILOT`
- Rationale: all phase gates passed; controlled release artifacts complete; no open blocker/major defects.

## Remaining Risks

- Existing frontend eslint warnings remain outside release-blocking scope.
- Existing backend deprecation warnings remain in test output.
- Legacy historical script examples may still exist outside hardened release package paths.

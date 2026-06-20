# Phase 10 Production Sign-off Checklist

## Release Identification

- Target branch: `restart/baseline-before-github-push`
- Baseline accepted Phase 9 commit: `ea30aa2`
- Phase 10 packaging commit: `TBD (filled in release response)`
- Release package path: `release_packages/corbit-rivar-rc1/`

## Target Environment

- Active release verification stack: `/root/pdss` on `193.162.129.58`
- Final witness stack (isolated demo): `/root/pdss_demo`

## Backup and Update Safety

- [x] Backup preflight previously validated (Phase 7)
- [x] Backup-failure abort behavior previously validated (Phase 7)
- [x] Staged apply rehearsal on cloned path previously validated (Phase 7)
- [x] Rollback command path validated (non-`down -v`) (Phase 7)

## Runtime Verification (Phase 10)

- [x] `docker compose ps` (active stack healthy: backend/postgres healthy)
- [x] `GET /health` on active stack (`{"status":"healthy","version":"1.0.0"}`)
- [x] Backend tests:
  - Command: `docker compose run --rm backend python -m pytest tests -q`
  - Result: `39 passed, 4 skipped, 38 warnings`
- [x] Phase 8 smoke tests:
  - Command: `docker compose run --rm backend python -m pytest tests/test_phase8_release_candidate_smoke.py -q`
  - Result: `3 passed, 20 warnings`
- [x] Frontend build:
  - Command: `docker compose run --rm frontend npm run build`
  - Result: success (`Compiled with warnings`)

## Demo Dataset Validation

- [x] Create: `docker compose run --rm -e PYTHONPATH=/app backend python scripts/create_demo_dataset.py --mode create`
- [x] Cleanup: `docker compose run --rm -e PYTHONPATH=/app backend python scripts/create_demo_dataset.py --mode cleanup`
- [x] Cleanup verification:
  - `demo_projects_count=0`
  - `demo_decisions_count=0`

## UI Witness Session (Package Wizard Focus)

- [x] Witness run completed on isolated demo stack (`/root/pdss_demo`)
- [x] Package Wizard create/edit partial package: pass
- [x] Package Wizard create full package: pass
- [x] Coverage summary visible: pass
- [x] Incomplete coverage lock rejected: pass
- [x] Complete coverage lock succeeded: pass
- [x] Procurement plan package/supplier context visible: pass
- Evidence file: `docs/release/evidence/phase10_ui_witness_probe_output.json`

## Known Limitations Acceptance

- Accepted:
  - Existing frontend eslint warnings (build stays green)
  - Existing backend deprecation warnings in pytest output
- Rejected blockers/majors: none

## Rollback Readiness

- [x] Release package includes backup/restore/update instructions
- [x] Release package includes update/deployment scripts and update files snapshot
- [x] Rollback steps documented in package README and notes

## Final Decision

- [x] `APPROVED FOR PILOT`
- [ ] `APPROVED FOR PRODUCTION`
- [ ] `APPROVED FOR DEMO ONLY`
- [ ] `NOT APPROVED`

Decision rationale: all Phase 10 verification gates passed, no open blocker/major defects, and controlled release package prepared.
